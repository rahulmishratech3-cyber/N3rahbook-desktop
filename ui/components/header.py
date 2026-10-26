"""
Top Header Bar Component
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS

class HeaderBar(tk.Frame):
    def __init__(self, parent, on_search=None, on_refresh=None):
        super().__init__(parent, bg=COLORS["bg_header"], height=65)
        self.pack_propagate(False)
        self.on_search = on_search
        self.on_refresh = on_refresh

        self._build_ui()

    def _build_ui(self):
        # Bottom divider border line
        divider = tk.Frame(self, bg=COLORS["border"], height=1)
        divider.pack(fill="x", side="bottom")

        # Left Title
        self.title_var = tk.StringVar(value="Dashboard")
        title_label = tk.Label(
            self,
            textvariable=self.title_var,
            font=FONTS["title"],
            bg=COLORS["bg_header"],
            fg=COLORS["text_dark"]
        )
        title_label.pack(side="left", padx=20, pady=12)

        # Right Action Container
        right_container = tk.Frame(self, bg=COLORS["bg_header"])
        right_container.pack(side="right", padx=20, pady=10)

        # Search Bar Box
        search_frame = tk.Frame(right_container, bg="#FFFFFF", bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        search_frame.pack(side="left", padx=10)

        s_icon = tk.Label(search_frame, text="🔍", bg="#FFFFFF", fg=COLORS["text_muted"], font=("Segoe UI", 10))
        s_icon.pack(side="left", padx=8)

        self.placeholder_text = "Global search..."
        self.search_entry = tk.Entry(
            search_frame,
            bg="#FFFFFF",
            fg=COLORS["text_muted"],
            insertbackground=COLORS["text_dark"],
            font=FONTS["body"],
            bd=0,
            width=24
        )
        self.search_entry.insert(0, self.placeholder_text)
        self.search_entry.pack(side="left", padx=(0, 8), pady=6)
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._handle_search)

        # Refresh Data Button
        ref_btn = tk.Button(
            right_container,
            text="🔄 Refresh Data",
            font=FONTS["small"],
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_dark"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["text_dark"],
            bd=1,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._handle_refresh
        )
        ref_btn.pack(side="left", padx=6)

        # Alert Badge Indicator
        self.alert_var = tk.StringVar(value="🔔 0 Alerts")
        self.alert_badge = tk.Label(
            right_container,
            textvariable=self.alert_var,
            font=FONTS["small"],
            bg=COLORS["badge_lowstock"],
            fg=COLORS["warning"],
            padx=12,
            pady=5
        )
        self.alert_badge.pack(side="left", padx=6)

    def set_title(self, title):
        self.title_var.set(title)

    def update_alerts(self, count):
        if count > 0:
            self.alert_var.set(f"⚠️ {count} Low Stock")
            self.alert_badge.config(bg=COLORS["badge_lowstock"], fg=COLORS["warning"])
        else:
            self.alert_var.set("✅ Stock Healthy")
            self.alert_badge.config(bg=COLORS["badge_instock"], fg=COLORS["success"])

    def _on_search_focus_in(self, event=None):
        if self.search_entry.get().strip() == self.placeholder_text:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=COLORS["text_dark"])

    def _on_search_focus_out(self, event=None):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, self.placeholder_text)
            self.search_entry.config(fg=COLORS["text_muted"])

    def _handle_search(self, event=None):
        if hasattr(self, '_search_timer') and self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._do_search)

    def _do_search(self):
        if self.on_search:
            txt = self.search_entry.get().strip()
            if txt == self.placeholder_text:
                txt = ""
            self.on_search(txt)

    def _handle_refresh(self):
        if self.on_refresh:
            self.on_refresh()
