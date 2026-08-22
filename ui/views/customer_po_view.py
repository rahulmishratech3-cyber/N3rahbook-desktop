"""
Party Purchase Order (Customer PO) Hisaab & Balance Tracker View
Tracks Customer POs, Dispatches in KG, and Balance Pending Quantities/Amounts in real time.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONTS
from models.customer_po import CustomerPOModel
from models.contact import ContactModel
from ui.components.cards import KPICard
from ui.components.data_table import DataTable
from ui.components.customer_po_dialog import CustomerPODialog
from ui.components.po_dispatch_dialog import PODispatchDialog

class CustomerPOView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. Top KPI Summary Cards Row
        kpi_container = tk.Frame(self, bg=COLORS["bg_dark"])
        kpi_container.pack(fill="x", padx=20, pady=15)

        self.card_ordered = KPICard(kpi_container, "TOTAL ORDERED PO (KG)", "0.00 KG", "📦", "Customer PO Quantities", COLORS["primary"])
        self.card_ordered.pack(side="left", fill="both", expand=True, padx=5)

        self.card_dispatched = KPICard(kpi_container, "DISPATCHED QTY (KG)", "0.00 KG", "🚚", "Total Delivered to Parties", COLORS["success"])
        self.card_dispatched.pack(side="left", fill="both", expand=True, padx=5)

        self.card_balance = KPICard(kpi_container, "BALANCE PENDING QTY (KG)", "0.00 KG", "⚖️", "Remaining Delivery Target", COLORS["warning"])
        self.card_balance.pack(side="left", fill="both", expand=True, padx=5)

        self.card_bal_val = KPICard(kpi_container, "BALANCE PO VALUE (₹)", "₹ 0.00", "💰", "Unfulfilled Order Value", COLORS["accent"])
        self.card_bal_val.pack(side="left", fill="both", expand=True, padx=5)

        # 2. Control Bar (Filters & Action Buttons)
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=5)

        # Search box
        tk.Label(ctrl_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=4)
        self.search_entry = ttk.Entry(ctrl_bar, width=18)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_data())

        # Customer/Party Filter
        tk.Label(ctrl_bar, text="Party:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=6)
        self.cust_combo = ttk.Combobox(ctrl_bar, values=["All"], state="readonly", width=18)
        self.cust_combo.current(0)
        self.cust_combo.pack(side="left", padx=4)
        self.cust_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Status Filter
        tk.Label(ctrl_bar, text="Status:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=6)
        self.status_combo = ttk.Combobox(ctrl_bar, values=["All", "Open", "Partially Dispatched", "Completed"], state="readonly", width=16)
        self.status_combo.current(0)
        self.status_combo.pack(side="left", padx=4)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Right Action Buttons
        ttk.Button(ctrl_bar, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_selected).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="📜 View Hisaab", style="Secondary.TButton", command=self._view_hisaab_details).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="✏️ Edit PO", style="Secondary.TButton", command=self._edit_selected).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="🚚 Log Dispatch", style="Secondary.TButton", command=self._log_dispatch).pack(side="right", padx=3)
        ttk.Button(ctrl_bar, text="➕ New Party PO", style="Primary.TButton", command=self._add_po).pack(side="right", padx=3)

        # 3. Data Table Container
        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        cols = [
            ("po_number", "PO Reference #", 120, "center"),
            ("customer_name", "Party / Customer Name", 200, "w"),
            ("po_date", "PO Date", 100, "center"),
            ("total_ordered_qty_kg", "Ordered (KG)", 110, "center"),
            ("total_dispatched_qty_kg", "Dispatched (KG)", 110, "center"),
            ("balance_qty_kg", "Balance Pending (KG)", 140, "center"),
            ("total_po_amount", "Total PO Value (₹)", 120, "e"),
            ("balance_amount", "Balance Value (₹)", 120, "e"),
            ("status", "Status", 130, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._view_hisaab_details)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_data(self):
        # Update Party Combo List
        customers = ContactModel.get_all()
        self.customers_map = {f"{c['name']} ({c['company_name'] or 'Individual'})": c['id'] for c in customers}
        party_options = ["All"] + list(self.customers_map.keys())
        
        curr_party = self.cust_combo.get()
        self.cust_combo.config(values=party_options)
        if curr_party in party_options:
            self.cust_combo.set(curr_party)
        else:
            self.cust_combo.current(0)

        # Query Filters
        query = self.search_entry.get().strip()
        selected_party_txt = self.cust_combo.get()
        customer_id = self.customers_map.get(selected_party_txt, "All")
        status_filter = self.status_combo.get()

        # Update KPI Summary Cards
        summary = CustomerPOModel.get_summary()
        self.card_ordered.update_value(f"{summary['total_ordered_kg']:,.2f} KG")
        self.card_dispatched.update_value(f"{summary['total_dispatched_kg']:,.2f} KG")
        self.card_balance.update_value(f"{summary['total_balance_kg']:,.2f} KG")
        self.card_bal_val.update_value(f"₹ {summary['total_balance_value']:,.2f}")

        # Fetch POs
        pos = CustomerPOModel.get_all(query=query, customer_id=customer_id, status_filter=status_filter)

        formatted_rows = []
        for p in pos:
            row = dict(p)
            row['total_ordered_qty_kg'] = f"{p['total_ordered_qty_kg']:,.2f} KG"
            row['total_dispatched_qty_kg'] = f"{p['total_dispatched_qty_kg']:,.2f} KG"
            row['balance_qty_kg'] = f"⚖️ {p['balance_qty_kg']:,.2f} KG"
            row['total_po_amount'] = f"₹ {p['total_po_amount']:,.2f}"
            row['balance_amount'] = f"₹ {p['balance_amount']:,.2f}"
            formatted_rows.append(row)

        self.table.load_data(formatted_rows)

    def _add_po(self):
        CustomerPODialog(self, on_save=self.refresh_data)

    def _edit_selected(self):
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Party PO from the table to edit.", parent=self)
            return

        po = CustomerPOModel.get_by_id(selected['id'])
        if po:
            CustomerPODialog(self, po_data=po, on_save=self.refresh_data)

    def _log_dispatch(self):
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Party PO from the table to log a dispatch.", parent=self)
            return

        PODispatchDialog(self, po_id=selected['id'], on_save=self.refresh_data)

    def _delete_selected(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more Party POs to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            po_num = selected_items[0].get('po_number', 'this PO')
            msg = f"Are you sure you want to delete Party PO #{po_num}?\n\nThis will remove all dispatch history associated with this PO."
        else:
            msg = f"Are you sure you want to delete {count} selected Party POs at once?\n\nThis will remove all dispatch history associated with these POs."

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt = CustomerPOModel.delete_many(ids)
                self.refresh_data()
                if count == 1:
                    messagebox.showinfo("Success", f"Party PO #{selected_items[0].get('po_number')} deleted successfully!", parent=self)
                else:
                    messagebox.showinfo("Success", f"{deleted_cnt} Party POs deleted successfully!", parent=self)
            except Exception as ex:
                messagebox.showerror("Delete Error", f"Failed to delete Party PO(s): {str(ex)}", parent=self)


    def _view_hisaab_details(self, selected_row=None):
        selected = selected_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a Party PO to view Hisaab details.", parent=self)
            return

        po = CustomerPOModel.get_by_id(selected['id'])
        if not po:
            return

        # Modal showing Hisaab summary and dispatch history
        dlg = tk.Toplevel(self)
        dlg.title(f"📜 Party PO Hisaab Statement - {po['po_number']}")
        dlg.geometry("700x600")
        dlg.configure(bg=COLORS["bg_dark"])
        dlg.transient(self)
        dlg.grab_set()

        # Header
        h = tk.Frame(dlg, bg=COLORS["bg_header"], padx=20, pady=12)
        h.pack(fill="x")
        tk.Label(h, text=f"📜 Party PO Hisaab Details: {po['po_number']}", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # Overview Card
        ov = tk.Frame(dlg, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        ov.pack(fill="x", padx=15, pady=10)

        tk.Label(ov, text=f"Party Name: {po['customer_name']} ({po.get('company_name', '')})", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w")
        tk.Label(ov, text=f"PO Date: {po['po_date']}  |  Target Date: {po.get('target_delivery_date', 'N/A')}", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=2)
        
        ord_kg = float(po['total_ordered_qty_kg'])
        disp_kg = float(po['total_dispatched_qty_kg'])
        bal_kg = po['balance_qty_kg']
        bal_val = po['balance_amount']
        subtot = float(po.get('subtotal', 0.0) or (po['total_po_amount'] / 1.18 if float(po.get('gst_rate', 18.0) or 18.0) > 0 else po['total_po_amount']))
        cgst = float(po.get('cgst_amount', 0.0) or (subtot * 0.09 if float(po.get('gst_rate', 18.0) or 18.0) > 0 else 0.0))
        sgst = float(po.get('sgst_amount', 0.0) or (subtot * 0.09 if float(po.get('gst_rate', 18.0) or 18.0) > 0 else 0.0))
        gst_rate = float(po.get('gst_rate', 18.0) or 18.0)

        stats_txt = f"Total Ordered: {ord_kg:,.2f} KG  |  Dispatched: {disp_kg:,.2f} KG  |  BALANCE PENDING: {bal_kg:,.2f} KG"
        tk.Label(ov, text=stats_txt, font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["warning"]).pack(anchor="w", pady=(4, 2))
        
        if gst_rate > 0:
            gst_txt = f"Taxable Subtotal: ₹ {subtot:,.2f}  |  CGST (9%): ₹ {cgst:,.2f}  |  SGST (9%): ₹ {sgst:,.2f}"
            tk.Label(ov, text=gst_txt, font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"]).pack(anchor="w", pady=(0, 2))

        val_txt = f"Total PO Value (incl. GST): ₹ {po['total_po_amount']:,.2f}  |  Dispatched: ₹ {po['total_dispatched_amount']:,.2f}  |  Balance Value: ₹ {bal_val:,.2f}"
        tk.Label(ov, text=val_txt, font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["success"]).pack(anchor="w")

        # Dispatches Table
        disp_card = tk.Frame(dlg, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        disp_card.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        tk.Label(disp_card, text="🚚 Dispatch & Delivery History Log", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", pady=(0, 8))

        cols = [
            ("dispatch_date", "Date", 100, "center"),
            ("invoice_number", "Invoice / Challan Ref", 150, "center"),
            ("dispatched_qty_kg", "Dispatched (KG)", 130, "center"),
            ("dispatched_amount", "Dispatched Amount (₹)", 140, "e"),
            ("notes", "Notes", 130, "w")
        ]
        table_disp = DataTable(disp_card, cols)
        table_disp.pack(fill="both", expand=True)

        formatted_dispatches = []
        for d in po.get('dispatches', []):
            formatted_dispatches.append({
                'dispatch_date': d['dispatch_date'],
                'invoice_number': d.get('invoice_number') or 'N/A',
                'dispatched_qty_kg': f"{d['dispatched_qty_kg']:,.2f} KG",
                'dispatched_amount': f"₹ {d['dispatched_amount']:,.2f}",
                'notes': d.get('notes', '')
            })

        table_disp.load_data(formatted_dispatches)

        # Close button
        b = tk.Frame(dlg, bg=COLORS["bg_dark"], padx=15, pady=10)
        b.pack(fill="x", side="bottom")
        ttk.Button(b, text="Close", style="Primary.TButton", command=dlg.destroy).pack(side="right")
