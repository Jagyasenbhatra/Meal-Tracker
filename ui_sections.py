from datetime import datetime
from io import BytesIO
from math import ceil

import pandas as pd
import streamlit as st
from bson.objectid import ObjectId

from constants import PAGE_SIZE, SESSION_DEFAULTS
from data_services import (
    clear_cached_queries,
    load_feedback_records,
    load_last_group_for_person,
    load_groups,
    load_monthly_menus,
)
from db_connection import feedback_col, groups_col, meals_col, menu_col


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

    if person_name and st.session_state.get("group_name_owner") != person_name:
        suggested_group = load_last_group_for_person(person_name)
        st.session_state["group_name"] = suggested_group
        st.session_state["group_name_owner"] = person_name

    group_name = st.text_input(
        "👥 Group Name (optional)",
        key="group_name",
        placeholder="Enter group name manually (e.g. demo)",
        help="Group list is hidden from regular users. If you know the group name, type it.",
    ).strip()

    if not person_name:
        st.warning("Please enter a name to continue.")
        st.stop()

    logger.info(f"User active | person={person_name} | group={group_name or 'individual'}")
    return person_name, group_name


def render_group_management_section(logger):
    st.divider()
    st.subheader("👥 Group Management (Admin Only)")

    groups = load_groups()

    with st.expander("Create / Update / Delete Groups", expanded=False):
        st.markdown("Use this section to manage reusable groups for meal entries.")

        new_group_name = st.text_input("New Group Name", key="new_group_name").strip()
        new_group_desc = st.text_input("Description (optional)", key="new_group_desc").strip()

        if st.button("➕ Create Group"):
            if not new_group_name:
                st.warning("Group name is required.")
            else:
                groups_col.update_one(
                    {"group_name": new_group_name},
                    {
                        "$setOnInsert": {"created_at": datetime.utcnow()},
                        "$set": {
                            "group_name": new_group_name,
                            "description": new_group_desc or None,
                            "updated_at": datetime.utcnow(),
                        },
                    },
                    upsert=True,
                )
                clear_cached_queries()
                logger.info(f"Group created/updated | group={new_group_name}")
                st.success(f"Group saved: {new_group_name}")
                st.rerun()

        if groups:
            group_names = [g["group_name"] for g in groups]
            selected_group = st.selectbox("Existing Group", group_names, key="existing_group")
            selected_doc = next(g for g in groups if g["group_name"] == selected_group)

            updated_name = st.text_input(
                "Update Group Name",
                value=selected_group,
                key="updated_group_name",
            ).strip()
            updated_desc = st.text_input(
                "Update Description",
                value=selected_doc.get("description") or "",
                key="updated_group_desc",
            ).strip()

            col_u, col_d = st.columns(2)
            with col_u:
                if st.button("✅ Update Group"):
                    if not updated_name:
                        st.warning("Updated group name cannot be empty.")
                    else:
                        groups_col.delete_one({"group_name": selected_group})
                        groups_col.update_one(
                            {"group_name": updated_name},
                            {
                                "$setOnInsert": {"created_at": selected_doc.get("created_at", datetime.utcnow())},
                                "$set": {
                                    "group_name": updated_name,
                                    "description": updated_desc or None,
                                    "updated_at": datetime.utcnow(),
                                },
                            },
                            upsert=True,
                        )
                        meals_col.update_many(
                            {"group_name": selected_group},
                            {"$set": {"group_name": updated_name}},
                        )
                        clear_cached_queries()
                        logger.info(f"Group updated | old={selected_group} | new={updated_name}")
                        st.success("Group updated")
                        st.rerun()

            with col_d:
                if st.button("🗑 Delete Group"):
                    groups_col.delete_one({"group_name": selected_group})
                    meals_col.update_many(
                        {"group_name": selected_group},
                        {"$set": {"group_name": None}},
                    )
                    clear_cached_queries()
                    logger.warning(f"Group deleted | group={selected_group}")
                    st.success("Group deleted. Linked meals moved to Individual.")
                    st.rerun()
        else:
            st.info("No groups yet. Create your first group.")


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


def render_save_and_reset(person_name, group_name, meal_data, logger):
    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Save Record"):
            meals_col.insert_one(
                {
                    "person_name": person_name,
                    "group_name": group_name or None,
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
                f"Meal saved | person={person_name} | group={group_name or 'individual'} | date={meal_data['meal_date']} "
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


def render_monthly_menu_section(person_name, logger):
    st.divider()
    st.subheader("📖 Monthly Menu")

    menu_records = load_monthly_menus()
    menu_by_key = {record["month_key"]: record for record in menu_records}

    current_key = datetime.utcnow().strftime("%Y-%m")
    current_label = datetime.utcnow().strftime("%B %Y")

    current_menu = menu_by_key.get(current_key)
    if current_menu:
        st.markdown(f"**Current Month Menu ({current_label})**")
        st.image(
            current_menu["image_bytes"],
            caption=f"Updated: {current_menu.get('updated_at')} | by {current_menu.get('updated_by', 'N/A')}",
            use_container_width=True,
        )
    else:
        st.info("No menu uploaded for the current month yet.")

    if menu_records:
        labels = [record["month_label"] for record in menu_records]
        key_for_label = {record["month_label"]: record["month_key"] for record in menu_records}
        default_index = 0
        if current_menu:
            default_index = labels.index(menu_by_key[current_key]["month_label"])

        selected_label = st.selectbox("Browse menu by month", labels, index=default_index)
        selected_menu = menu_by_key[key_for_label[selected_label]]
        st.image(
            selected_menu["image_bytes"],
            caption=f"{selected_menu['month_label']} menu",
            use_container_width=True,
        )

    st.markdown("### Upload / Update Monthly Menu")
    selected_month = st.date_input(
        "Select month for menu",
        value=datetime.utcnow().date(),
        key="menu_month",
    )
    uploaded_menu = st.file_uploader(
        "Upload menu image (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        key="menu_uploader",
    )

    if st.button("💾 Save Monthly Menu"):
        if not uploaded_menu:
            st.warning("Please upload an image before saving.")
            return

        month_key = selected_month.strftime("%Y-%m")
        month_label = selected_month.strftime("%B %Y")
        menu_col.update_one(
            {"month_key": month_key},
            {
                "$set": {
                    "month_key": month_key,
                    "month_label": month_label,
                    "image_bytes": uploaded_menu.getvalue(),
                    "image_type": uploaded_menu.type,
                    "updated_at": datetime.utcnow(),
                    "updated_by": person_name,
                }
            },
            upsert=True,
        )

        clear_cached_queries()
        logger.info(f"Monthly menu updated | month={month_key} | by={person_name}")
        st.success(f"Menu saved for {month_label}")
        st.rerun()


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


def _get_default_year_month(df):
    current_year = datetime.utcnow().year
    current_month = datetime.utcnow().month

    years = sorted(df["year"].unique(), reverse=True)
    if current_year in years:
        year_choice = current_year
        months = df[df["year"] == year_choice]["month_num"].unique().tolist()
        month_choice = current_month if current_month in months else max(months)
    else:
        year_choice = years[0]
        month_choice = max(df[df["year"] == year_choice]["month_num"].unique().tolist())

    return year_choice, month_choice


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

        default_year, default_month_num = _get_default_year_month(df)

        col_y, col_m = st.columns(2)

        years = sorted(df["year"].unique(), reverse=True)
        with col_y:
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year))

        months_for_year = (
            df[df["year"] == selected_year][["month_num", "month_name"]]
            .drop_duplicates()
            .sort_values("month_num")
        )

        if months_for_year.empty:
            logger.warning(f"No months found for year {selected_year}")
            st.info("No records found for the selected year.")
        else:
            month_labels = months_for_year["month_name"].tolist()
            month_nums = months_for_year["month_num"].tolist()
            month_index = 0
            if selected_year == default_year and default_month_num in month_nums:
                month_index = month_nums.index(default_month_num)
            else:
                month_index = len(month_labels) - 1

            with col_m:
                selected_month = st.selectbox("Select Month", month_labels, index=month_index)

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




def render_group_payment_summary(all_records_df, logger):
    st.divider()
    st.subheader("👥 Group & Individual Payment Summary")

    if all_records_df.empty:
        st.info("No records available for group/individual summary.")
        return

    work_df = all_records_df.copy()
    work_df["meal_date"] = pd.to_datetime(work_df["meal_date"])
    work_df["year"] = work_df["meal_date"].dt.year
    work_df["month_num"] = work_df["meal_date"].dt.month
    work_df["month_name"] = work_df["meal_date"].dt.strftime("%B")

    default_year, default_month_num = _get_default_year_month(work_df)

    col_y, col_m = st.columns(2)
    years = sorted(work_df["year"].unique(), reverse=True)

    with col_y:
        selected_year = st.selectbox(
            "Payment Year",
            years,
            index=years.index(default_year),
        )

    months_for_year = (
        work_df[work_df["year"] == selected_year][["month_num", "month_name"]]
        .drop_duplicates()
        .sort_values("month_num")
    )

    month_labels = months_for_year["month_name"].tolist()
    month_nums = months_for_year["month_num"].tolist()
    month_index = month_nums.index(default_month_num) if selected_year == default_year and default_month_num in month_nums else len(month_labels) - 1

    with col_m:
        selected_month = st.selectbox("Payment Month", month_labels, index=month_index)

    selected_month_num = months_for_year[months_for_year["month_name"] == selected_month]["month_num"].iloc[0]

    monthly_scope = work_df[(work_df["year"] == selected_year) & (work_df["month_num"] == selected_month_num)].copy()
    if monthly_scope.empty:
        st.info("No monthly payment data found.")
        return

    if "group_name" not in monthly_scope.columns:
        monthly_scope["group_name"] = ""

    monthly_scope["pay_bucket"] = monthly_scope["group_name"].fillna("").astype(str).str.strip()
    monthly_scope["pay_bucket"] = monthly_scope.apply(
        lambda row: row["pay_bucket"] if row["pay_bucket"] else f"Individual - {row['person_name']}",
        axis=1,
    )

    payment_summary = (
        monthly_scope.groupby("pay_bucket")
        .agg(total_meals=("total_meals", "sum"), total_amount=("total_amount", "sum"), members=("person_name", lambda x: ", ".join(sorted(set(x)))))
        .reset_index()
        .rename(columns={"pay_bucket": "payment_target"})
        .sort_values("payment_target")
    )

    st.caption(f"Combined payment view for {selected_month} {selected_year}. Groups are merged; users without a group remain individual.")
    st.dataframe(payment_summary, width="stretch")
    logger.info(f"Rendered group payment summary | month={selected_month} {selected_year} | rows={len(payment_summary)}")

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

    render_group_management_section(logger)

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
