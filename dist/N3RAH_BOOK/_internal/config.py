"""
App Configuration and Design System Constants
Sleek Modern Midnight & Electric Indigo Theme (N3Rah Enterprise Edition)
"""

import os
import sys
from pathlib import Path

# Paths
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "inventory_system.db"
EXPORTS_DIR = BASE_DIR / "exports"
INVOICES_DIR = BASE_DIR / "generated_invoices"

# Ensure directories exist
EXPORTS_DIR.mkdir(exist_ok=True)
INVOICES_DIR.mkdir(exist_ok=True)

# Theme Palette (100% Executive Pure Light Mode Theme)
COLORS = {
    "bg_dark": "#F8FAFC",       # Soft Off-White Main Content Area
    "bg_sidebar": "#FFFFFF",    # Pure White Crisp Sidebar
    "bg_card": "#FFFFFF",       # Pure White Elevated Card Surface
    "bg_card_alt": "#F1F5F9",   # Soft Gray Input / Table Header Surface
    "bg_header": "#FFFFFF",     # Clean White Top Header Surface
    "border": "#E2E8F0",        # Crisp Light Slate Border
    "border_light": "#F1F5F9",  # Extra Light Border Accent
    
    # Accents & Brand Colors
    "primary": "#4F46E5",       # Executive Indigo Primary
    "primary_hover": "#6366F1", # Light Indigo Hover
    "primary_active": "#4338CA",# Deep Indigo Active
    
    "secondary": "#F1F5F9",     # Light Secondary Button Surface
    "accent": "#0284C7",        # Ocean Blue Accent
    "purple": "#9333EA",        # Rich Purple Accent
    
    "text_light": "#0F172A",    # Crisp Dark Slate Text for All Surfaces
    "text_muted": "#64748B",    # Muted Cool Gray Text
    "text_dark": "#0F172A",     # Dark Slate Text
    
    "success": "#10B981",      # Emerald Green
    "warning": "#D97706",      # Amber Yellow
    "danger": "#EF4444",       # Rose Red
    "info": "#0284C7",         # Sky Blue
    
    # Status Badges
    "badge_instock": "#DCFCE7",   # Soft Emerald Light
    "badge_lowstock": "#FEF3C7",  # Soft Amber Light
    "badge_outstock": "#FEE2E2",  # Soft Rose Light
}

# Typography (Segoe UI Modern Vector Fonts - 2px Larger)
FONTS = {
    "title": ("Segoe UI", 21, "bold"),
    "subtitle": ("Segoe UI", 16, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 11),
    "mono": ("Consolas", 12),
}

# Company Profile Defaults
COMPANY_PROFILE = {
    "name": "My Business Enterprise",
    "address": "Enter Company Address Here",
    "gstin": "",
    "pan": "",
    "mobile": "",
    "email": "",
    "udyam_reg_no": "UDYAM-UP-18-0048627",
    "bank_name": "",
    "bank_branch": "",
    "account_no": "",
    "ifsc_code": "",
    "terms": [
        "1. Goods once sold will not be taken back or exchanged",
        "2. All disputes are subject to local jurisdiction only"
    ]
}
