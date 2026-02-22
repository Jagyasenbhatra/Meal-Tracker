import streamlit as st

from data_services import load_context_records, load_person_records, prepare_records_dataframe
from logger import get_logger
from ui_sections import (
    initialize_session_state,
    render_chart_and_monthly_summary,
    render_current_entry_summary,
    render_edit_delete,
    render_group_payment_summary,
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
person_name, group_name = render_name_input(logger)
meal_data = render_meal_input()
render_save_and_reset(person_name, group_name, meal_data, logger)
render_current_entry_summary(meal_data, logger)
render_monthly_menu_section(person_name, group_name, logger)

own_records = load_person_records(person_name)
visible_records = load_context_records(person_name, group_name)
logger.info(f"Fetched own records | count={len(own_records)}")
logger.info(f"Fetched visible records (own + group) | count={len(visible_records)}")
own_df = prepare_records_dataframe(own_records)
visible_df = prepare_records_dataframe(visible_records)

render_saved_records(person_name, visible_df, logger)
render_export_data(person_name, visible_df, logger)
render_edit_delete(own_df, logger)
render_monthly_section(person_name, visible_df, logger)
render_group_payment_summary(visible_df, logger)
render_chart_and_monthly_summary(person_name, visible_df, logger)
render_feedback_and_admin_panel(person_name, admin_password, logger)
