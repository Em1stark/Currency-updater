from flask import Flask, jsonify, request, render_template
from config import Config
from extensions import db, scheduler
from models import Rate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    scheduler.init_app(app)

    with app.app_context():
        db.create_all()
        from services import RateService, CurrencyInfoService, RateDateService  # Move import statements here


    @app.route('/')
    def index():
        return render_template("index.html")

    from datetime import datetime
    from services import RateService, CurrencyInfoService, RateDateService

    from flask import request

    from flask import request, jsonify

    @app.route('/report', methods=['GET'])
    def get_rates_report():
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currencies = request.args.get('currencies')

        # Validate and parse input
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD' format.", 400

        currencies = [c.strip() for c in currencies.split(',')]
        if not all(currencies):
            return "Invalid currencies input. Please provide a comma-separated list of currency codes.", 400

        report_data = []

        for currency_code in currencies:
            currency_info = CurrencyInfoService.get_by_code(currency_code)
            if not currency_info:
                continue

            rates = Rate.query.filter(Rate.currency_info_id == currency_info.id,
                                      Rate.rate_date_id >= RateDateService.find_or_create(start_date).id,
                                      Rate.rate_date_id <= RateDateService.find_or_create(end_date).id).all()

            if not rates:
                continue

            rates_data = [rate.rate for rate in rates]
            report_data.append({
                "currency": currency_code,
                "minimum": min(rates_data),
                "maximum": max(rates_data),
                "average": sum(rates_data) / len(rates_data)
            })

        if not report_data:
            return "No data found for the given date range and currencies.", 404

        response = jsonify(report_data)
        response.headers.set('Content-Type', 'application/json; charset=utf-8')
        response.headers.set('Access-Control-Allow-Origin', '*')
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        return response

    @app.route('/rates/<date_string>')
    def get_rates_by_date(date_string):
        try:
            date_object = datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD' format.", 400

        rate_date = RateDateService.find_or_create(date_object)
        rates = Rate.query.filter_by(rate_date_id=rate_date.id).all()

        if not rates:
            return "No currency rates found for the given date.", 404

        rates_data = [
            {
                "currency": rate.currency_info.code,
                "amount": rate.amount,
                "rate": rate.rate
            }
            for rate in rates
        ]

        return jsonify(rates_data)  # Return the JSON response

    return app

app = create_app()

if __name__ == '__main__':
    app.run()
