# Combined Risk and KRI Analysis Tool

This Python script combines **Risk Analysis** and **Key Risk Indicator (KRI) Analysis** into a single comprehensive HTML report.

## Features

### Risk Analysis
- Analyzes IT risks from RCM_QTLD report
- Identifies delayed and not submitted risks (Critical, High, Medium)
- Finds risks without owners or control measures
- Calculates percentages for Q2 2025 data

### KRI Analysis
- Processes 5 different KRIs (KRI8, KRI10, KRI12, KRI13, KRI19)
- Analyzes incident data for critical systems
- Groups Birbank systems appropriately
- Tracks RTO compliance and resolution times

## Requirements

- Python 3.7+
- pandas
- openpyxl
- xlrd

## Installation

1. Create a virtual environment:
```bash
python3 -m venv analysis_env
source analysis_env/bin/activate  # On Windows: analysis_env\Scripts\activate
```

2. Install required packages:
```bash
pip install pandas openpyxl xlrd
```

## Usage

### File Paths Configuration
The script is configured to use these specific file paths:

```python
# Risk analysis file
risk_file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\RCM_QTLD report_Report (1).xls"

# KRI analysis file  
kri_file_path = r"C:\Users\RzazadaTN\Desktop\Incident Report.xlsx"
```

**Note**: If your files are in different locations, update these paths in the `main()` function.

### Run the Analysis
```bash
python combined_risk_kri_analysis.py
```

## Expected Data Format

### Risk Data (Excel file)
Required columns:
- `Risk status`: Status of the risk (aktiv, gecikdirilmiş, etc.)
- `Risk növü`: Type of risk (İT, Operasional, etc.)
- `Məxsusi risk dərəcəsi`: Risk level (Kritik, Yüksək, Orta, Aşağı)
- `Riskin aşkarlanma tarixi`: Risk discovery date
- `Prosesin sahibi`: Process owner
- `Nəzarət tədbirinin təsviri`: Control measure description

### KRI Data (Excel file)
Required columns:
- `Issue Key`: System identifier or incident ID
- `Incident start date`: When the incident started
- `Incident end date`: When the incident ended (or "-" for ongoing)
- `Incident duration`: Duration in minutes

## Output

The script generates:
1. **Combined_Risk_KRI_Analysis_Report.html**: Comprehensive HTML report
2. **Console summary**: Key statistics and counts

## KRI Definitions

- **KRI8**: Systems with no incidents for 120+ days
- **KRI10**: Monthly incident counts per system (Q2 focus)
- **KRI12**: Incidents exceeding RTO (>120 minutes)
- **KRI13**: Incidents resolved within RTO (≤120 minutes)  
- **KRI19**: Average resolution time per system

## Risk Analysis Focus

- **Q2 2025** (April, May, June) analysis period
- **IT risks only**
- Excludes cancelled risks (`ləğv edilmiş`)
- Separate analysis for Critical vs High/Medium risks

## Sample Data

If no data files are found, the script creates realistic sample data:
- 100 risk records with various statuses and levels
- 300+ incident records across 6 critical systems
- Appropriate date distributions for Q2 2025 analysis

## Customization

To modify for your specific needs:
1. Update file paths in the `main()` function
2. Adjust system names in KRI processing functions
3. Modify date ranges and thresholds as needed
4. Customize HTML styling in the report generation function

## Troubleshooting

**Issue**: `No engine for filetype: 'xls'`
**Solution**: Use `.xlsx` format instead of `.xls`

**Issue**: `AttributeError: 'list' object has no attribute 'items'`
**Solution**: Ensure the KRI analysis function returns proper dictionary structures

**Issue**: Missing columns in data
**Solution**: Check that your Excel files have the required column names (case-sensitive)