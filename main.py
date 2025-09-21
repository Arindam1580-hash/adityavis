import sys
import pandas as pd
from datetime import date
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QCheckBox, QLineEdit,
                             QFileDialog, QMessageBox, QTabWidget, QLabel, QHeaderView,
                             QGroupBox, QGridLayout, QSplitter, QFrame)
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QFont

class EnhancedTableModel(QAbstractTableModel):
    """Enhanced table model with better data handling."""
    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else pd.DataFrame()
        
    def rowCount(self, parent=None):
        return len(self._data)
    
    def columnCount(self, parent=None):
        return len(self._data.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value) if pd.notna(value) else ""
        return None
    
    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[col])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(col + 1)
        return None
    
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        ascending = order == Qt.AscendingOrder
        self._data = self._data.sort_values(by=self._data.columns[column], ascending=ascending)
        self._data.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()
    
    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data.copy() if new_data is not None else pd.DataFrame()
        self.endResetModel()

class FilterWidget(QWidget):
    """Widget for column-based filtering."""
    filters_changed = pyqtSignal()
    
    def __init__(self, columns=None):
        super().__init__()
        self.columns = columns or []
        self.filter_inputs = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Column Filters")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)
        
        # Scrollable area for filters
        self.filter_frame = QFrame()
        self.filter_layout = QGridLayout(self.filter_frame)
        layout.addWidget(self.filter_frame)
        
        # Reset button
        self.reset_btn = QPushButton("Reset All Filters")
        self.reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(self.reset_btn)
    
    def update_columns(self, columns):
        """Update available columns for filtering."""
        self.columns = columns
        self._clear_filters()
        self._create_filter_inputs()
    
    def _clear_filters(self):
        """Clear existing filter inputs."""
        for i in reversed(range(self.filter_layout.count())): 
            self.filter_layout.itemAt(i).widget().setParent(None)
        self.filter_inputs.clear()
    
    def _create_filter_inputs(self):
        """Create filter input widgets for each column."""
        for i, column in enumerate(self.columns):
            label = QLabel(f"{column}:")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Filter by {column}...")
            line_edit.textChanged.connect(self.filters_changed.emit)
            
            self.filter_layout.addWidget(label, i, 0)
            self.filter_layout.addWidget(line_edit, i, 1)
            
            self.filter_inputs[column] = line_edit
    
    def get_active_filters(self):
        """Get dictionary of active filters."""
        return {col: widget.text().strip() 
                for col, widget in self.filter_inputs.items() 
                if widget.text().strip()}
    
    def reset_filters(self):
        """Reset all filter inputs."""
        for widget in self.filter_inputs.values():
            widget.clear()

class EnhancedDashboardPage(QWidget):
    """Enhanced dashboard page with comprehensive filtering and sorting."""
    def __init__(self, report_type, title="Dashboard"):
        super().__init__()
        self.report_type = report_type
        self.title = title
        self.df = None
        self.filtered_df = None
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel for filters
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.btn_open = QPushButton("Open CSV File")
        self.btn_save = QPushButton("Save Filtered Data")
        self.btn_save.setEnabled(False)
        
        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.btn_save)
        left_layout.addWidget(file_group)
        
        # Filter widget
        self.filter_widget = FilterWidget()
        left_layout.addWidget(self.filter_widget)
        
        # Status info
        self.status_label = QLabel("No data loaded")
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_panel)
        
        # Right panel for table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Table controls
        table_controls = QHBoxLayout()
        self.records_label = QLabel("Records: 0")
        table_controls.addWidget(self.records_label)
        table_controls.addStretch()
        
        right_layout.addLayout(table_controls)
        
        # Table view
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.verticalHeader().setVisible(False)
        right_layout.addWidget(self.table_view)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])  # Set initial sizes
        
        # Connect signals
        self.btn_open.clicked.connect(self._open_file)
        self.btn_save.clicked.connect(self._save_file)
        self.filter_widget.filters_changed.connect(self._apply_filters)
    
    def _open_file(self):
        """Open and load a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self._update_display()
                self.status_label.setText(f"Loaded: {len(self.df)} rows, {len(self.df.columns)} columns")
                self.btn_save.setEnabled(True)
                
                # Update filter widget with new columns
                self.filter_widget.update_columns(list(self.df.columns))
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def _apply_filters(self):
        """Apply all active filters to the data."""
        if self.df is None:
            return
        
        filtered_df = self.df.copy()
        active_filters = self.filter_widget.get_active_filters()
        
        for column, filter_text in active_filters.items():
            if column in filtered_df.columns:
                # Apply case-insensitive string filtering, handle NaN values
                mask = filtered_df[column].astype(str).str.contains(
                    filter_text, case=False, na=False
                )
                filtered_df = filtered_df[mask]
        
        self.filtered_df = filtered_df
        self._update_table(filtered_df)
    
    def _update_display(self):
        """Update the entire display with current data."""
        if self.df is not None:
            self.filtered_df = self.df.copy()
            self._update_table(self.filtered_df)
    
    def _update_table(self, data):
        """Update table with given data."""
        model = EnhancedTableModel(data)
        self.table_view.setModel(model)
        self.records_label.setText(f"Records: {len(data)}")
        
        # Auto-resize columns to content
        self.table_view.resizeColumnsToContents()
    
    def _save_file(self):
        """Save the currently displayed (filtered) data."""
        if self.filtered_df is None or self.filtered_df.empty:
            QMessageBox.warning(self, "No Data", "No data to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                self.filtered_df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Data saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def update_data(self, new_df):
        """Update data from external source (for compatibility)."""
        self.df = new_df.copy() if new_df is not None else None
        if self.df is not None:
            self._update_display()
            self.filter_widget.update_columns(list(self.df.columns))
            self.status_label.setText(f"Updated: {len(self.df)} rows, {len(self.df.columns)} columns")
            self.btn_save.setEnabled(True)

class PivotConvertorPage(QWidget):
    """Enhanced Pivot Convertor with comprehensive features."""
    data_loaded = pyqtSignal(pd.DataFrame)
    
    def __init__(self):
        super().__init__()
        self.original_df = None
        self.transformed_df = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel for controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.btn_open = QPushButton("Open CSV File")
        self.btn_get_data = QPushButton("Display Original Data")
        self.btn_save = QPushButton("Save Transformed Data")
        self.btn_save.setEnabled(False)
        
        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.btn_get_data)
        file_layout.addWidget(self.btn_save)
        left_layout.addWidget(file_group)
        
        # Transformation controls
        transform_group = QGroupBox("Transformation Options")
        transform_layout = QVBoxLayout(transform_group)
        
        # Zone filtering
        zone_layout = QHBoxLayout()
        zone_layout.addWidget(QLabel("Zone Filter:"))
        self.combo_zone = QComboBox()
        zone_layout.addWidget(self.combo_zone)
        transform_layout.addLayout(zone_layout)
        
        # Transform options
        self.check_zone_col = QCheckBox("Create Zone Columns (Pivot)")
        transform_layout.addWidget(self.check_zone_col)
        
        self.btn_transform = QPushButton("Transform Data")
        transform_layout.addWidget(self.btn_transform)
        
        left_layout.addWidget(transform_group)
        
        # Filters for original data
        self.filter_widget = FilterWidget()
        left_layout.addWidget(self.filter_widget)
        
        # Status
        today_str = date.today().strftime("%B %d, %Y")
        self.status_label = QLabel(f"Date: {today_str}\nNo data loaded")
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_panel)
        
        # Right panel for table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Table info
        self.table_info = QLabel("No data to display")
        right_layout.addWidget(self.table_info)
        
        # Table
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        right_layout.addWidget(self.table_view)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])
        
        # Connect signals
        self.btn_open.clicked.connect(self._open_file)
        self.btn_get_data.clicked.connect(self._display_original_data)
        self.btn_transform.clicked.connect(self._transform_data)
        self.btn_save.clicked.connect(self._save_file)
        self.filter_widget.filters_changed.connect(self._apply_filters)
    
    def _open_file(self):
        """Open and load CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                self.original_df = pd.read_csv(file_path)
                self.transformed_df = None
                self._display_original_data()
                
                # Update zone combo
                self.combo_zone.clear()
                self.combo_zone.addItem("All Zones")
                if 'Zone' in self.original_df.columns:
                    zones = sorted(self.original_df['Zone'].astype(str).unique())
                    self.combo_zone.addItems(zones)
                
                # Update filter widget
                self.filter_widget.update_columns(list(self.original_df.columns))
                
                # Emit signal for other tabs
                self.data_loaded.emit(self.original_df)
                
                self.status_label.setText(
                    f"Date: {date.today().strftime('%B %d, %Y')}\n"
                    f"Loaded: {len(self.original_df)} rows, {len(self.original_df.columns)} columns"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def _display_original_data(self):
        """Display the original data."""
        if self.original_df is not None:
            self._update_table(self.original_df, "Original Data")
        else:
            QMessageBox.warning(self, "No Data", "Please open a file first.")
    
    def _apply_filters(self):
        """Apply filters to original data."""
        if self.original_df is None:
            return
        
        filtered_df = self.original_df.copy()
        active_filters = self.filter_widget.get_active_filters()
        
        for column, filter_text in active_filters.items():
            if column in filtered_df.columns:
                mask = filtered_df[column].astype(str).str.contains(
                    filter_text, case=False, na=False
                )
                filtered_df = filtered_df[mask]
        
        self._update_table(filtered_df, f"Filtered Data ({len(filtered_df)} rows)")
    
    def _transform_data(self):
        """Transform the data using pivot or groupby operations."""
        if self.original_df is None:
            QMessageBox.warning(self, "No Data", "Please open a file first.")
            return
        
        try:
            # Get filtered data if filters are active
            active_filters = self.filter_widget.get_active_filters()
            data_to_transform = self.original_df.copy()
            
            # Apply filters
            for column, filter_text in active_filters.items():
                if column in data_to_transform.columns:
                    mask = data_to_transform[column].astype(str).str.contains(
                        filter_text, case=False, na=False
                    )
                    data_to_transform = data_to_transform[mask]
            
            # Apply zone filter
            selected_zone = self.combo_zone.currentText()
            if selected_zone != "All Zones" and 'Zone' in data_to_transform.columns:
                data_to_transform = data_to_transform[data_to_transform['Zone'] == selected_zone]
            
            # Transform based on checkbox
            if self.check_zone_col.isChecked():
                # Pivot transformation
                if 'User' in data_to_transform.columns and 'Zone' in data_to_transform.columns and 'Load No.' in data_to_transform.columns:
                    self.transformed_df = pd.pivot_table(
                        data_to_transform, 
                        index='User', 
                        columns='Zone', 
                        values='Load No.', 
                        aggfunc='count', 
                        fill_value=0
                    )
                else:
                    QMessageBox.warning(self, "Missing Columns", 
                                      "Required columns (User, Zone, Load No.) not found.")
                    return
            else:
                # Group by transformation
                if 'User' in data_to_transform.columns and 'Load No.' in data_to_transform.columns:
                    self.transformed_df = data_to_transform.groupby('User')['Load No.'].count().reset_index()
                    self.transformed_df.columns = ['User', 'Load_Count']
                else:
                    QMessageBox.warning(self, "Missing Columns", 
                                      "Required columns (User, Load No.) not found.")
                    return
            
            # Display transformed data
            display_df = self.transformed_df.reset_index() if hasattr(self.transformed_df, 'reset_index') else self.transformed_df
            self._update_table(display_df, "Transformed Data")
            self.btn_save.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Transform Error", f"Failed to transform data: {str(e)}")
    
    def _update_table(self, data, info_text):
        """Update table display with given data."""
        model = EnhancedTableModel(data)
        self.table_view.setModel(model)
        self.table_info.setText(f"{info_text} - Records: {len(data)}")
        self.table_view.resizeColumnsToContents()
    
    def _save_file(self):
        """Save transformed data."""
        if self.transformed_df is None:
            QMessageBox.warning(self, "No Transformed Data", "Please transform the data first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                save_df = self.transformed_df.reset_index() if hasattr(self.transformed_df, 'reset_index') else self.transformed_df
                save_df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Data saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

class MainWindow(QMainWindow):
    """Main application window with all tabs."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Logistics Analysis Tool")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create all pages
        self.pivot_convertor_page = PivotConvertorPage()
        self.bid_performance_page = EnhancedDashboardPage("bid_performance", "Bid Performance")
        self.order_wise_page = EnhancedDashboardPage("order_wise", "Order Wise Person Bidding")
        self.placement_page = EnhancedDashboardPage("placement", "Placement Report")
        self.roado_erp_page = EnhancedDashboardPage("roado_erp", "Roado ERP Report")
        self.time_gap_page = EnhancedDashboardPage("time_gap", "Time Gap Bidding")
        
        # Add tabs
        self.tabs.addTab(self.pivot_convertor_page, "Pivot Convertor")
        self.tabs.addTab(self.bid_performance_page, "Bid Performance")
        self.tabs.addTab(self.order_wise_page, "Order Wise Person Bidding")
        self.tabs.addTab(self.placement_page, "Placement Report")
        self.tabs.addTab(self.roado_erp_page, "Roado ERP Report")
        self.tabs.addTab(self.time_gap_page, "Time Gap Bidding")
        
        # Connect pivot convertor to other tabs
        self.pivot_convertor_page.data_loaded.connect(self.bid_performance_page.update_data)
        self.pivot_convertor_page.data_loaded.connect(self.order_wise_page.update_data)
        self.pivot_convertor_page.data_loaded.connect(self.placement_page.update_data)
        self.pivot_convertor_page.data_loaded.connect(self.roado_erp_page.update_data)
        self.pivot_convertor_page.data_loaded.connect(self.time_gap_page.update_data)

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()