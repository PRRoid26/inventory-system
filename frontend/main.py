"""
IT Asset Inventory Management System - Qt Desktop Client
Production-ready PyQt6 application with cloud connectivity
MODIFICATIONS:
- Overview tab with pie chart showing device status distribution
- Category filtering with ESC key to reset
- Active work log notes editing that syncs to inventory tab
"""

import sys
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QLabel, QComboBox, QDateEdit, QTextEdit, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QDialogButtonBox, QHeaderView, QCompleter,
    QGroupBox, QGridLayout, QSpinBox, QCheckBox, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate, QTimer, QThread, pyqtSignal, QStringListModel
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QKeyEvent

# Matplotlib for pie chart
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change for cloud deployment


class APIClient:
    """Handle all API communications"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token = None
        self.headers = {}
    
    def set_token(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def login(self, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.set_token(data['access_token'])
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def register(self, username: str, email: str, password: str, full_name: str = "") -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": full_name
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.set_token(data['access_token'])
                return True
            return False
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def get_equipment(self, category=None, status=None, search=None, import_id=None):
        """Fetch ALL equipment, paginating automatically."""
        try:
            all_items = []
            skip = 0
            page_size = 500
            while True:
                params = {'skip': skip, 'limit': page_size}
                if category:
                    params['category'] = category
                if import_id is not None:
                    params['import_id'] = import_id
                if status:
                    params['status'] = status
                if search:
                    params['search'] = search

                response = requests.get(
                    f"{self.base_url}/api/equipment",
                    headers=self.headers,
                    params=params
                )
                if response.status_code != 200:
                    break
                page = response.json()
                if not page:
                    break
                all_items.extend(page)
                if len(page) < page_size:
                    break
                skip += page_size
            return all_items
        except Exception as e:
            print(f"Get equipment error: {e}")
            return []

    def get_import_categories(self):
        """Return list of import records (used to populate Category dropdown)."""
        try:
            response = requests.get(
                f"{self.base_url}/api/imports",
                headers=self.headers,
                params={"limit": 200}
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get import categories error: {e}")
            return []
    
    def search_equipment_autocomplete(self, prefix: str):
        try:
            response = requests.get(
                f"{self.base_url}/api/equipment/search/{prefix}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Autocomplete error: {e}")
            return []
    
    def create_equipment(self, data: dict):
        try:
            response = requests.post(
                f"{self.base_url}/api/equipment",
                headers=self.headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Create equipment error: {e}")
            return False
    
    def update_equipment(self, equipment_id: int, data: dict):
        try:
            response = requests.put(
                f"{self.base_url}/api/equipment/{equipment_id}",
                headers=self.headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Update equipment error: {e}")
            return False
    
    def delete_equipment(self, equipment_id: int):
        try:
            response = requests.delete(
                f"{self.base_url}/api/equipment/{equipment_id}",
                headers=self.headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Delete equipment error: {e}")
            return False
    
    def get_specifications(self, equipment_id: int):
        try:
            response = requests.get(
                f"{self.base_url}/api/specifications/{equipment_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get specifications error: {e}")
            return []
    
    def create_specification(self, data: dict):
        try:
            response = requests.post(
                f"{self.base_url}/api/specifications",
                headers=self.headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Create specification error: {e}")
            return False
    
    def update_specification(self, spec_id: int, data: dict):
        try:
            response = requests.put(
                f"{self.base_url}/api/specifications/{spec_id}",
                headers=self.headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Update specification error: {e}")
            return False
    
    def get_worklogs(self, equipment_id=None, status=None):
        try:
            params = {}
            if equipment_id:
                params['equipment_id'] = equipment_id
            if status:
                params['status'] = status
            
            response = requests.get(
                f"{self.base_url}/api/worklogs",
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get worklogs error: {e}")
            return []
    
    def create_worklog(self, data: dict):
        try:
            print(f"[DEBUG] Creating worklog with data: {data}")
            response = requests.post(
                f"{self.base_url}/api/worklogs",
                headers=self.headers,
                json=data
            )
            if response.status_code != 200:
                print(f"[DEBUG] Worklog creation failed: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Create worklog error: {e}")
            return False
    
    def update_worklog(self, worklog_id: int, data: dict):
        try:
            print(f"[DEBUG] Updating worklog {worklog_id} with data: {data}")
            response = requests.put(
                f"{self.base_url}/api/worklogs/{worklog_id}",
                headers=self.headers,
                json=data
            )
            if response.status_code != 200:
                print(f"[DEBUG] Worklog update failed: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Update worklog error: {e}")
            return False
    
    def upload_csv(self, file_path: str):
        try:
            fname = Path(file_path).name
            ext = Path(file_path).suffix.lower()

            mime_map = {
                '.csv':  'text/csv',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls':  'application/vnd.ms-excel',
            }
            mime = mime_map.get(ext, 'application/octet-stream')

            with open(file_path, 'rb') as f:
                files = {'file': (fname, f, mime)}
                response = requests.post(
                    f"{self.base_url}/api/import/csv",
                    headers=self.headers,
                    files=files
                )
                if response.status_code == 200:
                    return response.json()
                try:
                    err = response.json().get('detail', response.text)
                except Exception:
                    err = response.text
                return {"error": err}
        except Exception as e:
            print(f"CSV upload error: {e}")
            return {"error": str(e)}
    
    def get_imports(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/imports",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get imports error: {e}")
            return []
    
    def get_import_details(self, import_id: int):
        try:
            response = requests.get(
                f"{self.base_url}/api/imports/{import_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Get import details error: {e}")
            return None
    
    def delete_import(self, import_id: int, delete_equipment: bool = False):
        try:
            response = requests.delete(
                f"{self.base_url}/api/imports/{import_id}",
                headers=self.headers,
                params={"delete_equipment": delete_equipment}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Delete import error: {e}")
            return False
    
    def get_overview_stats(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/overview",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Get overview stats error: {e}")
            return {}
    
    def get_category_stats(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/category",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get category stats error: {e}")
            return []
    
    def get_category_equipment_stats(self, category: str):
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/category/{category}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Get category equipment stats error: {e}")
            return []


# class PieChartWidget(QWidget):
#     """Widget to display a pie chart"""
    
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.figure = Figure(figsize=(5, 4))
#         self.canvas = FigureCanvas(self.figure)
        
#         layout = QVBoxLayout()
#         layout.addWidget(self.canvas)
#         self.setLayout(layout)
    
#     def update_chart(self, data: dict, title: str = "Device Status Distribution"):
#         """Update pie chart with new data"""
#         self.figure.clear()
#         ax = self.figure.add_subplot(111)
        
#         # Filter out zero values
#         labels = []
#         sizes = []
#         colors = []
        
#         color_map = {
#             'Available': '#4CAF50',   # Green
#             'In Service': '#FFC107',  # Amber
#             'Faulty': '#F44336',      # Red
#             'Retired': '#9E9E9E'      # Grey
#         }
        
#         for key in ['Available', 'In Service', 'Faulty', 'Retired']:
#             value = data.get(key.lower().replace(' ', '_'), 0)
#             if value > 0:
#                 labels.append(f'{key}\n({value})')
#                 sizes.append(value)
#                 colors.append(color_map.get(key, '#2196F3'))
        
#         if sizes:
#             ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
#                    startangle=90, textprops={'fontsize': 9})
#             ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
#         else:
#             ax.text(0.5, 0.5, 'No Data Available', 
#                    horizontalalignment='center',
#                    verticalalignment='center',
#                    transform=ax.transAxes,
#                    fontsize=12)
#             ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        
#         self.canvas.draw()
class BarChartWidget(QWidget):
    """Modern horizontal stacked bar chart widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 1.8), facecolor='#242424')
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def update_chart(self, data: dict, title: str = ""):
        """Update horizontal stacked bar chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Set dark background
        ax.set_facecolor('#242424')
        self.figure.patch.set_facecolor('#242424')
        
        # Color scheme matching modern UI
        colors = {
            'In Service': '#5B9BD5',    # Blue
            'Faulty': '#ED7D31',        # Orange
            'Available': '#70AD47',     # Green
            'Retired': '#A5A5A5'        # Grey
        }
        
        # Get values in specific order
        statuses = ['Available', 'In Service', 'Faulty', 'Retired']
        values = []
        chart_colors = []
        labels = []
        
        total = data.get('total', 0)
        
        for status in statuses:
            value = data.get(status.lower().replace(' ', '_'), 0)
            if value > 0:
                values.append(value)
                chart_colors.append(colors[status])
                percentage = (value / total * 100) if total > 0 else 0
                # Show decimal for small percentages, otherwise round to nearest integer
                if percentage < 1 and percentage > 0:
                    labels.append(f'{status}: {value} ({percentage:.1f}%)')
                else:
                    labels.append(f'{status}: {value} ({percentage:.0f}%)')
        
        if values:
            # Create sleek horizontal stacked bar with minimum visibility for tiny segments
            left = 0
            bar_height = 0.5
            
            # Calculate minimum visible width (2% of total for segments < 1%)
            min_visible_percent = 2.0
            
            # Identify which segments need boosting
            boosted_widths = []
            boost_total = 0
            
            for value in values:
                percentage = (value / total * 100)
                if percentage < 1 and percentage > 0:
                    # Boost this segment to minimum visible width
                    boosted_width = total * (min_visible_percent / 100)
                    boosted_widths.append(boosted_width)
                    boost_total += (boosted_width - value)
                else:
                    boosted_widths.append(value)
            
            # Adjust large segments proportionally to make room for boosted segments
            if boost_total > 0:
                # Find segments that can be reduced
                large_segments_total = sum(w for w in boosted_widths if w > total * 0.05)  # segments > 5%
                if large_segments_total > 0:
                    adjusted_widths = []
                    for orig_val, boosted_val in zip(values, boosted_widths):
                        if boosted_val > total * 0.05:
                            # Reduce proportionally
                            reduction_factor = (large_segments_total - boost_total) / large_segments_total
                            adjusted_widths.append(boosted_val * reduction_factor)
                        else:
                            adjusted_widths.append(boosted_val)
                    boosted_widths = adjusted_widths
            
            # Draw the bars
            for i, (value, color, width) in enumerate(zip(values, chart_colors, boosted_widths)):
                # Draw the bar segment with thick white edge for visibility
                bar = ax.barh(0, width, left=left, height=bar_height, color=color, 
                       edgecolor='white', linewidth=2.5, alpha=0.95)
                
                left += width
            
            # Set limits based on actual displayed total
            display_total = sum(boosted_widths)
            ax.set_xlim(0, display_total)
            ax.set_ylim(-0.5, 0.5)
            
            # Hide all spines and ticks
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Modern legend at bottom
            legend = ax.legend(labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                             ncol=4, frameon=False, fontsize=11,
                             labelcolor='white', handlelength=1.5, handleheight=0.8)
            
            # Style legend markers
            for patch in legend.get_patches():
                patch.set_height(10)
                patch.set_y(patch.get_y() - 3)
        else:
            # No data state
            ax.text(0.5, 0.5, 'No Data Available', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   fontsize=14, color='#888', 
                   style='italic')
            ax.axis('off')
        
        self.figure.tight_layout(pad=0.5)
        self.canvas.draw()


class LoginDialog(QDialog):
    """Login/Registration dialog"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("IT Asset Management - Login")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("IT Asset Management System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Production-Grade Inventory Management")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Login form
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        button_layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.show_register_dialog)
        button_layout.addWidget(self.register_btn)
        
        layout.addLayout(button_layout)
        
        # Server settings
        layout.addSpacing(20)
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit(API_BASE_URL)
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        self.setLayout(layout)
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        # Update API base URL
        global API_BASE_URL
        API_BASE_URL = self.server_input.text()
        self.api_client.base_url = API_BASE_URL
        
        if self.api_client.login(username, password):
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
    
    def show_register_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New User")
        layout = QFormLayout()
        
        username = QLineEdit()
        email = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        full_name = QLineEdit()
        
        layout.addRow("Username:", username)
        layout.addRow("Email:", email)
        layout.addRow("Password:", password)
        layout.addRow("Full Name:", full_name)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self.api_client.register(
                username.text(),
                email.text(),
                password.text(),
                full_name.text()
            ):
                QMessageBox.information(self, "Success", "Registration successful! Please login.")
            else:
                QMessageBox.critical(self, "Error", "Registration failed")


class EquipmentDialog(QDialog):
    """Dialog for adding/editing equipment"""
    
    def __init__(self, parent=None, equipment_data=None):
        super().__init__(parent)
        self.equipment_data = equipment_data
        self.setWindowTitle("Add Equipment" if not equipment_data else "Edit Equipment")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.asset_no = QLineEdit(self.equipment_data.get('asset_no', '') if self.equipment_data else '')
        layout.addRow("Asset No:", self.asset_no)
        
        self.serial_no = QLineEdit(self.equipment_data.get('serial_no', '') if self.equipment_data else '')
        layout.addRow("Serial No:", self.serial_no)
        
        self.product_name = QLineEdit(self.equipment_data.get('product_name', '') if self.equipment_data else '')
        layout.addRow("Product Name:", self.product_name)
        
        self.category = QComboBox()
        categories = [
            'Computers', 'Network Equipment', 'Monitors', 'Printers & Scanners',
            'Servers', 'Mobile Devices', 'Tablets', 'Peripherals', 'Power & UPS',
            'Cables & Adapters', 'Other'
        ]
        self.category.addItems(categories)
        if self.equipment_data:
            idx = self.category.findText(self.equipment_data.get('category', ''))
            if idx >= 0:
                self.category.setCurrentIndex(idx)
        layout.addRow("Category:", self.category)
        
        self.status = QComboBox()
        self.status.addItems(['Available', 'In Service', 'Faulty', 'Retired'])
        if self.equipment_data:
            idx = self.status.findText(self.equipment_data.get('status', ''))
            if idx >= 0:
                self.status.setCurrentIndex(idx)
        layout.addRow("Status:", self.status)
        
        self.location = QLineEdit(self.equipment_data.get('location', '') if self.equipment_data else '')
        layout.addRow("Location:", self.location)
        
        self.supplier = QLineEdit(self.equipment_data.get('supplier', '') if self.equipment_data else '')
        layout.addRow("Supplier:", self.supplier)
        
        self.cost = QLineEdit(str(self.equipment_data.get('cost', '')) if self.equipment_data and self.equipment_data.get('cost') else '')
        layout.addRow("Cost:", self.cost)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_data(self):
        data = {
            'asset_no': self.asset_no.text(),
            'serial_no': self.serial_no.text(),
            'product_name': self.product_name.text(),
            'category': self.category.currentText(),
            'status': self.status.currentText(),
            'location': self.location.text(),
            'supplier': self.supplier.text()
        }
        
        if self.cost.text():
            try:
                data['cost'] = float(self.cost.text())
            except ValueError:
                pass
        
        return data


class SpecificationDialog(QDialog):
    """Dialog for adding/editing equipment specifications"""
    
    def __init__(self, parent=None, spec_data=None):
        super().__init__(parent)
        self.spec_data = spec_data
        self.setWindowTitle("Equipment Specifications")
        self.setMinimumWidth(600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.processor = QLineEdit(self.spec_data.get('processor', '') if self.spec_data else '')
        self.processor.setPlaceholderText("e.g., Intel Core i7-11700K @ 3.6GHz")
        layout.addRow("Processor:", self.processor)
        
        self.ram = QLineEdit(self.spec_data.get('ram', '') if self.spec_data else '')
        self.ram.setPlaceholderText("e.g., 32GB DDR4 3200MHz")
        layout.addRow("RAM:", self.ram)
        
        self.storage = QLineEdit(self.spec_data.get('storage', '') if self.spec_data else '')
        self.storage.setPlaceholderText("e.g., 1TB NVMe SSD + 2TB HDD")
        layout.addRow("Storage:", self.storage)
        
        self.graphics = QLineEdit(self.spec_data.get('graphics', '') if self.spec_data else '')
        self.graphics.setPlaceholderText("e.g., NVIDIA RTX 3060 Ti 8GB")
        layout.addRow("Graphics:", self.graphics)
        
        self.os = QLineEdit(self.spec_data.get('os', '') if self.spec_data else '')
        self.os.setPlaceholderText("e.g., Windows 11 Pro")
        layout.addRow("Operating System:", self.os)
        
        self.network = QLineEdit(self.spec_data.get('network', '') if self.spec_data else '')
        self.network.setPlaceholderText("e.g., Gigabit Ethernet + WiFi 6")
        layout.addRow("Network:", self.network)
        
        self.additional_specs = QTextEdit()
        if self.spec_data and self.spec_data.get('additional_specs'):
            self.additional_specs.setPlainText(self.spec_data['additional_specs'])
        self.additional_specs.setPlaceholderText("Any additional specifications, notes, or details")
        self.additional_specs.setMaximumHeight(150)
        layout.addRow("Additional Info:", self.additional_specs)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'processor': self.processor.text(),
            'ram': self.ram.text(),
            'storage': self.storage.text(),
            'graphics': self.graphics.text(),
            'os': self.os.text(),
            'network': self.network.text(),
            'additional_specs': self.additional_specs.toPlainText()
        }


class WorkLogDialog(QDialog):
    """Dialog for creating work logs"""
    
    def __init__(self, parent=None, equipment_id=None):
        super().__init__(parent)
        self.equipment_id = equipment_id
        self.setWindowTitle("Create Work Log")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.job_name = QLineEdit()
        self.job_name.setPlaceholderText("e.g., Software Development - Project X")
        layout.addRow("Job/Project Name:", self.job_name)
        
        self.assigned_to = QLineEdit()
        self.assigned_to.setPlaceholderText("e.g., John Doe")
        layout.addRow("Assigned To:", self.assigned_to)
        
        self.department = QLineEdit()
        self.department.setPlaceholderText("e.g., Engineering")
        layout.addRow("Department:", self.department)
        
        self.check_out_date = QDateEdit()
        self.check_out_date.setDate(QDate.currentDate())
        self.check_out_date.setCalendarPopup(True)
        layout.addRow("Check Out Date:", self.check_out_date)
        
        self.expected_return = QDateEdit()
        self.expected_return.setCalendarPopup(True)
        self.expected_return.setSpecialValueText("Not Set")
        self.expected_return.setDate(QDate(2000, 1, 1))
        self.expected_return.setMinimumDate(QDate(2000, 1, 1))
        layout.addRow("Expected Return:", self.expected_return)
        
        self.status = QComboBox()
        self.status.addItems(['In Progress', 'Completed', 'On Hold'])
        layout.addRow("Status:", self.status)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Any additional notes or comments")
        layout.addRow("Notes:", self.notes)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_data(self):
        data = {
            'equipment_id': self.equipment_id,
            'job_name': self.job_name.text(),
            'assigned_to': self.assigned_to.text(),
            'department': self.department.text(),
            'check_out_date': self.check_out_date.date().toString(Qt.DateFormat.ISODate),
            'current_status': self.status.currentText(),
            'notes': self.notes.toPlainText()
        }
        
        # Only include expected return date if user explicitly set it
        return_date = self.expected_return.date()
        if return_date > QDate(2000, 1, 1):
            data['expected_return_date'] = return_date.toString(Qt.DateFormat.ISODate)
        
        return data


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.current_equipment = []
        self.current_import_list = []
        self.current_category_filter = None  # Track current category for overview
        self.all_worklogs = []  # Cache worklogs for inventory tab
        
        self.setWindowTitle("IT Asset Inventory Management System")
        self.setGeometry(100, 100, 1400, 800)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Main tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_overview_tab(), "📊 Overview")
        self.tabs.addTab(self.create_inventory_tab(), "📦 Inventory")
        self.tabs.addTab(self.create_active_worklog_tab(), "📋 Active Work Logs")
        self.tabs.addTab(self.create_past_worklog_tab(), "🕐 Past Work Logs")
        self.tabs.addTab(self.create_imports_tab(), "📂 Import History")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle ESC key press to reset overview to all categories"""
        if event.key() == Qt.Key.Key_Escape:
            if self.tabs.currentIndex() == 0:  # Overview tab
                self.current_category_filter = None
                self.load_overview_stats()
                self.statusBar().showMessage("Showing overall statistics")
        super().keyPressEvent(event)
    
    def create_header(self):
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QHBoxLayout()
        
        title = QLabel("IT Asset Management System")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        header.setLayout(layout)
        return header
    
    def create_modern_stat_card(self, title, value, color1, color2, icon):
        """Create modern stat card with gradient background"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 {color1}, stop:1 {color2});
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            QFrame:hover {{
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title row
        title_label = QLabel(title.upper())
        title_label.setStyleSheet("""
            font-size: 10px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 600;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Value and icon row
        value_layout = QHBoxLayout()
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        value_layout.addWidget(value_label)
        
        value_layout.addStretch()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 32px;
            color: rgba(255, 255, 255, 0.6);
            background: transparent;
        """)
        value_layout.addWidget(icon_label)
        
        layout.addLayout(value_layout)
        layout.addStretch()
        
        card.setLayout(layout)
        return card

    def create_overview_tab(self):
        """Redesigned aesthetic overview tab with horizontal bar chart"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QGroupBox {
                border: none;
                border-radius: 12px;
                margin-top: 15px;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #2d2d2d, stop:1 #242424);
                font-weight: 600;
                font-size: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 8px 15px;
                background-color: transparent;
                color: #ffffff;
                font-size: 16px;
            }
            QLabel {
                color: #e8e8e8;
            }
            QTableWidget {
                background-color: #242424;
                alternate-background-color: #2a2a2a;
                color: #ffffff;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                selection-background-color: #5B9BD5;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTableWidget::item:hover {
                background-color: #323232;
            }
            QTableWidget::item:selected {
                background-color: #5B9BD5;
                color: white;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3d3d3d, stop:1 #343434);
                color: #ffffff;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #5B9BD5;
                font-weight: 600;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background-color: #454545;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 20, 30, 20)
        
        # ============ HEADER SECTION ============
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #2d5f8d, stop:1 #1a3a5c);
                border-radius: 12px;
                padding: 12px 20px;
            }
        """)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        # Title
        title_label = QLabel("Fugro's Inventory System")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 300;
            color: #ffffff;
            padding: 2px 0;
            background: transparent;
        """)
        header_layout.addWidget(title_label)
        
        # Subtitle/Info
        info_label = QLabel("Monitor your IT assets at a glance  •  Click category to filter  •  Press ESC to reset")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            color: #b8d4f1;
            font-style: italic;
            font-size: 11px;
            background: transparent;
        """)
        header_layout.addWidget(info_label)
        
        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)
        
        # ============ STAT CARDS ROW ============
        stats_card_layout = QHBoxLayout()
        stats_card_layout.setSpacing(20)
        
        # Create modern stat cards with gradients
        self.total_card = self.create_modern_stat_card("Total Assets", "0", "#5B9BD5", "#4A8AC4", "🏢")
        self.available_card = self.create_modern_stat_card("Available", "0", "#70AD47", "#5A9037", "✓")
        self.in_service_card = self.create_modern_stat_card("In Service", "0", "#5B9BD5", "#4A8AC4", "⚙")
        self.faulty_card = self.create_modern_stat_card("Faulty", "0", "#ED7D31", "#D46D21", "⚠")
        self.retired_card = self.create_modern_stat_card("Retired", "0", "#A5A5A5", "#8A8A8A", "📴")
        
        stats_card_layout.addWidget(self.total_card)
        stats_card_layout.addWidget(self.available_card)
        stats_card_layout.addWidget(self.in_service_card)
        stats_card_layout.addWidget(self.faulty_card)
        stats_card_layout.addWidget(self.retired_card)
        
        main_layout.addLayout(stats_card_layout)
        
        # ============ BAR CHART SECTION ============
        chart_group = QGroupBox()
        chart_group.setStyleSheet("""
            QGroupBox {
                border: none;
                border-radius: 12px;
                margin-top: 0px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #2d2d2d, stop:1 #242424);
                font-weight: 700;
                font-size: 16px;
            }
        """)
        chart_layout = QVBoxLayout()
        chart_layout.setContentsMargins(15, 10, 15, 15)
        chart_layout.setSpacing(10)
        
        # Add title inside the card
        chart_title = QLabel("Device Status Distribution")
        chart_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 0px 0px 5px 0px;
            background: transparent;
        """)
        chart_layout.addWidget(chart_title)
        
        self.bar_chart = BarChartWidget()
        self.bar_chart.setMinimumHeight(130)
        self.bar_chart.setMaximumHeight(150)
        self.bar_chart.setStyleSheet("background: transparent; border: none;")
        chart_layout.addWidget(self.bar_chart)
        
        chart_group.setLayout(chart_layout)
        main_layout.addWidget(chart_group)
        
        # ============ CATEGORY TABLE ============
        category_group = QGroupBox()
        category_group.setStyleSheet("""
            QGroupBox {
                border: none;
                border-radius: 12px;
                margin-top: 0px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #2d2d2d, stop:1 #242424);
                font-weight: 700;
                font-size: 16px;
            }
        """)
        category_layout = QVBoxLayout()
        category_layout.setContentsMargins(15, 10, 15, 15)
        
        # Add title inside the card
        category_title = QLabel("Equipment by Category")
        category_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 0px 0px 5px 0px;
            background: transparent;
        """)
        category_layout.addWidget(category_title)
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(6)
        self.category_table.setHorizontalHeaderLabels([
            'Category', 'Total', 'Available', 'In Service', 'Faulty', 'Retired'
        ])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.category_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setShowGrid(False)
        self.category_table.setMinimumHeight(280)
        self.category_table.doubleClicked.connect(self.show_category_details)
        self.category_table.clicked.connect(self.filter_overview_by_category)
        
        category_layout.addWidget(self.category_table)
        category_group.setLayout(category_layout)
        main_layout.addWidget(category_group)
        
        # Add stretch at bottom
        main_layout.addStretch()
        
        widget.setLayout(main_layout)
        return widget
        
    def filter_overview_by_category(self, index):
        """Filter overview statistics by selected category (Excel sheet name)"""
        sheet_name = self.category_table.item(index.row(), 0).text()
        self.current_category_filter = sheet_name
        self.load_overview_stats()
        self.statusBar().showMessage(f"Showing statistics for: {sheet_name} (Press ESC for overall view)")
    
    def create_inventory_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Asset No:"))
        self.asset_search = QLineEdit()
        self.asset_search.setPlaceholderText("Type to search (autocomplete enabled)...")
        self.asset_search.textChanged.connect(self.on_asset_search_changed)

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.asset_search.setCompleter(self.completer)

        filter_layout.addWidget(self.asset_search)

        filter_layout.addWidget(QLabel("Product:"))
        self.product_filter = QComboBox()
        self.product_filter.setMinimumWidth(200)
        self.product_filter.setMaxVisibleItems(20)
        self.product_filter.addItem("All")
        self.product_filter.currentTextChanged.connect(self.filter_equipment)
        filter_layout.addWidget(self.product_filter)

        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(180)
        self.category_filter.addItem("All")
        self.category_filter.currentTextChanged.connect(self.filter_equipment)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All")
        self.status_filter.addItems(['Available', 'In Service', 'Faulty', 'Retired'])
        self.status_filter.currentTextChanged.connect(self.filter_equipment)
        filter_layout.addWidget(self.status_filter)

        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.filter_equipment)
        filter_layout.addWidget(search_btn)

        layout.addLayout(filter_layout)

        action_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Equipment")
        add_btn.clicked.connect(self.add_equipment)
        action_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_equipment)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_equipment)
        action_layout.addWidget(delete_btn)

        import_btn = QPushButton("📥 Import CSV/Excel")
        import_btn.clicked.connect(self.import_csv)
        action_layout.addWidget(import_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Inventory table with worklog notes column
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(9)
        self.equipment_table.setHorizontalHeaderLabels([
            'ID', 'Asset No', 'Serial No', 'Product Name', 'Category',
            'Status', 'Notes', 'Specification', 'Worklog Notes'
        ])

        self.equipment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.equipment_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.equipment_table.setSortingEnabled(True)

        layout.addWidget(self.equipment_table)
        self.equipment_table.itemChanged.connect(self._save_notes_spec)

        # Record count label at bottom
        self.record_count_label = QLabel("Total: 0 records")
        self.record_count_label.setStyleSheet("""
            color: #aaaaaa;
            font-size: 12px;
            padding: 4px 8px;
        """)
        layout.addWidget(self.record_count_label)

        widget.setLayout(layout)
        return widget
    
    def create_active_worklog_tab(self):
        """Active Work Logs - devices currently unavailable with reason"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("💡 Tip: You can edit notes directly in the Notes column. Changes are saved automatically.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        add_active_btn = QPushButton("➕ Change Device Status")
        add_active_btn.clicked.connect(self.change_device_status)
        action_layout.addWidget(add_active_btn)
        
        make_available_btn = QPushButton("✅ Make Available")
        make_available_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        make_available_btn.clicked.connect(self.make_device_available)
        action_layout.addWidget(make_available_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Active work logs table
        self.active_worklog_table = QTableWidget()
        self.active_worklog_table.setColumnCount(11)
        self.active_worklog_table.setHorizontalHeaderLabels([
            'ID', 'Asset No', 'Product', 'Status', 'Assigned To', 
            'Department', 'Designation', 'Check Out', 'Expected Return', 'Reason', 'Notes'
        ])
        self.active_worklog_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.active_worklog_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Connect signal for auto-saving notes
        self.active_worklog_table.itemChanged.connect(self._save_active_worklog_notes)
        
        layout.addWidget(self.active_worklog_table)
        
        widget.setLayout(layout)
        return widget
    
    def _save_active_worklog_notes(self, item):
        """Auto-save notes when edited in active worklog table"""
        if not item:
            return
        
        # Only process edits to the Notes column (column 10)
        if item.column() != 10:
            return
        
        # Check if we're actually in editing state
        if self.active_worklog_table.state() != QAbstractItemView.State.EditingState:
            return
        
        row = item.row()
        
        # Get worklog ID from the first column
        id_item = self.active_worklog_table.item(row, 0)
        if not id_item:
            return
        
        worklog_id = int(id_item.text())
        new_notes = item.text()
        
        # Update via API
        if self.api_client.update_worklog(worklog_id, {'notes': new_notes}):
            self.statusBar().showMessage(f"Notes saved for worklog ID {worklog_id}", 3000)
            # Refresh inventory table to show updated notes
            self.load_equipment()
        else:
            QMessageBox.warning(self, "Error", "Failed to save notes")
    
    def create_past_worklog_tab(self):
        """Past Work Logs - historical log of all device activities"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Asset:"))
        
        self.past_log_search = QLineEdit()
        self.past_log_search.setPlaceholderText("Search asset number...")
        self.past_log_search.textChanged.connect(self.filter_past_worklogs)
        filter_layout.addWidget(self.past_log_search)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Past work logs table
        self.past_worklog_table = QTableWidget()
        self.past_worklog_table.setColumnCount(11)
        self.past_worklog_table.setHorizontalHeaderLabels([
            'ID', 'Asset No', 'Product', 'Status', 'Assigned To', 
            'Department', 'Designation', 'Check Out', 'Check In', 'Duration (days)', 'Notes'
        ])
        self.past_worklog_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.past_worklog_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.past_worklog_table)
        
        widget.setLayout(layout)
        return widget

    def create_imports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        info = QLabel("CSV Import History - All imported files are preserved and can be viewed or deleted")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_import_history)
        button_layout.addWidget(refresh_btn)
        
        view_btn = QPushButton("👁️ View Details")
        view_btn.clicked.connect(self.view_import_details)
        button_layout.addWidget(view_btn)
        
        delete_import_btn = QPushButton("🗑️ Delete Import Record")
        delete_import_btn.clicked.connect(self.delete_import)
        button_layout.addWidget(delete_import_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Imports table
        self.imports_table = QTableWidget()
        self.imports_table.setColumnCount(6)
        self.imports_table.setHorizontalHeaderLabels([
            'ID', 'Filename', 'Import Date', 'Total Records', 
            'Successful', 'Failed'
        ])
        self.imports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.imports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.imports_table)
        
        widget.setLayout(layout)
        return widget
    
    def change_device_status(self):
        """
        Change Device Status dialog
        Supports:
        - typing full asset
        - typing prefix
        - typing last 4 digits (contains search)
        - instant dropdown suggestions
        """
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QTextEdit, QComboBox, QDateEdit, QPushButton, QMessageBox,
            QFormLayout, QCompleter
        )
        from PyQt6.QtCore import QDate, Qt

        dialog = QDialog(self)
        dialog.setWindowTitle("Change Device Status")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout()
        form = QFormLayout()

        # SMART AUTOFILL (MATCHES LAST DIGITS / CONTAINS)
        asset_input = QLineEdit()
        asset_input.setPlaceholderText("Type last 4 digits or asset number...")

        model = QStringListModel()
        completer = QCompleter()
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        asset_input.setCompleter(completer)

        def update_asset_autocomplete(text):
            text = text.strip().lower()

            if len(text) < 2:
                model.setStringList([])
                return

            suggestions = []

            # FAST: local cache search
            for eq in self.current_equipment:
                asset = eq.get("asset_no", "").lower()
                if text in asset:
                    suggestions.append(eq.get("asset_no"))

            suggestions = suggestions[:15]

            # If few results, ask server
            if len(suggestions) < 5:
                results = self.api_client.search_equipment_autocomplete(text)
                for r in results:
                    if r["asset_no"] not in suggestions:
                        suggestions.append(r["asset_no"])

            model.setStringList(suggestions)

        asset_input.textChanged.connect(update_asset_autocomplete)

        def on_selected(text):
            for eq in self.current_equipment:
                if eq.get("asset_no") == text:
                    assigned_to.setText(eq.get("location", ""))
                    break

        completer.activated.connect(on_selected)

        form.addRow("Asset Number:", asset_input)

        # Status selection
        status_combo = QComboBox()
        status_combo.addItems(['In Service', 'Faulty', 'Retired'])
        form.addRow("New Status:", status_combo)

        conditional_widget = QWidget()
        conditional_layout = QVBoxLayout()
        conditional_widget.setLayout(conditional_layout)

        # In Service fields
        in_service_widget = QWidget()
        in_service_form = QFormLayout()

        assigned_to = QLineEdit()
        department = QLineEdit()
        designation = QLineEdit()

        checkout_date = QDateEdit()
        checkout_date.setDate(QDate.currentDate())
        checkout_date.setCalendarPopup(True)

        expected_return = QDateEdit()
        expected_return.setCalendarPopup(True)
        expected_return.setSpecialValueText("Not Set")
        expected_return.setDate(QDate(2000, 1, 1))  # Set to minimum date
        expected_return.setMinimumDate(QDate(2000, 1, 1))
        expected_return.clearButtonEnabled = True

        in_service_form.addRow("Assigned To:", assigned_to)
        in_service_form.addRow("Department:", department)
        in_service_form.addRow("Designation:", designation)
        in_service_form.addRow("Check Out Date:", checkout_date)
        in_service_form.addRow("Expected Return:", expected_return)
        in_service_widget.setLayout(in_service_form)

        # Reason fields
        reason_widget = QWidget()
        reason_layout = QFormLayout()

        reason_text = QTextEdit()
        reason_text.setPlaceholderText("Enter reason for status change...")
        reason_text.setMaximumHeight(100)

        reason_layout.addRow("Reason:", reason_text)
        reason_widget.setLayout(reason_layout)

        conditional_layout.addWidget(in_service_widget)
        conditional_layout.addWidget(reason_widget)

        def update_conditional_fields():
            status = status_combo.currentText()
            in_service_widget.setVisible(status == 'In Service')
            reason_widget.setVisible(status in ['Faulty', 'Retired'])

        status_combo.currentTextChanged.connect(update_conditional_fields)
        update_conditional_fields()

        layout.addLayout(form)
        layout.addWidget(conditional_widget)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        def save_status():
            asset_no = asset_input.text().strip()
            if not asset_no:
                QMessageBox.warning(dialog, "Error", "Please enter asset number")
                return

            equipment = None
            for eq in self.current_equipment:
                if eq.get('asset_no') == asset_no:
                    equipment = eq
                    break

            if not equipment:
                QMessageBox.warning(dialog, "Error", f"Asset {asset_no} not found")
                return

            status = status_combo.currentText()

            # Create worklog with empty notes (user can add later)
            worklog_data = {
                'equipment_id': equipment['id'],
                'job_name': f'{status} - {asset_no}',
                'current_status': 'In Progress',
                'check_out_date': QDate.currentDate().toString('yyyy-MM-dd') + 'T00:00:00',
                'notes': ''  # Always start empty - user adds notes in the table
            }

            if status == 'In Service':
                worklog_data['assigned_to'] = assigned_to.text().strip()
                worklog_data['department'] = department.text().strip()
                worklog_data['designation'] = designation.text().strip()
                worklog_data['check_out_date'] = checkout_date.date().toString('yyyy-MM-dd') + 'T00:00:00'
                
                # Only include expected return date if user explicitly set it
                return_date = expected_return.date()
                if return_date > QDate(2000, 1, 1):
                    worklog_data['expected_return_date'] = return_date.toString('yyyy-MM-dd') + 'T00:00:00'
            elif status in ['Faulty', 'Retired']:
                # For Faulty/Retired, we can optionally store the reason in notes if provided
                reason = reason_text.toPlainText().strip()
                if reason:
                    worklog_data['notes'] = reason

            if self.api_client.update_equipment(equipment['id'], {'status': status}):
                if self.api_client.create_worklog(worklog_data):
                    QMessageBox.information(dialog, "Success", f"Status changed to {status}")
                    dialog.accept()
                    self.load_data()
                else:
                    QMessageBox.warning(dialog, "Error", "Failed to create work log")
            else:
                QMessageBox.warning(dialog, "Error", "Failed to update status")

        save_btn.clicked.connect(save_status)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()
    
    def make_device_available(self):
        """Make selected device available and close work log"""
        current_row = self.active_worklog_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a work log")
            return
        
        worklog_id = int(self.active_worklog_table.item(current_row, 0).text())
        asset_no = self.active_worklog_table.item(current_row, 1).text()
        
        # Find equipment
        equipment = None
        for eq in self.current_equipment:
            if eq.get('asset_no') == asset_no:
                equipment = eq
                break
        
        if not equipment:
            QMessageBox.warning(self, "Error", f"Equipment {asset_no} not found")
            return
        
        # Update equipment status to Available
        if self.api_client.update_equipment(equipment['id'], {'status': 'Available'}):
            # Update work log status to Completed with actual return date
            from PyQt6.QtCore import QDate
            worklog_data = {
                'current_status': 'Completed',
                'actual_return_date': QDate.currentDate().toString('yyyy-MM-dd') + 'T00:00:00'
            }
            if self.api_client.update_worklog(worklog_id, worklog_data):
                QMessageBox.information(self, "Success", f"Device {asset_no} is now Available")
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to update work log")
        else:
            QMessageBox.warning(self, "Error", "Failed to update equipment status")
    
    def filter_past_worklogs(self):
        """Filter past work logs by asset number"""
        search = self.past_log_search.text().strip().lower()
        
        for row in range(self.past_worklog_table.rowCount()):
            asset_item = self.past_worklog_table.item(row, 1)
            if asset_item:
                asset_no = asset_item.text().lower()
                self.past_worklog_table.setRowHidden(row, search not in asset_no if search else False)

    def load_data(self):
        """Load all data from server"""
        self.load_import_history()
        self.load_equipment()
        self.load_overview_stats()
        self.load_active_worklogs()
        self.load_past_worklogs()
        self.update_autocomplete()
    
    def load_equipment(self):
        """Load equipment list"""
        self.current_equipment = self.api_client.get_equipment()
        self.update_equipment_table(self.current_equipment)
        count = len(self.current_equipment)
        self.statusBar().showMessage(f"Showing all {count} record(s)")
    
    # Colours for each status value
    STATUS_COLORS = {
        'Available':  QColor(200, 255, 200),
        'In Service': QColor(255, 255, 180),
        'Faulty':     QColor(255, 200, 200),
        'Retired':    QColor(210, 210, 210),
    }

    def update_equipment_table(self, equipment_list):
        """Update equipment table with worklog notes"""
        self.equipment_table.setSortingEnabled(False)
        self.equipment_table.setRowCount(len(equipment_list))

        # Build import_id -> filename map
        import_names = {imp.get('id'): imp.get('filename', '') for imp in self.current_import_list}

        for row, equipment in enumerate(equipment_list):
            eq_id = equipment.get('id', '')
            status = equipment.get('status', 'Available')

            self.equipment_table.setItem(row, 0, QTableWidgetItem(str(eq_id)))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(equipment.get('asset_no', '')))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(equipment.get('serial_no', '')))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(equipment.get('product_name', '')))

            # CATEGORY - show Excel filename if available, otherwise show category
            csv_import_id = equipment.get('csv_import_id')
            if csv_import_id and csv_import_id in import_names and import_names[csv_import_id]:
                category_display = import_names[csv_import_id]
            else:
                category_display = equipment.get('category', '')
            self.equipment_table.setItem(row, 4, QTableWidgetItem(category_display))

            # STATUS
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(0, 0, 0))
            status_item.setBackground(self.STATUS_COLORS.get(status, QColor(255, 255, 255)))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.equipment_table.setItem(row, 5, status_item)

            # NOTES (mapped to backend LOCATION)
            notes_item = QTableWidgetItem(equipment.get('location', '') or '')
            self.equipment_table.setItem(row, 6, notes_item)

            # SPECIFICATION (mapped to backend SUPPLIER)
            spec_item = QTableWidgetItem(equipment.get('supplier', '') or '')
            self.equipment_table.setItem(row, 7, spec_item)
            
            # WORKLOG NOTES - Show actual user notes from active worklog
            worklog_notes = ""
            for log in self.all_worklogs:
                if log.get('equipment_id') == eq_id and log.get('current_status') == 'In Progress':
                    worklog_notes = log.get('notes', '') or ''
                    break
            
            worklog_notes_item = QTableWidgetItem(worklog_notes)
            worklog_notes_item.setFlags(worklog_notes_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            worklog_notes_item.setForeground(QColor(0, 0, 200))
            self.equipment_table.setItem(row, 8, worklog_notes_item)

        self.equipment_table.setSortingEnabled(True)

        # Update record count label
        total = len(equipment_list)
        self.record_count_label.setText(f"📋 Showing {total} record{'s' if total != 1 else ''}")

        # Refresh product name dropdown with unique product names from current list
        self.refresh_product_filter(equipment_list)

    def _save_notes_spec(self, item):
        if not item:
            return

        # only user edits
        if not self.equipment_table.state() == QAbstractItemView.State.EditingState:
            return

        row = item.row()
        col = item.column()

        if col not in (6, 7):
            return

        id_item = self.equipment_table.item(row, 0)
        notes_item = self.equipment_table.item(row, 6)
        spec_item = self.equipment_table.item(row, 7)

        if not id_item or not notes_item or not spec_item:
            return

        equipment_id = int(id_item.text())

        self.api_client.update_equipment(
            equipment_id,
            {
                "location": notes_item.text(),
                "supplier": spec_item.text()
            }
        )
    
    # REPLACE THIS METHOD IN YOUR MAIN FILE

    def load_overview_stats(self):
        """Load overview statistics with optional Excel sheet filter"""
        if self.current_category_filter:
            # Filter by Excel sheet name
            # First check if this is an import filename
            filter_import_id = None
            for imp in self.current_import_list:
                if imp.get('filename') == self.current_category_filter:
                    filter_import_id = imp.get('id')
                    break
            
            # Filter equipment
            if filter_import_id is not None:
                # Filter by csv_import_id
                filtered_equipment = [eq for eq in self.current_equipment 
                                    if eq.get('csv_import_id') == filter_import_id]
            else:
                # Fallback: filter by category (for equipment without csv_import_id)
                filtered_equipment = [eq for eq in self.current_equipment 
                                    if eq.get('category') == self.current_category_filter]
            
            total = len(filtered_equipment)
            available = sum(1 for eq in filtered_equipment if eq.get('status') == 'Available')
            in_service = sum(1 for eq in filtered_equipment if eq.get('status') == 'In Service')
            faulty = sum(1 for eq in filtered_equipment if eq.get('status') == 'Faulty')
            retired = sum(1 for eq in filtered_equipment if eq.get('status') == 'Retired')
            
            stats = {
                'total': total,
                'available': available,
                'in_service': in_service,
                'faulty': faulty,
                'retired': retired
            }
            
            chart_title = f"{self.current_category_filter}"
        else:
            # Overall statistics
            stats = self.api_client.get_overview_stats()
            chart_title = ""
        
        # Update stat cards with new values
        try:
            self.total_card.findChild(QLabel, "total_assets_value").setText(str(stats.get('total', 0)))
            self.available_card.findChild(QLabel, "available_value").setText(str(stats.get('available', 0)))
            self.in_service_card.findChild(QLabel, "in_service_value").setText(str(stats.get('in_service', 0)))
            self.faulty_card.findChild(QLabel, "faulty_value").setText(str(stats.get('faulty', 0)))
            self.retired_card.findChild(QLabel, "retired_value").setText(str(stats.get('retired', 0)))
        except AttributeError as e:
            print(f"Error updating stat cards: {e}")
        
        # Update bar chart
        self.bar_chart.update_chart(stats, chart_title)
        
        # Load stats grouped by import file (Excel sheet name)
        # Calculate stats from current equipment grouped by csv_import_id
        import_stats = {}
        import_names = {}  # Map csv_import_id to filename
        
        # First, create a map of csv_import_id to filename
        for imp in self.current_import_list:
            import_names[imp.get('id')] = imp.get('filename', 'Unknown')
        
        # Group equipment by csv_import_id and calculate stats
        for eq in self.current_equipment:
            csv_import_id = eq.get('csv_import_id')
            
            # Get the filename for this csv_import_id, or use category as fallback
            if csv_import_id is not None and csv_import_id in import_names:
                sheet_name = import_names[csv_import_id]
            else:
                # Fallback to category if csv_import_id is not set
                sheet_name = eq.get('category', 'Unknown')
            
            if sheet_name not in import_stats:
                import_stats[sheet_name] = {
                    'total': 0,
                    'available': 0,
                    'in_service': 0,
                    'faulty': 0,
                    'retired': 0
                }
            
            import_stats[sheet_name]['total'] += 1
            status = eq.get('status', '').lower()
            if status == 'available':
                import_stats[sheet_name]['available'] += 1
            elif status == 'in service':
                import_stats[sheet_name]['in_service'] += 1
            elif status == 'faulty':
                import_stats[sheet_name]['faulty'] += 1
            elif status == 'retired':
                import_stats[sheet_name]['retired'] += 1
        
        # Convert to list format
        stats_list = [{'sheet_name': k, **v} for k, v in import_stats.items()]
        
        self.category_table.setRowCount(len(stats_list))
        
        # Populate table with enhanced styling
        for row, item in enumerate(stats_list):
            # Sheet name (Excel filename)
            name_item = QTableWidgetItem(item.get('sheet_name', ''))
            name_item.setFont(QFont("", 10, QFont.Weight.Bold))
            self.category_table.setItem(row, 0, name_item)
            
            # Total
            total_item = QTableWidgetItem(str(item.get('total', 0)))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_table.setItem(row, 1, total_item)
            
            # Available (green if > 0)
            avail_val = item.get('available', 0)
            avail_item = QTableWidgetItem(str(avail_val))
            avail_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if avail_val > 0:
                avail_item.setForeground(QColor('#70AD47'))
            self.category_table.setItem(row, 2, avail_item)
            
            # In Service (blue if > 0)
            service_val = item.get('in_service', 0)
            service_item = QTableWidgetItem(str(service_val))
            service_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if service_val > 0:
                service_item.setForeground(QColor('#5B9BD5'))
            self.category_table.setItem(row, 3, service_item)
            
            # Faulty (orange if > 0)
            faulty_val = item.get('faulty', 0)
            faulty_item = QTableWidgetItem(str(faulty_val))
            faulty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if faulty_val > 0:
                faulty_item.setForeground(QColor('#ED7D31'))
            self.category_table.setItem(row, 4, faulty_item)
            
            # Retired (gray if > 0)
            retired_val = item.get('retired', 0)
            retired_item = QTableWidgetItem(str(retired_val))
            retired_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if retired_val > 0:
                retired_item.setForeground(QColor('#A5A5A5'))
            self.category_table.setItem(row, 5, retired_item)
        
        # Adjust row heights for better appearance
        for row in range(self.category_table.rowCount()):
            self.category_table.setRowHeight(row, 45)
        
    def load_active_worklogs(self):
        """Load active work logs (In Progress status only)"""
        self.all_worklogs = self.api_client.get_worklogs()
        active_logs = [log for log in self.all_worklogs if log.get('current_status') == 'In Progress']
        
        # Block signals while loading to prevent auto-save triggers
        self.active_worklog_table.blockSignals(True)
        self.active_worklog_table.setRowCount(len(active_logs))
        
        for row, log in enumerate(active_logs):
            equipment = next((e for e in self.current_equipment if e['id'] == log.get('equipment_id')), None)
            
            # ID (read-only)
            id_item = QTableWidgetItem(str(log.get('id', '')))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 0, id_item)
            
            # Asset No (read-only)
            asset_item = QTableWidgetItem(equipment.get('asset_no', '') if equipment else '')
            asset_item.setFlags(asset_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 1, asset_item)
            
            # Product (read-only)
            product_item = QTableWidgetItem(equipment.get('product_name', '') if equipment else '')
            product_item.setFlags(product_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 2, product_item)
            
            # Status (read-only)
            status_item = QTableWidgetItem(equipment.get('status', '') if equipment else '')
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 3, status_item)
            
            # Assigned To (read-only)
            assigned_item = QTableWidgetItem(log.get('assigned_to', '') or '')
            assigned_item.setFlags(assigned_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 4, assigned_item)
            
            # Department (read-only)
            dept_item = QTableWidgetItem(log.get('department', '') or '')
            dept_item.setFlags(dept_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 5, dept_item)
            
            # Designation (read-only)
            desig_item = QTableWidgetItem(log.get('designation', '') or '')
            desig_item.setFlags(desig_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 6, desig_item)
            
            # Check Out Date (read-only)
            checkout_item = QTableWidgetItem(log.get('check_out_date', '')[:10] if log.get('check_out_date') else '')
            checkout_item.setFlags(checkout_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 7, checkout_item)
            
            # Expected Return (read-only)
            return_item = QTableWidgetItem(log.get('expected_return_date', '')[:10] if log.get('expected_return_date') else '')
            return_item.setFlags(return_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.active_worklog_table.setItem(row, 8, return_item)
            
            # Reason (read-only) - AUTO-GENERATED from status and assignment
            reason_text = ""
            if equipment:
                status = equipment.get('status', '')
                assigned_to = log.get('assigned_to', '')
                
                if status == 'In Service' and assigned_to:
                    reason_text = f"In Service - Assigned to {assigned_to}"
                elif status == 'Faulty':
                    reason_text = "Device is Faulty"
                elif status == 'Retired':
                    reason_text = "Device is Retired"
                else:
                    reason_text = status
            
            reason_item = QTableWidgetItem(reason_text)
            reason_item.setFlags(reason_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            reason_item.setForeground(QColor(100, 100, 100))  # Gray text
            self.active_worklog_table.setItem(row, 9, reason_item)
            
            # Notes (EDITABLE) - Separate field, can be empty, user types here
            # This uses the 'notes' field from database
            notes_text = log.get('notes', '') or ''
            notes_item = QTableWidgetItem(notes_text)
            notes_item.setForeground(QColor(0, 100, 200))  # Blue text to indicate editable
            self.active_worklog_table.setItem(row, 10, notes_item)
        
        # Re-enable signals after loading
        self.active_worklog_table.blockSignals(False)
    
    def load_past_worklogs(self):
        """Load past work logs (Completed status only)"""
        from datetime import datetime
        
        all_worklogs = self.api_client.get_worklogs()
        past_logs = [log for log in all_worklogs if log.get('current_status') == 'Completed']
        
        self.past_worklog_table.setRowCount(len(past_logs))
        
        for row, log in enumerate(past_logs):
            equipment = next((e for e in self.current_equipment if e['id'] == log.get('equipment_id')), None)
            
            # Calculate duration
            checkout = log.get('check_out_date', '')
            checkin = log.get('actual_return_date', '')
            duration = ''
            if checkout and checkin:
                try:
                    d1 = datetime.strptime(checkout[:10], '%Y-%m-%d')
                    d2 = datetime.strptime(checkin[:10], '%Y-%m-%d')
                    duration = str((d2 - d1).days)
                except:
                    pass
            
            self.past_worklog_table.setItem(row, 0, QTableWidgetItem(str(log.get('id', ''))))
            self.past_worklog_table.setItem(row, 1, QTableWidgetItem(equipment.get('asset_no', '') if equipment else ''))
            self.past_worklog_table.setItem(row, 2, QTableWidgetItem(equipment.get('product_name', '') if equipment else ''))
            self.past_worklog_table.setItem(row, 3, QTableWidgetItem(equipment.get('status', '') if equipment else ''))
            self.past_worklog_table.setItem(row, 4, QTableWidgetItem(log.get('assigned_to', '') or ''))
            self.past_worklog_table.setItem(row, 5, QTableWidgetItem(log.get('department', '') or ''))
            self.past_worklog_table.setItem(row, 6, QTableWidgetItem(log.get('designation', '') or ''))
            self.past_worklog_table.setItem(row, 7, QTableWidgetItem(checkout[:10] if checkout else ''))
            self.past_worklog_table.setItem(row, 8, QTableWidgetItem(checkin[:10] if checkin else ''))
            self.past_worklog_table.setItem(row, 9, QTableWidgetItem(duration))
            
            # Show actual user notes (can be empty)
            self.past_worklog_table.setItem(row, 10, QTableWidgetItem(log.get('notes', '') or ''))

    def load_import_history(self):
        """Load CSV import history and refresh category filter dropdown."""
        self.current_import_list = self.api_client.get_imports()
        self.imports_table.setRowCount(len(self.current_import_list))

        for row, import_record in enumerate(self.current_import_list):
            self.imports_table.setItem(row, 0, QTableWidgetItem(str(import_record.get('id', ''))))
            self.imports_table.setItem(row, 1, QTableWidgetItem(import_record.get('filename', '')))

            import_date = import_record.get('import_date', '')
            if import_date:
                import_date = import_date[:19].replace('T', ' ')
            self.imports_table.setItem(row, 2, QTableWidgetItem(import_date))

            self.imports_table.setItem(row, 3, QTableWidgetItem(str(import_record.get('total_records', 0))))
            self.imports_table.setItem(row, 4, QTableWidgetItem(str(import_record.get('successful_records', 0))))
            self.imports_table.setItem(row, 5, QTableWidgetItem(str(import_record.get('failed_records', 0))))

        self.refresh_category_filter()
    
    def refresh_category_filter(self):
        """Populate Category dropdown with import filenames"""
        imports = self.current_import_list
        seen = set()
        filenames = []
        for imp in imports:
            fn = imp.get('filename', '').strip()
            if fn and fn not in seen:
                seen.add(fn)
                filenames.append(fn)

        self.category_filter.blockSignals(True)
        try:
            current = self.category_filter.currentText()
            self.category_filter.clear()
            self.category_filter.addItem("All")
            self.category_filter.addItems(filenames)
            idx = self.category_filter.findText(current)
            self.category_filter.setCurrentIndex(idx if idx >= 0 else 0)
        finally:
            self.category_filter.blockSignals(False)

    def refresh_product_filter(self, equipment_list):
        """Populate Product dropdown with unique product names from current equipment list"""
        seen = set()
        products = []
        for eq in equipment_list:
            name = eq.get('product_name', '').strip()
            if name and name not in seen:
                seen.add(name)
                products.append(name)
        products.sort()

        self.product_filter.blockSignals(True)
        try:
            current = self.product_filter.currentText()
            self.product_filter.clear()
            self.product_filter.addItem("All")
            self.product_filter.addItems(products)
            idx = self.product_filter.findText(current)
            self.product_filter.setCurrentIndex(idx if idx >= 0 else 0)
        finally:
            self.product_filter.blockSignals(False)

    def update_autocomplete(self):
        """Update autocomplete suggestions"""
        asset_numbers = [e.get('asset_no', '') for e in self.current_equipment if e.get('asset_no')]
        
        model = QStringListModel()
        model.setStringList(asset_numbers)
        
        self.completer.setModel(model)
    
    def on_asset_search_changed(self, text):
        """Handle asset search text changes for autocomplete"""
        if len(text) >= 2:
            results = self.api_client.search_equipment_autocomplete(text)
            suggestions = [r.get('asset_no', '') for r in results]
            
            model = QStringListModel()
            model.setStringList(suggestions)
            self.completer.setModel(model)
    
    def filter_equipment(self):
        """Filter table by import filename + product name + status + search."""
        filename   = self.category_filter.currentText().strip()
        product    = self.product_filter.currentText().strip()
        status     = self.status_filter.currentText()
        search     = self.asset_search.text().strip()

        import_id = None

        if filename and filename != "All":
            for imp in self.current_import_list:
                stored = (imp.get("filename") or "").strip()
                if stored.lower() == filename.lower():
                    import_id = imp.get("id")
                    break

            if import_id is None:
                self.update_equipment_table([])
                self.statusBar().showMessage(
                    f"No import found matching '{filename}' — try refreshing (Ctrl+R)"
                )
                return

        status_val = None if status == "All" else status

        data = self.api_client.get_equipment(
            import_id=import_id,
            status=status_val,
            search=search if search else None
        )

        # Apply product name filter client-side
        if product and product != "All":
            data = [eq for eq in data if eq.get('product_name', '').strip() == product]

        if import_id is None and not search and status_val is None and (not product or product == "All"):
            self.current_equipment = data
            self.update_autocomplete()

        count = len(data)
        filters_active = []
        if filename and filename != "All":
            filters_active.append(f"Category: {filename}")
        if product and product != "All":
            filters_active.append(f"Product: {product}")
        if status_val:
            filters_active.append(f"Status: {status_val}")
        if search:
            filters_active.append(f"Search: '{search}'")

        if filters_active:
            self.statusBar().showMessage(f"Filtered: {count} record(s)  |  " + "  |  ".join(filters_active))
        else:
            self.statusBar().showMessage(f"Showing all {count} record(s)")

        self.update_equipment_table(data)
    
    def add_equipment(self):
        """Add new equipment"""
        dialog = EquipmentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.api_client.create_equipment(data):
                QMessageBox.information(self, "Success", "Equipment added successfully")
                self.load_equipment()
                self.load_overview_stats()
            else:
                QMessageBox.critical(self, "Error", "Failed to add equipment")
    
    def edit_equipment(self):
        """Edit selected equipment"""
        current_row = self.equipment_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select equipment to edit")
            return
        
        equipment_id = int(self.equipment_table.item(current_row, 0).text())
        equipment = next((e for e in self.current_equipment if e['id'] == equipment_id), None)
        
        if not equipment:
            return
        
        dialog = EquipmentDialog(self, equipment)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.api_client.update_equipment(equipment_id, data):
                QMessageBox.information(self, "Success", "Equipment updated successfully")
                self.load_equipment()
                self.load_overview_stats()
            else:
                QMessageBox.critical(self, "Error", "Failed to update equipment")
    
    def delete_equipment(self):
        """Delete selected equipment"""
        current_row = self.equipment_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select equipment to delete")
            return
        
        equipment_id = int(self.equipment_table.item(current_row, 0).text())
        asset_no = self.equipment_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f'Are you sure you want to delete equipment {asset_no}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.api_client.delete_equipment(equipment_id):
                QMessageBox.information(self, "Success", "Equipment deleted successfully")
                self.load_equipment()
                self.load_overview_stats()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete equipment")
    
    def import_csv(self):
        """Import CSV/Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV or Excel File",
            "",
            "Data Files (*.csv *.xlsx *.xls)"
        )

        if file_path:
            result = self.api_client.upload_csv(file_path)
            if result and "error" not in result:
                msg = f"Import completed!\n\nTotal Records: {result['total_records']}\n"
                msg += f"Successful: {result['successful']}\n"
                msg += f"Failed: {result['failed']}"

                if result.get('errors'):
                    msg += f"\n\nFirst few errors:\n" + "\n".join(result['errors'])

                QMessageBox.information(self, "Import Complete", msg)
                self.load_equipment()
                self.load_overview_stats()
                self.load_import_history()
            else:
                err_msg = result.get("error", "Unknown error") if result else "No response from server. Is the backend running?"
                QMessageBox.critical(self, "Import Failed", f"Failed to import file:\n\n{err_msg}")
    
    def show_category_details(self, index):
        """Show detailed equipment list for selected Excel sheet"""
        sheet_name = self.category_table.item(index.row(), 0).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Equipment Details - {sheet_name}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Find the import_id for this sheet name
        import_id = None
        for imp in self.current_import_list:
            if imp.get('filename') == sheet_name:
                import_id = imp.get('id')
                break
        
        # Filter equipment and group by product name
        product_stats = {}
        for eq in self.current_equipment:
            # Check if this equipment belongs to this sheet
            eq_csv_import_id = eq.get('csv_import_id')
            eq_category = eq.get('category', '')
            
            # Match by csv_import_id if available, otherwise match by category
            is_match = False
            if import_id is not None and eq_csv_import_id == import_id:
                is_match = True
            elif import_id is None and eq_category == sheet_name:
                is_match = True
            
            if is_match:
                product_name = eq.get('product_name', 'Unknown')
                
                if product_name not in product_stats:
                    product_stats[product_name] = {
                        'total': 0,
                        'available': 0,
                        'in_service': 0,
                        'faulty': 0,
                        'retired': 0
                    }
                
                product_stats[product_name]['total'] += 1
                status = eq.get('status', '').lower()
                if status == 'available':
                    product_stats[product_name]['available'] += 1
                elif status == 'in service':
                    product_stats[product_name]['in_service'] += 1
                elif status == 'faulty':
                    product_stats[product_name]['faulty'] += 1
                elif status == 'retired':
                    product_stats[product_name]['retired'] += 1
        
        # Convert to list
        equipment_stats = [{'product_name': k, **v} for k, v in product_stats.items()]
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            'Product Name', 'Total', 'Available', 'In Service', 'Faulty', 'Retired'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        table.setRowCount(len(equipment_stats))
        for row, item in enumerate(equipment_stats):
            table.setItem(row, 0, QTableWidgetItem(item.get('product_name', '')))
            table.setItem(row, 1, QTableWidgetItem(str(item.get('total', 0))))
            table.setItem(row, 2, QTableWidgetItem(str(item.get('available', 0))))
            table.setItem(row, 3, QTableWidgetItem(str(item.get('in_service', 0))))
            table.setItem(row, 4, QTableWidgetItem(str(item.get('faulty', 0))))
            table.setItem(row, 5, QTableWidgetItem(str(item.get('retired', 0))))
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def view_import_details(self):
        """View details of selected import"""
        current_row = self.imports_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an import to view")
            return
        
        import_id = int(self.imports_table.item(current_row, 0).text())
        details = self.api_client.get_import_details(import_id)
        
        if not details:
            QMessageBox.critical(self, "Error", "Failed to load import details")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Details")
        dialog.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout()
        
        info_text = f"Filename: {details['import_info']['filename']}\n"
        info_text += f"Import Date: {details['import_info']['import_date']}\n"
        info_text += f"Total Records: {details['import_info']['total_records']}\n"
        info_text += f"Successful: {details['import_info']['successful_records']}\n"
        info_text += f"Failed: {details['import_info']['failed_records']}"
        
        info_label = QLabel(info_text)
        layout.addWidget(info_label)
        
        layout.addWidget(QLabel(f"\nEquipment imported ({details['equipment_count']} items):"))
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Asset No', 'Serial No', 'Product Name', 'Category', 'Status'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        equipment = details['equipment']
        table.setRowCount(len(equipment))
        
        for row, item in enumerate(equipment):
            table.setItem(row, 0, QTableWidgetItem(item.get('asset_no', '')))
            table.setItem(row, 1, QTableWidgetItem(item.get('serial_no', '')))
            table.setItem(row, 2, QTableWidgetItem(item.get('product_name', '')))
            table.setItem(row, 3, QTableWidgetItem(item.get('category', '')))
            table.setItem(row, 4, QTableWidgetItem(item.get('status', '')))
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_import(self):
        """Delete selected import record"""
        current_row = self.imports_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an import to delete")
            return
        
        import_id = int(self.imports_table.item(current_row, 0).text())
        filename = self.imports_table.item(current_row, 1).text()
        
        msg = QMessageBox()
        msg.setWindowTitle("Delete Import")
        msg.setText(f"Delete import record for '{filename}'?")
        msg.setInformativeText("Do you also want to delete all equipment imported from this file?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        msg.button(QMessageBox.StandardButton.Yes).setText("Delete Record & Equipment")
        msg.button(QMessageBox.StandardButton.No).setText("Delete Record Only")
        
        result = msg.exec()
        
        if result == QMessageBox.StandardButton.Cancel:
            return
        
        delete_equipment = result == QMessageBox.StandardButton.Yes
        
        if self.api_client.delete_import(import_id, delete_equipment):
            QMessageBox.information(self, "Success", "Import record deleted successfully")
            self.load_import_history()
            if delete_equipment:
                self.load_equipment()
                self.load_overview_stats()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete import record")


def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    api_client = APIClient()
    
    login_dialog = LoginDialog(api_client)
    if login_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
    
    window = MainWindow(api_client)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()