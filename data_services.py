import pandas as pd
import streamlit as st

from db_connection import feedback_col, groups_col, meals_col, menu_col


@st.cache_data(ttl=30, show_spinner=False)
def load_person_records(person: str):
    return list(
        meals_col.find(
            {"person_name": person},
            {
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
            },
        ).sort("meal_date", 1)
    )


@st.cache_data(ttl=30, show_spinner=False)
def load_all_records():
    return list(
        meals_col.find(
            {},
            {
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
            },
        ).sort("meal_date", 1)
    )


@st.cache_data(ttl=30, show_spinner=False)
def load_feedback_records():
    return list(
        feedback_col.find(
            {},
            {"person_name": 1, "message": 1, "rating": 1, "created_at": 1},
        ).sort("created_at", -1)
    )




@st.cache_data(ttl=30, show_spinner=False)
def load_groups():
    return list(
        groups_col.find(
            {},
            {"group_name": 1, "description": 1, "created_at": 1, "updated_at": 1},
        ).sort("group_name", 1)
    )

@st.cache_data(ttl=30, show_spinner=False)
def load_monthly_menus():
    return list(
        menu_col.find(
            {},
            {
                "month_key": 1,
                "month_label": 1,
                "image_bytes": 1,
                "image_type": 1,
                "updated_at": 1,
                "updated_by": 1,
            },
        ).sort("month_key", -1)
    )


def clear_cached_queries():
    load_person_records.clear()
    load_all_records.clear()
    load_feedback_records.clear()
    load_groups.clear()
    load_monthly_menus.clear()


def prepare_records_dataframe(records):
    frame = pd.DataFrame(records)

    if frame.empty:
        return frame

    frame["_id"] = frame["_id"].astype(str)
    frame["meal_date"] = pd.to_datetime(frame["meal_date"])
    return frame
