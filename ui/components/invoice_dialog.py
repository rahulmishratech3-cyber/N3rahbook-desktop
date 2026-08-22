"""
Full Tax Invoice Creation and A4/Letter PDF Print Preview Dialog
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS, COMPANY_PROFILE
from models.item import ItemModel
from models.contact import ContactModel
from models.sales_order import SalesOrderModel
from services.pdf_service import generate_tax_invoice_pdf
from services.num2words_service import number_to_words_indian

class InvoiceDialog(tk.Toplevel):
    def __init__(self, parent, order_id=None, on_save=None):
        super().__init__(parent)
        self.title("GST Tax Invoice Creator & Print Preview")
        self.geometry("1100x780")
        self.minsize(1020, 700)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.order_id = order_id
        self.on_save = on_save
        self.customers = ContactModel.get_all("Customer")
        self.items_list = ItemModel.get_all()

        self.line_items = [] # list of dicts

        self._build_ui()
        if self.order_id:
            self._load_existing_order()
        else:
            self._add_line_item_row()

    def _build_ui(self):
        # 1. Header Toolbar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x")

        tk.Label(h_frame, text="📄 GST Tax Invoice Creator", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(side="left")

        # Format & Copy selector
        format_frame = tk.Frame(h_frame, bg=COLORS["bg_header"])
        format_frame.pack(side="right")

        tk.Label(format_frame, text="Paper Size:", font=FONTS["small"], bg=COLORS["bg_header"], fg=COLORS["text_muted"]).pack(side="left", padx=2)
        self.page_size_combo = ttk.Combobox(format_frame, values=["A4", "LETTER"], state="readonly", width=8)
        self.page_size_combo.current(0) # Default A4
        self.page_size_combo.pack(side="left", padx=5)

        tk.Label(format_frame, text="Copy:", font=FONTS["small"], bg=COLORS["bg_header"], fg=COLORS["text_muted"]).pack(side="left", padx=2)
        self.copy_combo = ttk.Combobox(format_frame, values=["ORIGINAL FOR RECIPIENT", "DUPLICATE FOR TRANSPORTER", "TRIPLICATE FOR SUPPLIER"], state="readonly", width=24)
        self.copy_combo.current(0)
        self.copy_combo.pack(side="left", padx=5)

        # 2. Main Scrollable Canvas Container
        container = tk.Frame(self, bg=COLORS["bg_dark"], padx=15, pady=10)
        container.pack(fill="both", expand=True)

        # Form Metadata Header
        meta_box = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        meta_box.pack(fill="x", pady=5)

        # Row 1: Invoice No, Customer, Date, Due Date, Vehicle No, E-Way Bill No
        f_r1 = tk.Frame(meta_box, bg=COLORS["bg_card"])
        f_r1.pack(fill="x", pady=4)

        from datetime import datetime, timedelta
        today_str = datetime.now().strftime("%d/%m/%Y")
        due_str = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

        tk.Label(f_r1, text="Invoice No *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=6)
        self.inv_num_entry = ttk.Entry(f_r1, width=18)
        next_id = (len(SalesOrderModel.get_all()) + 1)
        self.inv_num_entry.insert(0, f"INV-{datetime.now().year}-{next_id:03d}")
        self.inv_num_entry.grid(row=1, column=0, sticky="w", padx=6, pady=2)

        tk.Label(f_r1, text="Select Customer *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=6)
        
        cust_sub = tk.Frame(f_r1, bg=COLORS["bg_card"])
        cust_sub.grid(row=1, column=1, sticky="w", padx=6, pady=2)

        cust_labels = [f"{c['name']} ({c.get('gstin', 'No GSTIN')})" for c in self.customers]
        self.cust_combo = ttk.Combobox(cust_sub, values=cust_labels, state="readonly", width=32)
        if cust_labels:
            self.cust_combo.current(0)
        self.cust_combo.pack(side="left", padx=(0, 6))

        ttk.Button(cust_sub, text="➕ New Customer", style="Secondary.TButton", command=self._quick_add_customer).pack(side="left")

        tk.Label(f_r1, text="Invoice Date", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=2, sticky="w", padx=6)
        self.inv_date_entry = ttk.Entry(f_r1, width=14)
        self.inv_date_entry.insert(0, today_str)
        self.inv_date_entry.grid(row=1, column=2, sticky="w", padx=6, pady=2)

        tk.Label(f_r1, text="Due Date", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=3, sticky="w", padx=6)
        self.due_date_entry = ttk.Entry(f_r1, width=14)
        self.due_date_entry.insert(0, due_str)
        self.due_date_entry.grid(row=1, column=3, sticky="w", padx=6, pady=2)

        tk.Label(f_r1, text="Vehicle No.", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=4, sticky="w", padx=6)
        self.veh_entry = ttk.Entry(f_r1, width=15)
        self.veh_entry.grid(row=1, column=4, sticky="w", padx=6, pady=2)

        tk.Label(f_r1, text="E-Way Bill No.", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=5, sticky="w", padx=6)
        self.eway_entry = ttk.Entry(f_r1, width=15)
        self.eway_entry.grid(row=1, column=5, sticky="w", padx=6, pady=2)

        tk.Label(f_r1, text="Payment Status *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=6, sticky="w", padx=6)
        self.status_combo = ttk.Combobox(f_r1, values=["Paid", "Unpaid", "Cancelled"], state="readonly", width=11)
        self.status_combo.current(0)
        self.status_combo.grid(row=1, column=6, sticky="w", padx=6, pady=2)

        # 3. Items Line Grid Header & Scroll Container
        items_frame = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=10)
        items_frame.pack(fill="both", expand=True, pady=10)

        grid_title_frame = tk.Frame(items_frame, bg=COLORS["bg_card"])
        grid_title_frame.pack(fill="x", pady=(0, 6))
        
        tk.Label(grid_title_frame, text="📦 Invoice Items & Tax Particulars", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")
        ttk.Button(grid_title_frame, text="➕ Add Item Row", style="Secondary.TButton", command=self._add_line_item_row).pack(side="right")

        # Scrollable Line Items Frame
        canvas = tk.Canvas(items_frame, bg=COLORS["bg_card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=canvas.yview)
        
        self.items_grid = tk.Frame(canvas, bg=COLORS["bg_card"])

        self.items_grid.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.items_grid, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, pady=2)
        scrollbar.pack(side="right", fill="y", pady=2)

        # Configure columns on items_grid
        self.items_grid.columnconfigure(0, weight=6, minsize=260)  # Product Description
        self.items_grid.columnconfigure(1, weight=2, minsize=90)   # HSN / SAC
        self.items_grid.columnconfigure(2, weight=1, minsize=75)   # Quantity
        self.items_grid.columnconfigure(3, weight=1, minsize=65)   # Unit
        self.items_grid.columnconfigure(4, weight=2, minsize=90)   # Rate
        self.items_grid.columnconfigure(5, weight=2, minsize=110)  # Amount
        self.items_grid.columnconfigure(6, weight=0, minsize=45)   # Action

        # Row 0: Table Header Bar
        tk.Label(self.items_grid, text="Item / Product Description", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="w", padx=8, pady=6).grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="HSN / SAC", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="center", padx=4, pady=6).grid(row=0, column=1, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="Quantity", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="center", padx=4, pady=6).grid(row=0, column=2, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="Unit", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="center", padx=4, pady=6).grid(row=0, column=3, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="Rate / Price (₹)", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="e", padx=8, pady=6).grid(row=0, column=4, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="Taxable Amount (₹)", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="e", padx=8, pady=6).grid(row=0, column=5, sticky="ew", padx=2, pady=(0, 4))
        tk.Label(self.items_grid, text="Action", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor="center", padx=2, pady=6).grid(row=0, column=6, sticky="ew", padx=2, pady=(0, 4))

        # 4. Footer Totals & Words Frame
        tot_frame = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        tot_frame.pack(fill="x", pady=5)

        left_tot = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        left_tot.pack(side="left", fill="both", expand=True)

        self.words_lbl = tk.Label(left_tot, text="Total in Words: Zero Rupees Only", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"], wraplength=550, justify="left")
        self.words_lbl.pack(anchor="w", pady=(0, 6))

        tk.Label(left_tot, text="* GST @ 18% (9% CGST + 9% SGST) applied to all taxable items & freight.", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

        right_tot = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        right_tot.pack(side="right")

        # Items Subtotal
        self.subtot_var = tk.StringVar(value="Items Subtotal: ₹ 0.00")
        tk.Label(right_tot, textvariable=self.subtot_var, font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, columnspan=2, sticky="e", pady=1)

        # Fare / Freight Row
        tk.Label(right_tot, text="🚚 Freight / Fare (₹):", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).grid(row=1, column=0, sticky="e", padx=(0, 6), pady=2)
        self.freight_entry = ttk.Entry(right_tot, width=12, justify="right")
        self.freight_entry.insert(0, "0.00")
        self.freight_entry.grid(row=1, column=1, sticky="e", pady=2)
        self.freight_entry.bind("<KeyRelease>", lambda e: self._recalculate_totals())

        # Tax
        self.tax_var = tk.StringVar(value="GST Tax (9%+9%): ₹ 0.00")
        tk.Label(right_tot, textvariable=self.tax_var, font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=2, column=0, columnspan=2, sticky="e", pady=1)

        # Grand Total
        self.grand_tot_var = tk.StringVar(value="Grand Total: ₹ 0.00")
        tk.Label(right_tot, textvariable=self.grand_tot_var, font=("Segoe UI", 14, "bold"), bg=COLORS["bg_card"], fg=COLORS["success"]).grid(row=3, column=0, columnspan=2, sticky="e", pady=(2, 0))

        # 5. Bottom Action Buttons
        btn_bar = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_bar.pack(fill="x", side="bottom")

        ttk.Button(btn_bar, text="Close", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_bar, text="🖨️ Export / Print PDF Invoice", style="Success.TButton", command=self._export_pdf).pack(side="right", padx=5)
        ttk.Button(btn_bar, text="💾 Save Invoice Record", style="Primary.TButton", command=self._save_invoice).pack(side="right", padx=5)

        if self.order_id:
            ttk.Button(btn_bar, text="🗑️ Delete Invoice", style="Secondary.TButton", command=self._delete_invoice).pack(side="left", padx=5)
            ttk.Button(btn_bar, text="🚫 Cancel Invoice", style="Secondary.TButton", command=self._cancel_invoice).pack(side="left", padx=5)

    def _delete_invoice(self):
        if not self.order_id:
            return
        inv_num = self.inv_num_entry.get().strip() or "this invoice"
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete Invoice #{inv_num}?\n\nThis action will remove the record and restore product stock levels.",
            parent=self
        )
        if confirm:
            try:
                SalesOrderModel.delete(self.order_id)
                if self.on_save:
                    self.on_save()
                messagebox.showinfo("Success", f"Invoice #{inv_num} deleted successfully!", parent=self)
                self.destroy()
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete invoice: {str(ex)}", parent=self)

    def _cancel_invoice(self):
        if not self.order_id:
            return
        inv_num = self.inv_num_entry.get().strip() or "this invoice"
        confirm = messagebox.askyesno(
            "Confirm Cancel",
            f"Are you sure you want to mark Invoice #{inv_num} as CANCELLED?\n\nThis action will revert deducted product stock levels back to inventory.",
            parent=self
        )
        if confirm:
            try:
                SalesOrderModel.update_status(self.order_id, 'Cancelled')
                self.status_combo.set('Cancelled')
                if self.on_save:
                    self.on_save()
                messagebox.showinfo("Success", f"Invoice #{inv_num} marked as Cancelled and inventory stock restored!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to cancel invoice: {str(ex)}", parent=self)

    def _add_line_item_row(self, initial_val=None):
        row_idx = len(self.line_items) + 1

        # Product Selector
        item_names = [f"{i['sku']} - {i['name']}" + (f" [{i['subcategory']}]" if i.get('subcategory') else "") for i in self.items_list]
        combo_item = ttk.Combobox(self.items_grid, values=item_names, state="readonly")
        combo_item.grid(row=row_idx, column=0, sticky="ew", padx=2, pady=2)

        # HSN
        entry_hsn = ttk.Entry(self.items_grid, justify="center")
        entry_hsn.insert(0, "39211310")
        entry_hsn.grid(row=row_idx, column=1, sticky="ew", padx=2, pady=2)

        # Qty
        entry_qty = ttk.Entry(self.items_grid, justify="center")
        entry_qty.insert(0, "1.0")
        entry_qty.grid(row=row_idx, column=2, sticky="ew", padx=2, pady=2)

        # Unit
        entry_unit = ttk.Entry(self.items_grid, justify="center")
        entry_unit.insert(0, "PCS")
        entry_unit.grid(row=row_idx, column=3, sticky="ew", padx=2, pady=2)

        # Rate
        entry_rate = ttk.Entry(self.items_grid, justify="right")
        entry_rate.insert(0, "0.00")
        entry_rate.grid(row=row_idx, column=4, sticky="ew", padx=2, pady=2)

        # Amount Label
        lbl_amt = tk.Label(self.items_grid, text="₹ 0.00", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_light"], anchor="e", padx=6, pady=4)
        lbl_amt.grid(row=row_idx, column=5, sticky="ew", padx=2, pady=2)

        # Remove Button
        btn_del = tk.Button(self.items_grid, text="❌", font=FONTS["small"], bg=COLORS["bg_card_alt"], fg=COLORS["danger"], bd=0, cursor="hand2")
        btn_del.grid(row=row_idx, column=6, sticky="ew", padx=2, pady=2)

        row_dict = {
            'combo_item': combo_item,
            'entry_hsn': entry_hsn,
            'entry_qty': entry_qty,
            'entry_unit': entry_unit,
            'entry_rate': entry_rate,
            'lbl_amt': lbl_amt,
            'btn_del': btn_del
        }

        btn_del.config(command=lambda r=row_dict: self._remove_line_item_row(r))

        combo_item.bind("<<ComboboxSelected>>", lambda e, r=row_dict: self._on_item_selected(r))
        entry_qty.bind("<KeyRelease>", lambda e: self._recalculate_totals())
        entry_rate.bind("<KeyRelease>", lambda e: self._recalculate_totals())

        self.line_items.append(row_dict)
        self._recalculate_totals()

    def _remove_line_item_row(self, row_dict):
        if len(self.line_items) <= 1:
            messagebox.showwarning("Warning", "At least one line item is required in the invoice!", parent=self)
            return
        row_dict['combo_item'].destroy()
        row_dict['entry_hsn'].destroy()
        row_dict['entry_qty'].destroy()
        row_dict['entry_unit'].destroy()
        row_dict['entry_rate'].destroy()
        row_dict['lbl_amt'].destroy()
        row_dict['btn_del'].destroy()
        self.line_items.remove(row_dict)

        # Re-grid remaining rows consecutively
        for idx, r in enumerate(self.line_items, start=1):
            r['combo_item'].grid(row=idx, column=0)
            r['entry_hsn'].grid(row=idx, column=1)
            r['entry_qty'].grid(row=idx, column=2)
            r['entry_unit'].grid(row=idx, column=3)
            r['entry_rate'].grid(row=idx, column=4)
            r['lbl_amt'].grid(row=idx, column=5)
            r['btn_del'].grid(row=idx, column=6)

        self._recalculate_totals()

    def _on_item_selected(self, row_dict):
        idx = row_dict['combo_item'].current()
        if idx >= 0 and idx < len(self.items_list):
            item = self.items_list[idx]
            row_dict['entry_hsn'].delete(0, tk.END)
            row_dict['entry_hsn'].insert(0, item.get('hsn_code', '00000000'))

            row_dict['entry_unit'].delete(0, tk.END)
            row_dict['entry_unit'].insert(0, item.get('unit', 'PCS'))

            row_dict['entry_rate'].delete(0, tk.END)
            row_dict['entry_rate'].insert(0, f"{item.get('selling_price', 0.0):.2f}")

            self._recalculate_totals()

    def _recalculate_totals(self):
        subtotal = 0.0
        for r in self.line_items:
            try:
                qty = float(r['entry_qty'].get().strip() or 0)
                rate = float(r['entry_rate'].get().strip() or 0)
                amt = qty * rate
                subtotal += amt
                r['lbl_amt'].config(text=f"₹ {amt:,.2f}")
            except ValueError:
                r['lbl_amt'].config(text="₹ 0.00")

        try:
            freight = float(self.freight_entry.get().strip() or 0)
        except ValueError:
            freight = 0.0

        taxable_total = subtotal + freight
        cgst_sum = taxable_total * 0.09
        sgst_sum = taxable_total * 0.09
        raw_total = taxable_total + cgst_sum + sgst_sum
        grand_total = round(raw_total)
        round_off = grand_total - raw_total

        self.subtot_var.set(f"Items Subtotal: ₹ {subtotal:,.2f}")
        self.tax_var.set(f"GST Tax (9%+9%): ₹ {(cgst_sum + sgst_sum):,.2f}")
        self.grand_tot_var.set(f"Grand Total: ₹ {grand_total:,.2f}")

        words = number_to_words_indian(grand_total)
        self.words_lbl.config(text=f"Total in Words: {words}")

    def _load_existing_order(self):
        order = SalesOrderModel.get_by_id(self.order_id)
        if not order:
            return

        self.inv_num_entry.delete(0, tk.END)
        self.inv_num_entry.insert(0, order['invoice_number'])

        self.inv_date_entry.delete(0, tk.END)
        self.inv_date_entry.insert(0, order['invoice_date'])

        self.due_date_entry.delete(0, tk.END)
        self.due_date_entry.insert(0, order.get('due_date', ''))

        self.veh_entry.delete(0, tk.END)
        self.veh_entry.insert(0, order.get('vehicle_no', ''))

        self.eway_entry.delete(0, tk.END)
        self.eway_entry.insert(0, order.get('eway_bill_no', ''))

        self.freight_entry.delete(0, tk.END)
        self.freight_entry.insert(0, f"{order.get('freight', 0.0):.2f}")

        # Set Payment Status
        pay_st = str(order.get('payment_status') or '').strip()
        st = str(order.get('status') or '').strip()
        if st.lower() == 'cancelled' or pay_st.lower() == 'cancelled':
            self.status_combo.set('Cancelled')
        elif pay_st.lower() == 'unpaid' or (not pay_st and st.lower() in ('unpaid', 'draft', 'pending')):
            self.status_combo.set('Unpaid')
        else:
            self.status_combo.set('Paid')

        # Select Customer
        for idx, c in enumerate(self.customers):
            if c['id'] == order['customer_id']:
                self.cust_combo.current(idx)
                break

        # Clear initial blank row
        for r in self.line_items:
            r['combo_item'].destroy()
            r['entry_hsn'].destroy()
            r['entry_qty'].destroy()
            r['entry_unit'].destroy()
            r['entry_rate'].destroy()
            r['lbl_amt'].destroy()
            r['btn_del'].destroy()
        self.line_items.clear()

        for item in order.get('items', []):
            self._add_line_item_row()
            last_row = self.line_items[-1]
            
            # Select Item in combo
            for i_idx, itm in enumerate(self.items_list):
                if itm['id'] == item['item_id']:
                    last_row['combo_item'].current(i_idx)
                    break

            last_row['entry_hsn'].delete(0, tk.END)
            last_row['entry_hsn'].insert(0, item.get('hsn_code', '39211310'))

            last_row['entry_qty'].delete(0, tk.END)
            last_row['entry_qty'].insert(0, str(item['quantity']))

            last_row['entry_unit'].delete(0, tk.END)
            last_row['entry_unit'].insert(0, item.get('unit', 'PCS'))

            last_row['entry_rate'].delete(0, tk.END)
            last_row['entry_rate'].insert(0, str(item['unit_price']))

        self._recalculate_totals()

    def _get_form_payload(self):
        c_idx = self.cust_combo.current()
        if c_idx < 0:
            raise ValueError("Please select a customer")

        customer = self.customers[c_idx]

        item_rows = []
        subtotal = 0.0

        for r in self.line_items:
            i_idx = r['combo_item'].current()
            if i_idx < 0:
                raise ValueError("Please select products for all line items")
            
            itm = self.items_list[i_idx]
            qty = float(r['entry_qty'].get().strip())
            rate = float(r['entry_rate'].get().strip())
            amt = qty * rate
            hsn = r['entry_hsn'].get().strip()
            unit = r['entry_unit'].get().strip()

            cgst_amt = amt * 0.09
            sgst_amt = amt * 0.09
            
            subtotal += amt

            item_rows.append({
                'item_id': itm['id'],
                'item_name': itm['name'],
                'hsn_code': hsn,
                'quantity': qty,
                'unit': unit,
                'unit_price': rate,
                'discount': 0.0,
                'amount': amt,
                'cgst_rate': 9.0,
                'sgst_rate': 9.0,
                'tax_amount': cgst_amt + sgst_amt
            })

        try:
            freight = float(self.freight_entry.get().strip() or 0)
        except ValueError:
            freight = 0.0

        taxable_total = subtotal + freight
        cgst_sum = taxable_total * 0.09
        sgst_sum = taxable_total * 0.09
        raw_tot = taxable_total + cgst_sum + sgst_sum
        grand_tot = round(raw_tot)
        round_off = grand_tot - raw_tot

        from models.fiscal_year import FiscalYearModel
        active_fy = FiscalYearModel.get_active_year().get('year_label', '2026-2027')

        sel_st = self.status_combo.get().strip() if hasattr(self, 'status_combo') else 'Paid'
        if sel_st == 'Cancelled':
            db_st = 'Cancelled'
            pay_st = 'Cancelled'
        elif sel_st == 'Unpaid':
            db_st = 'Confirmed'
            pay_st = 'Unpaid'
        else:
            db_st = 'Paid'
            pay_st = 'Paid'

        order_data = {
            'invoice_number': self.inv_num_entry.get().strip(),
            'customer_id': customer['id'],
            'invoice_date': self.inv_date_entry.get().strip(),
            'due_date': self.due_date_entry.get().strip(),
            'vehicle_no': self.veh_entry.get().strip(),
            'eway_bill_no': self.eway_entry.get().strip(),
            'fiscal_year': active_fy,
            'place_of_supply': customer.get('place_of_supply', 'Uttar Pradesh'),
            'status': db_st,
            'payment_status': pay_st,
            'subtotal': subtotal,
            'freight': freight,
            'cgst_amount': cgst_sum,
            'sgst_amount': sgst_sum,
            'igst_amount': 0.0,
            'round_off': round_off,
            'total_amount': grand_tot,
            'notes': 'Generated via Desktop App'
        }

        return order_data, customer, item_rows

    def _save_invoice(self):
        try:
            order_data, _, item_rows = self._get_form_payload()
            if self.order_id:
                SalesOrderModel.update(self.order_id, order_data, item_rows)
            else:
                self.order_id = SalesOrderModel.create(order_data, item_rows)
            if self.on_save:
                self.on_save()
            messagebox.showinfo("Success", f"Invoice #{order_data['invoice_number']} saved successfully!", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save invoice: {str(ex)}", parent=self)

    def _export_pdf(self):
        try:
            order_data, customer, item_rows = self._get_form_payload()
            page_size = self.page_size_combo.get()
            copy_type = self.copy_combo.get()

            pdf_path = generate_tax_invoice_pdf(
                order=order_data,
                customer=customer,
                items=item_rows,
                page_size=page_size,
                copy_type=copy_type
            )

            # Auto-open PDF in default viewer
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path])

            messagebox.showinfo("PDF Export", f"Generated Tax Invoice PDF ({page_size}) successfully!\nSaved to: {pdf_path}", parent=self)
        except Exception as ex:
            messagebox.showerror("Export Error", f"Failed to generate PDF: {str(ex)}", parent=self)

    def _quick_add_customer(self):
        from ui.components.dialogs import ContactDialog
        ContactDialog(self, contact_data={'contact_type': 'Customer'}, on_save=self._on_customer_created)

    def _on_customer_created(self, new_id=None):
        self.customers = ContactModel.get_all("Customer")
        cust_labels = [f"{c['name']} ({c.get('gstin', 'No GSTIN')})" for c in self.customers]
        self.cust_combo['values'] = cust_labels

        if new_id:
            for idx, c in enumerate(self.customers):
                if c['id'] == new_id:
                    self.cust_combo.current(idx)
                    break
        elif cust_labels:
            self.cust_combo.current(len(cust_labels) - 1)

