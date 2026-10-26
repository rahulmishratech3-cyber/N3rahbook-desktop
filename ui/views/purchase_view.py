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
        ctrl_bar.pack(fill="x", padx=20, pady=12)

        # Top Row: Title + Primary Action Buttons
        row_top = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_top.pack(fill="x", pady=(0, 8))

        tk.Label(row_top, text="🚚 Purchases & Supplier Replenishment", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        # Top Right Primary Buttons
        ttk.Button(row_top, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_selected_po).pack(side="right", padx=3)
        ttk.Button(row_top, text="📄 View / Print PDF", style="Primary.TButton", command=self._export_selected_pdf).pack(side="right", padx=3)
        ttk.Button(row_top, text="📥 Download GSTR-2 (.xlsx)", style="Success.TButton", command=self._export_gstr2_excel).pack(side="right", padx=3)
        ttk.Button(row_top, text="📋 Create PO (Pending)", style="Secondary.TButton", command=self._new_po_dialog).pack(side="right", padx=3)
        ttk.Button(row_top, text="🛒 Direct Purchase (Stock In)", style="Primary.TButton", command=self._direct_purchase_dialog).pack(side="right", padx=3)

        # Bottom Sub-Row: Search Filter + Management Buttons
        row_sub = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_sub.pack(fill="x")

        tk.Label(row_sub, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self.search_entry = ttk.Entry(row_sub, width=22)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_data())

        ttk.Button(row_sub, text="❌ Mark Unpaid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(False)).pack(side="right", padx=3)
        ttk.Button(row_sub, text="✅ Mark Paid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(True)).pack(side="right", padx=3)
        ttk.Button(row_sub, text="📦 Mark Received", style="Success.TButton", command=self._mark_received).pack(side="right", padx=3)
        ttk.Button(row_sub, text="✏️ Edit Purchase", style="Secondary.TButton", command=self._edit_selected_po).pack(side="right", padx=3)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("po_number", "PO / Ref No.", 130, "center"),
            ("order_date", "Purchase Date", 110, "center"),
            ("expected_date", "Expected Date", 110, "center"),
            ("supplier_name", "Vendor / Supplier Name", 220, "w"),
            ("company_name", "Company Name", 200, "w"),
            ("freight_display", "Freight (₹)", 100, "e"),
            ("total_amount", "Total Cost (₹)", 130, "e"),
            ("status", "Status", 110, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_selected_po)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self._all_display_pos = []

    def _filter_data(self):
        q = self.search_entry.get().strip().lower()
        if not q:
            self.table.load_data(self._all_display_pos)
            return
        filtered = [
            p for p in self._all_display_pos
            if q in str(p.get('po_number', '')).lower()
            or q in str(p.get('supplier_name', '')).lower()
            or q in str(p.get('company_name', '')).lower()
            or q in str(p.get('order_date', '')).lower()
            or q in str(p.get('status', '')).lower()
        ]
        self.table.load_data(filtered)

    def refresh_data(self):
        pos = PurchaseOrderModel.get_all()
        display_pos = []
        for p in pos:
            row = dict(p)
            fr = float(p.get('freight') or 0.0)
            row['freight_display'] = f"₹ {fr:,.2f}" if fr > 0 else "-"
            row['total_amount'] = f"₹ {p['total_amount']:,.2f}"
            pay_st = str(p.get('payment_status') or 'Unpaid').strip().upper()
            st = str(p.get('status') or '').strip().upper()
            row['status'] = f"{st} ({pay_st})"
            display_pos.append(row)
        self._all_display_pos = display_pos
        self._filter_data()

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

    def _mark_selected_paid(self, is_paid=True):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more Purchase Orders from the table.", parent=self)
            return

        status_label = "PAID" if is_paid else "UNPAID"
        ids = [item['id'] for item in selected_items]
        for pid in ids:
            PurchaseOrderModel.update_status(pid, payment_status="Paid" if is_paid else "Unpaid")

        self.refresh_data()
        count = len(ids)
        if count == 1:
            po_num = selected_items[0].get('po_number', '')
            messagebox.showinfo("Status Updated", f"Purchase Order #{po_num} marked as {status_label}. Vendor balance updated!", parent=self)
        else:
            messagebox.showinfo("Status Updated", f"{count} purchase orders marked as {status_label}. Vendor balances updated!", parent=self)


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

    def _export_selected_pdf(self):
        import os
        import subprocess
        from models.contact import ContactModel
        from services.pdf_service import generate_purchase_invoice_pdf
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Purchase Order from the table to export as PDF.", parent=self)
            return

        po = PurchaseOrderModel.get_by_id(selected['id'])
        if not po:
            return

        supplier = ContactModel.get_by_id(po['supplier_id']) or {}
        try:
            pdf_path = generate_purchase_invoice_pdf(
                po=po,
                supplier=supplier,
                items=po.get('items', []),
                page_size="A4"
            )

            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path])

            messagebox.showinfo("PDF Generated", f"Purchase Tax Invoice PDF generated successfully:\n{pdf_path}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate Purchase PDF: {str(ex)}", parent=self)

    def _export_gstr2_excel(self):
        from models.report import ReportModel
        from services.export_service import export_to_excel
        from datetime import datetime
        try:
            rows = ReportModel.get_gstr2_purchase_report()
            headers = [
                "S.no",
                "Description of Product",
                "Grade / Subcategory",
                "HSN CODE",
                "quantity",
                "Assessable value",
                "CGST",
                "SGST",
                "IGST",
                "Roundoff",
                "Bill / PO No",
                "Purchase Date",
                "Supplier Name",
                "Supplier GSTIN",
                "Total Amount"
            ]
            data = []
            for idx, r in enumerate(rows, start=1):
                data.append([
                    idx,
                    r['item_name'],
                    r.get('subcategory', ''),
                    r['hsn_code'],
                    f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                    r['assessable_value'],
                    r['cgst_amount'],
                    r['sgst_amount'],
                    r['igst_amount'],
                    r['round_off'],
                    r['invoice_number'],
                    r['invoice_date'],
                    r['supplier_name'],
                    r['supplier_gstin'],
                    r['total_amount']
                ])

            fname = f"GSTR2_Purchase_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            fpath = export_to_excel(fname, "GSTR-2 Purchases", headers, data)
            messagebox.showinfo("GSTR-2 Download Successful", f"GSTR-2 Purchase Report downloaded successfully:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export GSTR-2 Report: {str(ex)}", parent=self)



