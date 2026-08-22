"""
Items & Product Catalog View Screen
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.item import ItemModel
from ui.components.data_table import DataTable
from ui.components.dialogs import ItemDialog
from ui.components.excel_import_dialog import ExcelImportDialog

class ItemsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Top Control Bar (Filters & Add Button)
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        # Search Box
        tk.Label(ctrl_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=4)
        self.search_entry = ttk.Entry(ctrl_bar, width=20)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_data())

        # Category Filter
        tk.Label(ctrl_bar, text="Category:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=5)
        self.cat_combo = ttk.Combobox(ctrl_bar, values=["All"], state="readonly", width=14)
        self.cat_combo.current(0)
        self.cat_combo.pack(side="left", padx=3)
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_cat_changed)

        # Sub-Category Filter
        tk.Label(ctrl_bar, text="Sub-Category:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=5)
        self.subcat_combo = ttk.Combobox(ctrl_bar, values=["All"], state="readonly", width=16)
        self.subcat_combo.current(0)
        self.subcat_combo.pack(side="left", padx=3)
        self.subcat_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Stock Status Filter
        tk.Label(ctrl_bar, text="Stock:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=5)
        self.stock_combo = ttk.Combobox(ctrl_bar, values=["All", "In Stock", "Low Stock", "Out of Stock"], state="readonly", width=12)
        self.stock_combo.current(0)
        self.stock_combo.pack(side="left", padx=3)
        self.stock_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Right Actions
        ttk.Button(ctrl_bar, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_selected).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="✏️ Edit", style="Secondary.TButton", command=self._edit_selected).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="📥 Import Excel", style="Secondary.TButton", command=self._import_excel).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="➕ Add Product", style="Primary.TButton", command=self._add_item).pack(side="right", padx=3)

        # Data Table Container
        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("sku", "SKU Code", 100, "center"),
            ("hsn_code", "HSN Code", 85, "center"),
            ("name", "Product Name", 200, "w"),
            ("category", "Main Category", 130, "center"),
            ("subcategory", "Sub-Category", 140, "center"),
            ("unit", "Unit", 60, "center"),
            ("cost_price", "Cost Price (₹)", 95, "e"),
            ("selling_price", "Selling Price (₹)", 105, "e"),
            ("current_stock", "Stock Qty", 85, "center"),
            ("reorder_level", "Reorder Level", 85, "center"),
            ("status", "Status", 75, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_selected)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_cat_changed(self, event=None):
        cat = self.cat_combo.get()
        subcats = ["All"] + ItemModel.get_subcategories(cat if cat != "All" else None)
        self.subcat_combo.config(values=subcats)
        self.subcat_combo.current(0)
        self.refresh_data()

    def refresh_data(self):
        query = self.search_entry.get().strip()
        category = self.cat_combo.get()
        subcategory = self.subcat_combo.get() if hasattr(self, 'subcat_combo') else "All"
        stock_filter = self.stock_combo.get()

        # Update Category list
        categories = ["All"] + ItemModel.get_categories()
        self.cat_combo.config(values=categories)

        items = ItemModel.search(query=query, category=category, subcategory=subcategory, stock_filter=stock_filter)
        
        # Format currency and clean stock fields for display
        display_items = []
        for i in items:
            row = dict(i)
            row['cost_price'] = f"₹ {i['cost_price']:,.2f}"
            row['selling_price'] = f"₹ {i['selling_price']:,.2f}"
            row['subcategory'] = i.get('subcategory') or '-'
            stk = round(float(i.get('current_stock', 0.0)), 2)
            row['current_stock'] = f"{stk:g}"
            reorder = round(float(i.get('reorder_level', 0.0)), 2)
            row['reorder_level'] = f"{reorder:g}"
            display_items.append(row)

        self.table.load_data(display_items)

    def _add_item(self):
        ItemDialog(self, on_save=self.refresh_data)

    def _edit_selected(self, item_row=None):
        selected = item_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a product from the table to edit.", parent=self)
            return

        item = ItemModel.get_by_id(selected['id'])
        if item:
            ItemDialog(self, item_data=item, on_save=self.refresh_data)

    def _delete_selected(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select product(s) to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            msg = f"Are you sure you want to delete SKU: {selected_items[0]['sku']}?\n\nThis will permanently delete the product and its transaction history."
        else:
            msg = f"Are you sure you want to delete {count} selected products?\n\nThis will permanently delete all selected products and their transaction history."

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt = ItemModel.delete_many(ids)
                self.refresh_data()
                if count == 1:
                    messagebox.showinfo("Success", f"Product SKU '{selected_items[0].get('sku')}' deleted successfully!", parent=self)
                else:
                    messagebox.showinfo("Success", f"{deleted_cnt} products deleted successfully!", parent=self)
            except Exception as ex:
                messagebox.showerror("Delete Error", f"Failed to delete product(s): {str(ex)}", parent=self)

    def _import_excel(self):
        ExcelImportDialog(self, default_type="items", on_success=self.refresh_data)
