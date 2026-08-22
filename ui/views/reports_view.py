"""
Reports & Analytics View Screen with Excel and CSV Export
Supports Stock In/Out Movement, Sales Invoices Summary, and HSN GST Tax Reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.report import ReportModel
from models.item import ItemModel
from services.export_service import export_to_csv, export_to_excel
from ui.components.data_table import DataTable

class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="📈 Reports & GST Analytics Center", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        ttk.Button(ctrl_bar, text="📊 Export Excel (.xlsx)", style="Success.TButton", command=self._export_excel).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="📄 Export CSV", style="Secondary.TButton", command=self._export_csv).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_data).pack(side="right", padx=4)

        # Tabbed container
        notebook_container = tk.Frame(self, bg=COLORS["bg_dark"])
        notebook_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.notebook = ttk.Notebook(notebook_container)
        self.notebook.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 1: Stock In/Out & Movement Report
        # ----------------------------------------------------
        tab_stock = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_stock, text=" 📦 Product Stock Movement (In/Out) ")

        stock_cols = [
            ("sku", "SKU Code", 100, "center"),
            ("item_name", "Product Name", 240, "w"),
            ("category", "Category", 140, "w"),
            ("unit", "Unit", 70, "center"),
            ("inwards_display", "Total Added (Inwards)", 140, "center"),
            ("outwards_display", "Total Invoiced (Outwards)", 140, "center"),
            ("current_stock_display", "Available Stock", 120, "center"),
            ("status_display", "Stock Health", 120, "center")
        ]
        self.stock_table = DataTable(tab_stock, stock_cols)
        self.stock_table.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 2: Sales Invoices Summary Report
        # ----------------------------------------------------
        tab_sales = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_sales, text=" 📄 Sales Invoices & Collections ")

        sales_cols = [
            ("invoice_number", "Invoice No.", 110, "center"),
            ("invoice_date", "Invoice Date", 100, "center"),
            ("customer_name", "Customer Name", 180, "w"),
            ("company_name", "Company", 180, "w"),
            ("subtotal_display", "Taxable Amt (₹)", 120, "e"),
            ("tax_display", "GST Tax (₹)", 110, "e"),
            ("freight_display", "Freight (₹)", 90, "e"),
            ("total_display", "Grand Total (₹)", 120, "e"),
            ("payment_status_display", "Payment Status", 110, "center")
        ]
        self.sales_table = DataTable(tab_sales, sales_cols)
        self.sales_table.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 3: HSN / SAC GST Tax Summary
        # ----------------------------------------------------
        tab_hsn = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_hsn, text=" 🏛️ HSN / SAC GST Tax Summary ")

        hsn_cols = [
            ("hsn_code", "HSN / SAC Code", 140, "center"),
            ("taxable_value", "Taxable Value (₹)", 180, "e"),
            ("cgst_amount", "CGST Amount (₹)", 160, "e"),
            ("sgst_amount", "SGST Amount (₹)", 160, "e"),
            ("total_tax", "Total Tax Payable (₹)", 180, "e")
        ]
        self.hsn_table = DataTable(tab_hsn, hsn_cols)
        self.hsn_table.pack(fill="both", expand=True)

    def refresh_data(self):
        # 1. Load Stock Movement Report
        stock_rows = ReportModel.get_stock_movement_report()
        display_stock = []
        for r in stock_rows:
            row = dict(r)
            tin = round(float(r.get('total_inwards', 0.0)), 2)
            tout = round(float(r.get('total_outwards', 0.0)), 2)
            cur = round(float(r.get('current_stock', 0.0)), 2)
            reorder = round(float(r.get('reorder_level', 0.0)), 2)

            row['inwards_display'] = f"+{tin:g}"
            row['outwards_display'] = f"-{tout:g}"
            row['current_stock_display'] = f"{cur:g}"

            if cur <= 0:
                row['status_display'] = "OUT OF STOCK"
                row['row_tag'] = "unpaid"
            elif cur <= reorder:
                row['status_display'] = "LOW STOCK"
                row['row_tag'] = "low_stock"
            else:
                row['status_display'] = "IN STOCK"
                row['row_tag'] = "paid"

            display_stock.append(row)
        self.stock_table.load_data(display_stock)

        # 2. Load Sales Invoices Report
        sales_rows = ReportModel.get_sales_invoice_report()
        display_sales = []
        for s in sales_rows:
            row = dict(s)
            sub = float(s.get('subtotal', 0.0))
            tax = float(s.get('tax_amount', 0.0))
            fr = float(s.get('freight', 0.0))
            tot = float(s.get('total_amount', 0.0))

            row['subtotal_display'] = f"₹ {sub:,.2f}"
            row['tax_display'] = f"₹ {tax:,.2f}"
            row['freight_display'] = f"₹ {fr:,.2f}"
            row['total_display'] = f"₹ {tot:,.2f}"

            pst = str(s.get('payment_status', 'Paid')).strip()
            if pst.lower() == 'unpaid' or s.get('status') in ('Draft', 'Pending'):
                row['payment_status_display'] = "UNPAID"
                row['row_tag'] = "unpaid"
            elif pst.lower() == 'paid' or s.get('status') in ('Paid', 'Confirmed', 'Shipped'):
                row['payment_status_display'] = "PAID"
                row['row_tag'] = "paid"
            elif s.get('status') == 'Cancelled':
                row['payment_status_display'] = "CANCELLED"
                row['row_tag'] = "cancelled"
            else:
                row['payment_status_display'] = pst.upper()

            display_sales.append(row)
        self.sales_table.load_data(display_sales)

        # 3. Load HSN Tax Report
        hsn_rows = ReportModel.get_hsn_tax_report()
        display_hsn = []
        for h in hsn_rows:
            row = dict(h)
            row['taxable_value'] = f"₹ {h['taxable_value']:,.2f}"
            row['cgst_amount'] = f"₹ {h['cgst_amount']:,.2f}"
            row['sgst_amount'] = f"₹ {h['sgst_amount']:,.2f}"
            row['total_tax'] = f"₹ {h['total_tax']:,.2f}"
            display_hsn.append(row)
        self.hsn_table.load_data(display_hsn)

    def _export_csv(self):
        tab_idx = self.notebook.index(self.notebook.select())
        try:
            if tab_idx == 0:
                rows = ReportModel.get_stock_movement_report()
                headers = ["SKU Code", "Product Name", "Category", "Unit", "Total Inwards (+)", "Total Invoiced Outwards (-)", "Current Stock", "Reorder Level"]
                data = [[r['sku'], r['item_name'], r['category'], r['unit'], r['total_inwards'], r['total_outwards'], r['current_stock'], r['reorder_level']] for r in rows]
                fname = "Stock_Movement_Report.csv"
            elif tab_idx == 1:
                rows = ReportModel.get_sales_invoice_report()
                headers = ["Invoice No.", "Invoice Date", "Customer Name", "Company", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Payment Status"]
                data = [[r['invoice_number'], r['invoice_date'], r['customer_name'], r['company_name'], r['subtotal'], r['freight'], r['tax_amount'], r['total_amount'], r['payment_status']] for r in rows]
                fname = "Sales_Invoices_Report.csv"
            else:
                rows = ReportModel.get_hsn_tax_report()
                headers = ["HSN/SAC Code", "Taxable Value (INR)", "CGST (INR)", "SGST (INR)", "Total Tax Payable (INR)"]
                data = [[r['hsn_code'], r['taxable_value'], r['cgst_amount'], r['sgst_amount'], r['total_tax']] for r in rows]
                fname = "HSN_GST_Tax_Report.csv"

            fpath = export_to_csv(fname, headers, data)
            messagebox.showinfo("Export Successful", f"Report exported to CSV:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export CSV: {str(ex)}", parent=self)

    def _export_excel(self):
        tab_idx = self.notebook.index(self.notebook.select())
        try:
            if tab_idx == 0:
                rows = ReportModel.get_stock_movement_report()
                headers = ["SKU Code", "Product Name", "Category", "Unit", "Total Inwards (+)", "Total Invoiced Outwards (-)", "Current Stock", "Reorder Level"]
                data = [[r['sku'], r['item_name'], r['category'], r['unit'], r['total_inwards'], r['total_outwards'], r['current_stock'], r['reorder_level']] for r in rows]
                fname = "Stock_Movement_Report.xlsx"
                sheet = "Stock Movement"
            elif tab_idx == 1:
                rows = ReportModel.get_sales_invoice_report()
                headers = ["Invoice No.", "Invoice Date", "Customer Name", "Company", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Payment Status"]
                data = [[r['invoice_number'], r['invoice_date'], r['customer_name'], r['company_name'], r['subtotal'], r['freight'], r['tax_amount'], r['total_amount'], r['payment_status']] for r in rows]
                fname = "Sales_Invoices_Report.xlsx"
                sheet = "Sales Invoices"
            else:
                rows = ReportModel.get_hsn_tax_report()
                headers = ["HSN/SAC Code", "Taxable Value (INR)", "CGST (INR)", "SGST (INR)", "Total Tax Payable (INR)"]
                data = [[r['hsn_code'], r['taxable_value'], r['cgst_amount'], r['sgst_amount'], r['total_tax']] for r in rows]
                fname = "HSN_GST_Tax_Report.xlsx"
                sheet = "HSN Tax Summary"

            fpath = export_to_excel(fname, sheet, headers, data)
            messagebox.showinfo("Export Successful", f"Report exported to Excel:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export Excel: {str(ex)}", parent=self)
