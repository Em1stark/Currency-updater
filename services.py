# from app import db  # Remove this line
from models import Rate, CurrencyInfo, RateDate
from datetime import date
from extensions import scheduler, db  # Add the db import here


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