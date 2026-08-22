"""
Company Profile & Application Settings View Screen
Allows any client to configure their business name, GSTIN, Bank details, and Invoice Terms.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.company import CompanyModel

class SettingsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.entries = {}
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Control Header
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="⚙️ Business Profile & Invoice Settings", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(side="left")

        ttk.Button(ctrl_bar, text="💾 Save Profile Settings", style="Primary.TButton", command=self._save_settings).pack(side="right", padx=4)

        # Scrollable Canvas Container
        canvas_container = tk.Frame(self, bg=COLORS["bg_dark"])
        canvas_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.canvas = tk.Canvas(canvas_container, bg=COLORS["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)

        scrollable_frame = tk.Frame(self.canvas, bg=COLORS["bg_dark"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        canvas_window = self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.canvas.itemconfig(canvas_window, width=event.width)

        self.canvas.bind('<Configure>', _on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel binding when hovering over settings
        def _on_mousewheel(event):
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        card = tk.Frame(scrollable_frame, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=25, pady=20)
        card.pack(fill="both", expand=True, padx=5, pady=5)

        # Row 0: Section - Business Info
        tk.Label(card, text="🏢 Company & GST Details", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Company Name
        tk.Label(card, text="Business / Company Name *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=1, column=0, sticky="w", padx=5)
        name_entry = ttk.Entry(card, width=35)
        name_entry.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['name'] = name_entry

        # GSTIN
        tk.Label(card, text="GSTIN *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=1, column=1, sticky="w", padx=5)
        gstin_entry = ttk.Entry(card, width=35)
        gstin_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=(0, 12))
        self.entries['gstin'] = gstin_entry

        # PAN Number
        tk.Label(card, text="PAN Number", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=0, sticky="w", padx=5)
        pan_entry = ttk.Entry(card, width=35)
        pan_entry.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['pan'] = pan_entry

        # Mobile Phone
        tk.Label(card, text="Mobile / Phone *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=1, sticky="w", padx=5)
        mob_entry = ttk.Entry(card, width=35)
        mob_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=(0, 12))
        self.entries['mobile'] = mob_entry

        # Email Address
        tk.Label(card, text="Business Email", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=5, column=0, sticky="w", padx=5)
        email_entry = ttk.Entry(card, width=35)
        email_entry.grid(row=6, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['email'] = email_entry

        # Udyam Registration Number
        tk.Label(card, text="Udyam Reg. No. (MSME)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=5, column=1, sticky="w", padx=5)
        udyam_entry = ttk.Entry(card, width=35)
        udyam_entry.grid(row=6, column=1, sticky="ew", padx=5, pady=(0, 12))
        self.entries['udyam_reg_no'] = udyam_entry

        # Full Business Address (Spans 2 columns)
        tk.Label(card, text="Registered Business Address *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=7, column=0, columnspan=2, sticky="w", padx=5)
        addr_entry = ttk.Entry(card, width=75)
        addr_entry.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 16))
        self.entries['address'] = addr_entry

        # Section - Bank Details
        tk.Label(card, text="🏦 Bank Details for Invoices", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=9, column=0, columnspan=2, sticky="w", pady=(10, 10))

        # Bank Name
        tk.Label(card, text="Bank Name", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=10, column=0, sticky="w", padx=5)
        bname_entry = ttk.Entry(card, width=35)
        bname_entry.grid(row=11, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['bank_name'] = bname_entry

        # Branch Location
        tk.Label(card, text="Branch Name / Location", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=10, column=1, sticky="w", padx=5)
        bbranch_entry = ttk.Entry(card, width=35)
        bbranch_entry.grid(row=11, column=1, sticky="ew", padx=5, pady=(0, 12))
        self.entries['bank_branch'] = bbranch_entry

        # Account Number
        tk.Label(card, text="Account Number", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=12, column=0, sticky="w", padx=5)
        acc_entry = ttk.Entry(card, width=35)
        acc_entry.grid(row=13, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['account_no'] = acc_entry

        # IFSC Code
        tk.Label(card, text="IFSC Code", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=12, column=1, sticky="w", padx=5)
        ifsc_entry = ttk.Entry(card, width=35)
        ifsc_entry.grid(row=13, column=1, sticky="ew", padx=5, pady=(0, 16))
        self.entries['ifsc_code'] = ifsc_entry

        # Section - Terms & Conditions
        tk.Label(card, text="📝 Default Invoice Terms & Conditions", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=14, column=0, columnspan=2, sticky="w", pady=(10, 8))

        tk.Label(card, text="Terms (One condition per line)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=15, column=0, columnspan=2, sticky="w", padx=5)
        self.terms_txt = tk.Text(card, height=3, width=75, font=FONTS["body"], bg="#FFFFFF", fg=COLORS["text_dark"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        self.terms_txt.grid(row=16, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 14))

        # Section - Fiscal Year Management
        tk.Label(card, text="📅 Fiscal Year Management", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=17, column=0, columnspan=2, sticky="w", pady=(10, 8))

        fy_box = tk.Frame(card, bg=COLORS["bg_card_alt"], padx=15, pady=10, bd=1, relief="flat")
        fy_box.grid(row=18, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        self.fy_status_lbl = tk.Label(fy_box, text="Current Active Fiscal Year: FY 2026-2027", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_light"])
        self.fy_status_lbl.pack(side="left")

        ttk.Button(fy_box, text="🔒 Close Fiscal Year & Start New FY", style="Secondary.TButton", command=self._open_fy_dialog).pack(side="right")

        # Section - Cloud & Server Data Backup
        tk.Label(card, text="☁️ Cloud & Server Data Backup", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=19, column=0, columnspan=2, sticky="w", pady=(12, 8))

        bk_box = tk.Frame(card, bg=COLORS["bg_card_alt"], padx=15, pady=12, bd=1, relief="flat")
        bk_box.grid(row=20, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        # Remote Server URL
        tk.Label(bk_box, text="Remote Server / Webhook URL", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=5)
        self.backup_url_entry = ttk.Entry(bk_box, width=38)
        self.backup_url_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 8))

        # API Secret Key
        tk.Label(bk_box, text="API Key / Auth Token (Optional)", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=5)
        self.backup_token_entry = ttk.Entry(bk_box, width=38, show="*")
        self.backup_token_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 8))

        # Local / Cloud Sync Directory
        tk.Label(bk_box, text="Local / Cloud Sync Folder Path (Google Drive / OneDrive / Local)", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        
        sync_frame = tk.Frame(bk_box, bg=COLORS["bg_card_alt"])
        sync_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        self.backup_sync_entry = ttk.Entry(sync_frame, width=65)
        self.backup_sync_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(sync_frame, text="📁 Browse", style="Secondary.TButton", command=self._browse_sync_folder).pack(side="right")

        # Auto Backup on Exit & Manual Push Button
        bottom_bk = tk.Frame(bk_box, bg=COLORS["bg_card_alt"])
        bottom_bk.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(4, 0))

        self.auto_backup_var = tk.BooleanVar(value=True)
        chk_exit = tk.Checkbutton(
            bottom_bk,
            text="Auto-Backup on Application Exit",
            variable=self.auto_backup_var,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"],
            activebackground=COLORS["bg_card_alt"],
            font=FONTS["small"]
        )
        chk_exit.pack(side="left")

        ttk.Button(bottom_bk, text="☁️ Push Backup Now", style="Primary.TButton", command=self._do_manual_backup).pack(side="right")

        # Backup Status Display
        self.backup_status_lbl = tk.Label(
            card,
            text="Last Backup: Never",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"]
        )
        self.backup_status_lbl.grid(row=21, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 10))

        # Row 22: Section - Excel Data Import Tool
        tk.Label(card, text="📥 GST & Excel Data Import Tool", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=22, column=0, columnspan=2, sticky="w", pady=(15, 10))

        import_card = tk.Frame(card, bg=COLORS["bg_card_alt"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        import_card.grid(row=23, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 15))

        tk.Label(
            import_card,
            text="Bulk import Sales Invoices, Products List, or Customers Directory from Excel (.xlsx, .xls, .csv) sheets.",
            font=FONTS["small"],
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"]
        ).pack(side="left", padx=5)

        ttk.Button(import_card, text="📥 Launch Excel Data Importer", style="Primary.TButton", command=self._open_excel_import).pack(side="right", padx=5)

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

    def load_data(self):
        profile = CompanyModel.get_profile()
        for key in ['name', 'address', 'gstin', 'pan', 'mobile', 'email', 'udyam_reg_no', 'bank_name', 'bank_branch', 'account_no', 'ifsc_code']:
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, profile.get(key, ''))

        terms = profile.get('terms', [])
        terms_str = "\n".join(terms) if isinstance(terms, list) else str(terms)
        self.terms_txt.delete("1.0", tk.END)
        self.terms_txt.insert("1.0", terms_str)

        from models.fiscal_year import FiscalYearModel
        active_fy = FiscalYearModel.get_active_year()
        self.fy_status_lbl.config(text=f"Current Active Fiscal Year: FY {active_fy.get('year_label', '2026-2027')}")

        from services.backup_service import get_backup_config
        bk_config = get_backup_config()
        self.backup_url_entry.delete(0, tk.END)
        self.backup_url_entry.insert(0, bk_config.get('server_url', ''))

        self.backup_token_entry.delete(0, tk.END)
        self.backup_token_entry.insert(0, bk_config.get('api_token', ''))

        self.backup_sync_entry.delete(0, tk.END)
        self.backup_sync_entry.insert(0, bk_config.get('sync_folder', ''))

        self.auto_backup_var.set(bk_config.get('auto_backup_on_exit', True))

        last_time = bk_config.get('last_backup_time', 'Never')
        last_stat = bk_config.get('last_backup_status', '')
        self.backup_status_lbl.config(text=f"Last Backup: {last_time} ({last_stat})")

    def _browse_sync_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(parent=self, title="Select Backup Destination / Cloud Sync Folder")
        if folder:
            self.backup_sync_entry.delete(0, tk.END)
            self.backup_sync_entry.insert(0, folder)

    def _open_fy_dialog(self):
        from ui.components.fiscal_year_dialog import FiscalYearDialog
        FiscalYearDialog(self, on_success=self.load_data)

    def _save_backup_settings(self):
        from services.backup_service import get_backup_config, save_backup_config
        config = get_backup_config()
        config['server_url'] = self.backup_url_entry.get().strip()
        config['api_token'] = self.backup_token_entry.get().strip()
        config['sync_folder'] = self.backup_sync_entry.get().strip()
        config['auto_backup_on_exit'] = self.auto_backup_var.get()
        save_backup_config(config)

    def _do_manual_backup(self):
        self._save_backup_settings()
        try:
            from services.backup_service import run_full_backup
            res = run_full_backup()
            self.load_data()
            messagebox.showinfo("Backup Success", f"☁️ Database Backup Completed!\n\nTimestamp: {res['timestamp']}\nSnapshot File: {res['filename']}\nFile Size: {res['size_kb']:.1f} KB\n\nDetails: {res['status']}", parent=self)
        except Exception as ex:
            messagebox.showerror("Backup Error", f"Failed to execute database backup: {str(ex)}", parent=self)

    def _save_settings(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        data['terms'] = self.terms_txt.get("1.0", tk.END).strip()

        if not data['name']:
            messagebox.showerror("Error", "Business / Company Name is required!", parent=self)
            return

        try:
            CompanyModel.update_profile(data)
            self._save_backup_settings()
            messagebox.showinfo("Success", "Company profile, invoice settings, and backup config updated successfully!", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save profile: {str(ex)}", parent=self)

    def _open_excel_import(self):
        from ui.components.excel_import_dialog import ExcelImportDialog
        ExcelImportDialog(self)
