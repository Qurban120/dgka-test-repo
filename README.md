# User Termination and Lock Date Analysis Tool

This Python script analyzes user termination and lock dates to ensure compliance with security procedures. It checks if users are locked timely after termination, considering weekends and holidays.

## Features

- Analyzes user termination vs lock dates according to business rules
- Considers weekends and holidays when evaluating compliance
- Filters users by status (EXPIRED, EXPIRED AND LOCKED, EXPIRED (GRACE) AND LOCKED, LOCKED)
- Generates detailed Excel reports with compliance analysis
- Identifies non-compliant records requiring action

## Business Rules Implemented

1. **Same Day Lock**: If lock date equals termination date → Process working effectively
2. **Different Dates**: If lock date differs from termination date:
   - Check if lock date exceeds 1 day from termination
   - Consider if termination was before weekend/holiday
   - Check if lock date exceeds 1 day after first business day post-termination

## Prerequisites

- Python 3.7 or higher
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - numpy
  - openpyxl
  - xlrd

## File Requirements

### CMS Excel File (Main User Data)
- Should contain user data with the following types of columns:
  - Status column (containing values like EXPIRED, LOCKED, etc.)
  - Termination date column
  - Lock date column
  - User ID column (optional, for identification)
- **All columns from the original file will be preserved in the output**

### Holidays Excel File
- Must contain a column named "DATES"
- Dates should be in dd/mm/yyyy format
- Each row should contain one holiday date

## Usage

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the script**:
   ```bash
   python user_termination_analysis.py
   ```

3. **Follow the prompts**:
   - Enter path to CMS Excel file (main user data file)
   - Enter path to Holidays Excel file
   - Enter output file name (optional, defaults to 'termination_analysis_report.xlsx')

## Output

The script generates an Excel report with multiple sheets:

### Analysis Results Sheet
Contains all analyzed records with:
- **All original columns from the CMS file**
- Additional analysis columns:
  - ANALYSIS_STATUS (COMPLIANT/NON_COMPLIANT)
  - ANALYSIS_REASON (detailed explanation)
  - ACTION_REQUIRED (true/false flag)
  - DAYS_DIFFERENCE (days between termination and lock)
  - TERMINATION_IS_WEEKEND/TERMINATION_IS_HOLIDAY
  - LOCK_IS_WEEKEND/LOCK_IS_HOLIDAY
  - FIRST_BUSINESS_DAY_AFTER_TERMINATION
  - DAYS_AFTER_FIRST_BUSINESS_DAY

### Summary Sheet
Provides overall statistics:
- Total records analyzed
- Number of compliant records
- Number of non-compliant records
- Records requiring action

### Non-Compliant Records Sheet
Contains only records that require action with detailed information.

## Column Detection

The script automatically detects columns based on common naming patterns:
- **Status columns**: Contains "status" or "state" in name
- **Termination columns**: Contains "termination" or "term" in name
- **Lock columns**: Contains "lock" in name
- **Last logon columns**: Contains "logon" or "login" in name

## Example Scenarios

### Compliant Cases
- User terminated Friday, locked Friday → ✅ COMPLIANT
- User terminated Friday, locked Monday (next business day) → ✅ COMPLIANT
- User terminated Thursday, locked Friday → ✅ COMPLIANT

### Non-Compliant Cases
- User terminated Tuesday, locked Thursday (2 days later) → ❌ NON_COMPLIANT
- User terminated Friday, locked Wednesday (3 business days later) → ❌ NON_COMPLIANT

## Troubleshooting

### Common Issues

1. **File not found**: Ensure file paths are correct and files exist
2. **Column not detected**: Check if column names match expected patterns
3. **Date parsing errors**: Ensure dates are in recognizable format
4. **Missing holidays**: Verify holidays file has "DATES" column in dd/mm/yyyy format

### Error Messages

- "Could not identify status column" → Check if status column exists
- "Could not identify required termination and lock date columns" → Verify column names
- "Error loading holidays file" → Check holidays file format and path

## Customization

To modify the script for different requirements:

1. **Change target statuses**: Edit the `target_statuses` list in `load_and_analyze_data()` method
2. **Modify business rules**: Update the logic in `analyze_user_lock_timing()` method
3. **Add new date formats**: Modify date parsing in the `load_holidays()` method
4. **Change column detection**: Update the column identification logic

## Support

For issues or questions about the script, please check:
1. Input file formats match requirements
2. All required columns are present
3. Dependencies are properly installed
4. File paths are accessible