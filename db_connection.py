from pymongo import ASCENDING, DESCENDING, MongoClient
import streamlit as st


@st.cache_resource
def get_database():
    """Create a shared MongoDB connection for all Streamlit reruns/sessions."""
    mongo_uri = st.secrets["MONGO_URI"]

    client = MongoClient(
        mongo_uri,
        maxPoolSize=100,
        minPoolSize=5,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
    )

    database = client["meal_tracker"]

    # ------------------------------
    # Meals indexes
    # ------------------------------
    database["meals"].create_index(
        [("person_name", ASCENDING), ("meal_date", DESCENDING)],
        name="idx_meals_person_date",
    )

    database["meals"].create_index(
        [("group_name", ASCENDING), ("meal_date", DESCENDING)],
        name="idx_meals_group_date",
    )

    # ------------------------------
    # Feedback indexes
    # ------------------------------
    database["feedback"].create_index(
        [("created_at", DESCENDING)],
        name="idx_feedback_created_at",
    )

    # ------------------------------
    # Menus indexes
    # ------------------------------
    menus = database["menus"]

    # Drop old incorrect index if it exists
    try:
        menus.drop_index("idx_menus_month_key")
    except Exception:
        pass  # Ignore if it doesn't exist

    # Correct compound unique index
    menus.create_index(
        [
            ("menu_scope", ASCENDING),
            ("scope_value", ASCENDING),
            ("month_key", ASCENDING),
        ],
        name="idx_menus_scope_month_key",
        unique=True,
    )

    return database


db = get_database()
meals_col = db["meals"]
feedback_col = db["feedback"]
menu_col = db["menus"]
