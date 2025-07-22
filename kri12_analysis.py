import os
from datetime import datetime

def extract_critical_system_from_issue_key(issue_key):
    """Extract critical system name from Issue Key column"""
    if not issue_key or str(issue_key).strip() == "":
        return None
    
    issue_key = str(issue_key).strip()
    
    # Skip IMP- entries, they are individual incidents
    if issue_key.startswith('IMP-'):
        return None
    
    # Extract system name before (ITAM-...)
    if '(' in issue_key and 'ITAM-' in issue_key:
        return issue_key.split('(')[0].strip()
    
    return issue_key

def analyze_kri12_from_excel(file_path):
    """Analyze KRI12 from Excel file - incidents exceeding RTO"""
    
    try:
        # Try to import openpyxl
        try:
            from openpyxl import load_workbook
        except ImportError:
            print("❌ openpyxl library not found!")
            print("Please install it using: pip install openpyxl")
            return []
        
        # Load Excel workbook
        print(f"📖 Loading Excel file: {file_path}")
        workbook = load_workbook(file_path)
        worksheet = workbook.active
        
        # Get headers from first row
        headers = []
        for cell in worksheet[1]:
            if cell.value:
                headers.append(cell.value)
        
        print(f"Excel columns found: {headers}")
        
        # Find column indices
        issue_key_col = None
        duration_col = None
        
        for i, header in enumerate(headers):
            if 'Issue Key' in str(header):
                issue_key_col = i
            elif 'Incident duration' in str(header):
                duration_col = i
        
        if issue_key_col is None or duration_col is None:
            print("❌ Required columns not found!")
            print(f"Looking for: 'Issue Key' and 'Incident duration'")
            return []
        
        # RTO threshold: 2 hours = 7200 seconds
        RTO_THRESHOLD = 7200
        
        rto_exceeded_incidents = []
        current_critical_system = None
        
        row_count = 0
        incident_count = 0
        
        # Process each row (starting from row 2, skipping header)
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            row_count += 1
            
            if len(row) <= max(issue_key_col, duration_col):
                continue
                
            issue_key = row[issue_key_col] if issue_key_col < len(row) else ""
            duration = row[duration_col] if duration_col < len(row) else ""
            
            # Check if this row defines a critical system
            critical_system = extract_critical_system_from_issue_key(issue_key)
            
            if critical_system:
                # This is a critical system definition row
                current_critical_system = critical_system
                print(f"Found critical system: {critical_system}")
            elif str(issue_key).startswith('IMP-') and current_critical_system:
                # This is an incident belonging to the current critical system
                incident_count += 1
                
                try:
                    # Convert duration to integer (seconds)
                    duration_seconds = int(duration) if duration and str(duration).isdigit() else 0
                    
                    # Check if duration exceeds RTO threshold
                    if duration_seconds > RTO_THRESHOLD:
                        rto_exceeded_incidents.append({
                            "System": current_critical_system,
                            "Incident": issue_key,
                            "RTO_Exceeded_Seconds": duration_seconds,
                            "RTO_Exceeded_Hours": round(duration_seconds / 3600, 2)
                        })
                        print(f"  ⚠️ RTO EXCEEDED: {issue_key} in {current_critical_system} - {duration_seconds} seconds ({round(duration_seconds/3600, 2)} hours)")
                
                except ValueError:
                    # Skip if duration is not a valid number
                    continue
        
        print(f"\nProcessed {row_count} rows, found {incident_count} incidents")
        print(f"RTO exceeded incidents: {len(rto_exceeded_incidents)}")
        
        return rto_exceeded_incidents
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_kri12_html_report(results):
    """Generate HTML report for KRI12 analysis"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI12 - RTO Exceeded Incidents Analysis</title>
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .exceeded {{
            background-color: #ffcccc;
            color: #cc0000;
            font-weight: bold;
        }}
        .summary {{
            margin-top: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>KRI12 - RTO Exceeded Incidents Analysis</h1>
    <h2>Critical Systems Recovery Time Objective Violations</h2>
    
    <p><strong>KRI12 Definition:</strong> Number of incidents in critical systems resolved longer than RTO</p>
    <p><strong>RTO Threshold:</strong> 2 hours (7200 seconds)</p>
    <p><strong>Target Value:</strong> 0 incidents exceeding RTO for each system</p>
    
    <p style="color: red; font-weight: bold; font-size: 18px;">
        Total incidents exceeding RTO: {len(results)}
    </p>
    
    <table>
        <tr>
            <th>System</th>
            <th>Incident</th>
            <th>RTO Time Which More Than Normal RTO</th>
            <th>Duration (Hours)</th>
        </tr>"""
    
    # Add table rows
    if results:
        for result in results:
            html_content += f"""
        <tr class="exceeded">
            <td>{result['System']}</td>
            <td>{result['Incident']}</td>
            <td>{result['RTO_Exceeded_Seconds']} (seconds)</td>
            <td>{result['RTO_Exceeded_Hours']} hours</td>
        </tr>"""
    else:
        html_content += f"""
        <tr>
            <td colspan="4" style="text-align: center; color: green; font-weight: bold;">
                ✅ No incidents exceeded RTO threshold - KRI12 Target Achieved!
            </td>
        </tr>"""
    
    html_content += f"""
    </table>
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </p>
    
</body>
</html>"""
    
    return html_content

def main():
    """Main function to run KRI12 analysis"""
    
    # Excel file path (as specified by user)
    excel_file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\Incident_Report_for_GRC__KRI_ (1).xlsx"
    
    print("KRI12 - RTO Exceeded Incidents Analysis")
    print("=" * 50)
    print(f"Excel file path: {excel_file_path}")
    print(f"RTO Threshold: 2 hours (7200 seconds)")
    
    # Check if Excel file exists
    if not os.path.exists(excel_file_path):
        print(f"❌ Excel file not found at: {excel_file_path}")
        print("Please check the file path and try again.")
        return
    
    print("✅ Excel file found!")
    
    # Analyze the data directly from Excel
    results = analyze_kri12_from_excel(excel_file_path)
    
    # Print results to console
    print("\n" + "=" * 80)
    print("KRI12 RESULTS - RTO EXCEEDED INCIDENTS")
    print("=" * 80)
    
    if results:
        print(f"{'System':<20} {'Incident':<12} {'RTO Time (seconds)':<20} {'Hours':<10}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['System']:<20} {result['Incident']:<12} {result['RTO_Exceeded_Seconds']:<20} {result['RTO_Exceeded_Hours']:<10}")
    else:
        print("✅ No incidents exceeded RTO threshold!")
        print("🎉 KRI12 Target Achieved - All incidents resolved within 2 hours")
    
    # Generate HTML report
    html_content = generate_kri12_html_report(results)
    
    # Write to file
    output_file = 'KRI12_RTO_Exceeded_Report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ HTML report generated: {output_file}")
    print(f"📊 Total incidents exceeding RTO: {len(results)}")
    
    if results:
        # Group by system
        system_counts = {}
        for result in results:
            system = result['System']
            if system not in system_counts:
                system_counts[system] = 0
            system_counts[system] += 1
        
        print(f"🏢 Critical systems affected: {len(system_counts)}")
        print(f"❌ KRI12 Status: FAILED")
        
        print(f"\n⚠️  Systems with RTO violations:")
        for system, count in sorted(system_counts.items()):
            print(f"   - {system}: {count} incident(s)")
    else:
        print(f"🏢 Critical systems monitored: All within limits")
        print(f"✅ KRI12 Status: PASSED")

if __name__ == "__main__":
    main()