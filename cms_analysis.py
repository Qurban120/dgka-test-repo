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
        try:
            df = pd.read_excel(self.main_file_path)
            
            # Find the exact column names
            termination_col = 'Termination Date'
            lock_col = 'User Lock Date'
            
            # Check if columns exist
            if termination_col not in df.columns or lock_col not in df.columns:
                print(f"Available columns: {list(df.columns)}")
                return None
            
            # Convert date columns
            df[termination_col] = pd.to_datetime(df[termination_col], errors='coerce')
            df[lock_col] = pd.to_datetime(df[lock_col], errors='coerce')
            
            results = []
            analyzed_count = 0
            
            for index, row in df.iterrows():
                # Only analyze rows that have both termination and lock dates
                if pd.notna(row[termination_col]) and pd.notna(row[lock_col]):
                    analysis = self.analyze_user_lock_timing(
                        row[termination_col], 
                        row[lock_col]
                    )
                    
                    result_row = row.to_dict()
                    result_row.update({
                        'ANALYSIS_STATUS': analysis['status'],
                        'ANALYSIS_REASON': analysis['reason'],
                        'ACTION_REQUIRED': analysis['action_required']
                    })
                    results.append(result_row)
                    analyzed_count += 1
            
            print(f"Analyzed {analyzed_count} records with both dates")
            return pd.DataFrame(results)
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
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