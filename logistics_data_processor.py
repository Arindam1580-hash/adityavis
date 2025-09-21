import sys
import pandas as pd
import os
import re
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QFrame, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class BidDataFillerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_data_df = None
        self.template_df = None
        self.filled_df = None
        self.main_file_path = ""
        self.template_file_path = ""
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Bid Data Filler Tool - Fixed Version")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Title
        title = QLabel("Bid Data Filler Tool - Fixed Version")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("margin: 20px; color: #2c3e50;")
        main_layout.addWidget(title)
        
        # Instructions
        instructions_frame = QFrame()
        instructions_frame.setStyleSheet("background-color: #ecf0f1; padding: 15px; border-radius: 5px;")
        instructions_layout = QVBoxLayout(instructions_frame)
        
        inst_title = QLabel("Instructions:")
        inst_title.setFont(QFont("Arial", 12, QFont.Bold))
        instructions_layout.addWidget(inst_title)
        
        instructions_layout.addWidget(QLabel("1. Select your main data CSV file (with Date, User, Zone columns)"))
        instructions_layout.addWidget(QLabel("2. Select your unfilled template CSV file"))
        instructions_layout.addWidget(QLabel("3. Click 'Process Data' to fill the template with correct bid counts"))
        instructions_layout.addWidget(QLabel("4. Click 'Download Filled Template' to save the result"))
        
        main_layout.addWidget(instructions_frame)
        
        # File selection section
        file_section = QFrame()
        file_section.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 5px;")
        file_layout = QGridLayout(file_section)
        
        # Main data file
        file_layout.addWidget(QLabel("Main Data CSV:"), 0, 0)
        self.main_file_label = QLabel("No file selected")
        self.main_file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        file_layout.addWidget(self.main_file_label, 0, 1)
        
        self.btn_select_main = QPushButton("Select Main Data CSV")
        self.btn_select_main.setStyleSheet("background-color: #3498db; color: white; padding: 8px; border-radius: 4px;")
        self.btn_select_main.clicked.connect(self.select_main_file)
        file_layout.addWidget(self.btn_select_main, 0, 2)
        
        # Template file
        file_layout.addWidget(QLabel("Template CSV:"), 1, 0)
        self.template_file_label = QLabel("No file selected")
        self.template_file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        file_layout.addWidget(self.template_file_label, 1, 1)
        
        self.btn_select_template = QPushButton("Select Template CSV")
        self.btn_select_template.setStyleSheet("background-color: #3498db; color: white; padding: 8px; border-radius: 4px;")
        self.btn_select_template.clicked.connect(self.select_template_file)
        file_layout.addWidget(self.btn_select_template, 1, 2)
        
        main_layout.addWidget(file_section)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.btn_process = QPushButton("Process Data")
        self.btn_process.setEnabled(False)
        self.btn_process.setStyleSheet("background-color: #27ae60; color: white; padding: 12px 24px; border-radius: 6px; font-weight: bold;")
        self.btn_process.clicked.connect(self.process_data)
        buttons_layout.addWidget(self.btn_process)
        
        self.btn_download = QPushButton("Download Filled Template")
        self.btn_download.setEnabled(False)
        self.btn_download.setStyleSheet("background-color: #e67e22; color: white; padding: 12px 24px; border-radius: 6px; font-weight: bold;")
        self.btn_download.clicked.connect(self.download_filled_template)
        buttons_layout.addWidget(self.btn_download)
        
        main_layout.addLayout(buttons_layout)
        
        # Status and log area
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Status: Ready to process files")
        self.status_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px;")
        status_layout.addWidget(self.status_label)
        
        # Log area
        log_label = QLabel("Processing Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        status_layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        self.log_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace; font-size: 10px;")
        status_layout.addWidget(self.log_area)
        
        main_layout.addWidget(status_frame)
    
    def log(self, message):
        """Add message to log area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        QApplication.processEvents()
    
    def select_main_file(self):
        """Select main data CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Main Data CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.main_file_path = file_path
            filename = os.path.basename(file_path)
            self.main_file_label.setText(filename)
            self.main_file_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.log(f"Main data file selected: {filename}")
            self.check_files_ready()
    
    def select_template_file(self):
        """Select template CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Template CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.template_file_path = file_path
            filename = os.path.basename(file_path)
            self.template_file_label.setText(filename)
            self.template_file_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.log(f"Template file selected: {filename}")
            self.check_files_ready()
    
    def check_files_ready(self):
        """Check if both files are selected and enable process button"""
        if self.main_file_path and self.template_file_path:
            self.btn_process.setEnabled(True)
            self.status_label.setText("Status: Ready to process data")
            self.status_label.setStyleSheet("font-weight: bold; color: #27ae60; padding: 10px;")
    
    def clean_user_name(self, name):
        """Clean user name by removing extra spaces and BOM characters"""
        if pd.isna(name):
            return None
        return str(name).strip().replace('\ufeff', '').replace('\u200b', '')
    
    def extract_day_from_date(self, date_str):
        """Extract day number from date string - improved version"""
        if pd.isna(date_str) or not isinstance(date_str, str):
            return None
        
        # Clean the string
        date_str = str(date_str).strip().replace('\ufeff', '')
        
        # Pattern 1: "Aug 1, 2025, 3:56:33 AM" or similar
        match = re.search(r'Aug\s+(\d+)[,\s]', date_str)
        if match:
            day = int(match.group(1))
            return day if 1 <= day <= 6 else None
        
        # Pattern 2: Just "Aug 1" format
        match = re.search(r'Aug\s+(\d+)', date_str)
        if match:
            day = int(match.group(1))
            return day if 1 <= day <= 6 else None
            
        return None
    
    def process_data(self):
        """Process the data and fill the template - CORRECTED VERSION"""
        try:
            self.log("=== Starting CORRECTED data processing ===")
            self.status_label.setText("Status: Processing data...")
            self.status_label.setStyleSheet("font-weight: bold; color: #f39c12; padding: 10px;")
            
            # Load main data file
            self.log("Loading main data file...")
            try:
                self.main_data_df = pd.read_csv(self.main_file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                self.main_data_df = pd.read_csv(self.main_file_path, encoding='latin1')
            
            # Clean column names
            self.main_data_df.columns = [col.strip().replace('\ufeff', '') for col in self.main_data_df.columns]
            self.log(f"Main data loaded: {len(self.main_data_df)} rows")
            self.log(f"Main data columns: {list(self.main_data_df.columns)}")
            
            # Load template file (skip first row)
            self.log("Loading template file...")
            try:
                self.template_df = pd.read_csv(self.template_file_path, skiprows=1, encoding='utf-8-sig')
            except UnicodeDecodeError:
                self.template_df = pd.read_csv(self.template_file_path, skiprows=1, encoding='latin1')
            
            # Clean template column names
            self.template_df.columns = [col.strip().replace('\ufeff', '') for col in self.template_df.columns]
            self.log(f"Template loaded: {len(self.template_df)} rows")
            
            # Validate columns
            if 'User' not in self.main_data_df.columns or 'Date' not in self.main_data_df.columns:
                raise ValueError("Main data must have 'User' and 'Date' columns")
            
            if 'User' not in self.template_df.columns:
                raise ValueError("Template must have 'User' column")
            
            # Clean user names in both dataframes
            self.log("Cleaning user names...")
            self.main_data_df['User_Clean'] = self.main_data_df['User'].apply(self.clean_user_name)
            self.template_df['User_Clean'] = self.template_df['User'].apply(self.clean_user_name)
            
            # Remove rows with null users from main data
            initial_count = len(self.main_data_df)
            self.main_data_df = self.main_data_df[self.main_data_df['User_Clean'].notna()]
            self.main_data_df = self.main_data_df[self.main_data_df['User_Clean'] != '']
            self.log(f"Removed {initial_count - len(self.main_data_df)} rows with empty users from main data")
            
            # Extract days from dates
            self.log("Extracting day numbers from dates...")
            self.main_data_df['Day'] = self.main_data_df['Date'].apply(self.extract_day_from_date)
            
            # Show day extraction results
            valid_days = self.main_data_df['Day'].dropna()
            self.log(f"Valid days extracted: {len(valid_days)} out of {len(self.main_data_df)} records")
            
            if len(valid_days) > 0:
                day_counts = valid_days.value_counts().sort_index()
                for day, count in day_counts.items():
                    self.log(f"  Day {day}: {count} records")
            
            # Filter to only valid day records
            main_data_valid = self.main_data_df[self.main_data_df['Day'].notna()].copy()
            self.log(f"Processing {len(main_data_valid)} records with valid days")
            
            # Get unique users from main data
            main_users = set(main_data_valid['User_Clean'].unique())
            self.log(f"Unique users in main data: {len(main_users)}")
            
            # Create copy of template for filling
            self.filled_df = self.template_df.copy()
            
            # Initialize all day columns with 0
            day_columns = ['1', '2', '3', '4', '5', '6']
            for col in day_columns:
                if col in self.filled_df.columns:
                    self.filled_df[col] = 0
            
            if 'Grand Total' in self.filled_df.columns:
                self.filled_df['Grand Total'] = 0
            
            # Count bids by user and day
            user_day_counts = main_data_valid.groupby(['User_Clean', 'Day']).size().reset_index(name='BidCount')
            self.log(f"Generated {len(user_day_counts)} user-day combinations")
            
            # Process each user in template
            self.log("=== Processing individual users ===")
            processed_users = 0
            users_with_data = 0
            users_without_data = 0
            
            for idx, template_row in self.filled_df.iterrows():
                user_clean = template_row['User_Clean']
                user_original = template_row['User']
                
                # Skip Grand Total row
                if pd.isna(user_clean) or user_clean == '' or user_clean == 'Grand Total':
                    continue
                
                # Check if this user exists in main data
                if user_clean in main_users:
                    # User has data - get their bid counts
                    user_bids = user_day_counts[user_day_counts['User_Clean'] == user_clean]
                    
                    if not user_bids.empty:
                        user_total = 0
                        daily_counts = []
                        
                        for _, bid_row in user_bids.iterrows():
                            day = int(bid_row['Day'])
                            count = bid_row['BidCount']
                            
                            if 1 <= day <= 6:
                                day_col = str(day)
                                if day_col in self.filled_df.columns:
                                    self.filled_df.at[idx, day_col] = count
                                    user_total += count
                                    daily_counts.append(f"Day {day}={count}")
                        
                        # Set Grand Total
                        if 'Grand Total' in self.filled_df.columns:
                            self.filled_df.at[idx, 'Grand Total'] = user_total
                        
                        if user_total > 0:
                            users_with_data += 1
                            self.log(f"✓ {user_original}: {user_total} bids ({', '.join(daily_counts)})")
                        else:
                            users_without_data += 1
                            self.log(f"○ {user_original}: 0 bids (user exists but no valid day data)")
                    else:
                        users_without_data += 1
                        self.log(f"○ {user_original}: 0 bids (user exists but no day counts)")
                else:
                    # User does not exist in main data - leave as 0
                    users_without_data += 1
                    self.log(f"○ {user_original}: 0 bids (user not found in main data)")
                
                processed_users += 1
            
            # Calculate Grand Total row
            grand_total_rows = self.filled_df[self.filled_df['User_Clean'] == 'Grand Total']
            if not grand_total_rows.empty:
                gt_idx = grand_total_rows.index[0]
                
                self.log("=== Calculating Grand Totals ===")
                day_totals = {}
                overall_total = 0
                
                for day_col in day_columns:
                    if day_col in self.filled_df.columns:
                        # Sum all users (exclude Grand Total row)
                        col_total = self.filled_df[day_col].iloc[:-1].sum()
                        self.filled_df.at[gt_idx, day_col] = col_total
                        day_totals[day_col] = col_total
                        overall_total += col_total
                        self.log(f"Day {day_col} total: {col_total}")
                
                # Set overall grand total
                if 'Grand Total' in self.filled_df.columns:
                    self.filled_df.at[gt_idx, 'Grand Total'] = overall_total
                    self.log(f"Overall Grand Total: {overall_total}")
            
            # Enable download
            self.btn_download.setEnabled(True)
            self.status_label.setText("Status: Processing complete! Ready to download.")
            self.status_label.setStyleSheet("font-weight: bold; color: #27ae60; padding: 10px;")
            
            self.log(f"=== PROCESSING COMPLETE ===")
            self.log(f"Total users processed: {processed_users}")
            self.log(f"Users with data: {users_with_data}")
            self.log(f"Users without data: {users_without_data}")
            
            # Show success message
            QMessageBox.information(
                self, "Success", 
                f"Data processed successfully!\n\n"
                f"• Total users processed: {processed_users}\n"
                f"• Users with bid data: {users_with_data}\n"  
                f"• Users with no data: {users_without_data}\n"
                f"• Check the log for detailed user-by-user breakdown\n\n"
                f"Ready to download the corrected template!"
            )
            
        except Exception as e:
            error_msg = str(e)
            self.status_label.setText(f"Status: Error occurred")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c; padding: 10px;")
            self.log(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Processing Error", f"Failed to process data:\n\n{error_msg}")
            import traceback
            traceback.print_exc()
    
    def download_filled_template(self):
        """Download the filled template"""
        if self.filled_df is None:
            QMessageBox.warning(self, "No Data", "No processed data to download.")
            return
        
        # Suggest filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"corrected_bidding_report_{timestamp}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Corrected Template", default_filename, "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Create final output without the User_Clean column
                output_df = self.filled_df.drop('User_Clean', axis=1)
                
                # Save with the original header
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    f.write("(North Branch) Day Wise Biding Report,,,,,,,,,\n")
                    output_df.to_csv(f, index=False)
                
                filename = os.path.basename(file_path)
                self.status_label.setText(f"Status: File saved successfully")
                self.log(f"Corrected template saved: {filename}")
                
                QMessageBox.information(
                    self, "Download Complete", 
                    f"Corrected template saved successfully!\n\n"
                    f"File: {filename}\n"
                    f"Location: {file_path}"
                )
                
            except Exception as e:
                error_msg = str(e)
                self.status_label.setText("Status: Error saving file")
                self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c; padding: 10px;")
                self.log(f"ERROR saving file: {error_msg}")
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n\n{error_msg}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BidDataFillerApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()