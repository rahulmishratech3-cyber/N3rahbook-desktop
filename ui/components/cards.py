"""
KPI Stat Summary Card Component with Accent Indicator Line
"""

import tkinter as tk
from config import COLORS, FONTS

class KPICard(tk.Frame):
    def __init__(self, parent, title, value="0", icon="📊", subtext="", accent_color=COLORS["primary"]):
        super().__init__(parent, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        self.accent_color = accent_color
        
        self._build_ui(title, value, icon, subtext)

    def _build_ui(self, title, value, icon, subtext):
        # Left Accent Stripe Canvas
        accent_strip = tk.Canvas(self, bg=self.accent_color, width=4, highlightthickness=0, bd=0)
        accent_strip.pack(side="left", fill="y")

        content = tk.Frame(self, bg=COLORS["bg_card"])
        content.pack(side="right", fill="both", expand=True)

        # Top Row
        top_frame = tk.Frame(content, bg=COLORS["bg_card"])
        top_frame.pack(fill="x", padx=14, pady=(12, 0))

        title_lbl = tk.Label(top_frame, text=title, font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        title_lbl.pack(side="left")

        icon_lbl = tk.Label(top_frame, text=icon, font=("Segoe UI", 13), bg=COLORS["bg_card"], fg=self.accent_color)
        icon_lbl.pack(side="right")

        # Value
        self.val_lbl = tk.Label(
            content,
            text=value,
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_light"]
        )
        self.val_lbl.pack(anchor="w", padx=14, pady=4)

        # Subtext
        self.sub_lbl = tk.Label(
            content,
            text=subtext,
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"]
        )
        self.sub_lbl.pack(anchor="w", padx=14, pady=(0, 12))

    def update_value(self, value, subtext=None):
        self.val_lbl.config(text=value)
        if subtext is not None:
            self.sub_lbl.config(text=subtext)
