from datetime import datetime

def parse_incident_data():
    """Parse the incident data from the provided table"""
    
    # Raw data from the table
    incident_data = [
        # BirBank-Business (ITAM-1454566)
        {"Issue Key": "BirBank-Business", "System": "CMS", "Start Date": "21/04/25 08:06:00", "End Date": "22/04/25 09:18:00"},
        {"Issue Key": "BirBank-Business", "System": "Other", "Start Date": "25/04/25 19:38:00", "End Date": "28/04/25 11:56:00"},
        {"Issue Key": "BirBank-Business", "System": "Birbank", "Start Date": "28/04/25 22:42:00", "End Date": "28/04/25 23:45:00"},
        
        # BirBank.EDV (ITAM-1444443)
        {"Issue Key": "BirBank.EDV", "System": "BirBank.EDV", "Start Date": "14/05/25 14:11:00", "End Date": "15/05/25 19:31:00"},
        {"Issue Key": "BirBank.EDV", "System": "BirBank.EDV", "Start Date": "28/05/25 14:14:00", "End Date": "08/06/25 03:52:00"},
        {"Issue Key": "BirBank.EDV", "System": "BirBank.EDV", "Start Date": "12/06/25 15:15:00", "End Date": "12/06/25 15:42:00"},
        
        # BirBank.Loyalty (ITAM-1444442)
        {"Issue Key": "BirBank.Loyalty", "System": "BirBank.Loyalty", "Start Date": "01/04/25 09:10:00", "End Date": "01/04/25 11:30:00"},
        {"Issue Key": "BirBank.Loyalty", "System": "BirBank.Loyalty", "Start Date": "21/06/25 22:38:00", "End Date": "21/06/25 22:53:00"},
        
        # BirBank.Payments (ITAM-1444440)
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "01/04/25 11:07:00", "End Date": "01/04/25 13:33:00"},
        {"Issue Key": "BirBank.Payments", "System": "Other", "Start Date": "02/05/25 00:08:00", "End Date": "02/05/25 00:54:00"},
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "09/05/25 07:51:00", "End Date": "09/05/25 08:33:00"},
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "14/05/25 11:58:00", "End Date": "14/05/25 12:18:00"},
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "01/06/25 12:30:00", "End Date": "02/06/25 11:05:00"},
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "04/06/25 07:55:00", "End Date": "04/06/25 08:33:00"},
        {"Issue Key": "BirBank.Payments", "System": "BirBank.Payments", "Start Date": "18/06/25 17:24:00", "End Date": "18/06/25 17:31:00"},
        
        # BirBank.Transfers (ITAM-1444441)
        {"Issue Key": "BirBank.Transfers", "System": "BirBank.Transfers", "Start Date": "01/05/25 09:31:00", "End Date": "02/05/25 09:00:00"},
        {"Issue Key": "BirBank.Transfers", "System": "BirBank.Transfers", "Start Date": "20/06/25 01:00:00", "End Date": "22/06/25 14:28:00"},
        
        # Birbank (ITAM-1442475)
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "04/04/25 16:20:00", "End Date": "04/04/25 17:37:00"},
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "05/04/25 08:00:00", "End Date": "05/04/25 22:58:00"},
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "02/04/25 22:40:00", "End Date": "08/05/25 16:00:00"},
        {"Issue Key": "Birbank", "System": "Optimus", "Start Date": "30/04/25 10:33:00", "End Date": "30/04/25 11:18:00"},
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "09/06/25 23:50:00", "End Date": "10/06/25 05:00:00"},
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "11/06/25 16:10:00", "End Date": "-"},
        {"Issue Key": "Birbank", "System": "Birbank", "Start Date": "23/06/25 11:47:00", "End Date": "23/06/25 15:30:00"},
        
        # CMS (ITAM-1442104)
        {"Issue Key": "CMS", "System": "CMS", "Start Date": "03/04/25 20:18:00", "End Date": "04/04/25 00:00:00"},
        {"Issue Key": "CMS", "System": "CMS", "Start Date": "18/04/25 19:48:00", "End Date": "18/04/25 20:27:00"},
        {"Issue Key": "CMS", "System": "BirBank-Business", "Start Date": "24/04/25 18:00:00", "End Date": "25/04/25 09:06:00"},
        
        # ELMA BPM (ITAM-1442126)
        {"Issue Key": "ELMA BPM", "System": "Other", "Start Date": "10/04/25 09:44:00", "End Date": "11/04/25 10:27:00"},
        {"Issue Key": "ELMA BPM", "System": "Other", "Start Date": "30/04/25 16:55:00", "End Date": "01/05/25 12:00:00"},
        {"Issue Key": "ELMA BPM", "System": "Other", "Start Date": "17/06/25 09:04:00", "End Date": "17/06/25 09:53:00"},
        
        # TWO (ITAM-1442182)
        {"Issue Key": "TWO", "System": "Atlas", "Start Date": "04/04/25 15:08:00", "End Date": "04/04/25 15:35:00"},
        {"Issue Key": "TWO", "System": "Birbank", "Start Date": "08/06/25 21:18:00", "End Date": "09/06/25 14:21:00"},
        {"Issue Key": "TWO", "System": "Atlas", "Start Date": "08/06/25 21:18:00", "End Date": "09/06/25 14:21:00"},
        {"Issue Key": "TWO", "System": "Telesales", "Start Date": "08/06/25 21:18:00", "End Date": "09/06/25 14:21:00"},
        {"Issue Key": "TWO", "System": "TWO", "Start Date": "15/06/25 12:03:00", "End Date": "15/06/25 12:14:00"},
        
        # Zeus (ITAM-1442192)
        {"Issue Key": "Zeus", "System": "Birbank", "Start Date": "01/04/25 01:12:00", "End Date": "01/04/25 05:45:00"},
        {"Issue Key": "Zeus", "System": "Optimus", "Start Date": "01/05/25 11:50:00", "End Date": "01/05/25 11:57:00"},
        {"Issue Key": "Zeus", "System": "Other", "Start Date": "02/05/25 10:11:00", "End Date": "05/06/25 17:00:00"},
        {"Issue Key": "Zeus", "System": "Optimus", "Start Date": "15/05/25 07:50:00", "End Date": "15/05/25 08:10:00"},
        {"Issue Key": "Zeus", "System": "Optimus", "Start Date": "25/05/25 12:53:00", "End Date": "25/05/25 13:07:00"},
        {"Issue Key": "Zeus", "System": "Optimus", "Start Date": "05/06/25 16:50:00", "End Date": "05/06/25 17:16:00"},
        {"Issue Key": "Zeus", "System": "Zeus", "Start Date": "23/06/25 23:19:00", "End Date": "23/06/25 23:34:00"},
        {"Issue Key": "Zeus", "System": "Other", "Start Date": "23/06/25 23:19:00", "End Date": "23/06/25 23:34:00"},
    ]
    
    return incident_data

def extract_month_from_date(date_str):
    """Extract month from date string in format DD/MM/YY HH:MM:SS"""
    if date_str == "-" or not date_str:
        return None
    
    try:
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

def analyze_kri10():
    """Analyze KRI10 - Number of incidents affecting critical systems"""
    
    # Get incident data
    incidents = parse_incident_data()
    
    # Critical systems are the ones in Issue Key column
    critical_systems = set()
    system_month_counts = {}
    
    for incident in incidents:
        issue_key = incident["Issue Key"]
        start_date = incident["Start Date"]
        
        # Add to critical systems
        critical_systems.add(issue_key)
        
        # Extract month from start date
        month = extract_month_from_date(start_date)
        
        if month:  # Only count incidents in Q2 months
            key = (issue_key, month)
            if key not in system_month_counts:
                system_month_counts[key] = 0
            system_month_counts[key] += 1
    
    # Create results list
    results = []
    
    # For each critical system, check all Q2 months
    for system in sorted(critical_systems):
        for month in ["April", "May", "June"]:
            count = system_month_counts.get((system, month), 0)
            if count > 0:  # Only include months with incidents
                results.append({
                    "System": system,
                    "Month": month,
                    "Count of Incidents": count,
                    "KRI Status": "EXCEEDED" if count > 2 else "WITHIN LIMIT"
                })
    
    return results

def generate_html_report(results):
    """Generate HTML report for KRI10 analysis"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KRI10 - Critical Systems Incident Analysis Q2 2025</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }}
            .kri-info {{
                background-color: #e8f4f8;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            tr:hover {{
                background-color: #e8f4f8;
            }}
            .exceeded {{
                background-color: #ffebee !important;
                color: #c62828;
                font-weight: bold;
            }}
            .within-limit {{
                background-color: #e8f5e8 !important;
                color: #2e7d32;
            }}
            .summary {{
                margin-top: 30px;
                padding: 15px;
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
            }}
            .report-date {{
                text-align: right;
                color: #666;
                font-style: italic;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>KRI10 - Critical Systems Incident Analysis</h1>
            <h2>Q2 2025 (April - June)</h2>
            
            <div class="kri-info">
                <strong>KRI10 Definition:</strong> Number of incidents affecting critical systems. 
                <br><strong>Threshold:</strong> Maximum 2 incidents per critical system per month.
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>System</th>
                        <th>Month</th>
                        <th>Count of Incidents</th>
                        <th>KRI Status</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add table rows
    for result in results:
        status_class = "exceeded" if result["KRI Status"] == "EXCEEDED" else "within-limit"
        html_content += f"""
                    <tr>
                        <td>{result['System']}</td>
                        <td>{result['Month']}</td>
                        <td>{result['Count of Incidents']}</td>
                        <td class="{status_class}">{result['KRI Status']}</td>
                    </tr>
        """
    
    # Calculate summary statistics
    total_incidents = sum(r['Count of Incidents'] for r in results)
    exceeded_count = sum(1 for r in results if r['KRI Status'] == 'EXCEEDED')
    total_system_months = len(results)
    
    html_content += f"""
                </tbody>
            </table>
            
            <div class="summary">
                <h3>Summary</h3>
                <ul>
                    <li><strong>Total System-Month combinations with incidents:</strong> {total_system_months}</li>
                    <li><strong>Total incidents recorded:</strong> {total_incidents}</li>
                    <li><strong>System-Month combinations exceeding KRI threshold:</strong> {exceeded_count}</li>
                    <li><strong>Compliance rate:</strong> {((total_system_months - exceeded_count) / total_system_months * 100):.1f}%</li>
                </ul>
            </div>
            
            <div class="report-date">
                Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main function to run KRI10 analysis"""
    print("Starting KRI10 Analysis...")
    
    # Analyze the data
    results = analyze_kri10()
    
    # Print results to console
    print("\nKRI10 Results:")
    print("=" * 60)
    print(f"{'System':<20} {'Month':<10} {'Count':<8} {'Status'}")
    print("=" * 60)
    
    for result in results:
        status = "⚠️ EXCEEDED" if result["KRI Status"] == "EXCEEDED" else "✅ OK"
        print(f"{result['System']:<20} {result['Month']:<10} {result['Count of Incidents']:<8} {status}")
    
    # Generate HTML report
    html_content = generate_html_report(results)
    
    # Write to file
    with open('KRI10_Critical_Systems_Report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML report generated: KRI10_Critical_Systems_Report.html")
    print(f"📊 Total incidents analyzed: {sum(r['Count of Incidents'] for r in results)}")
    print(f"🏢 Critical systems monitored: {len(set(r['System'] for r in results))}")
    
    # Show systems exceeding threshold
    exceeded_systems = [r for r in results if r['KRI Status'] == 'EXCEEDED']
    if exceeded_systems:
        print(f"\n⚠️  Systems exceeding KRI10 threshold (>2 incidents/month):")
        for system in exceeded_systems:
            print(f"   - {system['System']} in {system['Month']}: {system['Count of Incidents']} incidents")
    else:
        print(f"\n✅ All critical systems are within KRI10 threshold!")

if __name__ == "__main__":
    main()