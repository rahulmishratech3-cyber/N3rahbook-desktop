"""UI Views Package Initializer"""
from ui.views.login_view import LoginView
from ui.views.dashboard_view import DashboardView
from ui.views.items_view import ItemsView
from ui.views.stock_view import StockView
from ui.views.sales_view import SalesView
from ui.views.purchase_view import PurchaseView
from ui.views.contacts_view import ContactsView
from ui.views.reports_view import ReportsView
from ui.views.users_view import UsersView
from ui.views.settings_view import SettingsView

__all__ = [
    "LoginView", "DashboardView", "ItemsView", "StockView",
    "SalesView", "PurchaseView", "ContactsView", "ReportsView", "UsersView", "SettingsView"
]
