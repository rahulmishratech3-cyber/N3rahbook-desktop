"""
SQLite Database Connection and Query Manager
"""

import sqlite3
from pathlib import Path
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        from database.schema import CREATE_TABLES_SQL
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for statement in CREATE_TABLES_SQL.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)

            # Auto-migrations for existing databases
            try:
                cursor.execute("ALTER TABLE sales_orders ADD COLUMN eway_bill_no TEXT;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE sales_orders ADD COLUMN fiscal_year TEXT DEFAULT '2026-2027';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE company_profile ADD COLUMN current_fiscal_year TEXT DEFAULT '2026-2027';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE sales_orders ADD COLUMN customer_po_id INTEGER;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE sales_orders ADD COLUMN freight REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE sales_orders ADD COLUMN payment_status TEXT DEFAULT 'Paid';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE purchase_orders ADD COLUMN subtotal REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE purchase_orders ADD COLUMN cgst_amount REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE purchase_orders ADD COLUMN sgst_amount REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE items ADD COLUMN subcategory TEXT DEFAULT '';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE purchase_order_items ADD COLUMN subcategory TEXT DEFAULT '';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE customer_pos ADD COLUMN subtotal REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE customer_pos ADD COLUMN cgst_amount REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE customer_pos ADD COLUMN sgst_amount REAL DEFAULT 0.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE customer_pos ADD COLUMN gst_rate REAL DEFAULT 18.0;")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE company_profile ADD COLUMN udyam_reg_no TEXT DEFAULT 'UDYAM-UP-18-0048627';")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("UPDATE company_profile SET udyam_reg_no = 'UDYAM-UP-18-0048627' WHERE udyam_reg_no IS NULL OR udyam_reg_no = '';")
            except Exception:
                pass

            try:
                cursor.execute("""
                    UPDATE items SET cost_price = (
                        SELECT poi.unit_cost FROM purchase_order_items poi 
                        WHERE poi.item_id = items.id AND poi.unit_cost > 0 
                        ORDER BY poi.id DESC LIMIT 1
                    )
                    WHERE (cost_price = 0 OR cost_price IS NULL) AND EXISTS (
                        SELECT 1 FROM purchase_order_items poi 
                        WHERE poi.item_id = items.id AND poi.unit_cost > 0
                    );
                """)
                cursor.execute("""
                    UPDATE items SET selling_price = (
                        SELECT soi.unit_price FROM sales_order_items soi 
                        WHERE soi.item_id = items.id AND soi.unit_price > 0 
                        ORDER BY soi.id DESC LIMIT 1
                    )
                    WHERE (selling_price = 0 OR selling_price IS NULL) AND EXISTS (
                        SELECT 1 FROM sales_order_items soi 
                        WHERE soi.item_id = items.id AND soi.unit_price > 0
                    );
                """)
            except Exception:
                pass

            try:
                cursor.execute("UPDATE items SET category = 'PU FOAM SHEETS' WHERE category = 'FOAM SHEETS';")
            except Exception:
                pass

            # Backfill existing sales orders into stock adjustments ledger if not already present
            try:
                cursor.execute("""
                    INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes, adjustment_date)
                    SELECT 
                        soi.item_id,
                        'Remove',
                        soi.quantity,
                        'Sales Invoice',
                        'Admin',
                        'Deducted via Invoice #' || so.invoice_number,
                        so.invoice_date
                    FROM sales_order_items soi
                    JOIN sales_orders so ON soi.sales_order_id = so.id
                    WHERE so.status != 'Cancelled'
                      AND NOT EXISTS (
                          SELECT 1 FROM stock_adjustments sa 
                          WHERE sa.notes LIKE '%' || so.invoice_number || '%'
                      )
                """)
            except Exception:
                pass

            conn.commit()

    def execute_query(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_all(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

# Singleton DB Instance
db = DatabaseManager()
