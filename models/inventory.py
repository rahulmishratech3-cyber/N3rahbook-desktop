"""
Stock Adjustment & Inventory Ledger Model
"""

from database.db_manager import db
from models.item import ItemModel

class InventoryModel:
    @staticmethod
    def get_adjustments():
        sql = """
        SELECT sa.*, i.name as item_name, i.sku, i.unit
        FROM stock_adjustments sa
        JOIN items i ON sa.item_id = i.id
        ORDER BY sa.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def create_adjustment(item_id, adjustment_type, quantity, reason="Audit", adjusted_by="Admin", notes=""):
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        sql = """
        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        db.execute_query(sql, (item_id, adjustment_type, quantity, reason, adjusted_by, notes))

        # Update item stock level
        qty_change = quantity if adjustment_type == 'Add' else -quantity
        ItemModel.update_stock(item_id, qty_change)
