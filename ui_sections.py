from datetime import datetime
from io import BytesIO
from math import ceil

import pandas as pd
import streamlit as st
from bson.objectid import ObjectId

from constants import PAGE_SIZE, SESSION_DEFAULTS
from data_services import clear_cached_queries, load_feedback_records
from db_connection import feedback_col, meals_col


def initialize_session_state():
    for key, value in SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    st.session_state.setdefault("admin_authenticated", False)


def reset_form(logger):
    logger.info("Form reset")
    for key in ["meal_date", "mode", "lunch", "dinner", "manual_total", "meal_price"]:
        st.session_state.pop(key, None)
    st.rerun()


def render_name_input(logger):
    person_name = st.text_input("👤 Person Name", key="person_name").strip()

    if not person_name:
        st.warning("Please enter a name to continue.")
        st.stop()

    logger.info(f"User active | person={person_name}")
    return person_name


def render_meal_input():
    meal_date = st.date_input("Select Date", key="meal_date")

    mode = st.radio(
        "Meal Count Mode", ["Auto (Lunch + Dinner)", "Manual (Total Meals)"], key="mode"
    )

    if mode.startswith("Auto"):
        c1, c2 = st.columns(2)
        with c1:
            lunch = st.number_input("Lunch Meals", min_value=0, step=1, key="lunch")
        with c2:
            dinner = st.number_input("Dinner Meals", min_value=0, step=1, key="dinner")
        total_meals = lunch + dinner
    else:
        lunch = None
        dinner = None
        total_meals = st.number_input("Total Meals", min_value=0, step=1, key="manual_total")

    meal_price = st.number_input(
        "Price per Meal (₹)", min_value=0.0, step=1.0, key="meal_price"
    )
    total_amount = total_meals * meal_price

    return {
        "meal_date": meal_date,
        "mode": mode,
        "lunch": lunch,
        "dinner": dinner,
        "total_meals": total_meals,
        "meal_price": meal_price,
        "total_amount": total_amount,
    }


def render_save_and_reset(person_name, meal_data, logger):
    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Save Record"):
            meals_col.insert_one(
                {
                    "person_name": person_name,
                    "meal_date": meal_data["meal_date"].isoformat(),
                    "mode": meal_data["mode"],
                    "lunch": meal_data["lunch"] if meal_data["mode"].startswith("Auto") else None,
                    "dinner": meal_data["dinner"] if meal_data["mode"].startswith("Auto") else None,
                    "total_meals": meal_data["total_meals"],
                    "meal_price": meal_data["meal_price"],
                    "total_amount": meal_data["total_amount"],
                    "created_at": datetime.utcnow(),
                }
            )

            logger.info(
                f"Meal saved | person={person_name} | date={meal_data['meal_date']} "
                f"| meals={meal_data['total_meals']} | amount={meal_data['total_amount']}"
            )

            st.success("Record saved!")
            clear_cached_queries()

    with c2:
        if st.button("🔄 Reset"):
            reset_form(logger)


def render_current_entry_summary(meal_data, logger):
    st.divider()
    st.subheader("📊 Meal Summary (Current Entry)")
    st.write(f"**Date:** {meal_data['meal_date']}")
    st.write(f"**Total Meals:** {meal_data['total_meals']}")
    st.write(f"### 💰 Total Amount: ₹{meal_data['total_amount']}")
    logger.info("Displayed current entry summary")


def render_saved_records(person_name, df, logger):
    st.divider()
    st.subheader(f"📁 Saved Records — {person_name}")

    c1, c2 = st.columns(2)
    c1.metric("🍽️ Total Meals", int(df["total_meals"].sum()) if not df.empty else 0)
    c2.metric("💰 Total Amount", f"₹{df['total_amount'].sum()}" if not df.empty else "₹0")

    if not df.empty:
        total_pages = ceil(len(df) / PAGE_SIZE)
        page_options = list(range(1, total_pages + 1))
        selected_page = st.selectbox("Records page", page_options, index=total_pages - 1)

        start_idx = (selected_page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        paged_df = df.iloc[start_idx:end_idx]

        st.caption(f"Showing records {start_idx + 1} to {min(end_idx, len(df))} of {len(df)}")
        st.dataframe(paged_df, width="stretch")
    else:
        st.dataframe(df, width="stretch")

    logger.info("Displayed records table")


def render_export_data(person_name, df, logger):
    st.divider()
    st.subheader("📤 Export Data")

    if df.empty:
        return

    logger.info(f"Export all data triggered | rows={len(df)}")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_meals.csv",
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    st.download_button("⬇️ Download Excel", buffer.getvalue(), file_name=f"{person_name}_meals.xlsx")


def render_edit_delete(df, logger):
    st.divider()
    st.subheader("✏️ Edit / 🗑 Delete Record")

    if df.empty:
        return

    record_map = {
        f"{row['meal_date'].date()} ({row['_id']})": row["_id"]
        for _, row in df.iterrows()
    }

    label = st.selectbox("Select Record", record_map.keys())
    record_id = record_map[label]
    record = df[df["_id"] == record_id].iloc[0]

    ec1, ec2 = st.columns(2)
    with ec1:
        edit_lunch = st.number_input("Edit Lunch", min_value=0, value=int(record["lunch"] or 0))
        edit_dinner = st.number_input("Edit Dinner", min_value=0, value=int(record["dinner"] or 0))
    with ec2:
        edit_price = st.number_input("Edit Price", min_value=0.0, value=float(record["meal_price"]))

    edit_total = edit_lunch + edit_dinner
    edit_amount = edit_total * edit_price

    u1, u2 = st.columns(2)
    with u1:
        if st.button("✅ Update"):
            meals_col.update_one(
                {"_id": ObjectId(record_id)},
                {
                    "$set": {
                        "lunch": edit_lunch,
                        "dinner": edit_dinner,
                        "total_meals": edit_total,
                        "meal_price": edit_price,
                        "total_amount": edit_amount,
                    }
                },
            )

            logger.info(f"Meal updated | id={record_id}")
            st.success("Record updated!")
            clear_cached_queries()
            st.rerun()

    with u2:
        if st.button("🗑 Delete"):
            meals_col.delete_one({"_id": ObjectId(record_id)})
            logger.warning(f"Meal deleted | id={record_id}")
            st.warning("Record deleted!")
            clear_cached_queries()
            st.rerun()


def render_monthly_section(person_name, df, logger):
    st.divider()
    st.subheader("📆 Filter Records by Month")

    monthly_df = pd.DataFrame()
    selected_year = None
    selected_month = None

    if not df.empty:
        df["year"] = df["meal_date"].dt.year
        df["month_num"] = df["meal_date"].dt.month
        df["month_name"] = df["meal_date"].dt.strftime("%B")

        col_y, col_m = st.columns(2)

        with col_y:
            selected_year = st.selectbox("Select Year", sorted(df["year"].unique(), reverse=True))

        months_for_year = (
            df[df["year"] == selected_year][["month_num", "month_name"]]
            .drop_duplicates()
            .sort_values("month_num")
        )

        if months_for_year.empty:
            logger.warning(f"No months found for year {selected_year}")
            st.info("No records found for the selected year.")
        else:
            with col_m:
                selected_month = st.selectbox("Select Month", months_for_year["month_name"].tolist())

            selected_month_num = months_for_year[
                months_for_year["month_name"] == selected_month
            ]["month_num"].iloc[0]

            monthly_df = df[(df["year"] == selected_year) & (df["month_num"] == selected_month_num)]

            logger.info(
                f"Monthly filter applied | {selected_month} {selected_year} | rows={len(monthly_df)}"
            )

            if monthly_df.empty:
                st.info("No records available for the selected month.")
            else:
                c1, c2 = st.columns(2)
                c1.metric("🍽️ Total Meals (Month)", int(monthly_df["total_meals"].sum()))
                c2.metric("💰 Total Amount (Month)", f"₹{float(monthly_df['total_amount'].sum())}")
                st.dataframe(monthly_df, width="stretch")
    else:
        logger.info("Monthly filter skipped — no data available")
        st.info("No records available.")

    st.subheader("📤 Export Monthly Data")

    if not df.empty and not monthly_df.empty:
        logger.info("Monthly export triggered")

        st.download_button(
            "⬇️ Download Monthly CSV",
            monthly_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{person_name}_{selected_year}_{selected_month}.csv",
        )

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            monthly_df.to_excel(writer, index=False)

        st.download_button(
            "⬇️ Download Monthly Excel",
            buffer.getvalue(),
            file_name=f"{person_name}_{selected_year}_{selected_month}.xlsx",
        )


def render_chart_and_monthly_summary(person_name, df, logger):
    st.divider()
    st.subheader("📊 Meals vs Date")

    if not df.empty:
        logger.info("Rendered meals vs date chart")
        st.line_chart(df.set_index("meal_date")["total_meals"])

    st.divider()
    st.subheader("📆 Monthly Summary")

    if df.empty:
        return

    df["month"] = df["meal_date"].dt.to_period("M").astype(str)

    monthly = (
        df.groupby("month")
        .agg(total_meals=("total_meals", "sum"), total_amount=("total_amount", "sum"))
        .reset_index()
        .sort_values("month")
    )

    logger.info("Generated monthly summary")
    st.dataframe(monthly, width="stretch")

    logger.info("Monthly summary export triggered")

    st.download_button(
        "⬇️ Download Monthly Summary CSV",
        monthly.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_monthly_summary.csv",
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        monthly.to_excel(writer, index=False)

    st.download_button(
        "⬇️ Download Monthly Summary Excel",
        buffer.getvalue(),
        file_name=f"{person_name}_monthly_summary.xlsx",
    )


def render_feedback_and_admin_panel(person_name, admin_password, logger):
    st.divider()
    st.header("📝 Feedback")

    with st.form("feedback_form"):
        msg = st.text_area("Your feedback")
        rating = st.slider("Rating", 1, 5, 4)

        if st.form_submit_button("📨 Submit") and msg.strip():
            feedback_col.insert_one(
                {
                    "person_name": person_name,
                    "message": msg.strip(),
                    "rating": rating,
                    "created_at": datetime.utcnow(),
                }
            )

            logger.info(f"Feedback submitted | rating={rating}")
            st.success("Thanks for the feedback 🙌")
            clear_cached_queries()

    st.divider()
    st.header("🔐 Admin Feedback Panel")

    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Admin Password", type="password")
        if st.button("🔓 Login"):
            if pwd == admin_password:
                st.session_state.admin_authenticated = True
                logger.info("Admin login successful")
                st.rerun()
            else:
                logger.warning("Admin login failed")
                st.error("Incorrect password")
        return

    fb_records = load_feedback_records()
    fb_df = pd.DataFrame(fb_records)

    if not fb_df.empty:
        fb_df["_id"] = fb_df["_id"].astype(str)
        st.dataframe(fb_df, width="stretch")

        fb_map = {
            f"{row['person_name']} | {row['created_at']}": row["_id"]
            for _, row in fb_df.iterrows()
        }

        fb_label = st.selectbox("Select feedback", fb_map.keys())
        if st.button("🗑 Delete Feedback"):
            feedback_col.delete_one({"_id": ObjectId(fb_map[fb_label])})
            logger.warning(f"Feedback deleted | id={fb_map[fb_label]}")
            st.success("Feedback deleted")
            clear_cached_queries()
            st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        logger.info("Admin logged out")
        st.rerun()
