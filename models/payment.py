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
        Recalculates current outstanding balance for a contact.
        Customer Balance = (Total Sales Invoices) - (Total Payment In Received)
        Supplier Balance = (Total Purchase Orders) - (Total Payment Out Paid)
        """
        cursor.execute("SELECT contact_type FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()
        if not row:
            return

        c_type = row['contact_type']

        if c_type == 'Customer':
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) as tot FROM sales_orders WHERE customer_id = ? AND status != 'Cancelled'", (contact_id,))
            total_billed = float(cursor.fetchone()['tot'])

            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) as tot FROM payments WHERE contact_id = ? AND payment_type = 'Payment In'", (contact_id,))
            total_paid = float(cursor.fetchone()['tot'])

            balance = total_billed - total_paid
        else: # Supplier
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) as tot FROM purchase_orders WHERE supplier_id = ? AND status != 'Cancelled'", (contact_id,))
            total_billed = float(cursor.fetchone()['tot'])

            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) as tot FROM payments WHERE contact_id = ? AND payment_type = 'Payment Out'", (contact_id,))
            total_paid = float(cursor.fetchone()['tot'])

            balance = total_billed - total_paid

        cursor.execute("UPDATE contacts SET balance = ? WHERE id = ?", (balance, contact_id))

    @staticmethod
    def recalculate_all_balances():
        """Helper to sync all contact balances across the entire database."""
        contacts = db.fetch_all("SELECT id FROM contacts")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for c in contacts:
                PaymentModel._recalculate_contact_balance(cursor, c['id'])
            conn.commit()

    @staticmethod
    def get_summary():
        # Recalculate first to ensure exact accuracy
        PaymentModel.recalculate_all_balances()

        tot_in_row = db.fetch_one("SELECT COALESCE(SUM(amount), 0.0) as tot FROM payments WHERE payment_type = 'Payment In'")
        total_received = tot_in_row['tot'] if tot_in_row else 0.0

        tot_out_row = db.fetch_one("SELECT COALESCE(SUM(amount), 0.0) as tot FROM payments WHERE payment_type = 'Payment Out'")
        total_paid = tot_out_row['tot'] if tot_out_row else 0.0

        net_rec_row = db.fetch_one("SELECT COALESCE(SUM(balance), 0.0) as tot FROM contacts WHERE contact_type = 'Customer' AND balance > 0")
        net_receivable = net_rec_row['tot'] if net_rec_row else 0.0

        net_pay_row = db.fetch_one("SELECT COALESCE(SUM(balance), 0.0) as tot FROM contacts WHERE contact_type = 'Supplier' AND balance > 0")
        net_payable = net_pay_row['tot'] if net_pay_row else 0.0

        return {
            'total_received': total_received,
            'total_paid': total_paid,
            'net_receivable': net_receivable,
            'net_payable': net_payable
        }

    @staticmethod
    def get_party_ledger(contact_id):
        contact = db.fetch_one("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        if not contact:
            return None

        ledger_entries = []

        # 1. Fetch Sales Orders (if Customer)
        if contact['contact_type'] == 'Customer':
            orders = db.fetch_all("""
                SELECT invoice_date as date, invoice_number as ref_no, 'Sales Invoice' as txn_type,
                       total_amount as amount, notes, 'Debit' as dr_cr
                FROM sales_orders
                WHERE customer_id = ? AND status != 'Cancelled'
            """, (contact_id,))
            ledger_entries.extend(orders)

        # 2. Fetch Purchase Orders (if Supplier)
        if contact['contact_type'] == 'Supplier':
            pos = db.fetch_all("""
                SELECT order_date as date, po_number as ref_no, 'Purchase Order' as txn_type,
                       total_amount as amount, notes, 'Credit' as dr_cr
                FROM purchase_orders
                WHERE supplier_id = ? AND status != 'Cancelled'
            """, (contact_id,))
            ledger_entries.extend(pos)

        # 3. Fetch Payments
        payments = db.fetch_all("""
            SELECT payment_date as date, payment_number as ref_no,
                   (payment_type || ' (' || payment_mode || ')') as txn_type,
                   amount, notes,
                   CASE WHEN payment_type = 'Payment In' THEN 'Credit' ELSE 'Debit' END as dr_cr
            FROM payments
            WHERE contact_id = ?
        """, (contact_id,))
        ledger_entries.extend(payments)

        # Sort entries chronologically by date
        ledger_entries.sort(key=lambda x: str(x['date']))

        running_balance = 0.0
        total_billed = 0.0
        total_paid_received = 0.0

        processed_rows = []
        for entry in ledger_entries:
            amt = float(entry['amount'])
            t_type = entry['txn_type']

            if "Sales Invoice" in t_type or "Purchase Order" in t_type:
                total_billed += amt
                running_balance += amt
                debit_val = amt
                credit_val = 0.0
            else:
                total_paid_received += amt
                running_balance -= amt
                debit_val = 0.0
                credit_val = amt

            processed_rows.append({
                'date': entry['date'],
                'ref_no': entry['ref_no'],
                'txn_type': entry['txn_type'],
                'debit': debit_val,
                'credit': credit_val,
                'balance': running_balance,
                'notes': entry.get('notes', '')
            })

        return {
            'contact': contact,
            'rows': processed_rows,
            'total_billed': total_billed,
            'total_paid_received': total_paid_received,
            'net_balance': running_balance
        }
