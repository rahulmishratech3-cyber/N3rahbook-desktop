"""
Payments & Party Ledger Management Screen
Displays Payment In (Collections), Payment Out (Vendor Payouts),
Payment Mode distribution, and Party Account Statements.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.payment import PaymentModel
from ui.components.cards import KPICard
from ui.components.data_table import DataTable
from ui.components.dialogs import PaymentDialog, PartyLedgerDialog

class PaymentsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. Top KPI Summary Cards Row
        kpi_container = tk.Frame(self, bg=COLORS["bg_dark"])
        kpi_container.pack(fill="x", padx=20, pady=15)

        self.card_in = KPICard(kpi_container, "TOTAL RECEIVED", "₹ 0.00", "📥", "Customer collections", COLORS["success"])
        self.card_in.pack(side="left", fill="both", expand=True, padx=5)

        self.card_out = KPICard(kpi_container, "TOTAL PAID", "₹ 0.00", "📤", "Vendor payouts", COLORS["primary"])
        self.card_out.pack(side="left", fill="both", expand=True, padx=5)

        self.card_rec = KPICard(kpi_container, "CUSTOMER DUES (BAAKI)", "₹ 0.00", "⏳", "Receivables pending", COLORS["warning"])
        self.card_rec.pack(side="left", fill="both", expand=True, padx=5)

        self.card_pay = KPICard(kpi_container, "VENDOR DUES (BAAKI)", "₹ 0.00", "💸", "Payables pending", COLORS["danger"])
        self.card_pay.pack(side="left", fill="both", expand=True, padx=5)

        # 2. Control Bar (Search & Filter + Actions)
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=5)

        # Search Input
        tk.Label(ctrl_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=4)
        self.search_entry = ttk.Entry(ctrl_bar, width=20)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Type Filter
        tk.Label(ctrl_bar, text="Type:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(10, 4))
        self.type_combo = ttk.Combobox(ctrl_bar, values=["All", "Payment In", "Payment Out"], state="readonly", width=14)
        self.type_combo.current(0)
        self.type_combo.pack(side="left", padx=4)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data(recalculate=False))

        # Mode Filter
        tk.Label(ctrl_bar, text="Mode:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=(10, 4))
        modes = ["All"] + PaymentModel.PAYMENT_MODES
        self.mode_combo = ttk.Combobox(ctrl_bar, values=modes, state="readonly", width=14)
        self.mode_combo.current(0)
        self.mode_combo.pack(side="left", padx=4)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data(recalculate=False))

        # Right Action Buttons
        ttk.Button(ctrl_bar, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_payment).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="📜 Party Ledger", style="Secondary.TButton", command=self._view_ledger).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="➕ Record Payment", style="Primary.TButton", command=self._record_payment).pack(side="right", padx=4)

        # 3. Main Data Table Box
        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        cols = [
            ("payment_number", "Voucher No", 140, "center"),
            ("payment_date", "Date", 110, "center"),
            ("contact_name", "Party / Customer / Vendor", 240, "w"),
            ("payment_type", "Type", 120, "center"),
            ("payment_mode", "Method / Mode", 130, "center"),
            ("amount", "Amount (₹)", 140, "e"),
            ("reference_no", "Txn / Ref No", 150, "center"),
            ("notes", "Notes / Description", 220, "w")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._view_ledger)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_search_key(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, lambda: self.refresh_data(recalculate=False))

    def refresh_data(self, recalculate=False):
        # Update KPI cards
        summary = PaymentModel.get_summary(recalculate=recalculate)
        self.card_in.update_value(f"₹ {summary['total_received']:,.2f}")
        self.card_out.update_value(f"₹ {summary['total_paid']:,.2f}")
        self.card_rec.update_value(f"₹ {summary['net_receivable']:,.2f}")
        self.card_pay.update_value(f"₹ {summary['net_payable']:,.2f}")

        # Search & Filter Table
        q = self.search_entry.get().strip()
        p_type = self.type_combo.get()
        p_mode = self.mode_combo.get()

        payments = PaymentModel.search(query=q, payment_type=p_type, payment_mode=p_mode)

        display_rows = []
        for p in payments:
            row = dict(p)
            row['amount'] = f"₹ {p['amount']:,.2f}"
            row['contact_name'] = f"{p['contact_name']} ({p.get('contact_type', '')})"
            display_rows.append(row)

        self.table.load_data(display_rows)

    def _record_payment(self):
        PaymentDialog(self, on_save=lambda: self.refresh_data(recalculate=True))

    def _view_ledger(self, selected_row=None):
        item = selected_row or self.table.get_selected_item()
        contact_id = item.get('contact_id') if item else None
        PartyLedgerDialog(self, contact_id=contact_id, on_close=lambda: self.refresh_data(recalculate=False))

    def _delete_payment(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more payment records to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            item = selected_items[0]
            msg = f"Are you sure you want to delete payment voucher '{item.get('payment_number')}' for {item.get('contact_name')}?"
        else:
            msg = f"Are you sure you want to delete {count} selected payment records at once?"

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt = PaymentModel.delete_many(ids)
                self.refresh_data()
                if count == 1:
                    messagebox.showinfo("Success", f"Payment voucher '{selected_items[0].get('payment_number')}' deleted successfully!", parent=self)
                else:
                    messagebox.showinfo("Success", f"{deleted_cnt} payment vouchers deleted successfully!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete payment(s): {str(ex)}", parent=self)

