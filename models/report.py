"""
Report and Analytics Data Model
Provides aggregated stats for Dashboard KPI cards, Matplotlib charts, and Reports.
"""

from database.db_manager import db

class ReportModel:
    @staticmethod
    def get_kpi_summary():
        # Total Stock Value (uses Cost Price, fallback to latest purchase cost, then selling price)
        stock_val_row = db.fetch_one("""
            SELECT SUM(current_stock * COALESCE(
                NULLIF(cost_price, 0),
                (SELECT poi.unit_cost FROM purchase_order_items poi WHERE poi.item_id = items.id AND poi.unit_cost > 0 ORDER BY poi.id DESC LIMIT 1),
                NULLIF(selling_price, 0),
                (SELECT soi.unit_price FROM sales_order_items soi WHERE soi.item_id = items.id AND soi.unit_price > 0 ORDER BY soi.id DESC LIMIT 1),
                0.0
            )) as total_val 
            FROM items
        """)
        total_stock_value = stock_val_row['total_val'] or 0.0

        # Low Stock Count
        low_stock_row = db.fetch_one("SELECT COUNT(*) as cnt FROM items WHERE current_stock <= reorder_level")
        low_stock_count = low_stock_row['cnt'] or 0

        # Monthly Sales Revenue
        sales_rev_row = db.fetch_one("SELECT SUM(total_amount) as rev FROM sales_orders WHERE status != 'Cancelled'")
        monthly_revenue = sales_rev_row['rev'] or 0.0

        # Pending Orders Count
        pending_row = db.fetch_one("SELECT COUNT(*) as cnt FROM sales_orders WHERE status IN ('Draft', 'Confirmed')")
        pending_orders = pending_row['cnt'] or 0

        return {
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            'monthly_revenue': monthly_revenue,
            'pending_orders': pending_orders
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
