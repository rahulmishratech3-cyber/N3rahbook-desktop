"""
Fiscal Year Management Model
Handles active fiscal year tracking, financial summaries, closing fiscal years, and initializing new fiscal years.
"""

from datetime import datetime
from database.db_manager import db
from models.company import CompanyModel


class FiscalYearModel:
    @staticmethod
    def get_active_year():
        """
        Retrieves the currently active fiscal year record.
        If no active record exists, initializes default FY 2026-2027.
        """
        active_fy = db.fetch_one("SELECT * FROM fiscal_years WHERE status = 'Active' ORDER BY id DESC LIMIT 1")
        if not active_fy:
            # Check company profile
            profile = CompanyModel.get_profile()
            fy_label = profile.get('current_fiscal_year', '2026-2027')
            
            start_yr = fy_label.split('-')[0] if '-' in fy_label else '2026'
            end_yr = fy_label.split('-')[1] if '-' in fy_label else '2027'
            if len(end_yr) == 2:
                end_yr = f"20{end_yr}"

            db.execute_query("""
            INSERT OR IGNORE INTO fiscal_years (year_label, start_date, end_date, status)
            VALUES (?, ?, ?, 'Active')
            """, (fy_label, f"01/04/{start_yr}", f"31/03/{end_yr}"))

            active_fy = db.fetch_one("SELECT * FROM fiscal_years WHERE status = 'Active' ORDER BY id DESC LIMIT 1")

        return active_fy or {
            'id': 1,
            'year_label': '2026-2027',
            'start_date': '01/04/2026',
            'end_date': '31/03/2027',
            'status': 'Active'
        }

    @staticmethod
    def get_all():
        """
        Retrieves all fiscal years (both active and closed).
        """
        # Ensure active year initialized
        FiscalYearModel.get_active_year()
        return db.fetch_all("SELECT * FROM fiscal_years ORDER BY id DESC")

    @staticmethod
    def get_closing_summary():
        """
        Calculates financial summary metrics for closing the current fiscal year.
        """
        active_fy = FiscalYearModel.get_active_year()
        fy_label = active_fy.get('year_label', '2026-2027')

        # Total Sales Revenue
        sales_row = db.fetch_one("""
        SELECT SUM(total_amount) as total_sales, COUNT(*) as sales_count
        FROM sales_orders
        WHERE status != 'Cancelled' AND (fiscal_year = ? OR fiscal_year IS NULL OR fiscal_year = '')
        """, (fy_label,))

        # Total Purchase Cost
        pur_row = db.fetch_one("""
        SELECT SUM(total_amount) as total_purchases, COUNT(*) as pur_count
        FROM purchase_orders
        WHERE status != 'Cancelled'
        """)

        # Inventory Value
        inv_row = db.fetch_one("SELECT SUM(current_stock * cost_price) as stock_val, COUNT(*) as item_cnt FROM items")

        return {
            'active_fy': active_fy,
            'total_sales': sales_row['total_sales'] or 0.0 if sales_row else 0.0,
            'sales_count': sales_row['sales_count'] or 0 if sales_row else 0,
            'total_purchases': pur_row['total_purchases'] or 0.0 if pur_row else 0.0,
            'pur_count': pur_row['pur_count'] or 0 if pur_row else 0,
            'stock_value': inv_row['stock_val'] or 0.0 if inv_row else 0.0,
            'item_count': inv_row['item_cnt'] or 0 if inv_row else 0
        }

    @staticmethod
    def close_and_start_new(next_year_label, start_date=None, end_date=None):
        """
        Closes current active fiscal year and initializes a new active fiscal year.
        """
        active_fy = FiscalYearModel.get_active_year()
        summary = FiscalYearModel.get_closing_summary()

        tot_sales = summary['total_sales']
        tot_pur = summary['total_purchases']

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Mark current FY as closed
            cursor.execute("""
            UPDATE fiscal_years SET
                status = 'Closed',
                closed_at = CURRENT_TIMESTAMP,
                total_sales = ?,
                total_purchases = ?
            WHERE id = ?
            """, (tot_sales, tot_pur, active_fy['id']))

            # Default dates for next FY if not provided
            if not start_date or not end_date:
                parts = next_year_label.split('-')
                start_yr = parts[0] if len(parts) > 0 else '2027'
                end_yr = parts[1] if len(parts) > 1 else '2028'
                if len(end_yr) == 2:
                    end_yr = f"20{end_yr}"
                start_date = f"01/04/{start_yr}"
                end_date = f"31/03/{end_yr}"

            # Insert new active fiscal year
            cursor.execute("""
            INSERT OR REPLACE INTO fiscal_years (year_label, start_date, end_date, status)
            VALUES (?, ?, ?, 'Active')
            """, (next_year_label, start_date, end_date))

            # Update company profile
            cursor.execute("UPDATE company_profile SET current_fiscal_year = ? WHERE id = 1", (next_year_label,))

            conn.commit()

        return True
