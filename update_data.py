from app import create_app
from tasks import update_yearly_rates, update_daily_rates

app = create_app()

with app.app_context():
    update_yearly_rates()
    update_daily_rates()
