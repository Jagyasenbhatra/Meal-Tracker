"""
Custom exceptions and error handling for the application.
Provides consistent error codes, messages, and logging.
"""


class MealTrackerError(Exception):
    """Base exception for all meal tracker errors"""
    def __init__(self, message: str, error_code: str = None, user_message: str = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.user_message = user_message or "An error occurred. Please try again."
        super().__init__(self.message)


class DatabaseError(MealTrackerError):
    """Raised when database operations fail"""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            error_code="DB_ERROR",
            user_message=user_message or "Database operation failed. Please try again."
        )


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(
            message,
            user_message="Unable to connect to database. Please check your connection and try again."
        )


class QueryError(DatabaseError):
    """Raised when database query fails"""
    def __init__(self, message: str, operation: str = None):
        op_msg = f" ({operation})" if operation else ""
        super().__init__(
            message,
            user_message=f"Failed to retrieve data{op_msg}. Please try again."
        )


class ValidationError(MealTrackerError):
    """Raised when validation fails"""
    def __init__(self, message: str):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            user_message=message
        )


class GroupNotFoundError(ValidationError):
    """Raised when a group is not found"""
    def __init__(self, group_name: str):
        super().__init__(f"Group '{group_name}' not found")


class MemberAlreadyExistsError(ValidationError):
    """Raised when trying to add a member that already exists"""
    def __init__(self, member_name: str, group_name: str):
        super().__init__(f"Member '{member_name}' already exists in group '{group_name}'")


class MemberNotFoundError(ValidationError):
    """Raised when a member is not found in a group"""
    def __init__(self, member_name: str, group_name: str):
        super().__init__(f"Member '{member_name}' not found in group '{group_name}'")


class ConfigError(MealTrackerError):
    """Raised when configuration is invalid"""
    def __init__(self, message: str):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            user_message="Application configuration error. Please contact administrator."
        )


# Error code registry
ERROR_CODES = {
    "UNKNOWN_ERROR": "Unknown error occurred",
    "DB_ERROR": "Database error",
    "DB_CONNECTION_ERROR": "Database connection failed",
    "DB_QUERY_ERROR": "Database query failed",
    "VALIDATION_ERROR": "Validation failed",
    "GROUP_NOT_FOUND": "Group not found",
    "MEMBER_EXISTS": "Member already exists",
    "MEMBER_NOT_FOUND": "Member not found",
    "CONFIG_ERROR": "Configuration error",
}


def get_error_message(error_code: str, default: str = None) -> str:
    """Get user-friendly message for error code"""
    return ERROR_CODES.get(error_code, default or "An error occurred")


def handle_error(error: Exception, logger=None, default_message: str = None):
    """
    Centralized error handling.

    Args:
        error: The exception that occurred
        logger: Logger instance for logging
        default_message: Default user message if error doesn't provide one

    Returns:
        Tuple of (error_code, user_message)
    """
    # Log the error if logger provided
    if logger:
        logger.error(f"Error occurred: {type(error).__name__}: {str(error)}")

    # Return appropriate message
    if isinstance(error, MealTrackerError):
        return error.error_code, error.user_message
    else:
        return "UNKNOWN_ERROR", default_message or "An unexpected error occurred"
