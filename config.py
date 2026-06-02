"""
Centralized configuration for database schemas, projections, and application settings.
This makes it easy to add features and maintain consistency across the codebase.
"""

# ============================================================================
# DATABASE FIELD PROJECTIONS (used in find() queries)
# ============================================================================
# Centralized to avoid repetition and ensure consistency across the app

MEALS_PROJECTION = {
    "person_name": 1,
    "group_name": 1,
    "meal_date": 1,
    "mode": 1,
    "lunch": 1,
    "dinner": 1,
    "total_meals": 1,
    "meal_price": 1,
    "total_amount": 1,
    "created_at": 1,
}

FEEDBACK_PROJECTION = {
    "person_name": 1,
    "message": 1,
    "rating": 1,
    "created_at": 1,
}

MENUS_PROJECTION = {
    "month_key": 1,
    "month_label": 1,
    "menu_scope": 1,
    "scope_value": 1,
    "image_bytes": 1,
    "image_type": 1,
    "updated_at": 1,
    "updated_by": 1,
}

GROUPS_PROJECTION = {
    "group_name": 1,
    "members": 1,
    "created_at": 1,
    "updated_at": 1,
}

# ============================================================================
# VALIDATION CONSTRAINTS
# ============================================================================

MIN_GROUP_NAME_LENGTH = 1
MAX_GROUP_NAME_LENGTH = 100

MIN_MEMBER_NAME_LENGTH = 1
MAX_MEMBER_NAME_LENGTH = 100

MIN_MEAL_PRICE = 0.0
MAX_MEAL_PRICE = 100000.0  # Reasonable upper limit

MIN_MEAL_COUNT = 0
MAX_MEAL_COUNT = 10  # Max meals per day

# ============================================================================
# CACHE SETTINGS
# ============================================================================

CACHE_TTL_GROUPS = 5  # seconds - groups change less frequently
CACHE_TTL_MENUS = 30  # seconds
CACHE_TTL_FEEDBACK = 30  # seconds
CACHE_TTL_RECORDS = 30  # seconds

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

MONGO_POOL_SIZE_MIN = 5
MONGO_POOL_SIZE_MAX = 100
MONGO_SERVER_TIMEOUT_MS = 5000
MONGO_RETRY_WRITES = True

# ============================================================================
# UI SETTINGS
# ============================================================================

PAGE_SIZE = 50
DEFAULT_MEAL_MODE = "Auto (Lunch + Dinner)"
CURRENCY_SYMBOL = "₹"

# ============================================================================
# MEAL MODES
# ============================================================================

MEAL_MODES = {
    "Manual": "Manual",
    "Auto (Lunch + Dinner)": "Auto (Lunch + Dinner)",
}

# ============================================================================
# FEATURE FLAGS (easy to enable/disable features)
# ============================================================================

FEATURES = {
    "group_management": True,
    "bulk_meal_entry": True,
    "monthly_menus": True,
    "payment_summary": True,
    "monthly_analytics": True,
    "admin_panel": True,
    "feedback_system": True,
    "data_export": True,
}


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return FEATURES.get(feature_name, False)
