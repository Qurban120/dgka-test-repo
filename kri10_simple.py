import os
from datetime import datetime

def analyze_kri10_from_excel(file_path):
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
        
        system_month_counts = {}
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
                # Extract month from start date
                month = None
                try:
                    if hasattr(start_date, 'month'):
                        month_num = start_date.month
                    else:
                        date_str = str(start_date).strip()
                        if date_str and date_str != "-":
                            date_part = date_str.split()[0]
                            day, month_part, year = date_part.split('/')
                            month_num = int(month_part)
                    
                    month_mapping = {4: "April", 5: "May", 6: "June"}
                    month = month_mapping.get(month_num)
                except:
                    pass
                
                if month:
                    key = (current_critical_system, month)
                    if key not in system_month_counts:
                        system_month_counts[key] = 0
                    system_month_counts[key] += 1
        
        # Create results
        results = []
        critical_systems = set([key[0] for key in system_month_counts.keys()])
        
        for system in sorted(critical_systems):
            for month in ["April", "May", "June"]:
                count = system_month_counts.get((system, month), 0)
                if count > 0:
                    results.append({
                        "System": system,
                        "Month": month,
                        "Count of Incidents": count
                    })
        
        return results
    except:
        return []

def generate_html_report(results):
    # Count systems exceeding threshold
    exceeded_count = len([r for r in results if r['Count of Incidents'] > 2])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI10 - Critical Systems Incident Analysis Q2 2025</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .exceeded {{ background-color: #ffcccc; color: #cc0000; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>KRI10 - Critical Systems Incident Analysis</h1>
    <h2>Q2 2025 (April - June)</h2>
    
    <p><strong>KRI10 Definition:</strong> Number of incidents affecting critical systems</p>
    <p><strong>Threshold:</strong> Maximum 2 incidents per critical system per month</p>
    
    <p style="color: red; font-weight: bold; font-size: 18px;">
        Systems exceeding threshold: {exceeded_count}
    </p>
    
    <table>
        <tr>
            <th>System</th>
            <th>Month</th>
            <th>Count of Incidents</th>
        </tr>"""
    
    for result in results:
        row_class = ' class="exceeded"' if result['Count of Incidents'] > 2 else ''
        html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Month']}</td>
            <td>{result['Count of Incidents']}</td>
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
    
    results = analyze_kri10_from_excel(excel_file_path)
    
    html_content = generate_html_report(results)
    
    with open('KRI10_Report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully reported!")

if __name__ == "__main__":
    main()