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
    load_monthly_menus,
    prepare_records_dataframe,
)
from db_connection import feedback_col, meals_col, menu_col
from group_services import (
    load_all_groups,
    load_group_members,
    create_group,
    add_member_to_group,
    remove_member_from_group,
    get_group_dataframe,
    clear_group_cache,
)


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
    """Step 1: Enter Group Name

    - If group exists → load it
    - If new group → create it automatically
    """
    st.markdown("### 👥 Group Name")
    group_input = st.text_input(
        "📋 Group Name",
        key="group_input_field",
        placeholder="e.g., demo, office, friends",
        help="Enter group name. New groups are created automatically.",
    ).strip()

    if not group_input:
        st.warning("Please enter a group name to continue.")
        st.stop()

    # Check and create group if needed
    all_groups = load_all_groups()
    if group_input not in all_groups:
        success, message = create_group(group_input, logger)
        if not success:
            st.error(f"❌ {message}")
            st.stop()
        st.success(f"✅ {message}")
        clear_group_cache()
    else:
        st.success(f"✅ Group '{group_input}' loaded!")

    logger.info(f"Group selected: {group_input}")

    # Return group name (person_name will be entered when adding members)
    return None, group_input


def render_group_selection(logger, group_name=None):
    """Render group management interface for the selected group.

    If group_name is provided, shows details for that group.
    Otherwise, allows selecting/creating a group.
    """
    if not group_name:
        st.markdown("### 👥 Group Management")
        group_input = st.text_input(
            "📋 Enter Group Name (or leave empty for individual)",
            key="group_selection_input",
            placeholder="e.g., demo, office, friends",
            help="Enter an existing group name to see its data, or a new name to create it",
        ).strip()

        if not group_input:
            st.info("No group selected. You're tracking meals individually.")
            return None

        # Check if group exists
        all_groups = load_all_groups()
        group_exists = group_input in all_groups

        if group_exists:
            st.success(f"✅ Group '{group_input}' found!")
        else:
            # Auto-create the group
            success, message = create_group(group_input, logger)
            if success:
                st.success(f"✅ {message}")
                clear_group_cache()
            else:
                st.error(f"❌ {message}")
                return None

        group_name = group_input

    # Display group information
    st.markdown(f"### 👥 {group_name.upper()} - Group Details")

    members = load_group_members(group_name)

    # Add member section
    st.markdown("#### ➕ Add Member")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_member = st.text_input(
            "Member Name", key=f"add_member_{group_name}", placeholder="e.g., John"
        ).strip()
    with col2:
        if st.button("Add", key=f"add_btn_{group_name}"):
            if new_member:
                success, msg = add_member_to_group(group_name, new_member, logger)
                if success:
                    st.success(msg)
                    clear_group_cache()
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Enter a member name")

    # Display members
    st.markdown("#### 👥 Current Members")
    if members:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**Total: {len(members)} member(s)**")
            st.write(", ".join(members))

        # Remove member section
        with col2:
            st.markdown("##### Remove")
            member_to_remove = st.selectbox(
                "Select to remove",
                members,
                key=f"remove_{group_name}",
                label_visibility="collapsed",
            )
            if st.button("🗑 Remove", key=f"remove_btn_{group_name}"):
                success, msg = remove_member_from_group(group_name, member_to_remove, logger)
                if success:
                    st.warning(msg)
                    clear_group_cache()
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("No members added yet. Add the first member above!")

    # Display group data if members exist
    if members:
        st.divider()
        st.markdown("#### 📈 Group Statistics")

        # Get meals for group members
        group_meals = list(
            meals_col.find(
                {"person_name": {"$in": members}},
                {
                    "person_name": 1,
                    "meal_date": 1,
                    "lunch": 1,
                    "dinner": 1,
                    "total_meals": 1,
                    "meal_price": 1,
                    "total_amount": 1,
                },
            ).sort("meal_date", -1)
        )

        if group_meals:
            records_df = prepare_records_dataframe(group_meals)

            # Metrics
            col1, col2, col3 = st.columns(3)
            total_meals = records_df["total_meals"].sum()
            total_amount = records_df["total_amount"].sum()

            with col1:
                st.metric("📊 Total Meals", int(total_meals))
            with col2:
                st.metric("💰 Total Amount (₹)", f"{total_amount:.2f}")
            with col3:
                st.metric("📝 Entries", len(records_df))

            # Group summary table
            st.markdown("**Member-wise Summary:**")
            group_df = get_group_dataframe(group_name)
            st.dataframe(group_df, use_container_width=True, hide_index=True)

            # Member filter
            st.markdown("**Individual Member Records:**")
            member_filter = st.selectbox(
                "Filter by member", ["All"] + members, key=f"filter_{group_name}"
            )

            if member_filter == "All":
                display_df = records_df.copy()
            else:
                display_df = records_df[records_df["person_name"] == member_filter].copy()

            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No meal data recorded for this group yet. Start adding meals!")

    return group_name


def render_bulk_meal_entry(group_name, logger):
    """Render bulk meal entry for all group members

    Shows all members with +/- buttons for lunch and dinner
    """
    if not group_name:
        st.warning("No group selected")
        return

    members = load_group_members(group_name)

    if not members:
        st.warning(
            f"No members in group '{group_name}'. Add members in the group details section above."
        )
        return

    st.divider()
    st.markdown("### 🍽️ Record Meals for All Members")

    # Get meal date and price
    col1, col2 = st.columns(2)
    with col1:
        meal_date = st.date_input("📅 Select Date", key="bulk_meal_date")
    with col2:
        meal_price = st.number_input(
            "💰 Price per Meal (₹)", min_value=0.0, step=1.0, key="bulk_meal_price", value=0.0
        )

    st.markdown("#### 🍴 Member Meals")

    # Initialize/Update session state for member meals
    if "member_meals" not in st.session_state:
        st.session_state.member_meals = {}

    # Ensure all current members exist in session state
    for member in members:
        if member not in st.session_state.member_meals:
            st.session_state.member_meals[member] = {"lunch": 0, "dinner": 0}

    # Display each member with +/- buttons - Clear Layout
    member_data = []
    for member in members:
        # Member name header
        st.markdown(f"### 👤 **{member}**")

        # Lunch row
        lunch_col1, lunch_col2, lunch_col3, lunch_col4 = st.columns([1, 0.5, 0.5, 0.5])
        with lunch_col1:
            st.write("🥗 **Lunch**")
        with lunch_col2:
            if st.button("➖", key=f"lunch_minus_{member}", help="Decrease lunch"):
                if st.session_state.member_meals[member]["lunch"] > 0:
                    st.session_state.member_meals[member]["lunch"] -= 1
                st.rerun()
        with lunch_col3:
            lunch_val = st.session_state.member_meals[member]["lunch"]
            st.metric("", lunch_val, label_visibility="collapsed")
        with lunch_col4:
            if st.button("➕", key=f"lunch_plus_{member}", help="Increase lunch"):
                st.session_state.member_meals[member]["lunch"] += 1
                st.rerun()

        # Dinner row
        dinner_col1, dinner_col2, dinner_col3, dinner_col4 = st.columns([1, 0.5, 0.5, 0.5])
        with dinner_col1:
            st.write("🍖 **Dinner**")
        with dinner_col2:
            if st.button("➖", key=f"dinner_minus_{member}", help="Decrease dinner"):
                if st.session_state.member_meals[member]["dinner"] > 0:
                    st.session_state.member_meals[member]["dinner"] -= 1
                st.rerun()
        with dinner_col3:
            dinner_val = st.session_state.member_meals[member]["dinner"]
            st.metric("", dinner_val, label_visibility="collapsed")
        with dinner_col4:
            if st.button("➕", key=f"dinner_plus_{member}", help="Increase dinner"):
                st.session_state.member_meals[member]["dinner"] += 1
                st.rerun()

        st.divider()

        lunch_count = st.session_state.member_meals[member]["lunch"]
        dinner_count = st.session_state.member_meals[member]["dinner"]
        total_meals = lunch_count + dinner_count
        total_amount = total_meals * meal_price

        member_data.append(
            {
                "member": member,
                "lunch": lunch_count,
                "dinner": dinner_count,
                "total_meals": total_meals,
                "total_amount": total_amount,
            }
        )

    # Summary
    st.markdown("#### 📊 Summary")
    col1, col2, col3 = st.columns(3)

    total_group_meals = sum(m["total_meals"] for m in member_data)
    total_group_amount = sum(m["total_amount"] for m in member_data)

    with col1:
        st.metric("📊 Total Meals", int(total_group_meals))
    with col2:
        st.metric("💰 Total Amount (₹)", f"{total_group_amount:.2f}")
    with col3:
        st.metric("👥 Members", len(members))

    # Save button
    if st.button("💾 Save All Meals", key="save_bulk_meals"):
        if meal_price == 0:
            st.error("Please enter a meal price")
            return

        saved_count = 0
        for data in member_data:
            if data["total_meals"] > 0:
                meals_col.insert_one(
                    {
                        "person_name": data["member"],
                        "group_name": group_name,
                        "meal_date": meal_date.isoformat(),
                        "mode": "Auto (Lunch + Dinner)",
                        "lunch": data["lunch"],
                        "dinner": data["dinner"],
                        "total_meals": data["total_meals"],
                        "meal_price": meal_price,
                        "total_amount": data["total_amount"],
                        "created_at": datetime.utcnow(),
                    }
                )
                saved_count += 1

        if saved_count > 0:
            st.success(f"✅ Saved {saved_count} member meal record(s)!")
            logger.info(f"Bulk meal entry saved | group={group_name} | count={saved_count}")
            clear_cached_queries()

            # Reset form - reset values for all members
            for member in members:
                if member in st.session_state.member_meals:
                    st.session_state.member_meals[member] = {"lunch": 0, "dinner": 0}
            st.rerun()
        else:
            st.warning("No meals recorded (all members have 0 meals)")


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

    meal_price = st.number_input("Price per Meal (₹)", min_value=0.0, step=1.0, key="meal_price")
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
                    "lunch": (meal_data["lunch"] if meal_data["mode"].startswith("Auto") else None),
                    "dinner": (
                        meal_data["dinner"] if meal_data["mode"].startswith("Auto") else None
                    ),
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


def render_monthly_menu_section(person_name, group_name, logger):
    st.divider()
    st.subheader("📖 Monthly Menu")

    normalized_group = (group_name or "").strip()
    menu_records = load_monthly_menus(person_name, normalized_group)

    current_key = datetime.utcnow().strftime("%Y-%m")
    current_label = datetime.utcnow().strftime("%B %Y")

    person_current = next(
        (
            record
            for record in menu_records
            if record.get("menu_scope") == "person"
            and record.get("scope_value") == person_name
            and record.get("month_key") == current_key
        ),
        None,
    )

    group_current = None
    if normalized_group:
        group_current = next(
            (
                record
                for record in menu_records
                if record.get("menu_scope") == "group"
                and record.get("scope_value") == normalized_group
                and record.get("month_key") == current_key
            ),
            None,
        )

    if person_current:
        st.markdown(f"**Your Menu ({current_label})**")
        st.image(
            person_current["image_bytes"],
            caption=f"Updated: {person_current.get('updated_at')} | by {person_current.get('updated_by', 'N/A')}",
            use_container_width=True,
        )
    else:
        st.info("No personal menu uploaded for current month.")

    if normalized_group:
        if group_current:
            st.markdown(f"**Your Group Menu ({normalized_group}) — {current_label}**")
            st.image(
                group_current["image_bytes"],
                caption=f"Updated: {group_current.get('updated_at')} | by {group_current.get('updated_by', 'N/A')}",
                use_container_width=True,
            )
        else:
            st.info("No group menu uploaded for current month.")

    if menu_records:
        options = []
        for record in menu_records:
            scope_label = (
                "Personal"
                if record.get("menu_scope") == "person"
                else f"Group ({record.get('scope_value')})"
            )
            label = f"{record['month_label']} — {scope_label}"
            options.append((label, record))

        labels = [label for label, _ in options]
        selected_label = st.selectbox("Browse accessible menus by month", labels, index=0)
        selected_menu = dict(options)[selected_label]

        if st.button("🖼️ Display Selected Month Menu"):
            st.session_state["show_selected_month_menu"] = selected_label

        if st.session_state.get("show_selected_month_menu") == selected_label:
            st.image(
                selected_menu["image_bytes"],
                caption=f"{selected_label}",
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

    menu_scope_options = ["Personal"] + (["Group"] if normalized_group else [])
    selected_scope = st.selectbox("Menu save scope", menu_scope_options, index=0)

    if st.button("💾 Save Monthly Menu"):
        if not uploaded_menu:
            st.warning("Please upload an image before saving.")
            return

        month_key = selected_month.strftime("%Y-%m")
        month_label = selected_month.strftime("%B %Y")
        scope_type = "group" if selected_scope == "Group" else "person"
        scope_value = normalized_group if scope_type == "group" else person_name

        menu_col.update_one(
            {
                "menu_scope": scope_type,
                "scope_value": scope_value,
                "month_key": month_key,
            },
            {
                "$set": {
                    "menu_scope": scope_type,
                    "scope_value": scope_value,
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
        logger.info(
            f"Monthly menu updated | scope={scope_type}:{scope_value} | month={month_key} | by={person_name}"
        )
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
        st.dataframe(paged_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

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
        f"{row['meal_date'].date()} ({row['_id']})": row["_id"] for _, row in df.iterrows()
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

            selected_month_num = months_for_year[months_for_year["month_name"] == selected_month][
                "month_num"
            ].iloc[0]

            monthly_df = df[(df["year"] == selected_year) & (df["month_num"] == selected_month_num)]

            logger.info(
                f"Monthly filter applied | {selected_month} {selected_year} | rows={len(monthly_df)}"
            )

            if monthly_df.empty:
                st.info("No records available for the selected month.")
            else:
                c1, c2 = st.columns(2)
                c1.metric("🍽️ Total Meals (Month)", int(monthly_df["total_meals"].sum()))
                c2.metric(
                    "💰 Total Amount (Month)",
                    f"₹{float(monthly_df['total_amount'].sum())}",
                )
                st.dataframe(monthly_df, use_container_width=True)
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


def render_group_payment_summary(all_records_df, logger, group_name=None):
    st.divider()
    st.subheader("👥 Payment Summary")

    if all_records_df.empty:
        st.info("No records available for payment summary.")
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
    month_index = (
        month_nums.index(default_month_num)
        if selected_year == default_year and default_month_num in month_nums
        else len(month_labels) - 1
    )

    with col_m:
        selected_month = st.selectbox("Payment Month", month_labels, index=month_index)

    selected_month_num = months_for_year[months_for_year["month_name"] == selected_month][
        "month_num"
    ].iloc[0]

    monthly_scope = work_df[
        (work_df["year"] == selected_year) & (work_df["month_num"] == selected_month_num)
    ].copy()
    if monthly_scope.empty:
        st.info("No payment data found for this period.")
        return

    if "group_name" not in monthly_scope.columns:
        monthly_scope["group_name"] = ""

    # If group_name is provided, show detailed breakdown for that group
    if group_name:
        st.markdown(
            f"### 📊 {group_name.upper()} - Payment Breakdown for {selected_month} {selected_year}"
        )

        # Get group data
        group_data = monthly_scope[
            monthly_scope["group_name"].astype(str).str.strip().str.lower()
            == group_name.strip().lower()
        ].copy()

        print(f"**Filtering records for group: '{group_name}'** {group_data}")

        if not group_data.empty:
            # Group totals
            st.markdown("#### 👥 Group Totals")
            group_total_meals = group_data["total_meals"].sum()
            group_total_amount = group_data["total_amount"].sum()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Meals", int(group_total_meals))
            with col2:
                st.metric("💰 Total Payment (₹)", f"{group_total_amount:.2f}")
            with col3:
                st.metric("👥 Members", group_data["person_name"].nunique())

            # Individual breakdown within group
            st.markdown("#### 👤 Individual Member Breakdown")
            individual_summary = (
                group_data.groupby("person_name")
                .agg(
                    Meals=("total_meals", "sum"),
                    Amount=("total_amount", "sum"),
                    Entries=("total_meals", "count"),
                )
                .reset_index()
                .rename(columns={"person_name": "Member"})
                .sort_values("Member")
            )

            individual_summary["Amount"] = individual_summary["Amount"].round(2)
            individual_summary = individual_summary[["Member", "Meals", "Amount", "Entries"]]
            st.dataframe(individual_summary, use_container_width=True, hide_index=True)
        else:
            st.warning(
                f"No data found for group '{group_name}' in {selected_month} {selected_year}"
            )
    else:
        # Show combined view if no specific group
        monthly_scope["pay_bucket"] = monthly_scope["group_name"].fillna("").astype(str).str.strip()
        monthly_scope["pay_bucket"] = monthly_scope.apply(
            lambda row: (
                row["pay_bucket"] if row["pay_bucket"] else f"Individual - {row['person_name']}"
            ),
            axis=1,
        )

        payment_summary = (
            monthly_scope.groupby("pay_bucket")
            .agg(
                total_meals=("total_meals", "sum"),
                total_amount=("total_amount", "sum"),
                members=("person_name", lambda x: ", ".join(sorted(set(x)))),
            )
            .reset_index()
            .rename(columns={"pay_bucket": "payment_target"})
            .sort_values("payment_target")
        )

        st.caption(
            f"Combined payment view for {selected_month} {selected_year}. Groups are merged; users without a group remain individual."
        )
        st.dataframe(payment_summary, use_container_width=True)

    logger.info(
        f"Rendered payment summary | month={selected_month} {selected_year} | group={group_name or 'all'}"
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
    st.dataframe(monthly, use_container_width=True)

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
        st.dataframe(fb_df, use_container_width=True)

        fb_map = {
            f"{row['person_name']} | {row['created_at']}": row["_id"] for _, row in fb_df.iterrows()
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


def render_group_management(logger):
    """Render group management interface"""
    st.divider()
    st.subheader("👥 Group Management")

    # Tab for creating new group or managing existing
    tab1, tab2 = st.tabs(["Create/Select Group", "Manage Members"])

    with tab1:
        st.markdown("#### Create New Group")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_group_name = st.text_input(
                "New Group Name", key="new_group_name", placeholder="e.g., demo, office, friends"
            )
        with col2:
            if st.button("➕ Create Group"):
                if new_group_name:
                    success, message = create_group(new_group_name, logger)
                    if success:
                        st.success(message)
                        clear_group_cache()
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter a group name")

        st.markdown("#### Select Existing Group")
        all_groups = load_all_groups()
        if all_groups:
            selected_group = st.selectbox("Choose a group", all_groups, key="selected_group_view")

            if selected_group:
                members = load_group_members(selected_group)
                st.info(f"**{selected_group}** has {len(members)} member(s)")

                if members:
                    st.markdown(f"**Members:** {', '.join(members)}")

                    # Show group statistics
                    st.markdown("#### Group Statistics")
                    group_df = get_group_dataframe(selected_group)
                    if not group_df.empty:
                        st.dataframe(group_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("This group has no members yet")
        else:
            st.info("No groups created yet. Create one above!")

    with tab2:
        st.markdown("#### Manage Group Members")
        all_groups = load_all_groups()
        if all_groups:
            selected_group = st.selectbox(
                "Choose a group to manage", all_groups, key="selected_group_manage"
            )

            if selected_group:
                members = load_group_members(selected_group)

                # Add member
                st.markdown("##### Add Member")
                col1, col2 = st.columns([3, 1])
                with col1:
                    member_name = st.text_input(
                        "Member Name",
                        key=f"member_name_{selected_group}",
                        placeholder="e.g., John, Alice",
                    )
                with col2:
                    if st.button("✅ Add Member"):
                        if member_name:
                            success, message = add_member_to_group(
                                selected_group, member_name, logger
                            )
                            if success:
                                st.success(message)
                                clear_group_cache()
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Please enter a member name")

                # Remove member
                if members:
                    st.markdown("##### Remove Member")
                    member_to_remove = st.selectbox(
                        "Select member to remove", members, key=f"remove_member_{selected_group}"
                    )

                    if st.button("🗑 Remove Member"):
                        success, message = remove_member_from_group(
                            selected_group, member_to_remove, logger
                        )
                        if success:
                            st.warning(message)
                            clear_group_cache()
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.info("No members in this group yet")
        else:
            st.info("No groups available. Create one first!")


def render_group_data_view(logger):
    """Render a view to see all data for a specific group"""
    st.divider()
    st.subheader("📊 View Group Data")

    all_groups = load_all_groups()
    if not all_groups:
        st.info("No groups created yet. Create one in the Group Management section.")
        return

    selected_group = st.selectbox("Select group to view data", all_groups, key="group_data_view")

    if selected_group:
        members = load_group_members(selected_group)

        if not members:
            st.warning(f"Group '{selected_group}' has no members yet")
            return

        # Get meals for group members
        group_meals = list(
            meals_col.find(
                {"person_name": {"$in": members}},
                {
                    "person_name": 1,
                    "meal_date": 1,
                    "lunch": 1,
                    "dinner": 1,
                    "total_meals": 1,
                    "meal_price": 1,
                    "total_amount": 1,
                },
            ).sort("meal_date", -1)
        )

        if not group_meals:
            st.info(f"No meal data recorded for group '{selected_group}' yet")
            return

        # Prepare dataframe
        records_df = prepare_records_dataframe(group_meals)

        # Group statistics
        col1, col2, col3 = st.columns(3)

        total_meals = records_df["total_meals"].sum()
        total_amount = records_df["total_amount"].sum()
        num_members = len(members)

        with col1:
            st.metric("Total Meals", int(total_meals))
        with col2:
            st.metric("Total Amount (₹)", f"{total_amount:.2f}")
        with col3:
            st.metric("Members", num_members)

        # Display group dataframe
        st.markdown("#### Group Summary")
        group_df = get_group_dataframe(selected_group)
        st.dataframe(group_df, use_container_width=True, hide_index=True)

        # Individual member meals
        st.markdown("#### Member-wise Meal Records")
        member_filter = st.selectbox(
            "Filter by member", ["All"] + members, key="member_filter_meals"
        )

        if member_filter == "All":
            display_df = records_df.copy()
        else:
            display_df = records_df[records_df["person_name"] == member_filter].copy()

        if not display_df.empty:
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No records found for selected filter")
