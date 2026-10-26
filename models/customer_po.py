"""
Customer Purchase Order (Party PO) Model
Handles tracking of party purchase orders, line items in KG, dispatches, and pending balance calculations.
"""

from datetime import datetime
from database.db_manager import db

def _to_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

class CustomerPOModel:
    @staticmethod
    def generate_po_number():
        rows = db.fetch_all("SELECT id FROM customer_pos")
        next_num = len(rows) + 1
        year = datetime.now().year
        return f"CPO-{year}-{next_num:03d}"

    @staticmethod
    def get_all(query="", customer_id="All", status_filter="All"):
        sql = """
        SELECT po.*, c.name as customer_name, c.company_name, c.phone as customer_phone,
               c.address as customer_address, c.gstin as customer_gstin, c.pan as customer_pan, c.email as customer_email
        FROM customer_pos po
        JOIN contacts c ON po.customer_id = c.id
        WHERE 1=1
        """
        params = []

        if query:
            sql += " AND (po.po_number LIKE ? OR c.name LIKE ? OR c.company_name LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q])

        if customer_id and customer_id != "All":
            sql += " AND po.customer_id = ?"
            params.append(customer_id)

        if status_filter and status_filter != "All":
            sql += " AND po.status = ?"
            params.append(status_filter)

        sql += " ORDER BY po.id DESC"
        rows = db.fetch_all(sql, params)

        # Compute calculated fields for balance Qty (KG) and balance Amount
        for r in rows:
            ordered_kg = _to_float(r['total_ordered_qty_kg'])
            dispatched_kg = _to_float(r['total_dispatched_qty_kg'])
            total_amt = _to_float(r['total_po_amount'])
            dispatched_amt = _to_float(r['total_dispatched_amount'])

            r['balance_qty_kg'] = max(0.0, ordered_kg - dispatched_kg)
            r['balance_amount'] = max(0.0, total_amt - dispatched_amt)

        return rows

    @staticmethod
    def get_by_id(po_id):
        po = db.fetch_one("""
        SELECT po.*, c.name as customer_name, c.company_name, c.phone as customer_phone,
               c.address as customer_address, c.gstin as customer_gstin, c.pan as customer_pan, c.email as customer_email
        FROM customer_pos po
        JOIN contacts c ON po.customer_id = c.id
        WHERE po.id = ?
        """, (po_id,))

        if po:
            ordered_kg = _to_float(po['total_ordered_qty_kg'])
            dispatched_kg = _to_float(po['total_dispatched_qty_kg'])
            total_amt = _to_float(po['total_po_amount'])
            dispatched_amt = _to_float(po['total_dispatched_amount'])

            po['balance_qty_kg'] = max(0.0, ordered_kg - dispatched_kg)
            po['balance_amount'] = max(0.0, total_amt - dispatched_amt)

            items = db.fetch_all("SELECT * FROM customer_po_items WHERE customer_po_id = ?", (po_id,))
            dispatches = db.fetch_all("SELECT * FROM customer_po_dispatches WHERE customer_po_id = ? ORDER BY id DESC", (po_id,))
            
            po['items'] = items
            po['dispatches'] = dispatches

        return po

    @staticmethod
    def create(po_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            po_number = po_data.get('po_number') or CustomerPOModel.generate_po_number()

            # Calculate overall total ordered KG & subtotal
            tot_kg = sum(_to_float(i.get('ordered_qty_kg')) for i in item_rows)
            subtotal = _to_float(po_data.get('subtotal', sum(_to_float(i.get('total_amount')) for i in item_rows)))
            gst_rate = _to_float(po_data.get('gst_rate', 18.0))
            
            if gst_rate > 0:
                cgst_amt = _to_float(po_data.get('cgst_amount', subtotal * 0.09))
                sgst_amt = _to_float(po_data.get('sgst_amount', subtotal * 0.09))
                tot_amt = _to_float(po_data.get('total_po_amount', round(subtotal + cgst_amt + sgst_amt)))
            else:
                cgst_amt = 0.0
                sgst_amt = 0.0
                tot_amt = subtotal

            sql_po = """
            INSERT INTO customer_pos (
                po_number, customer_id, po_date, target_delivery_date,
                total_ordered_qty_kg, total_dispatched_qty_kg, subtotal, cgst_amount, sgst_amount, gst_rate, total_po_amount,
                total_dispatched_amount, status, notes
            ) VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, 0.0, 'Open', ?)
            """
            cursor.execute(sql_po, (
                po_number,
                po_data.get('customer_id'),
                po_data.get('po_date'),
                po_data.get('target_delivery_date', ''),
                tot_kg,
                subtotal,
                cgst_amt,
                sgst_amt,
                gst_rate,
                tot_amt,
                po_data.get('notes', '')
            ))
            po_id = cursor.lastrowid

            sql_item = """
            INSERT INTO customer_po_items (
                customer_po_id, item_id, item_name, hsn_code, ordered_qty_kg,
                dispatched_qty_kg, unit, unit_price, total_amount
            ) VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, ?)
            """
            for item in item_rows:
                cursor.execute(sql_item, (
                    po_id,
                    item.get('item_id'),
                    item.get('item_name'),
                    item.get('hsn_code', '00000000'),
                    _to_float(item.get('ordered_qty_kg')),
                    item.get('unit', 'KGS'),
                    _to_float(item.get('unit_price')),
                    _to_float(item.get('total_amount'))
                ))

            conn.commit()
            return po_id

    @staticmethod
    def update(po_id, po_data, item_rows):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            tot_kg = sum(_to_float(i.get('ordered_qty_kg')) for i in item_rows)
            subtotal = _to_float(po_data.get('subtotal', sum(_to_float(i.get('total_amount')) for i in item_rows)))
            gst_rate = _to_float(po_data.get('gst_rate', 18.0))

            if gst_rate > 0:
                cgst_amt = _to_float(po_data.get('cgst_amount', subtotal * 0.09))
                sgst_amt = _to_float(po_data.get('sgst_amount', subtotal * 0.09))
                tot_amt = _to_float(po_data.get('total_po_amount', round(subtotal + cgst_amt + sgst_amt)))
            else:
                cgst_amt = 0.0
                sgst_amt = 0.0
                tot_amt = subtotal

            sql_po = """
            UPDATE customer_pos SET
                po_number = ?, customer_id = ?, po_date = ?, target_delivery_date = ?,
                total_ordered_qty_kg = ?, subtotal = ?, cgst_amount = ?, sgst_amount = ?, gst_rate = ?, total_po_amount = ?, notes = ?
            WHERE id = ?
            """
            cursor.execute(sql_po, (
                po_data.get('po_number'),
                po_data.get('customer_id'),
                po_data.get('po_date'),
                po_data.get('target_delivery_date', ''),
                tot_kg,
                subtotal,
                cgst_amt,
                sgst_amt,
                gst_rate,
                tot_amt,
                po_data.get('notes', ''),
                po_id
            ))

            # Delete old items and insert updated ones
            cursor.execute("DELETE FROM customer_po_items WHERE customer_po_id = ?", (po_id,))
            sql_item = """
            INSERT INTO customer_po_items (
                customer_po_id, item_id, item_name, hsn_code, ordered_qty_kg,
                dispatched_qty_kg, unit, unit_price, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for item in item_rows:
                cursor.execute(sql_item, (
                    po_id,
                    item.get('item_id'),
                    item.get('item_name'),
                    item.get('hsn_code', '00000000'),
                    _to_float(item.get('ordered_qty_kg')),
                    _to_float(item.get('dispatched_qty_kg', 0.0)),
                    item.get('unit', 'KGS'),
                    _to_float(item.get('unit_price')),
                    _to_float(item.get('total_amount'))
                ))

            conn.commit()
            CustomerPOModel.recalculate_po_status(po_id)

    @staticmethod
    def delete_many(po_ids):
        if not po_ids:
            return 0

        id_list = list({int(pid) for pid in po_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM customer_po_dispatches WHERE customer_po_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM customer_po_items WHERE customer_po_id IN ({placeholders})", id_list)
            cursor.execute(f"DELETE FROM customer_pos WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount
            conn.commit()
        return deleted_count

    @staticmethod
    def delete(po_id):
        return CustomerPOModel.delete_many([po_id]) > 0


    @staticmethod
    def get_by_po_number(po_number):
        if not po_number or not str(po_number).strip():
            return None
        clean_num = str(po_number).strip()
        row = db.fetch_one("SELECT id FROM customer_pos WHERE UPPER(po_number) = UPPER(?)", (clean_num,))
        if row:
            return CustomerPOModel.get_by_id(row['id'])
        return None

    @staticmethod
    def get_pos_for_customer(customer_id):
        if not customer_id:
            return []
        sql = """
        SELECT id, po_number, po_date, total_ordered_qty_kg, total_dispatched_qty_kg, status
        FROM customer_pos
        WHERE customer_id = ? AND status != 'Cancelled'
        ORDER BY id DESC
        """
        return db.fetch_all(sql, (customer_id,))

    @staticmethod
    def sync_invoice_dispatch(invoice_number, po_number, dispatch_date, dispatched_qty_kg, dispatched_amount=0.0, notes=""):
        """
        Syncs a sales invoice's billed quantity against the referenced Customer PO.
        Idempotent: Removes any previous dispatch record for this invoice_number and re-applies if po_number matches.
        """
        if not invoice_number:
            return

        inv_clean = str(invoice_number).strip()
        po_clean = str(po_number or '').strip()

        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Find any POs previously affected by this invoice
            prev_records = cursor.execute("SELECT DISTINCT customer_po_id FROM customer_po_dispatches WHERE invoice_number = ?", (inv_clean,)).fetchall()
            affected_po_ids = {r[0] for r in prev_records}

            # 2. Delete old dispatches for this invoice number
            cursor.execute("DELETE FROM customer_po_dispatches WHERE invoice_number = ?", (inv_clean,))

            # 3. If a valid matching Customer PO is specified, insert new dispatch
            if po_clean:
                po_row = cursor.execute("SELECT id FROM customer_pos WHERE UPPER(po_number) = UPPER(?)", (po_clean,)).fetchone()
                if po_row:
                    target_po_id = po_row[0]
                    affected_po_ids.add(target_po_id)
                    disp_date = dispatch_date or datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("""
                        INSERT INTO customer_po_dispatches (customer_po_id, dispatch_date, invoice_number, dispatched_qty_kg, dispatched_amount, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (target_po_id, disp_date, inv_clean, _to_float(dispatched_qty_kg), _to_float(dispatched_amount), notes or f"Billed via Tax Invoice #{inv_clean}"))

            # 4. Recalculate total_dispatched_qty_kg, total_dispatched_amount, and status for all affected POs
            for p_id in affected_po_ids:
                disp_totals = cursor.execute("""
                    SELECT COALESCE(SUM(dispatched_qty_kg), 0.0) as sum_qty,
                           COALESCE(SUM(dispatched_amount), 0.0) as sum_amt
                    FROM customer_po_dispatches
                    WHERE customer_po_id = ?
                """, (p_id,)).fetchone()

                sum_qty = _to_float(disp_totals[0]) if disp_totals else 0.0
                sum_amt = _to_float(disp_totals[1]) if disp_totals else 0.0

                po_info = cursor.execute("SELECT total_ordered_qty_kg FROM customer_pos WHERE id = ?", (p_id,)).fetchone()
                if po_info:
                    ord_qty = _to_float(po_info[0])
                    if sum_qty >= ord_qty and ord_qty > 0:
                        new_status = 'Completed'
                    elif sum_qty > 0:
                        new_status = 'Partially Dispatched'
                    else:
                        new_status = 'Open'

                    cursor.execute("""
                        UPDATE customer_pos
                        SET total_dispatched_qty_kg = ?, total_dispatched_amount = ?, status = ?
                        WHERE id = ?
                    """, (sum_qty, sum_amt, new_status, p_id))

            conn.commit()

    @staticmethod
    def remove_invoice_dispatch(invoice_number):
        """
        Removes dispatch records associated with an invoice and restores the PO balances.
        """
        if not invoice_number:
            return
        CustomerPOModel.sync_invoice_dispatch(invoice_number=invoice_number, po_number=None, dispatch_date=None, dispatched_qty_kg=0.0, dispatched_amount=0.0)

    @staticmethod
    def record_dispatch(po_id, dispatch_date, invoice_number, dispatched_qty_kg, dispatched_amount=0.0, notes=""):
        po = CustomerPOModel.get_by_id(po_id)
        if not po:
            return False

        qty_kg = _to_float(dispatched_qty_kg)
        amt = _to_float(dispatched_amount)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Insert dispatch history log
            cursor.execute("""
            INSERT INTO customer_po_dispatches (customer_po_id, dispatch_date, invoice_number, dispatched_qty_kg, dispatched_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (po_id, dispatch_date, invoice_number, qty_kg, amt, notes))

            # 2. Update Customer PO totals
            cursor.execute("""
            UPDATE customer_pos SET
                total_dispatched_qty_kg = total_dispatched_qty_kg + ?,
                total_dispatched_amount = total_dispatched_amount + ?
            WHERE id = ?
            """, (qty_kg, amt, po_id))

            conn.commit()

        CustomerPOModel.recalculate_po_status(po_id)
        return True

    @staticmethod
    def recalculate_po_status(po_id):
        po = db.fetch_one("SELECT total_ordered_qty_kg, total_dispatched_qty_kg FROM customer_pos WHERE id = ?", (po_id,))
        if not po:
            return

        ordered = _to_float(po['total_ordered_qty_kg'])
        dispatched = _to_float(po['total_dispatched_qty_kg'])

        if dispatched >= ordered and ordered > 0:
            status = 'Completed'
        elif dispatched > 0:
            status = 'Partially Dispatched'
        else:
            status = 'Open'

        db.execute_query("UPDATE customer_pos SET status = ? WHERE id = ?", (status, po_id))

    @staticmethod
    def get_summary():
        rows = db.fetch_all("SELECT total_ordered_qty_kg, total_dispatched_qty_kg, total_po_amount, total_dispatched_amount, status FROM customer_pos WHERE status != 'Cancelled'")
        
        tot_ordered_kg = sum(_to_float(r['total_ordered_qty_kg']) for r in rows)
        tot_dispatched_kg = sum(_to_float(r['total_dispatched_qty_kg']) for r in rows)
        tot_balance_kg = max(0.0, tot_ordered_kg - tot_dispatched_kg)

        tot_val = sum(_to_float(r['total_po_amount']) for r in rows)
        tot_dispatched_val = sum(_to_float(r['total_dispatched_amount']) for r in rows)
        tot_balance_val = max(0.0, tot_val - tot_dispatched_val)

        open_po_count = sum(1 for r in rows if r['status'] in ('Open', 'Partially Dispatched'))

        return {
            'total_ordered_kg': tot_ordered_kg,
            'total_dispatched_kg': tot_dispatched_kg,
            'total_balance_kg': tot_balance_kg,
            'total_po_value': tot_val,
            'total_balance_value': tot_balance_val,
            'open_po_count': open_po_count
        }
