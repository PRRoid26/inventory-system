# IT Asset Inventory Management System - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Login](#login)
3. [Dashboard Overview](#dashboard-overview)
4. [Managing Equipment](#managing-equipment)
5. [Import Equipment Data](#import-equipment-data)
6. [Equipment Specifications](#equipment-specifications)
7. [Work Logs](#work-logs)
8. [Import History](#import-history)
9. [Search and Filters](#search-and-filters)
10. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### First Time Setup

1. **Launch the Application**
   - Run the desktop client: `./start_frontend.sh`
   - Or use: `python frontend/main.py`

2. **Login Screen**
   - Default credentials:
     - Username: `admin`
     - Password: `admin123`
   - **Important**: Change the default password immediately!

3. **Configure Server**
   - For local use: `http://localhost:8000`
   - For remote access: `https://your-server.com`

## Login

### Creating New Users

Administrators can create new user accounts:

1. Click **Register** on login screen
2. Fill in details:
   - Username (unique)
   - Email address
   - Password (minimum 8 characters)
   - Full Name
3. Click **Register**

### User Roles

- **Admin**: Full access, can delete equipment and imports
- **Manager**: Can manage equipment and work logs
- **User**: Can view and create work logs

## Dashboard Overview

The **Overview** tab shows:

### Overall Statistics
- **Total Equipment**: Total number of assets
- **Available**: Equipment ready for use
- **In Service**: Currently checked out
- **Faulty**: Equipment requiring repair
- **Retired**: Decommissioned equipment

### Category Breakdown
- Equipment organized by category
- Status breakdown for each category
- Click any category to see detailed product list

## Managing Equipment

### Adding Equipment Manually

1. Go to **Inventory** tab
2. Click **➕ Add Equipment**
3. Fill in the form:
   - **Asset No**: Unique identifier (e.g., COMP-001)
   - **Serial No**: Manufacturer serial number
   - **Product Name**: Equipment name
   - **Category**: Auto-selected or manual
   - **Status**: Current status
   - **Location**: Physical location
   - **Supplier**: Vendor name
   - **Cost**: Purchase cost
4. Click **OK**

### Editing Equipment

1. Select equipment from the table
2. Click **✏️ Edit**
3. Modify fields as needed
4. Click **OK** to save

### Deleting Equipment

1. Select equipment from the table
2. Click **🗑️ Delete**
3. Confirm deletion
4. **Note**: Only Admin and Manager roles can delete

## Import Equipment Data

### Preparing CSV/Excel File

Create a file with these columns:
```
asset_no,serial_no,product_name,status,location,supplier,cost
COMP-001,SN12345,Dell OptiPlex,Available,IT Dept,Dell,1200.00
```

**Required Columns**:
- `asset_no` - Must be unique
- `product_name` - Equipment name

**Optional Columns**:
- `serial_no`
- `status` (Available/In Service/Faulty/Retired)
- `location`
- `supplier`
- `cost`

### Importing Data

1. Go to **Inventory** tab
2. Click **📥 Import CSV/Excel**
3. Select your file (.csv, .xlsx, or .xls)
4. Review import results:
   - Total records processed
   - Successful imports
   - Failed imports (with error messages)

### Auto-Categorization

The system automatically categorizes equipment based on product name:
- Contains "laptop/computer/pc" → Computers
- Contains "switch/router" → Network Equipment
- Contains "monitor/display" → Monitors
- Contains "printer/scanner" → Printers & Scanners
- And more...

## Equipment Specifications

### Adding Specifications

1. Go to **Specifications** tab
2. Search for equipment by asset number (autocomplete enabled)
3. Click **Load Specifications**
4. Click **➕ Add/Edit Specifications**
5. Fill in technical details:
   - Processor
   - RAM
   - Storage
   - Graphics card
   - Operating System
   - Network capabilities
   - Additional notes
6. Click **OK**

### Viewing Specifications

1. Search for equipment
2. Click **Load Specifications**
3. All technical details are displayed

## Work Logs

Work logs track when equipment is checked out and returned.

### Creating a Work Log

1. Go to **Work Logs** tab
2. Click **➕ Create Work Log**
3. Search for equipment
4. Fill in details:
   - **Job Name**: Project or purpose
   - **Assigned To**: Person's name
   - **Department**: Department name
   - **Check Out Date**: When issued
   - **Expected Return**: When it should return
   - **Status**: In Progress/Completed/On Hold
   - **Notes**: Additional information
5. Click **OK**

### Automatic Status Updates

- Creating a work log sets equipment to **In Service**
- Completing a work log sets equipment to **Available**

### Filtering Work Logs

Use the status dropdown to filter:
- All work logs
- In Progress only
- Completed only
- On Hold only

## Import History

The system keeps a complete history of all CSV imports.

### Viewing Import History

1. Go to **Import History** tab
2. See all past imports with:
   - Filename
   - Import date and time
   - Total records
   - Successful/failed counts

### Viewing Import Details

1. Select an import from the list
2. Click **👁️ View Details**
3. See:
   - Import information
   - All equipment from this import
   - Individual equipment details

### Managing Imports

**Delete Import Record Only**:
- Removes the import record
- Keeps all equipment in the database

**Delete Import + Equipment**:
- Removes the import record
- Removes all equipment from this import
- **Warning**: This cannot be undone!

To delete:
1. Select import
2. Click **🗑️ Delete Import Record**
3. Choose deletion option
4. Confirm

## Search and Filters

### Quick Asset Search

The Asset No field has autocomplete:
1. Type the first few characters
2. Suggestions appear automatically
3. Select from the list

### Advanced Filtering

Use multiple filters simultaneously:
- **Asset No**: Type to search
- **Category**: Filter by equipment type
- **Status**: Filter by current status
- Click **🔍 Search** to apply

### Sorting

Click any column header to sort:
- Click once: Ascending order
- Click again: Descending order

## Tips and Best Practices

### Asset Numbering

Use a consistent naming scheme:
- `COMP-001` to `COMP-999` for Computers
- `NET-001` to `NET-999` for Network Equipment
- `MON-001` to `MON-999` for Monitors

### Regular Backups

- Backups run automatically daily (if configured)
- Manual backup: Use the backup script
- Store backups in a secure location

### Data Entry

- **Be consistent** with naming conventions
- **Include serial numbers** when available
- **Update status** when equipment changes
- **Add specifications** for important equipment

### CSV Imports

- Always keep a copy of your original files
- Review import results carefully
- Fix errors and re-import if needed
- Use the template as a reference

### Work Log Management

- Create work logs when checking out equipment
- Update status when work is completed
- Add detailed notes for context
- Set realistic return dates

### Security

- **Change default password** immediately
- Use **strong passwords** (12+ characters)
- **Logout** when finished
- Grant appropriate **role permissions**

### Performance

- Use filters to narrow down large datasets
- Regular database maintenance
- Archive old work logs periodically

### Troubleshooting

**Can't connect to server**:
- Check if backend is running
- Verify server URL in settings
- Check firewall settings

**Import fails**:
- Verify CSV format matches template
- Check for duplicate asset numbers
- Ensure required columns are present

**Search not working**:
- Click **🔄 Refresh** to reload data
- Check network connection
- Verify you're logged in

## Keyboard Shortcuts

- **Tab**: Navigate between fields
- **Enter**: Confirm dialogs
- **Escape**: Cancel dialogs
- **Ctrl+F**: Focus search field (when available)

## Getting Help

- Check the **README.md** for technical details
- Review **API documentation** at `/docs` endpoint
- Check application logs for errors
- Contact your system administrator

## Advanced Features

### Cloud Access

When deployed to cloud:
1. Change server URL to your cloud address
2. Use HTTPS for secure connections
3. Access from anywhere with internet

### API Integration

The system has a REST API for integration:
- Full API documentation available
- Use for custom scripts or tools
- Automate repetitive tasks

### Bulk Operations

For large datasets:
- Use CSV import instead of manual entry
- Prepare data in spreadsheet first
- Import in batches if needed

---

**Version**: 1.0  
**Last Updated**: 2024

For technical support or feature requests, contact your IT administrator.
