"""
Incoming Email PO Review & Import Dialog
Displays Purchase Orders fetched from Gmail PDF attachments, allowing user to review, edit, preview PDF, and 1-click import into Customer PO tracker.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.contact import ContactModel
from models.item import ItemModel
from models.customer_po import CustomerPOModel
from services.po_parser_service import POParserService
from services.gmail_service import GmailSyncService
from services.num2words_service import number_to_words_indian

class IncomingPODialog(tk.Toplevel):
    def __init__(self, parent, fetched_emails, on_imported=None):
        super().__init__(parent)
        self.fetched_emails = fetched_emails or []
        self.on_imported = on_imported
        self.parsed_pos = []
        self.current_index = 0

        self.title("📥 Incoming Gmail Purchase Orders (PDF Review)")
        self.geometry("1050x760")
        self.minsize(950, 680)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self._load_reference_data()
        self._parse_all_emails()
        self._build_ui()
        if self.parsed_pos:
            self.po_listbox.selection_set(0)
            self._select_po(0)

    def _load_reference_data(self):
        self.customers = ContactModel.get_all()
        self.customer_names = []
        self.customer_map = {}
        for c in self.customers:
            comp = str(c.get('company_name') or '').strip()
            name = str(c.get('name') or '').strip()
            addr = str(c.get('address') or '').strip()
            label = comp if comp else name
            if comp and name and comp.lower() != name.lower():
                label = f"{comp} ({name})"
            if addr and addr.lower() != 'n/a':
                label += f" — 📍 {addr}"
            self.customer_names.append(label)
            self.customer_map[label] = c

        self.items = ItemModel.get_all()

    def _parse_all_emails(self):
        self.parsed_pos = []
        for em in self.fetched_emails:
            pdf_path = em.get('pdf_path')
            if pdf_path and os.path.exists(pdf_path):
                try:
                    parsed = POParserService.parse_po_pdf(
                        pdf_path=pdf_path,
                        sender_email=em.get('sender', ''),
                        sender_name=em.get('sender', ''),
                        email_subject=em.get('subject', '')
                    )
                    parsed['email_meta'] = em
                    parsed['is_imported'] = em.get('is_already_imported', False)
                    self.parsed_pos.append(parsed)
                except Exception as ex:
                    print(f"Error parsing PDF {pdf_path}: {ex}")

    def _build_ui(self):
        # 1. Header Bar
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x", side="top")

        tk.Label(h_frame, text="📥 Incoming Gmail Purchase Orders — PDF Review & Import", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(side="left")
        
        count_txt = f"{len(self.parsed_pos)} PO PDF(s) Found"
        tk.Label(h_frame, text=count_txt, font=FONTS["small_bold"], bg=COLORS["primary"], fg=COLORS["text_light"], padx=10, pady=4).pack(side="right")

        # 2. Main Content Container (Left: Email List, Right: PO Review Form)
        main_container = tk.Frame(self, bg=COLORS["bg_dark"])
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        # Left Listbox Frame (Fixed width sidebar)
        left_frame = tk.Frame(main_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=12, width=350)
        left_frame.pack(side="left", fill="y", padx=(0, 12))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="📁 Incoming PO Files", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(anchor="w", pady=(0, 4))

        # Search / Filter Box
        self.search_entry = ttk.Entry(left_frame, font=FONTS["small"])
        self.search_entry.pack(fill="x", pady=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._filter_list)

        list_container = tk.Frame(left_frame, bg=COLORS["bg_card"])
        list_container.pack(fill="both", expand=True)

        list_scroll = ttk.Scrollbar(list_container)
        self.po_listbox = tk.Listbox(
            list_container,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_light"],
            font=FONTS["small"],
            selectbackground=COLORS["primary"],
            selectforeground="white",
            highlightthickness=0,
            activestyle="none",
            bd=0,
            yscrollcommand=list_scroll.set
        )
        list_scroll.config(command=self.po_listbox.yview)
        
        self.po_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.po_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        self.filtered_indices = list(range(len(self.parsed_pos)))
        self._populate_listbox()

        # Right Form Container
        right_container = tk.Frame(main_container, bg=COLORS["bg_dark"])
        right_container.pack(side="left", fill="both", expand=True)

        # Email Info Strip
        self.email_info_card = tk.Frame(right_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=8)
        self.email_info_card.pack(fill="x", pady=(0, 8))

        self.lbl_email_from = tk.Label(self.email_info_card, text="From: -", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], anchor="w")
        self.lbl_email_from.pack(fill="x")
        self.lbl_email_subj = tk.Label(self.email_info_card, text="Subject: -", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"], anchor="w")
        self.lbl_email_subj.pack(fill="x")

        # PO Header Form Card
        form_card = tk.Frame(right_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=14, pady=10)
        form_card.pack(fill="x", pady=(0, 8))

        # Row 1: PO Number & PO Date & PDF Viewer Button
        r1 = tk.Frame(form_card, bg=COLORS["bg_card"])
        r1.pack(fill="x", pady=2)

        tk.Label(r1, text="PO Ref #:", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], width=10, anchor="w").pack(side="left")
        self.entry_po_num = ttk.Entry(r1, width=18, font=FONTS["body"])
        self.entry_po_num.pack(side="left", padx=(0, 15))

        tk.Label(r1, text="PO Date:", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], width=8, anchor="w").pack(side="left")
        self.entry_po_date = ttk.Entry(r1, width=12, font=FONTS["body"])
        self.entry_po_date.pack(side="left", padx=(0, 10))

        ttk.Button(r1, text="👁️ Open PDF", style="Secondary.TButton", command=self._open_pdf).pack(side="right")

        # Row 2: Customer / Party Selection
        r2 = tk.Frame(form_card, bg=COLORS["bg_card"])
        r2.pack(fill="x", pady=4)

        tk.Label(r2, text="Party/Client:", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], width=10, anchor="w").pack(side="left")
        self.combo_customer = ttk.Combobox(r2, values=self.customer_names, state="readonly", font=FONTS["body"])
        self.combo_customer.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # Row 3: Target Date & Notes
        r3 = tk.Frame(form_card, bg=COLORS["bg_card"])
        r3.pack(fill="x", pady=2)

        tk.Label(r3, text="Target Date:", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], width=10, anchor="w").pack(side="left")
        self.entry_target_date = ttk.Entry(r3, width=14, font=FONTS["body"])
        self.entry_target_date.pack(side="left", padx=(0, 15))

        tk.Label(r3, text="Notes/Remarks:", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], width=12, anchor="w").pack(side="left")
        self.entry_notes = ttk.Entry(r3, font=FONTS["body"])
        self.entry_notes.pack(side="left", fill="x", expand=True)

        # Line Items Table Frame
        items_frame = tk.Frame(right_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=10, pady=8)
        items_frame.pack(fill="both", expand=True, pady=(0, 8))

        it_top = tk.Frame(items_frame, bg=COLORS["bg_card"])
        it_top.pack(fill="x", pady=(0, 4))
        tk.Label(it_top, text="📦 Parsed Order Items (KG / Quantities)", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["text_light"]).pack(side="left")

        # Treeview for Items
        cols = ("item_name", "qty_kg", "unit", "unit_price", "total_amount")
        self.items_tree = ttk.Treeview(items_frame, columns=cols, show="headings", height=5)
        self.items_tree.heading("item_name", text="Item Name & Specification")
        self.items_tree.heading("qty_kg", text="Quantity (KG)")
        self.items_tree.heading("unit", text="Unit")
        self.items_tree.heading("unit_price", text="Rate (₹)")
        self.items_tree.heading("total_amount", text="Total (₹)")

        self.items_tree.column("item_name", width=260, anchor="w")
        self.items_tree.column("qty_kg", width=90, anchor="center")
        self.items_tree.column("unit", width=60, anchor="center")
        self.items_tree.column("unit_price", width=80, anchor="e")
        self.items_tree.column("total_amount", width=100, anchor="e")

        it_scroll = ttk.Scrollbar(items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=it_scroll.set)

        self.items_tree.pack(side="left", fill="both", expand=True)
        it_scroll.pack(side="right", fill="y")

        # Calculation Summary & Actions Footer
        footer_card = tk.Frame(right_container, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=12, pady=8)
        footer_card.pack(fill="x", side="bottom")

        # Summary Row
        sum_row = tk.Frame(footer_card, bg=COLORS["bg_card"])
        sum_row.pack(fill="x", pady=(0, 6))

        self.lbl_tot_ordered = tk.Label(sum_row, text="Total Ordered: 0.00 KG", font=FONTS["body_bold"], bg=COLORS["bg_card"], fg=COLORS["warning"])
        self.lbl_tot_ordered.pack(side="left")

        self.lbl_grand_total = tk.Label(sum_row, text="Grand Total: ₹ 0.00", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["success"])
        self.lbl_grand_total.pack(side="right")

        # Buttons Row
        btn_row = tk.Frame(footer_card, bg=COLORS["bg_card"])
        btn_row.pack(fill="x", pady=(4, 0))

        ttk.Button(btn_row, text="❌ Close", style="Secondary.TButton", command=self.destroy).pack(side="left")
        
        self.btn_import = ttk.Button(btn_row, text="✅ Approve & Import to Customer POs", style="Primary.TButton", command=self._import_current_po)
        self.btn_import.pack(side="right", padx=4)

    def _populate_listbox(self):
        self.po_listbox.delete(0, tk.END)
        for real_idx in self.filtered_indices:
            p = self.parsed_pos[real_idx]
            em = p.get('email_meta', {})
            status_icon = "✅" if p.get('is_imported') else "🆕"
            p_label = p.get('party_name', 'Customer')[:20]
            po_ref = p.get('po_number', 'PO')
            self.po_listbox.insert(tk.END, f"{status_icon} {po_ref} — {p_label}")

    def _filter_list(self, event=None):
        q = self.search_entry.get().strip().lower()
        if not q:
            self.filtered_indices = list(range(len(self.parsed_pos)))
        else:
            self.filtered_indices = []
            for idx, p in enumerate(self.parsed_pos):
                po_num = p.get('po_number', '').lower()
                party = p.get('party_name', '').lower()
                subj = p.get('email_meta', {}).get('subject', '').lower()
                if q in po_num or q in party or q in subj:
                    self.filtered_indices.append(idx)
        
        self._populate_listbox()
        if self.filtered_indices:
            self.po_listbox.selection_set(0)
            self._select_po(self.filtered_indices[0])

    def _on_listbox_select(self, event=None):
        sel = self.po_listbox.curselection()
        if sel and sel[0] < len(self.filtered_indices):
            real_index = self.filtered_indices[sel[0]]
            self._select_po(real_index)

    def _select_po(self, index):
        if not (0 <= index < len(self.parsed_pos)):
            return

        self.current_index = index
        po = self.parsed_pos[index]
        em = po.get('email_meta', {})

        # Email details
        self.lbl_email_from.config(text=f"✉️ From: {em.get('sender', '-')}")
        self.lbl_email_subj.config(text=f"📌 Subject: {em.get('subject', '-')} ({em.get('date', '')})")

        # Header fields
        self.entry_po_num.delete(0, tk.END)
        self.entry_po_num.insert(0, po.get('po_number', ''))

        self.entry_po_date.delete(0, tk.END)
        self.entry_po_date.insert(0, po.get('po_date', ''))

        self.entry_target_date.delete(0, tk.END)
        self.entry_target_date.insert(0, po.get('target_delivery_date', ''))

        self.entry_notes.delete(0, tk.END)
        self.entry_notes.insert(0, f"Auto-imported from Gmail attachment: {em.get('pdf_filename', '')}")

        # Customer selection
        cust_id = po.get('customer_id')
        selected = False
        if cust_id:
            for idx, c in enumerate(self.customers):
                if c['id'] == cust_id:
                    self.combo_customer.current(idx)
                    selected = True
                    break

        if not selected:
            # Try to match by party_name string
            p_name = po.get('party_name', '').lower()
            for idx, c in enumerate(self.customers):
                c_comp = str(c.get('company_name') or '').lower()
                c_name = str(c.get('name') or '').lower()
                if (c_comp and c_comp in p_name) or (c_name and c_name in p_name):
                    self.combo_customer.current(idx)
                    selected = True
                    break

        if not selected and self.customer_names:
            self.combo_customer.current(0)

        # Items treeview
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)

        tot_kg = 0.0
        tot_val = 0.0
        for it in po.get('items', []):
            q = float(it.get('ordered_qty_kg') or 0.0)
            r = float(it.get('unit_price') or 0.0)
            t = float(it.get('total_amount') or (q * r))
            tot_kg += q
            tot_val += t
            self.items_tree.insert("", tk.END, values=(
                it.get('item_name', ''),
                f"{q:,.2f}",
                it.get('unit', 'KG'),
                f"₹ {r:,.2f}",
                f"₹ {t:,.2f}"
            ))

        self.lbl_tot_ordered.config(text=f"Total Ordered: {tot_kg:,.2f} KG")
        self.lbl_grand_total.config(text=f"Grand Total: ₹ {tot_val:,.2f}")

        # Update Import button status
        if po.get('is_imported'):
            self.btn_import.config(text="⚠️ Already Imported (Re-Import)", style="Secondary.TButton")
        else:
            self.btn_import.config(text="✅ Approve & Import to Customer POs", style="Primary.TButton")

    def _open_pdf(self):
        if not self.parsed_pos:
            return
        po = self.parsed_pos[self.current_index]
        pdf_path = po.get('pdf_path')
        if pdf_path and os.path.exists(pdf_path):
            try:
                if os.name == 'nt':
                    os.startfile(pdf_path)
                else:
                    subprocess.run(['xdg-open', pdf_path])
            except Exception as e:
                messagebox.showerror("Error", f"PDF open nahi ho saki: {e}", parent=self)
        else:
            messagebox.showwarning("File Missing", "PDF attachment file nahi mili.", parent=self)

    def _import_current_po(self):
        if not self.parsed_pos:
            return

        po = self.parsed_pos[self.current_index]
        po_num = self.entry_po_num.get().strip()
        po_date = self.entry_po_date.get().strip()
        target_date = self.entry_target_date.get().strip()
        notes = self.entry_notes.get().strip()

        if not po_num:
            messagebox.showerror("Validation", "PO Number khali nahi ho sakta.", parent=self)
            return

        cust_idx = self.combo_customer.current()
        if cust_idx < 0 or cust_idx >= len(self.customers):
            messagebox.showerror("Validation", "Kripya Customer / Party select karein.", parent=self)
            return

        customer = self.customers[cust_idx]
        cust_id = customer['id']

        # Prepare line items
        items_data = []
        for it in po.get('items', []):
            q = float(it.get('ordered_qty_kg') or 0.0)
            r = float(it.get('unit_price') or 0.0)
            t = float(it.get('total_amount') or (q * r))
            
            # Map item_id
            item_id = it.get('item_id')
            if not item_id and self.items:
                item_id = self.items[0]['id']

            items_data.append({
                'item_id': item_id,
                'item_name': it.get('item_name', 'PU Foam'),
                'hsn_code': it.get('hsn_code', '3921'),
                'ordered_qty_kg': q,
                'unit': it.get('unit', 'KG'),
                'unit_price': r,
                'total_amount': t
            })

        subtotal = sum(i['total_amount'] for i in items_data)
        cgst = round(subtotal * 0.09, 2)
        sgst = round(subtotal * 0.09, 2)
        total_amt = round(subtotal + cgst + sgst)

        po_dict = {
            'po_number': po_num,
            'customer_id': cust_id,
            'po_date': po_date,
            'target_delivery_date': target_date,
            'subtotal': subtotal,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'gst_rate': 18.0,
            'total_po_amount': total_amt,
            'notes': notes
        }

        try:
            # Check if PO already exists in customer_pos
            from database.db_manager import db
            existing = db.fetch_one("SELECT id FROM customer_pos WHERE po_number = ?", (po_num,))
            if existing:
                resp = messagebox.askyesno("PO Exists", f"PO Number '{po_num}' pehle se inventory me mojood hai. Kya aap isse overwrite karna chahte hain?", parent=self)
                if not resp:
                    return
                # Update existing
                CustomerPOModel.update(existing['id'], po_dict, items_data)
            else:
                CustomerPOModel.create(po_dict, items_data)

            # Record in processed emails
            em = po.get('email_meta', {})
            GmailSyncService.record_processed_po(
                message_id=em.get('message_id', ''),
                sender=em.get('sender', ''),
                subject=em.get('subject', ''),
                received_date=em.get('date', ''),
                pdf_filename=em.get('pdf_filename', ''),
                po_number=po_num,
                customer_id=cust_id,
                status="Imported"
            )

            po['is_imported'] = True
            self.po_listbox.delete(self.current_index)
            self.po_listbox.insert(self.current_index, f"✅ {po_num} | {customer.get('name', '')[:18]}")
            self.po_listbox.selection_set(self.current_index)
            self.btn_import.config(text="✅ Successfully Imported!", style="Success.TButton")

            messagebox.showinfo("Success", f"Party PO '{po_num}' successfully Inventory me add ho gaya!", parent=self)

            if self.on_imported:
                self.on_imported()

        except Exception as ex:
            messagebox.showerror("Import Error", f"PO import karne me truti: {str(ex)}", parent=self)
