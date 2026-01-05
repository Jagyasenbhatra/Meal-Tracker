from pymongo import MongoClient
from bson.objectid import ObjectId
import streamlit as st

MONGO_URI = st.secrets["MONGO_URI"]  # or os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["meal_tracker"]
meals_col = db["meals"]
feedback_col = db["feedback"]
