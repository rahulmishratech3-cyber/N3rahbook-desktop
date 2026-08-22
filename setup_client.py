"""
New Client Setup & Database Initialization Script
Use this script when selling/deploying N3RAH BOOK to a new client.
Clears test data and configures the new client's initial Admin credentials and business profile.
"""

import sys
import os
from database.db_manager import db
from database.schema import CREATE_TABLES_SQL
from models.user import UserModel
from models.company import CompanyModel

def setup_client(client_name="Client Business", admin_username="admin", admin_password="admin123"):
    print("==================================================")
    print("N3RAH BOOK - New Client Setup & License Deployer")
    print("==================================================")

    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory_system.db")
    
    # Re-initialize tables
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(CREATE_TABLES_SQL)
        conn.commit()

    # Clear old data if existing
    db.execute_query("DELETE FROM payments")
    db.execute_query("DELETE FROM customer_po_dispatches")
    db.execute_query("DELETE FROM customer_po_items")
    db.execute_query("DELETE FROM customer_pos")
    db.execute_query("DELETE FROM sales_order_items")
    db.execute_query("DELETE FROM sales_orders")
    db.execute_query("DELETE FROM purchase_order_items")
    db.execute_query("DELETE FROM purchase_orders")
    db.execute_query("DELETE FROM stock_adjustments")
    db.execute_query("DELETE FROM items")
    db.execute_query("DELETE FROM contacts")
    db.execute_query("DELETE FROM users")

    # Create Initial Client Admin Account
    UserModel.create_user(
        username=admin_username,
        password=admin_password,
        full_name=f"{client_name} Administrator",
        role="Admin",
        status="Active"
    )

    # Initialize Client Business Profile
    CompanyModel.update_profile({
        'name': client_name,
        'address': 'Enter Registered Business Address Here',
        'gstin': '09XXXXX0000X1Z0',
        'pan': 'XXXXX0000X',
        'mobile': '9876543210',
        'email': 'contact@clientcompany.com',
        'bank_name': 'State Bank of India',
        'bank_branch': 'Main Branch',
        'account_no': '123456789012',
        'ifsc_code': 'SBIN0000000',
        'terms': [
            '1. Goods once sold will not be taken back or exchanged.',
            '2. Subject to local jurisdiction only.'
        ]
    })

    print(f"\n[SUCCESS] New Client Instance Ready!")
    print(f"Business Name: {client_name}")
    print(f"Admin Username: {admin_username}")
    print(f"Admin Password: {admin_password}")
    print("\nClient can now log in and configure their profile under 'Settings & Profile'!")

if __name__ == "__main__":
    c_name = input("Enter Client Business Name [Default: Client Store]: ").strip() or "Client Store"
    c_pass = input("Enter Admin Password [Default: admin123]: ").strip() or "admin123"
    setup_client(client_name=c_name, admin_password=c_pass)
