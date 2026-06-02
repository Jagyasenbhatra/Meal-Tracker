from datetime import date
from config import DEFAULT_MEAL_MODE, PAGE_SIZE as CONFIG_PAGE_SIZE

# Use values from config module for consistency
PAGE_SIZE = CONFIG_PAGE_SIZE

SESSION_DEFAULTS = {
    "person_name": "",
    "meal_date": date.today(),
    "mode": DEFAULT_MEAL_MODE,
    "lunch": 0,
    "dinner": 0,
    "manual_total": 0,
    "meal_price": 0.0,
}
