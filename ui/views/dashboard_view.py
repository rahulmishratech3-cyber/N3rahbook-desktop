"""
Dashboard View Screen with Dynamic Matplotlib Charts and KPI Cards
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from config import COLORS, FONTS
from models.report import ReportModel
from models.item import ItemModel
from ui.components.cards import KPICard
from ui.components.data_table import DataTable
from ui.components.dialogs import ItemDialog, StockAdjustmentDialog
from ui.components.invoice_dialog import InvoiceDialog

class DashboardView(tk.Frame):
    def __init__(self, parent, nav_callback=None):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.nav_callback = nav_callback

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. KPI Cards Row
        kpi_container = tk.Frame(self, bg=COLORS["bg_dark"])
        kpi_container.pack(fill="x", padx=20, pady=15)

        self.card_val = KPICard(kpi_container, "TOTAL STOCK VALUE", "₹ 0.00", "💰", "Valuation at cost", COLORS["success"])
        self.card_val.pack(side="left", fill="both", expand=True, padx=5)

        self.card_alert = KPICard(kpi_container, "LOW STOCK ALERTS", "0", "⚠️", "Needs replenishment", COLORS["warning"])
        self.card_alert.pack(side="left", fill="both", expand=True, padx=5)

        self.card_rev = KPICard(kpi_container, "MONTHLY REVENUE", "₹ 0.00", "📈", "Confirmed Sales", COLORS["primary"])
        self.card_rev.pack(side="left", fill="both", expand=True, padx=5)

        self.card_pend = KPICard(kpi_container, "PENDING ORDERS", "0", "⏳", "Unfulfilled sales", COLORS["accent"])
        self.card_pend.pack(side="left", fill="both", expand=True, padx=5)

        # 2. Middle Row (Matplotlib Charts)
        charts_container = tk.Frame(self, bg=COLORS["bg_dark"])
        charts_container.pack(fill="both", expand=True, padx=20, pady=5)

        # Sales Trend Chart Card
        trend_card = tk.Frame(charts_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        trend_card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(trend_card, text="📊 7-Day Sales Trend (₹)", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", padx=15, pady=10)

        self.fig_trend, self.ax_trend = plt.subplots(figsize=(5, 3), facecolor=COLORS["bg_card"])
        self.ax_trend.set_facecolor(COLORS["bg_card"])
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=trend_card)
        self.canvas_trend.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

        # Category Stock Donut Chart Card
        donut_card = tk.Frame(charts_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        donut_card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(donut_card, text="🍩 Stock Distribution by Category", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", padx=15, pady=10)

        self.fig_donut, self.ax_donut = plt.subplots(figsize=(5, 3), facecolor=COLORS["bg_card"])
        self.ax_donut.set_facecolor(COLORS["bg_card"])
        self.canvas_donut = FigureCanvasTkAgg(self.fig_donut, master=donut_card)
        self.canvas_donut.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

        # 3. Bottom Row (Low Stock Feed & Quick Action Buttons)
        bottom_container = tk.Frame(self, bg=COLORS["bg_dark"])
        bottom_container.pack(fill="x", padx=20, pady=15)

        # Low Stock Warning Table Card
        low_card = tk.Frame(bottom_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        low_card.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(low_card, text="🚨 Low Stock Warnings", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["warning"]).pack(anchor="w", padx=15, pady=10)

        cols = [
            ("sku", "SKU", 100, "center"),
            ("name", "Product Name", 180, "w"),
            ("category", "Category", 110, "center"),
            ("current_stock", "In Stock", 80, "center"),
            ("reorder_level", "Reorder Level", 90, "center")
        ]
        self.table_low = DataTable(low_card, cols)
        self.table_low.pack(fill="both", expand=True, padx=10, pady=5)

        # Quick Actions Card
        actions_card = tk.Frame(bottom_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, width=220)
        actions_card.pack(side="right", fill="y", padx=5)

        tk.Label(actions_card, text="⚡ Quick Actions", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", padx=15, pady=10)

        b1 = ttk.Button(actions_card, text="📄 New Tax Invoice", style="Primary.TButton", command=self._action_new_invoice)
        b1.pack(fill="x", padx=15, pady=5)

        b2 = ttk.Button(actions_card, text="📦 Add Product", style="Secondary.TButton", command=self._action_add_product)
        b2.pack(fill="x", padx=15, pady=5)

        b3 = ttk.Button(actions_card, text="🔄 Adjust Stock", style="Secondary.TButton", command=self._action_adjust_stock)
        b3.pack(fill="x", padx=15, pady=5)

    def refresh_data(self):
        # Update KPI Cards
        stats = ReportModel.get_kpi_summary()
        self.card_val.update_value(f"₹ {stats['total_stock_value']:,.2f}")
        self.card_alert.update_value(str(stats['low_stock_count']))
        self.card_rev.update_value(f"₹ {stats['monthly_revenue']:,.2f}")
        self.card_pend.update_value(str(stats['pending_orders']))

        # Update Sales Trend Chart
        self.ax_trend.clear()
        trend_data = ReportModel.get_recent_sales_trend()
        if trend_data:
            dates = [d['invoice_date'] for d in trend_data]
            sales = [d['daily_sales'] for d in trend_data]
            self.ax_trend.plot(dates, sales, marker='o', color='#6366F1', linewidth=2.5, markersize=6)
            self.ax_trend.fill_between(dates, sales, color='#6366F1', alpha=0.2)
        else:
            self.ax_trend.text(0.5, 0.5, 'No Recent Sales Data', color='#9CA3AF', ha='center', va='center')
        
        self.ax_trend.tick_params(colors='#9CA3AF', labelsize=8)
        self.ax_trend.grid(True, linestyle='--', alpha=0.2, color='#374151')
        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

        # Update Donut Chart
        self.ax_donut.clear()
        cat_data = ReportModel.get_category_distribution()
        if cat_data:
            labels = [f"{c['category']} ({c['stock_qty']:g})" for c in cat_data]
            values = [c['stock_qty'] for c in cat_data]
            palette = ['#6366F1', '#10B981', '#F59E0B', '#06B6D4', '#F43F5E', '#A855F7', '#3B82F6', '#EC4899']
            wedges, texts = self.ax_donut.pie(
                values, 
                colors=palette[:len(labels)], 
                wedgeprops={'width': 0.45, 'edgecolor': '#1F2937'}
            )
            self.ax_donut.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.85, 0.5), frameon=False, labelcolor='#9CA3AF', fontsize=8)
        else:
            self.ax_donut.text(0.5, 0.5, 'No Stock Data', color='#9CA3AF', ha='center', va='center')
        
        self.fig_donut.tight_layout()
        self.canvas_donut.draw()

        # Update Low Stock Table
        low_items = ItemModel.search(stock_filter="Low Stock") + ItemModel.search(stock_filter="Out of Stock")
        self.table_low.load_data(low_items)

    def _action_new_invoice(self):
        dlg = InvoiceDialog(self, on_save=self.refresh_data)

    def _action_add_product(self):
        dlg = ItemDialog(self, on_save=self.refresh_data)

    def _action_adjust_stock(self):
        dlg = StockAdjustmentDialog(self, on_save=self.refresh_data)
