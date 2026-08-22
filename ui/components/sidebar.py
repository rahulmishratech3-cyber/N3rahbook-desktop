"""
Sidebar Navigation Menu Component
N3Rah Inventory style navigation with electric indigo active pills.
"""

import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS

class Sidebar(tk.Frame):
    def __init__(self, parent, on_tab_change, on_logout=None):
        super().__init__(parent, bg=COLORS["bg_sidebar"], width=235)
        self.pack_propagate(False)
        self.on_tab_change = on_tab_change
        self.on_logout = on_logout
        self.active_tab = "dashboard"
        self.buttons = {}

        self._build_ui()

    def _build_ui(self):
        # Brand Header Card with Official N3RAH BOOK Logo
        brand_frame = tk.Frame(self, bg=COLORS["bg_sidebar"], padx=15, pady=12)
        brand_frame.pack(fill="x")

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                raw_img = Image.open(logo_path)
                resized_img = raw_img.resize((195, 106), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(resized_img)
                logo_lbl = tk.Label(brand_frame, image=self.logo_img, bg=COLORS["bg_sidebar"])
                logo_lbl.pack(anchor="center", pady=(5, 5))
            except Exception as ex:
                print("Failed to load sidebar logo image:", ex)
                tk.Label(brand_frame, text="N3RAH BOOK", font=("Segoe UI", 16, "bold"), bg=COLORS["bg_sidebar"], fg=COLORS["text_dark"]).pack(anchor="center")
        else:
            tk.Label(brand_frame, text="N3RAH BOOK", font=("Segoe UI", 16, "bold"), bg=COLORS["bg_sidebar"], fg=COLORS["text_dark"]).pack(anchor="center")

        # Divider
        divider = tk.Frame(self, bg=COLORS["border"], height=1)
        divider.pack(fill="x", padx=15, pady=6)

        # Navigation Items
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("items", "📦  Items Catalog"),
            ("stock", "🔄  Stock Adjustments"),
            ("sales", "📄  Sales & Invoices"),
            ("customer_po", "📜  Party PO Tracker"),
            ("purchase", "🚚  Purchase Orders"),
            ("contacts", "👥  Customers & Vendors"),
            ("payments", "💳  Payments & Ledger"),
            ("reports", "📈  Reports & Analytics"),
            ("users", "🔑  Users & Roles"),
            ("settings", "⚙️  Settings & Profile")
        ]


        menu_container = tk.Frame(self, bg=COLORS["bg_sidebar"], pady=5)
        menu_container.pack(fill="both", expand=True)

        for tab_id, label in nav_items:
            btn = tk.Button(
                menu_container,
                text=label,
                font=FONTS["body"],
                anchor="w",
                padx=16,
                pady=9,
                bd=0,
                bg=COLORS["bg_sidebar"],
                fg="#334155",
                activebackground=COLORS["bg_card_alt"],
                activeforeground=COLORS["text_dark"],
                cursor="hand2",
                command=lambda tid=tab_id: self.select_tab(tid)
            )
            btn.pack(fill="x", padx=10, pady=2)
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn, tid=tab_id: self._on_hover(b, tid, True))
            btn.bind("<Leave>", lambda e, b=btn, tid=tab_id: self._on_hover(b, tid, False))
            
            self.buttons[tab_id] = btn

        self._update_button_styles()

        # Footer User Profile Box with Logout Button
        user_frame = tk.Frame(self, bg=COLORS["bg_card_alt"], padx=12, pady=10, bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        user_frame.pack(fill="x", side="bottom", padx=12, pady=12)

        u_top = tk.Frame(user_frame, bg=COLORS["bg_card_alt"])
        u_top.pack(fill="x", pady=(0, 4))

        u_icon = tk.Label(u_top, text="👑", font=("Segoe UI", 13), bg=COLORS["bg_card_alt"], fg=COLORS["warning"])
        u_icon.pack(side="left", padx=(2, 6))

        u_info = tk.Frame(u_top, bg=COLORS["bg_card_alt"])
        u_info.pack(side="left", fill="both", expand=True)

        self.u_name_lbl = tk.Label(u_info, text="Admin User", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"])
        self.u_name_lbl.pack(anchor="w")

        self.u_role_lbl = tk.Label(u_info, text="Admin Access", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"])
        self.u_role_lbl.pack(anchor="w")

        # Logout Button
        if self.on_logout:
            btn_logout = tk.Button(
                user_frame,
                text="🚪  Sign Out",
                font=FONTS["small"],
                bg=COLORS["bg_card"],
                fg=COLORS["danger"],
                activebackground=COLORS["danger"],
                activeforeground="#FFFFFF",
                bd=0,
                padx=8,
                pady=4,
                cursor="hand2",
                command=self.on_logout
            )
            btn_logout.pack(fill="x", pady=(4, 0))

    def set_user_info(self, name, role="Admin"):
        self.u_name_lbl.config(text=name)
        self.u_role_lbl.config(text=f"{role} Access")
        # Hide Users & Roles tab for non-admin users
        if role != "Admin" and "users" in self.buttons:
            self.buttons["users"].pack_forget()

    def select_tab(self, tab_id):
        self.active_tab = tab_id
        self._update_button_styles()
        self.on_tab_change(tab_id)

    def _on_hover(self, button, tab_id, hovering):
        if tab_id == self.active_tab:
            return
        if hovering:
            button.config(bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"])
        else:
            button.config(bg=COLORS["bg_sidebar"], fg="#334155")

    def _update_button_styles(self):
        for tab_id, btn in self.buttons.items():
            if tab_id == self.active_tab:
                btn.config(
                    bg=COLORS["primary"],
                    fg="#FFFFFF",
                    font=FONTS["body_bold"]
                )
            else:
                btn.config(
                    bg=COLORS["bg_sidebar"],
                    fg="#334155",
                    font=FONTS["body"]
                )
