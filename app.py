import streamlit as st
from datetime import date, datetime
import pandas as pd
from io import BytesIO
from bson.objectid import ObjectId
from logger import get_logger
from db_connection import meals_col, feedback_col


logger =get_logger()

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title="Meal Tracker", layout="centered")
st.title("🍽️ Daily Meal Tracker")

logger.info("Application started")

# ======================================================
# Session defaults
# ======================================================
defaults = {
    "person_name": "",
    "meal_date": date.today(),
    "mode": "Auto (Lunch + Dinner)",
    "lunch": 0,
    "dinner": 0,
    "manual_total": 0,
    "meal_price": 0.0,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

st.session_state.setdefault("admin_authenticated", False)

# ======================================================
# Reset
# ======================================================
def reset_form():
    logger.info("Form reset")
    for k in ["meal_date", "mode", "lunch", "dinner", "manual_total", "meal_price"]:
        st.session_state.pop(k, None)
    st.rerun()

# ======================================================
# Name input
# ======================================================
person_name = st.text_input("👤 Person Name", key="person_name").strip()

if not person_name:
    st.warning("Please enter a name to continue.")
    st.stop()

logger.info(f"User active | person={person_name}")

# ======================================================
# Input section
# ======================================================
meal_date = st.date_input("Select Date", key="meal_date")

mode = st.radio(
    "Meal Count Mode",
    ["Auto (Lunch + Dinner)", "Manual (Total Meals)"],
    key="mode"
)

if mode.startswith("Auto"):
    c1, c2 = st.columns(2)
    with c1:
        lunch = st.number_input("Lunch Meals", min_value=0, step=1, key="lunch")
    with c2:
        dinner = st.number_input("Dinner Meals", min_value=0, step=1, key="dinner")
    total_meals = lunch + dinner
else:
    total_meals = st.number_input("Total Meals", min_value=0, step=1, key="manual_total")

meal_price = st.number_input("Price per Meal (₹)", min_value=0.0, step=1.0, key="meal_price")
total_amount = total_meals * meal_price

# ======================================================
# Save / Reset
# ======================================================
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 Save Record"):
        meals_col.insert_one({
            "person_name": person_name,
            "meal_date": meal_date.isoformat(),
            "mode": mode,
            "lunch": lunch if mode.startswith("Auto") else None,
            "dinner": dinner if mode.startswith("Auto") else None,
            "total_meals": total_meals,
            "meal_price": meal_price,
            "total_amount": total_amount,
            "created_at": datetime.utcnow()
        })

        logger.info(
            f"Meal saved | person={person_name} | date={meal_date} "
            f"| meals={total_meals} | amount={total_amount}"
        )

        st.success("Record saved!")

with c2:
    if st.button("🔄 Reset"):
        reset_form()

# ======================================================
# Summary (current entry)
# ======================================================
st.divider()
st.subheader("📊 Meal Summary (Current Entry)")
st.write(f"**Date:** {meal_date}")
st.write(f"**Total Meals:** {total_meals}")
st.write(f"### 💰 Total Amount: ₹{total_amount}")

logger.info("Displayed current entry summary")

# ======================================================
# Fetch records
# ======================================================
records = list(
    meals_col.find({"person_name": person_name}).sort("meal_date", 1)
)
logger.info(f"Fetched records | count={len(records)}")

df = pd.DataFrame(records)

if not df.empty:
    df["_id"] = df["_id"].astype(str)
    df["meal_date"] = pd.to_datetime(df["meal_date"])

# ======================================================
# Records table
# ======================================================
st.divider()
st.subheader(f"📁 Saved Records — {person_name}")

c1, c2 = st.columns(2)
c1.metric("🍽️ Total Meals", int(df["total_meals"].sum()) if not df.empty else 0)
c2.metric("💰 Total Amount", f"₹{df['total_amount'].sum()}" if not df.empty else "₹0")

st.dataframe(df, width="stretch")

logger.info("Displayed records table")

# ======================================================
# Export (All data)
# ======================================================
st.divider()
st.subheader("📤 Export Data")

if not df.empty:
    logger.info(f"Export all data triggered | rows={len(df)}")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_meals.csv"
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "⬇️ Download Excel",
        buffer.getvalue(),
        file_name=f"{person_name}_meals.xlsx"
    )

# ======================================================
# Edit / Delete
# ======================================================
st.divider()
st.subheader("✏️ Edit / 🗑 Delete Record")

if not df.empty:
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
                {"$set": {
                    "lunch": edit_lunch,
                    "dinner": edit_dinner,
                    "total_meals": edit_total,
                    "meal_price": edit_price,
                    "total_amount": edit_amount
                }}
            )

            logger.info(f"Meal updated | id={record_id}")
            st.success("Record updated!")
            st.rerun()

    with u2:
        if st.button("🗑 Delete"):
            meals_col.delete_one({"_id": ObjectId(record_id)})
            logger.warning(f"Meal deleted | id={record_id}")
            st.warning("Record deleted!")
            st.rerun()
# ======================================================
# Month-wise Filter
# ======================================================
st.divider()
st.subheader("📆 Filter Records by Month")

if not df.empty:
    df["year"] = df["meal_date"].dt.year
    df["month_num"] = df["meal_date"].dt.month
    df["month_name"] = df["meal_date"].dt.strftime("%B")

    col_y, col_m = st.columns(2)

    with col_y:
        selected_year = st.selectbox(
            "Select Year",
            sorted(df["year"].unique(), reverse=True)
        )

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
            selected_month = st.selectbox(
                "Select Month",
                months_for_year["month_name"].tolist()
            )

        selected_month_num = months_for_year[
            months_for_year["month_name"] == selected_month
        ]["month_num"].iloc[0]

        monthly_df = df[
            (df["year"] == selected_year) &
            (df["month_num"] == selected_month_num)
        ]

        logger.info(
            f"Monthly filter applied | {selected_month} {selected_year} | rows={len(monthly_df)}"
        )

        if monthly_df.empty:
            st.info("No records available for the selected month.")
        else:
            # Monthly totals
            c1, c2 = st.columns(2)
            c1.metric(
                "🍽️ Total Meals (Month)",
                int(monthly_df["total_meals"].sum())
            )
            c2.metric(
                "💰 Total Amount (Month)",
                f"₹{float(monthly_df['total_amount'].sum())}"
            )

            st.dataframe(monthly_df, width="stretch")

else:
    logger.info("Monthly filter skipped — no data available")
    st.info("No records available.")


# ======================================================
# Export Monthly
# ======================================================
st.subheader("📤 Export Monthly Data")

if not df.empty and not monthly_df.empty:
    logger.info("Monthly export triggered")

    st.download_button(
        "⬇️ Download Monthly CSV",
        monthly_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_{selected_year}_{selected_month}.csv"
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        monthly_df.to_excel(writer, index=False)

    st.download_button(
        "⬇️ Download Monthly Excel",
        buffer.getvalue(),
        file_name=f"{person_name}_{selected_year}_{selected_month}.xlsx"
    )

# ======================================================
# Chart
# ======================================================
st.divider()
st.subheader("📊 Meals vs Date")

if not df.empty:
    logger.info("Rendered meals vs date chart")
    st.line_chart(df.set_index("meal_date")["total_meals"])

# ======================================================
# Monthly Summary (All Months)
# ======================================================
st.divider()
st.subheader("📆 Monthly Summary")

if not df.empty:
    df["month"] = df["meal_date"].dt.to_period("M").astype(str)

    monthly = (
        df.groupby("month")
        .agg(
            total_meals=("total_meals", "sum"),
            total_amount=("total_amount", "sum")
        )
        .reset_index()
        .sort_values("month")
    )

    logger.info("Generated monthly summary")
    st.dataframe(monthly, width="stretch")

    # Export summary
    logger.info("Monthly summary export triggered")

    st.download_button(
        "⬇️ Download Monthly Summary CSV",
        monthly.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_monthly_summary.csv"
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        monthly.to_excel(writer, index=False)

    st.download_button(
        "⬇️ Download Monthly Summary Excel",
        buffer.getvalue(),
        file_name=f"{person_name}_monthly_summary.xlsx"
    )

# ======================================================
# Feedback
# ======================================================
st.divider()
st.header("📝 Feedback")

with st.form("feedback_form"):
    msg = st.text_area("Your feedback")
    rating = st.slider("Rating", 1, 5, 4)

    if st.form_submit_button("📨 Submit"):
        if msg.strip():
            feedback_col.insert_one({
                "person_name": person_name,
                "message": msg.strip(),
                "rating": rating,
                "created_at": datetime.utcnow()
            })

            logger.info(f"Feedback submitted | rating={rating}")
            st.success("Thanks for the feedback 🙌")

# ======================================================
# Admin Panel
# ======================================================
st.divider()
st.header("🔐 Admin Feedback Panel")

if not st.session_state.admin_authenticated:
    pwd = st.text_input("Admin Password", type="password")
    if st.button("🔓 Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            logger.info("Admin login successful")
            st.rerun()
        else:
            logger.warning("Admin login failed")
            st.error("Incorrect password")
else:
    fb_df = pd.DataFrame(list(feedback_col.find().sort("created_at", -1)))

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
            st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        logger.info("Admin logged out")
        st.rerun()
