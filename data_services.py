import pandas as pd
import streamlit as st

from db_connection import feedback_col, meals_col, menu_col
from errors import QueryError
from config import (
    MEALS_PROJECTION,
    FEEDBACK_PROJECTION,
    MENUS_PROJECTION,
    CACHE_TTL_RECORDS,
    CACHE_TTL_FEEDBACK,
    CACHE_TTL_MENUS,
)


@st.cache_data(ttl=CACHE_TTL_RECORDS, show_spinner=False)
def load_person_records(person: str):
    """Load meal records for a specific person with error handling"""
    try:
        return list(
            meals_col.find(
                {"person_name": person},
                MEALS_PROJECTION,
            ).sort("meal_date", 1)
        )
    except Exception as e:
        raise QueryError(str(e), operation="load_person_records")


@st.cache_data(ttl=CACHE_TTL_RECORDS, show_spinner=False)
def load_context_records(person: str, group_name: str):
    """Load context records for person and group with error handling"""
    try:
        filters = {"person_name": person}

        normalized_group = (group_name or "").strip()
        if normalized_group:
            filters = {
                "$or": [
                    {"person_name": person},
                    {"group_name": normalized_group},
                ]
            }

        return list(
            meals_col.find(
                filters,
                MEALS_PROJECTION,
            ).sort("meal_date", 1)
        )
    except Exception as e:
        raise QueryError(str(e), operation="load_context_records")


@st.cache_data(ttl=CACHE_TTL_RECORDS, show_spinner=False)
def load_all_records():
    """Load all meal records with error handling"""
    try:
        return list(
            meals_col.find(
                {},
                MEALS_PROJECTION,
            ).sort("meal_date", 1)
        )
    except Exception as e:
        raise QueryError(str(e), operation="load_all_records")


@st.cache_data(ttl=CACHE_TTL_FEEDBACK, show_spinner=False)
def load_feedback_records():
    """Load all feedback records with error handling"""
    try:
        return list(
            feedback_col.find(
                {},
                FEEDBACK_PROJECTION,
            ).sort("created_at", -1)
        )
    except Exception as e:
        raise QueryError(str(e), operation="load_feedback_records")


@st.cache_data(ttl=CACHE_TTL_MENUS, show_spinner=False)
def load_monthly_menus(group_name: str):
    """Load monthly menus with error handling"""
    try:
        normalized_group = (group_name or "").strip()

        if not normalized_group:
            return []

        return list(
            menu_col.find(
                {
                    "menu_scope": "group",
                    "scope_value": normalized_group,
                },
                MENUS_PROJECTION,
            ).sort("month_key", -1)
        )

    except Exception as e:
        raise QueryError(str(e), operation="load_monthly_menus")


def clear_cached_queries():
    """Clear all cached queries"""
    load_person_records.clear()
    load_context_records.clear()
    load_all_records.clear()
    load_feedback_records.clear()
    load_monthly_menus.clear()


def prepare_records_dataframe(records):
    """Prepare DataFrame from records with error handling"""
    try:
        frame = pd.DataFrame(records)

        if frame.empty:
            return frame

        frame["_id"] = frame["_id"].astype(str)
        frame["meal_date"] = pd.to_datetime(frame["meal_date"])
        return frame
    except Exception as e:
        raise QueryError(
            f"Failed to prepare dataframe: {str(e)}", operation="prepare_records_dataframe"
        )
