"""
Database Schema Definitions
"""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'Admin',
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    barcode TEXT,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'PU FOAM SHEETS',
    subcategory TEXT DEFAULT 'Standard',
    brand TEXT DEFAULT 'Generic',
    hsn_code TEXT DEFAULT '00000000',
    unit TEXT DEFAULT 'PCS',
    cost_price REAL DEFAULT 0.0,
    selling_price REAL DEFAULT 0.0,
    current_stock REAL DEFAULT 0.0,
    reorder_level REAL DEFAULT 10.0,
    tax_rate REAL DEFAULT 18.0,
    location TEXT DEFAULT 'Warehouse A',
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company_name TEXT,
    contact_type TEXT CHECK(contact_type IN ('Customer', 'Supplier')) NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    gstin TEXT,
    pan TEXT,
    place_of_supply TEXT DEFAULT 'Uttar Pradesh',
    balance REAL DEFAULT 0.0,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    adjustment_type TEXT CHECK(adjustment_type IN ('Add', 'Remove')) NOT NULL,
    quantity REAL NOT NULL,
    reason TEXT DEFAULT 'Audit',
    adjusted_by TEXT DEFAULT 'Admin',
    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    invoice_date TEXT NOT NULL,
    due_date TEXT,
    po_number TEXT,
    po_date TEXT,
    vehicle_no TEXT,
    eway_bill_no TEXT,
    fiscal_year TEXT DEFAULT '2026-2027',
    place_of_supply TEXT DEFAULT 'Uttar Pradesh',
    status TEXT CHECK(status IN ('Draft', 'Confirmed', 'Shipped', 'Paid', 'Cancelled')) DEFAULT 'Paid',
    payment_status TEXT DEFAULT 'Paid',
    subtotal REAL DEFAULT 0.0,
    freight REAL DEFAULT 0.0,
    cgst_amount REAL DEFAULT 0.0,
    sgst_amount REAL DEFAULT 0.0,
    igst_amount REAL DEFAULT 0.0,
    round_off REAL DEFAULT 0.0,
    total_amount REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES contacts (id)
);

CREATE TABLE IF NOT EXISTS sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    hsn_code TEXT,
    quantity REAL NOT NULL,
    unit TEXT DEFAULT 'PCS',
    unit_price REAL NOT NULL,
    discount REAL DEFAULT 0.0,
    amount REAL NOT NULL,
    cgst_rate REAL DEFAULT 9.0,
    sgst_rate REAL DEFAULT 9.0,
    igst_rate REAL DEFAULT 0.0,
    tax_amount REAL DEFAULT 0.0,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders (id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items (id)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    expected_date TEXT,
    status TEXT CHECK(status IN ('Draft', 'Issued', 'Received', 'Cancelled')) DEFAULT 'Draft',
    subtotal REAL DEFAULT 0.0,
    freight REAL DEFAULT 0.0,
    cgst_amount REAL DEFAULT 0.0,
    sgst_amount REAL DEFAULT 0.0,
    igst_amount REAL DEFAULT 0.0,
    round_off REAL DEFAULT 0.0,
    total_amount REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES contacts (id)
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    hsn_code TEXT,
    quantity REAL NOT NULL,
    unit TEXT DEFAULT 'PCS',
    unit_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items (id)
);

CREATE TABLE IF NOT EXISTS company_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    gstin TEXT,
    pan TEXT,
    mobile TEXT,
    email TEXT,
    udyam_reg_no TEXT DEFAULT 'UDYAM-UP-18-0048627',
    bank_name TEXT,
    bank_branch TEXT,
    account_no TEXT,
    ifsc_code TEXT,
    terms TEXT,
    current_fiscal_year TEXT DEFAULT '2026-2027',
    gmail_address TEXT DEFAULT '',
    gmail_app_password TEXT DEFAULT '',
    gmail_filter_keywords TEXT DEFAULT 'PO, Purchase Order, Order, CPO'
);

CREATE TABLE IF NOT EXISTS processed_email_pos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE,
    sender TEXT,
    subject TEXT,
    received_date TEXT,
    pdf_filename TEXT,
    po_number TEXT,
    customer_id INTEGER,
    status TEXT DEFAULT 'Imported',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fiscal_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_label TEXT UNIQUE NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('Active', 'Closed')) DEFAULT 'Active',
    total_sales REAL DEFAULT 0.0,
    total_purchases REAL DEFAULT 0.0,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_number TEXT UNIQUE NOT NULL,
    contact_id INTEGER NOT NULL,
    payment_type TEXT CHECK(payment_type IN ('Payment In', 'Payment Out')) NOT NULL,
    payment_mode TEXT CHECK(payment_mode IN ('Cash', 'UPI', 'Bank Transfer', 'Cheque', 'Card', 'Net Banking', 'Other')) DEFAULT 'Cash',
    amount REAL NOT NULL DEFAULT 0.0,
    payment_date TEXT NOT NULL,
    reference_no TEXT,
    sales_order_id INTEGER,
    purchase_order_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts (id),
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders (id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id)
);

CREATE TABLE IF NOT EXISTS customer_pos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    po_date TEXT NOT NULL,
    target_delivery_date TEXT,
    total_ordered_qty_kg REAL DEFAULT 0.0,
    total_dispatched_qty_kg REAL DEFAULT 0.0,
    total_po_amount REAL DEFAULT 0.0,
    total_dispatched_amount REAL DEFAULT 0.0,
    status TEXT CHECK(status IN ('Open', 'Partially Dispatched', 'Completed', 'Cancelled')) DEFAULT 'Open',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES contacts (id)
);

CREATE TABLE IF NOT EXISTS customer_po_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_po_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    hsn_code TEXT,
    ordered_qty_kg REAL NOT NULL DEFAULT 0.0,
    dispatched_qty_kg REAL NOT NULL DEFAULT 0.0,
    unit TEXT DEFAULT 'KGS',
    unit_price REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (customer_po_id) REFERENCES customer_pos (id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items (id)
);

CREATE TABLE IF NOT EXISTS customer_po_dispatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_po_id INTEGER NOT NULL,
    dispatch_date TEXT NOT NULL,
    invoice_number TEXT,
    dispatched_qty_kg REAL NOT NULL DEFAULT 0.0,
    dispatched_amount REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_po_id) REFERENCES customer_pos (id) ON DELETE CASCADE
);
"""


