#!/usr/bin/env python3
"""
User Termination and Lock Date Analysis Script

This script analyzes user termination and lock dates to ensure compliance with
security procedures. It checks if users are locked timely after termination,
considering weekends and holidays.

Business Rules:
1. If lock date = termination date: Process working effectively
2. If lock date differs from termination date:
   - Check if lock date exceeds 1 day from termination
   - Consider weekends and holidays
   - Check if lock date exceeds 1 day after first work day
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys


class UserTerminationAnalyzer:
    def __init__(self, main_file_path, holidays_file_path):
        """
        Initialize the analyzer with file paths
        
        Args:
            main_file_path (str): Path to the main Excel file with user data
            holidays_file_path (str): Path to the holidays Excel file
        """
        self.main_file_path = main_file_path
        self.holidays_file_path = holidays_file_path
        self.holidays = set()
        self.load_holidays()
    
    def load_holidays(self):
        """Load holidays from the holidays Excel file"""
        try:
            holidays_df = pd.read_excel(self.holidays_file_path)
            if 'DATES' in holidays_df.columns:
                # Convert dates to datetime and store in set for fast lookup
                holiday_dates = pd.to_datetime(holidays_df['DATES'], format='%d/%m/%Y', errors='coerce')
                self.holidays = set(holiday_dates.dropna().dt.date)
                print(f"Loaded {len(self.holidays)} holidays from {self.holidays_file_path}")
            else:
                print("Warning: 'DATES' column not found in holidays file")
        except Exception as e:
            print(f"Error loading holidays file: {e}")
            self.holidays = set()
    
    def is_weekend(self, date):
        """Check if a date is weekend (Saturday=5, Sunday=6)"""
        return date.weekday() >= 5
    
    def is_holiday(self, date):
        """Check if a date is a holiday"""
        return date in self.holidays
    
    def is_business_day(self, date):
        """Check if a date is a business day (not weekend or holiday)"""
        return not (self.is_weekend(date) or self.is_holiday(date))
    
    def get_next_business_day(self, date):
        """Get the next business day after the given date"""
        next_day = date + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def analyze_user_lock_timing(self, termination_date, lock_date):
        """
        Analyze if user was locked timely according to business rules
        
        Args:
            termination_date (datetime.date): User termination date
            lock_date (datetime.date): User lock date
            
        Returns:
            dict: Analysis result with status and details
        """
        result = {
            'status': 'COMPLIANT',
            'reason': '',
            'action_required': False,
            'details': {}
        }
        
        # Convert to date objects if they're datetime
        if isinstance(termination_date, pd.Timestamp):
            termination_date = termination_date.date()
        if isinstance(lock_date, pd.Timestamp):
            lock_date = lock_date.date()
        
        result['details'] = {
            'termination_date': termination_date,
            'lock_date': lock_date,
            'termination_is_weekend': self.is_weekend(termination_date),
            'termination_is_holiday': self.is_holiday(termination_date),
            'lock_is_weekend': self.is_weekend(lock_date),
            'lock_is_holiday': self.is_holiday(lock_date)
        }
        
        # Rule 1: If dates are the same, process is working effectively
        if termination_date == lock_date:
            result['reason'] = 'Lock date matches termination date'
            return result
        
        # Rule 2: If dates differ, check compliance
        days_difference = (lock_date - termination_date).days
        result['details']['days_difference'] = days_difference
        
        # Check if lock date exceeds one day from termination
        if days_difference <= 1:
            result['reason'] = 'Lock date within 1 day of termination'
            return result
        
        # Check if termination was before weekend or holiday
        termination_is_before_non_business = (
            self.is_weekend(termination_date) or 
            self.is_holiday(termination_date) or
            not self.is_business_day(termination_date + timedelta(days=1))
        )
        
        if termination_is_before_non_business:
            # Find the first business day after termination
            first_business_day = self.get_next_business_day(termination_date)
            result['details']['first_business_day_after_termination'] = first_business_day
            
            # Check if lock date exceeds one day after first business day
            days_after_first_business_day = (lock_date - first_business_day).days
            result['details']['days_after_first_business_day'] = days_after_first_business_day
            
            if days_after_first_business_day <= 1:
                result['reason'] = f'Lock date within acceptable range (termination before weekend/holiday, locked by {lock_date})'
                return result
            else:
                result['status'] = 'NON_COMPLIANT'
                result['action_required'] = True
                result['reason'] = f'Lock date exceeds 1 day after first business day ({first_business_day})'
                return result
        else:
            # Termination was on a business day, but lock was too late
            result['status'] = 'NON_COMPLIANT'
            result['action_required'] = True
            result['reason'] = f'Lock date is {days_difference} days after termination (exceeds 1 day limit)'
            return result
    
    def load_and_analyze_data(self):
        """Load the main data file and perform analysis"""
        try:
            # Load the main Excel file
            df = pd.read_excel(self.main_file_path)
            print(f"Loaded {len(df)} records from {self.main_file_path}")
            print(f"Columns available: {list(df.columns)}")
            
            # Filter for users with specific statuses (as mentioned in requirements)
            target_statuses = ['EXPIRED', 'EXPIRED AND LOCKED', 'EXPIRED (GRACE) AND LOCKED', 'LOCKED']
            
            # Try to identify the status column (flexible matching)
            status_column = None
            for col in df.columns:
                if 'status' in col.lower() or 'state' in col.lower():
                    status_column = col
                    break
            
            if status_column:
                print(f"Using status column: {status_column}")
                # Filter data for target statuses
                filtered_df = df[df[status_column].isin(target_statuses)].copy()
                print(f"Filtered to {len(filtered_df)} records with target statuses")
            else:
                print("Warning: Could not identify status column, processing all records")
                filtered_df = df.copy()
            
            # Try to identify date columns
            date_columns = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'termination' in col_lower or 'term' in col_lower:
                    date_columns['termination'] = col
                elif 'lock' in col_lower:
                    date_columns['lock'] = col
                elif 'logon' in col_lower or 'login' in col_lower:
                    date_columns['last_logon'] = col
            
            print(f"Identified date columns: {date_columns}")
            
            if 'termination' not in date_columns or 'lock' not in date_columns:
                print("Error: Could not identify required termination and lock date columns")
                return None
            
            # Convert date columns to datetime
            for date_type, col_name in date_columns.items():
                if col_name in filtered_df.columns:
                    filtered_df[col_name] = pd.to_datetime(filtered_df[col_name], errors='coerce')
            
            # Perform analysis
            results = []
            for index, row in filtered_df.iterrows():
                if pd.notna(row[date_columns['termination']]) and pd.notna(row[date_columns['lock']]):
                    analysis = self.analyze_user_lock_timing(
                        row[date_columns['termination']], 
                        row[date_columns['lock']]
                    )
                    
                    result_row = {
                        'row_index': index,
                        'user_id': row.get('User ID', row.get('ID', f'Row_{index}')),
                        'termination_date': analysis['details']['termination_date'],
                        'lock_date': analysis['details']['lock_date'],
                        'status': analysis['status'],
                        'reason': analysis['reason'],
                        'action_required': analysis['action_required'],
                        'days_difference': analysis['details'].get('days_difference', 0),
                        'termination_is_weekend': analysis['details']['termination_is_weekend'],
                        'termination_is_holiday': analysis['details']['termination_is_holiday'],
                    }
                    results.append(result_row)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            print(f"Error loading and analyzing data: {e}")
            return None
    
    def generate_report(self, results_df, output_file='termination_analysis_report.xlsx'):
        """Generate a detailed report of the analysis"""
        if results_df is None or results_df.empty:
            print("No results to generate report")
            return
        
        # Create summary statistics
        total_records = len(results_df)
        compliant_records = len(results_df[results_df['status'] == 'COMPLIANT'])
        non_compliant_records = len(results_df[results_df['status'] == 'NON_COMPLIANT'])
        action_required_records = len(results_df[results_df['action_required'] == True])
        
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Total records analyzed: {total_records}")
        print(f"Compliant records: {compliant_records} ({compliant_records/total_records*100:.1f}%)")
        print(f"Non-compliant records: {non_compliant_records} ({non_compliant_records/total_records*100:.1f}%)")
        print(f"Records requiring action: {action_required_records}")
        
        # Save detailed report
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main results
            results_df.to_excel(writer, sheet_name='Analysis Results', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': ['Total Records', 'Compliant', 'Non-Compliant', 'Action Required'],
                'Count': [total_records, compliant_records, non_compliant_records, action_required_records],
                'Percentage': [100.0, compliant_records/total_records*100, 
                              non_compliant_records/total_records*100, action_required_records/total_records*100]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Non-compliant records only
            if non_compliant_records > 0:
                non_compliant_df = results_df[results_df['status'] == 'NON_COMPLIANT']
                non_compliant_df.to_excel(writer, sheet_name='Non-Compliant Records', index=False)
        
        print(f"Detailed report saved to: {output_file}")


def main():
    """Main function to run the analysis"""
    print("User Termination and Lock Date Analysis Tool")
    print("=" * 50)
    
    # Get file paths from user
    main_file_path = input("Enter the path to the main Excel file with user data: ").strip()
    holidays_file_path = input("Enter the path to the holidays Excel file: ").strip()
    
    # Validate file paths
    if not os.path.exists(main_file_path):
        print(f"Error: Main file not found at {main_file_path}")
        return
    
    if not os.path.exists(holidays_file_path):
        print(f"Error: Holidays file not found at {holidays_file_path}")
        return
    
    # Create analyzer and run analysis
    analyzer = UserTerminationAnalyzer(main_file_path, holidays_file_path)
    
    print("\nStarting analysis...")
    results = analyzer.load_and_analyze_data()
    
    if results is not None:
        # Generate report
        output_file = input("Enter output file name (default: termination_analysis_report.xlsx): ").strip()
        if not output_file:
            output_file = "termination_analysis_report.xlsx"
        
        analyzer.generate_report(results, output_file)
        
        # Show non-compliant records
        non_compliant = results[results['action_required'] == True]
        if len(non_compliant) > 0:
            print(f"\n=== NON-COMPLIANT RECORDS REQUIRING ACTION ===")
            for _, row in non_compliant.iterrows():
                print(f"User ID: {row['user_id']}")
                print(f"  Termination: {row['termination_date']}")
                print(f"  Lock Date: {row['lock_date']}")
                print(f"  Issue: {row['reason']}")
                print("-" * 40)
    else:
        print("Analysis failed. Please check your input files and try again.")


if __name__ == "__main__":
    main()