from pymongo import ASCENDING, DESCENDING, MongoClient
import streamlit as st
from errors import ConnectionError as DBConnectionError, ConfigError
from config import MONGO_POOL_SIZE_MAX, MONGO_POOL_SIZE_MIN, MONGO_SERVER_TIMEOUT_MS, MONGO_RETRY_WRITES


@st.cache_resource
def get_database():
    """Create a shared MongoDB connection for all Streamlit reruns/sessions."""
    try:
        if "MONGO_URI" not in st.secrets:
            raise ConfigError("MONGO_URI not found in secrets. Please check your .streamlit/secrets.toml file.")

        mongo_uri = st.secrets["MONGO_URI"]

        if not mongo_uri:
            raise ConfigError("MONGO_URI is empty. Please provide a valid MongoDB connection string.")

        # Create client with connection error handling
        client = MongoClient(
            mongo_uri,
            maxPoolSize=MONGO_POOL_SIZE_MAX,
            minPoolSize=MONGO_POOL_SIZE_MIN,
            serverSelectionTimeoutMS=MONGO_SERVER_TIMEOUT_MS,
            retryWrites=MONGO_RETRY_WRITES,
            connectTimeoutMS=MONGO_SERVER_TIMEOUT_MS,
        )

        # Test connection
        client.admin.command('ping')

    except Exception as e:
        raise DBConnectionError(f"Failed to connect to MongoDB: {str(e)}")

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

    # ------------------------------
    # Groups indexes
    # ------------------------------
    groups = database["groups"]

    # Drop old incorrect index if it exists
    try:
        groups.drop_index("idx_groups_group_name")
    except Exception:
        pass  # Ignore if it doesn't exist

    # Create correct index
    groups.create_index(
        [("group_name", ASCENDING)],
        name="idx_groups_name",
        unique=True,
    )

    return database


db = get_database()
meals_col = db["meals"]
feedback_col = db["feedback"]
menu_col = db["menus"]
groups_col = db["groups"]
