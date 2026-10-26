"""
Customers & Suppliers Contacts Directory View Screen
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.contact import ContactModel
from ui.components.data_table import DataTable
from ui.components.dialogs import ContactDialog, PaymentDialog, PartyLedgerDialog

class ContactsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=4)
        self.search_entry = ttk.Entry(ctrl_bar, width=20)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        tk.Label(ctrl_bar, text="Type:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=6)
        self.type_combo = ttk.Combobox(ctrl_bar, values=["All", "Customer", "Supplier"], state="readonly", width=12)
        self.type_combo.current(0)
        self.type_combo.pack(side="left", padx=4)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data(sync_balances=False))

        ttk.Button(ctrl_bar, text="🗑️ Delete", style="Secondary.TButton", command=self._delete_contact).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="📜 Party Ledger", style="Secondary.TButton", command=self._view_ledger).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="💳 Record Payment", style="Secondary.TButton", command=self._record_payment).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="✏️ Edit Contact", style="Secondary.TButton", command=self._edit_contact).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="➕ Add Contact", style="Primary.TButton", command=self._add_contact).pack(side="right", padx=4)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("name", "Contact / Owner Name", 210, "w"),
            ("company_name", "Business / Company Name", 250, "w"),
            ("contact_type", "Party Type", 95, "center"),
            ("phone", "Mobile / Phone", 120, "center"),
            ("address", "Full Business Address", 340, "w"),
            ("gstin", "GSTIN", 150, "center"),
            ("balance", "Outstanding Due (₹)", 150, "e")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_contact)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_search_key(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, lambda: self.refresh_data(sync_balances=False))

    def refresh_data(self, sync_balances=True):
        if sync_balances:
            from models.payment import PaymentModel
            PaymentModel.recalculate_all_balances()

        query = self.search_entry.get().strip()
        ctype = self.type_combo.get()
        contacts = ContactModel.search(query=query, contact_type=ctype)
        display_c = []
        for c in contacts:
            row = dict(c)
            bal = float(c.get('balance') or 0.0)
            tag = " (Due)" if bal > 0 else (" (Settled)" if bal == 0 else " (Advance)")
            row['balance'] = f"₹ {bal:,.2f}{tag}"
            display_c.append(row)
        self.table.load_data(display_c)

    def _add_contact(self):
        ContactDialog(self, on_save=lambda: self.refresh_data(sync_balances=True))

    def _edit_contact(self, contact_row=None):
        selected = contact_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a contact from the table.", parent=self)
            return

        contact = ContactModel.get_by_id(selected['id'])
        if contact:
            ContactDialog(self, contact_data=contact, on_save=lambda: self.refresh_data(sync_balances=True))

    def _record_payment(self):
        selected = self.table.get_selected_item()
        c_id = selected['id'] if selected else None
        PaymentDialog(self, contact_id=c_id, on_save=lambda: self.refresh_data(sync_balances=True))

    def _view_ledger(self, contact_row=None):
        selected = contact_row or self.table.get_selected_item()
        c_id = selected['id'] if selected else None
        PartyLedgerDialog(self, contact_id=c_id, on_close=lambda: self.refresh_data(sync_balances=False))

    def _delete_contact(self):
        selected_items = self.table.get_selected_items()
        if not selected_items:
            messagebox.showwarning("Selection Required", "Please select one or more contacts to delete.", parent=self)
            return

        count = len(selected_items)
        if count == 1:
            name = selected_items[0].get('name', 'this contact')
            prompt = (
                f"Are you sure you want to delete contact: '{name}'?\n\n"
                "⚠️ Note: Any linked invoices, purchase orders, customer POs, and payments for this party will also be removed.\n\n"
                "🛡️ An automatic database backup snapshot will be saved before deletion."
            )
        else:
            prompt = (
                f"Are you sure you want to delete {count} selected contacts at once?\n\n"
                "⚠️ Note: Any linked invoices, purchase orders, customer POs, and payments for all selected parties will also be removed.\n\n"
                "🛡️ An automatic database backup snapshot will be saved before deletion."
            )

        confirm = messagebox.askyesno("Confirm Delete & Auto-Backup", prompt, parent=self)
        if confirm:
            try:
                ids = [item['id'] for item in selected_items]
                deleted_cnt, backup_file = ContactModel.delete_many(ids)
                
                if count == 1:
                    msg = f"Contact '{selected_items[0].get('name')}' and linked records were removed successfully."
                else:
                    msg = f"Successfully removed {deleted_cnt} contacts and all their linked records."
                    
                if backup_file:
                    msg += f"\n\n🛡️ Safety Backup Saved:\nexports/backups/{backup_file}"
                    
                messagebox.showinfo("Deleted Successfully", msg, parent=self)
                self.refresh_data(sync_balances=True)
            except Exception as ex:
                messagebox.showerror("Delete Failed", f"An error occurred while deleting contact(s):\n{str(ex)}", parent=self)



