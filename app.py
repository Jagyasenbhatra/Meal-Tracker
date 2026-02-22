import streamlit as st

from data_services import load_person_records, prepare_records_dataframe
from logger import get_logger
from ui_sections import (
    initialize_session_state,
    render_chart_and_monthly_summary,
    render_current_entry_summary,
    render_edit_delete,
    render_export_data,
    render_feedback_and_admin_panel,
    render_meal_input,
    render_monthly_menu_section,
    render_monthly_section,
    render_name_input,
    render_save_and_reset,
    render_saved_records,
)


logger = get_logger()
admin_password = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title="Meal Tracker", layout="centered")
st.title("🍽️ Daily Meal Tracker")
logger.info("Application started")

initialize_session_state()
person_name = render_name_input(logger)
meal_data = render_meal_input()
render_save_and_reset(person_name, meal_data, logger)
render_current_entry_summary(meal_data, logger)
render_monthly_menu_section(person_name, logger)

records = load_person_records(person_name)
logger.info(f"Fetched records | count={len(records)}")
df = prepare_records_dataframe(records)

render_saved_records(person_name, df, logger)
render_export_data(person_name, df, logger)
render_edit_delete(df, logger)
render_monthly_section(person_name, df, logger)
render_chart_and_monthly_summary(person_name, df, logger)
render_feedback_and_admin_panel(person_name, admin_password, logger)
