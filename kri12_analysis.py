import os
from datetime import datetime

def analyze_kri12_from_excel(file_path):
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
        
        RTO_THRESHOLD = 120  # 2 hours = 120 minutes
        rto_exceeded_incidents = []
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
                    duration_minutes = int(duration) if duration and str(duration).isdigit() else 0
                    
                    if duration_minutes > RTO_THRESHOLD:
                        rto_exceeded_incidents.append({
                            "System": current_critical_system,
                            "Incident": issue_key,
                            "RTO_Exceeded_Minutes": duration_minutes,
                            "RTO_Exceeded_Hours": round(duration_minutes / 60, 2)
                        })
                except:
                    continue
        
        return rto_exceeded_incidents
        
    except:
        return []

def generate_kri12_html_report(results):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI12 - RTO Exceeded Incidents Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .exceeded {{ background-color: #ffcccc; }}
        .total-count {{ color: red; font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>KRI12 - RTO Exceeded Incidents</h1>
    <p class="total-count">Total incidents exceeding RTO: {len(results)}</p>
    <table>
        <tr>
            <th>System</th>
            <th>Incident</th>
            <th>RTO time which more than normal RTP (minutes)</th>
        </tr>"""
    
    for result in results:
        html_content += f"""
        <tr class="exceeded">
            <td>{result['System']}</td>
            <td>{result['Incident']}</td>
            <td>{result['RTO_Exceeded_Minutes']}</td>
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
    
    # Analyze KRI12
    results = analyze_kri12_from_excel(excel_file_path)
    
    # Generate HTML report
    html_content = generate_kri12_html_report(results)
    
    # Write to file
    with open('KRI12_RTO_Exceeded_Report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully reported!")

if __name__ == "__main__":
    main()