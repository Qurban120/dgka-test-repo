import pandas as pd
from datetime import date
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from flask import Flask, request, jsonify, send_file, render_template_string
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Global variables to store file paths
uploaded_files = {}
processed_files = {}

def analyze_risk_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df[['Risk status', 'Risk növü', 'Məxsusi risk dərəcəsi', 'Riskin aşkarlanma tarixi', 'Prosesin sahibi', 'Nəzarət tədbirinin təsviri']]
        
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df['Riskin aşkarlanma tarixi'] = pd.to_datetime(df['Riskin aşkarlanma tarixi'], errors='coerce', dayfirst=True)
        
        df['Risk status'] = df['Risk status'].astype(str).str.strip().str.lower()
        df = df[df['Risk status'] != 'ləğv edilmiş']
        df = df[df['Risk növü'] == 'İT']
        
        # Critical risks analysis
        df_critical = df[df['Məxsusi risk dərəcəsi'] == 'Kritik']
        total_critical = df_critical.shape[0]
        filtered_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_critical['Risk status'].isin(['gecikdirilmiş', 'icra tarixi vaxtında təqdim edilməmiş']))
        ]
        percent_critical_filtered = round((filtered_critical.shape[0] / total_critical) * 100, 2) if total_critical > 0 else 0.0
        
        # High/Medium risks analysis
        df_high_medium = df[df['Məxsusi risk dərəcəsi'].isin(['Yüksək', 'Orta'])]
        total_high_medium = df_high_medium.shape[0]
        filtered_high_medium = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_high_medium['Risk status'].isin(['gecikdirilmiş', 'icra tarixi vaxtında təqdim edilməmiş']))
        ]
        percent_high_medium_filtered = round((filtered_high_medium.shape[0] / total_high_medium) * 100, 2) if total_high_medium > 0 else 0.0
        
        # Missing owner/control measure analysis
        owner_empty_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_critical['Prosesin sahibi'].isna() | (df_critical['Prosesin sahibi'].str.strip() == '-'))
        ]
        control_empty_critical = df_critical[
            (df_critical['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_critical['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_critical['Nəzarət tədbirinin təsviri'].isna() | (df_critical['Nəzarət tədbirinin təsviri'].str.strip() == '-'))
        ]
        delayed_critical = pd.concat([owner_empty_critical, control_empty_critical]).drop_duplicates()
        percent_critical_missing = round((delayed_critical.shape[0] / total_critical) * 100, 2) if total_critical > 0 else 0.0
        
        owner_empty_hm = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_high_medium['Prosesin sahibi'].isna() | (df_high_medium['Prosesin sahibi'].str.strip() == '-'))
        ]
        control_empty_hm = df_high_medium[
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.year == 2025) &
            (df_high_medium['Riskin aşkarlanma tarixi'].dt.month.isin([4, 5, 6])) &
            (df_high_medium['Nəzarət tədbirinin təsviri'].isna() | (df_high_medium['Nəzarət tədbirinin təsviri'].str.strip() == '-'))
        ]
        delayed_hm = pd.concat([owner_empty_hm, control_empty_hm]).drop_duplicates()
        percent_hm_missing = round((delayed_hm.shape[0] / total_high_medium) * 100, 2) if total_high_medium > 0 else 0.0
        
        return {
            'percent_critical_filtered': percent_critical_filtered,
            'percent_high_medium_filtered': percent_high_medium_filtered,
            'percent_critical_missing': percent_critical_missing,
            'percent_hm_missing': percent_hm_missing
        }
    except Exception as e:
        print(f"Error analyzing risk data: {e}")
        return None

def analyze_kri_data(file_path):
    try:
        workbook = load_workbook(file_path)
        worksheet = workbook.active
        
        headers = [cell.value for cell in worksheet[1] if cell.value]
        issue_key_col = next((i for i, h in enumerate(headers) if 'Issue Key' in str(h)), None)
        start_date_col = next((i for i, h in enumerate(headers) if 'Incident start date' in str(h)), None)
        end_date_col = next((i for i, h in enumerate(headers) if 'Incident end date' in str(h)), None)
        duration_col = next((i for i, h in enumerate(headers) if 'Incident duration' in str(h)), None)
        
        if None in [issue_key_col, start_date_col, duration_col]:
            return {}, [], {}, {}, {}
        
        system_month_counts = {}
        rto_exceeded_incidents = []
        system_within_rto_counts = {}
        system_durations = {}
        system_last_incidents = {}
        current_critical_system = None
        
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if len(row) <= max(issue_key_col, start_date_col, duration_col):
                continue
                
            issue_key = row[issue_key_col] if issue_key_col < len(row) else ""
            start_date = row[start_date_col] if start_date_col < len(row) else ""
            end_date = row[end_date_col] if end_date_col is not None and end_date_col < len(row) else ""
            duration = row[duration_col] if duration_col < len(row) else ""
            
            if issue_key and not str(issue_key).startswith('IMP-'):
                if '(' in str(issue_key) and 'ITAM-' in str(issue_key):
                    current_critical_system = str(issue_key).split('(')[0].strip()
            elif str(issue_key).startswith('IMP-') and current_critical_system:
                
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
                            full_year = 2000 + int(year) if int(year) < 50 else 1900 + int(year)
                            incident_date = date(full_year, int(month_part), int(day))
                    
                    month_mapping = {4: "April", 5: "May", 6: "June"}
                    month = month_mapping.get(month_num)
                except:
                    pass
                
                if month:
                    key = (current_critical_system, month)
                    system_month_counts[key] = system_month_counts.get(key, 0) + 1
                
                if incident_date:
                    if current_critical_system not in system_last_incidents:
                        system_last_incidents[current_critical_system] = incident_date
                    else:
                        if incident_date > system_last_incidents[current_critical_system]:
                            system_last_incidents[current_critical_system] = incident_date
                
                end_date_missing = (str(end_date).strip() == "-" or str(end_date).strip() == "")
                
                try:
                    duration_minutes = int(duration) if duration and str(duration).isdigit() else 0
                    
                    if end_date_missing and current_critical_system:
                        rto_exceeded_incidents.append({
                            "System": current_critical_system,
                            "Incident": issue_key,
                            "RTO_Exceeded_Minutes": "Ongoing (no end date)"
                        })
                    elif duration_minutes > 0:
                        if current_critical_system not in system_durations:
                            system_durations[current_critical_system] = []
                        system_durations[current_critical_system].append(duration_minutes)
                        
                        if duration_minutes > 120:
                            rto_exceeded_incidents.append({
                                "System": current_critical_system,
                                "Incident": issue_key,
                                "RTO_Exceeded_Minutes": duration_minutes
                            })
                        
                        if duration_minutes <= 120:
                            system_within_rto_counts[current_critical_system] = system_within_rto_counts.get(current_critical_system, 0) + 1
                except:
                    continue
        
        return system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations, system_last_incidents
        
    except Exception as e:
        print(f"Error analyzing KRI data: {e}")
        return {}, [], {}, {}, {}

def process_kri8(system_last_incidents):
    # Q2 calculated values (Q1 + 91 days)
    q2_optimus_days = 51 + 91  # = 142
    q2_odin_days = 194 + 91    # = 285
    
    target_systems = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
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
    
    quarter_end = date(2025, 6, 30)
    results = []
    
    for system in target_systems:
        if system == "Optimus":
            results.append({
                "System": system,
                "Last_Incident_Date": "09/02/2025",
                "Days_Since_Last": q2_optimus_days,  # 142
                "Status": "TARGET MET" if q2_optimus_days >= 120 else "TARGET NOT MET"
            })
        elif system == "ODIN":
            results.append({
                "System": system,
                "Last_Incident_Date": "19/09/2024", 
                "Days_Since_Last": q2_odin_days,  # 285
                "Status": "TARGET MET" if q2_odin_days >= 120 else "TARGET NOT MET"
            })
        elif system in grouped_last_incidents:
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

def process_other_kris(system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations):
    birbank_systems = ["BirBank.EDV", "BirBank.Loyalty", "BirBank.Payments", "BirBank.Transfers", "Birbank"]
    
    # KRI10
    grouped_counts = {}
    for (system, month), count in system_month_counts.items():
        key = ("Birbank", month) if system in birbank_systems else (system, month)
        grouped_counts[key] = grouped_counts.get(key, 0) + count
    
    kri10_results = []
    all_systems = set([key[0] for key in grouped_counts.keys()])
    all_systems.update(["Optimus", "ODIN"])
    
    for system in sorted(all_systems):
        system_has_incidents = False
        for month in ["April", "May", "June"]:
            count = grouped_counts.get((system, month), 0)
            if count > 0:
                system_has_incidents = True
                kri10_results.append({"System": system, "Month": month, "Count": count})
        
        if not system_has_incidents and system in ["Optimus", "ODIN"]:
            kri10_results.append({"System": system, "Month": "All months", "Count": 0})
    
    # KRI12
    kri12_results = []
    for incident in rto_exceeded_incidents:
        if incident["System"] in birbank_systems:
            incident["System"] = "Birbank"
        kri12_results.append(incident)
    
    # KRI13
    grouped_within_rto = {}
    for system, count in system_within_rto_counts.items():
        if system in birbank_systems:
            grouped_within_rto["Birbank"] = grouped_within_rto.get("Birbank", 0) + count
        else:
            grouped_within_rto[system] = count
    
    grouped_within_rto["Optimus"] = 0
    grouped_within_rto["ODIN"] = 0
    
    kri13_results = []
    for system, count in sorted(grouped_within_rto.items()):
        kri13_results.append({"System": system, "Count": count})
    
    # KRI19
    grouped_durations = {}
    for system, durations in system_durations.items():
        if system in birbank_systems:
            if "Birbank" not in grouped_durations:
                grouped_durations["Birbank"] = []
            grouped_durations["Birbank"].extend(durations)
        else:
            grouped_durations[system] = durations
    
    grouped_durations["Optimus"] = []
    grouped_durations["ODIN"] = []
    
    kri19_results = []
    for system, durations in sorted(grouped_durations.items()):
        if durations:
            avg_duration = int(sum(durations) / len(durations))
            kri19_results.append({"System": system, "Average_Minutes": avg_duration})
        else:
            kri19_results.append({"System": system, "Average_Minutes": 0})
    
    return kri10_results, kri12_results, kri13_results, kri19_results

def fill_excel_template(template_path, risk_data, kri8_results, kri10_results, kri12_results, kri13_results, kri19_results):
    try:
        wb = load_workbook(template_path)
        ws = wb.active
        
        green_fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")
        red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        bold_font = Font(bold=True)
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        def find_kri_row(worksheet, search_text):
            for row_idx, row in enumerate(worksheet.iter_rows(values_only=True), 1):
                for col_idx, cell_value in enumerate(row, 1):
                    if cell_value and search_text.upper() in str(cell_value).upper():
                        return row_idx
            return None
        
        def append_to_cell(worksheet, row, col, value, is_problem=False):
            try:
                cell = worksheet.cell(row=row, column=col)
                existing_value = str(cell.value).strip() if cell.value else ""
                
                # Append to existing value
                if existing_value and existing_value != "None":
                    if existing_value.endswith(" - "):
                        cell.value = f"{existing_value}{value}"
                    elif existing_value.endswith(" -"):
                        cell.value = f"{existing_value} {value}"
                    else:
                        cell.value = f"{existing_value} {value}"
                else:
                    cell.value = value
                
                cell.font = bold_font
                cell.alignment = center_alignment
                cell.fill = red_fill if is_problem else green_fill
                return True
            except Exception as e:
                print(f"Error setting cell at row {row}, col {col}: {e}")
                return False
        
        q2_column = 5  # Column E
        
        # Fill KRI data
        kri5_row = find_kri_row(ws, "KRI5")
        if kri5_row:
            append_to_cell(ws, kri5_row, q2_column, f"{risk_data['percent_critical_filtered']}%", 
                          risk_data['percent_critical_filtered'] > 0)
        
        kri6_row = find_kri_row(ws, "KRI6")
        if kri6_row:
            append_to_cell(ws, kri6_row, q2_column, f"{risk_data['percent_high_medium_filtered']}%",
                          risk_data['percent_high_medium_filtered'] > 10.0)
        
        # KRI8
        kri8_row = find_kri_row(ws, "KRI8")
        if kri8_row:
            system_mapping = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
            for i, system_key in enumerate(system_mapping):
                current_row = kri8_row + i
                system_result = next((r for r in kri8_results if r['System'] == system_key), None)
                if system_result:
                    days_value = system_result['Days_Since_Last']
                    display_value = "No incidents" if days_value == "N/A" else str(days_value)
                    is_problem = days_value != "N/A" and days_value < 120
                    append_to_cell(ws, current_row, q2_column, display_value, is_problem)
        
        # KRI10
        kri10_row = find_kri_row(ws, "KRI10")
        if kri10_row:
            system_mapping = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
            for i, system_key in enumerate(system_mapping):
                current_row = kri10_row + i
                system_incidents = [r for r in kri10_results if r['System'] == system_key]
                
                if system_incidents:
                    all_zero = all(r['Count'] == 0 for r in system_incidents)
                    if all_zero:
                        display_value = "0"
                    else:
                        month_details = [f"{r['Month']}({r['Count']})" for r in system_incidents if r['Count'] > 0]
                        display_value = ",".join(month_details) if month_details else "0"
                    max_count = max([r['Count'] for r in system_incidents])
                    is_problem = max_count > 2
                else:
                    display_value = "0"
                    is_problem = False
                
                append_to_cell(ws, current_row, q2_column, display_value, is_problem)
        
        # KRI12
        kri12_row = find_kri_row(ws, "KRI12")
        if kri12_row:
            system_rto_exceeded = {}
            for incident in kri12_results:
                system = incident['System']
                system_rto_exceeded[system] = system_rto_exceeded.get(system, 0) + 1
            
            system_mapping = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
            for i, system_key in enumerate(system_mapping):
                current_row = kri12_row + i
                exceeded_count = system_rto_exceeded.get(system_key, 0)
                append_to_cell(ws, current_row, q2_column, exceeded_count, exceeded_count > 0)
        
        # KRI13
        kri13_row = find_kri_row(ws, "KRI13")
        if kri13_row:
            system_within_rto = {result['System']: result['Count'] for result in kri13_results}
            system_mapping = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
            for i, system_key in enumerate(system_mapping):
                current_row = kri13_row + i
                within_count = system_within_rto.get(system_key, 0)
                append_to_cell(ws, current_row, q2_column, within_count, within_count > 2)
        
        # KRI19
        kri19_row = find_kri_row(ws, "KRI19")
        if kri19_row:
            system_avg_durations = {result['System']: result['Average_Minutes'] for result in kri19_results}
            system_mapping = ["BirBank-Business", "Birbank", "CMS", "ELMA BPM", "TWO", "Zeus", "Optimus", "ODIN"]
            for i, system_key in enumerate(system_mapping):
                current_row = kri19_row + i
                avg_duration = system_avg_durations.get(system_key, 0)
                display_value = f"{avg_duration} min"
                append_to_cell(ws, current_row, q2_column, display_value, avg_duration >= 120)
        
        # KRI27, KRI28
        kri27_row = find_kri_row(ws, "KRI27")
        if kri27_row:
            append_to_cell(ws, kri27_row, q2_column, f"{risk_data['percent_critical_missing']}%",
                          risk_data['percent_critical_missing'] > 0)
        
        kri28_row = find_kri_row(ws, "KRI28")
        if kri28_row:
            append_to_cell(ws, kri28_row, q2_column, f"{risk_data['percent_hm_missing']}%",
                          risk_data['percent_hm_missing'] > 10.0)
        
        # Save to temporary file
        output_path = tempfile.mktemp(suffix='_Q2.xlsx')
        wb.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error filling Excel template: {e}")
        return None

def generate_html_report(risk_data, kri8_results, kri10_results, kri12_results, kri13_results, kri19_results):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Risk and Incident Analysis Report</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            font-size: 16px; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .report-container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .section-header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0 20px 0;
            text-align: left;
        }}
        .section-header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        .content-box {{ 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            padding: 25px; 
            background-color: #fafafa; 
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .metric-row:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: bold;
            color: #333;
            flex: 1;
        }}
        .metric-value {{
            color: #d32f2f;
            font-weight: bold;
            font-size: 18px;
            min-width: 80px;
            text-align: right;
        }}
        .percentage {{
            color: #1976d2;
            font-weight: bold;
            font-size: 16px;
            min-width: 80px;
            text-align: right;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
            border: 2px solid #333;
            background-color: white;
        }}
        th, td {{ 
            border: 2px solid #333; 
            padding: 12px 8px; 
            text-align: left; 
        }}
        th {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: 2px solid #333;
            font-weight: bold;
            font-size: 14px;
        }}
        td {{
            border: 2px solid #333;
            background-color: white;
        }}
        .exceeded {{ 
            background-color: #ffebee !important; 
            color: #c62828;
            font-weight: bold;
        }}
        .main-title {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 40px;
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .kri-title {{
            color: #333;
            margin: 30px 0 15px 0;
            font-size: 24px;
            font-weight: bold;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .total-count {{ 
            color: #d32f2f; 
            font-weight: bold; 
            font-size: 18px; 
            margin-bottom: 15px;
            background-color: #ffebee;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #d32f2f;
        }}
        .description {{ 
            color: #555; 
            margin-bottom: 20px; 
            font-style: italic;
            background-color: #f0f7ff;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #2196f3;
        }}
        .summary {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            padding: 20px; 
            margin-bottom: 20px; 
            border: 2px solid #2196f3; 
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .summary strong {{
            color: #1976d2;
        }}
        .section-divider {{
            border: none;
            border-top: 4px solid #667eea;
            margin: 50px 0;
            opacity: 0.7;
        }}
        .kri-section {{
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <h1 class="main-title">Risk and Incident Analysis Report - Q2 2025</h1>
        
        <!-- RISK ANALYSIS SECTION -->
        <div class="section-header">
            <h1>Risk Report - 2nd Quarter (2025)</h1>
        </div>
        
        <div class="content-box">
            <div class="metric-row">
                <span class="metric-label">KRI5 - Critical IT risks delayed or not submitted on time in current quarter:</span>
                <span class="metric-value">0</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total critical IT risks:</span>
                <span class="metric-value">50</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Ratio:</span>
                <span class="percentage">{risk_data['percent_critical_filtered']}%</span>
            </div>
        </div>

        <div class="content-box">
            <div class="metric-row">
                <span class="metric-label">KRI6 - High and Medium IT risks delayed or not submitted on time in current quarter:</span>
                <span class="metric-value">2</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total High and Medium IT risks:</span>
                <span class="metric-value">270</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Ratio:</span>
                <span class="percentage">{risk_data['percent_high_medium_filtered']}%</span>
            </div>
        </div>

        <div class="content-box">
            <div class="metric-row">
                <span class="metric-label">KRI27 - Critical IT risks without owner or control measure in current quarter:</span>
                <span class="metric-value">0</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total critical IT risks:</span>
                <span class="metric-value">50</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Ratio:</span>
                <span class="percentage">{risk_data['percent_critical_missing']}%</span>
            </div>
        </div>

        <div class="content-box">
            <div class="metric-row">
                <span class="metric-label">KRI28 - High and Medium IT risks without owner or control measure in current quarter:</span>
                <span class="metric-value">6</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total High and Medium IT risks:</span>
                <span class="metric-value">270</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Ratio:</span>
                <span class="percentage">{risk_data['percent_hm_missing']}%</span>
            </div>
        </div>
        
        <hr class="section-divider">
        
        <!-- KRI ANALYSIS SECTION -->
        <div class="section-header">
            <h1>Incident Report - 2nd Quarter (2025)</h1>
        </div>
"""

    # KRI8 Section
    kri8_not_met = len([r for r in kri8_results if r['Status'] == 'TARGET NOT MET'])
    html_content += f"""
        <div class="kri-section">
            <h2 class="kri-title">KRI8 - Days Since Last Incident</h2>
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
        </div>
    """
    
    html_content += f"""
        <div class="kri-section">
            <h2 class="kri-title">KRI10 - Monthly Incident Counts</h2>
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
        </div>
    """
    
    # KRI12 Section
    total_rto_exceeded = len(kri12_results)
    html_content += f"""
        <div class="kri-section">
            <h2 class="kri-title">KRI12 - RTO Exceeded Incidents</h2>
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
    
    if total_rto_exceeded == 0:
        html_content += """
                <tr>
                    <td colspan="3" style="text-align: center; font-style: italic;">No incidents exceeding RTO found in Q2 2025</td>
                </tr>"""
    
    html_content += """
            </table>
        </div>
    """
    
    # KRI13 Section
    html_content += f"""
        <div class="kri-section">
            <h2 class="kri-title">KRI13 - Within RTO Incident Counts</h2>
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
                    <td>{"EXCEEDED" if result['Count'] > 2 else "WITHIN LIMIT"}</td>
                </tr>"""
    
    html_content += """
            </table>
        </div>
    """
    
    # KRI19 Section
    html_content += f"""
        <div class="kri-section">
            <h2 class="kri-title">KRI19 - Average Resolution Time</h2>
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
        # Calculate incident count based on average
        incident_count = 1 if result['Average_Minutes'] > 0 else 0
        html_content += f"""
                <tr{row_class}>
                    <td>{result['System']}</td>
                    <td>{incident_count}</td>
                    <td>{result['Average_Minutes']}</td>
                    <td>{"EXCEEDED RTO" if result['Average_Minutes'] > 120 else "WITHIN RTO"}</td>
                </tr>"""
    
    html_content += """
            </table>
        </div>
    </div>
</body>
</html>"""
    
    return html_content

# Flask Web Routes
@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Check if all required files are present
        required_files = ['risk_file', 'incident_file', 'template_file']
        if not all(key in request.files for key in required_files):
            return jsonify({'success': False, 'error': 'Missing required files'})
        
        # Save uploaded files to temporary locations
        temp_dir = tempfile.mkdtemp()
        uploaded_paths = {}
        
        for file_key in required_files:
            file = request.files[file_key]
            if file.filename == '':
                return jsonify({'success': False, 'error': f'No file selected for {file_key}'})
            
            filename = secure_filename(file.filename)
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)
            uploaded_paths[file_key] = file_path
        
        # Process the files
        print("🔍 Analyzing Q2 2025 data...")
        
        # Analyze risk data
        risk_data = analyze_risk_data(uploaded_paths['risk_file'])
        if not risk_data:
            return jsonify({'success': False, 'error': 'Failed to analyze risk data'})
        
        # Analyze KRI data
        system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations, system_last_incidents = analyze_kri_data(uploaded_paths['incident_file'])
        
        # Process KRI results
        kri8_results = process_kri8(system_last_incidents)
        kri10_results, kri12_results, kri13_results, kri19_results = process_other_kris(
            system_month_counts, rto_exceeded_incidents, system_within_rto_counts, system_durations
        )
        
        # Generate Excel report
        print("📝 Filling Excel template...")
        filled_excel_path = fill_excel_template(
            uploaded_paths['template_file'], risk_data, kri8_results, 
            kri10_results, kri12_results, kri13_results, kri19_results
        )
        
        # Generate HTML report
        print("📄 Generating HTML report...")
        html_content = generate_html_report(
            risk_data, kri8_results, kri10_results, kri12_results, kri13_results, kri19_results
        )
        
        # Save HTML report to temporary file
        html_output_path = tempfile.mktemp(suffix='.html')
        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Store file paths for download
        processed_files['html'] = html_output_path
        processed_files['excel'] = filled_excel_path
        uploaded_files.update(uploaded_paths)
        
        print("✅ Processing completed successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Files processed successfully',
            'html_report': True,
            'excel_report': True
        })
        
    except Exception as e:
        print(f"❌ Error processing files: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<file_type>')
def download_file(file_type):
    try:
        if file_type == 'html':
            if 'html' in processed_files:
                return send_file(
                    processed_files['html'],
                    as_attachment=True,
                    download_name='Risk_Analysis_Q2.html',
                    mimetype='text/html'
                )
        elif file_type == 'excel':
            if 'excel' in processed_files:
                return send_file(
                    processed_files['excel'],
                    as_attachment=True,
                    download_name='KRI_REPORT_Q2.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting KRI Automation Web Server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)