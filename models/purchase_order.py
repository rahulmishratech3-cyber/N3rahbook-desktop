"""
Purchase Orders Model (Vendor Replenishment)
Auto-increments item inventory when PO status is updated to "Received"
"""

from database.db_manager import db

class PurchaseOrderModel:
    @staticmethod
    def get_all():
        sql = """
        SELECT po.*, c.name as supplier_name, c.company_name
        FROM purchase_orders po
        JOIN contacts c ON po.supplier_id = c.id
        ORDER BY po.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_by_id(po_id):
        po = db.fetch_one("""
        SELECT po.*, c.name as supplier_name, c.company_name, c.address as supplier_address
        FROM purchase_orders po
        JOIN contacts c ON po.supplier_id = c.id
        WHERE po.id = ?
        """, (po_id,))

        if po:
            items = db.fetch_all("SELECT * FROM purchase_order_items WHERE purchase_order_id = ?", (po_id,))
            po['items'] = items
        return po

    @staticmethod
    def generate_po_number():
        pos = db.fetch_all("SELECT id FROM purchase_orders")
        next_num = len(pos) + 1
        from datetime import datetime
        return f"PO-{datetime.now().year}-{next_num:03d}"

    @staticmethod
    def create(po_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            po_number = po_data.get('po_number')
            status = po_data.get('status', 'Issued')

            sql_po = """
            INSERT INTO purchase_orders (po_number, supplier_id, order_date, expected_date, status, subtotal, cgst_amount, sgst_amount, total_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_po, (
                po_number,
                po_data.get('supplier_id'),
                po_data.get('order_date'),
                po_data.get('expected_date'),
                status,
                float(po_data.get('subtotal', po_data.get('total_amount', 0))),
                float(po_data.get('cgst_amount', 0)),
                float(po_data.get('sgst_amount', 0)),
                float(po_data.get('total_amount', 0)),
                po_data.get('notes', '')
            ))
            po_id = cursor.lastrowid

            sql_item = """
            INSERT INTO purchase_order_items (purchase_order_id, item_id, item_name, subcategory, hsn_code, quantity, unit, unit_cost, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for item in item_rows:
                item_id = item['item_id']
                qty = float(item['quantity'])
                subcat = item.get('subcategory', '')
                cursor.execute(sql_item, (
                    po_id,
                    item_id,
                    item.get('item_name'),
                    subcat,
                    item.get('hsn_code', '00000000'),
                    qty,
                    item.get('unit', 'PCS'),
                    float(item['unit_cost']),
                    float(item['total_cost'])
                ))

                # Increment stock & log stock adjustment if created directly as "Received"
                if status == 'Received':
                    unit_c = float(item['unit_cost'])
                    cursor.execute("""
                        UPDATE items SET 
                            current_stock = current_stock + ?,
                            cost_price = CASE WHEN ? > 0 THEN ? ELSE cost_price END
                        WHERE id = ?
                    """, (qty, unit_c, unit_c, item_id))
                    notes_sub = f" [{subcat}]" if subcat else ""
                    cursor.execute(
                        """
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (item_id, 'Add', qty, 'Purchase Order Received', 'Admin', f"Stock received via PO #{po_number}{notes_sub}")
                    )

            conn.commit()
            return po_id

    @staticmethod
    def update(po_id, po_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            po = PurchaseOrderModel.get_by_id(po_id)
            if not po:
                raise ValueError("Purchase Order not found.")

            old_status = po.get('status')
            new_status = po_data.get('status', 'Received')
            po_number = po_data.get('po_number') or po.get('po_number')

            # 1. Revert previous stock if old order was Received
            if old_status == 'Received':
                for item in po.get('items', []):
                    old_qty = float(item['quantity'])
                    old_item_id = item['item_id']
                    cursor.execute("UPDATE items SET current_stock = current_stock - ? WHERE id = ?", (old_qty, old_item_id))
                    cursor.execute(
                        """
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (old_item_id, 'Remove', old_qty, 'Purchase Order Edited', 'Admin', f"Stock reverted for edit on PO #{po_number}")
                    )

            # 2. Update purchase_orders record
            sql_po = """
            UPDATE purchase_orders SET
                po_number = ?, supplier_id = ?, order_date = ?, expected_date = ?, status = ?,
                subtotal = ?, cgst_amount = ?, sgst_amount = ?, total_amount = ?, notes = ?
            WHERE id = ?
            """
            cursor.execute(sql_po, (
                po_number,
                po_data.get('supplier_id'),
                po_data.get('order_date'),
                po_data.get('expected_date'),
                new_status,
                float(po_data.get('subtotal', po_data.get('total_amount', 0))),
                float(po_data.get('cgst_amount', 0)),
                float(po_data.get('sgst_amount', 0)),
                float(po_data.get('total_amount', 0)),
                po_data.get('notes', ''),
                po_id
            ))

            # 3. Delete old items and insert updated items
            cursor.execute("DELETE FROM purchase_order_items WHERE purchase_order_id = ?", (po_id,))
            sql_item = """
            INSERT INTO purchase_order_items (purchase_order_id, item_id, item_name, subcategory, hsn_code, quantity, unit, unit_cost, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for item in item_rows:
                item_id = item['item_id']
                qty = float(item['quantity'])
                subcat = item.get('subcategory', '')
                unit_c = float(item['unit_cost'])
                cursor.execute(sql_item, (
                    po_id,
                    item_id,
                    item.get('item_name'),
                    subcat,
                    item.get('hsn_code', '00000000'),
                    qty,
                    item.get('unit', 'PCS'),
                    unit_c,
                    float(item['total_cost'])
                ))

                # If new status is Received, apply new stock & log
                if new_status == 'Received':
                    cursor.execute("""
                        UPDATE items SET 
                            current_stock = current_stock + ?,
                            cost_price = CASE WHEN ? > 0 THEN ? ELSE cost_price END
                        WHERE id = ?
                    """, (qty, unit_c, unit_c, item_id))
                    notes_sub = f" [{subcat}]" if subcat else ""
                    cursor.execute(
                        """
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (item_id, 'Add', qty, 'Purchase Order Received', 'Admin', f"Stock received via updated PO #{po_number}{notes_sub}")
                    )

            conn.commit()

    @staticmethod
    def update_status(po_id, new_status):
        po = PurchaseOrderModel.get_by_id(po_id)
        if not po:
            return

        old_status = po['status']
        if old_status == new_status:
            return

        po_number = po.get('po_number', f"PO-{po_id}")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # If updated to Received, increment stock and log stock adjustment
            if new_status == 'Received' and old_status != 'Received':
                for item in po.get('items', []):
                    qty = float(item['quantity'])
                    item_id = item['item_id']
                    cursor.execute("UPDATE items SET current_stock = current_stock + ? WHERE id = ?", (qty, item_id))
                    cursor.execute(
                        """
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (item_id, 'Add', qty, 'Purchase Order Received', 'Admin', f"Stock received via PO #{po_number}")
                    )
            elif old_status == 'Received' and new_status != 'Received':
                for item in po.get('items', []):
                    qty = float(item['quantity'])
                    item_id = item['item_id']
                    cursor.execute("UPDATE items SET current_stock = current_stock - ? WHERE id = ?", (qty, item_id))
                    cursor.execute(
                        """
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (item_id, 'Remove', qty, 'PO Status Changed', 'Admin', f"Stock reverted (PO #{po_number} changed to {new_status})")
                    )

            cursor.execute("UPDATE purchase_orders SET status = ? WHERE id = ?", (new_status, po_id))
            conn.commit()

    @staticmethod
    def delete_many(po_ids):
        if not po_ids:
            return 0

        id_list = list({int(pid) for pid in po_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            for po_id in id_list:
                po = PurchaseOrderModel.get_by_id(po_id)
                if po and po.get('status') == 'Received':
                    po_number = po.get('po_number', f"PO-{po_id}")
                    for item in po.get('items', []):
                        qty = float(item['quantity'])
                        item_id = item['item_id']
                        cursor.execute("UPDATE items SET current_stock = current_stock - ? WHERE id = ?", (qty, item_id))
                        cursor.execute(
                            """
                            INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (item_id, 'Remove', qty, 'Purchase Order Deleted', 'Admin', f"Stock reverted (Deleted PO #{po_number})")
                        )

            cursor.execute(f"DELETE FROM payments WHERE purchase_order_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM purchase_order_items WHERE purchase_order_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM purchase_orders WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount
            conn.commit()

        # Recalculate balances
        from models.payment import PaymentModel
        PaymentModel.recalculate_all_balances()

        return deleted_count

    @staticmethod
    def delete(po_id):
        return PurchaseOrderModel.delete_many([po_id]) > 0

