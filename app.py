import streamlit as st
from datetime import date
import sqlite3
import pandas as pd

# --------------------
# Page setup
# --------------------
st.set_page_config(page_title="Meal Calculator", layout="centered")
st.title("🍽️ Daily Meal Calculator")

# --------------------
# Session defaults
# --------------------
if "meal_date" not in st.session_state:
    st.session_state.meal_date = date.today()
if "mode" not in st.session_state:
    st.session_state.mode = "Auto (Lunch + Dinner)"
if "lunch" not in st.session_state:
    st.session_state.lunch = 0
if "dinner" not in st.session_state:
    st.session_state.dinner = 0
if "manual_total" not in st.session_state:
    st.session_state.manual_total = 0
if "meal_price" not in st.session_state:
    st.session_state.meal_price = 0.0

# --------------------
# Reset function
# --------------------
def reset_form():
    st.session_state.meal_date = date.today()
    st.session_state.mode = "Auto (Lunch + Dinner)"
    st.session_state.lunch = 0
    st.session_state.dinner = 0
    st.session_state.manual_total = 0
    st.session_state.meal_price = 0.0

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
# Input section
# --------------------
meal_date = st.date_input(
    "Select Date",
    value=st.session_state.meal_date,
    key="meal_date"
)

mode = st.radio(
    "Meal Count Mode",
    ["Auto (Lunch + Dinner)", "Manual (Total Meals)"],
    key="mode"
)

if mode == "Auto (Lunch + Dinner)":
    col1, col2 = st.columns(2)
    with col1:
        lunch = st.number_input("Lunch Meals", min_value=0, step=1, key="lunch")
    with col2:
        dinner = st.number_input("Dinner Meals", min_value=0, step=1, key="dinner")
    total_meals = lunch + dinner
else:
    total_meals = st.number_input(
        "Total Meals",
        min_value=0,
        step=1,
        key="manual_total"
    )

meal_price = st.number_input(
    "Price per Meal (₹)",
    min_value=0.0,
    step=1.0,
    key="meal_price"
)

total_amount = total_meals * meal_price

# --------------------
# Action buttons
# --------------------
col_save, col_reset = st.columns(2)

with col_save:
    if st.button("💾 Save Record"):
        cursor.execute("""
            INSERT INTO meals (
                meal_date, mode, lunch, dinner,
                total_meals, meal_price, total_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(meal_date),
            mode,
            lunch if mode.startswith("Auto") else None,
            dinner if mode.startswith("Auto") else None,
            total_meals,
            meal_price,
            total_amount
        ))
        conn.commit()
        st.success("Record saved successfully!")

with col_reset:
    if st.button("🔄 Reset"):
        reset_form()
        st.rerun()

# --------------------
# Summary
# --------------------
st.divider()
st.subheader("📊 Meal Summary")
st.write(f"**Date:** {meal_date}")
st.write(f"**Total Meals:** {total_meals}")
st.write(f"### 💰 Total Amount: ₹{total_amount}")

# --------------------
# Records table
# --------------------
st.divider()
st.subheader("📁 Saved Records")

df = pd.read_sql(
    "SELECT * FROM meals ORDER BY meal_date DESC",
    conn
)

st.dataframe(df, width="stretch")

# --------------------
# Edit / Delete section
# --------------------
st.divider()
st.subheader("✏️ Edit / 🗑 Delete Record")

if not df.empty:
    record_map = {
        f"{row['meal_date']} (ID {row['id']})": row["id"]
        for _, row in df.iterrows()
    }

    selected = st.selectbox("Select a record", record_map.keys())
    record_id = record_map[selected]
    record = df[df["id"] == record_id].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        edit_lunch = st.number_input(
            "Edit Lunch Meals",
            min_value=0,
            value=record["lunch"] if record["lunch"] else 0
        )
        edit_dinner = st.number_input(
            "Edit Dinner Meals",
            min_value=0,
            value=record["dinner"] if record["dinner"] else 0
        )

    with col2:
        edit_price = st.number_input(
            "Edit Price per Meal (₹)",
            min_value=0.0,
            value=record["meal_price"]
        )

    edit_total_meals = edit_lunch + edit_dinner
    edit_total_amount = edit_total_meals * edit_price

    st.info(f"Updated Meals: {edit_total_meals}")
    st.info(f"Updated Amount: ₹{edit_total_amount}")

    col_update, col_delete = st.columns(2)

    with col_update:
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

    with col_delete:
        if st.button("🗑 Delete Record"):
            cursor.execute("DELETE FROM meals WHERE id=?", (record_id,))
            conn.commit()
            st.warning("Record deleted!")
            st.rerun()
else:
    st.info("No records found.")
