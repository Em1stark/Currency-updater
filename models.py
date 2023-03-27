from datetime import date
from extensions import db

class Rate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    rate = db.Column(db.Float)
    rate_date_id = db.Column(db.Integer, db.ForeignKey('rate_date.id'))
    rate_date = db.relationship('RateDate', backref=db.backref('rates', lazy=True))
    currency_info_id = db.Column(db.Integer, db.ForeignKey('currency_info.id'))
    currency_info = db.relationship('CurrencyInfo', backref=db.backref('rates', lazy=True))

class CurrencyInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(255))
    currency = db.Column(db.String(255))
    code = db.Column(db.String(255), unique=True)

class RateDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate_date = db.Column(db.Date, unique=True, default=date.today)
