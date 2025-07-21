import pandas as pd
from datetime import datetime, timedelta
import os

def analyze_incidents(file_path):
    """
    Analyze incident data and generate HTML report
    """
    
    # Read Excel file
    try:
        df = pd.read_excel(file_path)
        print(f"Successfully loaded {len(df)} rows from Excel file")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Define Quarter 2 end date (June 30, 2025)
    q2_end = datetime(2025, 6, 30)
    
    # System mapping based on Issue Key patterns
    system_mapping = {
        'BirBank-Business': 'BirBank-Business',
        'BirBank.EDV': 'Birbank',
        'BirBank.Loyalty': 'Birbank', 
        'BirBank.Payments': 'Birbank',
        'BirBank.Transfers': 'Birbank',
        'Birbank': 'Birbank',
        'CMS': 'CMS',
        'ELMA BPM': 'ELMA BPM',
        'TWO': 'TWO',
        'Zeus': 'Zeus'
    }
    
    # Process data
    results = []
    
    # Clean and prepare data
    df['Issue Key'] = df['Issue Key'].astype(str)
    df['Incident end date'] = pd.to_datetime(df['Incident end date'], errors='coerce')
    
    # Filter out rows without valid end dates
    df_valid = df.dropna(subset=['Incident end date'])
    
    print(f"Processing {len(df_valid)} valid incidents...")
    
    # Group by system based on Issue Key
    system_incidents = {}
    
    for index, row in df_valid.iterrows():
        issue_key = row['Issue Key']
        end_date = row['Incident end date']
        
        # Determine system based on Issue Key
        system = None
        
        if 'BirBank-Business' in issue_key:
            system = 'BirBank-Business'
        elif any(birbank_key in issue_key for birbank_key in ['BirBank.EDV', 'BirBank.Loyalty', 'BirBank.Payments', 'BirBank.Transfers', 'Birbank']):
            system = 'Birbank'
        elif 'CMS' in issue_key:
            system = 'CMS'
        elif 'ELMA BPM' in issue_key:
            system = 'ELMA BPM'
        elif 'TWO' in issue_key:
            system = 'TWO'
        elif 'Zeus' in issue_key:
            system = 'Zeus'
        else:
            # Check if it's an IMP- ticket and look at impacted systems
            if issue_key.startswith('IMP-'):
                impacted_systems = str(row.get('Impacted Systems', ''))
                if 'CMS' in impacted_systems:
                    system = 'CMS'
                elif 'ELMA' in impacted_systems or 'Other' in impacted_systems:
                    # For Other systems, we need to check more carefully
                    if 'ELMA' in impacted_systems:
                        system = 'ELMA BPM'
                    else:
                        continue  # Skip if we can't determine the system
                elif any(birbank_term in impacted_systems for birbank_term in ['Birbank', 'BirBank']):
                    system = 'Birbank'
                elif 'TWO' in impacted_systems:
                    system = 'TWO'
                elif 'Zeus' in impacted_systems:
                    system = 'Zeus'
                elif 'Atlas' in impacted_systems:
                    system = 'TWO'  # Atlas is part of TWO system
                elif 'Telesales' in impacted_systems:
                    system = 'TWO'  # Telesales is part of TWO system
                elif 'Optimus' in impacted_systems:
                    system = 'Zeus'  # Optimus is part of Zeus system
        
        if system:
            if system not in system_incidents:
                system_incidents[system] = []
            system_incidents[system].append({
                'issue_key': issue_key,
                'end_date': end_date,
                'impacted_systems': row.get('Impacted Systems', '')
            })
    
    print(f"Found incidents for systems: {list(system_incidents.keys())}")
    
    # Find latest incident for each system and calculate days until Q2 end
    for system, incidents in system_incidents.items():
        if incidents:
            # Sort by end date to get the latest incident
            latest_incident = max(incidents, key=lambda x: x['end_date'])
            latest_end_date = latest_incident['end_date']
            
            # Calculate days until Q2 end
            days_until_q2_end = (q2_end - latest_end_date).days
            
            results.append({
                'System': system,
                'Incident end date': latest_end_date.strftime('%d/%m/%y'),
                'Days until Quarter2 end': days_until_q2_end
            })
            
            print(f"{system}: Latest incident ended on {latest_end_date.strftime('%d/%m/%y')}, "
                  f"{days_until_q2_end} days until Q2 end")
    
    # Sort results by system name
    results.sort(key=lambda x: x['System'])
    
    # Generate HTML report
    generate_html_report(results)
    
    return results

def generate_html_report(results):
    """
    Generate HTML report from results
    """
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KRI8 - Critical Systems Incident Analysis</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 10px;
                font-size: 28px;
            }
            .subtitle {
                text-align: center;
                color: #7f8c8d;
                margin-bottom: 30px;
                font-size: 16px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
            }
            th {
                background-color: #34495e;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #ecf0f1;
            }
            tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            tr:hover {
                background-color: #e8f4f8;
            }
            .days-good {
                color: #27ae60;
                font-weight: bold;
            }
            .days-warning {
                color: #f39c12;
                font-weight: bold;
            }
            .days-critical {
                color: #e74c3c;
                font-weight: bold;
            }
            .summary {
                background-color: #ecf0f1;
                padding: 20px;
                border-radius: 5px;
                margin-top: 30px;
            }
            .summary h3 {
                color: #2c3e50;
                margin-top: 0;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #7f8c8d;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>KRI8 - Critical Systems Incident Analysis</h1>
            <p class="subtitle">Days since last critical incident until Quarter 2 end (Target: >120 days)</p>
            
            <table>
                <thead>
                    <tr>
                        <th>System</th>
                        <th>Incident End Date</th>
                        <th>Days until Quarter 2 End</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add table rows
    total_systems = len(results)
    systems_meeting_target = 0
    
    for result in results:
        days = result['Days until Quarter2 end']
        
        # Determine CSS class based on days
        if days >= 120:
            css_class = "days-good"
            systems_meeting_target += 1
        elif days >= 90:
            css_class = "days-warning"
        else:
            css_class = "days-critical"
        
        html_content += f"""
                    <tr>
                        <td><strong>{result['System']}</strong></td>
                        <td>{result['Incident end date']}</td>
                        <td class="{css_class}">{days} days</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            
            <div class="summary">
                <h3>Summary</h3>
                <p><strong>Total Systems Analyzed:</strong> {total_systems}</p>
                <p><strong>Systems Meeting Target (≥120 days):</strong> {systems_meeting_target} / {total_systems}</p>
                <p><strong>Compliance Rate:</strong> {(systems_meeting_target/total_systems*100):.1f}%</p>
                <p><strong>Target:</strong> All systems should have >120 days since last critical incident</p>
            </div>
            
            <div class="footer">
                <p>Report generated on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p>Quarter 2 End Date: 30/06/2025</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write HTML file
    output_file = "KRI8_Critical_Systems_Report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nHTML report generated: {output_file}")
    print(f"Systems meeting target (≥120 days): {systems_meeting_target}/{total_systems}")

def main():
    """
    Main function to run the analysis
    """
    # File path - update this to your actual file path
    file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\Incident_Report_for_GRC__KRI_ (1).xlsx"
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        print("Please update the file_path variable with the correct path to your Excel file.")
        return
    
    print("Starting KRI8 Critical Systems Incident Analysis...")
    print("=" * 60)
    
    # Run analysis
    results = analyze_incidents(file_path)
    
    if results:
        print("\nAnalysis completed successfully!")
        print("=" * 60)
        
        # Display results in console
        print("\nResults:")
        print("-" * 60)
        for result in results:
            days = result['Days until Quarter2 end']
            status = "✓ MEETS TARGET" if days >= 120 else "⚠ BELOW TARGET"
            print(f"{result['System']:<20} | {result['Incident end date']:<12} | {days:>3} days | {status}")
    else:
        print("No results generated. Please check the data and file path.")

if __name__ == "__main__":
    main()