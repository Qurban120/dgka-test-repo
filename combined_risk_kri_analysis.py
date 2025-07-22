import pandas as pd
import os
from datetime import datetime, date

def analyze_risk_data(file_path):
    """Analyze risk data from the first Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Select required columns
        df = df[['Risk status', 'Risk növü', 'Məxsusi risk dərəcəsi', 'Riskin aşkarlanma tarixi', 'Prosesin sahibi', 'Nəzarət tədbirinin təsviri']]
        
        # Convert date to datetime format
        df['Riskin aşkarlanma tarixi'] = pd.to_datetime(df['Riskin aşkarlanma tarixi'], errors='coerce')
        
        # Parameters
        year = 2025
        second_quarter_months = [4, 5, 6]
        
        # Convert risk status to lowercase and clean spaces
        df['Risk status'] = df['Risk status'].astype(str).str.strip().str.lower()
        
        # Remove cancelled risks
        df = df[df['Risk status'] != 'ləğv edilmiş']
        
        # Only IT risks
        df = df[df['Risk növü'] == 'İT']
        
        # --- 1. Delayed and not submitted on time risks (Critical and High/Medium) ---
        
        # Critical risks - delayed and not submitted on time
        df_critical = df[df['Məxsusi risk dərəcəsi'] == 'Kritik']
        total_critical = df_critical.shape[0]
        filtered_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_critical['Risk status'].isin(['gecikdirilmiş', 'icra tarixi vaxtında təqdim edilməmiş']))
        ]
        filtered_critical_count = filtered_critical.shape[0]
        percent_critical_filtered = round((filtered_critical_count / total_critical) * 100, 2) if total_critical > 0 else 0.0
        
        # High and Medium risks - delayed and not submitted on time
        df_high_medium = df[df['Məxsusi risk dərəcəsi'].isin(['Yüksək', 'Orta'])]
        total_high_medium = df_high_medium.shape[0]
        filtered_high_medium = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_high_medium['Risk status'].isin(['gecikdirilmiş', 'icra tarixi vaxtında təqdim edilməmiş']))
        ]
        filtered_high_medium_count = filtered_high_medium.shape[0]
        percent_high_medium_filtered = round((filtered_high_medium_count / total_high_medium) * 100, 2) if total_high_medium > 0 else 0.0
        
        # --- 2. Risks without owner or control measure (Critical and High/Medium) ---
        
        # Critical risks without owner or control measure in current quarter
        owner_empty_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_critical['Prosesin sahibi'].isna() | (df_critical['Prosesin sahibi'].str.strip() == '-'))
        ]
        control_empty_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_critical['Nəzarət tədbirinin təsviri'].isna() | (df_critical['Nəzarət tədbirinin təsviri'].str.strip() == '-'))
        ]
        delayed_critical = pd.concat([owner_empty_critical, control_empty_critical]).drop_duplicates()
        delayed_critical_count = delayed_critical.shape[0]
        percent_critical_missing = round((delayed_critical_count / total_critical) * 100, 2) if total_critical > 0 else 0.0
        
        # High and Medium risks without owner or control measure in current quarter
        owner_empty_hm = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_high_medium['Prosesin sahibi'].isna() | (df_high_medium['Prosesin sahibi'].str.strip() == '-'))
        ]
        control_empty_hm = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == year) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin(second_quarter_months)) &
            (df_high_medium['Nəzarət tədbirinin təsviri'].isna() | (df_high_medium['Nəzarət tədbirinin təsviri'].str.strip() == '-'))
        ]
        delayed_hm = pd.concat([owner_empty_hm, control_empty_hm]).drop_duplicates()
        delayed_hm_count = delayed_hm.shape[0]
        percent_hm_missing = round((delayed_hm_count / total_high_medium) * 100, 2) if total_high_medium > 0 else 0.0
        
        return {
            'filtered_critical_count': filtered_critical_count,
            'total_critical': total_critical,
            'percent_critical_filtered': percent_critical_filtered,
            'filtered_high_medium_count': filtered_high_medium_count,
            'total_high_medium': total_high_medium,
            'percent_high_medium_filtered': percent_high_medium_filtered,
            'delayed_critical_count': delayed_critical_count,
            'percent_critical_missing': percent_critical_missing,
            'delayed_hm_count': delayed_hm_count,
            'percent_hm_missing': percent_hm_missing,
            'year': year
        }
    except Exception as e:
        print(f"Error analyzing risk data: {e}")
        return None

def analyze_all_kris_from_excel(file_path):
    """Analyze KRI data from the second Excel file"""
    try:
        from openpyxl import load_workbook
        
        workbook = load_workbook(file_path)
        worksheet = workbook.active
        
        # Find columns
        headers = [cell.value for cell in worksheet[1] if cell.value]
        issue_key_col = next((i for i, h in enumerate(headers) if 'Issue Key' in str(h)), None)
        start_date_col = next((i for i, h in enumerate(headers) if 'Incident start date' in str(h)), None)
        end_date_col = next((i for i, h in enumerate(headers) if 'Incident end date' in str(h)), None)
        duration_col = next((i for i, h in enumerate(headers) if 'Incident duration' in str(h)), None)
        
        if issue_key_col is None or start_date_col is None or duration_col is None:
            return {}, [], {}, {}, {}
        
        RTO_THRESHOLD = 120  # 2 hours = 120 minutes
        
        # Data structures for different KRIs
        system_month_counts = {}  # KRI10
        rto_exceeded_incidents = []  # KRI12
        system_within_rto_counts = {}  # KRI13
        system_durations = {}  # KRI19
        system_last_incidents = {}  # KRI8
        
        current_critical_system = None
        
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if len(row) <= max(issue_key_col, start_date_col, duration_col):
                continue
                
            issue_key = row[issue_key_col] if issue_key_col < len(row) else ""
            start_date = row[start_date_col] if start_date_col < len(row) else ""
            end_date = row[end_date_col] if end_date_col is not None and end_date_col < len(row) else ""
            duration = row[duration_col] if duration_col < len(row) else ""
            
            # Check if critical system
            if issue_key and not str(issue_key).startswith('IMP-'):
                if '(' in str(issue_key) and 'ITAM-' in str(issue_key):
                    current_critical_system = str(issue_key).split('(')[0].strip()
            elif str(issue_key).startswith('IMP-') and current_critical_system:
                
                # KRI10: Monthly incident counts
                month = None
                incident_date = None
                try:
                    if hasattr(start_date, 'month'):
                        month_num = start_date.month
                        incident_date = start_date.date()
                    else:
                        date_str = str(start_date).strip()
                        if date_str and date_str != "-":
                            date_part = date_str.split()[0]
                            day, month_part, year = date_part.split('/')
                            month_num = int(month_part)
                            # For KRI8 date calculation
                            full_year = 2000 + int(year) if int(year) < 50 else 1900 + int(year)
                            incident_date = date(full_year, int(month_part), int(day))
                    
                    month_mapping = {4: "April", 5: "May", 6: "June"}
                    month = month_mapping.get(month_num)
                except:
                    pass
                
                if month:
                    key = (current_critical_system, month)
                    if key not in system_month_counts:
                        system_month_counts[key] = 0
                    system_month_counts[key] += 1
                
                # KRI8: Track last incident date
                if incident_date:
                    if current_critical_system not in system_last_incidents:
                        system_last_incidents[current_critical_system] = incident_date
                    else:
                        if incident_date > system_last_incidents[current_critical_system]:
                            system_last_incidents[current_critical_system] = incident_date
                
                # KRI12, KRI13, KRI19: Duration-based analysis (duration is in minutes)
                # Check if end date is missing (marked as "-") - this means RTO exceeded
                end_date_missing = (str(end_date).strip() == "-" or str(end_date).strip() == "")
                
                try:
                    duration_minutes = int(duration) if duration and str(duration).isdigit() else 0
                    
                    # If end date is missing, treat as RTO exceeded
                    if end_date_missing and current_critical_system:
                        rto_exceeded_incidents.append({
                            "System": current_critical_system,
                            "Incident": issue_key,
                            "RTO_Exceeded_Minutes": "Ongoing (no end date)"
                        })
                    elif duration_minutes > 0:
                        # KRI19: Collect all durations
                        if current_critical_system not in system_durations:
                            system_durations[current_critical_system] = []
                        system_durations[current_critical_system].append(duration_minutes)
                        
                        # KRI12: RTO exceeded incidents
                        if duration_minutes > RTO_THRESHOLD:
                            rto_exceeded_incidents.append({
                                "System": current_critical_system,
                                "Incident": issue_key,
                                "RTO_Exceeded_Minutes": duration_minutes,
                                "RTO_Exceeded_Hours": round(duration_minutes / 60, 2)
                            })
                        
                        # KRI13: Within RTO incidents
                        if duration_minutes <= RTO_THRESHOLD:
                            if current_critical_system not in system_within_rto_counts:
                                system_within_rto_counts[current_critical_system] = 0
                            system_within_rto_counts[current_critical_system] += 1
                except:
                    continue
        
        return system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations, system_last_incidents
        
    except Exception as e:
        print(f"Error analyzing KRI data: {e}")
        return {}, [], [], [], {}

def process_kri8(system_last_incidents):
    # KRI8 target systems (only existing ones from data)
    target_systems = ["Birbank", "BirBank-Business", "ELMA BPM", "CMS", "TWO", "Zeus"]
    
    # Group Birbank systems (except BirBank-Business)
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    grouped_last_incidents = {}
    
    for system, last_date in system_last_incidents.items():
        if system in birbank_systems:
            if "Birbank" not in grouped_last_incidents:
                grouped_last_incidents["Birbank"] = last_date
            else:
                if last_date > grouped_last_incidents["Birbank"]:
                    grouped_last_incidents["Birbank"] = last_date
        else:
            grouped_last_incidents[system] = last_date
    
    # Q2 2025 end date (June 30, 2025)
    quarter_end = date(2025, 6, 30)
    
    results = []
    for system in target_systems:
        if system in grouped_last_incidents:
            last_incident_date = grouped_last_incidents[system]
            days_since_last = (quarter_end - last_incident_date).days
            
            results.append({
                "System": system,
                "Last_Incident_Date": last_incident_date.strftime('%d/%m/%Y'),
                "Days_Since_Last": days_since_last,
                "Status": "TARGET MET" if days_since_last >= 120 else "TARGET NOT MET"
            })
        else:
            results.append({
                "System": system,
                "Last_Incident_Date": "No incidents found",
                "Days_Since_Last": "N/A",
                "Status": "TARGET MET"
            })
    
    return sorted(results, key=lambda x: x['System'])

def process_kri10(system_month_counts):
    # Group Birbank systems
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    grouped_counts = {}
    
    for (system, month), count in system_month_counts.items():
        if system in birbank_systems:
            key = ("Birbank", month)
        else:
            key = (system, month)
        
        if key not in grouped_counts:
            grouped_counts[key] = 0
        grouped_counts[key] += count
    
    results = []
    critical_systems = set([key[0] for key in grouped_counts.keys()])
    
    for system in sorted(critical_systems):
        for month in ["April", "May", "June"]:
            count = grouped_counts.get((system, month), 0)
            if count > 0:
                results.append({
                    "System": system,
                    "Month": month,
                    "Count": count,
                    "Status": "EXCEEDED" if count > 2 else "WITHIN LIMIT"
                })
    
    return results

def process_kri12(rto_exceeded_incidents):
    # Group Birbank systems
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    grouped_incidents = []
    
    for incident in rto_exceeded_incidents:
        if incident["System"] in birbank_systems:
            incident["System"] = "Birbank"
        grouped_incidents.append(incident)
    
    return grouped_incidents

def process_kri13(system_within_rto_counts):
    # Group Birbank systems
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    grouped_counts = {}
    
    for system, count in system_within_rto_counts.items():
        if system in birbank_systems:
            if "Birbank" not in grouped_counts:
                grouped_counts["Birbank"] = 0
            grouped_counts["Birbank"] += count
        else:
            grouped_counts[system] = count
    
    results = []
    for system, count in sorted(grouped_counts.items()):
        if count > 0:
            results.append({
                "System": system,
                "Count": count,
                "Status": "EXCEEDED" if count > 2 else "WITHIN LIMIT"
            })
    
    return results

def process_kri19(system_durations):
    # Group Birbank systems
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    grouped_durations = {}
    
    for system, durations in system_durations.items():
        if system in birbank_systems:
            if "Birbank" not in grouped_durations:
                grouped_durations["Birbank"] = []
            grouped_durations["Birbank"].extend(durations)
        else:
            grouped_durations[system] = durations
    
    results = []
    for system, durations in sorted(grouped_durations.items()):
        if durations:
            total_duration = sum(durations)
            incident_count = len(durations)
            average_duration = total_duration / incident_count
            
            results.append({
                "System": system,
                "Incident_Count": incident_count,
                "Average_Minutes": int(average_duration),
                "Status": "EXCEEDED RTO" if average_duration > 120 else "WITHIN RTO"
            })
    
    return results

def generate_combined_html_report(risk_data, kri8_results, kri10_results, kri12_results, kri13_results, kri19_results):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Combined Risk and KRI Analysis Report</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            font-size: 16px; 
            padding: 20px; 
        }}
        .box {{ 
            border: 1px solid #ccc; 
            border-radius: 8px; 
            padding: 15px; 
            background-color: #f9f9f9; 
            width: 700px; 
            margin-bottom: 30px; 
        }}
        .box h2 {{ 
            color: #333; 
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin-bottom: 30px; 
            border: 2px solid #333;
        }}
        th, td {{ 
            border: 2px solid #333; 
            padding: 8px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #f2f2f2; 
            border: 2px solid #333;
            font-weight: bold;
        }}
        td {{
            border: 2px solid #333;
        }}
        .exceeded {{ 
            background-color: #ffcccc; 
        }}
        h1 {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 40px;
        }}
        h2 {{ 
            margin-top: 40px; 
        }}
        .total-count {{ 
            color: red; 
            font-weight: bold; 
            font-size: 18px; 
            margin-bottom: 10px; 
        }}
        .description {{ 
            color: #666; 
            margin-bottom: 15px; 
            font-style: italic; 
        }}
        .summary {{ 
            background-color: #f9f9f9; 
            padding: 10px; 
            margin-bottom: 20px; 
            border: 2px solid #333; 
        }}
        hr {{ 
            border: none; 
            border-top: 2px solid #ddd; 
            margin: 40px 0; 
        }}
        .section-divider {{
            border: none;
            border-top: 4px solid #333;
            margin: 60px 0;
        }}
    </style>
</head>
<body>
    <h1>Combined Risk and KRI Analysis Report - Q2 {risk_data['year']}</h1>
    
    <!-- RISK ANALYSIS SECTION -->
    <div class="box">
        <h2>Risk Hesabatı – 2-ci rüb ({risk_data['year']})</h2>
    </div>
    
    <div class="box">
        <p><strong>Cari rübdə gecikdirilmiş və ya icra vaxtında təqdim edilməmiş kritik İT risk sayı:</strong> {risk_data['filtered_critical_count']}</p>
        <p><strong>Ümumi kritik İT risk sayı:</strong> {risk_data['total_critical']}</p>
        <p><strong>Nisbət:</strong> {risk_data['percent_critical_filtered']}%</p>

        <br></br>
    
        <p><strong>Cari rübdə gecikdirilmiş və ya icra vaxtında təqdim edilməmiş Yüksək və Orta İT risk sayı:</strong> {risk_data['filtered_high_medium_count']}</p>
        <p><strong>Ümumi Yüksək və Orta İT risk sayı:</strong> {risk_data['total_high_medium']}</p>
        <p><strong>Nisbət:</strong> {risk_data['percent_high_medium_filtered']}%</p>
    
        <br></br>

        <p><strong>Cari rübdə sahibi və ya nəzarət tədbiri olmayan kritik İT risk sayı:</strong> {risk_data['delayed_critical_count']}</p>
        <p><strong>Ümumi kritik İT risk sayı:</strong> {risk_data['total_critical']}</p>
        <p><strong>Nisbət:</strong> {risk_data['percent_critical_missing']}%</p>

        <br></br>
   
        <p><strong>Cari rübdə sahibi və ya nəzarət tədbiri olmayan Yüksək və Orta İT risk sayı:</strong> {risk_data['delayed_hm_count']}</p>
        <p><strong>Ümumi Yüksək və Orta İT risk sayı:</strong> {risk_data['total_high_medium']}</p>
        <p><strong>Nisbət:</strong> {risk_data['percent_hm_missing']}%</p>
    </div>
    
    <hr class="section-divider">
    
    <!-- KRI ANALYSIS SECTION -->
    <h1>KRI Analysis Report</h1>
"""

    # KRI8 Section
    kri8_not_met = len([r for r in kri8_results if r['Status'] == 'TARGET NOT MET'])
    html_content += f"""
    <h2>KRI8 - Days Since Last Incident</h2>
    <div class="summary">
        <strong>KRI8 Definition:</strong> Days from last incident in critical system to end of quarter<br>
        <strong>Target:</strong> More than 120 days (systems should remain incident-free)<br>
        <strong>Quarter End:</strong> June 30, 2025
    </div>
    <p class="total-count">Systems not meeting 120+ days target: {kri8_not_met}</p>
    <table>
        <tr>
            <th>System</th>
            <th>Last Incident Date</th>
            <th>Days Since Last Incident</th>
            <th>Status</th>
        </tr>"""
    
    for result in kri8_results:
        row_class = ' class="exceeded"' if result['Status'] == 'TARGET NOT MET' else ''
        html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Last_Incident_Date']}</td>
            <td>{result['Days_Since_Last']}</td>
            <td>{result['Status']}</td>
        </tr>"""
    
    html_content += """
    </table>
    <hr>
    """
    
    html_content += f"""
    <h2>KRI10 - Monthly Incident Counts</h2>
    <div class="summary">
        <strong>KRI10 Definition:</strong> Number of incidents affecting critical systems per month<br>
        <strong>Threshold:</strong> Maximum 2 incidents per system per month<br>
        <strong>Period:</strong> Q2 2025 (April, May, June)
    </div>
    <table>
        <tr>
            <th>System</th>
            <th>Month</th>
            <th>Count of Incidents</th>
        </tr>"""
    
    for result in kri10_results:
        row_class = ' class="exceeded"' if result['Count'] > 2 else ''
        html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Month']}</td>
            <td>{result['Count']}</td>
        </tr>"""
    
    html_content += """
    </table>
    <hr>
    """
    
    # KRI12 Section
    total_rto_exceeded = len(kri12_results)
    html_content += f"""
    <h2>KRI12 - RTO Exceeded Incidents</h2>
    <div class="summary">
        <strong>KRI12 Definition:</strong> Incidents resolved longer than RTO (>2 hours)<br>
        <strong>RTO Threshold:</strong> 2 hours (120 minutes)<br>
        <strong>Target:</strong> 0 incidents exceeding RTO for each system<br>
        <strong>Note:</strong> Incidents with missing end dates are considered RTO exceeded
    </div>
    <p class="total-count">Total incidents exceeding RTO: {total_rto_exceeded}</p>
    <table>
        <tr>
            <th>System</th>
            <th>Incident</th>
            <th>RTO time which more than normal RTO (minutes)</th>
        </tr>"""
    
    for result in kri12_results:
        html_content += f"""
        <tr class="exceeded">
            <td>{result['System']}</td>
            <td>{result['Incident']}</td>
            <td>{result['RTO_Exceeded_Minutes']}</td>
        </tr>"""
    
    html_content += """
    </table>
    <hr>
    """
    
    # KRI13 Section
    html_content += f"""
    <h2>KRI13 - Within RTO Incident Counts</h2>
    <div class="summary">
        <strong>KRI13 Definition:</strong> Number of incidents resolved within RTO (≤2 hours)<br>
        <strong>RTO Threshold:</strong> 2 hours (120 minutes)<br>
        <strong>Threshold:</strong> Maximum 2 incidents per system 
    </div>
    <table>
        <tr>
            <th>System</th>
            <th>Incidents Within RTO</th>
            <th>Status</th>
        </tr>"""
    
    for result in kri13_results:
        row_class = ' class="exceeded"' if result['Count'] > 2 else ''
        html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Count']}</td>
            <td>{result['Status']}</td>
        </tr>"""
    
    html_content += """
    </table>
    <hr>
    """
    
    # KRI19 Section
    html_content += f"""
    <h2>KRI19 - Average Resolution Time</h2>
    <div class="summary">
        <strong>KRI19 Definition:</strong> Average incident resolution time per system<br>
        <strong>RTO Threshold:</strong> 2 hours (120 minutes)<br>
        <strong>Target:</strong> Average should be less than RTO for each system
    </div>
    <table>
        <tr>
            <th>System</th>
            <th>Total Incidents</th>
            <th>Average Duration (Minutes)</th>
            <th>Status</th>
        </tr>"""
    
    for result in kri19_results:
        row_class = ' class="exceeded"' if result['Average_Minutes'] > 120 else ''
        html_content += f"""
        <tr{row_class}>
            <td>{result['System']}</td>
            <td>{result['Incident_Count']}</td>
            <td>{result['Average_Minutes']}</td>
            <td>{result['Status']}</td>
        </tr>"""
    
    html_content += """
    </table>
</body>
</html>"""
    
    return html_content


def main():
    # File paths - original paths as requested
    risk_file_path = r"C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\RCM_QTLD report_Report (1).xls"
    kri_file_path = r"C:\Users\RzazadaTN\Desktop\Incident Report.xlsx"
    output_file = "Combined_Risk_KRI_Analysis_Report.html"
    
    print("Starting combined analysis...")
    
    # Analyze risk data
    print("Analyzing risk data...")
    risk_data = analyze_risk_data(risk_file_path)
    if risk_data is None:
        print("Failed to analyze risk data")
        return
    
    # Analyze KRI data
    print("Analyzing KRI data...")
    system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations, system_last_incidents = analyze_all_kris_from_excel(kri_file_path)
    
    # Process each KRI
    print("Processing KRI results...")
    kri8_results = process_kri8(system_last_incidents)
    kri10_results = process_kri10(system_month_counts)
    kri12_results = process_kri12(rto_exceeded_incidents)
    kri13_results = process_kri13(system_within_rto_counts)
    kri19_results = process_kri19(system_durations)
    
    # Generate combined HTML report
    print("Generating combined HTML report...")
    html_content = generate_combined_html_report(risk_data, kri8_results, kri10_results, kri12_results, kri13_results, kri19_results)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Combined analysis report successfully created: {output_file}")
    
    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    print("RISK ANALYSIS RESULTS:")
    print(f"- Critical IT risks delayed/not submitted on time: {risk_data['filtered_critical_count']} ({risk_data['percent_critical_filtered']}%)")
    print(f"- High/Medium IT risks delayed/not submitted on time: {risk_data['filtered_high_medium_count']} ({risk_data['percent_high_medium_filtered']}%)")
    print(f"- Critical IT risks without owner/control: {risk_data['delayed_critical_count']} ({risk_data['percent_critical_missing']}%)")
    print(f"- High/Medium IT risks without owner/control: {risk_data['delayed_hm_count']} ({risk_data['percent_hm_missing']}%)")
    
    print("\nKRI ANALYSIS RESULTS:")
    kri8_not_met = len([r for r in kri8_results if r['Status'] == 'TARGET NOT MET'])
    print(f"- KRI8: Systems not meeting 120+ days target: {kri8_not_met}")
    print(f"- KRI10: Monthly incident counts processed for {len(kri10_results)} system-month combinations")
    print(f"- KRI12: Total incidents exceeding RTO: {len(kri12_results)}")
    print(f"- KRI13: Systems with incidents within RTO: {len(kri13_results)}")
    print(f"- KRI19: Systems with average resolution time analysis: {len(kri19_results)}")

if __name__ == "__main__":
    main()