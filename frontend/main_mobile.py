"""
IT Asset Management System — Android/Kivy Mobile Client
Targets KivyMD 1.2.0 (pip install kivymd==1.2.0)

Run:
    python3 main_android.py

Build APK:
    pip install buildozer
    buildozer android debug
"""

import json
import threading
import requests
from datetime import date
from typing import List
from pathlib import Path

import os
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.chip import MDChip


# ═══════════════════════════════════════════════════════════════════════════════
# BACKEND — identical to desktop main.py
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_api_url():
    local_url = "http://192.168.64.75:8000"
    cloud_url = "https://inventory-system-iaub.onrender.com"
    try:
        import requests as _r
        _r.get(local_url + "/", timeout=3)
        print("[API] Local NAS reachable — using local backend")
        return local_url, "local"
    except Exception:
        print("[API] Local NAS unreachable — using cloud backend")
        return cloud_url, "cloud"


API_BASE_URL, API_CONNECTION_TYPE = _detect_api_url()
REQUEST_TIMEOUT = 30


class LocationHistory:
    _FILE = Path.home() / ".it_asset_locations.json"
    _MAX  = 200

    def __init__(self):
        self._items: List[str] = []
        self._load()

    def _load(self):
        try:
            if self._FILE.exists():
                data = json.loads(self._FILE.read_text(encoding="utf-8"))
                self._items = data if isinstance(data, list) else []
        except Exception as e:
            print(f"[LocationHistory] Load error: {e}")
            self._items = []

    def _save(self):
        try:
            self._FILE.write_text(json.dumps(self._items, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[LocationHistory] Save error: {e}")

    def add(self, text: str):
        text = text.strip()
        if not text:
            return
        if text in self._items:
            self._items.remove(text)
        self._items.insert(0, text)
        self._items = self._items[: self._MAX]
        self._save()

    def items(self) -> List[str]:
        return list(self._items)


_location_history = LocationHistory()


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
            r = requests.post(f"{self.base_url}/api/auth/login",
                              json={"username": username, "password": password},
                              timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                self.set_token(r.json()["access_token"])
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def get_equipment(self, status=None, search=None):
        try:
            all_items, skip, page_size = [], 0, 500
            while True:
                params = {"skip": skip, "limit": page_size}
                if status: params["status"] = status
                if search: params["search"] = search
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

    def update_equipment(self, equipment_id: int, data: dict) -> bool:
        try:
            r = requests.put(f"{self.base_url}/api/equipment/{equipment_id}",
                             headers=self.headers, json=data,
                             timeout=REQUEST_TIMEOUT)
            return r.status_code == 200
        except Exception as e:
            print(f"Update equipment error: {e}")
            return False

    def get_worklogs(self):
        try:
            r = requests.get(f"{self.base_url}/api/worklogs",
                             headers=self.headers, timeout=REQUEST_TIMEOUT)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"Get worklogs error: {e}")
            return []

    def create_worklog(self, data: dict) -> bool:
        try:
            print(f"[DEBUG] Creating worklog: {data}")
            r = requests.post(f"{self.base_url}/api/worklogs",
                              headers=self.headers, json=data,
                              timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                print(f"[DEBUG] Worklog creation failed: {r.status_code} - {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"Create worklog error: {e}")
            return False

    def update_worklog(self, worklog_id: int, data: dict) -> bool:
        try:
            print(f"[DEBUG] Updating worklog {worklog_id}: {data}")
            r = requests.put(f"{self.base_url}/api/worklogs/{worklog_id}",
                             headers=self.headers, json=data,
                             timeout=REQUEST_TIMEOUT)
            if r.status_code != 200:
                print(f"[DEBUG] Worklog update failed: {r.status_code} - {r.text}")
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
            print(f"Get overview stats error: {e}")
            return {}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def today_str() -> str:
    return date.today().isoformat()


def fmt_date(iso: str) -> str:
    return iso[:10] if iso else ""


def run_async(fn, callback=None):
    def _run():
        result = fn()
        if callback:
            Clock.schedule_once(lambda dt: callback(result), 0)
    threading.Thread(target=_run, daemon=True).start()


STATUS_COLORS = {
    "Available":  (0.298, 0.686, 0.314, 1),
    "In Service": (1.0,   0.757, 0.027, 1),
    "Faulty":     (0.957, 0.263, 0.212, 1),
    "Retired":    (0.620, 0.620, 0.620, 1),
}


def status_color(s: str):
    return STATUS_COLORS.get(s, (0.5, 0.5, 0.5, 1))


def show_snack(text: str, duration: float = 3, error: bool = False):
    """KivyMD 1.2.0: MDSnackbar requires child widgets, no text property."""
    snack = MDSnackbar(duration=duration)
    if error:
        snack.md_bg_color = (0.75, 0.15, 0.15, 1)
    snack.add_widget(MDLabel(
        text=text,
        theme_text_color="Custom",
        text_color=(1, 1, 1, 1),
    ))
    snack.open()


# ═══════════════════════════════════════════════════════════════════════════════
# REUSABLE WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class StatCard(MDCard):
    def __init__(self, icon, value, label, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding     = dp(10)
        self.spacing     = dp(2)
        self.radius      = [dp(10)]
        self.elevation   = 2
        self.md_bg_color = (0.13, 0.13, 0.16, 1)
        self.size_hint   = (None, None)
        self.size        = (dp(140), dp(100))

        self.add_widget(MDLabel(text=icon, font_style="H5", halign="center",
                                theme_text_color="Custom", text_color=color,
                                size_hint_y=None, height=dp(36)))
        self.add_widget(MDLabel(text=str(value), font_style="H5", halign="center",
                                bold=True, theme_text_color="Custom", text_color=color,
                                size_hint_y=None, height=dp(30)))
        self.add_widget(MDLabel(text=label, font_style="Caption", halign="center",
                                theme_text_color="Secondary",
                                size_hint_y=None, height=dp(20)))


class SectionHeader(MDLabel):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, font_style="Subtitle1", bold=True,
                         theme_text_color="Primary",
                         size_hint_y=None, height=dp(36),
                         padding_x=dp(4), **kwargs)


class EmptyLabel(MDLabel):
    def __init__(self, msg="No data found", **kwargs):
        super().__init__(text=msg, halign="center", valign="middle",
                         theme_text_color="Hint", font_style="Body1",
                         size_hint_y=None, height=dp(80), **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

class LoginScreen(Screen):
    def __init__(self, api_client, on_login, **kwargs):
        super().__init__(name="login", **kwargs)
        self.api_client = api_client
        self.on_login   = on_login
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(32), spacing=dp(14))

        root.add_widget(Widget(size_hint_y=0.12))
        root.add_widget(MDLabel(text="[b]IT Asset Manager[/b]", markup=True,
                                font_style="H5", halign="center",
                                size_hint_y=None, height=dp(48)))
        backend_txt = "Cloud Backend" if API_CONNECTION_TYPE == "cloud" else "Local Backend"
        root.add_widget(MDLabel(text=backend_txt, halign="center",
                                theme_text_color="Hint", font_style="Caption",
                                size_hint_y=None, height=dp(22)))
        root.add_widget(Widget(size_hint_y=0.06))

        self.username = MDTextField(hint_text="Username",
                                    size_hint_y=None, height=dp(54))
        self.password = MDTextField(hint_text="Password", password=True,
                                    size_hint_y=None, height=dp(54))
        root.add_widget(self.username)
        root.add_widget(self.password)
        root.add_widget(Widget(size_hint_y=0.04))

        self.login_btn = MDRaisedButton(
            text="Login", size_hint=(1, None), height=dp(48),
            md_bg_color=(0.18, 0.55, 0.95, 1))
        self.login_btn.bind(on_release=self._do_login)
        root.add_widget(self.login_btn)

        self.err_lbl = MDLabel(text="", halign="center",
                               theme_text_color="Error", font_style="Caption",
                               size_hint_y=None, height=dp(22))
        root.add_widget(self.err_lbl)
        root.add_widget(Widget())
        self.add_widget(root)

    def _do_login(self, *_):
        self.login_btn.text     = "Logging in..."
        self.login_btn.disabled = True
        self.err_lbl.text       = ""

        def _auth():
            return self.api_client.login(self.username.text.strip(),
                                         self.password.text)

        def _done(ok):
            self.login_btn.disabled = False
            self.login_btn.text     = "Login"
            if ok:
                self.on_login()
            else:
                self.err_lbl.text = "Invalid credentials. Please try again."

        run_async(_auth, _done)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB CONTENT VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class OverviewView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.add_widget(MDTopAppBar(title="Overview", elevation=3))
        self.scroll  = ScrollView()
        self.content = BoxLayout(orientation="vertical", padding=dp(14),
                                 spacing=dp(14), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

    def refresh(self, data: dict):
        self.content.clear_widgets()
        stats  = data.get("overview", {})
        eq_map = {e["id"]: e for e in data.get("equipment", [])}
        active = [w for w in data.get("worklogs", [])
                  if w.get("current_status") == "In Progress"]

        # Stat cards
        self.content.add_widget(SectionHeader("Device Status"))
        row = BoxLayout(size_hint_y=None, height=dp(108), spacing=dp(10))
        for icon, key, label, color in [
            ("OK",  "available",  "Available",  STATUS_COLORS["Available"]),
            ("SVC", "in_service", "In Service", STATUS_COLORS["In Service"]),
            ("ERR", "faulty",     "Faulty",     STATUS_COLORS["Faulty"]),
            ("RET", "retired",    "Retired",    STATUS_COLORS["Retired"]),
        ]:
            row.add_widget(StatCard(icon, stats.get(key, 0), label, color))
        self.content.add_widget(row)

        # Active log cards
        self.content.add_widget(SectionHeader(f"Active Logs ({len(active)})"))
        for log in active[:8]:
            eq  = eq_map.get(log.get("equipment_id"), {})
            loc = log.get("location") or eq.get("location", "") or "-"
            card = MDCard(orientation="vertical", padding=dp(10), spacing=dp(4),
                          radius=[dp(8)], elevation=1, size_hint_y=None,
                          md_bg_color=(0.13, 0.13, 0.17, 1))
            card.bind(minimum_height=card.setter("height"))
            top = BoxLayout(size_hint_y=None, height=dp(22))
            top.add_widget(MDLabel(text=eq.get("asset_no", "?"), bold=True))
            top.add_widget(MDLabel(text=loc, halign="right",
                                   theme_text_color="Secondary"))
            card.add_widget(top)
            card.add_widget(MDLabel(text=eq.get("product_name", ""),
                                    font_style="Caption",
                                    theme_text_color="Hint",
                                    size_hint_y=None, height=dp(16)))
            self.content.add_widget(card)

        if not active:
            self.content.add_widget(EmptyLabel("No active work logs"))


class InventoryView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._all = []

        self.add_widget(MDTopAppBar(
            title="Inventory", elevation=3,
            right_action_items=[["refresh",
                lambda x: MDApp.get_running_app().load_data()]]))

        sb = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(10), dp(5)])
        self.search = MDTextField(hint_text="Search asset / product...",
                                  size_hint_y=None, height=dp(44))
        self.search.bind(text=self._on_search)
        sb.add_widget(self.search)
        self.add_widget(sb)

        # Filter chips
        chip_row = BoxLayout(size_hint_y=None, height=dp(38),
                             padding=[dp(10), 0], spacing=dp(6))
        for s in ["All", "Available", "In Service", "Faulty", "Retired"]:
            c = MDChip(text=s, size_hint=(None, None), height=dp(30))
            c.bind(on_release=lambda chip, st=s: self._filter(st))
            chip_row.add_widget(c)
        self.add_widget(chip_row)

        self.scroll = ScrollView()
        self.lst    = MDList()
        self.scroll.add_widget(self.lst)
        self.add_widget(self.scroll)

    def refresh(self, data: dict):
        self._all = data.get("equipment", [])
        self._render(self._all)

    def _render(self, items):
        self.lst.clear_widgets()
        if not items:
            self.lst.add_widget(EmptyLabel())
            return
        for eq in items:
            status = eq.get("status", "")
            loc    = eq.get("location") or ""
            sec    = f"{status}  |  {loc}" if loc else status
            item = TwoLineListItem(
                text=f"{eq.get('asset_no','')}  -  {eq.get('product_name','')}",
                secondary_text=sec,
                on_release=lambda x, e=eq: MDApp.get_running_app().show_eq_detail(e)
            )
            item.secondary_theme_text_color = "Custom"
            item.secondary_text_color       = status_color(status)
            self.lst.add_widget(item)

    def _on_search(self, _, text):
        q = text.lower().strip()
        if not q:
            self._render(self._all)
            return
        self._render([
            e for e in self._all
            if q in e.get("asset_no", "").lower()
            or q in e.get("product_name", "").lower()
            or q in (e.get("location") or "").lower()
        ])

    def _filter(self, status):
        items = ([e for e in self._all if e.get("status") == status]
                 if status != "All" else self._all)
        self._render(items)


class ActiveLogsView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._active = []
        self._eq_map = {}

        self.add_widget(MDTopAppBar(title="Active Work Logs", elevation=3))

        btn_row = BoxLayout(size_hint_y=None, height=dp(50),
                            padding=[dp(10), dp(5)], spacing=dp(8))
        btn_row.add_widget(MDRaisedButton(
            text="+ Change Status",
            md_bg_color=(0.18, 0.55, 0.95, 1),
            on_release=lambda x: MDApp.get_running_app().open_change_status()))
        btn_row.add_widget(MDRaisedButton(
            text="Make Available",
            md_bg_color=(0.18, 0.68, 0.30, 1),
            on_release=lambda x: MDApp.get_running_app().open_make_available()))
        self.add_widget(btn_row)

        self.scroll = ScrollView()
        self.lst    = MDList()
        self.scroll.add_widget(self.lst)
        self.add_widget(self.scroll)

    def refresh(self, data: dict):
        self._eq_map = {e["id"]: e for e in data.get("equipment", [])}
        self._active = [w for w in data.get("worklogs", [])
                        if w.get("current_status") == "In Progress"]
        self._render()

    def _render(self):
        self.lst.clear_widgets()
        if not self._active:
            self.lst.add_widget(EmptyLabel("No active work logs"))
            return
        for log in self._active:
            eq   = self._eq_map.get(log.get("equipment_id"), {})
            loc  = log.get("location") or eq.get("location", "") or "-"
            dept = log.get("department", "") or ""
            line2 = f"{loc}  |  {dept}" if dept else loc
            line3 = f"Out: {fmt_date(log.get('check_out_date',''))}"
            item = ThreeLineListItem(
                text=f"{eq.get('asset_no','?')}  -  {eq.get('product_name','')}",
                secondary_text=line2,
                tertiary_text=line3,
                on_release=lambda x, l=log, e=eq:
                    MDApp.get_running_app().show_worklog_detail(l, e)
            )
            self.lst.add_widget(item)

    def get_active(self): return self._active
    def get_eq_map(self): return self._eq_map


class PastLogsView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._past   = []
        self._eq_map = {}

        self.add_widget(MDTopAppBar(title="Past Work Logs", elevation=3))

        sb = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(10), dp(5)])
        self.search = MDTextField(hint_text="Search by asset or location...",
                                  size_hint_y=None, height=dp(44))
        self.search.bind(text=self._on_search)
        sb.add_widget(self.search)
        self.add_widget(sb)

        self.scroll = ScrollView()
        self.lst    = MDList()
        self.scroll.add_widget(self.lst)
        self.add_widget(self.scroll)

    def refresh(self, data: dict):
        self._eq_map = {e["id"]: e for e in data.get("equipment", [])}
        self._past   = [w for w in data.get("worklogs", [])
                        if w.get("current_status") != "In Progress"]
        self._render(self._past)

    def _render(self, items):
        self.lst.clear_widgets()
        if not items:
            self.lst.add_widget(EmptyLabel("No past work logs"))
            return
        for log in items:
            eq  = self._eq_map.get(log.get("equipment_id"), {})
            loc = log.get("location") or eq.get("location", "") or "-"
            self.lst.add_widget(ThreeLineListItem(
                text=f"{eq.get('asset_no','?')}  -  {eq.get('product_name','')}",
                secondary_text=f"{loc}  |  Out: {fmt_date(log.get('check_out_date',''))}",
                tertiary_text=f"Returned: {fmt_date(log.get('actual_return_date',''))}  [{log.get('current_status','')}]"
            ))

    def _on_search(self, _, text):
        q = text.lower()
        if not q:
            self._render(self._past)
            return
        self._render([
            l for l in self._past
            if q in (self._eq_map.get(l.get("equipment_id"),{}).get("asset_no","")).lower()
            or q in (l.get("location") or "").lower()
        ])


class ImportsView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.add_widget(MDTopAppBar(title="Import History", elevation=3))
        self.scroll = ScrollView()
        self.lst    = MDList()
        self.scroll.add_widget(self.lst)
        self.add_widget(self.scroll)

    def refresh(self, data: dict):
        self.lst.clear_widgets()
        imports = data.get("imports", [])
        if not imports:
            self.lst.add_widget(EmptyLabel("No import history"))
            return
        for imp in imports:
            name    = imp.get("filename", imp.get("name", "Import"))
            count   = imp.get("equipment_count", imp.get("count", "?"))
            created = fmt_date(imp.get("created_at", ""))
            self.lst.add_widget(TwoLineListItem(
                text=name,
                secondary_text=f"{count} items  |  {created}"
            ))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

class ITAssetApp(MDApp):

    def build(self):
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette  = "Amber"

        self.api_client = APIClient()
        self._data      = {}

        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(LoginScreen(self.api_client,
                                       on_login=self._after_login))
        self.sm.add_widget(self._build_main())
        self.sm.current = "login"
        return self.sm

    def _build_main(self):
        shell = Screen(name="main")
        nav   = MDBottomNavigation()

        self.overview_view  = OverviewView()
        self.inventory_view = InventoryView()
        self.active_view    = ActiveLogsView()
        self.past_view      = PastLogsView()
        self.imports_view   = ImportsView()

        tabs = [
            ("home-outline",    "Overview",  "overview",  self.overview_view),
            ("package-variant", "Inventory", "inventory", self.inventory_view),
            ("clipboard-list",  "Active",    "active",    self.active_view),
            ("history",         "Past",      "past",      self.past_view),
            ("file-import",     "Imports",   "imports",   self.imports_view),
        ]
        for icon, text, name, view in tabs:
            tab = MDBottomNavigationItem(name=name, text=text, icon=icon)
            tab.add_widget(view)
            nav.add_widget(tab)

        shell.add_widget(nav)
        return shell

    # ── Auth + data ───────────────────────────────────────────────────────────

    def _after_login(self):
        self.sm.current = "main"
        self.load_data()

    def load_data(self):
        show_snack("Refreshing data...", duration=1.5)

        def _fetch():
            return {
                "equipment": self.api_client.get_equipment(),
                "worklogs":  self.api_client.get_worklogs(),
                "imports":   self.api_client.get_imports(),
                "overview":  self.api_client.get_overview_stats(),
            }

        def _done(data):
            self._data = data
            self.overview_view.refresh(data)
            self.inventory_view.refresh(data)
            self.active_view.refresh(data)
            self.past_view.refresh(data)
            self.imports_view.refresh(data)
            show_snack("Data refreshed", duration=2)

        run_async(_fetch, _done)

    # ── Detail dialogs ────────────────────────────────────────────────────────

    def _detail_box(self, fields):
        box = BoxLayout(orientation="vertical", spacing=dp(6),
                        size_hint_y=None, padding=[0, dp(4)])
        box.bind(minimum_height=box.setter("height"))
        for label, val in fields:
            row = BoxLayout(size_hint_y=None, height=dp(26))
            row.add_widget(MDLabel(text=f"{label}:", size_hint_x=0.4,
                                   theme_text_color="Hint", font_style="Caption"))
            row.add_widget(MDLabel(text=str(val or "-"), size_hint_x=0.6,
                                   font_style="Body2"))
            box.add_widget(row)
        return box

    def show_eq_detail(self, eq):
        content = self._detail_box([
            ("Asset No",  eq.get("asset_no", "")),
            ("Product",   eq.get("product_name", "")),
            ("Category",  eq.get("category", "")),
            ("Status",    eq.get("status", "")),
            ("Location",  eq.get("location", "")),
            ("Serial No", eq.get("serial_no", "")),
            ("Supplier",  eq.get("supplier", "")),
        ])
        dlg = MDDialog(title=eq.get("asset_no", "Equipment"),
                       type="custom", content_cls=content,
                       buttons=[MDFlatButton(text="Close",
                                on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def show_worklog_detail(self, log, eq):
        loc = log.get("location") or eq.get("location", "") or "-"
        content = self._detail_box([
            ("Asset No",    eq.get("asset_no", "")),
            ("Product",     eq.get("product_name", "")),
            ("Location",    loc),
            ("Department",  log.get("department", "")),
            ("Designation", log.get("designation", "")),
            ("Check Out",   fmt_date(log.get("check_out_date", ""))),
            ("Exp. Return", fmt_date(log.get("expected_return_date", ""))),
            ("Notes",       log.get("notes", "")),
        ])
        dlg = MDDialog(
            title=f"Work Log #{log.get('id','')}",
            type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Close",
                             on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="Make Available",
                               md_bg_color=(0.18, 0.68, 0.30, 1),
                               on_release=lambda x: (
                                   dlg.dismiss(),
                                   self._do_make_available(log, eq)))
            ])
        dlg.open()

    # ── Change Device Status ──────────────────────────────────────────────────

    def open_change_status(self):
        equipment = self._data.get("equipment", [])

        self._cs_asset    = MDTextField(hint_text="Asset Number",
                                        size_hint_y=None, height=dp(52))
        self._cs_status   = "In Service"
        self._cs_loc      = MDTextField(hint_text="Location",
                                        size_hint_y=None, height=dp(52))
        self._cs_dept     = MDTextField(hint_text="Department",
                                        size_hint_y=None, height=dp(52))
        self._cs_desig    = MDTextField(hint_text="Designation",
                                        size_hint_y=None, height=dp(52))
        self._cs_checkout = MDTextField(hint_text="Check-out Date (YYYY-MM-DD)",
                                        text=today_str(),
                                        size_hint_y=None, height=dp(52))
        self._cs_reason   = MDTextField(hint_text="Reason (for Faulty/Retired)",
                                        size_hint_y=None, height=dp(52))

        # Status dropdown button
        self._cs_status_btn = MDRaisedButton(
            text="Status: In Service", size_hint=(1, None), height=dp(42))
        status_items = [
            {"text": s, "viewclass": "OneLineListItem",
             "on_release": lambda x=s: self._set_cs_status(x)}
            for s in ["In Service", "Faulty", "Retired"]
        ]
        self._cs_menu = MDDropdownMenu(caller=self._cs_status_btn,
                                       items=status_items, width_mult=3)
        self._cs_status_btn.bind(on_release=lambda x: self._cs_menu.open())

        # Asset hint (autocomplete suggestion)
        self._cs_hint = MDLabel(text="", font_style="Caption",
                                theme_text_color="Hint",
                                size_hint_y=None, height=dp(18))
        self._cs_asset.bind(
            text=lambda f, t: self._update_asset_hint(t, equipment))

        # Recent location chips
        chips = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        for loc in _location_history.items()[:5]:
            c = MDChip(text=loc, size_hint=(None, None), height=dp(28))
            c.bind(on_release=lambda chip, l=loc:
                   setattr(self._cs_loc, "text", l))
            chips.add_widget(c)

        content = BoxLayout(orientation="vertical", spacing=dp(6),
                            size_hint_y=None, padding=[0, dp(4)])
        content.bind(minimum_height=content.setter("height"))
        for w in [self._cs_asset, self._cs_hint, self._cs_status_btn,
                  chips, self._cs_loc, self._cs_dept,
                  self._cs_desig, self._cs_checkout, self._cs_reason]:
            content.add_widget(w)

        dlg = MDDialog(
            title="Change Device Status", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel",
                             on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="Save",
                               on_release=lambda x: (
                                   dlg.dismiss(),
                                   self._save_status(equipment)))
            ])
        dlg.open()

    def _set_cs_status(self, status):
        self._cs_status = status
        self._cs_status_btn.text = f"Status: {status}"
        self._cs_menu.dismiss()

    def _update_asset_hint(self, text, equipment):
        matches = [e["asset_no"] for e in equipment
                   if text.lower() in e.get("asset_no", "").lower()][:4]
        self._cs_hint.text = "  ".join(matches) if matches else ""

    def _save_status(self, equipment):
        asset_no = self._cs_asset.text.strip()
        status   = self._cs_status

        if not asset_no:
            show_snack("Please enter an asset number", error=True)
            return

        eq = next((e for e in equipment if e.get("asset_no") == asset_no), None)
        if not eq:
            show_snack(f"Asset {asset_no} not found", error=True)
            return

        loc_text = self._cs_loc.text.strip()
        worklog  = {
            "equipment_id":   eq["id"],
            "job_name":       f"{status} - {asset_no}",
            "current_status": "In Progress",
            "check_out_date": self._cs_checkout.text.strip() or today_str(),
            "notes": "",
        }
        eq_update = {"status": status}

        if status == "In Service":
            worklog["location"]    = loc_text
            worklog["department"]  = self._cs_dept.text.strip()
            worklog["designation"] = self._cs_desig.text.strip()
            if loc_text:
                eq_update["location"] = loc_text
                _location_history.add(loc_text)
        elif status in ("Faulty", "Retired"):
            reason = self._cs_reason.text.strip()
            if reason:
                worklog["notes"] = reason

        show_snack("Saving...")

        def _do():
            ok1 = self.api_client.update_equipment(eq["id"], eq_update)
            ok2 = self.api_client.create_worklog(worklog) if ok1 else False
            return ok1 and ok2

        def _done(ok):
            if ok:
                show_snack(f"Status changed to {status}")
                self.load_data()
            else:
                show_snack("Failed to update status", error=True)

        run_async(_do, _done)

    # ── Make Available ────────────────────────────────────────────────────────

    def open_make_available(self):
        active = self.active_view.get_active()
        eq_map = self.active_view.get_eq_map()

        if not active:
            show_snack("No active work logs to close")
            return

        lst = MDList()
        for log in active:
            eq  = eq_map.get(log.get("equipment_id"), {})
            loc = log.get("location") or eq.get("location", "") or "-"
            item = TwoLineListItem(
                text=f"{eq.get('asset_no','?')}  -  {eq.get('product_name','')}",
                secondary_text=loc,
                on_release=lambda x, l=log, e=eq: (
                    dlg.dismiss(), self._do_make_available(l, e))
            )
            lst.add_widget(item)

        scroll = ScrollView(size_hint_y=None,
                            height=min(dp(300), dp(64 * len(active))))
        scroll.add_widget(lst)

        content = BoxLayout(orientation="vertical", size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        content.add_widget(scroll)

        dlg = MDDialog(
            title="Select Device to Return", type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="Cancel",
                                  on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def _do_make_available(self, log, eq):
        show_snack("Updating...")

        def _do():
            ok1 = self.api_client.update_equipment(eq["id"], {"status": "Available"})
            ok2 = self.api_client.update_worklog(log["id"], {
                "current_status":     "Completed",
                "actual_return_date": today_str(),
            }) if ok1 else False
            return ok1 and ok2

        def _done(ok):
            if ok:
                show_snack(f"{eq.get('asset_no','')} is now Available")
                self.load_data()
            else:
                show_snack("Failed to mark as available", error=True)

        run_async(_do, _done)


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ITAssetApp().run()