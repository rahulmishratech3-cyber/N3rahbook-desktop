"""
Sales Orders & GST Tax Invoices View Screen
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.sales_order import SalesOrderModel
from models.contact import ContactModel
from services.pdf_service import generate_tax_invoice_pdf
from ui.components.data_table import DataTable
from ui.components.invoice_dialog import InvoiceDialog
from ui.components.excel_import_dialog import ExcelImportDialog

class SalesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="📄 Sales Orders & Tax Invoices", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        # Right Action Buttons
        ttk.Button(ctrl_bar, text="🗑️ Delete Invoice", style="Secondary.TButton", command=self._delete_selected_invoice).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="🚫 Cancel Invoice", style="Secondary.TButton", command=self._cancel_selected_invoice).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="🖨️ Export PDF", style="Secondary.TButton", command=self._export_selected_pdf).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="✏️ Edit Invoice", style="Secondary.TButton", command=self._edit_selected_invoice).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="❌ Mark as Unpaid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(False)).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="✅ Mark as Paid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(True)).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="📥 Import Excel", style="Secondary.TButton", command=self._import_excel).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="➕ Create Tax Invoice", style="Primary.TButton", command=self._new_invoice).pack(side="right", padx=3)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("invoice_number", "Invoice No.", 110, "center"),
            ("invoice_date", "Invoice Date", 100, "center"),
            ("customer_name", "Customer Name", 180, "w"),
            ("company_name", "Company", 180, "w"),
            ("vehicle_no", "Vehicle No.", 90, "center"),
            ("eway_bill_no", "E-Way Bill No.", 110, "center"),
            ("total_amount", "Total Amount (₹)", 120, "e"),
            ("status_display", "Payment Status", 110, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_selected_invoice)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_data(self):
        orders = SalesOrderModel.get_all()
        display_orders = []
        for o in orders:
            row = dict(o)
            row['total_amount'] = f"₹ {o['total_amount']:,.2f}"
            
            pay_st = str(o.get('payment_status') or '').strip()
            st = str(o.get('status') or '').strip()

            if st.lower() == 'cancelled' or pay_st.lower() == 'cancelled':
                row['status_display'] = "CANCELLED"
                row['row_tag'] = "cancelled"
            elif pay_st.lower() == 'unpaid' or (not pay_st and st.lower() in ('unpaid', 'draft', 'pending')):
                row['status_display'] = "UNPAID"
                row['row_tag'] = "unpaid"
            elif pay_st.lower() == 'paid' or st.lower() in ('paid', 'confirmed', 'shipped'):
                row['status_display'] = "PAID"
                row['row_tag'] = "paid"
            else:
                row['status_display'] = pay_st.upper() if pay_st else st.upper()
                row['row_tag'] = "even"

            display_orders.append(row)

        self.table.load_data(display_orders)

    def _cancel_selected_invoice(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more invoices from the table to cancel.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            inv_num = selected_items[0].get('invoice_number', '')
            msg = f"Are you sure you want to mark Invoice #{inv_num} as CANCELLED?\n\nThis will restore the deducted product stock back to inventory."
        else:
            msg = f"Are you sure you want to mark {count} selected invoices as CANCELLED?\n\nThis will restore the deducted product stock back to inventory."

        if not messagebox.askyesno("Confirm Invoice Cancellation", msg, parent=self):
            return

        ids = [item['id'] for item in selected_items]
        for oid in ids:
            SalesOrderModel.update_status(oid, 'Cancelled')

        self.refresh_data()
        if count == 1:
            inv_num = selected_items[0].get('invoice_number', '')
            messagebox.showinfo("Invoice Cancelled", f"Invoice #{inv_num} marked as CANCELLED and stock restored successfully!", parent=self)
        else:
            messagebox.showinfo("Invoices Cancelled", f"{count} invoices marked as CANCELLED and stock restored successfully!", parent=self)

    def _mark_selected_paid(self, is_paid=True):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more invoices from the table.", parent=self)
            return

        new_status = "Paid" if is_paid else "Unpaid"
        status_label = "PAID" if is_paid else "UNPAID"

        ids = [item['id'] for item in selected_items]
        for oid in ids:
            SalesOrderModel.update_status(oid, new_status)

        self.refresh_data()
        count = len(ids)
        if count == 1:
            inv_num = selected_items[0].get('invoice_number', '')
            messagebox.showinfo("Status Updated", f"Invoice #{inv_num} marked as {status_label} successfully!", parent=self)
        else:
            messagebox.showinfo("Status Updated", f"{count} invoices marked as {status_label} successfully!", parent=self)

    def _new_invoice(self):
        InvoiceDialog(self, on_save=self.refresh_data)

    def _edit_selected_invoice(self, order_row=None):
        selected = order_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an invoice from the table.", parent=self)
            return

        InvoiceDialog(self, order_id=selected['id'], on_save=self.refresh_data)

    def _delete_selected_invoice(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more invoices to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            inv_num = selected_items[0].get('invoice_number', 'this invoice')
            msg = f"Are you sure you want to permanently delete Invoice #{inv_num}?\n\nThis will remove the record and restore product stock levels."
        else:
            msg = f"Are you sure you want to permanently delete {count} selected invoices at once?\n\nThis will remove all selected invoice records and restore product stock levels."

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt = SalesOrderModel.delete_many(ids)
                self.refresh_data()
                if count == 1:
                    messagebox.showinfo("Success", f"Invoice #{selected_items[0].get('invoice_number')} deleted successfully!", parent=self)
                else:
                    messagebox.showinfo("Success", f"{deleted_cnt} invoices deleted successfully and inventory stock restored!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete invoice(s): {str(ex)}", parent=self)


    def _export_selected_pdf(self):
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an invoice to export as PDF.", parent=self)
            return

        order = SalesOrderModel.get_by_id(selected['id'])
        if not order:
            return

        customer = ContactModel.get_by_id(order['customer_id']) or {}

        try:
            pdf_path = generate_tax_invoice_pdf(
                order=order,
                customer=customer,
                items=order.get('items', []),
                page_size="A4",
                copy_type="ORIGINAL FOR RECIPIENT"
            )

            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path])

            messagebox.showinfo("PDF Generated", f"Generated Tax Invoice PDF:\n{pdf_path}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(ex)}", parent=self)

    def _import_excel(self):
        ExcelImportDialog(self, default_type="sales", on_success=self.refresh_data)
