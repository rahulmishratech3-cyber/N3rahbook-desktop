"""
Fiscal Year Closing & Transition Modal Dialog
Allows user to review closing financial statistics, close the current fiscal year, and start the new fiscal year.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.fiscal_year import FiscalYearModel


class FiscalYearDialog(tk.Toplevel):
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        self.title("📅 Close Fiscal Year & Start New Year")
        self.geometry("620x540")
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.on_success = on_success
        self.summary = FiscalYearModel.get_closing_summary()

        self._build_ui()

    def _build_ui(self):
        # 1. Header Toolbar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x")

        active_fy_lbl = self.summary['active_fy'].get('year_label', '2026-2027')
        tk.Label(
            h_frame,
            text=f"📅 Fiscal Year Closing: FY {active_fy_lbl}",
            font=FONTS["heading"],
            bg=COLORS["bg_header"],
            fg=COLORS["text_light"]
        ).pack(side="left")

        # 2. Main Content Box
        container = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=15)
        container.pack(fill="both", expand=True)

        # Overview Card
        card = tk.Frame(
            container,
            bg=COLORS["bg_card"],
            bd=1,
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=20,
            pady=15
        )
        card.pack(fill="x", pady=(0, 15))

        tk.Label(
            card,
            text="📊 Current Fiscal Year Financial Summary",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["primary"]
        ).pack(anchor="w", pady=(0, 10))

        # Metrics Table Grid
        grid_frame = tk.Frame(card, bg=COLORS["bg_card"])
        grid_frame.pack(fill="x", pady=5)

        # Row 1: Total Sales
        tk.Label(grid_frame, text="Total Sales Revenue:", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", pady=4)
        tk.Label(grid_frame, text=f"₹ {self.summary['total_sales']:,.2f} ({self.summary['sales_count']} orders)", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["success"]).grid(row=0, column=1, sticky="e", pady=4)

        # Row 2: Total Purchases
        tk.Label(grid_frame, text="Total Purchase Cost:", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=1, column=0, sticky="w", pady=4)
        tk.Label(grid_frame, text=f"₹ {self.summary['total_purchases']:,.2f} ({self.summary['pur_count']} POs)", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["warning"]).grid(row=1, column=1, sticky="e", pady=4)

        # Row 3: Closing Stock Value
        tk.Label(grid_frame, text="Closing Inventory Value:", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=2, column=0, sticky="w", pady=4)
        tk.Label(grid_frame, text=f"₹ {self.summary['stock_value']:,.2f} ({self.summary['item_count']} items)", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).grid(row=2, column=1, sticky="e", pady=4)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # New FY Inputs Box
        new_fy_box = tk.Frame(
            container,
            bg=COLORS["bg_card"],
            bd=1,
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=20,
            pady=15
        )
        new_fy_box.pack(fill="x", pady=5)

        tk.Label(
            new_fy_box,
            text="🚀 Initialize New Fiscal Year",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["primary"]
        ).pack(anchor="w", pady=(0, 10))

        # Default next year label calculation
        curr_label = self.summary['active_fy'].get('year_label', '2026-2027')
        try:
            parts = curr_label.split('-')
            s_yr = int(parts[0]) + 1
            e_yr = int(parts[1]) + 1
            default_next = f"{s_yr}-{e_yr}"
        except Exception:
            default_next = "2027-2028"

        tk.Label(new_fy_box, text="New Fiscal Year Label (e.g. 2027-2028) *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 2))
        self.next_fy_entry = ttk.Entry(new_fy_box, width=30)
        self.next_fy_entry.insert(0, default_next)
        self.next_fy_entry.pack(anchor="w", pady=(0, 10))

        info_lbl = tk.Label(
            new_fy_box,
            text="⚠️ Closing the fiscal year archives current sales & purchase metrics and starts the new fiscal year cleanly. Your inventory stock levels and customer balances remain intact.",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"],
            wraplength=520,
            justify="left"
        )
        info_lbl.pack(anchor="w", pady=5)

        # 3. Action Buttons
        btn_bar = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=15)
        btn_bar.pack(fill="x", side="bottom")

        ttk.Button(btn_bar, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_bar, text="🔒 Confirm Close & Start New FY", style="Primary.TButton", command=self._confirm_close_fy).pack(side="right", padx=5)

    def _confirm_close_fy(self):
        next_label = self.next_fy_entry.get().strip()
        if not next_label:
            messagebox.showerror("Error", "Please enter a label for the new Fiscal Year!", parent=self)
            return

        curr_label = self.summary['active_fy'].get('year_label', 'current FY')
        confirm = messagebox.askyesno(
            "Confirm Fiscal Year Close",
            f"Are you sure you want to close FY {curr_label} and activate FY {next_label}?\n\nThis will record current totals and switch system operations to FY {next_label}.",
            parent=self
        )

        if confirm:
            try:
                FiscalYearModel.close_and_start_new(next_label)
                if self.on_success:
                    self.on_success()
                messagebox.showinfo("Success", f"Fiscal Year {curr_label} closed successfully!\nActivated New Fiscal Year {next_label}.", parent=self)
                self.destroy()
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to close fiscal year: {str(ex)}", parent=self)
