import streamlit as st
from logger import get_logger
from errors import MealTrackerError, ConfigError

st.set_page_config(page_title="Meal Tracker", layout="centered")

logger = get_logger()

# Initialize app
try:
    from data_services import (
        prepare_records_dataframe,
    )
    from db_connection import meals_col
    from group_services import load_group_members
    from ui_sections import (
        initialize_session_state,
        render_chart_and_monthly_summary,
        render_group_payment_summary,
        render_export_data,
        render_feedback_and_admin_panel,
        render_monthly_section,
        render_monthly_menu_section,
        render_name_input,
        render_saved_records,
        render_group_selection,
        render_bulk_meal_entry,
    )

    logger.info("Application started")

except (ImportError, ConfigError) as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    st.error("❌ Application initialization failed. Please check your configuration and try again.")
    st.stop()

try:
    admin_password = st.secrets.get("ADMIN_PASSWORD", "")
    if not admin_password:
        raise ConfigError("ADMIN_PASSWORD not found in secrets")

except (ConfigError, Exception) as e:
    logger.error(f"Configuration error: {str(e)}")
    st.error("❌ Configuration error. Please check your secrets.")
    st.stop()

st.title("🍽️ Daily Meal Tracker")

try:
    initialize_session_state()

    # User & Group Selection
    person_name, group_name = render_name_input(logger)

    st.divider()

    # Group Management
    render_group_selection(logger, group_name)

    st.divider()

    # Bulk Meal Entry
    render_bulk_meal_entry(group_name, logger)

    st.divider()

    # Load group members
    members = load_group_members(group_name) if group_name else []

    if members:
        # Monthly Menu Section
        render_monthly_menu_section(group_name, logger)

        st.divider()

        # Fetch group meal data
        group_meals = list(
            meals_col.find(
                {"person_name": {"$in": members}},
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
            ).sort("meal_date", -1)
        )

        visible_df = prepare_records_dataframe(group_meals)

        logger.info(f"Fetched group records for '{group_name}' | count={len(group_meals)}")

        # Meal Records
        st.markdown(f"## 📋 {group_name.upper()} Meal Records")
        render_saved_records(group_name, visible_df, logger)

        st.divider()

        # Export Section
        st.markdown("## 📤 Export Data")
        render_export_data(group_name, visible_df, logger)

        st.divider()

        # Monthly Summary
        st.markdown("## 📅 Monthly Summary")
        render_monthly_section(group_name, visible_df, logger)

        st.divider()

        # Payment Summary
        st.markdown("## 💰 Group Payment Summary")
        render_group_payment_summary(
            visible_df,
            logger,
            group_name,
        )

        st.divider()

        # Charts & Analytics
        st.markdown("## 📊 Analytics & Trends")
        render_chart_and_monthly_summary(
            group_name,
            visible_df,
            logger,
        )

    else:
        st.info("ℹ️ Add members to the group to view meal records.")

    st.divider()

    # Feedback & Admin Panel
    render_feedback_and_admin_panel(
        group_name,
        admin_password,
        logger,
    )

except MealTrackerError as e:
    logger.error(f"Application error: {e.error_code} - {e.message}")
    st.error(f"❌ {e.user_message}")
    st.stop()

except Exception as e:
    logger.error(
        f"Unexpected error: {str(e)}",
        exc_info=True,
    )
    st.error("❌ An unexpected error occurred. Please refresh the page or try again later.")
    st.stop()
