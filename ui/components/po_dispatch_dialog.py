"""
Party PO Dispatch & Hisaab Entry Dialog
Records quantity (KG) delivered/dispatched against a Customer Purchase Order and updates balance in real time.
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONTS
from models.customer_po import CustomerPOModel

class PODispatchDialog(tk.Toplevel):
    def __init__(self, parent, po_id, on_save=None):
        super().__init__(parent)
        self.po_id = po_id
        self.on_save = on_save
        self.po = CustomerPOModel.get_by_id(po_id)

        if not self.po:
            messagebox.showerror("Error", "Selected Party PO was not found.", parent=parent)
            self.destroy()
            return

        self.title(f"🚚 Log Dispatch / Hisaab - {self.po['po_number']}")
        self.geometry("540x540")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x", side="top")

        tk.Label(h_frame, text=f"🚚 Log Dispatch Against {self.po['po_number']}", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # Pinned Buttons
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="✅ Record Dispatch & Update Hisaab", style="Primary.TButton", command=self._save_dispatch).pack(side="right", padx=5)

        # Form Body
        form = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=15)
        form.pack(fill="both", expand=True)

        # Current PO Status Card
        status_card = tk.Frame(form, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        status_card.pack(fill="x", pady=(0, 15))

        tk.Label(status_card, text=f"Party: {self.po['customer_name']}", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w")

        ordered_kg = float(self.po['total_ordered_qty_kg'])
        dispatched_kg = float(self.po['total_dispatched_qty_kg'])
        bal_kg = max(0.0, ordered_kg - dispatched_kg)

        info_txt = f"Total Ordered: {ordered_kg:,.2f} KG  |  Dispatched: {dispatched_kg:,.2f} KG"
        tk.Label(status_card, text=info_txt, font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 4))

        self.lbl_bal = tk.Label(status_card, text=f"Balance Pending Qty: {bal_kg:,.2f} KG ⚖️", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["warning"])
        self.lbl_bal.pack(anchor="w")

        # Input fields
        tk.Label(form, text="Dispatch Date (YYYY-MM-DD) *", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.date_entry = ttk.Entry(form, width=35)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(anchor="w", pady=(0, 8))

        tk.Label(form, text="Tax Invoice / Delivery Challan Ref #", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.inv_entry = ttk.Entry(form, width=35)
        self.inv_entry.pack(anchor="w", pady=(0, 8))

        tk.Label(form, text="Dispatched Quantity (in KG) *", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.qty_entry = ttk.Entry(form, width=35)
        self.qty_entry.insert(0, f"{bal_kg:g}")
        self.qty_entry.pack(anchor="w", pady=(0, 8))
        self.qty_entry.bind("<KeyRelease>", self._update_preview)

        tk.Label(form, text="Dispatched Amount (₹)", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.amt_entry = ttk.Entry(form, width=35)
        self.amt_entry.insert(0, "0.00")
        self.amt_entry.pack(anchor="w", pady=(0, 8))

        tk.Label(form, text="Notes / Dispatch Remarks", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.notes_entry = ttk.Entry(form, width=45)
        self.notes_entry.pack(anchor="w", pady=(0, 8))

        # Preview label
        self.lbl_prev = tk.Label(form, text="", font=FONTS["small_bold"], bg=COLORS["bg_dark"], fg=COLORS["success"])
        self.lbl_prev.pack(anchor="w", pady=(4, 0))
        self._update_preview()

    def _update_preview(self, event=None):
        try:
            val = float(self.qty_entry.get().strip() or 0.0)
            ordered_kg = float(self.po['total_ordered_qty_kg'])
            dispatched_kg = float(self.po['total_dispatched_qty_kg'])
            new_dispatched = dispatched_kg + val
            rem_bal = max(0.0, ordered_kg - new_dispatched)

            if rem_bal <= 0:
                self.lbl_prev.config(text=f"✨ After this dispatch: PO will be COMPLETED! (Remaining: 0.00 KG)", fg=COLORS["success"])
            else:
                self.lbl_prev.config(text=f"⚖️ After this dispatch: Remaining Balance = {rem_bal:,.2f} KG", fg=COLORS["warning"])
        except ValueError:
            self.lbl_prev.config(text="Please enter a valid numeric quantity.", fg=COLORS["danger"])

    def _save_dispatch(self):
        date_str = self.date_entry.get().strip()
        inv_no = self.inv_entry.get().strip()
        
        try:
            qty_kg = float(self.qty_entry.get().strip())
            amt = float(self.amt_entry.get().strip() or 0.0)
            if qty_kg <= 0:
                raise ValueError("Dispatch quantity must be greater than 0.")
        except ValueError as ex:
            messagebox.showerror("Error", f"Invalid quantity or amount: {str(ex)}", parent=self)
            return

        notes = self.notes_entry.get().strip()

        try:
            success = CustomerPOModel.record_dispatch(
                po_id=self.po_id,
                dispatch_date=date_str,
                invoice_number=inv_no,
                dispatched_qty_kg=qty_kg,
                dispatched_amount=amt,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"Dispatched {qty_kg:,.2f} KG recorded successfully against PO #{self.po['po_number']}!", parent=self)
                if self.on_save:
                    self.on_save()
                self.destroy()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to record dispatch: {str(ex)}", parent=self)
