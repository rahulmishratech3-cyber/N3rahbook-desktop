# 💼 N3RAH BOOK — Commercial Selling & Client Deployment Guide

**N3RAH BOOK (Enterprise Billing & Inventory Solutions)** is a production-ready, high-performance desktop application designed for small-to-medium enterprises, retail stores, wholesale traders, and manufacturers.

---

## 🚀 Key Commercial Features

1. **Complete GST Billing & Invoicing**:
   * Professional A4 Tax Invoice printing with exact compliance.
   * Auto-calculated **CGST (9%)**, **SGST (9%)**, **IGST**, Subtotals, and Rounding Off.
   * Auto-converts total invoice amounts into words (e.g., *Seven Thousand Two Hundred Rupees Only*).
   * Supports **Vehicle No.**, **Place of Supply**, **HSN/SAC Codes**, and **2-Level Tax Summaries**.

2. **Smart Inventory & Stock Control**:
   * Real-time stock level tracking with automated deduction on confirmed sales.
   * Automatic stock restoration when an invoice is deleted or cancelled.
   * Stock audit adjustments (`Add` / `Remove` items with reason codes).

3. **Multi-Role User Credentials & Access Control**:
   * 👑 **Admin**: Full access to all business configuration, user management, and financials.
   * 💼 **Manager**: Inventory, Billing, Purchase Orders, and Reports.
   * 🧾 **Biller / Sales Agent**: Quick invoice generation, customer directory, and PDF export.
   * 📦 **Storekeeper**: Inventory stock catalog and stock level adjustments.

4. **Custom Client Business Profile**:
   * Clients can easily set their own Business Name, Address, GSTIN, PAN, Phone, Email, Bank details, and Custom Invoice Terms under the **"⚙️ Settings & Profile"** screen.

---

## 📦 How to Onboard & Deploy to a New Client (Party)

When you sell this application to a new client:

### Step 1: Initialize New Client Database
Run the setup utility to generate clean database tables with the client's initial credentials:
```cmd
python setup_client.py
```
* Enter Client Business Name (e.g. `Gupta Trading Company`).
* Set initial Admin password.

### Step 2: Package Standalone `.exe` Executable
Build a single distribution folder so the client does **NOT** need Python installed:
```cmd
python build_exe.py
```
* Copy the output directory `dist/N3RAH_BOOK/` onto a USB drive or ZIP file for the client.

### Step 3: Client Handover & Login
* Give the client `dist/N3RAH_BOOK/N3RAH_BOOK.exe`.
* Default Admin Login:
  * **Username**: `admin`
  * **Password**: `admin123` (or custom set during setup)

---

## 🗄️ Database Backup & Maintenance

* Database file: `inventory_system.db`
* To back up a client's data, simply copy `inventory_system.db` to a backup folder or Google Drive.
* Generated PDF Invoices are stored in `generated_invoices/`.

---

## 🔒 Security & Data Ownership
* 100% Offline & Private: No cloud connection required. All client data stays securely on their local system.
