import streamlit as st
from datetime import date,datetime
import sqlite3
import pandas as pd
from io import BytesIO
import os


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
    if k not in st.session_state:
        st.session_state[k] = v


if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# --------------------
# Reset function
# --------------------
def reset_form():
    for k in ["meal_date", "mode", "lunch", "dinner", "manual_total", "meal_price"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# --------------------
# DB connection
# --------------------
conn = sqlite3.connect("meals.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_date TEXT,
    mode TEXT,
    lunch INTEGER,
    dinner INTEGER,
    total_meals INTEGER,
    meal_price REAL,
    total_amount REAL
)
""")
conn.commit()

# --------------------
# DB migration (ADD person_name)
# --------------------
cursor.execute("PRAGMA table_info(meals)")
cols = [c[1] for c in cursor.fetchall()]
if "person_name" not in cols:
    cursor.execute("ALTER TABLE meals ADD COLUMN person_name TEXT")
    conn.commit()

# --------------------
# Name input
# --------------------
person_name = st.text_input(
    "👤 Person Name",
    placeholder="Enter name",
    key="person_name"
).strip()

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

if mode == "Auto (Lunch + Dinner)":
    c1, c2 = st.columns(2)
    with c1:
        lunch = st.number_input("Lunch Meals", min_value=0, step=1, key="lunch")
    with c2:
        dinner = st.number_input("Dinner Meals", min_value=0, step=1, key="dinner")
    total_meals = lunch + dinner
else:
    total_meals = st.number_input(
        "Total Meals", min_value=0, step=1, key="manual_total"
    )

meal_price = st.number_input(
    "Price per Meal (₹)", min_value=0.0, step=1.0, key="meal_price"
)

total_amount = total_meals * meal_price

# --------------------
# Action buttons
# --------------------
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 Save Record"):
        cursor.execute("""
            INSERT INTO meals (
                person_name, meal_date, mode, lunch, dinner,
                total_meals, meal_price, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            person_name,
            str(meal_date),
            mode,
            lunch if mode.startswith("Auto") else None,
            dinner if mode.startswith("Auto") else None,
            total_meals,
            meal_price,
            total_amount
        ))
        conn.commit()
        st.success("Record saved!")

with c2:
    if st.button("🔄 Reset"):
        reset_form()

# --------------------
# Current summary
# --------------------
st.divider()
st.subheader("📊 Meal Summary (Current Entry)")
st.write(f"**Date:** {meal_date}")
st.write(f"**Total Meals:** {total_meals}")
st.write(f"### 💰 Total Amount: ₹{total_amount}")

# --------------------
# Records per person
# --------------------
st.divider()
st.subheader(f"📁 Saved Records — {person_name}")

df = pd.read_sql(
    "SELECT * FROM meals WHERE person_name=? ORDER BY meal_date",
    conn,
    params=(person_name,)
)

df["meal_date"] = pd.to_datetime(df["meal_date"])

# ---- Totals ----
c1, c2 = st.columns(2)
c1.metric("🍽️ Total Meals", int(df["total_meals"].sum()) if not df.empty else 0)
c2.metric("💰 Total Amount", f"₹{float(df['total_amount'].sum()) if not df.empty else 0}")

st.dataframe(df, width="stretch")

# --------------------
# ✏️ Edit / 🗑 Delete (FIXED — ID BASED)
# --------------------
st.divider()
st.subheader("✏️ Edit / 🗑 Delete Record")

if not df.empty:
    record_map = {
        f"{row['meal_date'].date()} (ID {row['id']})": row["id"]
        for _, row in df.iterrows()
    }

    selected_label = st.selectbox("Select Record", record_map.keys())
    record_id = record_map[selected_label]

    record = df[df["id"] == record_id].iloc[0]

    ec1, ec2 = st.columns(2)
    with ec1:
        edit_lunch = st.number_input(
            "Edit Lunch Meals", min_value=0, value=int(record["lunch"] or 0)
        )
        edit_dinner = st.number_input(
            "Edit Dinner Meals", min_value=0, value=int(record["dinner"] or 0)
        )
    with ec2:
        edit_price = st.number_input(
            "Edit Price per Meal (₹)",
            min_value=0.0,
            value=float(record["meal_price"])
        )

    edit_total_meals = edit_lunch + edit_dinner
    edit_total_amount = edit_total_meals * edit_price

    st.info(f"Updated Meals: {edit_total_meals}")
    st.info(f"Updated Amount: ₹{edit_total_amount}")

    u1, u2 = st.columns(2)
    with u1:
        if st.button("✅ Update Record"):
            cursor.execute("""
                UPDATE meals
                SET lunch=?, dinner=?, total_meals=?, meal_price=?, total_amount=?
                WHERE id=?
            """, (
                edit_lunch,
                edit_dinner,
                edit_total_meals,
                edit_price,
                edit_total_amount,
                record_id
            ))
            conn.commit()
            st.success("Record updated!")
            st.rerun()

    with u2:
        if st.button("🗑 Delete Record"):
            cursor.execute("DELETE FROM meals WHERE id=?", (record_id,))
            conn.commit()
            st.warning("Record deleted!")
            st.rerun()
else:
    st.info("No records available.")

# --------------------
# 📊 Chart
# --------------------
st.divider()
st.subheader("📊 Meals vs Date")
if not df.empty:
    st.line_chart(df.set_index("meal_date")["total_meals"])
else:
    st.info("No data available.")

# --------------------
# 📆 Monthly Summary
# --------------------
st.divider()
st.subheader("📆 Monthly Summary")
if not df.empty:
    df["month"] = df["meal_date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").agg(
        total_meals=("total_meals", "sum"),
        total_amount=("total_amount", "sum")
    ).reset_index()
    st.dataframe(monthly, width="stretch")
else:
    st.info("No data available.")

# --------------------
# 📤 Export
# --------------------
st.divider()
st.subheader("📤 Export Data")

if not df.empty:
    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{person_name}_meals.csv",
        mime="text/csv"
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        "⬇️ Download Excel",
        buffer.getvalue(),
        file_name=f"{person_name}_meals.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No data available to export.")


# # ======================================================
# # 📝 FEEDBACK SECTION
# # ======================================================
# st.divider()
# st.header("📝 Feedback / Suggestions")

# with st.form("feedback_form"):
#     feedback_text = st.text_area(
#         "Your feedback (feature request / issue / suggestion)",
#         placeholder="Example: Add monthly bill export, improve UI..."
#     )
#     rating = st.slider("Overall Experience Rating", 1, 5, 4)

#     submitted = st.form_submit_button("📨 Submit Feedback")

#     if submitted:
#         if not feedback_text.strip():
#             st.warning("Feedback message cannot be empty.")
#         else:
#             cursor.execute("""
#                 INSERT INTO feedback (person_name, message, rating, created_at)
#                 VALUES (?, ?, ?, ?)
#             """, (
#                 person_name,
#                 feedback_text.strip(),
#                 rating,
#                 datetime.now().isoformat()
#             ))
#             conn.commit()
#             st.success("Thank you! Your feedback has been saved 🙌")

# # ======================================================
# # 🛠️ DEVELOPER / ADMIN FEEDBACK VIEW
# # ======================================================
# st.divider()
# st.header("🛠️ Developer Feedback Inbox")

# feedback_df = pd.read_sql(
#     "SELECT * FROM feedback ORDER BY created_at DESC",
#     conn
# )

# if not feedback_df.empty:
#     st.dataframe(feedback_df, width="stretch")

#     feedback_map = {
#         f"{row['person_name']} | {row['created_at']}": row["id"]
#         for _, row in feedback_df.iterrows()
#     }

#     selected_fb = st.selectbox(
#         "Select feedback to delete (after review)",
#         feedback_map.keys()
#     )

#     if st.button("🗑 Delete Selected Feedback"):
#         cursor.execute(
#             "DELETE FROM feedback WHERE id=?",
#             (feedback_map[selected_fb],)
#         )
#         conn.commit()
#         st.success("Feedback deleted.")
#         st.rerun()
# else:
#     st.info("No feedback submitted yet.")

# ======================================================
# 📝 FEEDBACK (USER)
# ======================================================
st.divider()
st.header("📝 Feedback / Suggestions")

with st.form("feedback_form"):
    feedback_text = st.text_area(
        "Your feedback (feature request / issue / suggestion)",
        placeholder="Example: Add PDF bill, monthly export..."
    )
    rating = st.slider("Overall Experience Rating", 1, 5, 4)

    if st.form_submit_button("📨 Submit Feedback"):
        if not feedback_text.strip():
            st.warning("Feedback message cannot be empty.")
        else:
            cursor.execute("""
                INSERT INTO feedback (person_name, message, rating, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                person_name,
                feedback_text.strip(),
                rating,
                datetime.now().isoformat()
            ))
            conn.commit()
            st.success("Thank you! Feedback saved 🙌")

# ======================================================
# 🔐 ADMIN FEEDBACK PANEL
# ======================================================
st.divider()
st.header("🔐 Admin Feedback Panel")

if not st.session_state.admin_authenticated:
    admin_pass = st.text_input("Enter Admin Password", type="password")

    if st.button("🔓 Login as Admin"):
        if admin_pass == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.success("Admin access granted")
            st.rerun()
        else:
            st.error("Incorrect password")
else:
    st.success("Logged in as Admin")

    feedback_df = pd.read_sql(
        "SELECT * FROM feedback ORDER BY created_at DESC",
        conn
    )

    if not feedback_df.empty:
        st.dataframe(feedback_df, width="stretch")

        fb_map = {
            f"{row['person_name']} | {row['created_at']}": row["id"]
            for _, row in feedback_df.iterrows()
        }

        selected_fb = st.selectbox("Select feedback to delete", fb_map.keys())

        if st.button("🗑 Delete Selected Feedback"):
            cursor.execute("DELETE FROM feedback WHERE id=?", (fb_map[selected_fb],))
            conn.commit()
            st.success("Feedback deleted")
            st.rerun()
    else:
        st.info("No feedback available.")

    if st.button("🚪 Logout Admin"):
        st.session_state.admin_authenticated = False
        st.rerun()
