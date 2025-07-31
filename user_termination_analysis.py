#!/usr/bin/env python3

import pandas as pd
from datetime import datetime, timedelta
import os

class UserTerminationAnalyzer:
    def __init__(self, main_file_path, holidays_file_path):
        self.main_file_path = main_file_path
        self.holidays_file_path = holidays_file_path
        self.holidays = set()
        self.load_holidays()
    
    def load_holidays(self):
        try:
            holidays_df = pd.read_excel(self.holidays_file_path)
            if 'DATES' in holidays_df.columns:
                holiday_dates = pd.to_datetime(holidays_df['DATES'], format='%d/%m/%Y', errors='coerce')
                self.holidays = set(holiday_dates.dropna().dt.date)
        except:
            self.holidays = set()
    
    def is_weekend(self, date):
        return date.weekday() >= 5
    
    def is_holiday(self, date):
        return date in self.holidays
    
    def is_business_day(self, date):
        return not (self.is_weekend(date) or self.is_holiday(date))
    
    def get_next_business_day(self, date):
        next_day = date + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def analyze_user_lock_timing(self, termination_date, lock_date):
        if isinstance(termination_date, pd.Timestamp):
            termination_date = termination_date.date()
        if isinstance(lock_date, pd.Timestamp):
            lock_date = lock_date.date()
        
        if termination_date == lock_date:
            return {'status': 'COMPLIANT', 'reason': 'Same day lock', 'action_required': False}
        
        days_difference = (lock_date - termination_date).days
        
        if days_difference <= 1:
            return {'status': 'COMPLIANT', 'reason': 'Within 1 day', 'action_required': False}
        
        if (self.is_weekend(termination_date) or self.is_holiday(termination_date) or 
            not self.is_business_day(termination_date + timedelta(days=1))):
            first_business_day = self.get_next_business_day(termination_date)
            days_after_first_business_day = (lock_date - first_business_day).days
            
            if days_after_first_business_day <= 1:
                return {'status': 'COMPLIANT', 'reason': 'Within acceptable range', 'action_required': False}
            else:
                return {'status': 'NON_COMPLIANT', 'reason': f'Too late after weekend/holiday', 'action_required': True}
        else:
            return {'status': 'NON_COMPLIANT', 'reason': f'{days_difference} days late', 'action_required': True}
    
    def load_and_analyze_data(self):
        df = pd.read_excel(self.main_file_path)
        
        target_statuses = ['EXPIRED', 'EXPIRED AND LOCKED', 'EXPIRED (GRACE) AND LOCKED', 'LOCKED']
        
        status_column = None
        for col in df.columns:
            if 'status' in col.lower() or 'state' in col.lower():
                status_column = col
                break
        
        if status_column:
            filtered_df = df[df[status_column].isin(target_statuses)].copy()
        else:
            filtered_df = df.copy()
        
        date_columns = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'termination' in col_lower or 'term' in col_lower:
                date_columns['termination'] = col
            elif 'lock' in col_lower:
                date_columns['lock'] = col
        
        if 'termination' not in date_columns or 'lock' not in date_columns:
            return None
        
        for date_type, col_name in date_columns.items():
            if col_name in filtered_df.columns:
                filtered_df[col_name] = pd.to_datetime(filtered_df[col_name], errors='coerce')
        
        results = []
        for index, row in filtered_df.iterrows():
            if pd.notna(row[date_columns['termination']]) and pd.notna(row[date_columns['lock']]):
                analysis = self.analyze_user_lock_timing(
                    row[date_columns['termination']], 
                    row[date_columns['lock']]
                )
                
                result_row = row.to_dict()
                result_row.update({
                    'ANALYSIS_STATUS': analysis['status'],
                    'ANALYSIS_REASON': analysis['reason'],
                    'ACTION_REQUIRED': analysis['action_required']
                })
                results.append(result_row)
        
        return pd.DataFrame(results)
    
    def generate_report(self, results_df, output_file):
        if results_df is None or results_df.empty:
            return
        
        total_records = len(results_df)
        compliant_records = len(results_df[results_df['ANALYSIS_STATUS'] == 'COMPLIANT'])
        non_compliant_records = len(results_df[results_df['ANALYSIS_STATUS'] == 'NON_COMPLIANT'])
        action_required_records = len(results_df[results_df['ACTION_REQUIRED'] == True])
        
        print(f"Total: {total_records}, Compliant: {compliant_records}, Non-compliant: {non_compliant_records}, Action required: {action_required_records}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='Analysis Results', index=False)
            
            summary_data = {
                'Metric': ['Total Records', 'Compliant', 'Non-Compliant', 'Action Required'],
                'Count': [total_records, compliant_records, non_compliant_records, action_required_records]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            if non_compliant_records > 0:
                non_compliant_df = results_df[results_df['ANALYSIS_STATUS'] == 'NON_COMPLIANT']
                non_compliant_df.to_excel(writer, sheet_name='Non-Compliant Records', index=False)

def main():
    main_file_path = input("CMS file path: ").strip()
    holidays_file_path = input("Holidays file path: ").strip()
    
    if not os.path.exists(main_file_path) or not os.path.exists(holidays_file_path):
        print("File not found")
        return
    
    analyzer = UserTerminationAnalyzer(main_file_path, holidays_file_path)
    results = analyzer.load_and_analyze_data()
    
    if results is not None:
        output_file = input("Output file (default: report.xlsx): ").strip() or "report.xlsx"
        analyzer.generate_report(results, output_file)
        print(f"Report saved: {output_file}")
    else:
        print("Analysis failed")

if __name__ == "__main__":
    main()