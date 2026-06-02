# Meal Tracker - Scalability & Maintainability Guide

## Overview

This application has been refactored for **stability, scalability, and ease of feature addition**. The architecture now follows these principles:

1. **Centralized Configuration** - Single source of truth for settings
2. **Error Handling** - Comprehensive error handling prevents crashes
3. **Input Validation** - All user inputs are validated before processing
4. **Modular Design** - Clear separation of concerns
5. **Code Reusability** - Helper functions reduce duplication
6. **Feature Flags** - Easy enable/disable of features

---

## Project Structure

```
Meal-Tracker/
├── app.py                    # Main application entry point (with error handling)
├── config.py                 # ⭐ Centralized configuration & feature flags
├── constants.py              # Legacy constants (imports from config)
├── validators.py             # ⭐ Input validation & sanitization
├── errors.py                 # ⭐ Custom exceptions & error codes
├── utils_helpers.py          # ⭐ Utility functions & helper methods
├── logger.py                 # Logging configuration
├── db_connection.py          # MongoDB connection (with error handling)
├── data_services.py          # Data loading & caching (with error handling)
├── group_services.py         # Group management logic (with validation)
├── ui_sections.py            # Streamlit UI rendering
└── ... (other files)
```

**⭐ = New/Improved files for stability & scalability**

---

## How to Add New Features

### Step 1: Define Configuration in `config.py`

```python
# In config.py - add feature flag
FEATURES = {
    "my_new_feature": True,  # Can toggle on/off
}

# Add any constants your feature needs
MY_FEATURE_SETTING = "value"
```

### Step 2: Create Validation Rules in `validators.py`

```python
# In validators.py - add input validation
def validate_my_input(value: str) -> str:
    """Validate and sanitize my input"""
    if not value:
        raise ValidationError("Input cannot be empty")
    return value.strip()
```

### Step 3: Create Business Logic with Error Handling

```python
# In a service file (e.g., data_services.py or new_service.py)
from validators import validate_my_input, ValidationError
from errors import QueryError
from config import is_feature_enabled

def my_feature_function(input_val: str, logger):
    """Implement my feature with error handling"""
    try:
        # Validate input
        cleaned_input = validate_my_input(input_val)

        # Check feature flag
        if not is_feature_enabled("my_new_feature"):
            return False, "Feature not available"

        # Do something with database
        result = some_db_operation(cleaned_input)

        logger.info(f"Feature executed successfully: {cleaned_input}")
        return True, result

    except ValidationError as e:
        return False, str(e)  # Input validation error

    except Exception as e:
        logger.error(f"Feature failed: {str(e)}")
        return False, "Feature execution failed"
```

### Step 4: Create UI Component in `ui_sections.py`

```python
# In ui_sections.py - render your feature with error handling
from utils_helpers import safe_streamlit_operation

def render_my_feature(logger):
    """Render my new feature with error handling"""
    st.subheader("🎯 My New Feature")

    # Get input
    user_input = st.text_input("Enter something", key="my_feature_input")

    if st.button("Execute"):
        # Use safe operation wrapper
        def execute():
            success, result = my_feature_function(user_input, logger)
            if success:
                st.success(f"Success: {result}")
            else:
                st.error(f"Failed: {result}")

        safe_streamlit_operation(execute)
```

### Step 5: Integrate into `app.py`

```python
# In app.py - add your feature to the main flow
from ui_sections import render_my_feature
from config import is_feature_enabled

if is_feature_enabled("my_new_feature"):
    st.divider()
    render_my_feature(logger)
```

---

## Error Handling Architecture

### Exception Hierarchy

```
Exception
  └─ MealTrackerError (base)
      ├─ DatabaseError
      │  ├─ ConnectionError
      │  └─ QueryError
      ├─ ValidationError
      │  ├─ GroupNotFoundError
      │  ├─ MemberAlreadyExistsError
      │  └─ MemberNotFoundError
      └─ ConfigError
```

### Usage Examples

#### Example 1: Database Operation

```python
from errors import QueryError

def load_data():
    try:
        return db_collection.find({})
    except Exception as e:
        raise QueryError(str(e), operation="load_data")
```

#### Example 2: API Handler

```python
from errors import MealTrackerError, handle_error
import streamlit as st

def handle_request():
    try:
        # Do something
        result = risky_operation()
        st.success("Operation succeeded!")
        return result

    except MealTrackerError as e:
        st.error(f"Error: {e.user_message}")
        logger.error(f"{e.error_code}: {e.message}")
        return None
```

---

## Input Validation Pattern

All user inputs should be validated before processing:

```python
from validators import (
    validate_group_name,
    validate_member_name,
    validate_meal_price,
    ValidationError
)

# Example: Validating form submission
user_group = st.text_input("Group name")
user_price = st.number_input("Price")

if st.button("Submit"):
    try:
        clean_group = validate_group_name(user_group)
        clean_price = validate_meal_price(user_price)

        # Now safe to use clean_group and clean_price
        save_to_database(clean_group, clean_price)
        st.success("Saved!")

    except ValidationError as e:
        st.error(f"Invalid input: {e}")
```

---

## Scalability Patterns

### 1. Caching with Invalidation

```python
from config import CACHE_TTL_GROUPS
import streamlit as st

@st.cache_data(ttl=CACHE_TTL_GROUPS)
def load_groups():
    """Cached with TTL from config - easy to adjust"""
    return db.groups.find()

def clear_group_cache():
    """Clear cache when data changes"""
    st.cache_data.clear()
```

**Why this matters**: Easy to adjust cache timing globally, and cache is cleared when mutations happen.

### 2. Batch Processing

```python
from utils_helpers import batch_process_items

# Process 1000s of records efficiently
large_list = get_large_dataset()
results = batch_process_items(
    large_list,
    batch_size=100,
    process_func=save_batch_to_db,
    logger=logger
)
```

### 3. Safe Database Operations

```python
from errors import QueryError

@st.cache_data(ttl=30)
def load_records(query):
    try:
        return list(db.find(query))
    except Exception as e:
        raise QueryError(str(e), operation="load_records")
```

---

## Configuration Management

### Updating Application Settings

Instead of hard-coding values, use `config.py`:

```python
# ❌ BAD - Hard-coded
CACHE_TIME = 30
MAX_MEALS = 10

# ✅ GOOD - In config.py
CACHE_TTL_RECORDS = 30
MAX_MEAL_COUNT = 10

# Then import
from config import CACHE_TTL_RECORDS, MAX_MEAL_COUNT
```

### Adding New Settings

1. Open `config.py`
2. Add your setting in appropriate section
3. Import and use it wherever needed
4. Change once = updates everywhere

---

## Testing & Validation Checklist

### Before Deploying New Features

- [ ] Input validation tests
  ```python
  from validators import validate_group_name, ValidationError

  # Test valid input
  assert validate_group_name("MyGroup") == "MyGroup"

  # Test invalid input
  try:
      validate_group_name("")
      assert False, "Should raise error"
  except ValidationError:
      pass  # Expected
  ```

- [ ] Database error handling
  ```python
  # Test with invalid connection
  # Verify proper error message shown to user
  ```

- [ ] Streamlit error handling
  ```python
  # Test that errors don't crash app
  # Verify user sees friendly error message
  ```

- [ ] Feature flag toggle
  ```python
  # Test with feature enabled
  # Test with feature disabled
  ```

---

## Best Practices

### 1. Always Validate User Input

```python
# ❌ DON'T
def add_item(name):
    db.insert({"name": name})

# ✅ DO
def add_item(name):
    try:
        name = validate_member_name(name)
        db.insert({"name": name})
    except ValidationError as e:
        return False, str(e)
```

### 2. Use Type Hints

```python
# ❌ DON'T
def load_members(group):
    return group.get("members", [])

# ✅ DO
def load_members(group_name: str) -> list:
    return group.get("members", [])
```

### 3. Add Logging at Key Points

```python
# ✅ DO
logger.info(f"Created group: {group_name}")
logger.error(f"Failed to load records: {str(e)}")
logger.warning(f"Member already exists: {member_name}")
```

### 4. Use Centralized Constants

```python
# ❌ DON'T
if len(name) > 100:
    raise ValueError("Too long")

# ✅ DO
from config import MAX_MEMBER_NAME_LENGTH
if len(name) > MAX_MEMBER_NAME_LENGTH:
    raise ValidationError(f"Name too long (max {MAX_MEMBER_NAME_LENGTH})")
```

### 5. Handle Errors Gracefully

```python
# ❌ DON'T
result = risky_operation()  # Crashes on error

# ✅ DO
try:
    result = risky_operation()
except MealTrackerError as e:
    st.error(f"Failed: {e.user_message}")
    logger.error(f"Error: {e.message}")
    return None
```

---

## Common Patterns

### Pattern 1: Form Submission with Validation

```python
def render_form():
    name = st.text_input("Name")
    price = st.number_input("Price")

    if st.button("Submit"):
        try:
            # Validate all inputs
            clean_name = validate_member_name(name)
            clean_price = validate_meal_price(price)

            # Process
            success, msg = save_item(clean_name, clean_price, logger)

            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

        except ValidationError as e:
            st.error(f"Invalid input: {e}")
```

### Pattern 2: Database Query with Error Handling

```python
def get_data(query: dict):
    try:
        results = list(db.find(query))
        if not results:
            return []
        return results
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise QueryError(str(e), operation="get_data")
```

### Pattern 3: Feature Flag Check

```python
from config import is_feature_enabled

if is_feature_enabled("my_feature"):
    render_my_feature()
else:
    st.info("Feature not available")
```

---

## Monitoring & Debugging

### Enable Debug Logging

```python
import logging

# In logger.py - set DEBUG level
logger.setLevel(logging.DEBUG)
```

### Check Error Codes

All errors have codes in `errors.py`:

```python
ERROR_CODES = {
    "DB_ERROR": "Database error",
    "VALIDATION_ERROR": "Validation failed",
    # ...
}
```

### Review Logs

Check logs for patterns:
- Connection errors → Database issues
- Validation errors → User input issues
- Query errors → Data access problems

---

## Performance Optimization

### 1. Use Caching for Read Operations

```python
# Frequently read, rarely changed
@st.cache_data(ttl=30)
def load_groups():
    return db.groups.find()
```

### 2. Avoid Caching for Real-time Data

```python
# Real-time data - no cache
def load_group_members(group_name):
    return db.groups.find_one(...)["members"]
```

### 3. Use Projections to Fetch Only Needed Fields

```python
# In config.py
GROUPS_PROJECTION = {
    "group_name": 1,
    "members": 1,
    "created_at": 1,
}

# In query
db.groups.find({}, GROUPS_PROJECTION)
```

---

## Scaling Considerations

### For Large Datasets

1. **Use Pagination**
   ```python
   from config import PAGE_SIZE

   skip = (page - 1) * PAGE_SIZE
   results = db.find().skip(skip).limit(PAGE_SIZE)
   ```

2. **Use Batch Processing**
   ```python
   from utils_helpers import batch_process_items
   batch_process_items(large_list, batch_size=1000)
   ```

3. **Add Database Indexes** (Already in `db_connection.py`)
   ```python
   db.meals.create_index([("person_name", 1), ("meal_date", -1)])
   ```

### For Multiple Users

- Connection pooling enabled in MongoDB config
- Cache invalidation when data changes
- Session state for user-specific data

---

## Troubleshooting

### App Crashes Without Error Message

1. Check `app.py` - has try-except around main code
2. Check logs - look for ImportError or ConfigError
3. Verify imports - check for circular imports
4. Check secrets - MONGO_URI and ADMIN_PASSWORD required

### Data Not Updating

1. Check cache - may need `clear_group_cache()`
2. Verify MongoDB connection
3. Check for duplicate documents
4. Review logs for update errors

### Validation Errors Not Showing

1. Check validators - ensure ValidationError raised
2. Check UI - ensure st.error() called
3. Check try-except blocks - ensure they handle ValidationError

---

## Summary

The refactored application provides:

✅ **Crash Prevention** - Comprehensive error handling
✅ **Scalability** - Modular, configurable architecture
✅ **Easy Feature Addition** - Clear patterns for new features
✅ **Input Safety** - Validation before processing
✅ **Maintainability** - Centralized config, helper functions
✅ **Performance** - Caching, projections, batch processing
✅ **User Experience** - Friendly error messages
✅ **Debugging** - Extensive logging

**Result**: Stable, maintainable, and easy to extend!
