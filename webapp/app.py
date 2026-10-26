"""
N3RAH BOOK - Web Application Server
Full-featured browser-based ERP, Billing & Inventory Management System.
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
import datetime
from functools import wraps

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, send_file, send_from_directory, abort
)
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider

# Import existing backend models and services
from database.db_manager import db
from models.user import UserModel
from models.item import ItemModel
from models.contact import ContactModel
from models.sales_order import SalesOrderModel
from models.purchase_order import PurchaseOrderModel
from models.customer_po import CustomerPOModel
from models.payment import PaymentModel
from models.company import CompanyModel
from models.report import ReportModel
from models.fiscal_year import FiscalYearModel
from services.pdf_service import (
    generate_tax_invoice_pdf,
    generate_purchase_invoice_pdf,
    generate_customer_po_pdf
)
from services.num2words_service import number_to_words_indian
from config import INVOICES_DIR

# Custom JSON Provider to handle Decimals, Dates, and Bytes automatically
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return super().default(obj)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
app.json = CustomJSONProvider(app)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "n3rah_book_super_secret_key_2026_didu")
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)


# -------------------------------------------------------------
# Authentication Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        if session.get('role') != 'Admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# Static Assets Serving
# -------------------------------------------------------------
@app.route('/assets/<path:filename>')
def serve_project_assets(filename):
    assets_dir = os.path.join(ROOT_DIR, 'assets')
    return send_from_directory(assets_dir, filename)


# -------------------------------------------------------------
# HTML Pages
# -------------------------------------------------------------
@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index_page'))
    company = CompanyModel.get_profile()
    return render_template('login.html', company=company)

@app.route('/')
@login_required
def index_page():
    company = CompanyModel.get_profile()
    return render_template('index.html', user=session, company=company)


# -------------------------------------------------------------
# Auth API Endpoints
# -------------------------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    remember = data.get('remember', False)

    if not username or not password:
        return jsonify({"success": False, "error": "Username aur Password dono zaroori hain."}), 400

    user = UserModel.authenticate(username, password)
    if not user:
        return jsonify({"success": False, "error": "Galat Username ya Password! Kripya dobara check karein."}), 401

    session.permanent = bool(remember)
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    session['role'] = user['role']

    return jsonify({
        "success": True,
        "message": f"Swagatam, {user['full_name']}!",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "full_name": user['full_name'],
            "role": user['role']
        }
    })

@app.route('/logout')
@app.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    if request.path.startswith('/api/'):
        return jsonify({"success": True})
    return redirect(url_for('login_page'))

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "user": {
            "id": session.get('user_id'),
            "username": session.get('username'),
            "full_name": session.get('full_name'),
            "role": session.get('role')
        },
        "cloud_mode": db.cloud_mode,
        "backend_name": "Cloud PostgreSQL" if db.cloud_mode else "Local SQLite"
    })


# -------------------------------------------------------------
# Dashboard API
# -------------------------------------------------------------
@app.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    kpi = ReportModel.get_kpi_summary()
    recent_sales = SalesOrderModel.get_all()[:6]
    
    # Low stock items list
    low_stock_items = db.fetch_all("""
        SELECT id, name, sku, category, current_stock, reorder_level, unit
        FROM items
        WHERE current_stock <= reorder_level
        ORDER BY current_stock ASC
        LIMIT 6
    """)

    # Category distribution for chart
    cat_dist = ReportModel.get_category_distribution()

    # Total counts
    counts = {
        "items": db.fetch_one("SELECT COUNT(*) as c FROM items")['c'],
        "contacts": db.fetch_one("SELECT COUNT(*) as c FROM contacts")['c'],
        "sales": db.fetch_one("SELECT COUNT(*) as c FROM sales_orders")['c'],
        "purchases": db.fetch_one("SELECT COUNT(*) as c FROM purchase_orders")['c']
    }

    return jsonify({
        "success": True,
        "kpi": kpi,
        "recent_sales": recent_sales,
        "low_stock_items": low_stock_items,
        "category_distribution": cat_dist,
        "counts": counts,
        "cloud_mode": db.cloud_mode
    })


# -------------------------------------------------------------
# Items / Inventory API
# -------------------------------------------------------------
@app.route('/api/items', methods=['GET'])
@login_required
def api_items_list():
    query = request.args.get('query', '')
    category = request.args.get('category', 'All')
    subcategory = request.args.get('subcategory', 'All')
    stock_filter = request.args.get('stock_filter', 'All')

    items = ItemModel.search(query=query, category=category, subcategory=subcategory, stock_filter=stock_filter)
    return jsonify({"success": True, "items": items})

@app.route('/api/items/meta', methods=['GET'])
@login_required
def api_items_meta():
    return jsonify({
        "success": True,
        "categories": ItemModel.DEFAULT_CATEGORIES,
        "subcategories": ItemModel.DEFAULT_SUBCATEGORIES
    })

@app.route('/api/items/<int:item_id>', methods=['GET'])
@login_required
def api_item_get(item_id):
    item = ItemModel.get_by_id(item_id)
    if not item:
        return jsonify({"success": False, "error": "Item not found"}), 404
    return jsonify({"success": True, "item": item})

@app.route('/api/items', methods=['POST'])
@login_required
def api_item_create():
    data = request.get_json(force=True) or {}
    try:
        new_id = ItemModel.create(data)
        return jsonify({"success": True, "id": new_id, "message": "Product successfully added!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def api_item_update(item_id):
    data = request.get_json(force=True) or {}
    try:
        ItemModel.update(item_id, data)
        return jsonify({"success": True, "message": "Product updated successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def api_item_delete(item_id):
    try:
        ItemModel.delete(item_id)
        return jsonify({"success": True, "message": "Product removed successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/items/<int:item_id>/adjust-stock', methods=['POST'])
@login_required
def api_item_adjust_stock(item_id):
    data = request.get_json(force=True) or {}
    qty = float(data.get('quantity', 0.0))
    adj_type = data.get('adjustment_type', 'Add')  # 'Add' or 'Remove'
    reason = data.get('reason', 'Manual Adjustment')
    notes = data.get('notes', '')

    if qty <= 0:
        return jsonify({"success": False, "error": "Quantity must be greater than zero."}), 400

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            sign = 1 if adj_type == 'Add' else -1
            delta = sign * qty
            cursor.execute("UPDATE items SET current_stock = ROUND(current_stock + ?, 4) WHERE id = ?", (delta, item_id))
            cursor.execute("""
                INSERT INTO stock_adjustments (item_id, adjustment_type, quantity, reason, adjusted_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item_id, adj_type, qty, reason, session.get('full_name', 'Web User'), notes))
            conn.commit()

        return jsonify({"success": True, "message": f"Stock {adj_type.lower()}ed by {qty} successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 500


# -------------------------------------------------------------
# Contacts (Customers & Suppliers) API
# -------------------------------------------------------------
@app.route('/api/contacts', methods=['GET'])
@login_required
def api_contacts_list():
    query = request.args.get('query', '')
    contact_type = request.args.get('type', 'All')
    contacts = ContactModel.search(query=query, contact_type=contact_type)
    return jsonify({"success": True, "contacts": contacts})

@app.route('/api/contacts/<int:contact_id>', methods=['GET'])
@login_required
def api_contact_get(contact_id):
    c = ContactModel.get_by_id(contact_id)
    if not c:
        return jsonify({"success": False, "error": "Contact not found"}), 404
    return jsonify({"success": True, "contact": c})

@app.route('/api/contacts/<int:contact_id>/ledger', methods=['GET'])
@login_required
def api_contact_ledger(contact_id):
    ledger = PaymentModel.get_party_ledger(contact_id)
    if not ledger:
        return jsonify({"success": False, "error": "Party not found"}), 404
    return jsonify({"success": True, "ledger": ledger})

@app.route('/api/contacts', methods=['POST'])
@login_required
def api_contact_create():
    data = request.get_json(force=True) or {}
    if not data.get('name'):
        return jsonify({"success": False, "error": "Party name is required"}), 400
    try:
        new_id = ContactModel.create(data)
        return jsonify({"success": True, "id": new_id, "message": "Party created successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def api_contact_update(contact_id):
    data = request.get_json(force=True) or {}
    try:
        ContactModel.update(contact_id, data)
        return jsonify({"success": True, "message": "Party updated successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def api_contact_delete(contact_id):
    try:
        ContactModel.delete(contact_id)
        return jsonify({"success": True, "message": "Party deleted successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


# -------------------------------------------------------------
# Tax Invoices & Sales Orders API
# -------------------------------------------------------------
@app.route('/api/sales', methods=['GET'])
@login_required
def api_sales_list():
    orders = SalesOrderModel.get_all()
    return jsonify({"success": True, "sales_orders": orders})

@app.route('/api/sales/<int:order_id>', methods=['GET'])
@login_required
def api_sales_get(order_id):
    order = SalesOrderModel.get_by_id(order_id)
    if not order:
        return jsonify({"success": False, "error": "Invoice not found"}), 404
    return jsonify({"success": True, "order": order})

@app.route('/api/sales/next-number', methods=['GET'])
@login_required
def api_sales_next_number():
    all_orders = SalesOrderModel.get_all()
    next_id = len(all_orders) + 1
    inv_num = f"INV-{datetime.datetime.now().year}-{next_id:03d}"
    return jsonify({"success": True, "invoice_number": inv_num})

@app.route('/api/sales', methods=['POST'])
@login_required
def api_sales_create():
    data = request.get_json(force=True) or {}
    order_data = data.get('order', {})
    item_rows = data.get('items', [])

    if not order_data.get('customer_id'):
        return jsonify({"success": False, "error": "Customer selection is required"}), 400
    if not item_rows:
        return jsonify({"success": False, "error": "At least one item row is required"}), 400

    try:
        new_id = SalesOrderModel.create(order_data, item_rows)
        return jsonify({"success": True, "id": new_id, "message": "Tax Invoice successfully generated!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/sales/<int:order_id>/status', methods=['PUT'])
@login_required
def api_sales_update_status(order_id):
    data = request.get_json(force=True) or {}
    status = data.get('status')
    payment_status = data.get('payment_status')

    try:
        SalesOrderModel.update_status(order_id, status=status, payment_status=payment_status)
        return jsonify({"success": True, "message": "Invoice status updated!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/sales/<int:order_id>', methods=['DELETE'])
@login_required
def api_sales_delete(order_id):
    try:
        SalesOrderModel.delete(order_id)
        return jsonify({"success": True, "message": "Invoice deleted and stock restored!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/sales/<int:order_id>/pdf', methods=['GET'])
@login_required
def api_sales_pdf(order_id):
    order = SalesOrderModel.get_by_id(order_id)
    if not order:
        return "Invoice not found", 404

    customer = ContactModel.get_by_id(order['customer_id'])
    items = order.get('items', [])
    company = CompanyModel.get_profile()

    try:
        pdf_path = generate_tax_invoice_pdf(order, customer, items, company=company)
        if not os.path.exists(pdf_path):
            return "Failed to generate PDF", 500

        download = request.args.get('download', '0') == '1'
        filename = f"Tax_Invoice_{order.get('invoice_number', 'bill')}.pdf"
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=download, download_name=filename)
    except Exception as ex:
        return f"Error creating PDF: {ex}", 500


# -------------------------------------------------------------
# Purchase Orders API
# -------------------------------------------------------------
@app.route('/api/purchases', methods=['GET'])
@login_required
def api_purchases_list():
    purchases = PurchaseOrderModel.get_all()
    return jsonify({"success": True, "purchases": purchases})

@app.route('/api/purchases/<int:po_id>', methods=['GET'])
@login_required
def api_purchase_get(po_id):
    po = PurchaseOrderModel.get_by_id(po_id)
    if not po:
        return jsonify({"success": False, "error": "Purchase order not found"}), 404
    return jsonify({"success": True, "purchase": po})

@app.route('/api/purchases', methods=['POST'])
@login_required
def api_purchase_create():
    data = request.get_json(force=True) or {}
    po_data = data.get('po', {})
    items = data.get('items', [])

    if not po_data.get('supplier_id'):
        return jsonify({"success": False, "error": "Supplier selection is required"}), 400

    try:
        new_id = PurchaseOrderModel.create(po_data, items)
        return jsonify({"success": True, "id": new_id, "message": "Purchase Order recorded!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/purchases/<int:po_id>/status', methods=['PUT'])
@login_required
def api_purchases_update_status(po_id):
    data = request.get_json(force=True) or {}
    status = data.get('status')
    payment_status = data.get('payment_status')

    try:
        PurchaseOrderModel.update_status(po_id, new_status=status, payment_status=payment_status)
        return jsonify({"success": True, "message": "Purchase order status updated!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/purchases/<int:po_id>/pdf', methods=['GET'])
@login_required
def api_purchase_pdf(po_id):
    po = PurchaseOrderModel.get_by_id(po_id)
    if not po:
        return "Purchase order not found", 404

    supplier = ContactModel.get_by_id(po['supplier_id'])
    items = po.get('items', [])
    company = CompanyModel.get_profile()

    try:
        pdf_path = generate_purchase_invoice_pdf(po, supplier, items, company=company)
        download = request.args.get('download', '0') == '1'
        filename = f"Purchase_PO_{po.get('po_number', 'PO')}.pdf"
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=download, download_name=filename)
    except Exception as ex:
        return f"Error creating PO PDF: {ex}", 500


# -------------------------------------------------------------
# Customer POs & Tracking API
# -------------------------------------------------------------
@app.route('/api/customer-pos', methods=['GET'])
@login_required
def api_customer_pos_list():
    pos = CustomerPOModel.get_all()
    return jsonify({"success": True, "customer_pos": pos})

@app.route('/api/customer-pos/<int:po_id>', methods=['GET'])
@login_required
def api_customer_po_get(po_id):
    po = CustomerPOModel.get_by_id(po_id)
    if not po:
        return jsonify({"success": False, "error": "Customer PO not found"}), 404
    return jsonify({"success": True, "customer_po": po})

@app.route('/api/customer-pos', methods=['POST'])
@login_required
def api_customer_po_create():
    data = request.get_json(force=True) or {}
    try:
        new_id = CustomerPOModel.create(data.get('po', {}), data.get('items', []))
        return jsonify({"success": True, "id": new_id, "message": "Customer PO registered!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


# -------------------------------------------------------------
# Payments & Ledger API
# -------------------------------------------------------------
@app.route('/api/payments', methods=['GET'])
@login_required
def api_payments_list():
    q = request.args.get('query', '')
    p_type = request.args.get('type', 'All')
    p_mode = request.args.get('mode', 'All')
    payments = PaymentModel.search(query=q, payment_type=p_type, payment_mode=p_mode)
    
    # Summary
    totals = db.fetch_one("""
        SELECT
            COALESCE(SUM(CASE WHEN payment_type = 'Payment In' THEN amount ELSE 0 END), 0.0) as total_in,
            COALESCE(SUM(CASE WHEN payment_type = 'Payment Out' THEN amount ELSE 0 END), 0.0) as total_out
        FROM payments
    """)

    return jsonify({
        "success": True,
        "payments": payments,
        "summary": {
            "total_in": float(totals['total_in'] or 0.0),
            "total_out": float(totals['total_out'] or 0.0)
        }
    })

@app.route('/api/payments', methods=['POST'])
@login_required
def api_payment_create():
    data = request.get_json(force=True) or {}
    if not data.get('contact_id') or not data.get('amount'):
        return jsonify({"success": False, "error": "Contact and Amount are required"}), 400
    try:
        new_id = PaymentModel.create(data)
        return jsonify({"success": True, "id": new_id, "message": "Payment recorded and ledger updated!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


# -------------------------------------------------------------
# Reports & Exports API
# -------------------------------------------------------------
@app.route('/api/reports/gstr1', methods=['GET'])
@login_required
def api_reports_gstr1():
    b2b_records = db.fetch_all("""
        SELECT so.invoice_number, so.invoice_date, c.name as customer_name, c.gstin as customer_gstin,
               c.place_of_supply, so.subtotal, so.cgst_amount, so.sgst_amount, so.igst_amount, so.total_amount
        FROM sales_orders so
        JOIN contacts c ON so.customer_id = c.id
        WHERE c.gstin IS NOT NULL AND c.gstin != '' AND so.status != 'Cancelled'
        ORDER BY so.id DESC
    """)

    b2c_records = db.fetch_all("""
        SELECT so.invoice_number, so.invoice_date, c.name as customer_name,
               c.place_of_supply, so.subtotal, so.cgst_amount, so.sgst_amount, so.igst_amount, so.total_amount
        FROM sales_orders so
        JOIN contacts c ON so.customer_id = c.id
        WHERE (c.gstin IS NULL OR c.gstin = '') AND so.status != 'Cancelled'
        ORDER BY so.id DESC
    """)

    totals = db.fetch_one("""
        SELECT 
            COALESCE(SUM(subtotal), 0) as total_taxable,
            COALESCE(SUM(cgst_amount), 0) as total_cgst,
            COALESCE(SUM(sgst_amount), 0) as total_sgst,
            COALESCE(SUM(igst_amount), 0) as total_igst,
            COALESCE(SUM(total_amount), 0) as total_invoice_value
        FROM sales_orders
        WHERE status != 'Cancelled'
    """)

    return jsonify({
        "success": True,
        "b2b": b2b_records,
        "b2c": b2c_records,
        "totals": {
            "taxable": float(totals['total_taxable']),
            "cgst": float(totals['total_cgst']),
            "sgst": float(totals['total_sgst']),
            "igst": float(totals['total_igst']),
            "grand_total": float(totals['total_invoice_value'])
        }
    })

@app.route('/api/reports/stock', methods=['GET'])
@login_required
def api_reports_stock():
    items = ItemModel.get_all()
    cat_summary = ReportModel.get_category_distribution()
    return jsonify({
        "success": True,
        "items": items,
        "category_summary": cat_summary
    })

@app.route('/api/reports/export-excel', methods=['GET'])
@login_required
def api_export_excel():
    report_type = request.args.get('type', 'sales')
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active

    if report_type == 'sales':
        ws.title = "Sales Invoices"
        ws.append(["Invoice No", "Date", "Customer", "GSTIN", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total (₹)", "Status"])
        orders = SalesOrderModel.get_all()
        for o in orders:
            ws.append([
                o.get('invoice_number'), o.get('invoice_date'), o.get('customer_name'),
                o.get('customer_gstin') or 'N/A', o.get('subtotal'), o.get('cgst_amount'),
                o.get('sgst_amount'), o.get('igst_amount'), o.get('total_amount'), o.get('payment_status')
            ])
        filename = f"Sales_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    elif report_type == 'stock':
        ws.title = "Inventory Valuation"
        ws.append(["SKU", "Item Name", "Category", "Subcategory", "Stock Qty", "Unit", "Cost Price", "Selling Price", "Valuation (₹)"])
        items = ItemModel.get_all()
        for i in items:
            val = float(i.get('current_stock', 0)) * float(i.get('cost_price', 0) or i.get('selling_price', 0))
            ws.append([
                i.get('sku'), i.get('name'), i.get('category'), i.get('subcategory'),
                i.get('current_stock'), i.get('unit'), i.get('cost_price'), i.get('selling_price'), round(val, 2)
            ])
        filename = f"Stock_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    else:
        ws.title = "Contacts"
        ws.append(["Party Name", "Company", "Type", "Phone", "Email", "GSTIN", "PAN", "Place of Supply", "Balance (₹)"])
        contacts = ContactModel.get_all()
        for c in contacts:
            ws.append([
                c.get('name'), c.get('company_name'), c.get('contact_type'),
                c.get('phone'), c.get('email'), c.get('gstin'), c.get('pan'),
                c.get('place_of_supply'), c.get('balance')
            ])
        filename = f"Contacts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    export_path = os.path.join(ROOT_DIR, 'exports', filename)
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    wb.save(export_path)
    return send_file(export_path, as_attachment=True, download_name=filename)


# -------------------------------------------------------------
# Company Profile API
# -------------------------------------------------------------
@app.route('/api/company', methods=['GET'])
@login_required
def api_company_get():
    profile = CompanyModel.get_profile()
    return jsonify({"success": True, "company": profile})

@app.route('/api/company', methods=['PUT'])
@admin_required
def api_company_update():
    data = request.get_json(force=True) or {}
    try:
        CompanyModel.update_profile(data)
        return jsonify({"success": True, "message": "Company Profile successfully updated!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


# -------------------------------------------------------------
# User Management API (Admin Only)
# -------------------------------------------------------------
@app.route('/api/users', methods=['GET'])
@admin_required
def api_users_list():
    users = UserModel.get_all()
    return jsonify({"success": True, "users": users})

@app.route('/api/users', methods=['POST'])
@admin_required
def api_users_create():
    data = request.get_json(force=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'User')

    if not username or not password:
        return jsonify({"success": False, "error": "Username & Password required"}), 400

    try:
        new_id = UserModel.create_user(username, password, full_name=full_name, role=role)
        return jsonify({"success": True, "id": new_id, "message": f"User '{username}' created successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_users_update(user_id):
    data = request.get_json(force=True) or {}
    password = data.get('password')
    try:
        UserModel.update_user(user_id, data, password=password)
        return jsonify({"success": True, "message": "User updated successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_users_delete(user_id):
    if user_id == session.get('user_id'):
        return jsonify({"success": False, "error": "You cannot delete your own active account!"}), 400
    try:
        UserModel.delete_user(user_id)
        return jsonify({"success": True, "message": "User deleted successfully!"})
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


# -------------------------------------------------------------
# Server Entrypoint
# -------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"============================================================")
    print(f"  N3RAH BOOK Web Application Server Running")
    print(f"  URL: http://127.0.0.1:{port}")
    print(f"  Backend: {'Cloud PostgreSQL' if db.cloud_mode else 'Local SQLite'}")
    print(f"============================================================")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
