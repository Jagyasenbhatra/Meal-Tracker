import streamlit as st
from datetime import date, datetime
import pandas as pd
from io import BytesIO
from bson.objectid import ObjectId

from db_connection import meals_col, feedback_col

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --------------------
# Page setup
# --------------------
st.set_page_config(page_title="Meal Tracker", layout="centered")
st.title("🍽️ Daily Meal Tracker")

# --------------------
# Session defaults
# --------------------
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

# --------------------
# Reset function
# --------------------
def reset_form():
    for k in ["meal_date", "mode", "lunch", "dinner", "manual_total", "meal_price"]:
        st.session_state.pop(k, None)
    st.rerun()

# --------------------
# Name input
# --------------------
person_name = st.text_input("👤 Person Name", key="person_name").strip()

if not person_name:
    st.warning("Please enter a name to continue.")
    st.stop()

# --------------------
# Input section
# --------------------
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

# --------------------
# Save / Reset
# --------------------
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
        st.success("Record saved!")

with c2:
    if st.button("🔄 Reset"):
        reset_form()

# --------------------
# Summary
# --------------------
st.divider()
st.subheader("📊 Meal Summary (Current Entry)")
st.write(f"**Date:** {meal_date}")
st.write(f"**Total Meals:** {total_meals}")
st.write(f"### 💰 Total Amount: ₹{total_amount}")

# --------------------
# Fetch records
# --------------------
records = list(
    meals_col.find({"person_name": person_name}).sort("meal_date", 1)
)

df = pd.DataFrame(records)

if not df.empty:
    df["_id"] = df["_id"].astype(str)
    df["meal_date"] = pd.to_datetime(df["meal_date"])

# --------------------
# Records table
# --------------------
st.divider()
st.subheader(f"📁 Saved Records — {person_name}")

c1, c2 = st.columns(2)
c1.metric("🍽️ Total Meals", int(df["total_meals"].sum()) if not df.empty else 0)
c2.metric("💰 Total Amount", f"₹{df['total_amount'].sum()}" if not df.empty else "₹0")

st.dataframe(df, width="stretch")

# --------------------
# Export
# --------------------
st.divider()
st.subheader("📤 Export Data")

if not df.empty:
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

# --------------------
# Edit / Delete
# --------------------
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
        edit_price = st.number_input(
            "Edit Price",
            min_value=0.0,
            value=float(record["meal_price"])
        )

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
            st.success("Record updated!")
            st.rerun()

    with u2:
        if st.button("🗑 Delete"):
            meals_col.delete_one({"_id": ObjectId(record_id)})
            st.warning("Record deleted!")
            st.rerun()

# --------------------
# 📆 Month-wise Filter
# --------------------
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

    with col_m:
        months_for_year = (
            df[df["year"] == selected_year]
            [["month_num", "month_name"]]
            .drop_duplicates()
            .sort_values("month_num")
        )

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

    st.subheader(f"📁 Records for {selected_month} {selected_year}")

    c1, c2 = st.columns(2)
    c1.metric("🍽️ Total Meals (Month)", int(monthly_df["total_meals"].sum()))
    c2.metric("💰 Total Amount (Month)", f"₹{monthly_df['total_amount'].sum()}")

    st.dataframe(monthly_df, width="stretch")

else:
    st.info("No records available.")
st.subheader("📤 Export Monthly Data")

if not df.empty and not monthly_df.empty:
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


# --------------------
# Chart
# --------------------
st.divider()
st.subheader("📊 Meals vs Date")
if not df.empty:
    st.line_chart(df.set_index("meal_date")["total_meals"])

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
            st.rerun()
        else:
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
            st.success("Feedback deleted")
            st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
