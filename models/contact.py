"""
Contact Model (Customers & Suppliers)
"""

from database.db_manager import db

def _to_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

class ContactModel:
    @staticmethod
    def get_all(contact_type=None):
        if contact_type:
            return db.fetch_all("SELECT * FROM contacts WHERE contact_type = ? ORDER BY name ASC", (contact_type,))
        return db.fetch_all("SELECT * FROM contacts ORDER BY name ASC")

    @staticmethod
    def get_by_id(contact_id):
        return db.fetch_one("SELECT * FROM contacts WHERE id = ?", (contact_id,))

    @staticmethod
    def search(query="", contact_type="All"):
        sql = "SELECT * FROM contacts WHERE 1=1"
        params = []

        if query:
            sql += " AND (name LIKE ? OR company_name LIKE ? OR phone LIKE ? OR email LIKE ? OR address LIKE ? OR gstin LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q, q, q, q])

        if contact_type != "All":
            sql += " AND contact_type = ?"
            params.append(contact_type)

        sql += " ORDER BY name ASC"
        return db.fetch_all(sql, params)

    @staticmethod
    def create(data):
        sql = """
        INSERT INTO contacts (name, company_name, contact_type, email, phone, address, gstin, pan, place_of_supply, balance, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('name'),
            data.get('company_name'),
            data.get('contact_type', 'Customer'),
            data.get('email'),
            data.get('phone'),
            data.get('address'),
            data.get('gstin'),
            data.get('pan'),
            data.get('place_of_supply', 'Uttar Pradesh'),
            _to_float(data.get('balance'), 0.0),
            data.get('status', 'Active')
        )
        cursor = db.execute_query(sql, params)
        return cursor.lastrowid

    @staticmethod
    def update(contact_id, data):
        sql = """
        UPDATE contacts SET
            name = ?, company_name = ?, contact_type = ?, email = ?, phone = ?,
            address = ?, gstin = ?, pan = ?, place_of_supply = ?, balance = ?, status = ?
        WHERE id = ?
        """
        params = (
            data.get('name'),
            data.get('company_name'),
            data.get('contact_type'),
            data.get('email'),
            data.get('phone'),
            data.get('address'),
            data.get('gstin'),
            data.get('pan'),
            data.get('place_of_supply'),
            _to_float(data.get('balance'), 0.0),
            data.get('status'),
            contact_id
        )
        db.execute_query(sql, params)


    @staticmethod
    def delete_many(contact_ids, take_backup=True):
        if not contact_ids:
            return 0, None

        backup_filename = None
        if take_backup:
            from services.backup_service import create_local_backup
            try:
                _, backup_filename, _ = create_local_backup()
            except Exception as e:
                print(f"Warning: Auto-backup before deletion encountered an issue: {e}")

        id_list = list({int(cid) for cid in contact_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Delete associated payments
            cursor.execute(f"DELETE FROM payments WHERE contact_id IN ({placeholders})", id_list)
            
            # 2. Delete customer POs, items, and dispatches
            cursor.execute(f"DELETE FROM customer_po_items WHERE customer_po_id IN (SELECT id FROM customer_pos WHERE customer_id IN ({placeholders}))", id_list)
            cursor.execute(f"DELETE FROM customer_po_dispatches WHERE customer_po_id IN (SELECT id FROM customer_pos WHERE customer_id IN ({placeholders}))", id_list)
            cursor.execute(f"DELETE FROM customer_pos WHERE customer_id IN ({placeholders})", id_list)
            
            # 3. Delete sales orders and items
            cursor.execute(f"DELETE FROM sales_order_items WHERE sales_order_id IN (SELECT id FROM sales_orders WHERE customer_id IN ({placeholders}))", id_list)
            cursor.execute(f"DELETE FROM sales_orders WHERE customer_id IN ({placeholders})", id_list)
            
            # 4. Delete purchase orders and items
            cursor.execute(f"DELETE FROM purchase_order_items WHERE purchase_order_id IN (SELECT id FROM purchase_orders WHERE supplier_id IN ({placeholders}))", id_list)
            cursor.execute(f"DELETE FROM purchase_orders WHERE supplier_id IN ({placeholders})", id_list)
            
            # 5. Delete contacts
            cursor.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount
            conn.commit()

        return deleted_count, backup_filename

    @staticmethod
    def delete(contact_id, take_backup=True):
        _, backup_filename = ContactModel.delete_many([contact_id], take_backup=take_backup)
        return backup_filename


