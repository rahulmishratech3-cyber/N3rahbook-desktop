"""
Customer PO Entry & Edit Dialog
Allows registering Party Purchase Orders, adding items in KG, unit prices, 9%+9% GST calculation, and target dates.
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONTS
from models.contact import ContactModel
from models.item import ItemModel
from models.customer_po import CustomerPOModel
from ui.components.data_table import DataTable
from services.num2words_service import number_to_words_indian

class CustomerPODialog(tk.Toplevel):
    def __init__(self, parent, po_data=None, on_save=None):
        super().__init__(parent)
        self.po_data = po_data or {}
        self.on_save = on_save
        self.title("✏️ Edit Party PO" if po_data else "➕ New Party Purchase Order (PO)")
        self.geometry("920x760")
        self.minsize(840, 660)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.items_list = []
        self._build_ui()
        self._load_existing_data()

    def _build_ui(self):
        # 1. Header
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x", side="top")

        title_txt = "✏️ Edit Party Purchase Order" if self.po_data else "📜 Register Party Purchase Order (Customer PO)"
        tk.Label(h_frame, text=title_txt, font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # 2. Bottom Footer Container (Totals + Action Buttons pinned to bottom so ALWAYS visible)
        footer_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=15, pady=4)
        footer_frame.pack(fill="x", side="bottom")

        # Calculation Summary Card (Bottom)
        tot_frame = tk.Frame(footer_frame, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=14, pady=6)
        tot_frame.pack(fill="x", pady=(0, 4))

        # Left Info
        tot_left = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        tot_left.pack(side="left", fill="both", expand=True)

        self.lbl_tot_kg = tk.Label(tot_left, text="Total Ordered: 0.00 KG", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["warning"])
        self.lbl_tot_kg.pack(anchor="w")

        self.words_lbl = tk.Label(tot_left, text="Total in Words: Zero Rupees Only", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"], anchor="w", wraplength=380, justify="left")
        self.words_lbl.pack(anchor="w", pady=(2, 0))

        # Right Breakdown
        tot_right = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        tot_right.pack(side="right")

        # Row: Taxable Subtotal
        r_sub = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_sub.pack(anchor="e", pady=1)
        tk.Label(r_sub, text="Taxable Subtotal: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_subtotal = tk.Label(r_sub, text="₹ 0.00", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=13, anchor="e")
        self.lbl_subtotal.pack(side="left")

        # Row: CGST (9%)
        r_cgst = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_cgst.pack(anchor="e", pady=1)
        tk.Label(r_cgst, text="CGST @ 9%: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_cgst = tk.Label(r_cgst, text="₹ 0.00", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=13, anchor="e")
        self.lbl_cgst.pack(side="left")

        # Row: SGST (9%)
        r_sgst = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_sgst.pack(anchor="e", pady=1)
        tk.Label(r_sgst, text="SGST @ 9%: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_sgst = tk.Label(r_sgst, text="₹ 0.00", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=13, anchor="e")
        self.lbl_sgst.pack(side="left")

        # Row: Total PO Amount (Grand Total)
        r_tot = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_tot.pack(anchor="e", pady=(2, 0))
        tk.Label(r_tot, text="Total PO Value (incl. GST): ", font=("Segoe UI", 11, "bold"), bg=COLORS["bg_card"], fg=COLORS["success"]).pack(side="left")
        self.lbl_grand_total = tk.Label(r_tot, text="₹ 0.00", font=("Segoe UI", 12, "bold"), bg=COLORS["bg_card"], fg=COLORS["success"], width=13, anchor="e")
        self.lbl_grand_total.pack(side="left")

        # Action Buttons
        btn_frame = tk.Frame(footer_frame, bg=COLORS["bg_dark"], pady=4)
        btn_frame.pack(fill="x")

        if self.po_data and 'id' in self.po_data:
            ttk.Button(btn_frame, text="📄 Export PDF", style="Secondary.TButton", command=self._export_current_pdf).pack(side="left", padx=4)

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="💾 Save Party PO", style="Secondary.TButton", command=lambda: self._save_po(open_pdf=False)).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="🖨️ Save & View PDF", style="Primary.TButton", command=lambda: self._save_po(open_pdf=True)).pack(side="right", padx=4)

        # 3. Main Form Area
        form_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=15, pady=4)
        form_frame.pack(fill="both", expand=True)

        # Top fields frame
        top_fields = tk.Frame(form_frame, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=14, pady=8)
        top_fields.pack(fill="x", pady=(0, 4))

        # Row 0: Customer & PO Reference
        tk.Label(top_fields, text="Party / Customer *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        cust_sub = tk.Frame(top_fields, bg=COLORS["bg_card"])
        cust_sub.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 2))

        self.customers = ContactModel.get_all()
        cust_names = []
        for c in self.customers:
            comp = str(c.get('company_name') or '').strip()
            name = str(c.get('name') or '').strip()
            addr = str(c.get('address') or '').strip()
            label = comp if comp else name
            if comp and name and comp.lower() != name.lower():
                label = f"{comp} ({name})"
            if addr and addr.lower() != 'n/a':
                label += f" — 📍 {addr}"
            cust_names.append(label)

        self.cust_combo = ttk.Combobox(cust_sub, values=cust_names, state="readonly", width=42)
        self.cust_combo.pack(side="left", padx=(0, 4))
        if cust_names:
            self.cust_combo.current(0)
        
        ttk.Button(cust_sub, text="➕ New", style="Secondary.TButton", command=self._quick_add_customer).pack(side="left")

        # Live Party Address Preview Label
        self.cust_addr_lbl = tk.Label(top_fields, text="", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["accent"], wraplength=380, justify="left")
        self.cust_addr_lbl.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 4))
        self.cust_combo.bind("<<ComboboxSelected>>", lambda e: self._on_customer_change())
        self._on_customer_change()

        tk.Label(top_fields, text="Customer PO Reference # *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.po_num_entry = ttk.Entry(top_fields, width=20)
        self.po_num_entry.insert(0, CustomerPOModel.generate_po_number())
        self.po_num_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 6))

        tk.Label(top_fields, text="GST Tax Applied *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.gst_mode_combo = ttk.Combobox(top_fields, values=["18% GST (9% CGST + 9% SGST)", "None (0% / Exempt)"], state="readonly", width=24)
        self.gst_mode_combo.current(0)
        self.gst_mode_combo.grid(row=1, column=2, sticky="w", padx=5, pady=(0, 6))
        self.gst_mode_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

        # Row 3: PO Date & Target Delivery Date
        today_str = datetime.now().strftime("%Y-%m-%d")
        tk.Label(top_fields, text="PO Date (YYYY-MM-DD) *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.po_date_entry = ttk.Entry(top_fields, width=20)
        self.po_date_entry.insert(0, today_str)
        self.po_date_entry.grid(row=4, column=0, sticky="w", padx=5, pady=(0, 4))

        tk.Label(top_fields, text="Target Delivery Date", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.target_date_entry = ttk.Entry(top_fields, width=20)
        self.target_date_entry.insert(0, today_str)
        self.target_date_entry.grid(row=4, column=1, sticky="w", padx=5, pady=(0, 4))

        tk.Label(top_fields, text="Notes / Delivery Terms", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=2, sticky="w", padx=5, pady=2)
        self.notes_entry = ttk.Entry(top_fields, width=26)
        self.notes_entry.grid(row=4, column=2, sticky="w", padx=5, pady=(0, 4))

        # 4. Line Items Entry Frame
        items_frame = tk.Frame(form_frame, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=10)
        items_frame.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(items_frame, text="📦 Order Items & Quantities (in KG / Units)", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", pady=(0, 6))

        # Item Selector Sub-Row
        sel_row = tk.Frame(items_frame, bg=COLORS["bg_card"])
        sel_row.pack(fill="x", pady=(0, 6))

        self.all_items = ItemModel.get_all()
        item_opts = [f"{i['sku']} - {i['name']} (Stock: {i['current_stock']} {i['unit']})" for i in self.all_items]

        tk.Label(sel_row, text="Product:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=3)
        self.item_combo = ttk.Combobox(sel_row, values=item_opts, state="readonly", width=25)
        self.item_combo.pack(side="left", padx=3)
        if item_opts:
            self.item_combo.current(0)
        self.item_combo.bind("<<ComboboxSelected>>", self._on_item_select)

        tk.Label(sel_row, text="Grade / Subcategory:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=3)
        subcats = ItemModel.get_subcategories("PU FOAM SHEETS")
        self.subcat_combo = ttk.Combobox(sel_row, values=subcats, width=16)
        self.subcat_combo.set("1ST GRADE")
        self.subcat_combo.pack(side="left", padx=3)

        tk.Label(sel_row, text="Qty (KG):", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=3)
        self.qty_entry = ttk.Entry(sel_row, width=8)
        self.qty_entry.insert(0, "50.0")
        self.qty_entry.pack(side="left", padx=3)

        tk.Label(sel_row, text="Rate (₹/KG):", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=3)
        self.rate_entry = ttk.Entry(sel_row, width=9)
        self.rate_entry.insert(0, "0.0")
        self.rate_entry.pack(side="left", padx=3)

        ttk.Button(sel_row, text="➕ Add Line Item", style="Primary.TButton", command=self._add_item_to_table).pack(side="left", padx=6)

        # Item Table
        cols = [
            ("sku", "SKU", 80, "center"),
            ("item_name", "Product Name", 180, "w"),
            ("subcategory", "Grade / Sub-Category", 140, "center"),
            ("ordered_qty_kg", "Ordered Qty (KG)", 110, "center"),
            ("unit_price", "Rate (₹/KG)", 95, "e"),
            ("total_amount", "Taxable Amount (₹)", 125, "e")
        ]
        self.item_table = DataTable(items_frame, cols)
        self.item_table.pack(fill="both", expand=True, pady=4)

        # Remove item bar
        rm_bar = tk.Frame(items_frame, bg=COLORS["bg_card"])
        rm_bar.pack(fill="x", pady=(2, 0))
        ttk.Button(rm_bar, text="🗑️ Remove Selected Item", style="Secondary.TButton", command=self._remove_selected_item).pack(side="left")



    def _on_item_select(self, event=None):
        idx = self.item_combo.current()
        if idx >= 0 and idx < len(self.all_items):
            item = self.all_items[idx]
            self.rate_entry.delete(0, tk.END)
            self.rate_entry.insert(0, str(item.get('selling_price', 0.0)))
            if item.get('subcategory'):
                self.subcat_combo.set(item['subcategory'])

    def _add_item_to_table(self):
        idx = self.item_combo.current()
        if idx < 0:
            messagebox.showwarning("Warning", "Please select a product to add.", parent=self)
            return

        try:
            qty = float(self.qty_entry.get().strip())
            rate = float(self.rate_entry.get().strip())
            if qty <= 0:
                raise ValueError("Quantity must be greater than 0.")
        except ValueError as ex:
            messagebox.showerror("Invalid Input", f"Please enter valid numeric quantity and rate: {str(ex)}", parent=self)
            return

        item = self.all_items[idx]
        total_amt = qty * rate
        subcat = self.subcat_combo.get().strip() or '1ST GRADE'

        # Check if already added
        for existing in self.items_list:
            if existing['item_id'] == item['id'] and existing.get('subcategory', '') == subcat:
                existing['ordered_qty_kg'] += qty
                existing['total_amount'] = existing['ordered_qty_kg'] * existing['unit_price']
                self._refresh_table()
                return

        row = {
            'item_id': item['id'],
            'sku': item['sku'],
            'item_name': item['name'],
            'subcategory': subcat,
            'hsn_code': item.get('hsn_code', '00000000'),
            'ordered_qty_kg': qty,
            'dispatched_qty_kg': 0.0,
            'unit': item.get('unit', 'KGS'),
            'unit_price': rate,
            'total_amount': total_amt
        }
        self.items_list.append(row)
        self._refresh_table()

    def _remove_selected_item(self):
        selected = self.item_table.get_selected_item()
        if not selected:
            messagebox.showwarning("Warning", "Select an item row from the table to remove.", parent=self)
            return

        self.items_list = [i for i in self.items_list if not (i['item_id'] == selected['item_id'] and i.get('subcategory') == selected.get('subcategory'))]
        self._refresh_table()

    def _refresh_table(self):
        formatted = []
        tot_kg = 0.0
        subtotal = 0.0

        for i in self.items_list:
            tot_kg += i['ordered_qty_kg']
            subtotal += i['total_amount']
            formatted.append({
                'item_id': i['item_id'],
                'sku': i.get('sku', ''),
                'item_name': i['item_name'],
                'subcategory': i.get('subcategory', '1ST GRADE'),
                'ordered_qty_kg': f"{i['ordered_qty_kg']:,.2f} {i.get('unit', 'KG')}",
                'unit_price': f"₹ {i['unit_price']:,.2f}",
                'total_amount': f"₹ {i['total_amount']:,.2f}"
            })

        self.item_table.load_data(formatted)

        gst_mode = self.gst_mode_combo.get() if hasattr(self, 'gst_mode_combo') else "18% GST (9% CGST + 9% SGST)"
        if "18%" in gst_mode or "9%" in gst_mode:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            grand_tot = round(subtotal + cgst + sgst)
        else:
            cgst = 0.0
            sgst = 0.0
            grand_tot = round(subtotal)

        self.lbl_tot_kg.config(text=f"Total Ordered: {tot_kg:,.2f} KG")
        self.lbl_subtotal.config(text=f"₹ {subtotal:,.2f}")
        self.lbl_cgst.config(text=f"₹ {cgst:,.2f}")
        self.lbl_sgst.config(text=f"₹ {sgst:,.2f}")
        self.lbl_grand_total.config(text=f"₹ {grand_tot:,.2f}")

        words = number_to_words_indian(grand_tot)
        self.words_lbl.config(text=f"Total in Words: {words}")

    def _load_existing_data(self):
        if not self.po_data:
            return

        # Select Customer
        cust_id = self.po_data.get('customer_id')
        for idx, c in enumerate(self.customers):
            if str(c['id']) == str(cust_id):
                self.cust_combo.current(idx)
                break

        self.po_num_entry.delete(0, tk.END)
        self.po_num_entry.insert(0, self.po_data.get('po_number', ''))

        self.po_date_entry.delete(0, tk.END)
        self.po_date_entry.insert(0, self.po_data.get('po_date', ''))

        self.target_date_entry.delete(0, tk.END)
        self.target_date_entry.insert(0, self.po_data.get('target_delivery_date', ''))

        self.notes_entry.delete(0, tk.END)
        self.notes_entry.insert(0, self.po_data.get('notes', ''))

        gst_r = float(self.po_data.get('gst_rate', 18.0) or 18.0)
        if gst_r <= 0:
            self.gst_mode_combo.set("None (0% / Exempt)")
        else:
            self.gst_mode_combo.set("18% GST (9% CGST + 9% SGST)")

        # Load items
        raw_items = self.po_data.get('items', [])
        for item in raw_items:
            sku = ''
            for it in self.all_items:
                if str(it['id']) == str(item['item_id']):
                    sku = it['sku']
                    break

            self.items_list.append({
                'item_id': item['item_id'],
                'sku': sku,
                'item_name': item['item_name'],
                'subcategory': item.get('subcategory', '1ST GRADE'),
                'hsn_code': item.get('hsn_code', '00000000'),
                'ordered_qty_kg': float(item['ordered_qty_kg']),
                'dispatched_qty_kg': float(item.get('dispatched_qty_kg', 0.0)),
                'unit': item.get('unit', 'KGS'),
                'unit_price': float(item['unit_price']),
                'total_amount': float(item['total_amount'])
            })

        self._refresh_table()

    def _save_po(self, open_pdf=False):
        cust_idx = self.cust_combo.current()
        if cust_idx < 0:
            messagebox.showerror("Error", "Please select a Party / Customer.", parent=self)
            return

        po_num = self.po_num_entry.get().strip()
        po_date = self.po_date_entry.get().strip()
        if not po_num or not po_date:
            messagebox.showerror("Error", "PO Reference # and PO Date are required.", parent=self)
            return

        if not self.items_list:
            messagebox.showerror("Error", "Please add at least one line item to the Party PO.", parent=self)
            return

        subtotal = sum(float(i['total_amount']) for i in self.items_list)
        gst_mode = self.gst_mode_combo.get() if hasattr(self, 'gst_mode_combo') else "18% GST (9% CGST + 9% SGST)"
        if "18%" in gst_mode or "9%" in gst_mode:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            grand_tot = round(subtotal + cgst + sgst)
            gst_rate = 18.0
        else:
            cgst = 0.0
            sgst = 0.0
            grand_tot = round(subtotal)
            gst_rate = 0.0

        customer = self.customers[cust_idx]
        po_header = {
            'customer_id': customer['id'],
            'po_number': po_num,
            'po_date': po_date,
            'target_delivery_date': self.target_date_entry.get().strip(),
            'subtotal': subtotal,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'gst_rate': gst_rate,
            'total_po_amount': grand_tot,
            'notes': self.notes_entry.get().strip()
        }

        try:
            if self.po_data and 'id' in self.po_data:
                CustomerPOModel.update(self.po_data['id'], po_header, self.items_list)
                saved_id = self.po_data['id']
            else:
                saved_id = CustomerPOModel.create(po_header, self.items_list)

            if open_pdf:
                self._export_pdf_for_data(po_header, customer, self.items_list)

            if self.on_save:
                self.on_save()

            messagebox.showinfo("Success", f"Party PO '{po_num}' saved successfully!", parent=self)
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Save Error", f"Failed to save Party PO: {str(ex)}", parent=self)

    def _export_current_pdf(self):
        cust_idx = self.cust_combo.current()
        if cust_idx < 0:
            messagebox.showerror("Error", "Customer information missing!", parent=self)
            return

        po_num = self.po_num_entry.get().strip()
        po_date = self.po_date_entry.get().strip()
        subtotal = sum(float(i['total_amount']) for i in self.items_list)
        gst_mode = self.gst_mode_combo.get() if hasattr(self, 'gst_mode_combo') else "18% GST (9% CGST + 9% SGST)"
        if "18%" in gst_mode or "9%" in gst_mode:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            grand_tot = round(subtotal + cgst + sgst)
            gst_rate = 18.0
        else:
            cgst = 0.0
            sgst = 0.0
            grand_tot = round(subtotal)
            gst_rate = 0.0

        customer = self.customers[cust_idx]
        po_header = {
            'customer_id': customer['id'],
            'po_number': po_num,
            'po_date': po_date,
            'target_delivery_date': self.target_date_entry.get().strip(),
            'subtotal': subtotal,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'gst_rate': gst_rate,
            'total_po_amount': grand_tot,
            'notes': self.notes_entry.get().strip(),
            'status': self.po_data.get('status', 'Open')
        }
        self._export_pdf_for_data(po_header, customer, self.items_list)

    def _export_pdf_for_data(self, po_header, customer, items):
        import os
        import subprocess
        from services.pdf_service import generate_customer_po_pdf
        try:
            pdf_path = generate_customer_po_pdf(
                po=po_header,
                customer=customer,
                items=items,
                page_size="A4"
            )
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path])
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to generate Party PO PDF: {str(ex)}", parent=self)

    def _on_customer_change(self):
        if not hasattr(self, 'cust_addr_lbl') or not self.customers:
            return
        idx = self.cust_combo.current()
        if 0 <= idx < len(self.customers):
            c = self.customers[idx]
            addr = str(c.get('address') or 'N/A').strip()
            gstin = str(c.get('gstin') or 'N/A').strip()
            phone = str(c.get('phone') or '').strip()
            txt = f"📍 Address: {addr}"
            if gstin and gstin != 'N/A':
                txt += f"  |  GSTIN: {gstin}"
            if phone:
                txt += f"  |  Mob: {phone}"
            self.cust_addr_lbl.config(text=txt)

    def _quick_add_customer(self):
        from ui.components.dialogs import ContactDialog
        ContactDialog(self, contact_data={'contact_type': 'Customer'}, on_save=self._on_customer_created)

    def _on_customer_created(self, new_id=None):
        self.customers = ContactModel.get_all()
        cust_names = []
        for c in self.customers:
            comp = str(c.get('company_name') or '').strip()
            name = str(c.get('name') or '').strip()
            addr = str(c.get('address') or '').strip()
            label = comp if comp else name
            if comp and name and comp.lower() != name.lower():
                label = f"{comp} ({name})"
            if addr and addr.lower() != 'n/a':
                label += f" — 📍 {addr}"
            cust_names.append(label)

        self.cust_combo['values'] = cust_names

        if new_id:
            for idx, c in enumerate(self.customers):
                if c['id'] == new_id:
                    self.cust_combo.current(idx)
                    break
        elif cust_names:
            self.cust_combo.current(len(cust_names) - 1)
        self._on_customer_change()

    def _load_existing_data(self):
        if not self.po_data or not self.po_data.get('id'):
            return

        po = CustomerPOModel.get_by_id(self.po_data['id'])
        if not po:
            return

        self.title(f"✏️ Edit Party Purchase Order - {po.get('po_number', '')}")

        # Set Customer in combo
        cust_id = po.get('customer_id')
        for idx, c in enumerate(self.customers):
            if str(c['id']) == str(cust_id):
                self.cust_combo.current(idx)
                break
        self._on_customer_change()

        self.po_num_entry.delete(0, tk.END)
        self.po_num_entry.insert(0, po.get('po_number', ''))

        self.po_date_entry.delete(0, tk.END)
        self.po_date_entry.insert(0, po.get('po_date', ''))

        self.target_date_entry.delete(0, tk.END)
        self.target_date_entry.insert(0, po.get('target_delivery_date', ''))

        self.notes_entry.delete(0, tk.END)
        self.notes_entry.insert(0, po.get('notes', ''))

        gst_rate = float(po.get('gst_rate', 18.0) or 0.0)
        if gst_rate > 0:
            self.gst_mode_combo.set("18% GST (9% CGST + 9% SGST)")
        else:
            self.gst_mode_combo.set("None (0% / Exempt)")

        # Load Items into self.items_list
        self.items_list = []
        for item in po.get('items', []):
            qty = float(item.get('ordered_qty_kg') or item.get('quantity') or 0.0)
            rate = float(item.get('unit_price') or 0.0)
            amt = float(item.get('total_amount') or (qty * rate))
            self.items_list.append({
                'item_id': item.get('item_id'),
                'sku': item.get('sku', 'SKU-001'),
                'item_name': item.get('item_name', ''),
                'subcategory': item.get('subcategory', '1ST GRADE'),
                'ordered_qty_kg': qty,
                'unit': item.get('unit', 'KG'),
                'unit_price': rate,
                'total_amount': amt
            })

        self._refresh_table()
