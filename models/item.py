"""
Item / Product Model and Data Access Layer
"""

from database.db_manager import db

def _to_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

class ItemModel:
    DEFAULT_CATEGORIES = [
        "PU FOAM SHEETS",
        "FOAM DANDA",
        "APPLICATION",
        "RAW MATERIAL",
        "PACKING MATERIAL",
        "GENERAL"
    ]

    DEFAULT_SUBCATEGORIES = {
        "PU FOAM SHEETS": [
            "1ST GRADE",
            "B-GRADE",
            "CROSS",
            "Density 32 (Standard)",
            "Density 40 (High Density)",
            "High Resilience (HR Foam)",
            "Memory Foam (Visco)",
            "Rebonded Foam",
            "Super Soft (SS Foam)",
            "Fire Retardant (FR Foam)",
            "Orthopedic Sheet",
            "Plain Sheet",
            "Cushioning Sheet"
        ],
        "FOAM DANDA": [
            "1ST GRADE",
            "B-GRADE",
            "CROSS",
            "Round Danda",
            "Square Danda",
            "Profile Danda"
        ],
        "APPLICATION": [
            "Digital Switch",
            "Mechanical Switch",
            "Controller Board"
        ],
        "RAW MATERIAL": [
            "Polyol",
            "TDI / Isocyanate",
            "Chemical Additives",
            "Pigment"
        ],
        "PACKING MATERIAL": [
            "Polythene Roll",
            "Corrugated Box",
            "Strapping Band",
            "Stretch Film"
        ]
    }

    @staticmethod
    def get_all():
        return db.fetch_all("SELECT * FROM items ORDER BY id DESC")

    @staticmethod
    def get_by_id(item_id):
        return db.fetch_one("SELECT * FROM items WHERE id = ?", (item_id,))

    @staticmethod
    def get_by_sku(sku):
        return db.fetch_one("SELECT * FROM items WHERE sku = ?", (sku,))

    @staticmethod
    def search(query="", category="All", subcategory="All", stock_filter="All"):
        sql = "SELECT * FROM items WHERE 1=1"
        params = []

        if query:
            sql += " AND (name LIKE ? OR sku LIKE ? OR hsn_code LIKE ? OR brand LIKE ? OR subcategory LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q, q, q])

        if category and category != "All":
            sql += " AND category = ?"
            params.append(category)

        if subcategory and subcategory != "All":
            sql += " AND subcategory = ?"
            params.append(subcategory)

        if stock_filter == "Low Stock":
            sql += " AND current_stock <= reorder_level AND current_stock > 0"
        elif stock_filter == "Out of Stock":
            sql += " AND current_stock <= 0"
        elif stock_filter == "Low or Out":
            sql += " AND current_stock <= reorder_level"
        elif stock_filter == "In Stock":
            sql += " AND current_stock > reorder_level"

        sql += " ORDER BY id DESC"
        return db.fetch_all(sql, params)

    @staticmethod
    def get_categories():
        rows = db.fetch_all("SELECT DISTINCT category FROM items WHERE category IS NOT NULL AND category != ''")
        cats = [r['category'] for r in rows]
        # Merge with defaults ensuring PU FOAM SHEETS is first
        merged = ["PU FOAM SHEETS"]
        for c in ItemModel.DEFAULT_CATEGORIES + cats:
            if c and c not in merged:
                merged.append(c)
        return merged

    @staticmethod
    def get_subcategories(category=None):
        if category and category != "All":
            rows = db.fetch_all("SELECT DISTINCT subcategory FROM items WHERE category = ? AND subcategory IS NOT NULL AND subcategory != ''", (category,))
            existing = [r['subcategory'] for r in rows]
            defaults = ItemModel.DEFAULT_SUBCATEGORIES.get(category, [])
        else:
            rows = db.fetch_all("SELECT DISTINCT subcategory FROM items WHERE subcategory IS NOT NULL AND subcategory != ''")
            existing = [r['subcategory'] for r in rows]
            defaults = []
            for sub_list in ItemModel.DEFAULT_SUBCATEGORIES.values():
                defaults.extend(sub_list)

        merged = []
        for s in defaults + existing:
            if s and s not in merged:
                merged.append(s)
        return merged

    @staticmethod
    def create(data):
        sql = """
        INSERT INTO items (sku, barcode, name, category, subcategory, brand, hsn_code, unit, cost_price, selling_price, current_stock, reorder_level, tax_rate, location, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('sku'),
            data.get('barcode') or data.get('sku'),
            data.get('name'),
            data.get('category') or 'PU FOAM SHEETS',
            data.get('subcategory') or '',
            data.get('brand') or 'Generic',
            data.get('hsn_code') or '00000000',
            data.get('unit') or 'PCS',
            _to_float(data.get('cost_price'), 0.0),
            _to_float(data.get('selling_price'), 0.0),
            _to_float(data.get('current_stock'), 0.0),
            _to_float(data.get('reorder_level'), 10.0),
            _to_float(data.get('tax_rate'), 18.0),
            data.get('location') or 'Warehouse A',
            data.get('status') or 'Active'
        )
        cursor = db.execute_query(sql, params)
        return cursor.lastrowid

    @staticmethod
    def update(item_id, data):
        sql = """
        UPDATE items SET
            sku = ?, barcode = ?, name = ?, category = ?, subcategory = ?, brand = ?, hsn_code = ?,
            unit = ?, cost_price = ?, selling_price = ?, current_stock = ?, reorder_level = ?,
            tax_rate = ?, location = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        params = (
            data.get('sku'),
            data.get('barcode'),
            data.get('name'),
            data.get('category'),
            data.get('subcategory', ''),
            data.get('brand'),
            data.get('hsn_code'),
            data.get('unit'),
            _to_float(data.get('cost_price'), 0.0),
            _to_float(data.get('selling_price'), 0.0),
            _to_float(data.get('current_stock'), 0.0),
            _to_float(data.get('reorder_level'), 10.0),
            _to_float(data.get('tax_rate'), 18.0),
            data.get('location'),
            data.get('status'),
            item_id
        )
        db.execute_query(sql, params)


    @staticmethod
    def delete_many(item_ids):
        if not item_ids:
            return 0

        id_list = list({int(iid) for iid in item_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM sales_order_items WHERE item_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM purchase_order_items WHERE item_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM customer_po_items WHERE item_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM stock_adjustments WHERE item_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM items WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount
            conn.commit()
        return deleted_count

    @staticmethod
    def delete(item_id):
        return ItemModel.delete_many([item_id]) > 0


    @staticmethod
    def update_stock(item_id, qty_change):
        db.execute_query("UPDATE items SET current_stock = current_stock + ? WHERE id = ?", (qty_change, item_id))
