"""
Purchase Orders & Supplier Replenishment View Screen
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.purchase_order import PurchaseOrderModel
from ui.components.data_table import DataTable
from ui.components.dialogs import PurchaseDialog

class PurchaseView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="🚚 Purchases & Supplier Replenishment", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        # Right Action Buttons
        ttk.Button(ctrl_bar, text="🗑️ Delete PO", style="Secondary.TButton", command=self._delete_selected_po).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="✏️ Edit Purchase", style="Secondary.TButton", command=self._edit_selected_po).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="✅ Mark Received", style="Success.TButton", command=self._mark_received).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="📋 Create PO (Pending)", style="Secondary.TButton", command=self._new_po_dialog).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="🛒 Direct Purchase (Stock In)", style="Primary.TButton", command=self._direct_purchase_dialog).pack(side="right", padx=4)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("po_number", "PO / Ref No.", 110, "center"),
            ("order_date", "Purchase Date", 100, "center"),
            ("expected_date", "Expected Date", 100, "center"),
            ("supplier_name", "Vendor / Supplier", 200, "w"),
            ("company_name", "Company", 180, "w"),
            ("total_amount", "Total Cost (₹)", 120, "e"),
            ("status", "Status", 90, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_selected_po)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_data(self):
        pos = PurchaseOrderModel.get_all()
        display_pos = []
        for p in pos:
            row = dict(p)
            row['total_amount'] = f"₹ {p['total_amount']:,.2f}"
            display_pos.append(row)
        self.table.load_data(display_pos)

    def _direct_purchase_dialog(self):
        PurchaseDialog(self, default_status="Received", on_save=self.refresh_data)

    def _new_po_dialog(self):
        PurchaseDialog(self, default_status="Issued", on_save=self.refresh_data)

    def _edit_selected_po(self, selected_row=None):
        selected = selected_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Purchase Order from the table to edit.", parent=self)
            return

        po = PurchaseOrderModel.get_by_id(selected['id'])
        if po:
            PurchaseDialog(self, po_id=selected['id'], on_save=self.refresh_data)

    def _mark_received(self):
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Purchase Order from the table.", parent=self)
            return

        po = PurchaseOrderModel.get_by_id(selected['id'])
        if not po:
            return

        if po['status'] == 'Received':
            messagebox.showinfo("Already Received", f"PO #{po['po_number']} is already marked as Received.", parent=self)
            return

        confirm = messagebox.askyesno("Confirm Receipt", f"Mark PO #{po['po_number']} as RECEIVED?\n\nThis will automatically increment stock levels for all items in the order and log the stock adjustment.", parent=self)
        if confirm:
            try:
                PurchaseOrderModel.update_status(selected['id'], "Received")
                self.refresh_data()
                messagebox.showinfo("Stock Updated", f"Purchase #{po['po_number']} marked as Received. Inventory stock has been updated!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to update PO status: {str(ex)}", parent=self)

    def _delete_selected_po(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more Purchase Orders to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            po_num = selected_items[0].get('po_number', 'this PO')
            msg = f"Are you sure you want to delete Purchase Order #{po_num}?\n\nIf this order was Received, product stock levels will be reverted."
        else:
            msg = f"Are you sure you want to delete {count} selected Purchase Orders at once?\n\nIf any orders were Received, product stock levels will be reverted."

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt = PurchaseOrderModel.delete_many(ids)
                self.refresh_data()
                if count == 1:
                    messagebox.showinfo("Success", f"Purchase Order #{selected_items[0].get('po_number')} deleted successfully!", parent=self)
                else:
                    messagebox.showinfo("Success", f"{deleted_cnt} Purchase Orders deleted successfully!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete purchase order(s): {str(ex)}", parent=self)

