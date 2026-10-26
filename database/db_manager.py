"""
Dual Database Connection and Query Manager
Supports both local SQLite and Cloud PostgreSQL (Supabase / Neon / AWS).
Automatically maps placeholders (? -> %s), emulates cursor.lastrowid, and provides dict-compatible rows.
"""

import os
import sys
import sqlite3
from pathlib import Path
from config import DB_PATH

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def _convert_placeholders(sql):
    """Replaces unquoted '?' with '%s' for PostgreSQL compatibility."""
    result = []
    in_single_quote = False
    in_double_quote = False
    for char in sql:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            result.append(char)
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            result.append(char)
        elif char == '?' and not in_single_quote and not in_double_quote:
            result.append('%s')
        else:
            result.append(char)
    return ''.join(result)


def _sanitize_postgres_url(raw_url):
    import urllib.parse
    import re
    url = raw_url.strip()
    if not url:
        return url
    if url.count('@') > 1 and '://' in url:
        userinfo_part, host_part = url.rsplit('@', 1)
        prefix, rest = userinfo_part.split('://', 1)
        if ':' in rest:
            user, raw_pass = rest.split(':', 1)
            encoded_pass = urllib.parse.quote_plus(raw_pass)
            url = f"{prefix}://{user}:{encoded_pass}@{host_part}"
    m = re.search(r'db\.([a-z0-9]+)\.supabase\.co', url)
    if m:
        project_ref = m.group(1)
        parts = url.split('@')
        left = parts[0]
        if '://postgres:' in left:
            left = left.replace('://postgres:', f'://postgres.{project_ref}:')
        url = f"{left}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    return url


class PostgresCursorWrapper:
    """Wraps a psycopg2 cursor to match sqlite3 cursor behavior (lastrowid, ?, dict access)."""
    def __init__(self, real_cursor):
        self._cursor = real_cursor
        self.lastrowid = None

    def execute(self, query, params=()):
        pg_query = _convert_placeholders(query).strip()
        is_insert = pg_query.upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in pg_query.upper()

        if is_insert and not has_returning:
            # Append RETURNING id to capture lastrowid
            pg_query_with_returning = f"{pg_query} RETURNING id;"
            try:
                self._cursor.execute(pg_query_with_returning, params or None)
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row['id'] if isinstance(row, dict) or hasattr(row, 'get') else row[0]
                return self
            except Exception:
                # Fallback if table does not have an 'id' column
                self._cursor.connection.rollback()
                self._cursor.execute(pg_query, params or None)
                self.lastrowid = None
                return self
        else:
            self._cursor.execute(pg_query, params or None)
            return self

    def executemany(self, query, param_seq):
        pg_query = _convert_placeholders(query).strip()
        self._cursor.executemany(pg_query, param_seq)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows] if rows else []

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnectionWrapper:
    """Wraps a psycopg2 connection (from pool or standalone) to match sqlite3 interface."""
    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def commit(self):
        if not self._closed and not self._conn.closed:
            self._conn.commit()

    def rollback(self):
        if not self._closed and not self._conn.closed:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def close(self):
        if not self._closed:
            self._closed = True
            if self._pool is not None:
                try:
                    if not self._conn.closed:
                        self._conn.rollback()
                        self._pool.putconn(self._conn)
                    else:
                        self._pool.putconn(self._conn, close=True)
                except Exception:
                    try:
                        self._pool.putconn(self._conn, close=True)
                    except Exception:
                        pass
            else:
                try:
                    self._conn.close()
                except Exception:
                    pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

    def execute(self, query, params=()):
        cur = self.cursor()
        cur.execute(query, params)
        return cur


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.cloud_mode = False
        self.cloud_url = ""
        self._pg_pool = None
        self.reload_backend()

    def _init_pg_pool(self):
        """Initializes or resets the PostgreSQL connection pool."""
        if not PSYCOPG2_AVAILABLE or not self.cloud_url:
            return
        if self._pg_pool:
            try:
                self._pg_pool.closeall()
            except Exception:
                pass
            self._pg_pool = None
        try:
            import psycopg2.pool
            clean_url = _sanitize_postgres_url(self.cloud_url)
            self._pg_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=clean_url,
                cursor_factory=psycopg2.extras.DictCursor
            )
            conn = self._pg_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SET datestyle = 'ISO, DMY';")
                pg_migrations = [
                    "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS freight DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS igst_amount DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS freight DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS cgst_amount DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS sgst_amount DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS igst_amount DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS round_off DOUBLE PRECISION DEFAULT 0.0;",
                    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'Unpaid';"
                ]
                for mig in pg_migrations:
                    try:
                        cur.execute(mig)
                    except Exception:
                        pass
            conn.commit()
            self._pg_pool.putconn(conn)
        except Exception as ex:
            print(f"[DB WARNING] Failed to initialize PostgreSQL pool ({ex}).")
            self._pg_pool = None

    def reload_backend(self):
        """Checks cloud configuration and sets active backend (SQLite or PostgreSQL)."""
        if self._pg_pool:
            try:
                self._pg_pool.closeall()
            except Exception:
                pass
            self._pg_pool = None

        config_file = Path(self.db_path).parent / "cloud_config.json"
        if config_file.exists():
            try:
                import json
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("enabled") and cfg.get("connection_url") and PSYCOPG2_AVAILABLE:
                    self.cloud_mode = True
                    self.cloud_url = cfg["connection_url"].strip()
                    display_host = self.cloud_url.split('@')[-1] if '@' in self.cloud_url else 'configured'
                    print(f"[DB] Active Backend: Cloud PostgreSQL ({display_host})")
                    self._init_pg_pool()
                else:
                    self.cloud_mode = False
                    self.cloud_url = ""
                    print(f"[DB] Active Backend: Local SQLite ({self.db_path})")
            except Exception as ex:
                self.cloud_mode = False
                self.cloud_url = ""
                print(f"[DB] Error checking cloud config, default to SQLite: {ex}")
        else:
            self.cloud_mode = False
            self.cloud_url = ""
            print(f"[DB] Active Backend: Local SQLite ({self.db_path})")

        # Always initialize SQLite DB so it is ready for offline fallback
        self._init_sqlite_db()

    def get_connection(self):
        """Returns an active connection for either PostgreSQL or SQLite."""
        if self.cloud_mode and self.cloud_url:
            if not self._pg_pool:
                self._init_pg_pool()
            if self._pg_pool:
                try:
                    raw_conn = self._pg_pool.getconn()
                    if raw_conn.closed != 0:
                        self._pg_pool.putconn(raw_conn, close=True)
                        raw_conn = self._pg_pool.getconn()
                    return PostgresConnectionWrapper(raw_conn, pool=self._pg_pool)
                except Exception as ex:
                    print(f"[DB WARNING] Pool checkout failed ({ex}), resetting pool...")
                    try:
                        self._init_pg_pool()
                        if self._pg_pool:
                            raw_conn = self._pg_pool.getconn()
                            return PostgresConnectionWrapper(raw_conn, pool=self._pg_pool)
                    except Exception as err:
                        print(f"[DB WARNING] Cloud reconnect failed ({err}). Falling back to Local SQLite.")
        
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")  # High concurrency WAL mode
        return conn

    def _init_sqlite_db(self):
        from database.schema import CREATE_TABLES_SQL
        
        # Explicitly use sqlite3 connection for init so it always initializes local DB
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.cursor()
            for statement in CREATE_TABLES_SQL.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)

            # Auto-migrations for existing databases
            cols_to_add = [
                ("sales_orders", "eway_bill_no", "TEXT"),
                ("sales_orders", "fiscal_year", "TEXT DEFAULT '2026-2027'"),
                ("company_profile", "current_fiscal_year", "TEXT DEFAULT '2026-2027'"),
                ("sales_orders", "customer_po_id", "INTEGER"),
                ("sales_orders", "freight", "REAL DEFAULT 0.0"),
                ("sales_orders", "payment_status", "TEXT DEFAULT 'Paid'"),
                ("sales_orders", "po_number", "TEXT"),
                ("sales_orders", "po_date", "TEXT"),
                ("purchase_orders", "subtotal", "REAL DEFAULT 0.0"),
                ("purchase_orders", "freight", "REAL DEFAULT 0.0"),
                ("purchase_orders", "cgst_amount", "REAL DEFAULT 0.0"),
                ("purchase_orders", "sgst_amount", "REAL DEFAULT 0.0"),
                ("purchase_orders", "igst_amount", "REAL DEFAULT 0.0"),
                ("purchase_orders", "round_off", "REAL DEFAULT 0.0"),
                ("purchase_orders", "payment_status", "TEXT DEFAULT 'Unpaid'"),
                ("items", "subcategory", "TEXT DEFAULT ''"),
                ("purchase_order_items", "subcategory", "TEXT DEFAULT ''"),
                ("customer_pos", "subtotal", "REAL DEFAULT 0.0"),
                ("customer_pos", "cgst_amount", "REAL DEFAULT 0.0"),
                ("customer_pos", "sgst_amount", "REAL DEFAULT 0.0"),
                ("customer_pos", "gst_rate", "REAL DEFAULT 18.0"),
                ("company_profile", "udyam_reg_no", "TEXT DEFAULT 'UDYAM-UP-18-0048627'"),
                ("company_profile", "gmail_address", "TEXT DEFAULT ''"),
                ("company_profile", "gmail_app_password", "TEXT DEFAULT ''"),
                ("company_profile", "gmail_filter_keywords", "TEXT DEFAULT 'PO, Purchase Order, Order, CPO'")
            ]
            for table, col, col_type in cols_to_add:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
                except sqlite3.OperationalError:
                    pass

            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_email_pos (
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
                );
                """)
            conn.commit()

        try:
            from models.payment import PaymentModel
            PaymentModel.sync_all_existing_paid_invoices()
        except Exception:
            pass

    def _get_sqlite_fallback_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def execute_query(self, query, params=()):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except Exception as ex:
            if self.cloud_mode:
                print(f"[DB] Cloud query failed ({ex}). Falling back to SQLite.")
                with self._get_sqlite_fallback_conn() as fallback_conn:
                    cursor = fallback_conn.cursor()
                    cursor.execute(query, params)
                    fallback_conn.commit()
                    return cursor
            raise

    def fetch_all(self, query, params=()):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as ex:
            if self.cloud_mode:
                print(f"[DB] Cloud query failed ({ex}). Falling back to SQLite.")
                with self._get_sqlite_fallback_conn() as fallback_conn:
                    cursor = fallback_conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            raise

    def fetch_one(self, query, params=()):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as ex:
            if self.cloud_mode:
                print(f"[DB] Cloud query failed ({ex}). Falling back to SQLite.")
                with self._get_sqlite_fallback_conn() as fallback_conn:
                    cursor = fallback_conn.cursor()
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    return dict(row) if row else None
            raise


# Singleton DB Instance
db = DatabaseManager()
