import os
from datetime import datetime, date

def analyze_kri8_from_excel(file_path):
    try:
        from openpyxl import load_workbook
        
        workbook = load_workbook(file_path)
        worksheet = workbook.active
        
        # Find columns
        headers = [cell.value for cell in worksheet[1] if cell.value]
        issue_key_col = next((i for i, h in enumerate(headers) if 'Issue Key' in str(h)), None)
        start_date_col = next((i for i, h in enumerate(headers) if 'Incident start date' in str(h)), None)
        
        if issue_key_col is None or start_date_col is None:
            return []
        
        # KRI8 target systems
        target_systems = ["Birbank", "BirBank-Business", "ODIN", "ELMA BPM", "Optimus", "CMS", "TWO", "Zeus"]
        
        # Group Birbank systems (except BirBank-Business)
        birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
        
        system_last_incidents = {}  # {system: latest_date}
        current_critical_system = None
        
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if len(row) <= max(issue_key_col, start_date_col):
                continue
                
            issue_key = row[issue_key_col] if issue_key_col < len(row) else ""
            start_date = row[start_date_col] if start_date_col < len(row) else ""
            
            # Check if critical system
            if issue_key and not str(issue_key).startswith('IMP-'):
                if '(' in str(issue_key) and 'ITAM-' in str(issue_key):
                    current_critical_system = str(issue_key).split('(')[0].strip()
            elif str(issue_key).startswith('IMP-') and current_critical_system:
                # Extract date from start_date
                incident_date = None
                try:
                    if hasattr(start_date, 'date'):
                        incident_date = start_date.date()
                    else:
                        date_str = str(start_date).strip()
                        if date_str and date_str != "-":
                            date_part = date_str.split()[0]
                            day, month, year = date_part.split('/')
                            # Assume 25 means 2025
                            full_year = 2000 + int(year) if int(year) < 50 else 1900 + int(year)
                            incident_date = date(full_year, int(month), int(day))
                except:
                    continue
                
                if incident_date:
                    # Group Birbank systems
                    system_name = current_critical_system
                    if current_critical_system in birbank_systems:
                        system_name = "Birbank"
                    
                    # Keep track of latest incident date for each system
                    if system_name not in system_last_incidents:
                        system_last_incidents[system_name] = incident_date
                    else:
                        if incident_date > system_last_incidents[system_name]:
                            system_last_incidents[system_name] = incident_date
        
        # Q2 2025 end date (June 30, 2025)
        quarter_end = date(2025, 6, 30)
        
        # Calculate days since last incident for each target system
        results = []
        for system in target_systems:
            if system in system_last_incidents:
                last_incident_date = system_last_incidents[system]
                days_since_last = (quarter_end - last_incident_date).days
                
                results.append({
                    "System": system,
                    "Last_Incident_Date": last_incident_date.strftime('%d/%m/%Y'),
                    "Days_Since_Last": days_since_last,
                    "Status": "TARGET MET" if days_since_last >= 120 else "TARGET NOT MET"
                })
            else:
                # No incidents found for this system in the data
                results.append({
                    "System": system,
                    "Last_Incident_Date": "No incidents found",
                    "Days_Since_Last": "N/A",
                    "Status": "TARGET MET"  # No incidents is good
                })
        
        return sorted(results, key=lambda x: x['System'])
        
    except:
        return []

def generate_html_report(results):
    # Count systems meeting target
    met_target_count = len([r for r in results if r['Status'] == 'TARGET MET'])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI8 - Days Since Last Incident Analysis</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .not-met {{ background-color: #ffcccc; color: #cc0000; font-weight: bold; }}
        .met {{ background-color: #ccffcc; color: #008000; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>KRI8 - Days Since Last Incident Analysis</h1>
    
    <p><strong>KRI8 Definition:</strong> Days from last incident in critical system to end of quarter</p>
    <p><strong>Target:</strong> More than 120 days (systems should remain incident-free)</p>
    <p><strong>Quarter End:</strong> June 30, 2025</p>
    
    <p style="color: green; font-weight: bold; font-size: 18px;">
        Systems meeting target: {met_target_count} / {len(results)}
    </p>
    
    <table>
        <tr>
            <th>System</th>
            <th>Last Incident Date</th>
            <th>Days Since Last Incident</th>
            <th>Status</th>
        </tr>"""
    
    if results:
        for result in results:
            if result['Status'] == 'TARGET MET':
                row_class = ' class="met"'
            else:
                row_class = ' class="not-met"'
                
            html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Last_Incident_Date']}</td>
            <td>{result['Days_Since_Last']}</td>
            <td>{result['Status']}</td>
        </tr>"""
    else:
        html_content += f"""
        <tr>
            <td colspan="4" style="text-align: center; color: gray;">
                No data available for analysis
            </td>
        </tr>"""
    
    html_content += """
    </table>
</body>
</html>"""
    
    return html_content

def main():
    excel_file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\Incident_Report_for_GRC__KRI_ (1).xlsx"
    
    if not os.path.exists(excel_file_path):
        print("Excel file not found!")
        return
    
    results = analyze_kri8_from_excel(excel_file_path)
    
    html_content = generate_html_report(results)
    
    with open('KRI8_Days_Since_Last_Report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully reported!")

if __name__ == "__main__":
    main()