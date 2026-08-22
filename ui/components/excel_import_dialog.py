"""
Excel & CSV Import GUI Dialog Component
Supports selecting single or MULTIPLE Excel/CSV files simultaneously for batch import.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import COLORS, FONTS
from services.excel_import_service import ExcelImportService
from ui.components.data_table import DataTable

class ExcelImportDialog(tk.Toplevel):
    def __init__(self, parent, default_type="sales", on_success=None):
        super().__init__(parent)
        self.default_type = default_type
        self.on_success = on_success
        self.selected_file_paths = []

        self.title("📥 Import GST Data from Excel / CSV (Multi-File)")
        self.geometry("860x680")
        self.minsize(740, 580)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=COLORS["bg_header"], padx=20, pady=12)
        h_frame.pack(fill="x", side="top")

        tk.Label(h_frame, text="📥 Bulk Import Data from Excel / CSV (Multi-File Select)", font=FONTS["heading"], bg=COLORS["bg_header"], fg=COLORS["text_light"]).pack(anchor="w")

        # Bottom Buttons
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=5)
        self.btn_import = ttk.Button(btn_frame, text="🚀 Import Selected Files Now", style="Primary.TButton", command=self._execute_import, state="disabled")
        self.btn_import.pack(side="right", padx=5)

        # Form Controls
        form = tk.Frame(self, bg=COLORS["bg_dark"], padx=20, pady=10)
        form.pack(fill="both", expand=True)

        # 1. File Picker & Category Frame
        top_box = tk.Frame(form, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=12)
        top_box.pack(fill="x", pady=(0, 10))

        # Import Type Selector
        tk.Label(top_box, text="Select Data Type to Import:", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        
        type_options = ["📄 Sales Invoices / GSTR-1", "📦 Product & Items Catalog", "👥 Customers & Vendors Directory"]
        self.type_combo = ttk.Combobox(top_box, values=type_options, state="readonly", width=32)
        
        type_idx = 0
        if self.default_type == "items":
            type_idx = 1
        elif self.default_type == "contacts":
            type_idx = 2
            
        self.type_combo.current(type_idx)
        self.type_combo.grid(row=1, column=0, sticky="w", padx=4, pady=(0, 8))

        # File Selection Row (Multi-Select Support)
        tk.Label(top_box, text="Select Excel / CSV File(s) (Multi-Select Allowed) *", font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).grid(row=0, column=1, sticky="w", padx=4, pady=2)
        
        file_row = tk.Frame(top_box, bg=COLORS["bg_card"])
        file_row.grid(row=1, column=1, sticky="w", padx=4, pady=(0, 8))

        self.file_entry = ttk.Entry(file_row, width=34)
        self.file_entry.pack(side="left", padx=(0, 4))

        ttk.Button(file_row, text="📁 Select File(s)...", style="Secondary.TButton", command=self._browse_files).pack(side="left")

        # Multi-file count label badge
        self.lbl_file_count = tk.Label(top_box, text="No files selected", font=FONTS["small_bold"], bg=COLORS["bg_card"], fg=COLORS["warning"])
        self.lbl_file_count.grid(row=2, column=1, sticky="w", padx=4, pady=(0, 4))

        # 2. Excel Sheet Preview Table Frame
        prev_box = tk.Frame(form, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        prev_box.pack(fill="both", expand=True)

        self.lbl_preview_title = tk.Label(prev_box, text="🔍 Sheet Data Preview (No File Selected)", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_light"])
        self.lbl_preview_title.pack(anchor="w", pady=(0, 6))

        # Preview Container
        self.table_container = tk.Frame(prev_box, bg=COLORS["bg_card"])
        self.table_container.pack(fill="both", expand=True)

        self.preview_table = None

    def _browse_files(self):
        fpaths = filedialog.askopenfilenames(
            title="Select One or Multiple Excel / CSV Files",
            filetypes=[("Excel & CSV Files", "*.xlsx *.xls *.csv"), ("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv"), ("All Files", "*.*")],
            parent=self
        )
        if fpaths:
            self.selected_file_paths = list(fpaths)
            file_names = [os.path.basename(f) for f in self.selected_file_paths]
            
            if len(self.selected_file_paths) == 1:
                display_txt = self.selected_file_paths[0]
                badge_txt = "📁 1 File Selected"
            else:
                display_txt = f"{len(self.selected_file_paths)} Files: " + ", ".join(file_names)
                badge_txt = f"📁 {len(self.selected_file_paths)} Files Selected for Batch Import!"

            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, display_txt)
            self.lbl_file_count.config(text=badge_txt, fg=COLORS["success"])
            self.btn_import.config(state="normal")
            
            # Preview first selected file
            self._load_file_preview(self.selected_file_paths[0])

    def _load_file_preview(self, fpath):
        try:
            rows = ExcelImportService.read_sheet_data(fpath, max_rows=15)
            if not rows:
                self.lbl_preview_title.config(text="⚠️ Selected Excel file is empty.")
                return

            fname = os.path.basename(fpath)
            prefix = f"Multi-File Batch (Showing preview for 1st file: {fname})" if len(self.selected_file_paths) > 1 else f"Preview ({fname})"
            self.lbl_preview_title.config(text=f"🔍 {prefix} - First {len(rows)-1} Rows:")

            # Build preview table dynamically
            if self.preview_table:
                self.preview_table.destroy()

            headers = rows[0]
            cols = []
            for idx, h in enumerate(headers):
                c_name = str(h).strip() or f"Col_{idx+1}"
                cols.append((f"col_{idx}", c_name, 120, "w"))

            self.preview_table = DataTable(self.table_container, cols)
            self.preview_table.pack(fill="both", expand=True)

            data_rows = []
            for r in rows[1:]:
                row_dict = {}
                for idx in range(len(headers)):
                    val = str(r[idx]).strip() if idx < len(r) else ""
                    row_dict[f"col_{idx}"] = val
                data_rows.append(row_dict)

            self.preview_table.load_data(data_rows)

        except Exception as ex:
            messagebox.showerror("File Error", f"Failed to read Excel file preview: {str(ex)}", parent=self)

    def _execute_import(self):
        if not self.selected_file_paths:
            messagebox.showerror("Error", "Please select at least one Excel or CSV file.", parent=self)
            return

        import_type_idx = self.type_combo.current()

        total_imported = 0
        total_skipped = 0
        failed_files = []

        try:
            for fpath in self.selected_file_paths:
                if not os.path.exists(fpath):
                    failed_files.append((os.path.basename(fpath), "File not found"))
                    continue

                if import_type_idx == 0:
                    res = ExcelImportService.import_sales_invoices(fpath)
                elif import_type_idx == 1:
                    res = ExcelImportService.import_products(fpath)
                else:
                    res = ExcelImportService.import_contacts(fpath)

                if res.get('success'):
                    total_imported += res.get('count', 0)
                else:
                    failed_files.append((os.path.basename(fpath), res.get('message', 'Unknown error')))

            # Formulate multi-file summary result
            num_files = len(self.selected_file_paths)
            summary_msg = f"🎉 Multi-File Batch Import Completed!\n\n"
            summary_msg += f"• Files Processed: {num_files}\n"
            summary_msg += f"• Total Records Imported: {total_imported}\n"

            if failed_files:
                summary_msg += f"\n⚠️ Failed/Skipped Files ({len(failed_files)}):\n"
                for fname, err in failed_files:
                    summary_msg += f"  - {fname}: {err}\n"

            messagebox.showinfo("Batch Import Complete", summary_msg, parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as ex:
            messagebox.showerror("Batch Import Error", f"Exception during batch import: {str(ex)}", parent=self)
