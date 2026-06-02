import pandas as pd
import streamlit as st
from datetime import datetime

from db_connection import groups_col, meals_col
from errors import (
    QueryError,
    GroupNotFoundError,
    MemberAlreadyExistsError,
    MemberNotFoundError,
)
from validators import (
    validate_group_name,
    validate_member_name,
    ValidationError,
)
from config import CACHE_TTL_GROUPS


@st.cache_data(ttl=CACHE_TTL_GROUPS, show_spinner=False)
def load_all_groups():
    """Load all group names with error handling"""
    try:
        groups = list(groups_col.find({}, {"group_name": 1}).sort("group_name", 1))
        return [g["group_name"] for g in groups]
    except Exception as e:
        raise QueryError(str(e), operation="load_all_groups")


def load_group_members(group_name: str):
    """Load members of a specific group - NO CACHE to show real-time updates"""
    try:
        group = groups_col.find_one({"group_name": group_name})
        if group:
            members = group.get("members", [])
            if "other" not in members:
                members.append("other")
            return members
        return ["other"]
    except Exception as e:
        raise QueryError(str(e), operation="load_group_members")


def clear_group_cache():
    """Clear the groups cache to show real-time updates"""
    st.cache_data.clear()


def create_group(group_name: str, logger):
    """Create a new group with validation and error handling"""
    try:
        # Validate input
        group_name = validate_group_name(group_name)

    except ValidationError as e:
        return False, str(e)

    try:
        existing = groups_col.find_one({"group_name": group_name})
        if existing:
            return False, f"Group '{group_name}' already exists"

        groups_col.insert_one(
            {
                "group_name": group_name,
                "members": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        logger.info(f"Created group: {group_name}")
        return True, f"Group '{group_name}' created successfully"

    except Exception as e:
        logger.error(f"Failed to create group '{group_name}': {str(e)}")
        return False, f"Failed to create group. Please try again."


def add_member_to_group(group_name: str, member_name: str, logger):
    """Add a member to a group with validation and error handling"""
    try:
        # Validate inputs
        group_name = validate_group_name(group_name)
        member_name = validate_member_name(member_name)

    except ValidationError as e:
        return False, str(e)

    try:
        group = groups_col.find_one({"group_name": group_name})
        if not group:
            return False, f"Group '{group_name}' not found"

        members = group.get("members", [])
        if member_name in members:
            return False, f"Member '{member_name}' already exists in this group"

        members.append(member_name)
        groups_col.update_one(
            {"group_name": group_name},
            {
                "$set": {
                    "members": members,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        logger.info(f"Added member '{member_name}' to group '{group_name}'")
        return True, f"Member '{member_name}' added successfully"

    except Exception as e:
        logger.error(f"Failed to add member to group: {str(e)}")
        return False, f"Failed to add member. Please try again."


def remove_member_from_group(group_name: str, member_name: str, logger):
    """Remove a member from a group with error handling"""
    try:
        # Validate inputs
        group_name = validate_group_name(group_name)
        member_name = validate_member_name(member_name)

    except ValidationError as e:
        return False, str(e)

    try:
        group = groups_col.find_one({"group_name": group_name})
        if not group:
            return False, f"Group '{group_name}' not found"

        members = group.get("members", [])
        if member_name not in members:
            return False, f"Member '{member_name}' not found in this group"

        members.remove(member_name)
        groups_col.update_one(
            {"group_name": group_name},
            {
                "$set": {
                    "members": members,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        logger.info(f"Removed member '{member_name}' from group '{group_name}'")
        return True, f"Member '{member_name}' removed successfully"

    except Exception as e:
        logger.error(f"Failed to remove member from group: {str(e)}")
        return False, f"Failed to remove member. Please try again."


def get_group_statistics(group_name: str):
    """Get statistics for a group with error handling"""
    try:
        members = load_group_members(group_name)

        if not members:
            return {
                "members": [],
                "member_stats": [],
                "group_total_meals": 0,
                "group_total_amount": 0,
            }

        # Get all meals for group members
        pipeline = [
            {"$match": {"person_name": {"$in": members}}},
            {
                "$group": {
                    "_id": "$person_name",
                    "total_meals": {"$sum": "$total_meals"},
                    "total_amount": {"$sum": "$total_amount"},
                    "meal_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        member_stats = list(meals_col.aggregate(pipeline))

        # Calculate group totals
        group_total_meals = sum(m.get("total_meals", 0) for m in member_stats)
        group_total_amount = sum(m.get("total_amount", 0) for m in member_stats)

        return {
            "members": members,
            "member_stats": member_stats,
            "group_total_meals": group_total_meals,
            "group_total_amount": group_total_amount,
        }

    except Exception as e:
        raise QueryError(str(e), operation="get_group_statistics")


def get_group_dataframe(group_name: str):
    """Get group statistics as a DataFrame with error handling"""
    try:
        stats = get_group_statistics(group_name)

        if not stats["member_stats"]:
            return pd.DataFrame()

        data = []
        for member in stats["member_stats"]:
            data.append(
                {
                    "Member": member["_id"],
                    "Total Meals": member.get("total_meals", 0),
                    "Total Amount (₹)": round(member.get("total_amount", 0), 2),
                    "Meal Entries": member.get("meal_count", 0),
                }
            )

        df = pd.DataFrame(data)

        # Add group total row
        if len(df) > 0:
            total_row = pd.DataFrame(
                [
                    {
                        "Member": "GROUP TOTAL",
                        "Total Meals": stats["group_total_meals"],
                        "Total Amount (₹)": round(stats["group_total_amount"], 2),
                        "Meal Entries": df["Meal Entries"].sum(),
                    }
                ]
            )
            df = pd.concat([df, total_row], ignore_index=True)

        return df

    except Exception as e:
        raise QueryError(str(e), operation="get_group_dataframe")
