"""
KPI Stat Summary Card Component with Modern Accent Strip & Pastel Icon Badges
"""

import tkinter as tk
from config import COLORS, FONTS

class KPICard(tk.Frame):
    def __init__(self, parent, title, value="0", icon="📊", subtext="", accent_color=COLORS["primary"]):
        super().__init__(parent, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        self.accent_color = accent_color
        
        # Determine pastel badge background & text color
        self.badge_bg = self._get_pastel_bg(accent_color)
        
        self._build_ui(title, value, icon, subtext)

    def _get_pastel_bg(self, color):
        color_map = {
            COLORS.get("success", "#10B981"): "#ECFDF5",
            COLORS.get("warning", "#D97706"): "#FFFBEB",
            COLORS.get("primary", "#4F46E5"): "#EEF2FF",
            COLORS.get("accent", "#0284C7"): "#F0F9FF",
            COLORS.get("danger", "#EF4444"): "#FEF2F2",
            COLORS.get("purple", "#9333EA"): "#FAF5FF",
        }
        return color_map.get(color, "#F1F5F9")

    def _build_ui(self, title, value, icon, subtext):
        # Left Accent Stripe
        accent_strip = tk.Canvas(self, bg=self.accent_color, width=4, highlightthickness=0, bd=0)
        accent_strip.pack(side="left", fill="y")

        content = tk.Frame(self, bg=COLORS["bg_card"], padx=14, pady=12)
        content.pack(side="right", fill="both", expand=True)

        # Top Row: Title + Pastel Icon Badge
        top_frame = tk.Frame(content, bg=COLORS["bg_card"])
        top_frame.pack(fill="x", pady=(0, 4))

        title_lbl = tk.Label(
            top_frame,
            text=title.upper(),
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"]
        )
        title_lbl.pack(side="left", anchor="w")

        # Icon Badge Frame (Rounded look with padding)
        icon_frame = tk.Frame(
            top_frame,
            bg=self.badge_bg,
            padx=7,
            pady=3,
            bd=0
        )
        icon_frame.pack(side="right", anchor="e")

        icon_lbl = tk.Label(
            icon_frame,
            text=icon,
            font=("Segoe UI", 11),
            bg=self.badge_bg,
            fg=self.accent_color
        )
        icon_lbl.pack()

        # Value
        self.val_lbl = tk.Label(
            content,
            text=value,
            font=("Segoe UI", 19, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_light"]
        )
        self.val_lbl.pack(anchor="w", pady=(2, 2))

        # Subtext with subtle pill/dot
        sub_frame = tk.Frame(content, bg=COLORS["bg_card"])
        sub_frame.pack(anchor="w", fill="x", pady=(2, 0))

        dot_lbl = tk.Label(
            sub_frame,
            text="●",
            font=("Segoe UI", 6),
            bg=COLORS["bg_card"],
            fg=self.accent_color
        )
        dot_lbl.pack(side="left", padx=(0, 4))

        self.sub_lbl = tk.Label(
            sub_frame,
            text=subtext,
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"]
        )
        self.sub_lbl.pack(side="left")

    def update_value(self, value, subtext=None):
        self.val_lbl.config(text=value)
        if subtext is not None:
            self.sub_lbl.config(text=subtext)

