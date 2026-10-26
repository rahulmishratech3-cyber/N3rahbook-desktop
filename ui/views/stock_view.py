"""
Stock Adjustments & Inventory Ledger View Screen
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS
from models.inventory import InventoryModel
from ui.components.data_table import DataTable
from ui.components.dialogs import StockAdjustmentDialog

class StockView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="📋 Inventory Stock In/Out & Audit Ledger", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        ttk.Button(ctrl_bar, text="🔄 New Manual Adjustment", style="Primary.TButton", command=self._new_adjustment).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_data).pack(side="right", padx=4)

        # Filter bar
        filter_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=8)
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(filter_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self.search_entry = ttk.Entry(filter_bar, width=22)
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        tk.Label(filter_bar, text="Movement Type:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self.type_combo = ttk.Combobox(filter_bar, values=["All", "Add (Inwards)", "Remove (Outwards)"], state="readonly", width=18)
        self.type_combo.current(0)
        self.type_combo.pack(side="left", padx=(0, 15))
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("id", "Txn ID", 75, "center"),
            ("adjustment_date", "Date & Time", 140, "center"),
            ("sku", "SKU", 110, "center"),
            ("item_name", "Product Name", 240, "w"),
            ("type_display", "Type (In/Out)", 120, "center"),
            ("quantity_display", "Quantity", 110, "center"),
            ("unit", "Unit", 70, "center"),
            ("reason", "Reason Code", 150, "center"),
            ("adjusted_by", "Adjusted By", 110, "center"),
            ("notes", "Invoice / Reference Notes", 280, "w")
        ]
        self.table = DataTable(table_container, cols)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_search_key(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self.refresh_data)

    def refresh_data(self):
        adjustments = InventoryModel.get_adjustments()
        query = self.search_entry.get().strip().lower() if hasattr(self, 'search_entry') else ""
        type_filter = self.type_combo.get() if hasattr(self, 'type_combo') else "All"

        display_rows = []
        for adj in adjustments:
            row = dict(adj)
            a_type = str(row.get('adjustment_type', '')).strip()
            
            # Type Filter
            if type_filter == "Add (Inwards)" and a_type.lower() != 'add':
                continue
            if type_filter == "Remove (Outwards)" and a_type.lower() != 'remove':
                continue

            # Search Filter
            if query:
                combined_text = f"{row.get('sku', '')} {row.get('item_name', '')} {row.get('reason', '')} {row.get('notes', '')}".lower()
                if query not in combined_text:
                    continue

            qty = round(float(row.get('quantity', 0.0)), 2)
            if a_type.lower() == 'add':
                row['type_display'] = "🟢 ADD (+)"
                row['quantity_display'] = f"+{qty:g}"
                row['row_tag'] = "paid"
            else:
                row['type_display'] = "🔴 REMOVE (-)"
                row['quantity_display'] = f"-{qty:g}"
                row['row_tag'] = "unpaid"

            display_rows.append(row)

        self.table.load_data(display_rows)

    def _new_adjustment(self):
        StockAdjustmentDialog(self, on_save=self.refresh_data)
