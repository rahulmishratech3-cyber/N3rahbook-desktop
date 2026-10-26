"""
Payment & Party Ledger Model
Handles Payment In (Customer collections), Payment Out (Vendor payouts),
Payment Modes (Cash, UPI, Bank, Cheque, Card), and Party Ledger Statements.
"""

from datetime import datetime
from database.db_manager import db

class PaymentModel:
    PAYMENT_MODES = ["Cash", "UPI", "Bank Transfer", "Cheque", "Card", "Net Banking", "Other"]
    PAYMENT_TYPES = ["Payment In", "Payment Out"]

    @staticmethod
    def generate_payment_number():
        res = db.fetch_all("SELECT id FROM payments")
        next_num = len(res) + 1
        year_str = datetime.now().year
        return f"PAY-{year_str}-{next_num:04d}"

    @staticmethod
    def get_all():
        sql = """
        SELECT p.*, c.name as contact_name, c.company_name, c.contact_type
        FROM payments p
        JOIN contacts c ON p.contact_id = c.id
        ORDER BY p.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_by_id(payment_id):
        sql = """
        SELECT p.*, c.name as contact_name, c.company_name, c.contact_type
        FROM payments p
        JOIN contacts c ON p.contact_id = c.id
        WHERE p.id = ?
        """
        return db.fetch_one(sql, (payment_id,))

    @staticmethod
    def search(query="", payment_type="All", payment_mode="All"):
        sql = """
        SELECT p.*, c.name as contact_name, c.company_name, c.contact_type
        FROM payments p
        JOIN contacts c ON p.contact_id = c.id
        WHERE 1=1
        """
        params = []

        if query:
            q = f"%{query}%"
            sql += " AND (p.payment_number LIKE ? OR c.name LIKE ? OR c.company_name LIKE ? OR p.reference_no LIKE ? OR p.notes LIKE ?)"
            params.extend([q, q, q, q, q])

        if payment_type != "All":
            sql += " AND p.payment_type = ?"
            params.append(payment_type)

        if payment_mode != "All":
            sql += " AND p.payment_mode = ?"
            params.append(payment_mode)

        sql += " ORDER BY p.id DESC"
        return db.fetch_all(sql, params)

    @staticmethod
    def create(payment_data):
        payment_num = payment_data.get('payment_number') or PaymentModel.generate_payment_number()
        contact_id = payment_data.get('contact_id')
        payment_type = payment_data.get('payment_type', 'Payment In')
        payment_mode = payment_data.get('payment_mode', 'Cash')
        amount = float(payment_data.get('amount', 0.0))
        payment_date = payment_data.get('payment_date', datetime.now().strftime("%Y-%m-%d"))
        ref_no = payment_data.get('reference_no', '')
        so_id = payment_data.get('sales_order_id')
        po_id = payment_data.get('purchase_order_id')
        notes = payment_data.get('notes', '')

        with db.get_connection() as conn:
            cursor = conn.cursor()
            sql_insert = """
            INSERT INTO payments (
                payment_number, contact_id, payment_type, payment_mode,
                amount, payment_date, reference_no, sales_order_id, purchase_order_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_insert, (
                payment_num, contact_id, payment_type, payment_mode,
                amount, payment_date, ref_no, so_id, po_id, notes
            ))
            payment_id = cursor.lastrowid

            # Recalculate Contact Balance
            PaymentModel._recalculate_contact_balance(cursor, contact_id)
            conn.commit()
            return payment_id

    @staticmethod
    def delete_many(payment_ids):
        if not payment_ids:
            return 0

        id_list = list({int(pid) for pid in payment_ids})
        placeholders = ",".join(["?"] * len(id_list))

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT DISTINCT contact_id FROM payments WHERE id IN ({placeholders})", id_list)
            contact_rows = cursor.fetchall()
            affected_contacts = [r['contact_id'] for r in contact_rows]

            cursor.execute(f"DELETE FROM payments WHERE id IN ({placeholders})", id_list)
            deleted_count = cursor.rowcount

            for cid in affected_contacts:
                PaymentModel._recalculate_contact_balance(cursor, cid)

            conn.commit()
        return deleted_count

    @staticmethod
    def delete(payment_id):
        return PaymentModel.delete_many([payment_id]) > 0


    @staticmethod
    def _recalculate_contact_balance(cursor, contact_id):
        """
        Recalculates current outstanding balance for a contact in 1 direct query.
        Customer Balance = (Total Sales Invoices) - (Total Payment In Received)
        Supplier Balance = (Total Purchase Orders) - (Total Payment Out Paid)
        """
        cursor.execute("SELECT contact_type FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()
        if not row:
            return

        c_type = row['contact_type']

        if c_type == 'Customer':
            cursor.execute("""
                UPDATE contacts
                SET balance = COALESCE((
                    SELECT COALESCE(SUM(total_amount), 0.0) FROM sales_orders WHERE customer_id = ? AND status != 'Cancelled'
                ), 0.0) - COALESCE((
                    SELECT COALESCE(SUM(amount), 0.0) FROM payments WHERE contact_id = ? AND payment_type = 'Payment In'
                ), 0.0)
                WHERE id = ?
            """, (contact_id, contact_id, contact_id))
        else: # Supplier
            cursor.execute("""
                UPDATE contacts
                SET balance = COALESCE((
                    SELECT COALESCE(SUM(total_amount), 0.0) FROM purchase_orders WHERE supplier_id = ? AND status != 'Cancelled'
                ), 0.0) - COALESCE((
                    SELECT COALESCE(SUM(amount), 0.0) FROM payments WHERE contact_id = ? AND payment_type = 'Payment Out'
                ), 0.0)
                WHERE id = ?
            """, (contact_id, contact_id, contact_id))

    @staticmethod
    def recalculate_all_balances():
        """Helper to sync all contact balances across the entire database in 2 bulk SQL updates."""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contacts
                    SET balance = COALESCE((
                        SELECT COALESCE(SUM(so.total_amount), 0.0)
                        FROM sales_orders so
                        WHERE so.customer_id = contacts.id AND so.status != 'Cancelled'
                    ), 0.0) - COALESCE((
                        SELECT COALESCE(SUM(p.amount), 0.0)
                        FROM payments p
                        WHERE p.contact_id = contacts.id AND p.payment_type = 'Payment In'
                    ), 0.0)
                    WHERE contact_type = 'Customer';
                """)
                cursor.execute("""
                    UPDATE contacts
                    SET balance = COALESCE((
                        SELECT COALESCE(SUM(po.total_amount), 0.0)
                        FROM purchase_orders po
                        WHERE po.supplier_id = contacts.id AND po.status != 'Cancelled'
                    ), 0.0) - COALESCE((
                        SELECT COALESCE(SUM(p.amount), 0.0)
                        FROM payments p
                        WHERE p.contact_id = contacts.id AND p.payment_type = 'Payment Out'
                    ), 0.0)
                    WHERE contact_type = 'Supplier';
                """)
                conn.commit()
        except Exception as ex:
            print(f"[Warning] Failed bulk balance recalculation: {ex}")

    @staticmethod
    def get_summary(recalculate=False):
        if recalculate:
            PaymentModel.recalculate_all_balances()

        try:
            row = db.fetch_one("""
                SELECT
                    (SELECT COALESCE(SUM(amount), 0.0) FROM payments WHERE payment_type = 'Payment In') as total_received,
                    (SELECT COALESCE(SUM(amount), 0.0) FROM payments WHERE payment_type = 'Payment Out') as total_paid,
                    (SELECT COALESCE(SUM(balance), 0.0) FROM contacts WHERE contact_type = 'Customer' AND balance > 0) as net_receivable,
                    (SELECT COALESCE(SUM(balance), 0.0) FROM contacts WHERE contact_type = 'Supplier' AND balance > 0) as net_payable
            """)
            if row:
                return {
                    'total_received': float(row.get('total_received') or 0.0),
                    'total_paid': float(row.get('total_paid') or 0.0),
                    'net_receivable': float(row.get('net_receivable') or 0.0),
                    'net_payable': float(row.get('net_payable') or 0.0)
                }
        except Exception as ex:
            print("Payment get_summary error:", ex)

        return {
            'total_received': 0.0,
            'total_paid': 0.0,
            'net_receivable': 0.0,
            'net_payable': 0.0
        }

    @staticmethod
    def recalculate_contact_balance(contact_id):
        """Public helper to recalculate a single contact's balance."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            PaymentModel._recalculate_contact_balance(cursor, contact_id)
            conn.commit()

    @staticmethod
    def sync_sales_invoice_payment(sales_order_id, is_paid=True, payment_mode="Cash"):
        """
        When a sales order is marked 'Paid':
        Ensures a linked 'Payment In' record exists in `payments` with sales_order_id = sales_order_id.
        When marked 'Unpaid' or 'Cancelled':
        Removes the linked 'Payment In' record.
        Always recalculates customer balance.
        """
        order = db.fetch_one("SELECT * FROM sales_orders WHERE id = ?", (sales_order_id,))
        if not order:
            return

        customer_id = order['customer_id']
        total_amount = float(order.get('total_amount') or 0.0)
        inv_no = order.get('invoice_number', f"INV-{sales_order_id}")
        inv_date = order.get('invoice_date') or datetime.now().strftime("%Y-%m-%d")

        status_str = str(order.get('status') or '').strip().lower()
        if status_str == 'cancelled':
            is_paid = False

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, amount FROM payments WHERE sales_order_id = ? AND payment_type = 'Payment In'", (sales_order_id,))
            existing = cursor.fetchone()

            if is_paid:
                if existing:
                    cursor.execute("""
                        UPDATE payments
                        SET contact_id = ?, amount = ?, payment_date = ?, reference_no = ?, notes = ?
                        WHERE id = ?
                    """, (
                        customer_id,
                        total_amount,
                        inv_date,
                        f"INV#{inv_no}",
                        f"Auto-settled via Tax Invoice #{inv_no}",
                        existing['id']
                    ))
                else:
                    pay_num = PaymentModel.generate_payment_number()
                    cursor.execute("""
                        INSERT INTO payments (
                            payment_number, contact_id, payment_type, payment_mode,
                            amount, payment_date, reference_no, sales_order_id, notes
                        ) VALUES (?, ?, 'Payment In', ?, ?, ?, ?, ?, ?)
                    """, (
                        pay_num,
                        customer_id,
                        payment_mode or 'Cash',
                        total_amount,
                        inv_date,
                        f"INV#{inv_no}",
                        sales_order_id,
                        f"Auto-settled via Tax Invoice #{inv_no}"
                    ))
            else:
                if existing:
                    cursor.execute("DELETE FROM payments WHERE sales_order_id = ? AND payment_type = 'Payment In'", (sales_order_id,))

            PaymentModel._recalculate_contact_balance(cursor, customer_id)
            conn.commit()

    @staticmethod
    def sync_purchase_order_payment(purchase_order_id, is_paid=True, payment_mode="Bank Transfer"):
        """
        When a purchase order is marked 'Paid':
        Ensures a linked 'Payment Out' record exists in `payments` with purchase_order_id = po_id.
        When marked 'Unpaid' or 'Cancelled':
        Removes the linked 'Payment Out' record.
        Always recalculates supplier balance.
        """
        po = db.fetch_one("SELECT * FROM purchase_orders WHERE id = ?", (purchase_order_id,))
        if not po:
            return

        supplier_id = po['supplier_id']
        total_amount = float(po.get('total_amount') or 0.0)
        po_no = po.get('po_number', f"PO-{purchase_order_id}")
        po_date = po.get('order_date') or datetime.now().strftime("%Y-%m-%d")

        status_str = str(po.get('status') or '').strip().lower()
        if status_str == 'cancelled':
            is_paid = False

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, amount FROM payments WHERE purchase_order_id = ? AND payment_type = 'Payment Out'", (purchase_order_id,))
            existing = cursor.fetchone()

            if is_paid:
                if existing:
                    cursor.execute("""
                        UPDATE payments
                        SET contact_id = ?, amount = ?, payment_date = ?, reference_no = ?, notes = ?
                        WHERE id = ?
                    """, (
                        supplier_id,
                        total_amount,
                        po_date,
                        f"PO#{po_no}",
                        f"Auto-settled via PO #{po_no}",
                        existing['id']
                    ))
                else:
                    pay_num = PaymentModel.generate_payment_number()
                    cursor.execute("""
                        INSERT INTO payments (
                            payment_number, contact_id, payment_type, payment_mode,
                            amount, payment_date, reference_no, purchase_order_id, notes
                        ) VALUES (?, ?, 'Payment Out', ?, ?, ?, ?, ?, ?)
                    """, (
                        pay_num,
                        supplier_id,
                        payment_mode or 'Bank Transfer',
                        total_amount,
                        po_date,
                        f"PO#{po_no}",
                        purchase_order_id,
                        f"Auto-settled via PO #{po_no}"
                    ))
            else:
                if existing:
                    cursor.execute("DELETE FROM payments WHERE purchase_order_id = ? AND payment_type = 'Payment Out'", (purchase_order_id,))

            PaymentModel._recalculate_contact_balance(cursor, supplier_id)
            conn.commit()

    @staticmethod
    def sync_all_existing_paid_invoices():
        """
        Scans existing sales orders and purchase orders.
        Syncs payment records for any orders marked 'Paid'.
        Ensures all contact balances match real running balance.
        """
        try:
            # Sales orders
            paid_sales = db.fetch_all("""
                SELECT id, payment_status, status FROM sales_orders
                WHERE status != 'Cancelled' AND (payment_status = 'Paid' OR status = 'Paid')
            """)
            for s in paid_sales:
                PaymentModel.sync_sales_invoice_payment(s['id'], is_paid=True)

            # Purchase orders
            try:
                paid_pos = db.fetch_all("""
                    SELECT id, payment_status, status FROM purchase_orders
                    WHERE status != 'Cancelled' AND (payment_status = 'Paid' OR status = 'Paid')
                """)
                for p in paid_pos:
                    PaymentModel.sync_purchase_order_payment(p['id'], is_paid=True)
            except Exception:
                pass

            PaymentModel.recalculate_all_balances()
        except Exception as ex:
            print(f"[PaymentModel] Error syncing existing paid invoices: {ex}")

    @staticmethod
    def get_party_ledger(contact_id):
        contact = db.fetch_one("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        if not contact:
            return None

        c_type = contact.get('contact_type', 'Customer')
        ledger_entries = []

        # 1. Fetch Sales Orders (if Customer)
        if c_type == 'Customer':
            orders = db.fetch_all("""
                SELECT invoice_date as date, invoice_number as ref_no, 'Sales Invoice' as txn_type,
                       total_amount as amount, notes, 'Debit' as dr_cr, created_at, id as order_id,
                       payment_status, status
                FROM sales_orders
                WHERE customer_id = ? AND status != 'Cancelled'
            """, (contact_id,))
            ledger_entries.extend(orders)

        # 2. Fetch Purchase Orders (if Supplier)
        if c_type == 'Supplier':
            pos = db.fetch_all("""
                SELECT order_date as date, po_number as ref_no, 'Purchase Order' as txn_type,
                       total_amount as amount, notes, 'Credit' as dr_cr, created_at, id as po_id,
                       status
                FROM purchase_orders
                WHERE supplier_id = ? AND status != 'Cancelled'
            """, (contact_id,))
            ledger_entries.extend(pos)

        # 3. Fetch Payments
        payments = db.fetch_all("""
            SELECT payment_date as date, payment_number as ref_no,
                   (payment_type || ' (' || payment_mode || ')') as txn_type,
                   amount, notes,
                   CASE WHEN payment_type = 'Payment In' THEN 'Credit' ELSE 'Debit' END as dr_cr,
                   created_at, sales_order_id, purchase_order_id, payment_type
            FROM payments
            WHERE contact_id = ?
        """, (contact_id,))
        ledger_entries.extend(payments)

        # Sort entries chronologically by date; on same date, invoice appears before its settlement
        def _sort_key(item):
            d = str(item.get('date') or '')
            t = str(item.get('txn_type') or '')
            priority = 0 if ('Sales Invoice' in t or 'Purchase Order' in t) else 1
            c = str(item.get('created_at') or '')
            return (d, priority, c)

        ledger_entries.sort(key=_sort_key)

        running_balance = 0.0
        total_billed = 0.0
        total_paid_received = 0.0

        processed_rows = []
        for entry in ledger_entries:
            amt = float(entry.get('amount') or 0.0)
            t_type = entry.get('txn_type', '')

            if c_type == 'Customer':
                if "Sales Invoice" in t_type:
                    total_billed += amt
                    running_balance += amt
                    debit_val = amt
                    credit_val = 0.0
                else: # Payment In
                    total_paid_received += amt
                    running_balance -= amt
                    debit_val = 0.0
                    credit_val = amt
            else: # Supplier / Vendor
                if "Purchase Order" in t_type:
                    total_billed += amt
                    running_balance += amt
                    debit_val = 0.0
                    credit_val = amt
                else: # Payment Out
                    total_paid_received += amt
                    running_balance -= amt
                    debit_val = amt
                    credit_val = 0.0

            processed_rows.append({
                'date': entry.get('date'),
                'ref_no': entry.get('ref_no'),
                'txn_type': entry.get('txn_type'),
                'debit': debit_val,
                'credit': credit_val,
                'balance': round(running_balance, 2),
                'notes': entry.get('notes', '')
            })

        return {
            'contact': contact,
            'rows': processed_rows,
            'total_billed': round(total_billed, 2),
            'total_paid_received': round(total_paid_received, 2),
            'net_balance': round(running_balance, 2)
        }

