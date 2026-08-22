"""
Modal Dialog Forms for Item, Contact, and Stock Adjustment Entry
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.item import ItemModel
from models.contact import ContactModel
from models.inventory import InventoryModel
from models.payment import PaymentModel
from ui.components.data_table import DataTable

class ItemDialog(tk.Toplevel):
    def __init__(self, parent, item_data=None, on_save=None):
        super().__init__(parent)
        self.title("Edit Item" if item_data else "Add New Item")
        self.geometry("640x720")
        self.minsize(580, 560)
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.item_data = item_data or {}
        self.on_save = on_save
        self.entries = {}

        self._build_ui()

    def _on_category_changed(self, event=None):
        selected_cat = self.cat_combo.get().strip()
        subcats = ItemModel.get_subcategories(selected_cat)
        self.subcat_combo['values'] = subcats
        cur_sub = self.subcat_combo.get().strip()
        if not cur_sub and subcats:
            self.subcat_combo.set(subcats[0])

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=15)
        h_frame.pack(fill="x", side="top")

        title_txt = "✏️ Edit Product Details" if self.item_data else "➕ Add New Product"
        tk.Label(h_frame, text=title_txt, font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # Action Buttons (Pinned to Bottom)
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=25, pady=15)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Save Item", style="Primary.TButton", command=self._save).pack(side="right", padx=5)

        # Form Container
        card = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=20, pady=15)
        card.pack(fill="both", expand=True, padx=20, pady=15)

        # Grid configuration
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        # Row 0: Basic info
        tk.Label(card, text="SKU Code *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=6, pady=(4, 2))
        sku_entry = ttk.Entry(card, width=24)
        sku_entry.insert(0, self.item_data.get('sku', ''))
        sku_entry.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.entries['sku'] = sku_entry

        tk.Label(card, text="Barcode / Serial", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=6, pady=(4, 2))
        barcode_entry = ttk.Entry(card, width=24)
        barcode_entry.insert(0, self.item_data.get('barcode', ''))
        barcode_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['barcode'] = barcode_entry

        # Row 2: Product Name (Span 2 cols)
        tk.Label(card, text="Product / Item Name *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=2, column=0, sticky="w", padx=6, pady=(4, 2))
        name_entry = ttk.Entry(card)
        name_entry.insert(0, self.item_data.get('name', 'PU FOAM SHEETS'))
        name_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
        self.entries['name'] = name_entry

        # Row 4: Parent Category & Sub-Category
        tk.Label(card, text="Main / Parent Category *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=4, column=0, sticky="w", padx=6, pady=(4, 2))
        all_cats = ItemModel.get_categories()
        self.cat_combo = ttk.Combobox(card, values=all_cats, width=24)
        init_cat = self.item_data.get('category', 'PU FOAM SHEETS')
        self.cat_combo.set(init_cat if init_cat in all_cats else init_cat or 'PU FOAM SHEETS')
        self.cat_combo.grid(row=5, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_category_changed)
        self.cat_combo.bind("<KeyRelease>", self._on_category_changed)
        self.entries['category'] = self.cat_combo

        tk.Label(card, text="Sub-Category (e.g. Density 32, HR Foam, etc.)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=4, column=1, sticky="w", padx=6, pady=(4, 2))
        subcats = ItemModel.get_subcategories(self.cat_combo.get())
        self.subcat_combo = ttk.Combobox(card, values=subcats, width=24)
        init_subcat = self.item_data.get('subcategory', '')
        self.subcat_combo.set(init_subcat)
        self.subcat_combo.grid(row=5, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['subcategory'] = self.subcat_combo

        # Row 6: Brand & HSN Code
        tk.Label(card, text="Brand", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=6, column=0, sticky="w", padx=6, pady=(4, 2))
        brand_entry = ttk.Entry(card, width=24)
        brand_entry.insert(0, self.item_data.get('brand', 'Generic'))
        brand_entry.grid(row=7, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.entries['brand'] = brand_entry

        tk.Label(card, text="HSN / SAC Code", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=6, column=1, sticky="w", padx=6, pady=(4, 2))
        hsn_entry = ttk.Entry(card, width=24)
        hsn_entry.insert(0, self.item_data.get('hsn_code', '39211310'))
        hsn_entry.grid(row=7, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['hsn_code'] = hsn_entry

        # Row 8: Unit & Tax Rate
        tk.Label(card, text="Unit (PCS / KGS / BOX / MTR)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=8, column=0, sticky="w", padx=6, pady=(4, 2))
        unit_combo = ttk.Combobox(card, values=["PCS", "KGS", "MTR", "BOX", "SET", "ROLL"], width=24)
        unit_combo.set(self.item_data.get('unit', 'PCS'))
        unit_combo.grid(row=9, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.entries['unit'] = unit_combo

        tk.Label(card, text="GST Tax Rate %", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=8, column=1, sticky="w", padx=6, pady=(4, 2))
        tax_combo = ttk.Combobox(card, values=["18.0", "12.0", "5.0", "28.0", "0.0"], width=24)
        tax_combo.set(str(self.item_data.get('tax_rate', 18.0)))
        tax_combo.grid(row=9, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['tax_rate'] = tax_combo

        # Row 10: Cost Price & Selling Price
        tk.Label(card, text="Unit Cost Price (₹)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=10, column=0, sticky="w", padx=6, pady=(4, 2))
        cost_entry = ttk.Entry(card, width=24)
        cost_entry.insert(0, str(self.item_data.get('cost_price', 0.0)))
        cost_entry.grid(row=11, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.entries['cost_price'] = cost_entry

        tk.Label(card, text="Selling Price (₹)", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=10, column=1, sticky="w", padx=6, pady=(4, 2))
        selling_entry = ttk.Entry(card, width=24)
        selling_entry.insert(0, str(self.item_data.get('selling_price', 0.0)))
        selling_entry.grid(row=11, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['selling_price'] = selling_entry

        # Row 12: Initial Stock & Reorder Threshold
        tk.Label(card, text="Current / Initial Stock", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=12, column=0, sticky="w", padx=6, pady=(4, 2))
        stock_entry = ttk.Entry(card, width=24)
        stock_entry.insert(0, str(self.item_data.get('current_stock', 0.0)))
        stock_entry.grid(row=13, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.entries['current_stock'] = stock_entry

        tk.Label(card, text="Reorder Alert Level", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=12, column=1, sticky="w", padx=6, pady=(4, 2))
        reorder_entry = ttk.Entry(card, width=24)
        reorder_entry.insert(0, str(self.item_data.get('reorder_level', 10.0)))
        reorder_entry.grid(row=13, column=1, sticky="ew", padx=6, pady=(0, 6))
        self.entries['reorder_level'] = reorder_entry

    def _save(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        if not data['sku'] or not data['name']:
            messagebox.showerror("Error", "SKU and Product Name are required fields!", parent=self)
            return

        if not data['category']:
            data['category'] = 'PU FOAM SHEETS'

        try:
            if self.item_data and 'id' in self.item_data:
                ItemModel.update(self.item_data['id'], data)
            else:
                ItemModel.create(data)

            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save item: {str(ex)}", parent=self)


class ContactDialog(tk.Toplevel):
    def __init__(self, parent, contact_data=None, on_save=None):
        super().__init__(parent)
        self.title("Edit Contact" if contact_data else "Add New Contact")
        self.geometry("640x640")
        self.minsize(580, 520)
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.contact_data = contact_data or {}
        self.on_save = on_save
        self.entries = {}

        self._build_ui()

    def _build_ui(self):
        # 1. Header Toolbar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=14)
        h_frame.pack(fill="x", side="top")

        title_txt = "✏️ Edit Contact Details" if self.contact_data else "👥 Add New Contact"
        tk.Label(h_frame, text=title_txt, font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # 2. Action Buttons (Pinned to Bottom)
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Save Contact", style="Primary.TButton", command=self._save).pack(side="right", padx=5)

        # 3. Main Form Card
        card = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=20, pady=15)
        card.pack(fill="both", expand=True, padx=20, pady=10)

        # Row 0: Section - Basic Info
        tk.Label(card, text="👤 Basic Information", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Contact Name
        tk.Label(card, text="Contact Name *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=1, column=0, sticky="w", padx=5)
        name_entry = ttk.Entry(card, width=28)
        name_entry.insert(0, self.contact_data.get('name', ''))
        name_entry.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 10))
        self.entries['name'] = name_entry

        # Company Name
        tk.Label(card, text="Company Name", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=1, column=1, sticky="w", padx=5)
        comp_entry = ttk.Entry(card, width=28)
        comp_entry.insert(0, self.contact_data.get('company_name', ''))
        comp_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=(0, 10))
        self.entries['company_name'] = comp_entry

        # Contact Type (Dropdown)
        tk.Label(card, text="Contact Type *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=3, column=0, sticky="w", padx=5)
        ctype_combo = ttk.Combobox(card, values=["Customer", "Supplier"], state="readonly", width=26)
        default_type = self.contact_data.get('contact_type', 'Customer')
        ctype_combo.set(default_type if default_type in ["Customer", "Supplier"] else "Customer")
        ctype_combo.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['contact_type'] = ctype_combo

        # Row 5: Section - Contact & Location Details
        tk.Label(card, text="📞 Contact & Location", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 8))

        # Phone
        tk.Label(card, text="Mobile / Phone", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=6, column=0, sticky="w", padx=5)
        phone_entry = ttk.Entry(card, width=28)
        phone_entry.insert(0, self.contact_data.get('phone', ''))
        phone_entry.grid(row=7, column=0, sticky="ew", padx=5, pady=(0, 10))
        self.entries['phone'] = phone_entry

        # Email
        tk.Label(card, text="Email Address", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=6, column=1, sticky="w", padx=5)
        email_entry = ttk.Entry(card, width=28)
        email_entry.insert(0, self.contact_data.get('email', ''))
        email_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=(0, 10))
        self.entries['email'] = email_entry

        # State / Place of Supply
        tk.Label(card, text="State / Place of Supply", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=8, column=0, sticky="w", padx=5)
        pos_entry = ttk.Entry(card, width=28)
        pos_entry.insert(0, self.contact_data.get('place_of_supply', 'Uttar Pradesh'))
        pos_entry.grid(row=9, column=0, sticky="ew", padx=5, pady=(0, 12))
        self.entries['place_of_supply'] = pos_entry

        # Row 10: Section - Tax & Billing
        tk.Label(card, text="🧾 GST & Tax Details", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"]).grid(row=10, column=0, columnspan=2, sticky="w", pady=(5, 8))

        # GSTIN
        tk.Label(card, text="GSTIN", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=11, column=0, sticky="w", padx=5)
        gstin_entry = ttk.Entry(card, width=28)
        gstin_entry.insert(0, self.contact_data.get('gstin', ''))
        gstin_entry.grid(row=12, column=0, sticky="ew", padx=5, pady=(0, 10))
        self.entries['gstin'] = gstin_entry

        # PAN Number
        tk.Label(card, text="PAN Number", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=11, column=1, sticky="w", padx=5)
        pan_entry = ttk.Entry(card, width=28)
        pan_entry.insert(0, self.contact_data.get('pan', ''))
        pan_entry.grid(row=12, column=1, sticky="ew", padx=5, pady=(0, 10))
        self.entries['pan'] = pan_entry

        # Address (Spans 2 columns)
        tk.Label(card, text="Full Billing Address", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=13, column=0, columnspan=2, sticky="w", padx=5)
        addr_entry = ttk.Entry(card, width=58)
        addr_entry.insert(0, self.contact_data.get('address', ''))
        addr_entry.grid(row=14, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        self.entries['address'] = addr_entry

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

    def _save(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        if not data['name']:
            messagebox.showerror("Error", "Contact Name is required!", parent=self)
            return

        try:
            if self.contact_data and 'id' in self.contact_data:
                ContactModel.update(self.contact_data['id'], data)
                new_id = self.contact_data['id']
            else:
                new_id = ContactModel.create(data)

            if self.on_save:
                try:
                    self.on_save(new_id)
                except TypeError:
                    self.on_save()
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save contact: {str(ex)}", parent=self)


class StockAdjustmentDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Adjust Stock Level")
        self.geometry("450x450")
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save
        self.items = ItemModel.get_all()
        self._build_ui()

    def _build_ui(self):
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=15)
        h_frame.pack(fill="x")

        tk.Label(h_frame, text="🔄 Record Stock Adjustment", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        form = tk.Frame(self, bg=COLORS["bg_dark"], padx=25, pady=20)
        form.pack(fill="both", expand=True)

        # Item Selector
        tk.Label(form, text="Select Product *", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        item_labels = [f"{i['sku']} - {i['name']} (Stock: {i['current_stock']})" for i in self.items]
        self.item_combo = ttk.Combobox(form, values=item_labels, state="readonly", width=45)
        if item_labels:
            self.item_combo.current(0)
        self.item_combo.pack(anchor="w", pady=(0, 6))

        # Type (Add / Remove)
        tk.Label(form, text="Adjustment Action *", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.type_combo = ttk.Combobox(form, values=["Add", "Remove"], state="readonly", width=45)
        self.type_combo.current(0)
        self.type_combo.pack(anchor="w", pady=(0, 6))

        # Quantity
        tk.Label(form, text="Quantity *", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.qty_entry = ttk.Entry(form, width=45)
        self.qty_entry.insert(0, "10")
        self.qty_entry.pack(anchor="w", pady=(0, 6))

        # Reason
        tk.Label(form, text="Reason Code", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.reason_combo = ttk.Combobox(form, values=["Restock", "Audit Adjustment", "Damaged / Expired", "Returned Item", "Theft / Loss"], state="readonly", width=45)
        self.reason_combo.current(0)
        self.reason_combo.pack(anchor="w", pady=(0, 6))

        # Notes
        tk.Label(form, text="Notes", font=FONTS["small"], bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.notes_entry = ttk.Entry(form, width=45)
        self.notes_entry.pack(anchor="w", pady=(0, 6))

        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=25, pady=15)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Post Adjustment", style="Primary.TButton", command=self._save).pack(side="right", padx=5)

    def _save(self):
        sel_idx = self.item_combo.current()
        if sel_idx < 0 or sel_idx >= len(self.items):
            messagebox.showerror("Error", "Please select a valid item!", parent=self)
            return

        item_id = self.items[sel_idx]['id']
        adj_type = self.type_combo.get()
        reason = self.reason_combo.get()
        notes = self.notes_entry.get().strip()

        try:
            qty = float(self.qty_entry.get().strip())
            InventoryModel.create_adjustment(item_id, adj_type, qty, reason, "Admin", notes)
            if self.on_save:
                self.on_save()
            self.destroy()
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid quantity: {str(ve)}", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to post adjustment: {str(ex)}", parent=self)


class UserDialog(tk.Toplevel):
    def __init__(self, parent, user_data=None, on_save=None):
        super().__init__(parent)
        self.title("Edit User Credentials & Role" if user_data else "Create New User Credentials")
        self.geometry("520x540")
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.user_data = user_data or {}
        self.on_save = on_save

        self._build_ui()

    def _build_ui(self):
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=14)
        h_frame.pack(fill="x")

        title_txt = "✏️ Edit User Credentials & Role" if self.user_data else "🔑 Create New User Credentials"
        tk.Label(h_frame, text=title_txt, font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_dark"]).pack(anchor="w")

        card = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=22, pady=20)
        card.pack(fill="both", expand=True, padx=20, pady=15)

        # Full Name
        tk.Label(card, text="Full Name *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.fullname_entry = ttk.Entry(card, width=44)
        self.fullname_entry.insert(0, self.user_data.get('full_name', ''))
        self.fullname_entry.pack(anchor="w", pady=(0, 10))

        # Username
        tk.Label(card, text="Username / Login ID *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.username_entry = ttk.Entry(card, width=44)
        self.username_entry.insert(0, self.user_data.get('username', ''))
        self.username_entry.pack(anchor="w", pady=(0, 10))

        # Password
        pass_lbl = "New Password (leave blank to keep current)" if self.user_data else "Password *"
        tk.Label(card, text=pass_lbl, font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.password_entry = ttk.Entry(card, width=44, show="•")
        self.password_entry.pack(anchor="w", pady=(0, 10))

        # Role Dropdown
        tk.Label(card, text="Assign User Role *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        roles = ["Admin", "Manager", "Biller / Sales", "Storekeeper"]
        self.role_combo = ttk.Combobox(card, values=roles, state="readonly", width=42)
        cur_role = self.user_data.get('role', 'Biller / Sales')
        self.role_combo.set(cur_role if cur_role in roles else "Admin")
        self.role_combo.pack(anchor="w", pady=(0, 10))

        # Account Status
        tk.Label(card, text="Account Status *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        statuses = ["Active", "Inactive"]
        self.status_combo = ttk.Combobox(card, values=statuses, state="readonly", width=42)
        self.status_combo.set(self.user_data.get('status', 'Active'))
        self.status_combo.pack(anchor="w", pady=(0, 10))

        # Bottom Buttons
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Save User Credentials", style="Primary.TButton", command=self._save).pack(side="right", padx=5)

    def _save(self):
        full_name = self.fullname_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get()
        status = self.status_combo.get()

        if not full_name or not username:
            messagebox.showerror("Error", "Full Name and Username are required!", parent=self)
            return

        if not self.user_data and not password:
            messagebox.showerror("Error", "Password is required for new users!", parent=self)
            return

        from models.user import UserModel
        try:
            data = {
                'full_name': full_name,
                'username': username,
                'role': role,
                'status': status
            }
            if self.user_data and 'id' in self.user_data:
                UserModel.update_user(self.user_data['id'], data, password)
            else:
                UserModel.create_user(username, password, full_name, role, status)

            if self.on_save:
                self.on_save()
            messagebox.showinfo("Success", f"User account '{username}' saved successfully!", parent=self)
            self.destroy()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save user: {str(ex)}", parent=self)


class PurchaseDialog(tk.Toplevel):
    def __init__(self, parent, default_status="Received", po_id=None, on_save=None):
        super().__init__(parent)
        self.po_id = po_id
        self.default_status = default_status
        self.on_save = on_save

        title_txt = f"✏️ Edit Purchase Order" if po_id else ("🛒 Direct Purchase Entry" if default_status == "Received" else "📋 Purchase Order")
        self.title(title_txt)
        self.geometry("1140x780")
        self.minsize(1040, 660)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.suppliers = ContactModel.get_all("Supplier")
        self.items_list = ItemModel.get_all()
        self.line_items = []

        self._build_ui()
        if self.po_id:
            self._load_existing_po()
        else:
            self._add_line_item_row()

    def _refresh_suppliers(self):
        self.suppliers = ContactModel.get_all("Supplier")
        sup_names = [f"{s['name']} ({s.get('company_name') or 'Supplier'})" for s in self.suppliers]
        self.sup_combo.config(values=sup_names)
        if sup_names:
            self.sup_combo.current(len(sup_names) - 1)

    def _quick_add_supplier(self):
        ContactDialog(self, contact_data={'contact_type': 'Supplier'}, on_save=self._refresh_suppliers)

    def _build_ui(self):
        from models.purchase_order import PurchaseOrderModel
        from datetime import datetime, timedelta

        # 1. Header Toolbar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x")

        title_txt = "✏️ Edit Purchase Entry / PO" if self.po_id else ("🛒 Direct Purchase Entry" if self.default_status == "Received" else "📋 Create Purchase Order")
        tk.Label(h_frame, text=title_txt, font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(side="left")

        # 2. Bottom Action Buttons
        btn_bar = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_bar.pack(fill="x", side="bottom")

        ttk.Button(btn_bar, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        save_txt = "💾 Update Purchase" if self.po_id else ("💾 Save & Add to Stock" if self.default_status == "Received" else "💾 Save Purchase Order")
        ttk.Button(btn_bar, text=save_txt, style="Primary.TButton", command=lambda: self._save(self.status_combo.get())).pack(side="right", padx=5)

        # 3. Main Form Scrollable Container
        outer_container = tk.Frame(self, bg=COLORS["bg_dark"])
        outer_container.pack(fill="both", expand=True, padx=15, pady=8)

        # Meta Box
        meta_box = tk.Frame(outer_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        meta_box.pack(fill="x", pady=(0, 10))

        # Metadata Row
        tk.Label(meta_box, text="Supplier *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=6, pady=2)
        sup_frame = tk.Frame(meta_box, bg=COLORS["bg_card"])
        sup_frame.grid(row=1, column=0, sticky="w", padx=6, pady=(0, 4))

        sup_names = [f"{s['name']} ({s.get('company_name') or 'Supplier'})" for s in self.suppliers]
        self.sup_combo = ttk.Combobox(sup_frame, values=sup_names, state="readonly", width=28)
        self.sup_combo.pack(side="left", padx=(0, 6))
        if sup_names:
            self.sup_combo.current(0)
        ttk.Button(sup_frame, text="➕ New", style="Secondary.TButton", command=self._quick_add_supplier).pack(side="left")

        tk.Label(meta_box, text="Supplier Invoice / PO #", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=6, pady=2)
        self.inv_num_entry = ttk.Entry(meta_box, width=18)
        self.inv_num_entry.insert(0, PurchaseOrderModel.generate_po_number())
        self.inv_num_entry.grid(row=1, column=1, sticky="w", padx=6, pady=(0, 4))

        tk.Label(meta_box, text="Purchase Date", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=2, sticky="w", padx=6, pady=2)
        self.pur_date_entry = ttk.Entry(meta_box, width=14)
        self.pur_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.pur_date_entry.grid(row=1, column=2, sticky="w", padx=6, pady=(0, 4))

        tk.Label(meta_box, text="Status", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=3, sticky="w", padx=6, pady=2)
        self.status_combo = ttk.Combobox(meta_box, values=["Ordered", "Received", "Cancelled"], state="readonly", width=12)
        self.status_combo.set(self.default_status)
        self.status_combo.grid(row=1, column=3, sticky="w", padx=6, pady=(0, 4))

        tk.Label(meta_box, text="Exp. Delivery Date", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=4, sticky="w", padx=6, pady=2)
        self.exp_date_entry = ttk.Entry(meta_box, width=14)
        self.exp_date_entry.insert(0, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.exp_date_entry.grid(row=1, column=4, sticky="w", padx=6, pady=(0, 4))

        tk.Label(meta_box, text="GST Tax Applied", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=5, sticky="w", padx=6, pady=2)
        self.gst_mode_combo = ttk.Combobox(meta_box, values=["18% GST (9% CGST + 9% SGST)", "None (0% / Exempt)"], state="readonly", width=22)
        self.gst_mode_combo.current(0)
        self.gst_mode_combo.grid(row=1, column=5, sticky="w", padx=6, pady=(0, 4))
        self.gst_mode_combo.bind("<<ComboboxSelected>>", lambda e: self._recalculate_totals())

        # 4. Items Table Box
        items_frame = tk.Frame(outer_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=10)
        items_frame.pack(fill="both", expand=True, pady=(0, 10))

        grid_hdr = tk.Frame(items_frame, bg=COLORS["bg_card"])
        grid_hdr.pack(fill="x", pady=(0, 6))

        tk.Label(grid_hdr, text="📦 Purchase Items & Cost Details", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")
        ttk.Button(grid_hdr, text="➕ Add Single Row", style="Secondary.TButton", command=self._add_line_item_row).pack(side="right", padx=3)
        ttk.Button(grid_hdr, text="☑️ Multi-Select Products", style="Primary.TButton", command=self._open_multi_select_dialog).pack(side="right", padx=3)

        # Scrollable Line Items Frame
        canvas = tk.Canvas(items_frame, bg=COLORS["bg_card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=canvas.yview)
        
        self.items_grid = tk.Frame(canvas, bg=COLORS["bg_card"])
        self.items_grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas_window = canvas.create_window((0, 0), window=self.items_grid, anchor="nw")
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', _on_canvas_configure)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure Grid Column Weights and Minsizes
        self.items_grid.columnconfigure(0, weight=3, minsize=220)  # Product
        self.items_grid.columnconfigure(1, weight=2, minsize=130)  # Sub-Category / Grade
        self.items_grid.columnconfigure(2, weight=1, minsize=90)   # HSN
        self.items_grid.columnconfigure(3, weight=1, minsize=80)   # Quantity
        self.items_grid.columnconfigure(4, weight=1, minsize=70)   # Unit
        self.items_grid.columnconfigure(5, weight=1, minsize=105)  # Unit Cost
        self.items_grid.columnconfigure(6, weight=1, minsize=120)  # Taxable Amount
        self.items_grid.columnconfigure(7, weight=0, minsize=45)   # Action

        # Table Column Headers (Row 0)
        headers = [
            ("Product / Item Description", "w", 0),
            ("Sub-Category / Grade", "w", 1),
            ("HSN Code", "center", 2),
            ("Quantity", "center", 3),
            ("Unit", "center", 4),
            ("Unit Cost (₹)", "e", 5),
            ("Taxable Cost (₹)", "e", 6),
            ("Action", "center", 7)
        ]
        for title, anchor_pos, col_idx in headers:
            h_lbl = tk.Label(self.items_grid, text=title, font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_dark"], anchor=anchor_pos, padx=6, pady=6)
            h_lbl.grid(row=0, column=col_idx, sticky="nsew", padx=2, pady=(0, 4))

        # 5. Calculation Summary Card (Bottom)
        tot_frame = tk.Frame(outer_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        tot_frame.pack(fill="x", pady=(0, 4))

        # Left Info in Summary Card
        tot_left = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        tot_left.pack(side="left", fill="both", expand=True)

        self.words_lbl = tk.Label(tot_left, text="Total in Words: Zero Rupees Only", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"], anchor="w", wraplength=450, justify="left")
        self.words_lbl.pack(anchor="w", pady=(2, 0))

        # Right Breakdown in Summary Card
        tot_right = tk.Frame(tot_frame, bg=COLORS["bg_card"])
        tot_right.pack(side="right")

        # Row: Taxable Subtotal
        r_sub = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_sub.pack(anchor="e", pady=1)
        tk.Label(r_sub, text="Taxable Subtotal: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_subtotal = tk.Label(r_sub, text="₹ 0.00", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=14, anchor="e")
        self.lbl_subtotal.pack(side="left")

        # Row: CGST (9%)
        r_cgst = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_cgst.pack(anchor="e", pady=1)
        tk.Label(r_cgst, text="CGST @ 9%: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_cgst = tk.Label(r_cgst, text="₹ 0.00", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=14, anchor="e")
        self.lbl_cgst.pack(side="left")

        # Row: SGST (9%)
        r_sgst = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_sgst.pack(anchor="e", pady=1)
        tk.Label(r_sgst, text="SGST @ 9%: ", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self.lbl_sgst = tk.Label(r_sgst, text="₹ 0.00", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_light"], width=14, anchor="e")
        self.lbl_sgst.pack(side="left")

        # Row: Total Purchase Amount
        r_tot = tk.Frame(tot_right, bg=COLORS["bg_card"])
        r_tot.pack(anchor="e", pady=(4, 0))
        tk.Label(r_tot, text="Total Purchase Amount: ", font=("Segoe UI", 12, "bold"), bg=COLORS["bg_card"], fg=COLORS["success"]).pack(side="left")
        self.lbl_grand_total = tk.Label(r_tot, text="₹ 0.00", font=("Segoe UI", 13, "bold"), bg=COLORS["bg_card"], fg=COLORS["success"], width=14, anchor="e")
        self.lbl_grand_total.pack(side="left")

    def _add_line_item_row(self):
        grid_row = len(self.line_items) + 1  # Row 0 is header

        # Product Dropdown with clean stock string
        item_names = [f"{i['sku']} - {i['name']} (Stock: {round(float(i.get('current_stock', 0.0)), 2):g})" for i in self.items_list]
        combo_item = ttk.Combobox(self.items_grid, values=item_names, state="readonly")
        combo_item.grid(row=grid_row, column=0, sticky="ew", padx=2, pady=2)
        if item_names:
            combo_item.current(0)

        # Sub-Category / Grade Combobox (1ST GRADE, B-GRADE, CROSS, etc.)
        subcats = ItemModel.get_subcategories("PU FOAM SHEETS")
        combo_subcat = ttk.Combobox(self.items_grid, values=subcats)
        combo_subcat.set("1ST GRADE")
        combo_subcat.grid(row=grid_row, column=1, sticky="ew", padx=2, pady=2)

        # HSN
        entry_hsn = ttk.Entry(self.items_grid, justify="center")
        entry_hsn.grid(row=grid_row, column=2, sticky="ew", padx=2, pady=2)

        # Qty
        entry_qty = ttk.Entry(self.items_grid, justify="center")
        entry_qty.insert(0, "10.0")
        entry_qty.grid(row=grid_row, column=3, sticky="ew", padx=2, pady=2)

        # Unit
        entry_unit = ttk.Entry(self.items_grid, justify="center")
        entry_unit.insert(0, "PCS")
        entry_unit.grid(row=grid_row, column=4, sticky="ew", padx=2, pady=2)

        # Cost Price
        entry_cost = ttk.Entry(self.items_grid, justify="right")
        entry_cost.insert(0, "0.00")
        entry_cost.grid(row=grid_row, column=5, sticky="ew", padx=2, pady=2)

        # Total Cost Label
        lbl_tot = tk.Label(self.items_grid, text="₹ 0.00", font=FONTS["body_bold"], bg=COLORS["bg_card_alt"], fg=COLORS["text_light"], anchor="e", padx=6, pady=4)
        lbl_tot.grid(row=grid_row, column=6, sticky="ew", padx=2, pady=2)

        # Delete Button
        btn_del = tk.Button(self.items_grid, text="❌", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["danger"], activeforeground="red", bd=0, cursor="hand2")
        btn_del.grid(row=grid_row, column=7, sticky="ew", padx=2, pady=2)

        row_dict = {
            'combo_item': combo_item,
            'combo_subcat': combo_subcat,
            'entry_hsn': entry_hsn,
            'entry_qty': entry_qty,
            'entry_unit': entry_unit,
            'entry_cost': entry_cost,
            'lbl_tot': lbl_tot,
            'btn_del': btn_del
        }

        btn_del.config(command=lambda r=row_dict: self._remove_line_item_row(r))
        combo_item.bind("<<ComboboxSelected>>", lambda e, r=row_dict: self._on_item_selected(r))
        entry_qty.bind("<KeyRelease>", lambda e: self._recalculate_totals())
        entry_cost.bind("<KeyRelease>", lambda e: self._recalculate_totals())

        self.line_items.append(row_dict)

        if item_names:
            self._on_item_selected(row_dict)
        else:
            self._recalculate_totals()

    def _remove_line_item_row(self, row_dict):
        if len(self.line_items) <= 1:
            messagebox.showwarning("Warning", "At least one product item is required in the purchase entry!", parent=self)
            return
        
        row_dict['combo_item'].destroy()
        row_dict['combo_subcat'].destroy()
        row_dict['entry_hsn'].destroy()
        row_dict['entry_qty'].destroy()
        row_dict['entry_unit'].destroy()
        row_dict['entry_cost'].destroy()
        row_dict['lbl_tot'].destroy()
        row_dict['btn_del'].destroy()
        self.line_items.remove(row_dict)

        # Re-index rows in grid
        for idx, r in enumerate(self.line_items, start=1):
            r['combo_item'].grid(row=idx, column=0, sticky="ew", padx=2, pady=2)
            r['combo_subcat'].grid(row=idx, column=1, sticky="ew", padx=2, pady=2)
            r['entry_hsn'].grid(row=idx, column=2, sticky="ew", padx=2, pady=2)
            r['entry_qty'].grid(row=idx, column=3, sticky="ew", padx=2, pady=2)
            r['entry_unit'].grid(row=idx, column=4, sticky="ew", padx=2, pady=2)
            r['entry_cost'].grid(row=idx, column=5, sticky="ew", padx=2, pady=2)
            r['lbl_tot'].grid(row=idx, column=6, sticky="ew", padx=2, pady=2)
            r['btn_del'].grid(row=idx, column=7, sticky="ew", padx=2, pady=2)

        self._recalculate_totals()

    def _on_item_selected(self, row_dict):
        idx = row_dict['combo_item'].current()
        if idx >= 0 and idx < len(self.items_list):
            item = self.items_list[idx]
            
            # Auto-set subcategory if present or defaults to 1ST GRADE
            if item.get('subcategory'):
                row_dict['combo_subcat'].set(item['subcategory'])
            elif not row_dict['combo_subcat'].get().strip():
                row_dict['combo_subcat'].set('1ST GRADE')

            row_dict['entry_hsn'].delete(0, tk.END)
            row_dict['entry_hsn'].insert(0, str(item.get('hsn_code') or '00000000'))

            row_dict['entry_unit'].delete(0, tk.END)
            row_dict['entry_unit'].insert(0, str(item.get('unit') or 'PCS'))

            row_dict['entry_cost'].delete(0, tk.END)
            cost_val = float(item.get('cost_price') or 0.0)
            row_dict['entry_cost'].insert(0, f"{cost_val:.2f}")

            self._recalculate_totals()

    def _recalculate_totals(self):
        subtotal = 0.0
        for r in self.line_items:
            try:
                qty = float(r['entry_qty'].get().strip() or 0)
                cost = float(r['entry_cost'].get().strip() or 0)
                tot = qty * cost
                subtotal += tot
                r['lbl_tot'].config(text=f"₹ {tot:,.2f}")
            except ValueError:
                r['lbl_tot'].config(text="₹ 0.00")

        gst_mode = self.gst_mode_combo.get() if hasattr(self, 'gst_mode_combo') else "18% GST (9% CGST + 9% SGST)"
        if "18%" in gst_mode or "9%" in gst_mode:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            grand_tot = round(subtotal + cgst + sgst)
        else:
            cgst = 0.0
            sgst = 0.0
            grand_tot = round(subtotal)

        self.lbl_subtotal.config(text=f"₹ {subtotal:,.2f}")
        self.lbl_cgst.config(text=f"₹ {cgst:,.2f}")
        self.lbl_sgst.config(text=f"₹ {sgst:,.2f}")
        self.lbl_grand_total.config(text=f"₹ {grand_tot:,.2f}")

        from services.num2words_service import number_to_words_indian
        words = number_to_words_indian(grand_tot)
        self.words_lbl.config(text=f"Total in Words: {words}")

    def _save(self, target_status):
        from models.purchase_order import PurchaseOrderModel
        try:
            if not self.suppliers:
                messagebox.showerror("Supplier Required", "No supplier found! Please add a supplier first using the '➕ New' button.", parent=self)
                return

            s_idx = self.sup_combo.current()
            if s_idx < 0 or s_idx >= len(self.suppliers):
                messagebox.showerror("Error", "Please select a valid supplier!", parent=self)
                return

            sup = self.suppliers[s_idx]
            po_num = self.inv_num_entry.get().strip()
            if not po_num:
                messagebox.showerror("Error", "Supplier Invoice / PO Number is required!", parent=self)
                return

            item_rows = []
            subtotal = 0.0

            for r in self.line_items:
                i_idx = r['combo_item'].current()
                if i_idx < 0 or i_idx >= len(self.items_list):
                    messagebox.showerror("Error", "Please select a valid product for all rows!", parent=self)
                    return
                
                itm = self.items_list[i_idx]
                qty = float(r['entry_qty'].get().strip() or 0)
                cost = float(r['entry_cost'].get().strip() or 0)
                if qty <= 0:
                    messagebox.showerror("Error", f"Quantity for product '{itm['name']}' must be greater than zero!", parent=self)
                    return

                tot = qty * cost
                subtotal += tot
                subcat_val = r['combo_subcat'].get().strip() if 'combo_subcat' in r else ''

                item_rows.append({
                    'item_id': itm['id'],
                    'item_name': itm['name'],
                    'subcategory': subcat_val,
                    'hsn_code': r['entry_hsn'].get().strip() or '00000000',
                    'quantity': qty,
                    'unit': r['entry_unit'].get().strip() or 'PCS',
                    'unit_cost': cost,
                    'total_cost': tot
                })

            gst_mode = self.gst_mode_combo.get() if hasattr(self, 'gst_mode_combo') else "18% GST (9% CGST + 9% SGST)"
            if "18%" in gst_mode or "9%" in gst_mode:
                cgst = subtotal * 0.09
                sgst = subtotal * 0.09
                grand_tot = round(subtotal + cgst + sgst)
            else:
                cgst = 0.0
                sgst = 0.0
                grand_tot = round(subtotal)

            po_data = {
                'po_number': po_num,
                'supplier_id': sup['id'],
                'order_date': self.pur_date_entry.get().strip(),
                'expected_date': self.exp_date_entry.get().strip(),
                'status': target_status,
                'subtotal': subtotal,
                'cgst_amount': cgst,
                'sgst_amount': sgst,
                'total_amount': grand_tot,
                'notes': f"Recorded via Desktop App ({target_status})"
            }

            if self.po_id:
                PurchaseOrderModel.update(self.po_id, po_data, item_rows)
                msg = f"Purchase #{po_num} updated successfully and inventory stock synchronized!"
            else:
                PurchaseOrderModel.create(po_data, item_rows)
                msg = f"Purchase #{po_num} recorded and stock levels successfully updated!" if target_status == 'Received' else f"Purchase Order #{po_num} created with status '{target_status}'."

            if self.on_save:
                self.on_save()

            messagebox.showinfo("Success", msg, parent=self.master)
            self.destroy()

        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save purchase: {str(ex)}", parent=self)

    def _load_existing_po(self):
        from models.purchase_order import PurchaseOrderModel
        try:
            po = PurchaseOrderModel.get_by_id(self.po_id)
            if not po:
                return

            self.title(f"✏️ Edit Purchase #{po.get('po_number', '')}")

            # Supplier
            sup_id = po.get('supplier_id')
            for idx, s in enumerate(self.suppliers):
                if s['id'] == sup_id:
                    self.sup_combo.current(idx)
                    break

            # Metadata entries
            self.inv_num_entry.delete(0, tk.END)
            self.inv_num_entry.insert(0, po.get('po_number', ''))

            self.pur_date_entry.delete(0, tk.END)
            self.pur_date_entry.insert(0, po.get('order_date', ''))

            self.status_combo.set(po.get('status', 'Received'))

            self.exp_date_entry.delete(0, tk.END)
            self.exp_date_entry.insert(0, po.get('expected_date', ''))

            cgst = float(po.get('cgst_amount', 0.0) or 0.0)
            if cgst > 0:
                self.gst_mode_combo.set("18% GST (9% CGST + 9% SGST)")
            else:
                self.gst_mode_combo.set("None (0% / Exempt)")

            # Clear line items if any
            for r in self.line_items:
                r['combo_item'].destroy()
                r['combo_subcat'].destroy()
                r['entry_hsn'].destroy()
                r['entry_qty'].destroy()
                r['entry_unit'].destroy()
                r['entry_cost'].destroy()
                r['lbl_tot'].destroy()
                r['btn_del'].destroy()
            self.line_items.clear()

            items = po.get('items', [])
            if not items:
                self._add_line_item_row()
            else:
                for itm in items:
                    self._add_line_item_row()
                    last_row = self.line_items[-1]

                    # Match product combo
                    for idx, item_obj in enumerate(self.items_list):
                        if item_obj['id'] == itm['item_id']:
                            last_row['combo_item'].current(idx)
                            break

                    if itm.get('subcategory'):
                        last_row['combo_subcat'].set(itm['subcategory'])

                    last_row['entry_hsn'].delete(0, tk.END)
                    last_row['entry_hsn'].insert(0, str(itm.get('hsn_code', '39211310')))

                    last_row['entry_qty'].delete(0, tk.END)
                    last_row['entry_qty'].insert(0, str(itm.get('quantity', 1.0)))

                    last_row['entry_unit'].delete(0, tk.END)
                    last_row['entry_unit'].insert(0, str(itm.get('unit', 'PCS')))

                    last_row['entry_cost'].delete(0, tk.END)
                    last_row['entry_cost'].insert(0, f"{float(itm.get('unit_cost', 0.0)):.2f}")

            self._recalculate_totals()
        except Exception as ex:
            messagebox.showerror("Load Error", f"Failed to load purchase details: {str(ex)}", parent=self)

    def _open_multi_select_dialog(self):
        MultiProductDialog(self, on_select=self._add_multiple_line_items)

    def _add_multiple_line_items(self, selected_items):
        for item in selected_items:
            self._add_line_item_row()
            last_row = self.line_items[-1]
            for idx, itm in enumerate(self.items_list):
                if itm['id'] == item['id']:
                    last_row['combo_item'].current(idx)
                    self._on_item_selected(last_row)
                    break


class MultiProductDialog(tk.Toplevel):
    def __init__(self, parent, on_select=None):
        super().__init__(parent)
        self.title("☑️ Select Multiple Products")
        self.geometry("560x580")
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.on_select = on_select
        self.items_list = ItemModel.get_all()
        self.check_vars = {}

        self._build_ui()

    def _build_ui(self):
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=14)
        h_frame.pack(fill="x", side="top")

        tk.Label(h_frame, text="☑️ Multi-Select Products for Purchase", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(side="left")

        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="➕ Add Selected Products to Purchase", style="Primary.TButton", command=self._confirm_selection).pack(side="right", padx=5)

        container = tk.Frame(self, bg=COLORS["bg_dark"], padx=15, pady=10)
        container.pack(fill="both", expand=True)

        ctrl_bar = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=10, pady=8)
        ctrl_bar.pack(fill="x", pady=(0, 8))

        tk.Label(ctrl_bar, text="Search:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left", padx=4)
        self.search_entry = ttk.Entry(ctrl_bar, width=20)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_items())

        ttk.Button(ctrl_bar, text="Select All", style="Secondary.TButton", command=self._select_all).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="Deselect All", style="Secondary.TButton", command=self._deselect_all).pack(side="right", padx=4)

        scroll_frame = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        scroll_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_frame, bg=COLORS["bg_card"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.list_inner = tk.Frame(canvas, bg=COLORS["bg_card"], padx=10, pady=10)
        canvas.create_window((0, 0), window=self.list_inner, anchor="nw")

        self.list_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.item_widgets = []
        for item in self.items_list:
            var = tk.IntVar(value=0)
            self.check_vars[item['id']] = var
            
            lbl_txt = f"{item['sku']} - {item['name']} (Cost: ₹{float(item.get('cost_price') or 0):,.2f} | Stock: {item.get('current_stock', 0)})"
            chk = tk.Checkbutton(
                self.list_inner,
                text=lbl_txt,
                variable=var,
                font=FONTS["body"],
                bg=COLORS["bg_card"],
                activebackground=COLORS["bg_card"],
                anchor="w",
                justify="left"
            )
            chk.pack(fill="x", pady=3, anchor="w")
            self.item_widgets.append((item, chk, var))

    def _filter_items(self):
        query = self.search_entry.get().strip().lower()
        for item, chk, var in self.item_widgets:
            match = (query in item['name'].lower()) or (query in item['sku'].lower()) or (query in str(item.get('hsn_code', '')).lower())
            if match:
                chk.pack(fill="x", pady=3, anchor="w")
            else:
                chk.pack_forget()

    def _select_all(self):
        for var in self.check_vars.values():
            var.set(1)

    def _deselect_all(self):
        for var in self.check_vars.values():
            var.set(0)

    def _confirm_selection(self):
        selected = [item for item in self.items_list if self.check_vars.get(item['id']) and self.check_vars[item['id']].get() == 1]
        if not selected:
            messagebox.showwarning("No Selection", "Please check at least one product to add!", parent=self)
            return
        if self.on_select:
            self.on_select(selected)
        self.destroy()


class PaymentDialog(tk.Toplevel):
    def __init__(self, parent, contact_id=None, default_type=None, on_save=None):
        super().__init__(parent)
        self.title("💳 Record Payment Transaction")
        self.geometry("540x580")
        self.minsize(500, 520)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save
        self.contacts = ContactModel.get_all()
        self.initial_contact_id = contact_id
        self.default_type = default_type

        self._build_ui()

    def _build_ui(self):
        from datetime import datetime

        # Header
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=14)
        h_frame.pack(fill="x", side="top")
        tk.Label(h_frame, text="💳 Record Payment (भुगतान प्रविष्टि)", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # Action buttons (bottom)
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Save Payment", style="Primary.TButton", command=self._save).pack(side="right", padx=5)

        # Card container
        card = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=22, pady=18)
        card.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Contact Selector
        tk.Label(card, text="Select Party / Contact *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        contact_labels = [f"{c['name']} ({c['contact_type']}) - Bal: ₹{c['balance']:,.2f}" for c in self.contacts]
        self.contact_combo = ttk.Combobox(card, values=contact_labels, state="readonly", width=48)
        self.contact_combo.pack(anchor="w", pady=(0, 6))

        # Select initial contact if provided
        sel_idx = 0
        if self.initial_contact_id:
            for idx, c in enumerate(self.contacts):
                if c['id'] == self.initial_contact_id:
                    sel_idx = idx
                    break
        if contact_labels:
            self.contact_combo.current(sel_idx)

        # Current Balance Warning/Info Label
        self.bal_info_lbl = tk.Label(card, text="", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["accent"])
        self.bal_info_lbl.pack(anchor="w", pady=(0, 10))
        self.contact_combo.bind("<<ComboboxSelected>>", lambda e: self._on_contact_change())

        # 2. Payment Type (Payment In / Payment Out)
        tk.Label(card, text="Payment Type *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.type_combo = ttk.Combobox(card, values=PaymentModel.PAYMENT_TYPES, state="readonly", width=48)
        self.type_combo.current(0)
        self.type_combo.pack(anchor="w", pady=(0, 10))

        # 3. Payment Mode (Cash, UPI, Bank Transfer, Cheque, Card, Net Banking)
        tk.Label(card, text="Payment Method / Mode *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.mode_combo = ttk.Combobox(card, values=PaymentModel.PAYMENT_MODES, state="readonly", width=48)
        self.mode_combo.current(0)
        self.mode_combo.pack(anchor="w", pady=(0, 10))

        # 4. Amount & Date Row
        row_ad = tk.Frame(card, bg=COLORS["bg_card"])
        row_ad.pack(fill="x", pady=(0, 10))

        # Amount
        f_amt = tk.Frame(row_ad, bg=COLORS["bg_card"])
        f_amt.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Label(f_amt, text="Payment Amount (₹) *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        self.amt_entry = ttk.Entry(f_amt, width=20)
        self.amt_entry.insert(0, "0.00")
        self.amt_entry.pack(anchor="w", fill="x")

        # Date
        f_dt = tk.Frame(row_ad, bg=COLORS["bg_card"])
        f_dt.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(f_dt, text="Payment Date *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        self.date_entry = ttk.Entry(f_dt, width=20)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(anchor="w", fill="x")

        # 5. Reference / Txn No
        tk.Label(card, text="Txn / Ref / Cheque No.", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.ref_entry = ttk.Entry(card, width=48)
        self.ref_entry.pack(anchor="w", pady=(0, 10))

        # 6. Notes
        tk.Label(card, text="Notes / Description", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 1))
        self.notes_entry = ttk.Entry(card, width=48)
        self.notes_entry.pack(anchor="w", pady=(0, 10))

        # Initial trigger
        self._on_contact_change()

    def _on_contact_change(self):
        c_idx = self.contact_combo.current()
        if c_idx >= 0 and c_idx < len(self.contacts):
            contact = self.contacts[c_idx]
            bal = contact.get('balance', 0.0)
            c_type = contact.get('contact_type', 'Customer')

            if self.default_type:
                self.type_combo.set(self.default_type)
            elif c_type == 'Customer':
                self.type_combo.set('Payment In')
            else:
                self.type_combo.set('Payment Out')

            if c_type == 'Customer':
                self.bal_info_lbl.config(text=f"📌 Current Receivable Balance: ₹ {bal:,.2f}", fg=COLORS["warning"] if bal > 0 else COLORS["success"])
            else:
                self.bal_info_lbl.config(text=f"📌 Current Payable Balance: ₹ {bal:,.2f}", fg=COLORS["danger"] if bal > 0 else COLORS["success"])

    def _save(self):
        c_idx = self.contact_combo.current()
        if c_idx < 0 or c_idx >= len(self.contacts):
            messagebox.showerror("Error", "Please select a valid party / contact!", parent=self)
            return

        contact = self.contacts[c_idx]
        p_type = self.type_combo.get()
        p_mode = self.mode_combo.get()
        p_date = self.date_entry.get().strip()
        ref_no = self.ref_entry.get().strip()
        notes = self.notes_entry.get().strip()

        try:
            amount = float(self.amt_entry.get().strip())
            if amount <= 0:
                messagebox.showerror("Error", "Payment amount must be greater than zero!", parent=self)
                return

            payment_data = {
                'contact_id': contact['id'],
                'payment_type': p_type,
                'payment_mode': p_mode,
                'amount': amount,
                'payment_date': p_date,
                'reference_no': ref_no,
                'notes': notes
            }

            PaymentModel.create(payment_data)

            if self.on_save:
                self.on_save()

            messagebox.showinfo("Payment Recorded", f"Payment of ₹{amount:,.2f} via {p_mode} recorded successfully!", parent=self.master)
            self.destroy()

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric payment amount!", parent=self)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to record payment: {str(ex)}", parent=self)


class PartyLedgerDialog(tk.Toplevel):
    def __init__(self, parent, contact_id=None, on_close=None):
        super().__init__(parent)
        self.title("📜 Party Ledger Statement")
        self.geometry("880x660")
        self.minsize(780, 520)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self.on_close = on_close
        self.contacts = ContactModel.get_all()
        self.selected_contact_id = contact_id or (self.contacts[0]['id'] if self.contacts else None)

        self._build_ui()
        self.load_ledger()

    def _build_ui(self):
        # Header Toolbar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=14)
        h_frame.pack(fill="x", side="top")

        tk.Label(h_frame, text="📜 Party Ledger Statement (खाता विवरण)", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(side="left")

        # Contact Selector in Header
        tk.Label(h_frame, text="Select Party:", font=FONTS["small"], bg=COLORS["bg_header"], fg=COLORS["text_muted"]).pack(side="left", padx=(20, 5))
        c_names = [f"{c['name']} ({c['contact_type']})" for c in self.contacts]
        self.c_combo = ttk.Combobox(h_frame, values=c_names, state="readonly", width=30)
        self.c_combo.pack(side="left", padx=5)
        
        # Set current contact index
        if self.selected_contact_id:
            for idx, c in enumerate(self.contacts):
                if c['id'] == self.selected_contact_id:
                    self.c_combo.current(idx)
                    break
        elif c_names:
            self.c_combo.current(0)

        self.c_combo.bind("<<ComboboxSelected>>", lambda e: self._on_party_changed())

        # Top Summary Bar Card
        summary_card = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        summary_card.pack(fill="x", padx=20, pady=10)

        self.lbl_party_name = tk.Label(summary_card, text="", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"])
        self.lbl_party_name.pack(anchor="w")

        self.lbl_stats = tk.Label(summary_card, text="", font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_stats.pack(anchor="w", pady=(2, 0))

        # Ledger Table Box
        tbl_frame = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        tbl_frame.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("date", "Date", 100, "center"),
            ("ref_no", "Ref / Voucher No", 140, "center"),
            ("txn_type", "Transaction Type", 180, "w"),
            ("debit", "Debit (₹)", 110, "e"),
            ("credit", "Credit (₹)", 110, "e"),
            ("balance", "Running Balance (₹)", 140, "e")
        ]
        self.table = DataTable(tbl_frame, cols)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom Action Bar
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Close", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💳 Record Payment for Party", style="Primary.TButton", command=self._record_payment_for_party).pack(side="right", padx=5)

    def _on_party_changed(self):
        c_idx = self.c_combo.current()
        if c_idx >= 0 and c_idx < len(self.contacts):
            self.selected_contact_id = self.contacts[c_idx]['id']
            self.load_ledger()

    def load_ledger(self):
        if not self.selected_contact_id:
            return

        ledger_data = PaymentModel.get_party_ledger(self.selected_contact_id)
        if not ledger_data:
            return

        contact = ledger_data['contact']
        c_type = contact['contact_type']
        tot_billed = ledger_data['total_billed']
        tot_paid = ledger_data['total_paid_received']
        net_bal = ledger_data['net_balance']

        self.lbl_party_name.config(text=f"👤 {contact['name']}  |  {contact.get('company_name') or 'N/A'}  ({c_type})")
        
        bal_label_txt = "Receivable Dues" if c_type == 'Customer' else "Payable Dues"
        self.lbl_stats.config(text=f"Total Billed/Invoiced: ₹ {tot_billed:,.2f}  |  Total Received/Paid: ₹ {tot_paid:,.2f}  |  Net {bal_label_txt}: ₹ {net_bal:,.2f}")

        display_rows = []
        for r in ledger_data['rows']:
            row = dict(r)
            row['debit'] = f"₹ {r['debit']:,.2f}" if r['debit'] > 0 else "-"
            row['credit'] = f"₹ {r['credit']:,.2f}" if r['credit'] > 0 else "-"
            row['balance'] = f"₹ {r['balance']:,.2f}"
            display_rows.append(row)

        self.table.load_data(display_rows)

    def _record_payment_for_party(self):
        PaymentDialog(self, contact_id=self.selected_contact_id, on_save=self.load_ledger)

