"""
Sales Orders and Invoicing Model
Handles creation, status transitions, tax calculations (CGST, SGST, IGST), and inventory deduction.
"""

from database.db_manager import db
from models.item import ItemModel

def _to_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

class SalesOrderModel:
    @staticmethod
    def get_all():
        sql = """
        SELECT so.*, c.name as customer_name, c.company_name, c.gstin as customer_gstin
        FROM sales_orders so
        JOIN contacts c ON so.customer_id = c.id
        ORDER BY so.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_by_id(order_id):
        order = db.fetch_one("""
        SELECT so.*, c.name as customer_name, c.company_name, c.address as customer_address, c.gstin as customer_gstin
        FROM sales_orders so
        JOIN contacts c ON so.customer_id = c.id
        WHERE so.id = ?
        """, (order_id,))

        if order:
            items = db.fetch_all("SELECT * FROM sales_order_items WHERE sales_order_id = ?", (order_id,))
            order['items'] = items
        return order

    @staticmethod
    def get_by_invoice_number(inv_num):
        return db.fetch_one("SELECT * FROM sales_orders WHERE invoice_number = ?", (inv_num,))

    @staticmethod
    def create(order_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            status_input = str(order_data.get('status', 'Paid')).strip()
            pay_status = order_data.get('payment_status') or ('Unpaid' if status_input == 'Unpaid' else 'Paid')
            if status_input == 'Unpaid':
                db_status = 'Confirmed'
            elif status_input in ('Draft', 'Confirmed', 'Shipped', 'Paid', 'Cancelled'):
                db_status = status_input
            else:
                db_status = 'Paid'

            sql_order = """
            INSERT INTO sales_orders (
                invoice_number, customer_id, invoice_date, due_date, po_number, po_date, vehicle_no,
                eway_bill_no, fiscal_year, place_of_supply, status, payment_status, subtotal,
                freight, cgst_amount, sgst_amount, igst_amount, round_off, total_amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_order, (
                order_data.get('invoice_number'),
                order_data.get('customer_id'),
                order_data.get('invoice_date'),
                order_data.get('due_date'),
                order_data.get('po_number', ''),
                order_data.get('po_date', ''),
                order_data.get('vehicle_no'),
                order_data.get('eway_bill_no', ''),
                order_data.get('fiscal_year', '2026-2027'),
                order_data.get('place_of_supply', 'Uttar Pradesh'),
                db_status,
                pay_status,
                _to_float(order_data.get('subtotal'), 0.0),
                _to_float(order_data.get('freight'), 0.0),
                _to_float(order_data.get('cgst_amount'), 0.0),
                _to_float(order_data.get('sgst_amount'), 0.0),
                _to_float(order_data.get('igst_amount'), 0.0),
                _to_float(order_data.get('round_off'), 0.0),
                _to_float(order_data.get('total_amount'), 0.0),
                order_data.get('notes', '')
            ))
            order_id = cursor.lastrowid

            sql_item = """
            INSERT INTO sales_order_items (
                sales_order_id, item_id, item_name, hsn_code, quantity, unit,
                unit_price, discount, amount, cgst_rate, sgst_rate, igst_rate, tax_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            for item in item_rows:
                item_id = item['item_id']
                qty = _to_float(item.get('quantity'), 0.0)
                cursor.execute(sql_item, (
                    order_id,
                    item_id,
                    item.get('item_name'),
                    item.get('hsn_code', '00000000'),
                    qty,
                    item.get('unit', 'PCS'),
                    _to_float(item.get('unit_price'), 0.0),
                    _to_float(item.get('discount'), 0.0),
                    _to_float(item.get('amount'), 0.0),
                    _to_float(item.get('cgst_rate'), 9.0),
                    _to_float(item.get('sgst_rate'), 9.0),
                    _to_float(item.get('igst_rate'), 0.0),
                    _to_float(item.get('tax_amount'), 0.0)
                ))


                # Deduct stock automatically if status is not Cancelled
                if db_status != 'Cancelled':
                    cursor.execute("UPDATE items SET current_stock = ROUND(current_stock - ?, 4) WHERE id = ?", (qty, item_id))
                    cursor.execute("""
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, 'Remove', ?, 'Sales Invoice', 'Admin', ?)
                    """, (item_id, qty, f"Deducted via Invoice #{order_data['invoice_number']}"))

            conn.commit()

            # Automatically sync and deduct from Customer PO if po_number is provided
            po_num = str(order_data.get('po_number') or '').strip()
            if po_num and db_status != 'Cancelled':
                try:
                    from models.customer_po import CustomerPOModel
                    tot_billed_qty = sum(_to_float(i.get('quantity'), 0.0) for i in item_rows)
                    tot_billed_amt = _to_float(order_data.get('total_amount'), 0.0)
                    CustomerPOModel.sync_invoice_dispatch(
                        invoice_number=order_data.get('invoice_number'),
                        po_number=po_num,
                        dispatch_date=order_data.get('invoice_date'),
                        dispatched_qty_kg=tot_billed_qty,
                        dispatched_amount=tot_billed_amt,
                        notes=f"Auto-deducted via Tax Invoice #{order_data.get('invoice_number')}"
                    )
                except Exception as ex:
                    print(f"[SalesOrderModel] Customer PO sync warning: {ex}")
            # Automatically sync payment status with Payments table and recalculate Customer balance
            try:
                from models.payment import PaymentModel
                is_paid = (pay_status.lower() == 'paid' or db_status.lower() == 'paid') and db_status != 'Cancelled'
                PaymentModel.sync_sales_invoice_payment(order_id, is_paid=is_paid)
            except Exception as e:
                print(f"[SalesOrderModel] Payment sync error on create: {e}")

            return order_id

    @staticmethod
    def update(order_id, order_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Restore stock from old items
            old_order = SalesOrderModel.get_by_id(order_id)
            if old_order and old_order.get('status') != 'Cancelled':
                for old_itm in old_order.get('items', []):
                    old_qty = float(old_itm['quantity'])
                    cursor.execute("UPDATE items SET current_stock = ROUND(current_stock + ?, 4) WHERE id = ?", (old_qty, old_itm['item_id']))
                    cursor.execute("""
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, 'Add', ?, 'Invoice Edit Reversion', 'Admin', ?)
                    """, (old_itm['item_id'], old_qty, f"Reverted previous stock for Invoice #{old_order.get('invoice_number')} edit"))

            status_input = str(order_data.get('status', 'Paid')).strip()
            pay_status = order_data.get('payment_status') or ('Unpaid' if status_input == 'Unpaid' else 'Paid')
            if status_input == 'Unpaid':
                db_status = 'Confirmed'
            elif status_input in ('Draft', 'Confirmed', 'Shipped', 'Paid', 'Cancelled'):
                db_status = status_input
            else:
                db_status = 'Paid'

            # 2. Update order metadata
            sql_order = """
            UPDATE sales_orders SET
                customer_id = ?, invoice_date = ?, due_date = ?, po_number = ?, po_date = ?, vehicle_no = ?,
                eway_bill_no = ?, fiscal_year = ?, place_of_supply = ?, status = ?,
                payment_status = ?, subtotal = ?, freight = ?, cgst_amount = ?, sgst_amount = ?,
                igst_amount = ?, round_off = ?, total_amount = ?, notes = ?
            WHERE id = ?
            """
            cursor.execute(sql_order, (
                order_data.get('customer_id'),
                order_data.get('invoice_date'),
                order_data.get('due_date'),
                order_data.get('po_number', ''),
                order_data.get('po_date', ''),
                order_data.get('vehicle_no'),
                order_data.get('eway_bill_no', ''),
                order_data.get('fiscal_year', '2026-2027'),
                order_data.get('place_of_supply', 'Uttar Pradesh'),
                db_status,
                pay_status,
                _to_float(order_data.get('subtotal'), 0.0),
                _to_float(order_data.get('freight'), 0.0),
                _to_float(order_data.get('cgst_amount'), 0.0),
                _to_float(order_data.get('sgst_amount'), 0.0),
                _to_float(order_data.get('igst_amount'), 0.0),
                _to_float(order_data.get('round_off'), 0.0),
                _to_float(order_data.get('total_amount'), 0.0),
                order_data.get('notes', ''),
                order_id
            ))

            # 3. Delete old items and insert new items
            cursor.execute("DELETE FROM sales_order_items WHERE sales_order_id = ?", (order_id,))

            sql_item = """
            INSERT INTO sales_order_items (
                sales_order_id, item_id, item_name, hsn_code, quantity, unit,
                unit_price, discount, amount, cgst_rate, sgst_rate, igst_rate, tax_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            for item in item_rows:
                item_id = item['item_id']
                qty = _to_float(item.get('quantity'), 0.0)
                cursor.execute(sql_item, (
                    order_id,
                    item_id,
                    item.get('item_name'),
                    item.get('hsn_code', '00000000'),
                    qty,
                    item.get('unit', 'PCS'),
                    _to_float(item.get('unit_price'), 0.0),
                    _to_float(item.get('discount'), 0.0),
                    _to_float(item.get('amount'), 0.0),
                    _to_float(item.get('cgst_rate'), 9.0),
                    _to_float(item.get('sgst_rate'), 9.0),
                    _to_float(item.get('igst_rate'), 0.0),
                    _to_float(item.get('tax_amount'), 0.0)
                ))

                # Deduct stock for new items if not Cancelled
                if db_status != 'Cancelled':
                    cursor.execute("UPDATE items SET current_stock = ROUND(current_stock - ?, 4) WHERE id = ?", (qty, item_id))
                    cursor.execute("""
                        INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                        VALUES (?, 'Remove', ?, 'Sales Invoice', 'Admin', ?)
                    """, (item_id, qty, f"Deducted via Updated Invoice #{order_data['invoice_number']}"))

            conn.commit()

            # Automatically sync and deduct from Customer PO
            try:
                from models.customer_po import CustomerPOModel
                inv_no = str(order_data.get('invoice_number') or '').strip()
                po_num = str(order_data.get('po_number') or '').strip()
                if db_status == 'Cancelled':
                    CustomerPOModel.remove_invoice_dispatch(inv_no)
                else:
                    tot_billed_qty = sum(_to_float(i.get('quantity'), 0.0) for i in item_rows)
                    tot_billed_amt = _to_float(order_data.get('total_amount'), 0.0)
                    CustomerPOModel.sync_invoice_dispatch(
                        invoice_number=inv_no,
                        po_number=po_num,
                        dispatch_date=order_data.get('invoice_date'),
                        dispatched_qty_kg=tot_billed_qty,
                        dispatched_amount=tot_billed_amt,
                        notes=f"Auto-deducted via Updated Invoice #{inv_no}"
                    )
            except Exception:
                pass
            # Automatically sync payment status with Payments table and recalculate Customer balance
            try:
                from models.payment import PaymentModel
                is_paid = (pay_status.lower() == 'paid' or db_status.lower() == 'paid') and db_status != 'Cancelled'
                PaymentModel.sync_sales_invoice_payment(order_id, is_paid=is_paid)
            except Exception as e:
                print(f"[SalesOrderModel] Payment sync error on update: {e}")

            return order_id

    @staticmethod
    def update_status(order_id, new_status=None, payment_status=None, status=None):
        order = SalesOrderModel.get_by_id(order_id)
        if not order:
            return

        old_status = order['status']
        target = new_status or status or payment_status or 'Paid'
        target_str = str(target).strip()
        
        if target_str in ('Unpaid', 'unpaid'):
            db_status = 'Confirmed'
            pay_status = 'Unpaid'
        elif target_str in ('Paid', 'paid'):
            db_status = 'Paid'
            pay_status = 'Paid'
        elif target_str in ('Draft', 'Confirmed', 'Shipped', 'Cancelled'):
            db_status = target_str
            if payment_status:
                pay_status = payment_status
            else:
                pay_status = 'Paid' if target_str in ('Confirmed', 'Shipped', 'Paid') else 'Unpaid'
        else:
            db_status = 'Confirmed'
            pay_status = target_str

        # Handle stock restoration if cancelled
        if db_status == 'Cancelled' and old_status != 'Cancelled':
            for item in order.get('items', []):
                qty = float(item['quantity'])
                db.execute_query("UPDATE items SET current_stock = ROUND(current_stock + ?, 4) WHERE id = ?", (qty, item['item_id']))
                db.execute_query("""
                    INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                    VALUES (?, 'Add', ?, 'Invoice Cancelled', 'Admin', ?)
                """, (item['item_id'], qty, f"Restored stock (Invoice #{order.get('invoice_number')} cancelled)"))
        elif old_status == 'Cancelled' and db_status != 'Cancelled':
            for item in order.get('items', []):
                qty = float(item['quantity'])
                db.execute_query("UPDATE items SET current_stock = ROUND(current_stock - ?, 4) WHERE id = ?", (qty, item['item_id']))
                db.execute_query("""
                    INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                    VALUES (?, 'Remove', ?, 'Sales Invoice', 'Admin', ?)
                """, (item['item_id'], qty, f"Re-deducted stock (Invoice #{order.get('invoice_number')} un-cancelled)"))

        db.execute_query("UPDATE sales_orders SET status = ?, payment_status = ? WHERE id = ?", (db_status, pay_status, order_id))

        # Sync payment settlement in payments table and update customer running balance
        try:
            from models.payment import PaymentModel
            is_paid = (pay_status.lower() == 'paid' or db_status.lower() == 'paid') and db_status != 'Cancelled'
            PaymentModel.sync_sales_invoice_payment(order_id, is_paid=is_paid)
        except Exception as e:
            print(f"[SalesOrderModel] Status sync payment error: {e}")

        # Sync Customer PO deduction
        try:
            from models.customer_po import CustomerPOModel
            inv_no = str(order.get('invoice_number') or '').strip()
            po_num = str(order.get('po_number') or '').strip()
            if db_status == 'Cancelled':
                CustomerPOModel.remove_invoice_dispatch(inv_no)
            elif old_status == 'Cancelled' and db_status != 'Cancelled' and po_num:
                tot_billed_qty = sum(_to_float(i.get('quantity'), 0.0) for i in order.get('items', []))
                tot_billed_amt = _to_float(order.get('total_amount'), 0.0)
                CustomerPOModel.sync_invoice_dispatch(
                    invoice_number=inv_no,
                    po_number=po_num,
                    dispatch_date=order.get('invoice_date'),
                    dispatched_qty_kg=tot_billed_qty,
                    dispatched_amount=tot_billed_amt,
                    notes=f"Restored deduction via Re-activated Invoice #{inv_no}"
                )
        except Exception:
            pass

    @staticmethod
    def delete_many(order_ids):
        """
        Deletes multiple invoice records and their associated line items.
        Restores stock levels for items if the orders were not cancelled.
        """
        if not order_ids:
            return 0

        id_list = list({int(oid) for oid in order_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            for oid in id_list:
                order = SalesOrderModel.get_by_id(oid)
                if order:
                    inv_no = str(order.get('invoice_number') or '').strip()
                    try:
                        from models.customer_po import CustomerPOModel
                        CustomerPOModel.remove_invoice_dispatch(inv_no)
                    except Exception:
                        pass

                    if order.get('status') != 'Cancelled':
                        for item in order.get('items', []):
                            qty = float(item['quantity'])
                            cursor.execute("UPDATE items SET current_stock = ROUND(current_stock + ?, 4) WHERE id = ?", (qty, item['item_id']))
                            cursor.execute("""
                                INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                                VALUES (?, 'Add', ?, 'Invoice Deleted', 'Admin', ?)
                            """, (item['item_id'], qty, f"Stock restored (Invoice #{order.get('invoice_number')} deleted)"))

            cursor.execute(f"DELETE FROM payments WHERE sales_order_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM sales_order_items WHERE sales_order_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM sales_orders WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount
            conn.commit()

        # Recalculate balances
        from models.payment import PaymentModel
        PaymentModel.recalculate_all_balances()

        return deleted_count

    @staticmethod
    def delete(order_id):
        return SalesOrderModel.delete_many([order_id]) > 0

