"""
Admin Login Panel Screen
Sleek Midnight Slate & Electric Indigo Authentication Portal
"""

import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS
from models.user import UserModel

class LoginView(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.on_login_success = on_login_success
        self.show_password_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        # Center Container
        center_box = tk.Frame(self, bg=COLORS["bg_dark"])
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        # Login Card Surface
        card = tk.Frame(
            center_box,
            bg=COLORS["bg_card"],
            bd=1,
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=45,
            pady=35
        )
        card.pack()

        # Logo Header
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                raw_img = Image.open(logo_path)
                resized_img = raw_img.resize((240, 130), Image.Resampling.LANCZOS)
                self.login_logo_img = ImageTk.PhotoImage(resized_img)
                logo_lbl = tk.Label(card, image=self.login_logo_img, bg=COLORS["bg_card"])
                logo_lbl.pack(anchor="center", pady=(0, 10))
            except Exception as ex:
                tk.Label(card, text="N3RAH BOOK", font=("Segoe UI", 22, "bold"), bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="center")
        else:
            tk.Label(card, text="N3RAH BOOK", font=("Segoe UI", 22, "bold"), bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="center")

        tk.Label(
            card,
            text="ENTERPRISE ADMIN PORTAL",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["primary"]
        ).pack(anchor="center", pady=(0, 15))

        # Error Banner
        self.err_lbl = tk.Label(
            card,
            text="",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["danger"]
        )
        self.err_lbl.pack(anchor="w", pady=(0, 10))

        # Username Field
        tk.Label(card, text="Username", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        
        user_frame = tk.Frame(card, bg=COLORS["bg_card_alt"], bd=1, relief="flat")
        user_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(user_frame, text="👤", font=("Segoe UI", 10), bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).pack(side="left", padx=8)
        self.user_entry = tk.Entry(
            user_frame,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"],
            insertbackground=COLORS["text_light"],
            font=FONTS["body"],
            bd=0,
            width=32
        )
        self.user_entry.insert(0, "admin")
        self.user_entry.pack(side="left", padx=(0, 8), pady=8)

        # Password Field
        tk.Label(card, text="Password", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))

        pass_frame = tk.Frame(card, bg=COLORS["bg_card_alt"], bd=1, relief="flat")
        pass_frame.pack(fill="x", pady=(0, 10))

        tk.Label(pass_frame, text="🔒", font=("Segoe UI", 10), bg=COLORS["bg_card_alt"], fg=COLORS["text_muted"]).pack(side="left", padx=8)
        self.pass_entry = tk.Entry(
            pass_frame,
            show="*",
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"],
            insertbackground=COLORS["text_light"],
            font=FONTS["body"],
            bd=0,
            width=32
        )
        self.pass_entry.insert(0, "admin123")
        self.pass_entry.pack(side="left", padx=(0, 8), pady=8)

        # Show Password Toggle
        chk_show = tk.Checkbutton(
            card,
            text="Show Password",
            variable=self.show_password_var,
            command=self._toggle_password,
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"],
            activebackground=COLORS["bg_card"],
            activeforeground=COLORS["text_light"],
            selectcolor=COLORS["bg_dark"],
            font=FONTS["small"]
        )
        chk_show.pack(anchor="w", pady=(0, 20))

        # Submit Login Button
        btn_login = ttk.Button(card, text="🔒 Secure Admin Sign In", style="Primary.TButton", command=self._do_login)
        btn_login.pack(fill="x", pady=(0, 15))

        # Enter key binding
        self.user_entry.bind("<Return>", lambda e: self._do_login())
        self.pass_entry.bind("<Return>", lambda e: self._do_login())

        # Demo Credentials Hint Card
        hint_card = tk.Frame(card, bg=COLORS["bg_dark"], padx=15, pady=10, bd=1, relief="flat")
        hint_card.pack(fill="x")

        tk.Label(hint_card, text="🔑 Demo Credentials:", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["warning"]).pack(anchor="w")
        tk.Label(hint_card, text="Username: admin | Password: admin123", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w")

    def _toggle_password(self):
        if self.show_password_var.get():
            self.pass_entry.config(show="")
        else:
            self.pass_entry.config(show="*")

    def _do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            self.err_lbl.config(text="❌ Please enter both username and password.")
            return

        user = UserModel.authenticate(username, password)
        if user:
            self.err_lbl.config(text="")
            self.on_login_success(user)
        else:
            self.err_lbl.config(text="❌ Invalid username or password!")
