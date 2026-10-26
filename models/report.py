"""
Report and Analytics Data Model
Provides aggregated stats for Dashboard KPI cards, Matplotlib charts, and Reports.
"""

from database.db_manager import db

class ReportModel:
    @staticmethod
    def get_low_stock_count():
        try:
            row = db.fetch_one("SELECT COUNT(*) as cnt FROM items WHERE current_stock <= reorder_level")
            return row['cnt'] if row and row.get('cnt') else 0
        except Exception:
            return 0

    @staticmethod
    def get_kpi_summary():
        try:
            res = db.fetch_one("""
                SELECT 
                    (SELECT COALESCE(SUM(current_stock * COALESCE(
                        NULLIF(cost_price, 0),
                        (SELECT poi.unit_cost FROM purchase_order_items poi WHERE poi.item_id = items.id AND poi.unit_cost > 0 ORDER BY poi.id DESC LIMIT 1),
                        NULLIF(selling_price, 0),
                        0.0
                    )), 0.0) FROM items) as total_stock_value,
                    (SELECT COUNT(*) FROM items WHERE current_stock <= reorder_level) as low_stock_count,
                    (SELECT COALESCE(SUM(total_amount), 0.0) FROM sales_orders WHERE status != 'Cancelled') as monthly_revenue,
                    (SELECT COUNT(*) FROM sales_orders WHERE status IN ('Draft', 'Confirmed')) as pending_orders
            """)
            if res:
                return {
                    'total_stock_value': float(res.get('total_stock_value') or 0.0),
                    'low_stock_count': int(res.get('low_stock_count') or 0),
                    'monthly_revenue': float(res.get('monthly_revenue') or 0.0),
                    'pending_orders': int(res.get('pending_orders') or 0)
                }
        except Exception as ex:
            print("KPI Summary query error:", ex)

        return {
            'total_stock_value': 0.0,
            'low_stock_count': 0,
            'monthly_revenue': 0.0,
            'pending_orders': 0
        }

    @staticmethod
    def get_category_distribution():
        sql = """
        SELECT category, SUM(current_stock) as stock_qty, 
               SUM(current_stock * COALESCE(
                   NULLIF(cost_price, 0),
                   (SELECT poi.unit_cost FROM purchase_order_items poi WHERE poi.item_id = items.id AND poi.unit_cost > 0 ORDER BY poi.id DESC LIMIT 1),
                   NULLIF(selling_price, 0),
                   0.0
               )) as category_value
        FROM items
        GROUP BY category
        ORDER BY stock_qty DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_recent_sales_trend():
        sql = """
        SELECT invoice_date, SUM(total_amount) as daily_sales
        FROM sales_orders
        WHERE status != 'Cancelled'
        GROUP BY invoice_date
        ORDER BY invoice_date ASC
        LIMIT 7
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_hsn_tax_report():
        sql = """
        SELECT hsn_code,
               SUM(amount) as taxable_value,
               SUM(amount * (cgst_rate / 100.0)) as cgst_amount,
               SUM(amount * (sgst_rate / 100.0)) as sgst_amount,
               SUM(amount * ((cgst_rate + sgst_rate) / 100.0)) as total_tax
        FROM sales_order_items
        GROUP BY hsn_code
        ORDER BY taxable_value DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_stock_movement_report():
        sql = """
        SELECT 
            i.id as item_id,
            i.sku,
            i.name as item_name,
            i.category,
            i.unit,
            i.current_stock,
            i.reorder_level,
            COALESCE(SUM(CASE WHEN sa.adjustment_type = 'Add' THEN sa.quantity ELSE 0 END), 0) as total_inwards,
            COALESCE(SUM(CASE WHEN sa.adjustment_type = 'Remove' THEN sa.quantity ELSE 0 END), 0) as total_outwards,
            COUNT(sa.id) as total_transactions
        FROM items i
        LEFT JOIN stock_adjustments sa ON i.id = sa.item_id
        GROUP BY i.id
        ORDER BY i.name ASC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_sales_invoice_report():
        sql = """
        SELECT 
            so.id,
            so.invoice_number,
            so.invoice_date,
            c.name as customer_name,
            c.company_name,
            so.subtotal,
            so.freight,
            (so.cgst_amount + so.sgst_amount) as tax_amount,
            so.total_amount,
            COALESCE(so.payment_status, so.status) as payment_status,
            so.status
        FROM sales_orders so
        JOIN contacts c ON so.customer_id = c.id
        ORDER BY so.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_gstr1_report(month=None, year=None):
        """
        Returns itemized GSTR-1 Sales Report data including:
        S.No, Description of Product, HSN CODE, Quantity, Assessable Value,
        CGST, SGST, IGST, Roundoff, Invoice No, Invoice Date, and E-Way Bill Number.
        """
        sql = """
        SELECT 
            so.id as sales_order_id,
            so.invoice_number,
            so.invoice_date,
            COALESCE(NULLIF(so.eway_bill_no, ''), 'N/A') as eway_bill_no,
            c.name as customer_name,
            c.company_name,
            c.gstin as customer_gstin,
            soi.item_name,
            COALESCE(NULLIF(soi.hsn_code, ''), '39211310') as hsn_code,
            soi.quantity,
            soi.unit,
            soi.unit_price,
            soi.amount as assessable_value,
            ROUND(CAST(soi.amount * (COALESCE(soi.cgst_rate, 9.0) / 100.0) AS NUMERIC), 2) as cgst_amount,
            ROUND(CAST(soi.amount * (COALESCE(soi.sgst_rate, 9.0) / 100.0) AS NUMERIC), 2) as sgst_amount,
            ROUND(CAST(soi.amount * (COALESCE(soi.igst_rate, 0.0) / 100.0) AS NUMERIC), 2) as igst_amount,
            COALESCE(so.round_off, 0.0) as round_off,
            so.total_amount
        FROM sales_order_items soi
        JOIN sales_orders so ON soi.sales_order_id = so.id
        JOIN contacts c ON so.customer_id = c.id
        WHERE so.status != 'Cancelled'
        """ + (f" AND so.invoice_date LIKE '%/{month}/{year}'" if month and year else (f" AND so.invoice_date LIKE '%/%/{year}'" if year else "")) + """
        ORDER BY so.id DESC, soi.id ASC
        """
        rows = db.fetch_all(sql)

        # Check for any invoices with freight charges and add freight rows under SAC 9965
        freight_orders = db.fetch_all("""
            SELECT so.id as sales_order_id, so.invoice_number, so.invoice_date,
                   COALESCE(NULLIF(so.eway_bill_no, ''), 'N/A') as eway_bill_no,
                   c.name as customer_name, c.company_name, c.gstin as customer_gstin,
                   so.freight, so.round_off, so.total_amount, so.igst_amount
            FROM sales_orders so
            JOIN contacts c ON so.customer_id = c.id
            WHERE so.status != 'Cancelled' AND so.freight > 0
            """ + (f" AND so.invoice_date LIKE '%/{month}/{year}'" if month and year else (f" AND so.invoice_date LIKE '%/%/{year}'" if year else "")) + """
            ORDER BY so.id DESC
        """)

        if freight_orders:
            for fo in freight_orders:
                fr_val = float(fo['freight'])
                is_igst = float(fo.get('igst_amount', 0.0) or 0.0) > 0
                rows.append({
                    'sales_order_id': fo['sales_order_id'],
                    'invoice_number': fo['invoice_number'],
                    'invoice_date': fo['invoice_date'],
                    'eway_bill_no': fo['eway_bill_no'],
                    'customer_name': fo['customer_name'],
                    'company_name': fo['company_name'],
                    'customer_gstin': fo['customer_gstin'],
                    'item_name': 'Freight / Transport Charges',
                    'hsn_code': '9965',
                    'quantity': 1.0,
                    'unit': 'LS',
                    'unit_price': fr_val,
                    'assessable_value': fr_val,
                    'cgst_amount': 0.0 if is_igst else round(fr_val * 0.09, 2),
                    'sgst_amount': 0.0 if is_igst else round(fr_val * 0.09, 2),
                    'igst_amount': round(fr_val * 0.18, 2) if is_igst else 0.0,
                    'round_off': fo['round_off'],
                    'total_amount': fo['total_amount']
                })

        return rows

    @staticmethod
    def get_gstr2_purchase_report(month=None, year=None):
        """
        Returns itemized GSTR-2 Purchase / Inward Supplies Report data including:
        S.No, Description of Product, HSN CODE, Quantity, Unit Cost, Assessable Value,
        CGST, SGST, IGST, Roundoff, Invoice / PO No, Invoice Date, Supplier Name, GSTIN, and Total Amount.
        """
        sql = """
        SELECT 
            po.id as purchase_order_id,
            po.po_number as invoice_number,
            po.order_date as invoice_date,
            c.name as supplier_name,
            c.company_name,
            COALESCE(NULLIF(c.gstin, ''), 'N/A') as supplier_gstin,
            poi.item_name,
            COALESCE(NULLIF(poi.subcategory, ''), '') as subcategory,
            COALESCE(NULLIF(poi.hsn_code, ''), '39211310') as hsn_code,
            poi.quantity,
            poi.unit,
            poi.unit_cost as unit_price,
            poi.total_cost as assessable_value,
            CASE 
                WHEN po.cgst_amount > 0 THEN ROUND(CAST(poi.total_cost * 0.09 AS NUMERIC), 2)
                ELSE 0.0
            END as cgst_amount,
            CASE 
                WHEN po.sgst_amount > 0 THEN ROUND(CAST(poi.total_cost * 0.09 AS NUMERIC), 2)
                ELSE 0.0
            END as sgst_amount,
            CASE 
                WHEN po.igst_amount > 0 THEN ROUND(CAST(poi.total_cost * 0.18 AS NUMERIC), 2)
                ELSE 0.0
            END as igst_amount,
            COALESCE(po.round_off, 0.0) as round_off,
            po.total_amount,
            po.status
        FROM purchase_order_items poi
        JOIN purchase_orders po ON poi.purchase_order_id = po.id
        JOIN contacts c ON po.supplier_id = c.id
        WHERE po.status != 'Cancelled'
        """ + (f" AND po.order_date LIKE '%/{month}/{year}'" if month and year else (f" AND po.order_date LIKE '%/%/{year}'" if year else "")) + """
        ORDER BY po.id DESC, poi.id ASC
        """
        rows = db.fetch_all(sql)

        # Check for any purchase orders with freight charges and add freight rows under SAC 9965
        freight_pos = db.fetch_all("""
            SELECT po.id as purchase_order_id, po.po_number as invoice_number, po.order_date as invoice_date,
                   c.name as supplier_name, c.company_name, COALESCE(NULLIF(c.gstin, ''), 'N/A') as supplier_gstin,
                   po.freight, po.round_off, po.total_amount, po.igst_amount, po.status
            FROM purchase_orders po
            JOIN contacts c ON po.supplier_id = c.id
            WHERE po.status != 'Cancelled' AND po.freight > 0
            """ + (f" AND po.order_date LIKE '%/{month}/{year}'" if month and year else (f" AND po.order_date LIKE '%/%/{year}'" if year else "")) + """
            ORDER BY po.id DESC
        """)

        if freight_pos:
            for fo in freight_pos:
                fr_val = float(fo['freight'])
                is_igst = float(fo.get('igst_amount', 0.0) or 0.0) > 0
                rows.append({
                    'purchase_order_id': fo['purchase_order_id'],
                    'invoice_number': fo['invoice_number'],
                    'invoice_date': fo['invoice_date'],
                    'supplier_name': fo['supplier_name'],
                    'company_name': fo['company_name'],
                    'supplier_gstin': fo['supplier_gstin'],
                    'item_name': 'Freight / Transport Charges',
                    'subcategory': '',
                    'hsn_code': '9965',
                    'quantity': 1.0,
                    'unit': 'LS',
                    'unit_price': fr_val,
                    'assessable_value': fr_val,
                    'cgst_amount': 0.0 if is_igst else round(fr_val * 0.09, 2),
                    'sgst_amount': 0.0 if is_igst else round(fr_val * 0.09, 2),
                    'igst_amount': round(fr_val * 0.18, 2) if is_igst else 0.0,
                    'round_off': fo.get('round_off', 0.0) or 0.0,
                    'total_amount': fo['total_amount'],
                    'status': fo['status']
                })

        return rows

    @staticmethod
    def get_purchase_invoice_report():
        """
        Returns purchase bills and replenishment orders summary.
        """
        sql = """
        SELECT 
            po.id,
            po.po_number,
            po.order_date,
            po.expected_date,
            c.name as supplier_name,
            c.company_name,
            COALESCE(NULLIF(c.gstin, ''), 'N/A') as supplier_gstin,
            po.subtotal,
            po.freight,
            po.cgst_amount,
            po.sgst_amount,
            po.igst_amount,
            (COALESCE(po.cgst_amount, 0.0) + COALESCE(po.sgst_amount, 0.0) + COALESCE(po.igst_amount, 0.0)) as tax_amount,
            po.total_amount,
            po.status
        FROM purchase_orders po
        JOIN contacts c ON po.supplier_id = c.id
        ORDER BY po.id DESC
        """
        return db.fetch_all(sql)

    @staticmethod
    def get_gstr3b_summary(month=None, year=None):
        """
        Computes GSTR-3B Tax Comparison:
        - Outward Supplies (Sales) Output Tax
        - Eligible ITC (Purchases) Input Tax Credit
        - Net GST Tax Payable
        """
        sales = db.fetch_one("""
            SELECT 
                COALESCE(SUM(subtotal + freight), 0.0) as total_taxable,
                COALESCE(SUM(cgst_amount), 0.0) as total_cgst,
                COALESCE(SUM(sgst_amount), 0.0) as total_sgst,
                COALESCE(SUM(igst_amount), 0.0) as total_igst,
                COALESCE(SUM(total_amount), 0.0) as total_gross
            FROM sales_orders
            WHERE status != 'Cancelled'
            """ + (f" AND invoice_date LIKE '%/{month}/{year}'" if month and year else (f" AND invoice_date LIKE '%/%/{year}'" if year else ""))) or {'total_taxable': 0.0, 'total_cgst': 0.0, 'total_sgst': 0.0, 'total_igst': 0.0, 'total_gross': 0.0}

        purchases = db.fetch_one("""
            SELECT 
                COALESCE(SUM(subtotal + freight), 0.0) as total_taxable,
                COALESCE(SUM(cgst_amount), 0.0) as total_cgst,
                COALESCE(SUM(sgst_amount), 0.0) as total_sgst,
                COALESCE(SUM(igst_amount), 0.0) as total_igst,
                COALESCE(SUM(total_amount), 0.0) as total_gross
            FROM purchase_orders
            WHERE status != 'Cancelled'
            """ + (f" AND order_date LIKE '%/{month}/{year}'" if month and year else (f" AND order_date LIKE '%/%/{year}'" if year else ""))) or {'total_taxable': 0.0, 'total_cgst': 0.0, 'total_sgst': 0.0, 'total_igst': 0.0, 'total_gross': 0.0}

        sales_tax = float(sales.get('total_cgst', 0.0)) + float(sales.get('total_sgst', 0.0)) + float(sales.get('total_igst', 0.0))
        pur_tax = float(purchases.get('total_cgst', 0.0)) + float(purchases.get('total_sgst', 0.0)) + float(purchases.get('total_igst', 0.0))
        net_cgst = float(sales.get('total_cgst', 0.0)) - float(purchases.get('total_cgst', 0.0))
        net_sgst = float(sales.get('total_sgst', 0.0)) - float(purchases.get('total_sgst', 0.0))
        net_igst = float(sales.get('total_igst', 0.0)) - float(purchases.get('total_igst', 0.0))
        net_tax = sales_tax - pur_tax

        return {
            'sales': sales,
            'purchases': purchases,
            'sales_tax': sales_tax,
            'purchase_itc': pur_tax,
            'net_cgst': net_cgst,
            'net_sgst': net_sgst,
            'net_igst': net_igst,
            'net_tax': net_tax
        }


