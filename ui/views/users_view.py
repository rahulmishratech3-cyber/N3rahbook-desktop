"""
User Credentials and Role Management View Screen
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from models.user import UserModel
from ui.components.data_table import DataTable
from ui.components.dialogs import UserDialog

class UsersView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        ctrl_bar = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, padx=15, pady=10)
        ctrl_bar.pack(fill="x", padx=20, pady=15)

        tk.Label(ctrl_bar, text="🔑 System Users & Role Credentials", font=FONTS["heading"], bg=COLORS["bg_card"], fg=COLORS["text_dark"]).pack(side="left")

        # Action Buttons
        ttk.Button(ctrl_bar, text="🗑️ Delete Account", style="Secondary.TButton", command=self._delete_user).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="✏️ Edit Credentials & Role", style="Secondary.TButton", command=self._edit_user).pack(side="right", padx=4)
        ttk.Button(ctrl_bar, text="➕ Create User Account", style="Primary.TButton", command=self._add_user).pack(side="right", padx=4)

        table_container = tk.Frame(self, bg=COLORS["bg_card"], bd=1, relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True, padx=20, pady=5)

        cols = [
            ("id", "User ID", 70, "center"),
            ("username", "Login Username", 160, "w"),
            ("full_name", "Full Name", 220, "w"),
            ("role", "Assigned Role", 150, "center"),
            ("status", "Account Status", 110, "center"),
            ("created_at", "Created On", 160, "center")
        ]
        self.table = DataTable(table_container, cols, on_double_click=self._edit_user)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_data(self):
        users = UserModel.get_all()
        self.table.load_data(users)

    def _add_user(self):
        UserDialog(self, on_save=self.refresh_data)

    def _edit_user(self, user_row=None):
        selected = user_row or self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a user account from the list.", parent=self)
            return

        user_data = UserModel.get_by_id(selected['id'])
        if user_data:
            UserDialog(self, user_data=user_data, on_save=self.refresh_data)

    def _delete_user(self):
        selected = self.table.get_selected_item()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a user account to delete.", parent=self)
            return

        if selected['username'] == 'admin':
            messagebox.showerror("Protected Account", "Default 'admin' account cannot be deleted!", parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete user account '{selected['username']}'?\nThis user will no longer be able to log in.",
            parent=self
        )
        if confirm:
            try:
                UserModel.delete_user(selected['id'])
                self.refresh_data()
                messagebox.showinfo("Success", f"User '{selected['username']}' deleted successfully!", parent=self)
            except Exception as ex:
                messagebox.showerror("Error", f"Failed to delete user: {str(ex)}", parent=self)
