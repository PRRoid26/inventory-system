"""
IT Asset Inventory Management System — Mobile Qt6 Client
Mobile-optimised PyQt6 frontend for phones/tablets.

Design principles:
  - Bottom navigation bar (thumb-friendly)
  - Large touch targets (≥ 48 px height for every interactive element)
  - Card-based lists instead of dense tables
  - Full-screen / bottom-sheet dialogs
  - Readable font sizes (≥ 13 pt body, 16 pt headings)
  - Same APIClient / DataFetcher / WriteWorker as the desktop version
"""

import sys
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QScrollArea, QFrame, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QSizePolicy,
    QProgressBar, QListWidget, QListWidgetItem, QAbstractItemView,
    QCheckBox, QSpacerItem,
)
from PyQt6.QtCore import (
    Qt, QDate, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QIcon, QFont, QColor, QPalette, QFontMetrics, QPainter,
    QBrush, QPen, QPixmap,
)

# ──────────────────────────────────────────────────────────────
# API / BACKEND  (identical to desktop version)
# ──────────────────────────────────────────────────────────────

def _detect_api_url():
    local_url = "http://192.168.64.75:8000"
    cloud_url = "https://inventory-system-iaub.onrender.com"
    try:
        requests.get(local_url + "/", timeout=3)
        print("[API] Local NAS reachable — using local backend")
        return local_url, "local"
    except Exception:
        print("[API] Local NAS unreachable — using cloud backend")
        return cloud_url, "cloud"

API_BASE_URL, API_CONNECTION_TYPE = _detect_api_url()
REQUEST_TIMEOUT = 30


class DataFetcher(QThread):
    data_ready    = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

    def run(self):
        try:
            self.data_ready.emit({
                "imports":   self.api_client.get_imports(),
                "equipment": self.api_client.get_equipment(),
                "worklogs":  self.api_client.get_worklogs(),
                "overview":  self.api_client.get_overview_stats(),
            })
        except Exception as e:
            self.error_occurred.emit(str(e))


class WriteWorker(QThread):
    finished       = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.finished.emit(self.fn())
        except Exception as e:
            self.error_occurred.emit(str(e))


class APIClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token    = None
        self.headers  = {}

    def set_token(self, token: str):
        self.token   = token
        self.headers = {"Authorization": f"Bearer {token}"}

    def login(self, username: str, password: str) -> bool:
        try:
            r = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code == 200:
                self.set_token(r.json()["access_token"])
                return True
        except Exception as e:
            print(f"Login error: {e}")
        return False

    def register(self, username, email, password, full_name="") -> bool:
        try:
            r = requests.post(
                f"{self.base_url}/api/auth/register",
                json={"username": username, "email": email,
                      "password": password, "full_name": full_name},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code == 200:
                self.set_token(r.json()["access_token"])
                return True
        except Exception as e:
            print(f"Registration error: {e}")
        return False

    def get_equipment(self, category=None, status=None, search=None, import_id=None):
        try:
            all_items, skip, page_size = [], 0, 500
            while True:
                params = {"skip": skip, "limit": page_size}
                if category:   params["category"]   = category
                if import_id:  params["import_id"]  = import_id
                if status:     params["status"]      = status
                if search:     params["search"]      = search
                r = requests.get(f"{self.base_url}/api/equipment",
                                 headers=self.headers, params=params,
                                 timeout=REQUEST_TIMEOUT)
                if r.status_code != 200: break
                page = r.json()
                if not page: break
                all_items.extend(page)
                if len(page) < page_size: break
                skip += page_size
            return all_items
        except Exception as e:
            print(f"Get equipment error: {e}")
            return []

    def create_equipment(self, data: dict) -> bool:
        try:
            r = requests.post(f"{self.base_url}/api/equipment",
                              headers=self.headers, json=data,
                              timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Create equipment error: {e}")
            return False

    def update_equipment(self, equipment_id: int, data: dict) -> bool:
        try:
            r = requests.put(f"{self.base_url}/api/equipment/{equipment_id}",
                             headers=self.headers, json=data,
                             timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Update equipment error: {e}")
            return False

    def delete_equipment(self, equipment_id: int) -> bool:
        try:
            r = requests.delete(f"{self.base_url}/api/equipment/{equipment_id}",
                                headers=self.headers, timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Delete equipment error: {e}")
            return False

    def get_worklogs(self, equipment_id=None, status=None):
        try:
            params = {}
            if equipment_id: params["equipment_id"] = equipment_id
            if status:       params["status"]       = status
            r = requests.get(f"{self.base_url}/api/worklogs",
                             headers=self.headers, params=params,
                             timeout=REQUEST_TIMEOUT)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"Get worklogs error: {e}")
            return []

    def create_worklog(self, data: dict) -> bool:
        try:
            r = requests.post(f"{self.base_url}/api/worklogs",
                              headers=self.headers, json=data,
                              timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Create worklog error: {e}")
            return False

    def update_worklog(self, worklog_id: int, data: dict) -> bool:
        try:
            r = requests.put(f"{self.base_url}/api/worklogs/{worklog_id}",
                             headers=self.headers, json=data,
                             timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Update worklog error: {e}")
            return False

    def get_imports(self):
        try:
            r = requests.get(f"{self.base_url}/api/imports",
                             headers=self.headers, timeout=REQUEST_TIMEOUT)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"Get imports error: {e}")
            return []

    def get_overview_stats(self):
        try:
            r = requests.get(f"{self.base_url}/api/stats/overview",
                             headers=self.headers, timeout=REQUEST_TIMEOUT)
            return r.json() if r.status_code == 200 else {}
        except Exception as e:
            print(f"Get overview error: {e}")
            return {}

    def upload_csv(self, file_path: str):
        try:
            fname = Path(file_path).name
            ext   = Path(file_path).suffix.lower()
            mime_map = {
                ".csv":  "text/csv",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xls":  "application/vnd.ms-excel",
            }
            mime = mime_map.get(ext, "application/octet-stream")
            with open(file_path, "rb") as f:
                r = requests.post(
                    f"{self.base_url}/api/import/csv",
                    headers=self.headers,
                    files={"file": (fname, f, mime)},
                    timeout=REQUEST_TIMEOUT,
                )
                if r.status_code == 200:
                    return r.json()
                try:
                    return {"error": r.json().get("detail", r.text)}
                except Exception:
                    return {"error": r.text}
        except Exception as e:
            return {"error": str(e)}


# ──────────────────────────────────────────────────────────────
# STYLE CONSTANTS
# ──────────────────────────────────────────────────────────────

DARK_BG      = "#121212"
SURFACE      = "#1E1E1E"
SURFACE2     = "#2A2A2A"
ACCENT       = "#4FC3F7"       # light-blue
ACCENT2      = "#81C784"       # green
DANGER       = "#EF5350"
WARN         = "#FFB74D"
TEXT         = "#EEEEEE"
TEXT_SUB     = "#9E9E9E"
DIVIDER      = "#333333"

STATUS_COLORS = {
    "available":  "#81C784",
    "in service": "#4FC3F7",
    "faulty":     "#EF5350",
    "retired":    "#9E9E9E",
}

GLOBAL_STYLE = f"""
QWidget {{
    background-color: {DARK_BG};
    color: {TEXT};
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 13pt;
}}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
    background-color: {SURFACE2};
    color: {TEXT};
    border: 1px solid {DIVIDER};
    border-radius: 8px;
    padding: 10px 14px;
    min-height: 44px;
    font-size: 13pt;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1.5px solid {ACCENT};
}}
QComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE2};
    selection-background-color: {ACCENT};
    selection-color: {DARK_BG};
    border: 1px solid {DIVIDER};
}}
QPushButton {{
    background-color: {ACCENT};
    color: {DARK_BG};
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    min-height: 48px;
    font-size: 13pt;
    font-weight: bold;
}}
QPushButton:hover  {{ background-color: #81D4FA; }}
QPushButton:pressed {{ background-color: #0288D1; }}
QPushButton[flat="true"] {{
    background: transparent;
    color: {ACCENT};
    border: 1.5px solid {ACCENT};
}}
QPushButton[danger="true"] {{
    background-color: {DANGER};
    color: white;
}}
QPushButton[success="true"] {{
    background-color: {ACCENT2};
    color: {DARK_BG};
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {DIVIDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QLabel {{ background: transparent; }}
QMessageBox {{ background-color: {SURFACE}; }}
"""


# ──────────────────────────────────────────────────────────────
# REUSABLE WIDGETS
# ──────────────────────────────────────────────────────────────

class Card(QFrame):
    """A rounded surface card."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border-radius: 14px;
                border: 1px solid {DIVIDER};
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(8)

    def layout(self):
        return self._layout


class StatusBadge(QLabel):
    """Coloured pill badge for equipment/worklog status."""
    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        color = STATUS_COLORS.get(status.lower(), TEXT_SUB)
        self.setText(f"  {status.title()}  ")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}33;
                color: {color};
                border: 1px solid {color};
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        self.setFixedHeight(26)


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"border: none; border-top: 1px solid {DIVIDER};")
        self.setFixedHeight(1)


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        font = QFont()
        font.setPointSize(17)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(f"color: {TEXT}; background: transparent;")


class SubLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; background: transparent;")


class LoadingBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 0)   # indeterminate
        self.setTextVisible(False)
        self.setFixedHeight(4)
        self.setStyleSheet(f"""
            QProgressBar {{ background: {SURFACE2}; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {ACCENT}; border-radius: 2px; }}
        """)
        self.hide()


class TitleBar(QWidget):
    """Top title bar with optional back button and action button."""
    back_clicked   = pyqtSignal()
    action_clicked = pyqtSignal()

    def __init__(self, title: str, show_back=False, action_label="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(f"background-color: {SURFACE}; border-bottom: 1px solid {DIVIDER};")

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 0, 12, 0)

        if show_back:
            back_btn = QPushButton("‹")
            back_btn.setFixedSize(44, 44)
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {ACCENT};
                    font-size: 22pt;
                    font-weight: bold;
                    border: none;
                    padding: 0;
                }}
            """)
            back_btn.clicked.connect(self.back_clicked)
            h.addWidget(back_btn)
        else:
            h.addSpacing(4)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 16pt; font-weight: bold; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(lbl, stretch=1)

        if action_label:
            act_btn = QPushButton(action_label)
            act_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {ACCENT};
                    font-size: 13pt;
                    border: none;
                    padding: 0 8px;
                    min-height: 44px;
                }}
            """)
            act_btn.clicked.connect(self.action_clicked)
            h.addWidget(act_btn)
        else:
            h.addSpacing(44)


class BottomNavBar(QWidget):
    """Fixed bottom navigation bar."""
    page_changed = pyqtSignal(int)

    TABS = [
        ("📊", "Overview"),
        ("📦", "Inventory"),
        ("📋", "Active"),
        ("🕐", "History"),
        ("📂", "Imports"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-top: 1px solid {DIVIDER};
            }}
        """)
        self._buttons: List[QPushButton] = []
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        for i, (icon, label) in enumerate(self.TABS):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setCheckable(True)
            btn.setFixedHeight(64)
            btn.setStyleSheet(self._btn_style(False))
            btn.clicked.connect(lambda _, idx=i: self._on_click(idx))
            h.addWidget(btn)
            self._buttons.append(btn)

        self._buttons[0].setChecked(True)
        self._apply_style(0)

    def _btn_style(self, active: bool):
        color = ACCENT if active else TEXT_SUB
        bg    = f"{ACCENT}18" if active else "transparent"
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: none;
                font-size: 10pt;
                padding: 4px 0;
            }}
        """

    def _apply_style(self, idx: int):
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._btn_style(i == idx))

    def _on_click(self, idx: int):
        self._apply_style(idx)
        self.page_changed.emit(idx)

    def set_active(self, idx: int):
        self._apply_style(idx)


# ──────────────────────────────────────────────────────────────
# FULL-SCREEN DIALOGS (mobile-style)
# ──────────────────────────────────────────────────────────────

class MobileDialog(QDialog):
    """Base full-screen dialog with title bar."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = TitleBar(title, show_back=True, parent=self)
        self._title_bar.back_clicked.connect(self.reject)
        root.addWidget(self._title_bar)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content.setStyleSheet(f"background: {DARK_BG};")
        self._form = QVBoxLayout(self._content)
        self._form.setContentsMargins(16, 16, 16, 16)
        self._form.setSpacing(12)

        scroll.setWidget(self._content)
        root.addWidget(scroll, stretch=1)

        # Bottom action bar
        action_bar = QWidget()
        action_bar.setFixedHeight(72)
        action_bar.setStyleSheet(f"background: {SURFACE}; border-top: 1px solid {DIVIDER};")
        ab = QHBoxLayout(action_bar)
        ab.setContentsMargins(16, 12, 16, 12)
        ab.setSpacing(12)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setProperty("flat", True)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUB};
                border: 1.5px solid {DIVIDER};
                border-radius: 10px;
                font-size: 13pt;
                min-height: 48px;
            }}
        """)
        self._cancel_btn.clicked.connect(self.reject)

        self._save_btn = QPushButton("Save")
        self._save_btn.clicked.connect(self.accept)

        ab.addWidget(self._cancel_btn)
        ab.addWidget(self._save_btn)
        root.addWidget(action_bar)

    def add_field(self, label: str, widget: QWidget):
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; font-weight: bold;")
        self._form.addWidget(lbl)
        self._form.addWidget(widget)

    def add_stretch(self):
        self._form.addStretch()


class EquipmentDialog(MobileDialog):
    def __init__(self, parent=None, equipment_data=None):
        super().__init__("Edit Asset" if equipment_data else "Add Asset", parent)
        self.equipment_data = equipment_data or {}
        self._build()

    def _build(self):
        d = self.equipment_data

        self.asset_no = QLineEdit(d.get("asset_no", ""))
        self.asset_no.setPlaceholderText("Asset number")
        self.add_field("Asset No.", self.asset_no)

        self.serial_no = QLineEdit(d.get("serial_no", ""))
        self.serial_no.setPlaceholderText("Serial number")
        self.add_field("Serial No.", self.serial_no)

        self.product_name = QLineEdit(d.get("product_name", ""))
        self.product_name.setPlaceholderText("Product / model name")
        self.add_field("Product Name", self.product_name)

        self.category = QComboBox()
        cats = ["Computers", "Network Equipment", "Monitors", "Printers & Scanners",
                "Servers", "Mobile Devices", "Tablets", "Peripherals",
                "Power & UPS", "Cables & Adapters", "Other"]
        self.category.addItems(cats)
        if d.get("category"):
            idx = self.category.findText(d["category"])
            if idx >= 0: self.category.setCurrentIndex(idx)
        self.add_field("Category", self.category)

        self.status = QComboBox()
        self.status.addItems(["Available", "In Service", "Faulty", "Retired"])
        if d.get("status"):
            idx = self.status.findText(d["status"])
            if idx >= 0: self.status.setCurrentIndex(idx)
        self.add_field("Status", self.status)

        self.location = QLineEdit(d.get("location", ""))
        self.location.setPlaceholderText("Physical location")
        self.add_field("Location", self.location)

        self.supplier = QLineEdit(d.get("supplier", ""))
        self.supplier.setPlaceholderText("Supplier / vendor")
        self.add_field("Supplier", self.supplier)

        self.cost = QLineEdit(str(d.get("cost", "")) if d.get("cost") else "")
        self.cost.setPlaceholderText("0.00")
        self.add_field("Cost (₹)", self.cost)

        self.add_stretch()

    def get_data(self):
        data = {
            "asset_no":     self.asset_no.text(),
            "serial_no":    self.serial_no.text(),
            "product_name": self.product_name.text(),
            "category":     self.category.currentText(),
            "status":       self.status.currentText(),
            "location":     self.location.text(),
            "supplier":     self.supplier.text(),
        }
        if self.cost.text():
            try:
                data["cost"] = float(self.cost.text())
            except ValueError:
                pass
        return data


class WorkLogDialog(MobileDialog):
    def __init__(self, parent=None, equipment_id=None):
        super().__init__("New Work Log", parent)
        self.equipment_id = equipment_id
        self._build()

    def _build(self):
        self.job_name = QLineEdit()
        self.job_name.setPlaceholderText("e.g., Software Development – Project X")
        self.add_field("Job / Project Name", self.job_name)

        self.assigned_to = QLineEdit()
        self.assigned_to.setPlaceholderText("e.g., Rahul Sharma")
        self.add_field("Assigned To", self.assigned_to)

        self.department = QLineEdit()
        self.department.setPlaceholderText("e.g., Engineering")
        self.add_field("Department", self.department)

        self.check_out_date = QDateEdit()
        self.check_out_date.setDate(QDate.currentDate())
        self.check_out_date.setCalendarPopup(True)
        self.add_field("Check-out Date", self.check_out_date)

        self.expected_return = QDateEdit()
        self.expected_return.setDate(QDate(2000, 1, 1))
        self.expected_return.setMinimumDate(QDate(2000, 1, 1))
        self.expected_return.setSpecialValueText("Not Set")
        self.expected_return.setCalendarPopup(True)
        self.add_field("Expected Return", self.expected_return)

        self.wl_status = QComboBox()
        self.wl_status.addItems(["In Progress", "Completed", "On Hold"])
        self.add_field("Status", self.wl_status)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Notes or comments…")
        self.notes.setFixedHeight(100)
        self.add_field("Notes", self.notes)

        self.add_stretch()

    def get_data(self):
        data = {
            "equipment_id":   self.equipment_id,
            "job_name":       self.job_name.text(),
            "assigned_to":    self.assigned_to.text(),
            "department":     self.department.text(),
            "check_out_date": self.check_out_date.date().toString(Qt.DateFormat.ISODate),
            "current_status": self.wl_status.currentText(),
            "notes":          self.notes.toPlainText(),
        }
        ret = self.expected_return.date()
        if ret > QDate(2000, 1, 1):
            data["expected_return_date"] = ret.toString(Qt.DateFormat.ISODate)
        return data


# ──────────────────────────────────────────────────────────────
# PAGE WIDGETS
# ──────────────────────────────────────────────────────────────

def _scrollable_page():
    """Return (outer QWidget, inner content QWidget with QVBoxLayout)."""
    outer  = QWidget()
    outer.setStyleSheet(f"background: {DARK_BG};")
    scroll = QScrollArea(outer)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)
    outer_layout.addWidget(scroll)

    inner = QWidget()
    inner.setStyleSheet(f"background: {DARK_BG};")
    inner_layout = QVBoxLayout(inner)
    inner_layout.setContentsMargins(14, 14, 14, 20)
    inner_layout.setSpacing(12)
    scroll.setWidget(inner)
    return outer, inner, inner_layout


class OverviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._loading = LoadingBar(self)
        root.addWidget(self._loading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet(f"background: {DARK_BG};")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(14, 14, 14, 20)
        self._layout.setSpacing(14)
        scroll.setWidget(content)

        self._layout.addWidget(SectionTitle("Overview"))

        # Status summary cards in a 2-column grid
        self._stat_cards: Dict[str, QLabel] = {}
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QHBoxLayout(grid_widget)
        grid.setSpacing(10)

        left_col  = QVBoxLayout()
        right_col = QVBoxLayout()
        left_col.setSpacing(10)
        right_col.setSpacing(10)

        statuses = [
            ("Total",      "total",      TEXT,           "📦"),
            ("Available",  "available",  ACCENT2,        "✅"),
            ("In Service", "in_service", ACCENT,         "🔧"),
            ("Faulty",     "faulty",     DANGER,         "⚠️"),
        ]
        for i, (label, key, color, icon) in enumerate(statuses):
            card = self._make_stat_card(label, key, color, icon)
            if i % 2 == 0:
                left_col.addWidget(card)
            else:
                right_col.addWidget(card)

        grid.addLayout(left_col)
        grid.addLayout(right_col)
        self._layout.addWidget(grid_widget)

        # Category breakdown section
        self._layout.addWidget(Divider())
        self._layout.addWidget(SectionTitle("By Category"))
        self._cat_container = QVBoxLayout()
        self._cat_container.setSpacing(8)
        self._layout.addLayout(self._cat_container)

        self._layout.addStretch()

    def _make_stat_card(self, label: str, key: str, color: str, icon: str) -> Card:
        card = Card()
        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        top = QLabel(f"{icon}  {label}")
        top.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; background: transparent;")

        val_lbl = QLabel("—")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 22pt; font-weight: bold; background: transparent;")

        self._stat_cards[key] = val_lbl

        v.addWidget(top)
        v.addWidget(val_lbl)
        card.layout().addLayout(v)
        return card

    def update_data(self, overview: dict, equipment: list = None):
        # ── Stat cards ──────────────────────────────────────
        mapping = {
            "total":      overview.get("total", 0),
            "available":  overview.get("available", 0),
            "in_service": overview.get("in_service", 0),
            "faulty":     overview.get("faulty", 0),
        }
        for key, val in mapping.items():
            if key in self._stat_cards:
                self._stat_cards[key].setText(str(val))

        # ── Category breakdown computed from raw equipment list ─
        while self._cat_container.count():
            item = self._cat_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        categories: Dict[str, int] = {}
        for eq in (equipment or []):
            cat = eq.get("category") or "Other"
            categories[cat] = categories.get(cat, 0) + 1

        if not categories:
            lbl = QLabel("No category data")
            lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 12pt; padding: 8px;")
            self._cat_container.addWidget(lbl)
            return

        total = sum(categories.values()) or 1
        for cat_name, count in sorted(categories.items(), key=lambda x: -x[1]):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)

            name_lbl = QLabel(cat_name)
            name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12pt; background: transparent;")

            pct = count / total * 100
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(pct))
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background: {SURFACE2}; border-radius: 3px; }}
                QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
            """)

            cnt_lbl = QLabel(str(count))
            cnt_lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; background: transparent;")
            cnt_lbl.setFixedWidth(40)
            cnt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(name_lbl)
            col.addWidget(bar)

            rl.addLayout(col, stretch=1)
            rl.addWidget(cnt_lbl)

            self._cat_container.addWidget(row)

    def set_loading(self, loading: bool):
        if loading:
            self._loading.show()
        else:
            self._loading.hide()


class EquipmentCard(QFrame):
    """One card per equipment item in the inventory list."""
    worklog_requested = pyqtSignal(int)
    edit_requested    = pyqtSignal(int)
    delete_requested  = pyqtSignal(int)

    def __init__(self, eq: dict, parent=None):
        super().__init__(parent)
        self.eq = eq
        self.eq_id = eq.get("id", -1)
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border-radius: 14px;
                border: 1px solid {DIVIDER};
            }}
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(6)

        # Row 1: product name + status badge
        r1 = QHBoxLayout()
        name = QLabel(self.eq.get("product_name", "Unknown"))
        name.setStyleSheet(f"color: {TEXT}; font-size: 13pt; font-weight: bold; background: transparent;")
        name.setWordWrap(True)
        r1.addWidget(name, stretch=1)

        badge = StatusBadge(self.eq.get("status", "Unknown"))
        r1.addWidget(badge)
        root.addLayout(r1)

        # Row 2: asset / serial
        asset  = self.eq.get("asset_no",  "—")
        serial = self.eq.get("serial_no", "—")
        meta = QLabel(f"Asset: {asset}   ·   S/N: {serial}")
        meta.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; background: transparent;")
        root.addWidget(meta)

        # Row 3: category + location
        cat = self.eq.get("category",  "—")
        loc = self.eq.get("location",  "—")
        r3 = QLabel(f"📁 {cat}   📍 {loc}")
        r3.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11pt; background: transparent;")
        root.addWidget(r3)

        root.addWidget(Divider())

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        wl_btn = QPushButton("+ Work Log")
        wl_btn.setFixedHeight(38)
        wl_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}22;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 8px;
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        wl_btn.clicked.connect(lambda: self.worklog_requested.emit(self.eq_id))

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setFixedHeight(38)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE2};
                color: {TEXT};
                border: 1px solid {DIVIDER};
                border-radius: 8px;
                font-size: 11pt;
            }}
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.eq_id))

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(38, 38)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DANGER}22;
                color: {DANGER};
                border: 1px solid {DANGER};
                border-radius: 8px;
                font-size: 13pt;
            }}
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.eq_id))

        btn_row.addWidget(wl_btn, stretch=2)
        btn_row.addWidget(edit_btn, stretch=2)
        btn_row.addWidget(del_btn)
        root.addLayout(btn_row)


class InventoryPage(QWidget):
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client       = api_client
        self.all_equipment: List[dict] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── toolbar ──────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet(f"background: {SURFACE}; border-bottom: 1px solid {DIVIDER};")
        toolbar.setFixedHeight(56)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(12, 6, 12, 6)
        tl.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search assets…")
        self._search.setFixedHeight(42)
        self._search.textChanged.connect(self._filter)
        tl.addWidget(self._search, stretch=1)

        add_btn = QPushButton("＋")
        add_btn.setFixedSize(42, 42)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: {DARK_BG};
                border-radius: 10px;
                font-size: 18pt;
                font-weight: bold;
                padding: 0;
            }}
        """)
        add_btn.clicked.connect(self._add_equipment)
        tl.addWidget(add_btn)
        root.addWidget(toolbar)

        # filter chips
        chips_widget = QWidget()
        chips_widget.setStyleSheet(f"background: {DARK_BG};")
        chips_layout = QHBoxLayout(chips_widget)
        chips_layout.setContentsMargins(12, 6, 12, 6)
        chips_layout.setSpacing(8)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All Status", "Available", "In Service", "Faulty", "Retired"])
        self._status_filter.setFixedHeight(36)
        self._status_filter.setStyleSheet(f"""
            QComboBox {{
                background: {SURFACE2};
                color: {TEXT};
                border: 1px solid {DIVIDER};
                border-radius: 18px;
                padding: 4px 12px;
                font-size: 11pt;
                min-height: 36px;
            }}
        """)
        self._status_filter.currentTextChanged.connect(self._filter)
        chips_layout.addWidget(self._status_filter)
        chips_layout.addStretch()
        root.addWidget(chips_widget)

        # loading bar
        self._loading = LoadingBar()
        root.addWidget(self._loading)

        # card list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll, stretch=1)

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background: {DARK_BG};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(12, 8, 12, 20)
        self._cards_layout.setSpacing(10)
        scroll.setWidget(self._cards_widget)

        self._empty_lbl = QLabel("No assets found")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 14pt; padding: 40px;")
        self._cards_layout.addWidget(self._empty_lbl)

    def update_data(self, equipment: List[dict]):
        self.all_equipment = equipment
        self._filter()

    def _filter(self):
        query  = self._search.text().lower()
        status = self._status_filter.currentText()
        if status == "All Status":
            status = ""

        filtered = [
            eq for eq in self.all_equipment
            if (not query or query in (eq.get("product_name", "") + eq.get("asset_no", "") + eq.get("serial_no", "")).lower())
            and (not status or eq.get("status", "").lower() == status.lower())
        ]

        # Clear existing cards
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not filtered:
            self._cards_layout.addWidget(self._empty_lbl)
            return

        for eq in filtered:
            card = EquipmentCard(eq)
            card.edit_requested.connect(self._edit_equipment)
            card.delete_requested.connect(self._delete_equipment)
            card.worklog_requested.connect(self._new_worklog)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    def _add_equipment(self):
        dlg = EquipmentDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._loading.show()
            worker = WriteWorker(lambda: self.api_client.create_equipment(data))
            worker.finished.connect(lambda ok: self._on_write(ok, "Asset added!"))
            worker.error_occurred.connect(lambda e: QMessageBox.critical(self, "Error", e))
            worker.finished.connect(lambda _: self._loading.hide())
            worker.start()
            self._workers = getattr(self, "_workers", [])
            self._workers.append(worker)

    def _edit_equipment(self, eq_id: int):
        eq = next((e for e in self.all_equipment if e.get("id") == eq_id), None)
        if not eq: return
        dlg = EquipmentDialog(self, equipment_data=eq)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._loading.show()
            worker = WriteWorker(lambda: self.api_client.update_equipment(eq_id, data))
            worker.finished.connect(lambda ok: self._on_write(ok, "Asset updated!"))
            worker.error_occurred.connect(lambda e: QMessageBox.critical(self, "Error", e))
            worker.finished.connect(lambda _: self._loading.hide())
            worker.start()
            self._workers = getattr(self, "_workers", [])
            self._workers.append(worker)

    def _delete_equipment(self, eq_id: int):
        eq = next((e for e in self.all_equipment if e.get("id") == eq_id), None)
        name = eq.get("product_name", "this asset") if eq else "this asset"
        reply = QMessageBox.question(
            self, "Delete Asset",
            f"Delete '{name}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes: return
        self._loading.show()
        worker = WriteWorker(lambda: self.api_client.delete_equipment(eq_id))
        worker.finished.connect(lambda ok: self._on_write(ok, "Asset deleted."))
        worker.error_occurred.connect(lambda e: QMessageBox.critical(self, "Error", e))
        worker.finished.connect(lambda _: self._loading.hide())
        worker.start()
        self._workers = getattr(self, "_workers", [])
        self._workers.append(worker)

    def _new_worklog(self, eq_id: int):
        dlg = WorkLogDialog(self, equipment_id=eq_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._loading.show()
            worker = WriteWorker(lambda: self.api_client.create_worklog(data))
            worker.finished.connect(lambda ok: self._on_write(ok, "Work log created!"))
            worker.error_occurred.connect(lambda e: QMessageBox.critical(self, "Error", e))
            worker.finished.connect(lambda _: self._loading.hide())
            worker.start()
            self._workers = getattr(self, "_workers", [])
            self._workers.append(worker)

    def _on_write(self, ok: bool, success_msg: str):
        if ok:
            QMessageBox.information(self, "Success", success_msg)
        else:
            QMessageBox.critical(self, "Error", "Operation failed. Please try again.")

    def set_loading(self, loading: bool):
        self._loading.show() if loading else self._loading.hide()


class WorklogCard(QFrame):
    """Card for a single work log entry."""
    def __init__(self, wl: dict, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.wl         = wl
        self.api_client = api_client
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border-radius: 14px;
                border: 1px solid {DIVIDER};
            }}
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(6)

        r1 = QHBoxLayout()
        job = QLabel(self.wl.get("job_name", "—"))
        job.setStyleSheet(f"color: {TEXT}; font-size: 13pt; font-weight: bold; background: transparent;")
        job.setWordWrap(True)
        r1.addWidget(job, stretch=1)

        status = self.wl.get("current_status", "—")
        color  = {"In Progress": ACCENT, "Completed": ACCENT2, "On Hold": WARN}.get(status, TEXT_SUB)
        badge  = QLabel(f"  {status}  ")
        badge.setStyleSheet(f"""
            QLabel {{
                background: {color}22;
                color: {color};
                border: 1px solid {color};
                border-radius: 10px;
                font-size: 10pt;
                font-weight: bold;
                padding: 2px 6px;
            }}
        """)
        r1.addWidget(badge)
        root.addLayout(r1)

        assigned = self.wl.get("assigned_to", "—")
        dept     = self.wl.get("department", "")
        root.addWidget(SubLabel(f"👤 {assigned}" + (f"  ·  {dept}" if dept else "")))

        checkout = self.wl.get("check_out_date", "")[:10] if self.wl.get("check_out_date") else "—"
        root.addWidget(SubLabel(f"📅 Checked out: {checkout}"))

        notes = self.wl.get("notes", "")
        if notes:
            note_lbl = QLabel(notes)
            note_lbl.setWordWrap(True)
            note_lbl.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SUB};
                    font-size: 11pt;
                    background: {DARK_BG};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            root.addWidget(note_lbl)


class WorklogPage(QWidget):
    """Shows either active or past work logs."""
    def __init__(self, api_client: APIClient, active_only: bool, parent=None):
        super().__init__(parent)
        self.api_client  = api_client
        self.active_only = active_only
        self.all_logs: List[dict] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._loading = LoadingBar()
        root.addWidget(self._loading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet(f"background: {DARK_BG};")
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(12, 12, 12, 20)
        self._cl.setSpacing(10)
        scroll.setWidget(content)

    def update_data(self, worklogs: List[dict]):
        if self.active_only:
            self.all_logs = [w for w in worklogs if w.get("current_status") != "Completed"]
        else:
            self.all_logs = [w for w in worklogs if w.get("current_status") == "Completed"]
        self._render()

    def _render(self):
        while self._cl.count():
            item = self._cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not self.all_logs:
            lbl = QLabel("No entries found")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 14pt; padding: 40px;")
            self._cl.addWidget(lbl)
            return

        for wl in self.all_logs:
            card = WorklogCard(wl, self.api_client)
            self._cl.addWidget(card)
        self._cl.addStretch()

    def set_loading(self, loading: bool):
        self._loading.show() if loading else self._loading.hide()


class ImportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.imports: List[dict] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._loading = LoadingBar()
        root.addWidget(self._loading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet(f"background: {DARK_BG};")
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(12, 12, 12, 20)
        self._cl.setSpacing(10)
        scroll.setWidget(content)

    def update_data(self, imports: List[dict]):
        self.imports = imports
        self._render()

    def _render(self):
        while self._cl.count():
            item = self._cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not self.imports:
            lbl = QLabel("No imports yet")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 14pt; padding: 40px;")
            self._cl.addWidget(lbl)
            return

        for imp in self.imports:
            card = Card()
            name = QLabel(imp.get("filename", "Unknown"))
            name.setStyleSheet(f"color: {TEXT}; font-size: 13pt; font-weight: bold; background: transparent;")
            name.setWordWrap(True)
            card.layout().addWidget(name)

            date_str = imp.get("import_date", "")[:10] if imp.get("import_date") else "—"
            total    = imp.get("total_records", 0)
            success  = imp.get("successful_records", 0)
            failed   = imp.get("failed_records", 0)

            card.layout().addWidget(SubLabel(f"📅 {date_str}"))

            row = QHBoxLayout()
            for label, val, color in [
                ("Total",   total,   TEXT),
                ("✅ OK",    success, ACCENT2),
                ("❌ Failed", failed, DANGER),
            ]:
                col = QVBoxLayout()
                lbl_v = QLabel(str(val))
                lbl_v.setStyleSheet(f"color: {color}; font-size: 16pt; font-weight: bold; background: transparent;")
                lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_k = QLabel(label)
                lbl_k.setStyleSheet(f"color: {TEXT_SUB}; font-size: 10pt; background: transparent;")
                lbl_k.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(lbl_v)
                col.addWidget(lbl_k)
                row.addLayout(col)
            card.layout().addLayout(row)

            self._cl.addWidget(card)

        self._cl.addStretch()

    def set_loading(self, loading: bool):
        self._loading.show() if loading else self._loading.hide()


# ──────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ──────────────────────────────────────────────────────────────

class LoginScreen(QWidget):
    login_success = pyqtSignal()

    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Hero section ──────────────────────────────────────
        hero = QWidget()
        hero.setStyleSheet(f"background: {SURFACE};")
        hero.setFixedHeight(190)
        hl = QVBoxLayout(hero)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.setSpacing(4)

        icon = QLabel("🖥️")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 44pt; background: transparent;")
        hl.addWidget(icon)

        title = QLabel("IT Asset Management")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT}; font-size: 17pt; font-weight: bold; background: transparent;")
        hl.addWidget(title)

        sub = QLabel("Mobile Inventory System")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_SUB}; font-size: 12pt; background: transparent;")
        hl.addWidget(sub)

        root.addWidget(hero)

        # ── Fields widget — fixed, no scroll, no unwanted stretch ──
        form_widget = QWidget()
        form_widget.setStyleSheet(f"background: {DARK_BG};")
        fl = QVBoxLayout(form_widget)
        fl.setContentsMargins(24, 20, 24, 16)
        fl.setSpacing(12)

        self._username = QLineEdit()
        self._username.setPlaceholderText("Username")
        fl.addWidget(self._username)

        self._password = QLineEdit()
        self._password.setPlaceholderText("Password")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.returnPressed.connect(self._login)
        fl.addWidget(self._password)

        server_lbl = QLabel("Server URL")
        server_lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 10pt;")
        fl.addWidget(server_lbl)

        self._server = QLineEdit(API_BASE_URL)
        self._server.setPlaceholderText("https://…")
        fl.addWidget(self._server)

        root.addWidget(form_widget)   # no stretch — sits tight below hero
        root.addStretch(1)            # flexible space pushes buttons downward

        # ── Loading bar ───────────────────────────────────────
        self._loading = LoadingBar()
        root.addWidget(self._loading)

        # ── Buttons — 30px from screen bottom, 10px gap between them ──
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background: {DARK_BG};")
        al = QVBoxLayout(action_bar)
        al.setContentsMargins(24, 0, 24, 30)   # bottom=30 so buttons float above edge
        al.setSpacing(10)                        # small gap between Sign In & Create Account

        login_btn = QPushButton("🔐  Sign In")
        login_btn.setFixedHeight(54)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {DARK_BG};
                border: none;
                border-radius: 10px;
                font-size: 14pt;
                font-weight: bold;
                min-height: 54px;
            }}
            QPushButton:hover  {{ background-color: #81D4FA; }}
            QPushButton:pressed {{ background-color: #0288D1; color: white; }}
        """)
        login_btn.clicked.connect(self._login)
        al.addWidget(login_btn)

        reg_btn = QPushButton("Create Account")
        reg_btn.setFixedHeight(54)
        reg_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1.5px solid {ACCENT};
                border-radius: 10px;
                font-size: 13pt;
                font-weight: bold;
                min-height: 54px;
            }}
            QPushButton:pressed {{ background: {ACCENT}22; }}
        """)
        reg_btn.clicked.connect(self._register_flow)
        al.addWidget(reg_btn)

        root.addWidget(action_bar)

    def _login(self):
        u = self._username.text().strip()
        p = self._password.text()
        if not u or not p:
            QMessageBox.warning(self, "Missing Info", "Enter username and password.")
            return

        global API_BASE_URL
        API_BASE_URL = self._server.text().strip()
        self.api_client.base_url = API_BASE_URL

        self._loading.show()
        worker = WriteWorker(lambda: self.api_client.login(u, p))
        worker.finished.connect(self._on_login)
        worker.error_occurred.connect(lambda e: (self._loading.hide(), QMessageBox.critical(self, "Error", e)))
        worker.start()
        self._login_worker = worker

    def _on_login(self, ok: bool):
        self._loading.hide()
        if ok:
            self.login_success.emit()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")

    def _register_flow(self):
        dlg = MobileDialog("Create Account", self)
        dlg._save_btn.setText("Register")

        uname = QLineEdit(); uname.setPlaceholderText("Username")
        email = QLineEdit(); email.setPlaceholderText("Email")
        pwd   = QLineEdit(); pwd.setPlaceholderText("Password")
        pwd.setEchoMode(QLineEdit.EchoMode.Password)
        fname = QLineEdit(); fname.setPlaceholderText("Full Name (optional)")

        dlg.add_field("Username", uname)
        dlg.add_field("Email", email)
        dlg.add_field("Password", pwd)
        dlg.add_field("Full Name", fname)
        dlg.add_stretch()

        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok = self.api_client.register(uname.text(), email.text(), pwd.text(), fname.text())
            if ok:
                QMessageBox.information(self, "Registered", "Account created! You can now log in.")
            else:
                QMessageBox.critical(self, "Error", "Registration failed.")


# ──────────────────────────────────────────────────────────────
# MAIN WINDOW
# ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self._workers: List[QThread] = []

        self.setWindowTitle("IT Asset Management — Mobile")
        # On real mobile this would be fullscreen; on desktop/emulator use a phone-like size
        self.setGeometry(0, 0, 420, 820)

        self._build()
        self._load_data()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # Title bar (global)
        self._title_bar = TitleBar("IT Assets", show_back=False, action_label="↻")
        self._title_bar.action_clicked.connect(self._load_data)
        rl.addWidget(self._title_bar)

        # Global loading bar
        self._global_loading = LoadingBar()
        rl.addWidget(self._global_loading)

        # Pages
        self._stack = QStackedWidget()
        rl.addWidget(self._stack, stretch=1)

        self._page_overview   = OverviewPage()
        self._page_inventory  = InventoryPage(self.api_client)
        self._page_active_wl  = WorklogPage(self.api_client, active_only=True)
        self._page_past_wl    = WorklogPage(self.api_client, active_only=False)
        self._page_imports    = ImportsPage()

        for page in [self._page_overview, self._page_inventory,
                     self._page_active_wl, self._page_past_wl, self._page_imports]:
            self._stack.addWidget(page)

        # Bottom nav
        self._nav = BottomNavBar()
        self._nav.page_changed.connect(self._switch_page)
        rl.addWidget(self._nav)

        PAGE_TITLES = ["Overview", "Inventory", "Active Work Logs", "Past Work Logs", "Import History"]
        self._page_titles = PAGE_TITLES

    def _switch_page(self, idx: int):
        self._stack.setCurrentIndex(idx)
        self._title_bar = TitleBar(self._page_titles[idx], show_back=False, action_label="↻")

    def _load_data(self):
        self._global_loading.show()
        self._page_overview.set_loading(True)
        self._page_inventory.set_loading(True)
        self._page_active_wl.set_loading(True)
        self._page_past_wl.set_loading(True)
        self._page_imports.set_loading(True)

        fetcher = DataFetcher(self.api_client)
        fetcher.data_ready.connect(self._on_data)
        fetcher.error_occurred.connect(self._on_error)
        fetcher.start()
        self._workers.append(fetcher)

    def _on_data(self, data: dict):
        self._global_loading.hide()

        self._page_overview.update_data(data.get("overview", {}), data.get("equipment", []))
        self._page_inventory.update_data(data.get("equipment", []))
        self._page_active_wl.update_data(data.get("worklogs", []))
        self._page_past_wl.update_data(data.get("worklogs", []))
        self._page_imports.update_data(data.get("imports", []))

        for page in [self._page_overview, self._page_inventory,
                     self._page_active_wl, self._page_past_wl, self._page_imports]:
            page.set_loading(False)

    def _on_error(self, msg: str):
        self._global_loading.hide()
        QMessageBox.critical(self, "Connection Error", f"Failed to load data:\n{msg}")


# ──────────────────────────────────────────────────────────────
# APP  ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLE)

    api_client = APIClient()

    # Root stack: login  →  main
    root_stack  = QStackedWidget()
    login_page  = LoginScreen(api_client)

    main_win_holder: List[Optional[MainWindow]] = [None]

    def on_login():
        win = MainWindow(api_client)
        main_win_holder[0] = win
        root_stack.addWidget(win.centralWidget())
        root_stack.setCurrentIndex(1)

    login_page.login_success.connect(on_login)
    root_stack.addWidget(login_page)
    root_stack.setCurrentIndex(0)

    root_stack.setWindowTitle("IT Asset Management — Mobile")
    root_stack.setGeometry(100, 50, 420, 820)
    root_stack.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()