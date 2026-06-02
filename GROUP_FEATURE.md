# Group Management Feature - Documentation

## Overview
The Meal Tracker has been enhanced with a comprehensive **Group Management** feature that allows you to organize members into groups, track their meals collectively, and view detailed statistics both by group and individual member.

## Features Added

### 1. **Group Management**
- **Create Groups**: Create new groups with custom names (e.g., "demo", "office", "friends")
- **View Groups**: See all created groups and their members at a glance
- **Group Statistics**: View group totals and individual member statistics

### 2. **Member Management**
- **Add Members**: Add any member to a group with a simple input
- **Remove Members**: Remove members from a group when needed
- **Member Tracking**: Track individual meal records for each member

### 3. **Group Data Analytics**
- **Group Totals**: See total meals consumed and total amount spent by the entire group
- **Individual Breakdown**: View per-member statistics including:
  - Total meals
  - Total amount spent (₹)
  - Number of meal entries
- **Member-wise Filtering**: Filter and view records by individual members

### 4. **Integration with Existing System**
- Works seamlessly with existing personal meal tracking
- Group data is organized separately from individual records
- All meal entries for group members are automatically aggregated

## How to Use

### Step 1: Create a Group
1. Navigate to the **"👥 Group Management"** section
2. Go to the **"Create/Select Group"** tab
3. Enter a group name (e.g., "demo")
4. Click **"➕ Create Group"**

### Step 2: Add Members to the Group
1. In the **"Manage Members"** tab
2. Select your group from the dropdown
3. Enter a member name (e.g., "john", "alice", "bob")
4. Click **"✅ Add Member"**
5. Repeat for all members you want to add

### Step 3: Record Meals for Members
1. At the top of the page, enter a member's name in the **"👤 Person Name"** field
2. Select a date, enter meal details (lunch/dinner or total meals)
3. Enter the price per meal
4. Click **"💾 Save Record"**

**Example**: If you have a group "demo" with member "john":
- Enter `john` in the Person Name field
- Add meal details and save

### Step 4: View Group Data
1. Scroll to the **"📊 View Group Data"** section
2. Select your group from the dropdown
3. View:
   - Group totals (meals and amount)
   - Member-wise breakdown table
   - Individual meal records
   - Filter by specific members

## Database Structure

### New Collections

#### `groups` Collection
Stores group information with the following fields:
```json
{
  "_id": ObjectId,
  "group_name": "demo",
  "members": ["john", "alice", "bob"],
  "created_at": timestamp,
  "updated_at": timestamp
}
```

### Files Modified/Created

#### New Files:
- **`group_services.py`**: Core logic for group management including:
  - `create_group()`: Create a new group
  - `add_member_to_group()`: Add member to group
  - `remove_member_from_group()`: Remove member from group
  - `load_all_groups()`: Fetch all groups
  - `load_group_members()`: Get members of a specific group
  - `get_group_statistics()`: Get detailed statistics
  - `get_group_dataframe()`: Format data for display

#### Modified Files:
- **`db_connection.py`**: Added groups collection with indexes
- **`ui_sections.py`**: Added three new UI rendering functions:
  - `render_group_management()`: Group and member management interface
  - `render_group_data_view()`: Display group data and analytics
  - Updated imports to include group services
- **`app.py`**: Integrated group management into main application flow

## Use Cases

### Example 1: Tracking Meals for an Office Group
```
1. Create group "office"
2. Add members: "john", "alice", "bob", "maria"
3. Each member records their meals under their name
4. View group statistics to see:
   - Total meals for the office
   - Who spent how much
   - Individual meal counts
```

### Example 2: Shared Meal Planning
```
1. Create group "friends"
2. Add members: "alex", "chris", "sam"
3. Track shared meals or individual spending
4. Export group data for payment settlement
```

## Tips and Best Practices

1. **Consistent Names**: Use consistent member names to ensure proper data aggregation
2. **Group Organization**: Create separate groups for different purposes
3. **Regular Updates**: Keep member lists up to date by removing inactive members
4. **Data Export**: Use the export feature to download group data for records
5. **Group Naming**: Use clear, lowercase group names for consistency

## Features Working Together

- **Meal Input**: Standard meal entry form works for all group members
- **Payment Summary**: Group payment summaries show group totals alongside individual entries
- **Exports**: Export functionality includes group member data
- **Monthly Filtering**: View group data filtered by months
- **Admin Panel**: Group data can be managed through the admin interface

## Error Handling

The system validates:
- ✅ Group names cannot be empty
- ✅ Duplicate group names are prevented
- ✅ Duplicate member names within a group are prevented
- ✅ Members can only be removed if they exist in the group
- ✅ All validations provide user-friendly error messages

## Future Enhancements

Potential features for future versions:
- Group permissions and roles
- Payment settlement calculations
- Group budget tracking
- Member join codes
- Email notifications for group updates
- Recurring meal patterns
- Group meal preferences/dietary restrictions
