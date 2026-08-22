"""
N3RAH BOOK — Standalone Windows Setup & Installation Wizard
Packages all application files and installs them to target PC with Desktop Shortcuts.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

def create_windows_shortcut(target_path, shortcut_path, description="N3RAH BOOK Billing"):
    """
    Creates a Windows Desktop / Start Menu shortcut using PowerShell.
    """
    try:
        ps_script = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target_path}"
        $Shortcut.WorkingDirectory = "{os.path.dirname(target_path)}"
        $Shortcut.Description = "{description}"
        $Shortcut.Save()
        '''
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    except Exception as ex:
        print("Shortcut Error:", ex)


class InstallerWizard(tk.Tk):
    def __init__(self, data_zip_path=None):
        super().__init__()
        self.title("N3RAH BOOK — Setup Wizard")
        self.geometry("560x420")
        self.resizable(False, False)
        self.configure(bg="#F8FAFC")

        self.data_zip_path = data_zip_path or self._find_data_zip()
        self.dest_path_var = tk.StringVar(value=r"C:\N3RAH_BOOK")
        self.create_desktop_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _find_data_zip(self):
        # When bundled with PyInstaller
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        data_zip = os.path.join(base_dir, "app_payload.zip")
        return data_zip if os.path.exists(data_zip) else None

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg="#4F46E5", padx=25, pady=18)
        header.pack(fill="x")

        tk.Label(
            header,
            text="N3RAH BOOK — Setup Wizard",
            font=("Segoe UI", 16, "bold"),
            bg="#4F46E5",
            fg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Enterprise Billing & Inventory Management System",
            font=("Segoe UI", 10),
            bg="#4F46E5",
            fg="#E0E7FF"
        ).pack(anchor="w", pady=(2, 0))

        # Main Content Area
        content = tk.Frame(self, bg="#F8FAFC", padx=25, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="Select Installation Directory:",
            font=("Segoe UI", 11, "bold"),
            bg="#F8FAFC",
            fg="#0F172A"
        ).pack(anchor="w", pady=(0, 5))

        path_frame = tk.Frame(content, bg="#F8FAFC")
        path_frame.pack(fill="x", pady=(0, 15))

        self.path_entry = ttk.Entry(path_frame, textvariable=self.dest_path_var, width=42)
        self.path_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)

        ttk.Button(path_frame, text="📁 Browse", command=self._browse_folder).pack(side="right")

        # Shortcuts Options
        tk.Label(
            content,
            text="Installation Options:",
            font=("Segoe UI", 11, "bold"),
            bg="#F8FAFC",
            fg="#0F172A"
        ).pack(anchor="w", pady=(10, 5))

        chk_desk = tk.Checkbutton(
            content,
            text="Create Desktop Shortcut (N3RAH BOOK.lnk)",
            variable=self.create_desktop_var,
            bg="#F8FAFC",
            fg="#0F172A",
            activebackground="#F8FAFC",
            font=("Segoe UI", 10)
        )
        chk_desk.pack(anchor="w", pady=2)

        # Progress Bar
        self.progress = ttk.Progressbar(content, mode="determinate", length=480)
        self.progress.pack(fill="x", pady=(20, 5))

        self.status_lbl = tk.Label(
            content,
            text="Ready to install N3RAH BOOK to your system.",
            font=("Segoe UI", 9),
            bg="#F8FAFC",
            fg="#64748B"
        )
        self.status_lbl.pack(anchor="w")

        # Action Buttons (Pinned to Bottom)
        btn_bar = tk.Frame(self, bg="#FFFFFF", padx=20, pady=12, bd=1, relief="flat")
        btn_bar.pack(fill="x", side="bottom")

        ttk.Button(btn_bar, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        self.install_btn = ttk.Button(btn_bar, text="🚀 Install Now", command=self._start_install)
        self.install_btn.pack(side="right", padx=5)

    def _browse_folder(self):
        folder = filedialog.askdirectory(parent=self, title="Select Installation Folder")
        if folder:
            self.dest_path_var.set(folder)

    def _start_install(self):
        dest_dir = self.dest_path_var.get().strip()
        if not dest_dir:
            messagebox.showerror("Error", "Please select a valid installation path!", parent=self)
            return

        if not self.data_zip_path or not os.path.exists(self.data_zip_path):
            messagebox.showerror("Installer Error", "Installation payload not found!", parent=self)
            return

        self.install_btn.config(state="disabled")
        self.status_lbl.config(text="Extracting application files...", fg="#4F46E5")
        self.progress['value'] = 20
        self.update_idletasks()

        try:
            os.makedirs(dest_dir, exist_ok=True)

            with zipfile.ZipFile(self.data_zip_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)

            self.progress['value'] = 70
            self.status_lbl.config(text="Creating Shortcuts...", fg="#4F46E5")
            self.update_idletasks()

            exe_path = os.path.join(dest_dir, "N3RAH_BOOK.exe")

            # Create Desktop Shortcut
            if self.create_desktop_var.get() and os.path.exists(exe_path):
                desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_folder, "N3RAH BOOK.lnk")
                create_windows_shortcut(exe_path, shortcut_path)

            self.progress['value'] = 100
            self.status_lbl.config(text="[SUCCESS] Installation Completed Successfully!", fg="#10B981")

            confirm = messagebox.askyesno(
                "Setup Completed",
                f"N3RAH BOOK has been installed successfully to:\n{dest_dir}\n\nWould you like to launch N3RAH BOOK now?",
                parent=self
            )

            if confirm and os.path.exists(exe_path):
                if os.name == 'nt':
                    os.startfile(exe_path)
                else:
                    subprocess.Popen([exe_path])

            self.destroy()
        except Exception as ex:
            self.status_lbl.config(text=f"Installation Failed: {str(ex)}", fg="#EF4444")
            messagebox.showerror("Installation Error", f"Failed to install: {str(ex)}", parent=self)
            self.install_btn.config(state="normal")


if __name__ == "__main__":
    app = InstallerWizard()
    app.mainloop()
