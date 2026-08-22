"""
Company Profile Model
Stores business profile, GSTIN, Bank details, and Invoice Terms in SQLite database.
"""

from database.db_manager import db
from config import COMPANY_PROFILE

class CompanyModel:
    @staticmethod
    def get_profile():
        profile = db.fetch_one("SELECT * FROM company_profile WHERE id = 1")
        if not profile:
            CompanyModel.update_profile(COMPANY_PROFILE)
            profile = db.fetch_one("SELECT * FROM company_profile WHERE id = 1")
        
        # Format terms as list if string
        if profile and isinstance(profile.get('terms'), str):
            terms_raw = profile['terms'].strip()
            profile['terms'] = [t.strip() for t in terms_raw.split('\n') if t.strip()] if terms_raw else []

        return profile or COMPANY_PROFILE

    @staticmethod
    def update_profile(data):
        existing = db.fetch_one("SELECT id FROM company_profile WHERE id = 1")
        terms_str = data.get('terms', '')
        if isinstance(terms_str, list):
            terms_str = "\n".join(terms_str)

        udyam_val = data.get('udyam_reg_no', 'UDYAM-UP-18-0048627') or 'UDYAM-UP-18-0048627'

        if existing:
            sql = """
            UPDATE company_profile SET
                name = ?, address = ?, gstin = ?, pan = ?, mobile = ?, email = ?, udyam_reg_no = ?,
                bank_name = ?, bank_branch = ?, account_no = ?, ifsc_code = ?, terms = ?,
                current_fiscal_year = COALESCE(?, current_fiscal_year, '2026-2027')
            WHERE id = 1
            """
            db.execute_query(sql, (
                data.get('name', ''), data.get('address', ''), data.get('gstin', ''),
                data.get('pan', ''), data.get('mobile', ''), data.get('email', ''), udyam_val,
                data.get('bank_name', ''), data.get('bank_branch', ''),
                data.get('account_no', ''), data.get('ifsc_code', ''), terms_str,
                data.get('current_fiscal_year')
            ))
        else:
            sql = """
            INSERT INTO company_profile (
                id, name, address, gstin, pan, mobile, email, udyam_reg_no,
                bank_name, bank_branch, account_no, ifsc_code, terms, current_fiscal_year
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute_query(sql, (
                data.get('name', ''), data.get('address', ''), data.get('gstin', ''),
                data.get('pan', ''), data.get('mobile', ''), data.get('email', ''), udyam_val,
                data.get('bank_name', ''), data.get('bank_branch', ''),
                data.get('account_no', ''), data.get('ifsc_code', ''), terms_str,
                data.get('current_fiscal_year', '2026-2027')
            ))
