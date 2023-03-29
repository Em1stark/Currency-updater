# from app import db  # Remove this line
from models import Rate, CurrencyInfo, RateDate
from datetime import date, timedelta
from extensions import scheduler, db  # Add the db import here
from tasks import fetch_daily_rates


class RateService:

    @staticmethod
    def create_or_update(rate_date, currency_info, amount, rate_value):
        rate = Rate.query.filter_by(rate_date=rate_date, currency_info=currency_info).first()
        if not rate:
            rate = Rate(rate_date=rate_date, currency_info=currency_info)

        rate.amount = amount
        rate.rate = rate_value
        db.session.add(rate)
        db.session.commit()
        return rate

    @staticmethod
    def fetch_rates_by_date_range(start_date, end_date):
        dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        for rate_date in dates:
            rates = fetch_daily_rates(rate_date)
            rate_date_obj = RateDateService.find_or_create(rate_date)

            header = rates.pop(0)  # Remove the header row
            date_key = next(
                (key for key in header if key is not None and key.startswith(rate_date.strftime("%d %b %Y"))), None)
            if not date_key:
                continue

            key_map = {key: index for index, key in enumerate(header[date_key])}  # Create a mapping of key to index

            for rate in rates:
                if key_map.get('Country') and rate[key_map['Country']] == "Country":
                    continue

                if 'Code' not in key_map:
                    continue
                code = rate[key_map['Code']]

                currency_info = CurrencyInfoService.get_by_code(code) or CurrencyInfoService.create(
                    rate[key_map['Currency']], rate[key_map['Country']], code)
                RateService.create_or_update(rate_date_obj, currency_info, int(rate[key_map['Amount']]),
                                             float(rate[key_map['Rate']]))

class CurrencyInfoService:

    @staticmethod
    def create(currency, country, code):
        info = CurrencyInfo(currency=currency, country=country, code=code)
        db.session.add(info)
        db.session.commit()
        return info

    @staticmethod
    def get_by_code(code):
        return CurrencyInfo.query.filter_by(code=code).first()


class RateDateService:

    @staticmethod
    def find_or_create(rate_date):
        rate_date_obj = RateDate.query.filter_by(rate_date=rate_date).first()
        if not rate_date_obj:
            rate_date_obj = RateDate(rate_date=rate_date)
            db.session.add(rate_date_obj)
            db.session.commit()

        return rate_date_obj

    @staticmethod
    def get_rates_by_date(rate_date):
        rates = Rate.query.filter_by(rate_date=rate_date).all()
        return rates