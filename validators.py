"""
Input validators and sanitizers to prevent crashes from invalid data.
Centralized validation makes it easy to enforce business rules across the app.
"""

from config import (
    MIN_GROUP_NAME_LENGTH,
    MAX_GROUP_NAME_LENGTH,
    MIN_MEMBER_NAME_LENGTH,
    MAX_MEMBER_NAME_LENGTH,
    MIN_MEAL_PRICE,
    MAX_MEAL_PRICE,
    MIN_MEAL_COUNT,
    MAX_MEAL_COUNT,
)


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_group_name(group_name) -> str:
    """
    Validate and sanitize group name.

    Args:
        group_name: The group name to validate

    Returns:
        Sanitized group name

    Raises:
        ValidationError: If validation fails
    """
    if not group_name:
        raise ValidationError("Group name cannot be empty")

    group_name = str(group_name).strip()

    if not group_name:
        raise ValidationError("Group name cannot be empty or whitespace only")

    if len(group_name) < MIN_GROUP_NAME_LENGTH:
        raise ValidationError(f"Group name too short (minimum {MIN_GROUP_NAME_LENGTH} character)")

    if len(group_name) > MAX_GROUP_NAME_LENGTH:
        raise ValidationError(f"Group name too long (maximum {MAX_GROUP_NAME_LENGTH} characters)")

    return group_name


def validate_member_name(member_name) -> str:
    """
    Validate and sanitize member name.

    Args:
        member_name: The member name to validate

    Returns:
        Sanitized member name

    Raises:
        ValidationError: If validation fails
    """
    if not member_name:
        raise ValidationError("Member name cannot be empty")

    member_name = str(member_name).strip()

    if not member_name:
        raise ValidationError("Member name cannot be empty or whitespace only")

    if len(member_name) < MIN_MEMBER_NAME_LENGTH:
        raise ValidationError(f"Member name too short (minimum {MIN_MEMBER_NAME_LENGTH} character)")

    if len(member_name) > MAX_MEMBER_NAME_LENGTH:
        raise ValidationError(f"Member name too long (maximum {MAX_MEMBER_NAME_LENGTH} characters)")

    return member_name


def validate_meal_price(price) -> float:
    """
    Validate and convert meal price to float.

    Args:
        price: The meal price to validate

    Returns:
        Validated price as float

    Raises:
        ValidationError: If validation fails
    """
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValidationError("Meal price must be a valid number")

    if price < MIN_MEAL_PRICE:
        raise ValidationError(f"Meal price cannot be negative")

    if price > MAX_MEAL_PRICE:
        raise ValidationError(f"Meal price exceeds maximum limit (₹{MAX_MEAL_PRICE})")

    return price


def validate_meal_count(lunch: int, dinner: int) -> tuple:
    """
    Validate meal counts.

    Args:
        lunch: Number of lunches
        dinner: Number of dinners

    Returns:
        Tuple of (lunch, dinner) as integers

    Raises:
        ValidationError: If validation fails
    """
    try:
        lunch = int(lunch)
        dinner = int(dinner)
    except (ValueError, TypeError):
        raise ValidationError("Meal counts must be valid integers")

    if lunch < MIN_MEAL_COUNT or lunch > MAX_MEAL_COUNT:
        raise ValidationError(f"Lunch count must be between {MIN_MEAL_COUNT} and {MAX_MEAL_COUNT}")

    if dinner < MIN_MEAL_COUNT or dinner > MAX_MEAL_COUNT:
        raise ValidationError(f"Dinner count must be between {MIN_MEAL_COUNT} and {MAX_MEAL_COUNT}")

    return lunch, dinner


def validate_members_list(members) -> list:
    """
    Validate a list of member names.

    Args:
        members: List of member names

    Returns:
        Validated and sanitized list of member names

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(members, list):
        raise ValidationError("Members must be a list")

    if not members:
        return []

    validated = []
    for member in members:
        validated.append(validate_member_name(member))

    # Check for duplicates (case-insensitive)
    lower_names = [name.lower() for name in validated]
    if len(lower_names) != len(set(lower_names)):
        raise ValidationError("Duplicate member names found")

    return validated


def validate_person_name(person_name) -> str:
    """
    Validate and sanitize person/member name (same as member validation).

    Args:
        person_name: The person name to validate

    Returns:
        Sanitized person name

    Raises:
        ValidationError: If validation fails
    """
    return validate_member_name(person_name)
