"""
Database Seeder Service
Ensures default system records (such as Admin user) exist.
"""

from database.db_manager import db
from models.user import UserModel

def seed_database(force=False):
    """
    Ensures the essential system user exists without populating demo data.
    """
    existing_admin = db.fetch_one("SELECT id FROM users WHERE username = 'admin'")
    if not existing_admin:
        UserModel.create_user("admin", "admin123", "Admin User", "Admin")

def clear_all_data():
    """
    Wipes all transaction, inventory, and contact data from the database.
    Retains user accounts so login remains functional.
    """
    with db.get_connection() as conn:
        conn.execute("DELETE FROM sales_order_items")
        conn.execute("DELETE FROM sales_orders")
        conn.execute("DELETE FROM purchase_order_items")
        conn.execute("DELETE FROM purchase_orders")
        conn.execute("DELETE FROM stock_adjustments")
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM contacts")
        conn.commit()

