# N3RAH BOOK - Desktop Architecture & Feature Plan

This document outlines the complete architectural design and feature set currently implemented in the **N3RAH BOOK** (Enterprise Billing & Inventory Solutions) desktop application.

---

## 1. Core Architecture

The desktop application follows a modular, robust Monolithic Architecture built for local speed with cloud-sync capabilities.

*   **Language:** Python 3
*   **UI Framework:** CustomTkinter / Tkinter (with `ui/views` and `ui/components` structure)
*   **Local Database:** SQLite (`inventory_system.db`) for zero-latency local operations
*   **Cloud Synchronization:** PostgreSQL integration via `cloud_db_service.py` to sync local SQLite data to the cloud (which powers the mobile app).
*   **Packaging:** PyInstaller (compiled via `build_exe.py` and `build_installer.py`) to create standalone Windows executables.

---

## 2. Database Schema & Data Models

The system is highly normalized to handle Indian accounting and inventory standards.

### Core Tables
1.  **`users`**: Manages authentication (Admin/User), password hashing, and active sessions.
2.  **`company_profile`**: Stores the root organization's metadata (Name, GSTIN, PAN, Udyam Reg, Bank Details, Terms) used in invoice headers.
3.  **`fiscal_years`**: Manages financial years (e.g., "2026-2027"), allowing the user to close a year and track aggregate totals.

### Master Data
4.  **`contacts`**: A unified CRM for both `Customer` and `Supplier` types. Tracks GSTIN, PAN, Place of Supply, and running balances.
5.  **`items`**: The core inventory ledger. Tracks SKU, Barcode, HSN Code, Unit type (KGS/PCS), Cost, Selling Price, Current Stock, Reorder Levels, and Tax Rates (GST).

### Transactions
6.  **`sales_orders` & `sales_order_items`**: Manages Tax Invoices. Includes deep tax breakdowns (CGST, SGST, IGST), freight, round-offs, vehicle numbers, e-way bills, and payment status.
7.  **`purchase_orders` & `purchase_order_items`**: Outbound purchase orders to suppliers.
8.  **`customer_pos` & `customer_po_items`**: Tracking inbound Customer Purchase Orders.
9.  **`customer_po_dispatches`**: Tracks partial or full dispatches against a Customer PO.
10. **`stock_adjustments`**: Audit trails for manually adding or removing stock (shrinkage/damages).
11. **`payments`**: Accounts Receivable/Payable tracking. Links Payments (In/Out) to specific Sales or Purchase Orders using various modes (Cash, UPI, Cheque, etc.).

---

## 3. Implemented Modules & Features

Based on the codebase analysis, the following modules are fully implemented in the Desktop version:

### 📊 Dashboard (`dashboard_view.py`)
*   Real-time Key Performance Indicators (KPIs).
*   Visual metrics for Total Revenue, Stock Value, Pending Orders, and Low Stock Alerts.

### 📦 Inventory & Stock (`items_view.py`, `stock_view.py`)
*   **Item Master:** Full CRUD operations for products.
*   **Stock Ledger:** Tracking inward/outward movement.
*   **Low Stock Management:** Automated flagging when stock dips below the `reorder_level`.

### 👥 CRM / Contacts (`contacts_view.py`)
*   Customer and Supplier onboarding.
*   Automated place of supply tagging (crucial for IGST vs CGST/SGST determination).

### 🧾 Invoicing & Sales (`sales_view.py`, `pdf_service.py`)
*   B2B & B2C Tax Invoice generation.
*   **Smart Tax Engine:** Automatically splits GST into CGST/SGST (intra-state) or IGST (inter-state) based on the contact's Place of Supply.
*   **PDF Generation:** Highly customized, professional PDF invoices (`pdf_service.py`) complete with "Amount in Words" auto-translation (`num2words_service.py`).

### 🛒 Purchasing & PO Tracking (`purchase_view.py`, `customer_po_view.py`)
*   Supplier PO creation.
*   Customer PO Tracking: Allows the business to receive a large PO from a client and track multiple partial deliveries/dispatches against it over time.

### 💳 Financials (`payments_view.py`)
*   Recording inward payments from customers against invoices.
*   Recording outward payments to suppliers.
*   Cashflow tracking across multiple payment methods.

### 📈 Reporting & Exports (`reports_view.py`)
*   Comprehensive data table views of all ledgers.
*   **Excel Import/Export:** Powerful utilities (`excel_import_service.py`, `export_service.py`) to bulk-upload items or contacts from Excel, and export reports for the CA/Accountant.

### 🤖 Advanced Automations (The "Magic" Features)
*   **Gmail Integration (`gmail_service.py`)**: Connects to the business's Gmail account using App Passwords.
*   **AI PO Parsing (`po_parser_service.py`)**: Automatically scans incoming emails for Purchase Orders (using keywords), parses the attached PDFs/text, and imports them directly into the database as pending orders (`processed_email_pos`).
*   **Cloud Bridge (`cloud_db_service.py`)**: Seamlessly pushes local SQLite data up to a managed Postgres instance, keeping the mobile app instantly in sync with the desktop terminal.
*   **Automated Backups (`backup_service.py`)**: Generates secure local `.zip` backups of the SQLite database to prevent data loss.

---

## 4. Technology Stack Summary
*   **Core UI:** `customtkinter` (Modern Tkinter)
*   **Data Processing:** `pandas` (for Excel imports/exports)
*   **PDF Engine:** `reportlab` or similar PDF canvas libraries.
*   **Email Engine:** `imaplib` / `email` modules.
*   **Cloud DB Layer:** `psycopg2` / `SQLAlchemy` (for Postgres connection).

This architecture provides an incredibly powerful, offline-first billing system for the desktop, while maintaining a tether to the cloud for mobile access and email automation.
