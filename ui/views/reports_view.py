"""
Reports & Analytics View Screen with Excel and CSV Export
Supports GSTR-1 Sales Invoices, GSTR-2 Inward Purchases, GSTR-3B Net GST Summary, Stock In/Out Movement, and HSN Tax Reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from datetime import datetime
from config import COLORS, FONTS
from models.report import ReportModel
from services.export_service import export_to_csv, export_to_excel
from ui.components.data_table import DataTable

class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=10)

        # Top Row: Title + General Actions
        row_top = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_top.pack(fill="x", pady=(0, 8))

        tk.Label(row_top, text="📈 Reports & GST Analytics Center", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        ttk.Button(row_top, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_data).pack(side="right", padx=3)
        ttk.Button(row_top, text="📄 Export CSV", style="Secondary.TButton", command=self._export_csv).pack(side="right", padx=3)
        ttk.Button(row_top, text="📊 Export Tab (.xlsx)", style="Secondary.TButton", command=self._export_excel).pack(side="right", padx=3)

        # Bottom Row: Year/Month Filters + GSTR Download Buttons
        row_sub = tk.Frame(ctrl_bar, bg=COLORS["bg_card"])
        row_sub.pack(fill="x")

        self.month_var = StringVar(value="All")
        self.year_var = StringVar(value=str(datetime.now().year))
        
        tk.Label(row_sub, text="Year:", bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left", padx=(0, 4))
        year_cb = ttk.Combobox(row_sub, textvariable=self.year_var, values=["All", "2024", "2025", "2026", "2027"], width=6, state="readonly")
        year_cb.pack(side="left", padx=(0, 8))
        
        tk.Label(row_sub, text="Month:", bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left", padx=(0, 4))
        month_cb = ttk.Combobox(row_sub, textvariable=self.month_var, values=["All", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], width=5, state="readonly")
        month_cb.pack(side="left", padx=(0, 8))
        
        ttk.Button(row_sub, text="Apply Filter", style="Primary.TButton", command=self.refresh_data).pack(side="left", padx=5)

        ttk.Button(row_sub, text="📥 Download GSTR-2 Purchase (.xlsx)", style="Primary.TButton", command=self._export_gstr2_excel).pack(side="right", padx=3)
        ttk.Button(row_sub, text="📥 Download GSTR-1 (.xlsx)", style="Success.TButton", command=self._export_gstr1_excel).pack(side="right", padx=3)

        # Tabbed container
        notebook_container = tk.Frame(self, bg=COLORS["bg_dark"])
        notebook_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.notebook = ttk.Notebook(notebook_container)
        self.notebook.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 1: GSTR-1 Detailed Itemized Sales Report
        # ----------------------------------------------------
        tab_gstr1 = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_gstr1, text=" 📑 GSTR-1 Sales Report ")

        gstr1_cols = [
            ("sno", "S.No", 45, "center"),
            ("item_name", "Description of Product", 180, "w"),
            ("hsn_code", "HSN CODE", 95, "center"),
            ("quantity_display", "Quantity", 90, "center"),
            ("assessable_display", "Assessable Value (₹)", 125, "e"),
            ("cgst_display", "CGST (₹)", 90, "e"),
            ("sgst_display", "SGST (₹)", 90, "e"),
            ("igst_display", "IGST (₹)", 75, "e"),
            ("round_off_display", "Roundoff", 75, "e"),
            ("invoice_number", "Invoice No", 105, "center"),
            ("invoice_date", "Invoice Date", 95, "center"),
            ("eway_bill_no", "E-Way Bill Number", 130, "center")
        ]
        self.gstr1_table = DataTable(tab_gstr1, gstr1_cols)
        self.gstr1_table.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 2: GSTR-2 Detailed Itemized Purchase Report
        # ----------------------------------------------------
        tab_gstr2 = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_gstr2, text=" 🛒 GSTR-2 Purchase Report ")

        gstr2_cols = [
            ("sno", "S.No", 45, "center"),
            ("item_name", "Description of Product", 170, "w"),
            ("subcategory", "Grade / Subcategory", 110, "w"),
            ("hsn_code", "HSN CODE", 90, "center"),
            ("quantity_display", "Quantity", 90, "center"),
            ("assessable_display", "Taxable Value (₹)", 120, "e"),
            ("cgst_display", "CGST (₹)", 85, "e"),
            ("sgst_display", "SGST (₹)", 85, "e"),
            ("igst_display", "IGST (₹)", 85, "e"),
            ("invoice_number", "Bill / PO No", 105, "center"),
            ("invoice_date", "Purchase Date", 95, "center"),
            ("supplier_name", "Supplier / Vendor Name", 160, "w"),
            ("supplier_gstin", "Supplier GSTIN", 120, "center")
        ]
        self.gstr2_table = DataTable(tab_gstr2, gstr2_cols)
        self.gstr2_table.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 3: GSTR-3B Tax Comparison (Sales vs Purchase ITC)
        # ----------------------------------------------------
        tab_gstr3b = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=15, pady=15)
        self.notebook.add(tab_gstr3b, text=" ⚖️ GSTR-3B Tax Summary (Sales vs Purchase) ")

        self.gstr3b_frame = tab_gstr3b
        self._build_gstr3b_tab()

        # ----------------------------------------------------
        # Tab 4: Sales Invoices Summary Report
        # ----------------------------------------------------
        tab_sales = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_sales, text=" 📄 Sales Invoices Summary ")

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
        # Tab 5: Purchase Bills Summary Report
        # ----------------------------------------------------
        tab_pur = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_pur, text=" 🚚 Purchase Bills Summary ")

        pur_cols = [
            ("po_number", "PO / Ref No.", 110, "center"),
            ("order_date", "Purchase Date", 100, "center"),
            ("supplier_name", "Supplier / Vendor", 180, "w"),
            ("company_name", "Company", 170, "w"),
            ("supplier_gstin", "GSTIN", 120, "center"),
            ("subtotal_display", "Taxable Cost (₹)", 120, "e"),
            ("tax_display", "GST Tax (₹)", 110, "e"),
            ("freight_display", "Freight (₹)", 90, "e"),
            ("total_display", "Grand Total (₹)", 120, "e"),
            ("status", "Status", 100, "center")
        ]
        self.pur_table = DataTable(tab_pur, pur_cols)
        self.pur_table.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # Tab 6: Stock Movement Report
        # ----------------------------------------------------
        tab_stock = tk.Frame(self.notebook, bg=COLORS["bg_card"], padx=10, pady=10)
        self.notebook.add(tab_stock, text=" 📦 Product Stock Movement ")

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
        # Tab 7: HSN / SAC GST Tax Summary
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

    def _build_gstr3b_tab(self):
        hdr_frame = tk.Frame(self.gstr3b_frame, bg=COLORS["bg_card"])
        hdr_frame.pack(fill="x", pady=(0, 10))

        tk.Label(hdr_frame, text="⚖️ GSTR-3B Tax Liability & Input Tax Credit (ITC) Computation", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w")
        tk.Label(hdr_frame, text="Automatic reconciliation of Sales Tax Collected vs Purchase Input Tax Credit Paid", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 0))

        # 3 Comparison Summary Cards
        cards_row = tk.Frame(self.gstr3b_frame, bg=COLORS["bg_card"])
        cards_row.pack(fill="x", pady=(0, 15))

        # Card 1: Sales Output Tax
        c1 = tk.Frame(cards_row, bg=COLORS["bg_card_alt"], bd=1, relief="flat", highlightbackground=COLORS["primary"], highlightthickness=1, padx=14, pady=12)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Label(c1, text="📈 Outward Supplies (Sales Tax)", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["primary"]).pack(anchor="w")
        self.lbl_sales_taxable = tk.Label(c1, text="Taxable Value: ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_sales_taxable.pack(anchor="w", pady=(4, 1))
        self.lbl_sales_cgst = tk.Label(c1, text="CGST (9%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_sales_cgst.pack(anchor="w")
        self.lbl_sales_sgst = tk.Label(c1, text="SGST (9%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_sales_sgst.pack(anchor="w")
        self.lbl_sales_igst = tk.Label(c1, text="IGST (18%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_sales_igst.pack(anchor="w")
        self.lbl_sales_tot_tax = tk.Label(c1, text="Total Output GST: ₹ 0.00", font=FONTS["heading"], bg=COLORS["bg_card_alt"], fg=COLORS["primary"])
        self.lbl_sales_tot_tax.pack(anchor="w", pady=(6, 0))

        # Card 2: Purchase Input Tax Credit
        c2 = tk.Frame(cards_row, bg=COLORS["bg_card_alt"], bd=1, relief="flat", highlightbackground=COLORS["accent"], highlightthickness=1, padx=14, pady=12)
        c2.pack(side="left", fill="both", expand=True, padx=3)
        tk.Label(c2, text="📉 Inward Supplies (Purchase ITC)", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["accent"]).pack(anchor="w")
        self.lbl_pur_taxable = tk.Label(c2, text="Taxable Value: ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_pur_taxable.pack(anchor="w", pady=(4, 1))
        self.lbl_pur_cgst = tk.Label(c2, text="CGST (9%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_pur_cgst.pack(anchor="w")
        self.lbl_pur_sgst = tk.Label(c2, text="SGST (9%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_pur_sgst.pack(anchor="w")
        self.lbl_pur_igst = tk.Label(c2, text="IGST (18%): ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_pur_igst.pack(anchor="w")
        self.lbl_pur_tot_tax = tk.Label(c2, text="Total Input ITC: ₹ 0.00", font=FONTS["heading"], bg=COLORS["bg_card_alt"], fg=COLORS["accent"])
        self.lbl_pur_tot_tax.pack(anchor="w", pady=(6, 0))

        # Card 3: Net GST Payable / (Credit Balance)
        c3 = tk.Frame(cards_row, bg=COLORS["bg_card_alt"], bd=1, relief="flat", highlightbackground=COLORS["success"], highlightthickness=1, padx=14, pady=12)
        c3.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.lbl_net_title = tk.Label(c3, text="💰 Net GST Payable / ITC", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["success"])
        self.lbl_net_title.pack(anchor="w")
        self.lbl_net_cgst = tk.Label(c3, text="Net CGST: ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_net_cgst.pack(anchor="w", pady=(4, 1))
        self.lbl_net_sgst = tk.Label(c3, text="Net SGST: ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_net_sgst.pack(anchor="w")
        self.lbl_net_igst = tk.Label(c3, text="Net IGST: ₹ 0.00", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.lbl_net_igst.pack(anchor="w")
        self.lbl_net_tot = tk.Label(c3, text="Net Payable: ₹ 0.00", font=FONTS["heading"], bg=COLORS["bg_card_alt"], fg=COLORS["success"])
        self.lbl_net_tot.pack(anchor="w", pady=(6, 0))

        # Detailed breakdown table
        tbl_box = tk.Frame(self.gstr3b_frame, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        tbl_box.pack(fill="both", expand=True)

        gstr3b_cols = [
            ("component", "GST Component / Head", 220, "w"),
            ("taxable_val", "Taxable Subtotal (₹)", 140, "e"),
            ("cgst_val", "CGST (₹)", 110, "e"),
            ("sgst_val", "SGST (₹)", 110, "e"),
            ("igst_val", "IGST (₹)", 110, "e"),
            ("total_val", "Total Tax / Amount (₹)", 160, "e")
        ]
        self.gstr3b_table = DataTable(tbl_box, gstr3b_cols)
        self.gstr3b_table.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_data(self):
        m = self.month_var.get()
        y = self.year_var.get()
        month = m if m != "All" else None
        year = y if y != "All" else None

        # 1. Load GSTR-1 Sales Report
        gstr1_rows = ReportModel.get_gstr1_report(month=month, year=year)
        display_gstr1 = []
        for idx, r in enumerate(gstr1_rows, start=1):
            row = dict(r)
            row['sno'] = str(idx)
            row['quantity_display'] = f"{r['quantity']:g} {r.get('unit', 'PCS')}"
            row['assessable_display'] = f"₹ {r['assessable_value']:,.2f}"
            row['cgst_display'] = f"₹ {r['cgst_amount']:,.2f}"
            row['sgst_display'] = f"₹ {r['sgst_amount']:,.2f}"
            row['igst_display'] = f"₹ {r['igst_amount']:,.2f}"
            row['round_off_display'] = f"{r['round_off']:+.2f}" if r['round_off'] != 0 else "0.00"
            display_gstr1.append(row)
        self.gstr1_table.load_data(display_gstr1)

        # 2. Load GSTR-2 Purchase Report
        gstr2_rows = ReportModel.get_gstr2_purchase_report(month=month, year=year)
        display_gstr2 = []
        for idx, r in enumerate(gstr2_rows, start=1):
            row = dict(r)
            row['sno'] = str(idx)
            row['quantity_display'] = f"{r['quantity']:g} {r.get('unit', 'PCS')}"
            row['assessable_display'] = f"₹ {r['assessable_value']:,.2f}"
            row['cgst_display'] = f"₹ {r['cgst_amount']:,.2f}"
            row['sgst_display'] = f"₹ {r['sgst_amount']:,.2f}"
            row['igst_display'] = f"₹ {r['igst_amount']:,.2f}"
            display_gstr2.append(row)
        self.gstr2_table.load_data(display_gstr2)

        # 3. Load GSTR-3B Tax Summary
        s3b = ReportModel.get_gstr3b_summary(month=month, year=year)
        sales_s = s3b['sales']
        pur_s = s3b['purchases']

        self.lbl_sales_taxable.config(text=f"Taxable Value: ₹ {sales_s['total_taxable']:,.2f}")
        self.lbl_sales_cgst.config(text=f"CGST (9%): ₹ {sales_s['total_cgst']:,.2f}")
        self.lbl_sales_sgst.config(text=f"SGST (9%): ₹ {sales_s['total_sgst']:,.2f}")
        self.lbl_sales_igst.config(text=f"IGST (18%): ₹ {sales_s.get('total_igst', 0.0):,.2f}")
        self.lbl_sales_tot_tax.config(text=f"Output GST: ₹ {s3b['sales_tax']:,.2f}")

        self.lbl_pur_taxable.config(text=f"Taxable Value: ₹ {pur_s['total_taxable']:,.2f}")
        self.lbl_pur_cgst.config(text=f"CGST (9%): ₹ {pur_s['total_cgst']:,.2f}")
        self.lbl_pur_sgst.config(text=f"SGST (9%): ₹ {pur_s['total_sgst']:,.2f}")
        self.lbl_pur_igst.config(text=f"IGST (18%): ₹ {pur_s.get('total_igst', 0.0):,.2f}")
        self.lbl_pur_tot_tax.config(text=f"Input ITC: ₹ {s3b['purchase_itc']:,.2f}")

        net_val = s3b['net_tax']
        if net_val >= 0:
            self.lbl_net_title.config(text="💰 Net GST Payable", fg=COLORS["warning"])
            self.lbl_net_tot.config(text=f"Payable: ₹ {net_val:,.2f}", fg=COLORS["warning"])
        else:
            self.lbl_net_title.config(text="✨ Net ITC Credit Balance", fg=COLORS["success"])
            self.lbl_net_tot.config(text=f"ITC Balance: ₹ {abs(net_val):,.2f}", fg=COLORS["success"])

        self.lbl_net_cgst.config(text=f"Net CGST: ₹ {s3b['net_cgst']:,.2f}")
        self.lbl_net_sgst.config(text=f"Net SGST: ₹ {s3b['net_sgst']:,.2f}")
        self.lbl_net_igst.config(text=f"Net IGST: ₹ {s3b.get('net_igst', 0.0):,.2f}")

        gstr3b_rows = [
            {
                'component': '1. Outward Taxable Supplies (Sales)',
                'taxable_val': f"₹ {sales_s['total_taxable']:,.2f}",
                'cgst_val': f"₹ {sales_s['total_cgst']:,.2f}",
                'sgst_val': f"₹ {sales_s['total_sgst']:,.2f}",
                'igst_val': f"₹ {sales_s.get('total_igst', 0.0):,.2f}",
                'total_val': f"₹ {s3b['sales_tax']:,.2f}"
            },
            {
                'component': '2. Eligible Input Tax Credit (Purchases)',
                'taxable_val': f"₹ {pur_s['total_taxable']:,.2f}",
                'cgst_val': f"₹ {pur_s['total_cgst']:,.2f}",
                'sgst_val': f"₹ {pur_s['total_sgst']:,.2f}",
                'igst_val': f"₹ {pur_s.get('total_igst', 0.0):,.2f}",
                'total_val': f"₹ {s3b['purchase_itc']:,.2f}"
            },
            {
                'component': '3. NET GST TAX LIABILITY / (ITC CARRYOVER)',
                'taxable_val': f"₹ {(sales_s['total_taxable'] - pur_s['total_taxable']):,.2f}",
                'cgst_val': f"₹ {s3b['net_cgst']:,.2f}",
                'sgst_val': f"₹ {s3b['net_sgst']:,.2f}",
                'igst_val': f"₹ {s3b.get('net_igst', 0.0):,.2f}",
                'total_val': f"₹ {net_val:,.2f}"
            }
        ]
        self.gstr3b_table.load_data(gstr3b_rows)

        # 4. Load Sales Invoices Report
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

        # 5. Load Purchase Bills Report
        pur_rows = ReportModel.get_purchase_invoice_report()
        display_pur = []
        for p in pur_rows:
            row = dict(p)
            sub = float(p.get('subtotal', 0.0))
            tax = float(p.get('tax_amount', 0.0))
            fr = float(p.get('freight', 0.0))
            tot = float(p.get('total_amount', 0.0))

            row['subtotal_display'] = f"₹ {sub:,.2f}"
            row['tax_display'] = f"₹ {tax:,.2f}"
            row['freight_display'] = f"₹ {fr:,.2f}"
            row['total_display'] = f"₹ {tot:,.2f}"
            display_pur.append(row)
        self.pur_table.load_data(display_pur)

        # 6. Load Stock Movement Report
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

        # 7. Load HSN Tax Report
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

    def _export_gstr1_excel(self):
        """Dedicated 1-click exporter for GSTR-1 Sales Excel report."""
        try:
            m = self.month_var.get(); y = self.year_var.get()
            month = m if m != "All" else None; year = y if y != "All" else None
            rows = ReportModel.get_gstr1_report(month=month, year=year)
            headers = [
                "S.No",
                "Invoice Date",
                "Invoice No",
                "Party Name",
                "Party GST Number",
                "Description of Goods",
                "HSN CODE",
                "Quantity",
                "Ass. Value",
                "CGST",
                "SGST",
                "IGST",
                "Roundoff",
                "E-Way Bill Number"
            ]
            data = []
            for idx, r in enumerate(rows, start=1):
                data.append([
                    idx,
                    r['invoice_date'],
                    r['invoice_number'],
                    r['customer_name'] or r['company_name'],
                    r['customer_gstin'],
                    r['item_name'],
                    r['hsn_code'],
                    f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                    r['assessable_value'],
                    r['cgst_amount'],
                    r['sgst_amount'],
                    r['igst_amount'],
                    r['round_off'],
                    r['eway_bill_no']
                ])

            from datetime import datetime
            fname = f"GSTR1_Detailed_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            fpath = export_to_excel(fname, "GSTR-1 Details", headers, data)
            messagebox.showinfo("GSTR-1 Download Successful", f"GSTR-1 Sales Report downloaded successfully:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export GSTR-1 Report: {str(ex)}", parent=self)

    def _export_gstr2_excel(self):
        """Dedicated 1-click exporter for GSTR-2 Purchase / Inward Excel report."""
        try:
            m = self.month_var.get(); y = self.year_var.get()
            month = m if m != "All" else None; year = y if y != "All" else None
            rows = ReportModel.get_gstr2_purchase_report(month=month, year=year)
            headers = [
                "S.No",
                "Purchase Date",
                "Bill / PO No",
                "Party Name",
                "Party GST Number",
                "Description of Goods",
                "Grade / Subcategory",
                "HSN CODE",
                "Quantity",
                "Ass. Value",
                "CGST",
                "SGST",
                "IGST",
                "Roundoff",
                "Total Amount"
            ]
            data = []
            for idx, r in enumerate(rows, start=1):
                data.append([
                    idx,
                    r['invoice_date'],
                    r['invoice_number'],
                    r['supplier_name'] or r['company_name'],
                    r['supplier_gstin'],
                    r['item_name'],
                    r.get('subcategory', ''),
                    r['hsn_code'],
                    f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                    r['assessable_value'],
                    r['cgst_amount'],
                    r['sgst_amount'],
                    r['igst_amount'],
                    r['round_off'],
                    r['total_amount']
                ])

            from datetime import datetime
            fname = f"GSTR2_Purchase_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            fpath = export_to_excel(fname, "GSTR-2 Purchases", headers, data)
            messagebox.showinfo("GSTR-2 Download Successful", f"GSTR-2 Purchase Report downloaded successfully:\n{fpath}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to export GSTR-2 Report: {str(ex)}", parent=self)

    def _export_csv(self):
        tab_idx = self.notebook.index(self.notebook.select())
        try:
            m = self.month_var.get(); y = self.year_var.get()
            month = m if m != "All" else None; year = y if y != "All" else None
            
            if tab_idx == 0:
                rows = ReportModel.get_gstr1_report(month=month, year=year)
                headers = [
                    "S.no", "Description of Product", "HSN CODE", "quantity",
                    "Assessable value", "CGST", "SGST", "IGST", "Roundoff",
                    "Invoice no", "invoice date", "eway bbill number"
                ]
                data = [
                    [
                        idx, r['invoice_date'], r['invoice_number'], r['customer_name'] or r['company_name'], r['customer_gstin'],
                        r['item_name'], r['hsn_code'], f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                        r['assessable_value'], r['cgst_amount'], r['sgst_amount'], r['igst_amount'],
                        r['round_off'], r['eway_bill_no']
                    ]
                    for idx, r in enumerate(rows, start=1)
                ]
                fname = "GSTR1_Detailed_Report.csv"
            elif tab_idx == 1:
                rows = ReportModel.get_gstr2_purchase_report(month=month, year=year)
                headers = [
                    "S.no", "Purchase Date", "Bill / PO No", "Supplier Name", "Supplier GSTIN",
                    "Description of Product", "Grade", "HSN CODE", "quantity",
                    "Assessable value", "CGST", "SGST", "IGST", "Roundoff", "Total Amount"
                ]
                data = [
                    [
                        idx, r['invoice_date'], r['invoice_number'], r['supplier_name'] or r['company_name'], r['supplier_gstin'],
                        r['item_name'], r.get('subcategory', ''), r['hsn_code'], f"{r['quantity']:g} {r.get('unit', 'PCS')}",
                        r['assessable_value'], r['cgst_amount'], r['sgst_amount'], r['igst_amount'], r.get('round_off', 0.0), r['total_amount']
                    ]
                    for idx, r in enumerate(rows, start=1)
                ]
                fname = "GSTR2_Purchase_Report.csv"
            elif tab_idx == 2:
                s3b = ReportModel.get_gstr3b_summary(month=month, year=year)
                headers = ["Component", "Taxable Value (INR)", "CGST (INR)", "SGST (INR)", "IGST (INR)", "Total GST (INR)"]
                data = [
                    ["1. Outward Supplies (Sales)", s3b['sales']['total_taxable'], s3b['sales']['total_cgst'], s3b['sales']['total_sgst'], s3b['sales'].get('total_igst', 0.0), s3b['sales_tax']],
                    ["2. Inward Supplies (Purchases ITC)", s3b['purchases']['total_taxable'], s3b['purchases']['total_cgst'], s3b['purchases']['total_sgst'], s3b['purchases'].get('total_igst', 0.0), s3b['purchase_itc']],
                    ["3. Net GST Liability / (ITC Balance)", s3b['sales']['total_taxable'] - s3b['purchases']['total_taxable'], s3b['net_cgst'], s3b['net_sgst'], s3b.get('net_igst', 0.0), s3b['net_tax']]
                ]
                fname = "GSTR3B_Tax_Summary.csv"
            elif tab_idx == 3:
                rows = ReportModel.get_sales_invoice_report()
                headers = ["Invoice No.", "Invoice Date", "Customer Name", "Company", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Payment Status"]
                data = [[r['invoice_number'], r['invoice_date'], r['customer_name'], r['company_name'], r['subtotal'], r['freight'], r['tax_amount'], r['total_amount'], r['payment_status']] for r in rows]
                fname = "Sales_Invoices_Report.csv"
            elif tab_idx == 4:
                rows = ReportModel.get_purchase_invoice_report()
                headers = ["PO / Bill No.", "Purchase Date", "Supplier Name", "Company", "GSTIN", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Status"]
                data = [[r['po_number'], r['order_date'], r['supplier_name'], r['company_name'], r['supplier_gstin'], r['subtotal'], r.get('freight', 0.0), r['tax_amount'], r['total_amount'], r['status']] for r in rows]
                fname = "Purchase_Bills_Report.csv"
            elif tab_idx == 5:
                rows = ReportModel.get_stock_movement_report()
                headers = ["SKU Code", "Product Name", "Category", "Unit", "Total Inwards (+)", "Total Invoiced Outwards (-)", "Current Stock", "Reorder Level"]
                data = [[r['sku'], r['item_name'], r['category'], r['unit'], r['total_inwards'], r['total_outwards'], r['current_stock'], r['reorder_level']] for r in rows]
                fname = "Stock_Movement_Report.csv"
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
            m = self.month_var.get(); y = self.year_var.get()
            month = m if m != "All" else None; year = y if y != "All" else None
            
            if tab_idx == 0:
                self._export_gstr1_excel()
                return
            elif tab_idx == 1:
                self._export_gstr2_excel()
                return
            elif tab_idx == 2:
                s3b = ReportModel.get_gstr3b_summary(month=month, year=year)
                headers = ["Component", "Taxable Value (INR)", "CGST (INR)", "SGST (INR)", "IGST (INR)", "Total GST (INR)"]
                data = [
                    ["1. Outward Supplies (Sales)", s3b['sales']['total_taxable'], s3b['sales']['total_cgst'], s3b['sales']['total_sgst'], s3b['sales'].get('total_igst', 0.0), s3b['sales_tax']],
                    ["2. Inward Supplies (Purchases ITC)", s3b['purchases']['total_taxable'], s3b['purchases']['total_cgst'], s3b['purchases']['total_sgst'], s3b['purchases'].get('total_igst', 0.0), s3b['purchase_itc']],
                    ["3. Net GST Liability / (ITC Balance)", s3b['sales']['total_taxable'] - s3b['purchases']['total_taxable'], s3b['net_cgst'], s3b['net_sgst'], s3b.get('net_igst', 0.0), s3b['net_tax']]
                ]
                fname = "GSTR3B_Tax_Summary.xlsx"
                sheet = "GSTR-3B Summary"
            elif tab_idx == 3:
                rows = ReportModel.get_sales_invoice_report()
                headers = ["Invoice No.", "Invoice Date", "Customer Name", "Company", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Payment Status"]
                data = [[r['invoice_number'], r['invoice_date'], r['customer_name'], r['company_name'], r['subtotal'], r['freight'], r['tax_amount'], r['total_amount'], r['payment_status']] for r in rows]
                fname = "Sales_Invoices_Report.xlsx"
                sheet = "Sales Invoices"
            elif tab_idx == 4:
                rows = ReportModel.get_purchase_invoice_report()
                headers = ["PO / Bill No.", "Purchase Date", "Supplier Name", "Company", "GSTIN", "Taxable Subtotal (INR)", "Freight (INR)", "GST Tax (INR)", "Grand Total (INR)", "Status"]
                data = [[r['po_number'], r['order_date'], r['supplier_name'], r['company_name'], r['supplier_gstin'], r['subtotal'], r.get('freight', 0.0), r['tax_amount'], r['total_amount'], r['status']] for r in rows]
                fname = "Purchase_Bills_Report.xlsx"
                sheet = "Purchase Bills"
            elif tab_idx == 5:
                rows = ReportModel.get_stock_movement_report()
                headers = ["SKU Code", "Product Name", "Category", "Unit", "Total Inwards (+)", "Total Invoiced Outwards (-)", "Current Stock", "Reorder Level"]
                data = [[r['sku'], r['item_name'], r['category'], r['unit'], r['total_inwards'], r['total_outwards'], r['current_stock'], r['reorder_level']] for r in rows]
                fname = "Stock_Movement_Report.xlsx"
                sheet = "Stock Movement"
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


