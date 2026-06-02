"""
Utility functions to reduce code duplication and improve maintainability.
Contains common patterns for error handling, data validation, and Streamlit operations.
"""

import streamlit as st
from typing import Tuple, Optional, Callable
from functools import wraps
import logging

from errors import MealTrackerError


def safe_streamlit_operation(
    operation_func: Callable,
    error_title: str = "❌ Error",
    default_error_msg: str = "An error occurred",
) -> Optional:
    """
    Safely execute a Streamlit operation with error handling.

    Args:
        operation_func: Function to execute
        error_title: Title for error message
        default_error_msg: Default error message if operation fails

    Returns:
        Result of operation_func, or None if error occurred
    """
    try:
        return operation_func()
    except MealTrackerError as e:
        st.error(f"{error_title}: {e.user_message}")
        return None
    except Exception as e:
        st.error(f"{error_title}: {default_error_msg}")
        return None


def handle_db_operation_error(error: Exception, logger: Optional[logging.Logger] = None):
    """
    Handle database operation errors and display user-friendly message.

    Args:
        error: The exception that occurred
        logger: Optional logger for error logging
    """
    if logger:
        logger.error(f"Database operation failed: {str(error)}")

    if isinstance(error, MealTrackerError):
        st.error(f"❌ {error.user_message}")
    else:
        st.error("❌ Database operation failed. Please try again.")


def show_success_with_delay(message: str, delay_seconds: int = 2):
    """
    Show success message that auto-dismisses after delay.

    Args:
        message: Success message to show
        delay_seconds: Seconds before dismissing (Streamlit limitation: requires rerun)
    """
    st.success(message)


def create_session_state_key(prefix: str, suffix: str) -> str:
    """
    Create a consistent session state key from prefix and suffix.

    Args:
        prefix: Key prefix
        suffix: Key suffix

    Returns:
        Combined key string
    """
    return f"{prefix}_{suffix}".replace(" ", "_").lower()


def validate_and_get_input(
    input_value, validator_func: Callable, error_message: str = None
) -> Tuple[bool, any, Optional[str]]:
    """
    Validate input and return status, value, and error message.

    Args:
        input_value: Value to validate
        validator_func: Function that validates and returns cleaned value
        error_message: Custom error message

    Returns:
        Tuple of (is_valid, cleaned_value, error_message)
    """
    try:
        cleaned_value = validator_func(input_value)
        return True, cleaned_value, None
    except Exception as e:
        return False, None, error_message or str(e)


def get_or_none(dictionary: dict, key: str, default=None):
    """
    Safely get a value from dictionary with default.

    Args:
        dictionary: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    if not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)


def batch_process_items(
    items: list,
    batch_size: int = 100,
    process_func: Callable = None,
    logger: Optional[logging.Logger] = None,
) -> list:
    """
    Process a large list of items in batches.
    Useful for bulk database operations.

    Args:
        items: List of items to process
        batch_size: Number of items per batch
        process_func: Function to process each batch
        logger: Optional logger

    Returns:
        List of results
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        if logger:
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} items)")

        if process_func:
            batch_result = process_func(batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
        else:
            results.extend(batch)

    return results


def format_currency(amount: float, currency_symbol: str = "₹") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format
        currency_symbol: Currency symbol

    Returns:
        Formatted currency string
    """
    try:
        return f"{currency_symbol}{float(amount):.2f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"


def format_date_display(date_obj) -> str:
    """
    Format date for display.

    Args:
        date_obj: Date object to format

    Returns:
        Formatted date string
    """
    try:
        return date_obj.strftime("%b %d, %Y")
    except (AttributeError, TypeError):
        return str(date_obj)


def format_count_display(count: int, singular: str, plural: str = None) -> str:
    """
    Format count with proper singular/plural form.

    Args:
        count: Count value
        singular: Singular form
        plural: Plural form (if None, adds 's' to singular)

    Returns:
        Formatted string with count
    """
    if plural is None:
        plural = f"{singular}s"

    form = singular if count == 1 else plural
    return f"{count} {form}"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def is_valid_email(email: str) -> bool:
    """
    Basic email validation.

    Args:
        email: Email to validate

    Returns:
        True if valid email format
    """
    if not isinstance(email, str):
        return False

    return "@" in email and "." in email.split("@")[-1]
