"""
Dashboard View Screen with Dynamic Matplotlib Charts and KPI Cards
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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
        # 1. KPI Cards Row (Compact and Sleek)
        kpi_container = tk.Frame(self, bg=COLORS["bg_dark"])
        kpi_container.pack(fill="x", padx=20, pady=(15, 10))

        self.card_val = KPICard(kpi_container, "TOTAL STOCK VALUE", "₹ 0.00", "💰", "Valuation at cost", COLORS["success"])
        self.card_val.pack(side="left", fill="both", expand=True, padx=6)

        self.card_alert = KPICard(kpi_container, "LOW STOCK ALERTS", "0", "⚠️", "Needs replenishment", COLORS["warning"])
        self.card_alert.pack(side="left", fill="both", expand=True, padx=6)

        self.card_rev = KPICard(kpi_container, "MONTHLY REVENUE", "₹ 0.00", "📈", "Confirmed Sales", COLORS["primary"])
        self.card_rev.pack(side="left", fill="both", expand=True, padx=6)

        self.card_pend = KPICard(kpi_container, "PENDING ORDERS", "0", "⏳", "Unfulfilled sales", COLORS["accent"])
        self.card_pend.pack(side="left", fill="both", expand=True, padx=6)

        # 2. Middle Row (Matplotlib Charts)
        charts_container = tk.Frame(self, bg=COLORS["bg_dark"])
        charts_container.pack(fill="both", expand=True, padx=20, pady=5)

        # Sales Trend Chart Card
        trend_card = tk.Frame(charts_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        trend_card.pack(side="left", fill="both", expand=True, padx=6)

        trend_header = tk.Frame(trend_card, bg=COLORS["bg_card"])
        trend_header.pack(fill="x", padx=15, pady=(12, 6))

        tk.Label(trend_header, text="📈 7-Day Sales Trend (₹)", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        self.fig_trend, self.ax_trend = plt.subplots(figsize=(5.5, 2.7), facecolor=COLORS["bg_card"], dpi=100)
        self.fig_trend.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.22)
        self.ax_trend.set_facecolor(COLORS["bg_card"])
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=trend_card)
        self.canvas_trend.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Category Stock Donut Chart Card
        donut_card = tk.Frame(charts_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        donut_card.pack(side="left", fill="both", expand=True, padx=6)

        donut_header = tk.Frame(donut_card, bg=COLORS["bg_card"])
        donut_header.pack(fill="x", padx=15, pady=(12, 6))

        tk.Label(donut_header, text="🍩 Stock Distribution by Category", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        self.fig_donut, self.ax_donut = plt.subplots(figsize=(5.5, 2.7), facecolor=COLORS["bg_card"], dpi=100)
        self.fig_donut.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.ax_donut.set_facecolor(COLORS["bg_card"])
        self.canvas_donut = FigureCanvasTkAgg(self.fig_donut, master=donut_card)
        self.canvas_donut.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 3. Bottom Row (Low Stock Feed & Quick Action Buttons)
        bottom_container = tk.Frame(self, bg=COLORS["bg_dark"])
        bottom_container.pack(fill="x", padx=20, pady=(5, 15))

        # Low Stock Warning Table Card
        low_card = tk.Frame(bottom_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        low_card.pack(side="left", fill="both", expand=True, padx=6)

        low_header = tk.Frame(low_card, bg=COLORS["bg_card"])
        low_header.pack(fill="x", padx=15, pady=(10, 4))
        tk.Label(low_header, text="🚨 Low Stock Warnings", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["warning"]).pack(side="left")

        cols = [
            ("sku", "SKU", 110, "center"),
            ("name", "Product Name", 200, "w"),
            ("category", "Category", 120, "center"),
            ("current_stock", "In Stock", 90, "center"),
            ("reorder_level", "Reorder Level", 100, "center")
        ]
        self.table_low = DataTable(low_card, cols)
        self.table_low.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Quick Actions Card
        actions_card = tk.Frame(bottom_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, width=230)
        actions_card.pack(side="right", fill="y", padx=6)

        actions_header = tk.Frame(actions_card, bg=COLORS["bg_card"])
        actions_header.pack(fill="x", padx=15, pady=(10, 8))
        tk.Label(actions_header, text="⚡ Quick Actions", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        b1 = ttk.Button(actions_card, text="📄 New Tax Invoice", style="Primary.TButton", command=self._action_new_invoice)
        b1.pack(fill="x", padx=15, pady=6)

        b2 = ttk.Button(actions_card, text="📦 Add Product", style="Secondary.TButton", command=self._action_add_product)
        b2.pack(fill="x", padx=15, pady=6)

        b3 = ttk.Button(actions_card, text="🔄 Adjust Stock", style="Secondary.TButton", command=self._action_adjust_stock)
        b3.pack(fill="x", padx=15, pady=6)

    def refresh_data(self):
        # Update KPI Cards
        stats = ReportModel.get_kpi_summary()
        self.card_val.update_value(f"₹ {stats['total_stock_value']:,.2f}")
        self.card_alert.update_value(str(stats['low_stock_count']))
        self.card_rev.update_value(f"₹ {stats['monthly_revenue']:,.2f}")
        self.card_pend.update_value(str(stats['pending_orders']))

        # Update Sales Trend Chart
        self.ax_trend.clear()
        self.ax_trend.set_facecolor(COLORS["bg_card"])
        trend_data = ReportModel.get_recent_sales_trend()
        if trend_data:
            dates = [d['invoice_date'] for d in trend_data]
            sales = [d['daily_sales'] for d in trend_data]
            
            # Clean formatted dates for X axis
            short_dates = []
            for dt in dates:
                parts = dt.split('-') if '-' in dt else dt.split('/')
                if len(parts) >= 3:
                    short_dates.append(f"{parts[-1]}/{parts[-2]}" if len(parts[0]) == 4 else f"{parts[0]}/{parts[1]}")
                else:
                    short_dates.append(dt)

            self.ax_trend.plot(short_dates, sales, marker='o', color='#4F46E5', linewidth=2.5, markersize=6, markerfacecolor='#4F46E5', markeredgecolor='#FFFFFF', markeredgewidth=1.8)
            self.ax_trend.fill_between(short_dates, sales, color='#4F46E5', alpha=0.12)
        else:
            self.ax_trend.text(0.5, 0.5, 'No Recent Sales Data', color='#94A3B8', ha='center', va='center', fontfamily='sans-serif', fontsize=10)
        
        # Clean light mode axis styling
        self.ax_trend.spines['top'].set_visible(False)
        self.ax_trend.spines['right'].set_visible(False)
        self.ax_trend.spines['left'].set_color('#E2E8F0')
        self.ax_trend.spines['bottom'].set_color('#E2E8F0')
        self.ax_trend.tick_params(colors='#64748B', labelsize=8.5)
        self.ax_trend.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'₹{x*1e-3:.0f}k' if x >= 1000 else f'₹{x:.0f}'))
        self.ax_trend.grid(True, linestyle='--', alpha=0.5, color='#E2E8F0', axis='y')
        
        self.canvas_trend.draw()

        # Update Donut Chart
        self.ax_donut.clear()
        self.ax_donut.set_facecolor(COLORS["bg_card"])
        cat_data = ReportModel.get_category_distribution()
        if cat_data:
            labels = [f"{c['category']} ({c['stock_qty']:g})" for c in cat_data]
            values = [c['stock_qty'] for c in cat_data]
            palette = ['#4F46E5', '#10B981', '#06B6D4', '#F59E0B', '#EC4899', '#8B5CF6', '#3B82F6', '#14B8A6']
            wedges, texts = self.ax_donut.pie(
                values, 
                colors=palette[:len(labels)], 
                wedgeprops={'width': 0.38, 'edgecolor': '#FFFFFF', 'linewidth': 2.5},
                startangle=90
            )
            # Center donut summary
            total_stock_qty = sum(values)
            self.ax_donut.text(0, 0, f"{total_stock_qty:g}\nUnits", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F172A')
            self.ax_donut.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.82, 0.5), frameon=False, labelcolor='#475569', fontsize=8.5)
        else:
            self.ax_donut.text(0.5, 0.5, 'No Stock Data', color='#94A3B8', ha='center', va='center', fontfamily='sans-serif', fontsize=10)
        
        self.canvas_donut.draw()

        # Update Low Stock Table
        low_items = ItemModel.search(stock_filter="Low or Out")
        self.table_low.load_data(low_items)

    def _action_new_invoice(self):
        dlg = InvoiceDialog(self, on_save=self.refresh_data)

    def _action_add_product(self):
        dlg = ItemDialog(self, on_save=self.refresh_data)

    def _action_adjust_stock(self):
        dlg = StockAdjustmentDialog(self, on_save=self.refresh_data)

