from datetime import date

PAGE_SIZE = 50

SESSION_DEFAULTS = {
    "person_name": "",
    "meal_date": date.today(),
    "mode": "Auto (Lunch + Dinner)",
    "lunch": 0,
    "dinner": 0,
    "manual_total": 0,
    "meal_price": 0.0,
    "group_name": "",
    "group_name_owner": "",
}
