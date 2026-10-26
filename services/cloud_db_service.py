"""
Cloud Database Service & PostgreSQL Sync Engine
Provides multi-PC real-time database synchronization via PostgreSQL (Supabase, Neon, AWS, etc.).
Includes connection testing, automatic schema initialization, and data migration.
"""

import os
import sys
import json
import sqlite3
import psycopg2
import psycopg2.extras
from pathlib import Path
from config import BASE_DIR, DB_PATH

CLOUD_CONFIG_FILE = Path(BASE_DIR) / "cloud_config.json"


def get_cloud_config():
    """Reads cloud database settings."""
    default_config = {
        "enabled": False,
        "connection_url": "",
        "ssl_mode": "require",
        "last_sync": None
    }
    if CLOUD_CONFIG_FILE.exists():
        try:
            with open(CLOUD_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception as ex:
            print("Error loading cloud config:", ex)
    return default_config


def save_cloud_config(config_data):
    """Saves cloud database settings to cloud_config.json."""
    try:
        current = get_cloud_config()
        current.update(config_data)
        with open(CLOUD_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return True, "Cloud configuration saved successfully."
    except Exception as ex:
        return False, f"Failed to save cloud config: {str(ex)}"


def sanitize_postgres_url(raw_url):
    """
    Handles passwords containing '@' or special characters and auto-fixes Supabase direct IPv6 links to IPv4 Pooler.
    """
    import urllib.parse
    import re

    url = raw_url.strip()
    if not url:
        return url

    # 1. URL encode password if multiple @ symbols exist
    if url.count('@') > 1 and '://' in url:
        userinfo_part, host_part = url.rsplit('@', 1)
        prefix, rest = userinfo_part.split('://', 1)
        if ':' in rest:
            user, raw_pass = rest.split(':', 1)
            encoded_pass = urllib.parse.quote_plus(raw_pass)
            url = f"{prefix}://{user}:{encoded_pass}@{host_part}"

    # 2. Check if it is a Supabase direct link (IPv6 only) and convert to IPv4 Pooler
    m = re.search(r'db\.([a-z0-9]+)\.supabase\.co', url)
    if m:
        project_ref = m.group(1)
        parts = url.split('@')
        left = parts[0]
        if '://postgres:' in left:
            left = left.replace('://postgres:', f'://postgres.{project_ref}:')
        url = f"{left}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

    return url


def test_connection(connection_url):
    """Tests connection to PostgreSQL database."""
    if not connection_url or not connection_url.strip():
        return False, "Connection URL cannot be empty."

    url = sanitize_postgres_url(connection_url)
    try:
        conn = psycopg2.connect(url, connect_timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        ver = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"Connection Successful!\nServer: {ver.split(',')[0]}"
    except Exception as ex:
        return False, f"Connection Failed:\n{str(ex)}"


def convert_sqlite_schema_to_postgres(sqlite_sql):
    """Translates SQLite schema definitions to PostgreSQL syntax."""
    sql = sqlite_sql
    # Auto-increment & Primary Key
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
    # Data types
    sql = sql.replace("REAL", "DOUBLE PRECISION")
    sql = sql.replace("TIMESTAMP", "TEXT")
    return sql


def init_cloud_schema(connection_url):
    """Initializes tables and columns in the PostgreSQL cloud database."""
    from database.schema import CREATE_TABLES_SQL

    url = sanitize_postgres_url(connection_url)
    try:
        conn = psycopg2.connect(url, connect_timeout=15)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SET datestyle = 'ISO, DMY';")

        # 1. Base Tables
        pg_sql = convert_sqlite_schema_to_postgres(CREATE_TABLES_SQL)
        for stmt in pg_sql.split(";"):
            statement = stmt.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as ex:
                    print(f"Schema stmt notice: {ex}")

        # Ensure all timestamp columns are TEXT to avoid out-of-range errors on formatted dates
        timestamp_cols = [
            ("stock_adjustments", "adjustment_date"),
            ("sales_orders", "created_at"),
            ("purchase_orders", "created_at"),
            ("payments", "created_at"),
            ("contacts", "created_at"),
            ("users", "created_at"),
            ("items", "created_at"),
            ("items", "updated_at"),
            ("customer_pos", "created_at"),
            ("customer_po_dispatches", "created_at"),
            ("fiscal_years", "created_at"),
            ("fiscal_years", "closed_at"),
            ("processed_email_pos", "created_at")
        ]
        for tbl, col in timestamp_cols:
            try:
                cursor.execute(f"ALTER TABLE {tbl} ALTER COLUMN {col} TYPE TEXT USING {col}::text;")
            except Exception:
                pass

        # 2. Add any migration columns
        migrations = [
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS eway_bill_no TEXT;",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS fiscal_year TEXT DEFAULT '2026-2027';",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS current_fiscal_year TEXT DEFAULT '2026-2027';",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS customer_po_id INTEGER;",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS freight DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'Paid';",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS po_number TEXT;",
            "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS po_date TEXT;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS freight DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS cgst_amount DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS sgst_amount DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS igst_amount DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS round_off DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE items ADD COLUMN IF NOT EXISTS subcategory TEXT DEFAULT '';",
            "ALTER TABLE purchase_order_items ADD COLUMN IF NOT EXISTS subcategory TEXT DEFAULT '';",
            "ALTER TABLE customer_pos ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE customer_pos ADD COLUMN IF NOT EXISTS cgst_amount DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE customer_pos ADD COLUMN IF NOT EXISTS sgst_amount DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE customer_pos ADD COLUMN IF NOT EXISTS gst_rate DOUBLE PRECISION DEFAULT 18.0;",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS udyam_reg_no TEXT DEFAULT 'UDYAM-UP-18-0048627';",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS gmail_address TEXT DEFAULT '';",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS gmail_app_password TEXT DEFAULT '';",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS gmail_filter_keywords TEXT DEFAULT 'PO, Purchase Order, Order, CPO';",
            """CREATE TABLE IF NOT EXISTS processed_email_pos (
                id SERIAL PRIMARY KEY,
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
            except Exception:
                pass

        cursor.close()
        conn.close()
        return True, "Cloud database schema initialized successfully!"
    except Exception as ex:
        return False, f"Failed to initialize cloud database schema:\n{str(ex)}"


def migrate_local_to_cloud(connection_url, progress_callback=None):
    """
    Migrates all data from local SQLite (inventory_system.db) into the PostgreSQL cloud database.
    """
    if not os.path.exists(DB_PATH):
        return False, f"Local database not found at {DB_PATH}"

    # 1. Initialize remote schema first
    ok, msg = init_cloud_schema(connection_url)
    if not ok:
        return False, msg

    tables_in_order = [
        "users",
        "company_profile",
        "fiscal_years",
        "contacts",
        "items",
        "stock_adjustments",
        "sales_orders",
        "sales_order_items",
        "purchase_orders",
        "purchase_order_items",
        "customer_pos",
        "customer_po_items",
        "customer_po_dispatches",
        "payments",
        "processed_email_pos"
    ]

    try:
        sqlite_conn = sqlite3.connect(DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        clean_url = sanitize_postgres_url(connection_url)
        pg_conn = psycopg2.connect(clean_url, connect_timeout=15)
        pg_conn.autocommit = False
        pg_cur = pg_conn.cursor()
        pg_cur.execute("SET datestyle = 'ISO, DMY';")

        total_tables = len(tables_in_order)
        migrated_counts = {}

        for idx, table in enumerate(tables_in_order):
            if progress_callback:
                progress_callback(f"Migrating table {idx+1}/{total_tables}: {table}...", int((idx / total_tables) * 100))

            # Fetch existing records from SQLite
            try:
                sqlite_cur.execute(f"SELECT * FROM {table}")
                rows = sqlite_cur.fetchall()
            except sqlite3.OperationalError:
                continue

            if not rows:
                migrated_counts[table] = 0
                continue

            # Clear remote table cleanly
            pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")

            col_names = list(rows[0].keys())
            cols_joined = ", ".join(col_names)
            placeholders = ", ".join(["%s"] * len(col_names))

            insert_sql = f"INSERT INTO {table} ({cols_joined}) VALUES ({placeholders})"

            data_tuples = [tuple(row[col] for col in col_names) for row in rows]
            psycopg2.extras.execute_batch(pg_cur, insert_sql, data_tuples)
            migrated_counts[table] = len(rows)

            # Update serial sequence to avoid primary key conflicts
            try:
                pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1) + 1, false);")
            except Exception:
                pass

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()
        sqlite_conn.close()

        summary_lines = [f"• {t}: {cnt} records" for t, cnt in migrated_counts.items() if cnt > 0]
        summary_text = "\n".join(summary_lines) if summary_lines else "Schema ready (0 existing records to transfer)."
        return True, f"Migration Completed Successfully!\n\nUploaded to Cloud:\n{summary_text}"
    except Exception as ex:
        return False, f"Migration Failed:\n{str(ex)}"
