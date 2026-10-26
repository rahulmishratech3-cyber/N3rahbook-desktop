"""
N3Rahp Inventory Desktop Management System - Main Entry Point
Supports Admin Login Authentication & Session Management
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# --- Make UI more responsive (hover cursor) globally ---
_orig_btn_init = ttk.Button.__init__
def _new_btn_init(self, master=None, **kw):
    if 'cursor' not in kw:
        kw['cursor'] = 'hand2'
    _orig_btn_init(self, master, **kw)
ttk.Button.__init__ = _new_btn_init
# --------------------------------------------------------

from PIL import Image, ImageTk
from config import COLORS, FONTS
from database.db_manager import db
from services.seed_service import seed_database
from models.report import ReportModel
from ui.styles import apply_app_styles
from ui.components.sidebar import Sidebar
from ui.components.header import HeaderBar

from ui.views.login_view import LoginView
from ui.views.dashboard_view import DashboardView
from ui.views.items_view import ItemsView
from ui.views.stock_view import StockView
from ui.views.sales_view import SalesView
from ui.views.customer_po_view import CustomerPOView
from ui.views.purchase_view import PurchaseView
from ui.views.contacts_view import ContactsView
from ui.views.payments_view import PaymentsView
from ui.views.reports_view import ReportsView
from ui.views.users_view import UsersView
from ui.views.settings_view import SettingsView


from services.session_service import save_session, get_active_session, clear_session

class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("N3RAH BOOK - Enterprise Billing & Inventory Solutions")
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        init_w = min(1280, max(1000, screen_w - 60))
        init_h = min(750, max(600, screen_h - 80))
        init_x = max(0, (screen_w - init_w) // 2)
        init_y = max(0, (screen_h - init_h) // 2 - 20)
        self.geometry(f"{init_w}x{init_h}+{init_x}+{init_y}")
        self.minsize(980, 580)
        self.configure(bg=COLORS["bg_dark"])

        # Set Window Icon
        logo_icon_path = os.path.join("assets", "logo_icon.png")
        if os.path.exists(logo_icon_path):
            try:
                icon_img = ImageTk.PhotoImage(file=logo_icon_path)
                self.iconphoto(True, icon_img)
                self._icon_ref = icon_img
            except Exception as ex:
                print("Failed to set window icon:", ex)

        # Apply design theme
        apply_app_styles(self)

        self.current_user = None
        self.current_view_id = "dashboard"

        # Ensure tax invoices folder is created automatically
        if not os.path.exists("tax invoices"):
            try:
                os.makedirs("tax invoices")
            except Exception:
                pass

        # Main Layout Structure
        self._build_ui()

        # Render window immediately on screen so double click feels instant
        self.update_idletasks()

        # Deferred background database seeding (does not block window launch)
        self.after(200, self._deferred_seed)

        # Check Active 24-Hour Session
        active_user = get_active_session()
        if active_user:
            self.handle_login_success(active_user, is_auto_login=True)
        else:
            self.show_login_screen()

        # Schedule background session check loop (every 60 seconds)
        self._schedule_session_check()

        # Handle window close (Auto-Backup on Exit)
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

        # Bring window to foreground
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)
        self.focus_force()

        # Dynamic Button Resizing (Responsive UI)
        self._last_w_cat = None
        self._resize_timer = None
        self.bind("<Configure>", self._on_resize_responsive)

    def _on_resize_responsive(self, event):
        if event.widget == self:
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, lambda: self._apply_responsive_styles(event.width))

    def _apply_responsive_styles(self, width):
        cat = 1 if width < 1100 else (3 if width > 1600 else 2)
        if cat != self._last_w_cat:
            self._last_w_cat = cat
            style = ttk.Style()
            if cat == 1:
                style.configure("Primary.TButton", padding=(8, 4), font=("Segoe UI", 9, "bold"))
                style.configure("Secondary.TButton", padding=(6, 3), font=("Segoe UI", 9))
                style.configure("Success.TButton", padding=(8, 4), font=("Segoe UI", 9, "bold"))
            elif cat == 3:
                style.configure("Primary.TButton", padding=(12, 6), font=("Segoe UI", 10, "bold"))
                style.configure("Secondary.TButton", padding=(10, 5), font=("Segoe UI", 9))
                style.configure("Success.TButton", padding=(12, 6), font=("Segoe UI", 10, "bold"))
            else:
                style.configure("Primary.TButton", padding=(10, 5), font=("Segoe UI", 9, "bold"))
                style.configure("Secondary.TButton", padding=(8, 4), font=("Segoe UI", 9))
                style.configure("Success.TButton", padding=(10, 5), font=("Segoe UI", 9, "bold"))

    def _deferred_seed(self):
        try:
            if not self.winfo_exists():
                return
            import threading
            threading.Thread(target=lambda: seed_database(force=False), daemon=True).start()
        except Exception as ex:
            print(f"Seed Warning: {str(ex)}")

    def _on_app_close(self):
        try:
            if hasattr(self, '_session_timer'):
                self.after_cancel(self._session_timer)
            from services.backup_service import get_backup_config, run_full_backup
            config = get_backup_config()
            if config.get('auto_backup_on_exit', True):
                run_full_backup()
        except Exception as ex:
            print("Exit Backup Exception:", ex)
        self.destroy()

    def _schedule_session_check(self):
        try:
            if not self.winfo_exists():
                return
            if self.current_user:
                active_user = get_active_session()
                if not active_user:
                    self.current_user = None
                    self.show_login_screen()
                    messagebox.showinfo("Session Expired", "Your 24-hour login session has expired. Please sign in again.", parent=self)

            if self.winfo_exists():
                self._session_timer = self.after(60000, self._schedule_session_check)
        except Exception:
            pass

    def _build_ui(self):
        # 1. Login View
        self.login_view = LoginView(self, on_login_success=self.handle_login_success)

        # 2. Main Dashboard Application Container
        self.main_container = tk.Frame(self, bg=COLORS["bg_dark"])

        # Sidebar Navigation Menu
        self.sidebar = Sidebar(
            self.main_container,
            on_tab_change=self.switch_view,
            on_logout=self.handle_logout
        )
        self.sidebar.pack(side="left", fill="y")

        # Main Content Wrapper
        content_wrapper = tk.Frame(self.main_container, bg=COLORS["bg_dark"])
        content_wrapper.pack(side="right", fill="both", expand=True)

        # Top Header Bar
        self.header = HeaderBar(
            content_wrapper,
            on_search=self._on_global_search,
            on_refresh=self._on_global_refresh
        )
        self.header.pack(side="top", fill="x")

        # Main View Frame Container
        self.view_container = tk.Frame(content_wrapper, bg=COLORS["bg_dark"])
        self.view_container.pack(side="bottom", fill="both", expand=True)
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

        # Lazy View Factories: views are only constructed when first visited
        self.view_factories = {
            "dashboard": lambda: DashboardView(self.view_container, nav_callback=self.switch_view),
            "items": lambda: ItemsView(self.view_container),
            "stock": lambda: StockView(self.view_container),
            "sales": lambda: SalesView(self.view_container),
            "customer_po": lambda: CustomerPOView(self.view_container),
            "purchase": lambda: PurchaseView(self.view_container),
            "contacts": lambda: ContactsView(self.view_container),
            "payments": lambda: PaymentsView(self.view_container),
            "reports": lambda: ReportsView(self.view_container),
            "users": lambda: UsersView(self.view_container),
            "settings": lambda: SettingsView(self.view_container)
        }
        self.views = {}

    def show_login_screen(self):
        if os.name == 'nt' and self.state() == 'zoomed':
            try:
                self.state('normal')
            except Exception:
                pass
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = min(1100, max(850, screen_w - 80))
        h = min(700, max(540, screen_h - 90))
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.main_container.pack_forget()
        self.login_view.pack(fill="both", expand=True)

    def handle_login_success(self, user, is_auto_login=False):
        self.current_user = user
        save_session(user)
        self.sidebar.set_user_info(user['full_name'], user.get('role', 'Admin'))
        
        self.login_view.pack_forget()
        self.main_container.pack(fill="both", expand=True)

        # Maximize cleanly on Windows so full workspace is visible without overflowing
        if os.name == 'nt':
            try:
                self.state('zoomed')
            except Exception:
                pass
        
        self.switch_view("dashboard")
        self.after(200, self.update_header_alerts)

    def handle_logout(self):
        confirm = messagebox.askyesno("Confirm Sign Out", "Are you sure you want to log out of Admin Portal?", parent=self)
        if confirm:
            clear_session()
            self.current_user = None
            self.show_login_screen()

    def switch_view(self, view_id):
        if view_id not in self.view_factories:
            return

        self.current_view_id = view_id
        is_first_load = False

        if view_id not in self.views:
            is_first_load = True
            view = self.view_factories[view_id]()
            view.grid(row=0, column=0, sticky="nsew")
            self.views[view_id] = view

        target_view = self.views[view_id]
        target_view.tkraise()

        # Update Header Title
        titles = {
            "dashboard": "📊 Dashboard Overview",
            "items": "📦 Product & Items Catalog",
            "stock": "🔄 Inventory Stock Adjustments",
            "sales": "📄 Sales Orders & GST Tax Invoices",
            "customer_po": "📜 Party Purchase Orders & Hisaab (KG)",
            "purchase": "🚚 Purchase Orders & Vendors",
            "contacts": "👥 Customers & Suppliers Directory",
            "payments": "💳 Payment Modes & Party Ledgers",
            "reports": "📈 Reports & GST Analytics",
            "users": "👤 User Accounts & Permissions",
            "settings": "⚙️ System Configuration & Cloud Sync"
        }
        self.header.set_title(titles.get(view_id, "Inventory Management"))

        # If already loaded previously, refresh it
        if not is_first_load and hasattr(target_view, "refresh_data"):
            target_view.refresh_data()

        # Asynchronously update header alerts (won't freeze tab switch)
        self.after(100, self.update_header_alerts)

    def update_header_alerts(self):
        try:
            if not self.winfo_exists():
                return
            count = ReportModel.get_low_stock_count()
            self.header.update_alerts(count)
        except Exception:
            pass

    def _on_global_search(self, query):
        active_view = self.views.get(self.current_view_id)
        if active_view and hasattr(active_view, "search_entry") and hasattr(active_view, "refresh_data"):
            active_view.search_entry.delete(0, tk.END)
            active_view.search_entry.insert(0, query)
            active_view.refresh_data()

    def _on_global_refresh(self):
        try:
            active_view = self.views.get(self.current_view_id)
            if active_view and hasattr(active_view, "refresh_data"):
                active_view.refresh_data()
            self.update_header_alerts()
            messagebox.showinfo("Data Refreshed", "Screen data refreshed successfully!", parent=self)
        except Exception as ex:
            messagebox.showerror("Refresh Error", f"Failed to refresh data: {str(ex)}", parent=self)


if __name__ == "__main__":
    try:
        app = InventoryApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[OK] Application closed.")
