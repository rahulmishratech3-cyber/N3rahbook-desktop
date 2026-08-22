"""
N3Rahp Inventory Desktop Management System - Main Entry Point
Supports Admin Login Authentication & Session Management
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

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
        self.geometry("1300x850")
        self.minsize(1100, 700)
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

        # Seed Database on initial run (includes admin user)
        try:
            seed_database(force=False)
        except Exception as ex:
            print(f"Seed Warning: {str(ex)}")

        self.current_user = None
        self.current_view_id = "dashboard"

        # Main Layout Structure
        self._build_ui()

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

    def _on_app_close(self):
        try:
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
                    # 24-hour session expired while app is running
                    self.current_user = None
                    self.show_login_screen()
                    messagebox.showinfo("Session Expired", "Your 24-hour login session has expired. Please sign in again.", parent=self)

            self.after(60000, self._schedule_session_check)
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

        # Instantiate Feature Views
        self.views = {
            "dashboard": DashboardView(self.view_container, nav_callback=self.switch_view),
            "items": ItemsView(self.view_container),
            "stock": StockView(self.view_container),
            "sales": SalesView(self.view_container),
            "customer_po": CustomerPOView(self.view_container),
            "purchase": PurchaseView(self.view_container),
            "contacts": ContactsView(self.view_container),
            "payments": PaymentsView(self.view_container),
            "reports": ReportsView(self.view_container),
            "users": UsersView(self.view_container),
            "settings": SettingsView(self.view_container)
        }

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

    def show_login_screen(self):
        self.main_container.pack_forget()
        self.login_view.pack(fill="both", expand=True)

    def handle_login_success(self, user, is_auto_login=False):
        self.current_user = user
        save_session(user)
        self.sidebar.set_user_info(user['full_name'], user.get('role', 'Admin'))
        
        self.login_view.pack_forget()
        self.main_container.pack(fill="both", expand=True)
        
        self.switch_view("dashboard")
        self.update_header_alerts()

    def handle_logout(self):
        confirm = messagebox.askyesno("Confirm Sign Out", "Are you sure you want to log out of Admin Portal?", parent=self)
        if confirm:
            clear_session()
            self.current_user = None
            self.show_login_screen()

    def switch_view(self, view_id):
        if view_id not in self.views:
            return

        self.current_view_id = view_id
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
            "reports": "📈 Reports & GST Analytics"
        }
        self.header.set_title(titles.get(view_id, "Inventory Management"))

        if hasattr(target_view, "refresh_data"):
            target_view.refresh_data()

        self.update_header_alerts()

    def update_header_alerts(self):
        stats = ReportModel.get_kpi_summary()
        self.header.update_alerts(stats.get('low_stock_count', 0))

    def _on_global_search(self, query):
        if self.current_view_id == "items":
            self.views["items"].search_entry.delete(0, tk.END)
            self.views["items"].search_entry.insert(0, query)
            self.views["items"].refresh_data()
        elif self.current_view_id == "contacts":
            self.views["contacts"].search_entry.delete(0, tk.END)
            self.views["contacts"].search_entry.insert(0, query)
            self.views["contacts"].refresh_data()
        elif self.current_view_id == "payments":
            self.views["payments"].search_entry.delete(0, tk.END)
            self.views["payments"].search_entry.insert(0, query)
            self.views["payments"].refresh_data()


    def _on_global_refresh(self):
        try:
            for view in self.views.values():
                if hasattr(view, "refresh_data"):
                    view.refresh_data()
            self.update_header_alerts()
            messagebox.showinfo("Data Refreshed", "Screen and dashboard data refreshed successfully!", parent=self)
        except Exception as ex:
            messagebox.showerror("Refresh Error", f"Failed to refresh data: {str(ex)}", parent=self)


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
