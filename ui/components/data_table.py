"""
Reusable Styled Treeview Data Table Component
Supports column sorting, custom row formatting, and scrollbars.
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS

class DataTable(tk.Frame):
    def __init__(self, parent, columns, show_select=True, on_double_click=None):
        super().__init__(parent, bg=COLORS["bg_card"])
        self.columns = columns
        self.on_double_click = on_double_click
        self.sort_desc = {}

        self._build_ui()

    def _build_ui(self):
        # Scrollbars
        v_scroll = ttk.Scrollbar(self, orient="vertical")
        v_scroll.pack(side="right", fill="y")

        h_scroll = ttk.Scrollbar(self, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        # Treeview
        col_keys = [c[0] for c in self.columns]
        self.tree = ttk.Treeview(
            self,
            columns=col_keys,
            show="headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            selectmode="extended"
        )
        self.tree.pack(fill="both", expand=True)

        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        # Configure columns
        for key, heading, width, anchor in self.columns:
            self.tree.heading(
                key,
                text=heading,
                anchor=anchor,
                command=lambda k=key: self._sort_column(k)
            )
            self.tree.column(key, width=width, anchor=anchor)
            self.sort_desc[key] = False

        # Configure alternating tags
        self.tree.tag_configure("even", background=COLORS["bg_card"])
        self.tree.tag_configure("odd", background=COLORS["bg_card_alt"])
        self.tree.tag_configure("low_stock", foreground=COLORS["warning"])
        self.tree.tag_configure("out_stock", foreground=COLORS["danger"])
        self.tree.tag_configure("paid", foreground=COLORS["success"])
        self.tree.tag_configure("unpaid", foreground=COLORS["danger"])
        self.tree.tag_configure("cancelled", foreground=COLORS["text_muted"])

        # Multi-select keyboard shortcut (Ctrl+A / Ctrl+a)
        self.tree.bind("<Control-a>", self._select_all_event)
        self.tree.bind("<Control-A>", self._select_all_event)

        if self.on_double_click:
            self.tree.bind("<Double-1>", lambda e: self.on_double_click(self.get_selected_item()))

    def _select_all_event(self, event=None):
        self.select_all()
        return "break"

    def select_all(self):
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())


    def load_data(self, rows):
        self.clear()
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            
            if 'row_tag' in row and row['row_tag']:
                tag = row['row_tag']
            elif 'current_stock' in row and 'reorder_level' in row:
                stock = float(row['current_stock'])
                reorder = float(row['reorder_level'])
                if stock <= 0:
                    tag = "out_stock"
                elif stock <= reorder:
                    tag = "low_stock"

            values = [row.get(c[0], "") for c in self.columns]
            self.tree.insert("", "end", iid=str(row.get('id', idx)), values=values, tags=(tag,))

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_selected_items(self):
        selected = self.tree.selection()
        if not selected:
            return []
        items = []
        for item_id in selected:
            values = self.tree.item(item_id, "values")
            res = {'id': item_id}
            for idx, col in enumerate(self.columns):
                if idx < len(values):
                    res[col[0]] = values[idx]
            items.append(res)
        return items

    def get_selected_item(self):
        items = self.get_selected_items()
        return items[0] if items else None


    def _sort_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        desc = self.sort_desc[col]
        
        # Try numeric sorting if possible
        try:
            items.sort(key=lambda t: float(t[0].replace('₹', '').replace(',', '').strip()), reverse=desc)
        except ValueError:
            items.sort(reverse=desc)

        for index, (val, k) in enumerate(items):
            self.tree.move(k, '', index)

        self.sort_desc[col] = not desc
