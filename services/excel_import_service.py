"""
Excel & CSV Data Import Service
Parses Excel files (.xlsx, .xls, .csv) and imports Sales Invoices, Products, and Contacts into database.
"""

import os
import csv
from datetime import datetime
import openpyxl

from database.db_manager import db
from models.contact import ContactModel
from models.item import ItemModel
from models.sales_order import SalesOrderModel

def _clean_str(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ('none', 'null', 'nan') else s

def _to_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == '':
            return default
        # Clean currency symbols or commas
        s = str(val).replace('₹', '').replace(',', '').strip()
        return float(s)
    except (ValueError, TypeError):
        return default

class ExcelImportService:
    @staticmethod
    def read_sheet_data(file_path, max_rows=100):
        """Reads rows from Excel (.xlsx/.xls) or CSV file for preview."""
        ext = os.path.splitext(file_path)[1].lower()
        rows = []

        if ext == '.csv':
            with open(file_path, mode='r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.reader(f)
                for idx, row in enumerate(reader):
                    if idx >= max_rows:
                        break
                    rows.append([_clean_str(cell) for cell in row])
        else:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            for idx, row in enumerate(sheet.iter_rows(values_only=True)):
                if idx >= max_rows:
                    break
                rows.append([_clean_str(cell) for cell in row])

        return rows

    @staticmethod
    def import_products(file_path):
        """Imports products from Excel/CSV file."""
        rows = ExcelImportService.read_sheet_data(file_path, max_rows=5000)
        if not rows or len(rows) < 2:
            return {'success': False, 'message': 'Excel file is empty or missing headers.', 'count': 0}

        headers = [h.lower() for h in rows[0]]
        
        # Column mapping logic
        col_map = {
            'sku': next((i for i, h in enumerate(headers) if 'sku' in h or 'code' in h), None),
            'name': next((i for i, h in enumerate(headers) if 'name' in h or 'product' in h or 'item' in h), None),
            'category': next((i for i, h in enumerate(headers) if 'cat' in h), None),
            'hsn': next((i for i, h in enumerate(headers) if 'hsn' in h or 'sac' in h), None),
            'unit': next((i for i, h in enumerate(headers) if 'unit' in h or 'uom' in h), None),
            'cost': next((i for i, h in enumerate(headers) if 'cost' in h or 'buy' in h or 'purchase' in h), None),
            'price': next((i for i, h in enumerate(headers) if 'price' in h or 'sell' in h or 'rate' in h), None),
            'stock': next((i for i, h in enumerate(headers) if 'stock' in h or 'qty' in h or 'quantity' in h), None),
        }

        if col_map['name'] is None:
            # Fallback column order: Col 0 SKU, Col 1 Name
            col_map['sku'] = 0 if len(headers) > 0 else None
            col_map['name'] = 1 if len(headers) > 1 else 0

        imported = 0
        existing_items = {i['sku'].upper(): i for i in ItemModel.get_all()}
        
        for r in rows[1:]:
            if not any(r):
                continue
            
            name = _clean_str(r[col_map['name']]) if col_map['name'] is not None and col_map['name'] < len(r) else ""
            if not name:
                continue

            sku = _clean_str(r[col_map['sku']]) if col_map['sku'] is not None and col_map['sku'] < len(r) else f"SKU-{imported+101:03d}"

            item_data = {
                'sku': sku,
                'name': name,
                'category': _clean_str(r[col_map['category']]) if col_map['category'] is not None and col_map['category'] < len(r) else 'General',
                'hsn_code': _clean_str(r[col_map['hsn']]) if col_map['hsn'] is not None and col_map['hsn'] < len(r) else '39211310',
                'unit': _clean_str(r[col_map['unit']]) if col_map['unit'] is not None and col_map['unit'] < len(r) else 'PCS',
                'cost_price': _to_float(r[col_map['cost']]) if col_map['cost'] is not None and col_map['cost'] < len(r) else 0.0,
                'selling_price': _to_float(r[col_map['price']]) if col_map['price'] is not None and col_map['price'] < len(r) else 0.0,
                'current_stock': _to_float(r[col_map['stock']]) if col_map['stock'] is not None and col_map['stock'] < len(r) else 0.0,
                'reorder_level': 10.0,
                'tax_rate': 18.0
            }

            if sku.upper() in existing_items:
                ItemModel.update(existing_items[sku.upper()]['id'], item_data)
            else:
                ItemModel.create(item_data)
            
            imported += 1

        return {'success': True, 'count': imported, 'message': f'Successfully imported/updated {imported} products.'}

    @staticmethod
    def import_contacts(file_path):
        """Imports Customers/Suppliers from Excel/CSV file."""
        rows = ExcelImportService.read_sheet_data(file_path, max_rows=5000)
        if not rows or len(rows) < 2:
            return {'success': False, 'message': 'Excel file is empty or missing headers.', 'count': 0}

        headers = [h.lower() for h in rows[0]]
        col_map = {
            'name': next((i for i, h in enumerate(headers) if 'name' in h or 'party' in h or 'customer' in h), 0),
            'company': next((i for i, h in enumerate(headers) if 'company' in h or 'firm' in h), None),
            'type': next((i for i, h in enumerate(headers) if 'type' in h or 'role' in h), None),
            'gstin': next((i for i, h in enumerate(headers) if 'gst' in h), None),
            'phone': next((i for i, h in enumerate(headers) if 'phone' in h or 'mobile' in h or 'contact' in h), None),
            'email': next((i for i, h in enumerate(headers) if 'email' in h), None),
            'address': next((i for i, h in enumerate(headers) if 'address' in h or 'city' in h), None),
        }

        imported = 0
        existing_contacts = {c['name'].upper(): c for c in ContactModel.get_all()}

        for r in rows[1:]:
            if not any(r):
                continue

            name = _clean_str(r[col_map['name']]) if col_map['name'] < len(r) else ""
            if not name:
                continue

            contact_type = 'Customer'
            if col_map['type'] is not None and col_map['type'] < len(r):
                t_val = _clean_str(r[col_map['type']]).lower()
                if 'supplier' in t_val or 'vendor' in t_val:
                    contact_type = 'Supplier'

            contact_data = {
                'name': name,
                'company_name': _clean_str(r[col_map['company']]) if col_map['company'] is not None and col_map['company'] < len(r) else '',
                'contact_type': contact_type,
                'gstin': _clean_str(r[col_map['gstin']]) if col_map['gstin'] is not None and col_map['gstin'] < len(r) else '',
                'phone': _clean_str(r[col_map['phone']]) if col_map['phone'] is not None and col_map['phone'] < len(r) else '',
                'email': _clean_str(r[col_map['email']]) if col_map['email'] is not None and col_map['email'] < len(r) else '',
                'address': _clean_str(r[col_map['address']]) if col_map['address'] is not None and col_map['address'] < len(r) else '',
                'place_of_supply': 'Uttar Pradesh',
                'balance': 0.0,
                'status': 'Active'
            }

            if name.upper() in existing_contacts:
                ContactModel.update(existing_contacts[name.upper()]['id'], contact_data)
            else:
                ContactModel.create(contact_data)
            imported += 1

        return {'success': True, 'count': imported, 'message': f'Successfully imported {imported} contacts.'}

    @staticmethod
    def import_sales_invoices(file_path):
        """Imports Sales Invoices / GSTR-1 data from Excel/CSV file."""
        rows = ExcelImportService.read_sheet_data(file_path, max_rows=5000)
        if not rows or len(rows) < 2:
            return {'success': False, 'message': 'Excel file is empty or missing headers.', 'count': 0}

        headers = [h.lower() for h in rows[0]]

        # Flexible column header finder
        c_inv = next((i for i, h in enumerate(headers) if 'inv' in h or 'bill' in h or 'voucher' in h), 0)
        c_date = next((i for i, h in enumerate(headers) if 'date' in h), 1)
        c_party = next((i for i, h in enumerate(headers) if 'party' in h or 'customer' in h or 'name' in h), 2)
        c_gstin = next((i for i, h in enumerate(headers) if 'gst' in h), None)
        c_item = next((i for i, h in enumerate(headers) if 'item' in h or 'product' in h or 'particular' in h), None)
        c_hsn = next((i for i, h in enumerate(headers) if 'hsn' in h or 'sac' in h), None)
        c_qty = next((i for i, h in enumerate(headers) if 'qty' in h or 'quantity' in h or 'weight' in h), None)
        c_unit = next((i for i, h in enumerate(headers) if 'unit' in h or 'uom' in h), None)
        c_price = next((i for i, h in enumerate(headers) if 'rate' in h or 'price' in h), None)
        c_taxable = next((i for i, h in enumerate(headers) if 'taxable' in h or 'subtotal' in h or 'amount' in h), None)
        c_cgst = next((i for i, h in enumerate(headers) if 'cgst' in h), None)
        c_sgst = next((i for i, h in enumerate(headers) if 'sgst' in h), None)
        c_igst = next((i for i, h in enumerate(headers) if 'igst' in h), None)
        c_total = next((i for i, h in enumerate(headers) if 'total' in h or 'grand' in h or 'net' in h), None)

        # Cache existing contacts and items
        all_contacts = {c['name'].upper(): c for c in ContactModel.get_all()}
        all_items = {i['name'].upper(): i for i in ItemModel.get_all()}

        invoices_group = {}

        for r in rows[1:]:
            if not any(r):
                continue

            inv_no = _clean_str(r[c_inv]) if c_inv < len(r) else ""
            if not inv_no:
                continue

            inv_date = _clean_str(r[c_date]) if c_date < len(r) else datetime.now().strftime("%Y-%m-%d")
            # Parse date format if needed
            if '/' in inv_date:
                try:
                    parts = inv_date.split('/')
                    if len(parts) == 3:
                        if len(parts[2]) == 4:
                            inv_date = f"{parts[2]}-{int(parts[0]):02d}-{int(parts[1]):02d}"
                except Exception:
                    pass

            party_name = _clean_str(r[c_party]) if c_party < len(r) else "Cash Sale"
            if not party_name:
                party_name = "Cash Customer"

            # Auto-create party if not exists
            if party_name.upper() not in all_contacts:
                gstin = _clean_str(r[c_gstin]) if c_gstin is not None and c_gstin < len(r) else ""
                cid = ContactModel.create({
                    'name': party_name,
                    'contact_type': 'Customer',
                    'gstin': gstin,
                    'place_of_supply': 'Uttar Pradesh'
                })
                all_contacts[party_name.upper()] = {'id': cid, 'name': party_name}

            customer_id = all_contacts[party_name.upper()]['id']

            item_name = _clean_str(r[c_item]) if c_item is not None and c_item < len(r) else "General Goods"
            if not item_name:
                item_name = "General Goods"

            # Auto-create item if not exists
            if item_name.upper() not in all_items:
                hsn = _clean_str(r[c_hsn]) if c_hsn is not None and c_hsn < len(r) else "39211310"
                unit = _clean_str(r[c_unit]) if c_unit is not None and c_unit < len(r) else "PCS"
                price = _to_float(r[c_price]) if c_price is not None and c_price < len(r) else 100.0
                iid = ItemModel.create({
                    'sku': f"SKU-{len(all_items)+101:03d}",
                    'name': item_name,
                    'hsn_code': hsn,
                    'unit': unit,
                    'selling_price': price,
                    'current_stock': 100.0
                })
                all_items[item_name.upper()] = {'id': iid, 'name': item_name, 'hsn_code': hsn, 'unit': unit}

            item_id = all_items[item_name.upper()]['id']

            qty = _to_float(r[c_qty]) if c_qty is not None and c_qty < len(r) else 1.0
            if qty <= 0:
                qty = 1.0

            unit_price = _to_float(r[c_price]) if c_price is not None and c_price < len(r) else 0.0
            amt = _to_float(r[c_taxable]) if c_taxable is not None and c_taxable < len(r) else (qty * unit_price)
            if unit_price == 0.0 and qty > 0 and amt > 0:
                unit_price = amt / qty

            cgst = _to_float(r[c_cgst]) if c_cgst is not None and c_cgst < len(r) else (amt * 0.09)
            sgst = _to_float(r[c_sgst]) if c_sgst is not None and c_sgst < len(r) else (amt * 0.09)
            igst = _to_float(r[c_igst]) if c_igst is not None and c_igst < len(r) else 0.0

            tot = _to_float(r[c_total]) if c_total is not None and c_total < len(r) else (amt + cgst + sgst + igst)

            item_row = {
                'item_id': item_id,
                'item_name': item_name,
                'hsn_code': all_items[item_name.upper()].get('hsn_code', '39211310'),
                'quantity': qty,
                'unit': all_items[item_name.upper()].get('unit', 'PCS'),
                'unit_price': unit_price,
                'discount': 0.0,
                'amount': amt,
                'cgst_rate': 9.0,
                'sgst_rate': 9.0,
                'igst_rate': 0.0,
                'tax_amount': cgst + sgst + igst
            }

            if inv_no not in invoices_group:
                invoices_group[inv_no] = {
                    'invoice_number': inv_no,
                    'customer_id': customer_id,
                    'invoice_date': inv_date,
                    'due_date': inv_date,
                    'subtotal': 0.0,
                    'cgst_amount': 0.0,
                    'sgst_amount': 0.0,
                    'igst_amount': 0.0,
                    'total_amount': 0.0,
                    'status': 'Confirmed',
                    'items': []
                }

            invoices_group[inv_no]['subtotal'] += amt
            invoices_group[inv_no]['cgst_amount'] += cgst
            invoices_group[inv_no]['sgst_amount'] += sgst
            invoices_group[inv_no]['igst_amount'] += igst
            invoices_group[inv_no]['total_amount'] += tot
            invoices_group[inv_no]['items'].append(item_row)

        imported = 0
        skipped = 0

        for inv_no, inv_data in invoices_group.items():
            existing = SalesOrderModel.get_by_invoice_number(inv_no)
            if existing:
                skipped += 1
                continue
            
            items = inv_data.pop('items')
            SalesOrderModel.create(inv_data, items)
            imported += 1

        msg = f"Successfully imported {imported} Sales Invoices."
        if skipped > 0:
            msg += f" ({skipped} existing invoices were skipped)."

        return {'success': True, 'count': imported, 'message': msg}
