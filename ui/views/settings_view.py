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

        # Row 19: Section - Multi-PC Real-Time Cloud Sync (PostgreSQL / Supabase)
        tk.Label(card, text="🌐 Multi-PC Cloud Database Sync (PostgreSQL / Supabase)", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=19, column=0, columnspan=2, sticky="w", pady=(14, 8))

        cloud_box = tk.Frame(card, bg=COLORS["bg_card_alt"], padx=15, pady=12, bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        cloud_box.grid(row=20, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 12))

        # Cloud Mode Status & Toggle
        cloud_top = tk.Frame(cloud_box, bg=COLORS["bg_card_alt"])
        cloud_top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.cloud_sync_var = tk.BooleanVar(value=False)
        self.chk_cloud = tk.Checkbutton(
            cloud_top,
            text="Enable Real-Time Cloud Sync (Multi-PC)",
            variable=self.cloud_sync_var,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"],
            activebackground=COLORS["bg_card_alt"],
            font=FONTS["body_bold"],
            command=self._on_toggle_cloud
        )
        self.chk_cloud.pack(side="left")

        self.cloud_status_badge = tk.Label(
            cloud_top,
            text="● Backend: Local SQLite (Offline)",
            font=FONTS["small_bold"],
            bg="#E2E8F0",
            fg="#475569",
            padx=8, pady=3
        )
        self.cloud_status_badge.pack(side="right")

        # Connection URL
        tk.Label(cloud_box, text="PostgreSQL Connection URI (from Supabase, Neon, or Cloud SQL) *", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)

        url_f = tk.Frame(cloud_box, bg=COLORS["bg_card_alt"])
        url_f.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 8))

        self.cloud_url_entry = ttk.Entry(url_f, width=65, show="*")
        self.cloud_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self._show_cloud_url = False
        def _toggle_cloud_url():
            self._show_cloud_url = not self._show_cloud_url
            self.cloud_url_entry.config(show="" if self._show_cloud_url else "*")
            self.btn_toggle_cloud_url.config(text="🙈" if self._show_cloud_url else "👁️")

        self.btn_toggle_cloud_url = ttk.Button(url_f, text="👁️", width=3, style="Secondary.TButton", command=_toggle_cloud_url)
        self.btn_toggle_cloud_url.pack(side="right")

        # Cloud Action Buttons
        cloud_btns = tk.Frame(cloud_box, bg=COLORS["bg_card_alt"])
        cloud_btns.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(4, 6))

        ttk.Button(cloud_btns, text="🔌 Test Connection", style="Secondary.TButton", command=self._test_cloud_connection).pack(side="left", padx=(0, 6))
        ttk.Button(cloud_btns, text="🚀 Upload & Migrate Local Data to Cloud", style="Secondary.TButton", command=self._migrate_local_to_cloud).pack(side="left", padx=(0, 6))
        ttk.Button(cloud_btns, text="💾 Save & Switch Mode", style="Primary.TButton", command=self._save_cloud_settings).pack(side="right")

        # Cloud Tip
        cloud_tip = tk.Label(
            cloud_box,
            text="💡 Tip: Create a free PostgreSQL DB on supabase.com or neon.tech, paste the connection URI above, and click 'Upload & Migrate'. Put the exact same URI on your other computer to share and sync all data in real time!",
            font=FONTS["caption"],
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_muted"],
            wraplength=700,
            justify="left"
        )
        cloud_tip.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 0))

        cloud_box.columnconfigure(0, weight=1)
        cloud_box.columnconfigure(1, weight=1)

        # Row 21: Section - Cloud & Server Data Backup
        tk.Label(card, text="☁️ Local / Server Data Backup & Auto-Sync Folder", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=21, column=0, columnspan=2, sticky="w", pady=(12, 8))

        bk_box = tk.Frame(card, bg=COLORS["bg_card_alt"], padx=15, pady=12, bd=1, relief="flat")
        bk_box.grid(row=22, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

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
        self.backup_status_lbl.grid(row=23, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 10))

        # Row 24: Section - Gmail PO Auto-Sync Settings
        tk.Label(card, text="📧 Gmail PO Auto-Sync & PDF Extraction", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=24, column=0, columnspan=2, sticky="w", pady=(15, 8))

        gmail_box = tk.Frame(card, bg=COLORS["bg_card_alt"], padx=15, pady=12, bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        gmail_box.grid(row=25, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 15))

        # Gmail Address
        tk.Label(gmail_box, text="Gmail Address *", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=5)
        self.gmail_entry = ttk.Entry(gmail_box, width=38)
        self.gmail_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 8))

        # Gmail 16-Digit App Password
        tk.Label(gmail_box, text="Google App Password (16 Characters) *", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=5)
        
        pass_f = tk.Frame(gmail_box, bg=COLORS["bg_card_alt"])
        pass_f.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 8))

        self.gmail_pass_entry = ttk.Entry(pass_f, width=28, show="*")
        self.gmail_pass_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._show_pass = False
        def _toggle_pass():
            self._show_pass = not self._show_pass
            self.gmail_pass_entry.config(show="" if self._show_pass else "*")
            self.btn_toggle_pass.config(text="🙈" if self._show_pass else "👁️")

        self.btn_toggle_pass = ttk.Button(pass_f, text="👁️", width=3, style="Secondary.TButton", command=_toggle_pass)
        self.btn_toggle_pass.pack(side="right")

        # PO Search Keywords
        tk.Label(gmail_box, text="Email Filter Keywords (Comma separated)", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        self.gmail_keywords_entry = ttk.Entry(gmail_box, width=75)
        self.gmail_keywords_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 8))

        # Gmail Help Text & Test Button Row
        gmail_bottom = tk.Frame(gmail_box, bg=COLORS["bg_card_alt"])
        gmail_bottom.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(4, 0))

        help_lbl = tk.Label(
            gmail_bottom,
            text="💡 Tip: Google Account -> Security -> 2-Step Verification -> App Passwords se 16-digit password banayein.",
            font=FONTS["small"],
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_muted"]
        )
        help_lbl.pack(side="left")

        ttk.Button(gmail_bottom, text="🔍 Test Gmail Connection", style="Secondary.TButton", command=self._test_gmail_connection).pack(side="right")

        gmail_box.columnconfigure(0, weight=1)
        gmail_box.columnconfigure(1, weight=1)

        # Row 26: Section - Excel Data Import Tool
        tk.Label(card, text="📥 GST & Excel Data Import Tool", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["primary"]).grid(row=26, column=0, columnspan=2, sticky="w", pady=(15, 10))

        import_card = tk.Frame(card, bg=COLORS["bg_card_alt"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        import_card.grid(row=27, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 15))

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

        # Load Gmail Sync Settings
        self.gmail_entry.delete(0, tk.END)
        self.gmail_entry.insert(0, profile.get('gmail_address', ''))

        self.gmail_pass_entry.delete(0, tk.END)
        self.gmail_pass_entry.insert(0, profile.get('gmail_app_password', ''))

        self.gmail_keywords_entry.delete(0, tk.END)
        self.gmail_keywords_entry.insert(0, profile.get('gmail_filter_keywords') or 'PO, Purchase Order, Order, CPO')

        terms = profile.get('terms', [])
        terms_str = "\n".join(terms) if isinstance(terms, list) else str(terms)
        self.terms_txt.delete("1.0", tk.END)
        self.terms_txt.insert("1.0", terms_str)

        # Load Cloud Sync Settings
        try:
            from services.cloud_db_service import get_cloud_config
            from database.db_manager import db
            cloud_cfg = get_cloud_config()
            self.cloud_sync_var.set(cloud_cfg.get("enabled", False))
            self.cloud_url_entry.delete(0, tk.END)
            self.cloud_url_entry.insert(0, cloud_cfg.get("connection_url", ""))
            is_active_cloud = cloud_cfg.get("enabled", False) and db.cloud_mode
            display_host = cloud_cfg.get("connection_url", "").split('@')[-1] if '@' in cloud_cfg.get("connection_url", "") else 'PostgreSQL'
            self._update_cloud_badge(is_active_cloud, display_host)
        except Exception as ex:
            print("Error loading cloud settings:", ex)

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

    def _update_cloud_badge(self, is_cloud, host_info=""):
        if is_cloud:
            self.cloud_status_badge.config(
                text=f"● Live Cloud Sync ACTIVE ({host_info})",
                bg="#DCFCE7",
                fg="#166534"
            )
        else:
            self.cloud_status_badge.config(
                text="● Backend: Local SQLite (Offline)",
                bg="#E2E8F0",
                fg="#475569"
            )

    def _on_toggle_cloud(self):
        is_enabled = self.cloud_sync_var.get()
        if is_enabled and not self.cloud_url_entry.get().strip():
            messagebox.showinfo(
                "Cloud Database Sync",
                "Please enter your PostgreSQL connection URI (from Supabase or Neon) and click 'Save & Switch Mode'.",
                parent=self
            )

    def _test_cloud_connection(self):
        import threading
        from services.cloud_db_service import test_connection

        url = self.cloud_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a PostgreSQL Connection URI.", parent=self)
            return

        def _test():
            ok, msg = test_connection(url)
            def _ui():
                if ok:
                    messagebox.showinfo("Cloud Connection Success", f"✅ {msg}", parent=self)
                else:
                    messagebox.showerror("Cloud Connection Failed", f"❌ {msg}", parent=self)
            self.after(0, _ui)

        threading.Thread(target=_test, daemon=True).start()

    def _migrate_local_to_cloud(self):
        import threading
        from services.cloud_db_service import migrate_local_to_cloud

        url = self.cloud_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a PostgreSQL Connection URI first.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirm Cloud Migration",
            "This will upload and synchronize all your existing products, customers, invoices, and settings from this computer into your cloud database.\n\n"
            "Do you want to proceed with the migration?",
            parent=self
        )
        if not confirm:
            return

        self.cloud_status_badge.config(text="⏳ Migrating data to cloud...", bg="#FEF3C7", fg="#92400E")

        def _migrate():
            ok, msg = migrate_local_to_cloud(url)
            def _ui():
                if ok:
                    messagebox.showinfo("Migration Successful", f"✅ {msg}", parent=self)
                    self.cloud_sync_var.set(True)
                    self._save_cloud_settings()
                else:
                    messagebox.showerror("Migration Error", f"❌ {msg}", parent=self)
                    self.load_data()
            self.after(0, _ui)

        threading.Thread(target=_migrate, daemon=True).start()

    def _save_cloud_settings(self):
        from services.cloud_db_service import save_cloud_config
        from database.db_manager import db

        url = self.cloud_url_entry.get().strip()
        enabled = self.cloud_sync_var.get()

        if enabled and not url:
            messagebox.showerror("Error", "Please enter a valid PostgreSQL Connection URI before enabling Cloud Sync.", parent=self)
            self.cloud_sync_var.set(False)
            return

        ok, msg = save_cloud_config({
            "enabled": enabled,
            "connection_url": url
        })

        if ok:
            db.reload_backend()
            display_host = url.split('@')[-1] if '@' in url else 'PostgreSQL'
            self._update_cloud_badge(enabled and db.cloud_mode, display_host)

            mode_name = "Online Cloud Database (PostgreSQL)" if (enabled and db.cloud_mode) else "Local Offline Database (SQLite)"
            messagebox.showinfo(
                "Database Backend Switched",
                f"✅ Database configuration saved!\n\nActive Mode: {mode_name}\n\nAll subsequent operations will synchronize directly with this database.",
                parent=self
            )
        else:
            messagebox.showerror("Error", f"Failed to save cloud config: {msg}", parent=self)

    def _test_gmail_connection(self):
        import threading
        from services.gmail_service import GmailSyncService

        gmail_addr = self.gmail_entry.get().strip()
        gmail_pass = self.gmail_pass_entry.get().strip()

        if not gmail_addr or not gmail_pass:
            messagebox.showerror("Error", "Kripya Gmail Address aur Google App Password dono daalein.", parent=self)
            return

        def _check():
            ok, msg = GmailSyncService.test_connection(gmail_addr, gmail_pass)
            def _ui():
                if ok:
                    messagebox.showinfo("Gmail Connection Success", f"✅ {msg}", parent=self)
                else:
                    messagebox.showerror("Gmail Connection Failed", f"❌ {msg}", parent=self)
            self.after(0, _ui)

        threading.Thread(target=_check, daemon=True).start()

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
        data['gmail_address'] = self.gmail_entry.get().strip()
        data['gmail_app_password'] = self.gmail_pass_entry.get().strip()
        data['gmail_filter_keywords'] = self.gmail_keywords_entry.get().strip() or 'PO, Purchase Order, Order, CPO'

        if not data['name']:
            messagebox.showerror("Error", "Business / Company Name is required!", parent=self)
            return

        try:
            CompanyModel.update_profile(data)
            self._save_backup_settings()
            messagebox.showinfo("Success", "Company profile, invoice settings, and Gmail configuration updated successfully!", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save profile: {str(ex)}", parent=self)

    def _open_excel_import(self):
        from ui.components.excel_import_dialog import ExcelImportDialog
        ExcelImportDialog(self)

