"""
Custom TTK Theme and Styling Configuration
Configures modern midnight & electric indigo theme styles for Tkinter widgets.
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS

def apply_app_styles(root):
    style = ttk.Style(root)
    
    # Base theme configuration
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')

    # General Frames & Cards
    style.configure("TFrame", background=COLORS["bg_dark"])
    style.configure("Sidebar.TFrame", background=COLORS["bg_sidebar"])
    style.configure("Header.TFrame", background=COLORS["bg_header"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat", borderwidth=1)
    
    # Labels
    style.configure("TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_light"], font=FONTS["body"])
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_light"], font=FONTS["body"])
    style.configure("CardMuted.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_muted"], font=FONTS["small"])
    style.configure("Title.TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_light"], font=FONTS["title"])
    style.configure("Header.TLabel", background=COLORS["bg_header"], foreground=COLORS["text_light"], font=FONTS["heading"])
    
    # Primary Button (Indigo with White Text)
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground="#FFFFFF",
        font=FONTS["body_bold"],
        borderwidth=0,
        focuscolor="none",
        padding=(14, 7)
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("pressed", COLORS["primary_active"])],
        foreground=[("active", "#FFFFFF")]
    )

    # Secondary Button (Light Gray with Dark Text)
    style.configure(
        "Secondary.TButton",
        background=COLORS["secondary"],
        foreground=COLORS["text_dark"],
        font=FONTS["body"],
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Secondary.TButton",
        background=[("active", COLORS["border"])],
        foreground=[("active", COLORS["text_dark"])]
    )

    # Success Button (Emerald Green with White Text)
    style.configure(
        "Success.TButton",
        background=COLORS["success"],
        foreground="#FFFFFF",
        font=FONTS["body_bold"],
        borderwidth=0,
        padding=(14, 7)
    )
    style.map(
        "Success.TButton",
        background=[("active", "#059669")]
    )

    # Entry Fields (White background with Dark text and Slate Border)
    style.configure(
        "TEntry",
        fieldbackground="#FFFFFF",
        foreground=COLORS["text_dark"],
        insertcolor=COLORS["text_dark"],
        borderwidth=1,
        relief="flat"
    )
    style.map("TEntry", fieldbackground=[("focus", "#FFFFFF")])

    # Combobox (White background with Dark text)
    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        background="#FFFFFF",
        foreground=COLORS["text_dark"],
        arrowcolor=COLORS["primary"],
        borderwidth=1
    )
    style.map("TCombobox", fieldbackground=[("readonly", "#FFFFFF")])

    # Treeview Data Table (Clean White Grid with Soft Gray Headers)
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground=COLORS["text_dark"],
        fieldbackground="#FFFFFF",
        font=FONTS["body"],
        rowheight=36,
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["bg_card_alt"],
        foreground=COLORS["text_dark"],
        font=FONTS["body_bold"],
        relief="flat",
        padding=(10, 8)
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary"])],
        foreground=[("selected", "#FFFFFF")]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["border"])]
    )

    # Scrollbars
    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["bg_card_alt"],
        troughcolor=COLORS["bg_dark"],
        bordercolor=COLORS["bg_dark"],
        arrowcolor=COLORS["text_muted"]
    )
