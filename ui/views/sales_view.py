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
        ctrl_bar.pack(fill="x", padx=20, pady=12)

        # Top Row: Title + Primary Action Buttons
        row_top = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_top.pack(fill="x", pady=(0, 8))

        tk.Label(row_top, text="📄 Sales Orders & Tax Invoices", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        # Top Right Primary Action Buttons
        ttk.Button(row_top, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_selected_invoice).pack(side="right", padx=3)
        ttk.Button(row_top, text="🚫 Cancel", style="Secondary.TButton", command=self._cancel_selected_invoice).pack(side="right", padx=3)
        ttk.Button(row_top, text="📄 View / Print PDF", style="Primary.TButton", command=self._export_selected_pdf).pack(side="right", padx=3)
        ttk.Button(row_top, text="📥 Download All PDFs", style="Primary.TButton", command=self._export_all_pdfs).pack(side="right", padx=3)
        ttk.Button(row_top, text="📥 Download GSTR-1 (.xlsx)", style="Success.TButton", command=self._export_gstr1_excel).pack(side="right", padx=3)
        ttk.Button(row_top, text="➕ Create Tax Invoice", style="Primary.TButton", command=self._new_invoice).pack(side="right", padx=3)

        # Bottom Sub-Row: Search Filter + Secondary Management Buttons
        row_sub = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_sub.pack(fill="x")

        tk.Label(row_sub, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(0, 4))
        self.search_entry = ttk.Entry(row_sub, width=22)
        self.search_entry.pack(side="left", padx=4)
        
        self._filter_timer = None
        def _schedule_filter(event):
            if self._filter_timer:
                self.after_cancel(self._filter_timer)
            self._filter_timer = self.after(300, self._filter_data)

        self.search_entry.bind("<KeyRelease>", _schedule_filter)

        ttk.Button(row_sub, text="📥 Import Excel", style="Secondary.TButton", command=self._import_excel).pack(side="right", padx=3)
        ttk.Button(row_sub, text="❌ Mark as Unpaid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(False)).pack(side="right", padx=3)
        ttk.Button(row_sub, text="✅ Mark as Paid", style="Secondary.TButton", command=lambda: self._mark_selected_paid(True)).pack(side="right", padx=3)
        ttk.Button(row_sub, text="✏️ Edit Invoice", style="Secondary.TButton", command=self._edit_selected_invoice).pack(side="right", padx=3)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("invoice_number", "Invoice No.", 120, "center"),
            ("invoice_date", "Invoice Date", 100, "center"),
            ("customer_name", "Customer Name", 200, "w"),
            ("company_name", "Company Name", 200, "w"),
            ("po_number", "PO No.", 120, "center"),
            ("vehicle_no", "Vehicle No.", 100, "center"),
            ("eway_bill_no", "E-Way Bill No.", 130, "center"),
            ("total_amount", "Total Amount (₹)", 130, "e"),
            ("status_display", "Payment Status", 120, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_selected_invoice)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self._all_display_orders = []

    def _filter_data(self):
        q = self.search_entry.get().strip().lower()
        if not q:
            self.table.load_data(self._all_display_orders)
            return
        filtered = [
            o for o in self._all_display_orders
            if q in str(o.get('invoice_number', '')).lower()
            or q in str(o.get('customer_name', '')).lower()
            or q in str(o.get('company_name', '')).lower()
            or q in str(o.get('po_number', '')).lower()
            or q in str(o.get('vehicle_no', '')).lower()
            or q in str(o.get('eway_bill_no', '')).lower()
        ]
        self.table.load_data(filtered)

    def refresh_data(self):
        orders = SalesOrderModel.get_all()
        display_orders = []
        for o in orders:
            row = dict(o)
            row['total_amount'] = f"₹ {o['total_amount']:,.2f}"
            row['po_number'] = str(o.get('po_number') or '-').strip()
            
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

        self._all_display_orders = display_orders
        self._filter_data()

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
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more invoices to export as PDF.", parent=self)
            return

        generated_paths = []
        errors = []

        for selected in selected_items:
            order = SalesOrderModel.get_by_id(selected['id'])
            if not order:
                continue

            customer = ContactModel.get_by_id(order['customer_id']) or {}

            try:
                pdf_path = generate_tax_invoice_pdf(
                    order=order,
                    customer=customer,
                    items=order.get('items', []),
                    page_size="A4",
                    copy_type="4 COPIES (ORIGINAL + DUPLICATE + TRIPLICATE + EXTRA COPY)"
                )
                generated_paths.append(pdf_path)
            except Exception as ex:
                errors.append(f"Invoice #{selected.get('invoice_number', 'Unknown')}: {str(ex)}")

        if generated_paths:
            if len(generated_paths) <= 3:
                for pdf_path in generated_paths:
                    if os.name == 'nt':
                        os.startfile(pdf_path)
                    else:
                        subprocess.run(['xdg-open', pdf_path])
            else:
                dir_path = os.path.dirname(generated_paths[0])
                if os.name == 'nt':
                    os.startfile(dir_path)
                else:
                    subprocess.run(['xdg-open', dir_path])

            msg = f"Generated {len(generated_paths)} Tax Invoice PDF(s)."
            if errors:
                msg += f"\n\nErrors encountered:\n" + "\n".join(errors)
            messagebox.showinfo("PDF(s) Generated", msg, parent=self)
        elif errors:
            messagebox.showerror("Error", "Failed to generate PDFs:\n" + "\n".join(errors), parent=self)

    def _export_all_pdfs(self):
        if not self._all_display_orders:
            messagebox.showwarning("No Invoices", "There are no invoices to export.", parent=self)
            return

        confirm = messagebox.askyesno("Download All PDFs", f"Are you sure you want to download 'Triplicate for Supplier' PDFs for all {len(self._all_display_orders)} invoices in a single file?", parent=self)
        if not confirm:
            return

        orders_data = []
        errors = []

        for item in self._all_display_orders:
            order = SalesOrderModel.get_by_id(item['id'])
            if not order:
                continue

            customer = ContactModel.get_by_id(order['customer_id']) or {}
            items = order.get('items', [])
            orders_data.append((order, customer, items))

        if not orders_data:
            messagebox.showerror("Error", "Could not fetch details for any invoices.", parent=self)
            return

        try:
            from services.pdf_service import generate_bulk_tax_invoices_pdf
            pdf_path = generate_bulk_tax_invoices_pdf(
                orders_data=orders_data,
                page_size="A4",
                copy_type="TRIPLICATE FOR SUPPLIER"
            )
            
            if pdf_path:
                if os.name == 'nt':
                    os.startfile(pdf_path)
                else:
                    subprocess.run(['xdg-open', pdf_path])

                messagebox.showinfo("PDF Generated", f"Successfully generated a single PDF containing {len(orders_data)} invoices (Triplicate for Supplier).", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate bulk PDF:\n{str(ex)}", parent=self)

    def _import_excel(self):
        ExcelImportDialog(self, default_type="sales", on_success=self.refresh_data)

    def _export_gstr1_excel(self):
        from models.report import ReportModel
        from services.export_service import export_to_excel
        try:
            rows = ReportModel.get_gstr1_report()
            headers = [
                "S.no",
                "Description of Product",
                "HSN CODE",
                "quantity",
                "Assessable value",
                "CGST",
                "SGST",
                "IGST",
                "Roundoff",
                "Invoice no",
                "invoice date",
                "eway bbill number"
            ]
            data = []
            for idx, r in enumerate(rows, start=1):
                data.append([
                    idx,
                    r['item_name'],
                    r['hsn_code'],
                    f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                    r['assessable_value'],
                    r['cgst_amount'],
                    r['sgst_amount'],
                    r['igst_amount'],
                    r['round_off'],
                    r['invoice_number'],
                    r['invoice_date'],
                    r['eway_bill_no']
                ])

            from datetime import datetime
            fname = f"GSTR1_Detailed_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            fpath = export_to_excel(fname, "GSTR-1 Details", headers, data)
            messagebox.showinfo("GSTR-1 Download Successful", f"GSTR-1 Report downloaded successfully:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export GSTR-1 Report: {str(ex)}", parent=self)

