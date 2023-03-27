import requests
import csv
import logging
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from extensions import scheduler
from datetime import datetime
from services import RateService, CurrencyInfoService, RateDateService

# Configure logging
logging.basicConfig(level=logging.INFO)

def parse_csv(data):
    reader = csv.DictReader(StringIO(data), delimiter='|')
    rates = []
    for row in reader:
        rates.append(row)
    return rates


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None


def fetch_daily_rates(date):
    url = f"https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt?date={date.strftime('%d.%m.%Y')}"
    data = fetch_data(url)
    return parse_csv(data) if data else []


def fetch_yearly_rates(year):
    url = f"https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/year.txt?year={year}"
    data = fetch_data(url)
    return parse_csv(data) if data else []


def update_daily_rates():
    logging.info("Starting update_daily_rates")
    today = datetime.now().date()
    rates = fetch_daily_rates(today)
    rate_date = RateDateService.find_or_create(today)

    header = rates.pop(0)  # Remove the header row
    date_key = next((key for key in header if key is not None and key.startswith(today.strftime("%d %b %Y"))), None)
    if not date_key:
        raise ValueError(f"Couldn't find date key for {today.strftime('%d %b %Y')} in the header")

    key_map = {key: index for index, key in enumerate(header[date_key])}  # Create a mapping of key to index

    for rate in rates:
        if key_map.get('Country') and rate[key_map['Country']] == "Country":
            continue

        if 'Code' not in key_map:
            continue
        code = rate[key_map['Code']]

        currency_info = CurrencyInfoService.get_by_code(code) or CurrencyInfoService.create(rate[key_map['Currency']], rate[key_map['Country']], code)
        RateService.create_or_update(rate_date, currency_info, int(rate[key_map['Amount']]), float(rate[key_map['Rate']]))

    logging.info("Finished update_daily_rates")


@scheduler.task("cron", id="update_yearly_rates", day="1", month="1", hour="0", minute="0")
def update_yearly_rates():
    logging.info("Starting update_yearly_rates")
    current_year = datetime.now().year

    def process_year(year):
        rates = fetch_yearly_rates(year)
        for rate in rates:
            if rate["Date"] == "Date":
                continue

            rate_date = datetime.strptime(rate["Date"], "%d.%m.%Y").date()
            rate_date_obj = RateDateService.find_or_create(rate_date)

            for key, value in rate.items():
                if key == "Date" or key is None or value is None:
                    continue

                code_amount = key.split()
                if len(code_amount) != 2:
                    continue

                code = code_amount[1]
                amount = int(code_amount[0])
                rate_value = float(value)

                currency_info = CurrencyInfoService.get_by_code(code) or CurrencyInfoService.create(code, "", code)
                RateService.create_or_update(rate_date_obj, currency_info, amount, rate_value)

    # Using ThreadPoolExecutor for parallel processing of years
    with ThreadPoolExecutor() as executor:
        executor.map(process_year, range(1999, current_year + 1))

    logging.info("Finished update_yearly_rates")