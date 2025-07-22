import os
from datetime import datetime

def analyze_kri19_from_excel(file_path):
    try:
        from openpyxl import load_workbook
        
        workbook = load_workbook(file_path)
        worksheet = workbook.active
        
        # Find columns
        headers = [cell.value for cell in worksheet[1] if cell.value]
        issue_key_col = next((i for i, h in enumerate(headers) if 'Issue Key' in str(h)), None)
        duration_col = next((i for i, h in enumerate(headers) if 'Incident duration' in str(h)), None)
        
        if issue_key_col is None or duration_col is None:
            return []
        
        RTO_THRESHOLD = 7200  # 2 hours = 7200 seconds
        system_durations = {}  # {system: [list of durations]}
        current_critical_system = None
        
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if len(row) <= max(issue_key_col, duration_col):
                continue
                
            issue_key = row[issue_key_col] if issue_key_col < len(row) else ""
            duration = row[duration_col] if duration_col < len(row) else ""
            
            # Check if critical system
            if issue_key and not str(issue_key).startswith('IMP-'):
                if '(' in str(issue_key) and 'ITAM-' in str(issue_key):
                    current_critical_system = str(issue_key).split('(')[0].strip()
            elif str(issue_key).startswith('IMP-') and current_critical_system:
                try:
                    duration_seconds = int(duration) if duration and str(duration).isdigit() else 0
                    
                    # Collect all incident durations for each system
                    if duration_seconds > 0:  # Only valid durations
                        if current_critical_system not in system_durations:
                            system_durations[current_critical_system] = []
                        system_durations[current_critical_system].append(duration_seconds)
                except:
                    continue
        
        # Group Birbank systems together (except BirBank-Business)
        birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
        grouped_durations = {}
        
        for system, durations in system_durations.items():
            if system in birbank_systems:
                # Group all Birbank systems under "Birbank"
                if "Birbank" not in grouped_durations:
                    grouped_durations["Birbank"] = []
                grouped_durations["Birbank"].extend(durations)
            else:
                # Keep other systems as they are (including BirBank-Business)
                grouped_durations[system] = durations
        
        # Calculate average durations
        results = []
        for system, durations in sorted(grouped_durations.items()):
            if durations:  # Only systems with incidents
                total_duration = sum(durations)
                incident_count = len(durations)
                average_duration = total_duration / incident_count
                
                results.append({
                    "System": system,
                    "Total_Duration": total_duration,
                    "Incident_Count": incident_count,
                    "Average_Duration_Seconds": int(average_duration),
                    "Average_Duration_Hours": round(average_duration / 3600, 2),
                    "Status": "EXCEEDED RTO" if average_duration > RTO_THRESHOLD else "WITHIN RTO"
                })
        
        return results
    except:
        return []

def generate_html_report(results):
    # Count systems exceeding RTO
    exceeded_count = len([r for r in results if r['Average_Duration_Seconds'] > 7200])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI19 - Average Incident Resolution Time Analysis</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .exceeded {{ background-color: #ffcccc; color: #cc0000; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>KRI19 - Average Incident Resolution Time Analysis</h1>
    
    <p><strong>KRI19 Definition:</strong> Average incident resolution time for critical systems</p>
    <p><strong>RTO Threshold:</strong> 2 hours (7200 seconds)</p>
    <p><strong>Target:</strong> Average resolution time should be less than RTO for each system</p>
    
    <p style="color: red; font-weight: bold; font-size: 18px;">
        Systems exceeding RTO: {exceeded_count}
    </p>
    
    <table>
        <tr>
            <th>System</th>
            <th>Total Incidents</th>
            <th>Average Duration (Seconds)</th>
            <th>Average Duration (Hours)</th>
            <th>Status</th>
        </tr>"""
    
    if results:
        for result in results:
            row_class = ' class="exceeded"' if result['Average_Duration_Seconds'] > 7200 else ''
            html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Incident_Count']}</td>
            <td>{result['Average_Duration_Seconds']}</td>
            <td>{result['Average_Duration_Hours']}</td>
            <td>{result['Status']}</td>
        </tr>"""
    else:
        html_content += f"""
        <tr>
            <td colspan="5" style="text-align: center; color: green; font-weight: bold;">
                ✅ No incidents found for analysis
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
    
    results = analyze_kri19_from_excel(excel_file_path)
    
    html_content = generate_html_report(results)
    
    with open('KRI19_Average_Duration_Report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully reported!")

if __name__ == "__main__":
    main()