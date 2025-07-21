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
    
    # Process data
    results = []
    
    # Clean and prepare data
    df['Issue Key'] = df['Issue Key'].astype(str)
    df['Incident end date'] = pd.to_datetime(df['Incident end date'], errors='coerce')
    
    # Filter out rows without valid end dates
    df_valid = df.dropna(subset=['Incident end date'])
    
    print(f"Processing {len(df_valid)} valid incidents...")
    
    # Debug: Print all unique Issue Keys to see what we have
    print("\nAll Issue Keys in data:")
    for idx, row in df.iterrows():
        print(f"  {row['Issue Key']} -> End date: {row['Incident end date']}")
    print()
    
    # Group by system based on Issue Key
    system_incidents = {}
    
    # First, let's identify which IMP tickets belong to which main systems
    # by looking at the parent system in the Excel structure
    elma_imp_tickets = []
    current_main_system = None
    
    for index, row in df.iterrows():
        issue_key = row['Issue Key']
        
        # Track the main system we're currently under
        if not issue_key.startswith('IMP-'):
            current_main_system = issue_key
        else:
            # This is an IMP ticket - associate it with the current main system
            if current_main_system and 'ELMA BPM' in current_main_system:
                elma_imp_tickets.append(issue_key)
    
    print(f"ELMA BPM IMP tickets identified: {elma_imp_tickets}")
    
    for index, row in df_valid.iterrows():
        issue_key = row['Issue Key']
        end_date = row['Incident end date']
        impacted_systems = str(row.get('Impacted Systems', ''))
        
        print(f"Processing: {issue_key} -> {impacted_systems}")
        
        # Determine system based on Issue Key
        system = None
        
        # Direct system matches in Issue Key
        if 'BirBank-Business' in issue_key:
            system = 'BirBank-Business'
        elif 'ELMA BPM' in issue_key:
            system = 'ELMA BPM'
        elif any(birbank_key in issue_key for birbank_key in ['BirBank.EDV', 'BirBank.Loyalty', 'BirBank.Payments', 'BirBank.Transfers']):
            system = 'Birbank'
        elif issue_key.startswith('Birbank'):
            system = 'Birbank'
        elif 'CMS' in issue_key:
            system = 'CMS'
        elif 'TWO' in issue_key:
            system = 'TWO'
        elif 'Zeus' in issue_key:
            system = 'Zeus'
        else:
            # For IMP- tickets, check impacted systems and our ELMA mapping
            if issue_key.startswith('IMP-'):
                # First check if this is an ELMA BPM ticket based on our mapping
                if issue_key in elma_imp_tickets:
                    system = 'ELMA BPM'
                elif 'BirBank-Business' in impacted_systems:
                    system = 'BirBank-Business'
                elif 'CMS' in impacted_systems:
                    system = 'CMS'
                elif 'ELMA' in impacted_systems:
                    system = 'ELMA BPM'
                elif any(birbank_term in impacted_systems for birbank_term in ['Birbank', 'BirBank.', 'BirBank (']):
                    system = 'Birbank'
                elif 'TWO' in impacted_systems:
                    system = 'TWO'
                elif 'Atlas' in impacted_systems:
                    system = 'TWO'  # Atlas is part of TWO system
                elif 'Telesales' in impacted_systems:
                    system = 'TWO'  # Telesales is part of TWO system
                elif 'Zeus' in impacted_systems:
                    system = 'Zeus'
                elif 'Optimus' in impacted_systems:
                    system = 'Zeus'  # Optimus is part of Zeus system
                elif 'Other' in impacted_systems:
                    # For remaining "Other" systems, we need more context - skip for now
                    print(f"  -> Skipping unidentified 'Other' system: {impacted_systems}")
                    continue
        
        if system:
            print(f"  -> Assigned to system: {system}")
            if system not in system_incidents:
                system_incidents[system] = []
            system_incidents[system].append({
                'issue_key': issue_key,
                'end_date': end_date,
                'impacted_systems': impacted_systems
            })
        else:
            print(f"  -> Could not determine system for: {issue_key}")
    
    print(f"\nFound incidents for systems: {list(system_incidents.keys())}")
    
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
    
    # Check for systems with no incidents (should show as meeting target)
    all_expected_systems = ['BirBank-Business', 'Birbank', 'CMS', 'ELMA BPM', 'TWO', 'Zeus']
    found_systems = [result['System'] for result in results]
    
    for expected_system in all_expected_systems:
        if expected_system not in found_systems:
            print(f"\n{expected_system}: No incidents found - assuming target met (>120 days)")
            results.append({
                'System': expected_system,
                'Incident end date': 'No incidents',
                'Days until Quarter2 end': 999  # Large number to indicate no recent incidents
            })
    
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
        
        # Handle special case for no incidents
        days_display = f"{days} days" if days < 999 else "No recent incidents (>120 days)"
        
        html_content += f"""
                    <tr>
                        <td><strong>{result['System']}</strong></td>
                        <td>{result['Incident end date']}</td>
                        <td class="{css_class}">{days_display}</td>
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
            if days >= 999:
                status = "✓ MEETS TARGET (No incidents)"
                days_str = "No incidents"
            else:
                status = "✓ MEETS TARGET" if days >= 120 else "⚠ BELOW TARGET"
                days_str = f"{days} days"
            print(f"{result['System']:<20} | {result['Incident end date']:<15} | {days_str:<15} | {status}")
    else:
        print("No results generated. Please check the data and file path.")

if __name__ == "__main__":
    main()