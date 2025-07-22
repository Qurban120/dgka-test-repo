import csv
import os
from datetime import datetime

def extract_month_from_date(date_str):
    """Extract month from date string in format DD/MM/YY HH:MM:SS"""
    if not date_str or date_str == "-" or date_str.strip() == "":
        return None
    
    try:
        # Convert to string and strip whitespace
        date_str = str(date_str).strip()
        # Extract the date part (before space)
        date_part = date_str.split()[0]
        # Parse DD/MM/YY format
        day, month, year = date_part.split('/')
        month_num = int(month)
        
        # Map month numbers to names for Q2
        month_mapping = {
            4: "April",
            5: "May", 
            6: "June"
        }
        
        return month_mapping.get(month_num)
    except:
        return None

def extract_critical_system_from_issue_key(issue_key):
    """Extract critical system name from Issue Key column"""
    if not issue_key or issue_key.strip() == "":
        return None
    
    issue_key = str(issue_key).strip()
    
    # Skip IMP- entries, they are individual incidents
    if issue_key.startswith('IMP-'):
        return None
    
    # Extract system name before (ITAM-...)
    if '(' in issue_key and 'ITAM-' in issue_key:
        return issue_key.split('(')[0].strip()
    
    return issue_key

def analyze_kri10_from_csv(file_path):
    """Analyze KRI10 from CSV file"""
    
    try:
        system_month_counts = {}
        current_critical_system = None
        
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            print(f"CSV columns found: {csv_reader.fieldnames}")
            
            row_count = 0
            incident_count = 0
            
            for row in csv_reader:
                row_count += 1
                
                issue_key = row.get('Issue Key', '')
                start_date = row.get('Incident start date', '')
                
                # Check if this row defines a critical system
                critical_system = extract_critical_system_from_issue_key(issue_key)
                
                if critical_system:
                    # This is a critical system definition row
                    current_critical_system = critical_system
                    print(f"Found critical system: {critical_system}")
                elif issue_key.startswith('IMP-') and current_critical_system:
                    # This is an incident belonging to the current critical system
                    incident_count += 1
                    
                    # Extract month from start date
                    month = extract_month_from_date(start_date)
                    
                    # Only count incidents in Q2 months (April, May, June)
                    if month:
                        key = (current_critical_system, month)
                        if key not in system_month_counts:
                            system_month_counts[key] = 0
                        system_month_counts[key] += 1
            
            print(f"\nProcessed {row_count} rows, found {incident_count} incidents")
        
        # Create results list
        results = []
        critical_systems = set([key[0] for key in system_month_counts.keys()])
        
        # For each critical system, check all Q2 months
        for system in sorted(critical_systems):
            for month in ["April", "May", "June"]:
                count = system_month_counts.get((system, month), 0)
                if count > 0:  # Only include months with incidents
                    results.append({
                        "System": system,
                        "Month": month,
                        "Count of Incidents": count
                    })
        
        return results
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def generate_simple_html_report(results):
    """Generate simple HTML report for KRI10 analysis"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>KRI10 - Critical Systems Incident Analysis Q2 2025</title>
</head>
<body>
    <h1>KRI10 - Critical Systems Incident Analysis</h1>
    <h2>Q2 2025 (April - June)</h2>
    
    <p><strong>KRI10 Definition:</strong> Number of incidents affecting critical systems</p>
    <p><strong>Threshold:</strong> Maximum 2 incidents per critical system per month</p>
    
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>System</th>
            <th>Month</th>
            <th>Count of Incidents</th>
        </tr>"""
    
    # Add table rows
    for result in results:
        html_content += f"""
        <tr>
            <td>{result['System']}</td>
            <td>{result['Month']}</td>
            <td>{result['Count of Incidents']}</td>
        </tr>"""
    
    html_content += f"""
    </table>
    
    <h3>Summary</h3>
    <p>Total incidents analyzed: {sum(r['Count of Incidents'] for r in results)}</p>
    <p>Critical systems monitored: {len(set(r['System'] for r in results))}</p>
    <p>Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
</body>
</html>"""
    
    return html_content

def main():
    """Main function to run KRI10 analysis"""
    
    # Excel file path (as specified by user)
    excel_file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\Incident_Report_for_GRC__KRI_ (1).xlsx"
    csv_file_path = "incident_data_converted.csv"
    
    print("KRI10 - Critical Systems Incident Analysis")
    print("=" * 50)
    print(f"Excel file path: {excel_file_path}")
    
    # Check if Excel file exists (for Windows environment)
    if os.path.exists(excel_file_path):
        print("✅ Excel file found!")
        print("\n⚠️  IMPORTANT: Please convert Excel to CSV format first!")
        print("Steps:")
        print("1. Open the Excel file")
        print("2. Go to File -> Save As")
        print("3. Choose 'CSV (Comma delimited) (*.csv)' format")
        print("4. Save as 'incident_data_converted.csv' in the same directory as this script")
        print("5. Run this script again")
        return
    else:
        print("⚠️  Excel file not found at specified path")
        print("Checking for CSV file instead...")
    
    # Check for CSV file
    if not os.path.exists(csv_file_path):
        print(f"\n❌ CSV file '{csv_file_path}' not found!")
        print("\nPlease:")
        print("1. Convert your Excel file to CSV format")
        print("2. Save it as 'incident_data_converted.csv' in the same directory")
        print("3. Run this script again")
        return
    
    print(f"✅ CSV file found: {csv_file_path}")
    
    # Analyze the data from CSV
    results = analyze_kri10_from_csv(csv_file_path)
    
    if not results:
        print("❌ No data found or error occurred!")
        return
    
    # Print results to console
    print("\n" + "=" * 60)
    print("KRI10 RESULTS")
    print("=" * 60)
    print(f"{'System':<25} {'Month':<10} {'Count'}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['System']:<25} {result['Month']:<10} {result['Count of Incidents']}")
    
    # Generate simple HTML report
    html_content = generate_simple_html_report(results)
    
    # Write to file
    output_file = 'KRI10_Report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ HTML report generated: {output_file}")
    print(f"📊 Total incidents analyzed: {sum(r['Count of Incidents'] for r in results)}")
    print(f"🏢 Critical systems monitored: {len(set(r['System'] for r in results))}")
    
    # Show systems exceeding threshold
    exceeded_systems = [r for r in results if r['Count of Incidents'] > 2]
    if exceeded_systems:
        print(f"\n⚠️  Systems exceeding KRI10 threshold (>2 incidents/month):")
        for system in exceeded_systems:
            print(f"   - {system['System']} in {system['Month']}: {system['Count of Incidents']} incidents")
    else:
        print(f"\n✅ All critical systems are within KRI10 threshold!")

if __name__ == "__main__":
    main()