"""
N3RAH BOOK — Dual Standalone Setup Installer Build Engine
Builds two standalone single-file Windows setup wizards:
1. dist/N3RAH_BOOK_Setup_With_Data.exe   -> Full current live database + invoices
2. dist/N3RAH_BOOK_Setup_Fresh_Clean.exe -> Clean / fresh empty database
Includes PostgreSQL (psycopg2) cloud sync support, app_icon.ico, and desktop shortcuts.
"""

import os
import sys
import json
import shutil
import hashlib
import sqlite3
import subprocess
from pathlib import Path
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_ICO = os.path.join(ASSETS_DIR, "app_icon.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "logo_icon.png")


def ensure_icon():
    """Ensures app_icon.ico exists in assets folder."""
    if not os.path.exists(ICON_ICO) and os.path.exists(ICON_PNG):
        try:
            img = Image.open(ICON_PNG)
            img.save(ICON_ICO, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print(f"[OK] Generated {ICON_ICO}")
        except Exception as ex:
            print(f"[WARN] Could not generate .ico: {ex}")


def build_base_app_bundle():
    """Compiles the core application bundle dist/N3RAH_BOOK with all dependencies."""
    print("\n" + "=" * 60)
    print("STEP 1: Compiling Base Application Bundle (N3RAH_BOOK)")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=N3RAH_BOOK",
        "--add-data=assets;assets",
        "--add-data=config.py;.",
        "--hidden-import=psycopg2",
        "--hidden-import=psycopg2.extras",
        "--hidden-import=psycopg2.pool",
        f"--icon={ICON_ICO if os.path.exists(ICON_ICO) else ICON_PNG}",
        "main.py"
    ]
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[ERROR] Base app build failed!")
        sys.exit(1)

    target_bundle = os.path.join(DIST_DIR, "N3RAH_BOOK")
    assets_dst = os.path.join(target_bundle, "assets")
    if os.path.exists(ASSETS_DIR) and not os.path.exists(assets_dst):
        shutil.copytree(ASSETS_DIR, assets_dst)
    print(f"[OK] Base bundle ready at: {target_bundle}")
    return target_bundle


def create_fresh_database(target_path):
    """Creates a pristine, clean database with initial schema and default admin."""
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
        except Exception:
            pass

    from database.schema import CREATE_TABLES_SQL
    from config import COMPANY_PROFILE

    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    for statement in CREATE_TABLES_SQL.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)

    migrations = [
        "ALTER TABLE sales_orders ADD COLUMN eway_bill_no TEXT;",
        "ALTER TABLE sales_orders ADD COLUMN fiscal_year TEXT DEFAULT '2026-2027';",
        "ALTER TABLE company_profile ADD COLUMN current_fiscal_year TEXT DEFAULT '2026-2027';",
        "ALTER TABLE sales_orders ADD COLUMN customer_po_id INTEGER;",
        "ALTER TABLE sales_orders ADD COLUMN freight REAL DEFAULT 0.0;",
        "ALTER TABLE sales_orders ADD COLUMN payment_status TEXT DEFAULT 'Paid';",
        "ALTER TABLE sales_orders ADD COLUMN po_number TEXT;",
        "ALTER TABLE sales_orders ADD COLUMN po_date TEXT;",
        "ALTER TABLE purchase_orders ADD COLUMN subtotal REAL DEFAULT 0.0;",
        "ALTER TABLE purchase_orders ADD COLUMN freight REAL DEFAULT 0.0;",
        "ALTER TABLE purchase_orders ADD COLUMN cgst_amount REAL DEFAULT 0.0;",
        "ALTER TABLE purchase_orders ADD COLUMN sgst_amount REAL DEFAULT 0.0;",
        "ALTER TABLE purchase_orders ADD COLUMN igst_amount REAL DEFAULT 0.0;",
        "ALTER TABLE purchase_orders ADD COLUMN round_off REAL DEFAULT 0.0;",
        "ALTER TABLE items ADD COLUMN subcategory TEXT DEFAULT '';",
        "ALTER TABLE purchase_order_items ADD COLUMN subcategory TEXT DEFAULT '';",
        "ALTER TABLE customer_pos ADD COLUMN subtotal REAL DEFAULT 0.0;",
        "ALTER TABLE customer_pos ADD COLUMN cgst_amount REAL DEFAULT 0.0;",
        "ALTER TABLE customer_pos ADD COLUMN sgst_amount REAL DEFAULT 0.0;",
        "ALTER TABLE customer_pos ADD COLUMN gst_rate REAL DEFAULT 18.0;",
        "ALTER TABLE company_profile ADD COLUMN udyam_reg_no TEXT DEFAULT 'UDYAM-UP-18-0048627';",
        "ALTER TABLE company_profile ADD COLUMN gmail_address TEXT DEFAULT '';",
        "ALTER TABLE company_profile ADD COLUMN gmail_app_password TEXT DEFAULT '';",
        "ALTER TABLE company_profile ADD COLUMN gmail_filter_keywords TEXT DEFAULT 'PO, Purchase Order, Order, CPO';",
        """CREATE TABLE IF NOT EXISTS processed_email_pos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            received_date TEXT,
            pdf_filename TEXT,
            po_number TEXT,
            customer_id INTEGER,
            status TEXT DEFAULT 'Imported',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""
    ]
    for mig in migrations:
        try:
            cursor.execute(mig)
        except sqlite3.OperationalError:
            pass

    p_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, role, status) VALUES (?, ?, ?, ?, ?)",
        ("admin", p_hash, "Admin User", "Admin", "Active")
    )

    cursor.execute(
        "INSERT OR IGNORE INTO fiscal_years (year_label, start_date, end_date, status) VALUES (?, ?, ?, ?)",
        ("2026-2027", "2026-04-01", "2027-03-31", "Active")
    )

    default_terms = (
        "1. Goods once sold will not be taken back or exchanged.\n"
        "2. All disputes are subject to local jurisdiction only."
    )
    cursor.execute("""
        INSERT OR REPLACE INTO company_profile (
            id, name, address, gstin, pan, mobile, email, udyam_reg_no,
            bank_name, bank_branch, account_no, ifsc_code, terms, current_fiscal_year,
            gmail_address, gmail_app_password, gmail_filter_keywords
        ) VALUES (
            1, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?
        )
    """, (
        COMPANY_PROFILE.get("name", "My Business Enterprise"),
        COMPANY_PROFILE.get("address", "Enter Registered Business Address Here"),
        COMPANY_PROFILE.get("gstin", ""),
        COMPANY_PROFILE.get("pan", ""),
        COMPANY_PROFILE.get("mobile", ""),
        COMPANY_PROFILE.get("email", ""),
        COMPANY_PROFILE.get("udyam_reg_no", "UDYAM-UP-18-0048627"),
        COMPANY_PROFILE.get("bank_name", ""),
        COMPANY_PROFILE.get("bank_branch", ""),
        COMPANY_PROFILE.get("account_no", ""),
        COMPANY_PROFILE.get("ifsc_code", ""),
        default_terms,
        "2026-2027",
        "", "", "PO, Purchase Order, Order, CPO"
    ))

    conn.commit()
    conn.close()
    print(f"[OK] Clean database initialized at: {target_path}")


def build_installer_variant(bundle_dir, variant_name, db_source_path, metadata, include_invoices=True):
    """Compiles a standalone installer .exe for a given variant."""
    print("\n" + "=" * 60)
    print(f"BUILDING INSTALLER: {variant_name}")
    print("=" * 60)

    staging_dir = os.path.join(BASE_DIR, f"staging_{variant_name}")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)

    shutil.copytree(bundle_dir, staging_dir)

    db_dest = os.path.join(staging_dir, "inventory_system.db")
    shutil.copy2(db_source_path, db_dest)
    print(f"[OK] Injected variant database: {db_dest}")

    invoices_dst = os.path.join(staging_dir, "generated_invoices")
    if os.path.exists(invoices_dst):
        shutil.rmtree(invoices_dst, ignore_errors=True)
    os.makedirs(invoices_dst, exist_ok=True)

    invoices_src = os.path.join(BASE_DIR, "generated_invoices")
    if include_invoices and os.path.exists(invoices_src):
        for f in os.listdir(invoices_src):
            src_f = os.path.join(invoices_src, f)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, os.path.join(invoices_dst, f))
        print(f"[OK] Bundled {len(os.listdir(invoices_dst))} invoice PDFs.")

    session_file = os.path.join(staging_dir, ".session.json")
    if os.path.exists(session_file):
        os.remove(session_file)

    exports_dst = os.path.join(staging_dir, "exports")
    if os.path.exists(exports_dst):
        shutil.rmtree(exports_dst, ignore_errors=True)
    os.makedirs(exports_dst, exist_ok=True)

    payload_zip = os.path.join(BASE_DIR, "app_payload.zip")
    if os.path.exists(payload_zip):
        os.remove(payload_zip)

    print(f"Creating payload archive for {variant_name}...")
    shutil.make_archive(os.path.join(BASE_DIR, "app_payload"), 'zip', staging_dir)
    print(f"[OK] Payload created: {payload_zip} ({os.path.getsize(payload_zip) / (1024*1024):.2f} MB)")

    info_json_path = os.path.join(BASE_DIR, "installer_info.json")
    with open(info_json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    installer_exe_name = variant_name
    print(f"Compiling {installer_exe_name}.exe...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={installer_exe_name}",
        f"--add-data={payload_zip};.",
        f"--add-data={info_json_path};.",
        f"--icon={ICON_ICO if os.path.exists(ICON_ICO) else ICON_PNG}",
        "setup_wizard.py"
    ]
    res = subprocess.run(cmd, cwd=BASE_DIR)

    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)
    if os.path.exists(payload_zip):
        os.remove(payload_zip)
    if os.path.exists(info_json_path):
        os.remove(info_json_path)

    installer_output = os.path.join(DIST_DIR, f"{installer_exe_name}.exe")
    if res.returncode == 0 and os.path.exists(installer_output):
        sz_mb = os.path.getsize(installer_output) / (1024 * 1024)
        print(f"[SUCCESS] Installer created: {installer_output} ({sz_mb:.2f} MB)")
        return installer_output
    else:
        print(f"[ERROR] Failed to compile {installer_exe_name}!")
        return None


def main():
    ensure_icon()

    bundle_dir = build_base_app_bundle()

    # 1. Installer With Complete Current Data
    meta_full = {
        "title": "N3RAH BOOK — Setup Wizard (Complete Current Data)",
        "edition": "Complete Current Data Edition",
        "badge": "📦 Full Database Included (All Products, Customers & Invoices)",
        "description": "Installs N3RAH BOOK with your complete current data and transactions.",
        "admin_note": "Admin Credentials: username 'admin', password 'admin123' (or custom)"
    }
    live_db = os.path.join(BASE_DIR, "inventory_system.db")
    installer_full = build_installer_variant(
        bundle_dir=bundle_dir,
        variant_name="N3RAH_BOOK_Setup_With_Data",
        db_source_path=live_db,
        metadata=meta_full,
        include_invoices=True
    )

    # 2. Installer Fresh Clean Installation (No Data)
    temp_clean_db = os.path.join(BASE_DIR, "temp_clean_inventory.db")
    create_fresh_database(temp_clean_db)

    meta_fresh = {
        "title": "N3RAH BOOK — Setup Wizard (Fresh Clean Edition)",
        "edition": "Fresh Installation (Zero Data)",
        "badge": "✨ Clean Database (Zero Items & Invoices, Ready for New Business)",
        "description": "Installs a brand new instance of N3RAH BOOK with blank inventory and clean ledger.",
        "admin_note": "Default Admin Account: username 'admin', password 'admin123'"
    }
    installer_fresh = build_installer_variant(
        bundle_dir=bundle_dir,
        variant_name="N3RAH_BOOK_Setup_Fresh_Clean",
        db_source_path=temp_clean_db,
        metadata=meta_fresh,
        include_invoices=False
    )

    if os.path.exists(temp_clean_db):
        try:
            os.remove(temp_clean_db)
        except Exception:
            pass

    print("\n" + "=" * 65)
    print("DUAL STANDALONE INSTALLER BUILD REPORT")
    print("=" * 65)
    if installer_full:
        sz1 = os.path.getsize(installer_full) / (1024 * 1024)
        print(f"1. FULL DATA INSTALLER:")
        print(f"   Path: {installer_full}")
        print(f"   Size: {sz1:.2f} MB")
        print(f"   Contents: Full live database & invoice PDFs\n")

    if installer_fresh:
        sz2 = os.path.getsize(installer_fresh) / (1024 * 1024)
        print(f"2. FRESH CLEAN INSTALLER:")
        print(f"   Path: {installer_fresh}")
        print(f"   Size: {sz2:.2f} MB")
        print(f"   Contents: Clean database (Admin: admin/admin123, 0 items, 0 invoices)\n")

    # 3. Create Standalone Portable ZIP
    zip_dest = os.path.join(BASE_DIR, "N3RAH_BOOK_Standalone.zip")
    if os.path.exists(zip_dest):
        try:
            os.remove(zip_dest)
        except Exception:
            pass
    db_src = os.path.join(BASE_DIR, "inventory_system.db")
    db_dst = os.path.join(bundle_dir, "inventory_system.db")
    if os.path.exists(db_src):
        shutil.copy2(db_src, db_dst)

    print("Creating N3RAH_BOOK_Standalone.zip...")
    shutil.make_archive(os.path.join(BASE_DIR, "N3RAH_BOOK_Standalone"), 'zip', bundle_dir)
    if os.path.exists(zip_dest):
        sz_zip = os.path.getsize(zip_dest) / (1024 * 1024)
        print(f"3. PORTABLE STANDALONE ZIP:")
        print(f"   Path: {zip_dest}")
        print(f"   Size: {sz_zip:.2f} MB")
        print(f"   Contents: Portable folder ready to unzip & run without installation!\n")

    print("All standalone packages are ready for deployment on any other Windows PC!")
    print("=" * 65)


if __name__ == "__main__":
    main()
