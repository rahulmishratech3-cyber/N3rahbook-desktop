/**
 * N3RAH BOOK - Enterprise Web Application Client
 * Reactive SPA Engine, Real-time GST Billing, and Inventory Ledger
 */

class N3rahBookApp {
  constructor() {
    this.currentView = 'dashboard';
    this.itemsCache = [];
    this.contactsCache = [];
    this.categoriesCache = [];
    this.subcategoriesCache = {};
    this.invoiceRows = [];
    this.companyProfile = null;

    this.initTheme();
    this.initEventListeners();
    this.initRouter();
    this.loadInitialData();
  }

  // -------------------------------------------------------------
  // Theme Management
  // -------------------------------------------------------------
  initTheme() {
    const savedTheme = localStorage.getItem('n3rah_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.updateThemeIcon(savedTheme);
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('n3rah_theme', next);
    this.updateThemeIcon(next);
  }

  updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    if (theme === 'dark') {
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      icon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    }
  }

  // -------------------------------------------------------------
  // Event Listeners & Router
  // -------------------------------------------------------------
  initEventListeners() {
    // Theme toggle
    document.getElementById('themeToggleBtn')?.addEventListener('click', () => this.toggleTheme());

    // Sidebar collapse
    document.getElementById('sidebarCollapseBtn')?.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Mobile menu toggle & drawer
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    const toggleMobileSidebar = () => {
      const isOpen = sidebar?.classList.toggle('mobile-open');
      if (isOpen) {
        sidebarBackdrop?.classList.add('active');
      } else {
        sidebarBackdrop?.classList.remove('active');
      }
    };

    const closeMobileSidebar = () => {
      sidebar?.classList.remove('mobile-open');
      sidebarBackdrop?.classList.remove('active');
    };

    document.getElementById('mobileMenuBtn')?.addEventListener('click', toggleMobileSidebar);
    sidebarBackdrop?.addEventListener('click', closeMobileSidebar);

    // Navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        closeMobileSidebar();
        const view = item.getAttribute('data-view');
        if (view) this.navigateTo(view);
      });
    });

    // Global ESC key listener to close mobile menu or active modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeMobileSidebar();
      }
    });

    // Quick New Invoice button
    document.getElementById('quickNewInvoiceBtn')?.addEventListener('click', () => {
      this.openCreateInvoiceModal();
    });

    // Product search & filters
    document.getElementById('itemsSearchInput')?.addEventListener('input', () => this.loadItems());
    document.getElementById('itemsCategoryFilter')?.addEventListener('change', () => this.loadItems());
    document.getElementById('itemsStockFilter')?.addEventListener('change', () => this.loadItems());

    // Contact search & tabs
    document.getElementById('contactsSearchInput')?.addEventListener('input', () => this.loadContacts());
    document.querySelectorAll('#contactsTypeTabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#contactsTypeTabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.loadContacts();
      });
    });

    // Sales filters
    document.getElementById('salesSearchInput')?.addEventListener('input', () => this.loadSales());
    document.getElementById('salesStatusFilter')?.addEventListener('change', () => this.loadSales());

    // Payment filters
    document.getElementById('paymentsSearchInput')?.addEventListener('input', () => this.loadPayments());
    document.querySelectorAll('#paymentsTypeTabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#paymentsTypeTabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.loadPayments();
      });
    });

    // Forms submission handlers
    this.initForms();
  }

  initRouter() {
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      this.navigateTo(hash, null, false);
    });

    const initialView = window.location.hash.replace('#', '') || 'dashboard';
    this.navigateTo(initialView, null, false);
  }

  navigateTo(viewName, params = null, updateHash = true) {
    this.currentView = viewName;
    if (updateHash) {
      window.location.hash = viewName;
    }

    // Update active nav link
    document.querySelectorAll('.nav-item').forEach(item => {
      if (item.getAttribute('data-view') === viewName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Show view section
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.classList.add('active');
    }

    // Update page title
    const titles = {
      'dashboard': 'Dashboard Overview',
      'items': 'Products & Stock Inventory',
      'contacts': 'Customers & Suppliers CRM',
      'sales': 'Tax Invoices & Sales Orders',
      'purchases': 'Purchase Orders',
      'customer-pos': 'Customer Purchase Orders',
      'payments': 'Payments & Party Ledgers',
      'reports': 'GST Reports & Compliance',
      'company': 'Company Profile Settings',
      'users': 'User Account Management'
    };
    const titleEl = document.getElementById('pageTitle');
    if (titleEl) titleEl.textContent = titles[viewName] || 'N3RAH BOOK';

    // Load data for the selected view
    this.loadViewData(viewName, params);
  }

  loadViewData(viewName, params) {
    switch (viewName) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'items':
        if (params && params.stock_filter) {
          const filterEl = document.getElementById('itemsStockFilter');
          if (filterEl) filterEl.value = params.stock_filter;
        }
        this.loadItems();
        break;
      case 'contacts':
        this.loadContacts();
        break;
      case 'sales':
        this.loadSales();
        break;
      case 'purchases':
        this.loadPurchases();
        break;
      case 'customer-pos':
        this.loadCustomerPOs();
        break;
      case 'payments':
        this.loadPayments();
        break;
      case 'reports':
        this.loadReports();
        break;
      case 'company':
        this.loadCompanyProfile();
        break;
      case 'users':
        this.loadUsers();
        break;
    }
  }

  // -------------------------------------------------------------
  // Initial Global Data Load
  // -------------------------------------------------------------
  async loadInitialData() {
    try {
      const [metaRes, compRes, meRes] = await Promise.all([
        fetch('/api/items/meta'),
        fetch('/api/company'),
        fetch('/api/auth/me')
      ]);

      if (metaRes.ok) {
        const meta = await metaRes.json();
        this.categoriesCache = meta.categories || [];
        this.subcategoriesCache = meta.subcategories || {};
        this.populateCategoriesDropdown();
      }

      if (compRes.ok) {
        const comp = await compRes.json();
        this.companyProfile = comp.company || {};
      }

      if (meRes.ok) {
        const me = await meRes.json();
        const badge = document.getElementById('dbStatusBadge');
        const badgeText = document.getElementById('dbStatusText');
        if (badge && badgeText) {
          if (me.cloud_mode) {
            badge.className = 'cloud-status-badge cloud';
            badgeText.textContent = 'Cloud PostgreSQL';
          } else {
            badge.className = 'cloud-status-badge sqlite';
            badgeText.textContent = 'Local SQLite (Offline)';
          }
        }
      }
    } catch (err) {
      console.error('Initial data load error:', err);
    }
  }

  populateCategoriesDropdown() {
    const filterSelect = document.getElementById('itemsCategoryFilter');
    const formSelect = document.getElementById('itemCategory');
    if (!filterSelect || !formSelect) return;

    filterSelect.innerHTML = '<option value="All">All Categories</option>';
    formSelect.innerHTML = '<option value="">Select Category...</option>';

    this.categoriesCache.forEach(cat => {
      filterSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
      formSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
    });
  }

  // -------------------------------------------------------------
  // DASHBOARD VIEW
  // -------------------------------------------------------------
  async loadDashboard() {
    try {
      const res = await fetch('/api/dashboard');
      if (!res.ok) return;
      const data = await res.json();

      const kpi = data.kpi || {};
      document.getElementById('kpiRevenue').textContent = this.formatCurrency(kpi.monthly_revenue || 0);
      document.getElementById('kpiStockValuation').textContent = this.formatCurrency(kpi.total_stock_value || 0);
      document.getElementById('kpiLowStock').textContent = `${kpi.low_stock_count || 0} Items`;
      document.getElementById('kpiContactsCount').textContent = `${data.counts?.contacts || 0} Parties`;
      document.getElementById('kpiItemsCount').textContent = `${data.counts?.items || 0} Active Products`;

      // Update sidebar low stock badge
      const sidebarBadge = document.getElementById('sidebarLowStockBadge');
      if (sidebarBadge) {
        if (kpi.low_stock_count > 0) {
          sidebarBadge.textContent = kpi.low_stock_count;
          sidebarBadge.style.display = 'inline-block';
        } else {
          sidebarBadge.style.display = 'none';
        }
      }

      // Recent Sales Invoices
      const tbody = document.getElementById('dashboardRecentSalesTbody');
      if (tbody) {
        if (!data.recent_sales || data.recent_sales.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">No sales invoices recorded yet.</td></tr>';
        } else {
          tbody.innerHTML = data.recent_sales.map(s => `
            <tr>
              <td><span style="font-weight: 700; color: var(--accent-cyan);">${s.invoice_number}</span></td>
              <td>${s.invoice_date}</td>
              <td>${s.customer_name || 'N/A'}</td>
              <td style="font-weight: 600;">${this.formatCurrency(s.total_amount)}</td>
              <td>${this.renderStatusBadge(s.payment_status || s.status)}</td>
              <td>
                <a href="/api/sales/${s.id}/pdf" target="_blank" class="action-btn" title="View PDF">
                  📄 PDF
                </a>
              </td>
            </tr>
          `).join('');
        }
      }

      // Low Stock Alerts
      const stockContainer = document.getElementById('dashboardLowStockContainer');
      if (stockContainer) {
        if (!data.low_stock_items || data.low_stock_items.length === 0) {
          stockContainer.innerHTML = '<p style="color: var(--success); text-align: center; padding: 20px;">✅ All inventory items are adequately stocked!</p>';
        } else {
          stockContainer.innerHTML = data.low_stock_items.map(item => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: var(--bg-subtle); border-radius: 8px; border-left: 3px solid var(--danger);">
              <div>
                <p style="font-weight: 600; font-size: 0.86rem;">${item.name}</p>
                <p style="font-size: 0.74rem; color: var(--text-dim);">SKU: ${item.sku} &bull; Min Level: ${item.reorder_level} ${item.unit}</p>
              </div>
              <div style="text-align: right;">
                <span style="font-weight: 800; color: var(--danger); font-size: 0.95rem;">${item.current_stock} ${item.unit}</span>
                <br>
                <button class="btn btn-secondary btn-sm" style="padding: 3px 8px; font-size: 0.72rem; margin-top: 4px;" onclick="window.app.openStockAdjustModal(${item.id}, '${escape(item.name)}')">
                  + Reorder
                </button>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  }

  // -------------------------------------------------------------
  // PRODUCTS & INVENTORY
  // -------------------------------------------------------------
  async loadItems() {
    const q = document.getElementById('itemsSearchInput')?.value.trim() || '';
    const cat = document.getElementById('itemsCategoryFilter')?.value || 'All';
    const stock = document.getElementById('itemsStockFilter')?.value || 'All';

    try {
      const res = await fetch(`/api/items?query=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}&stock_filter=${encodeURIComponent(stock)}`);
      if (!res.ok) return;
      const data = await res.json();
      this.itemsCache = data.items || [];

      const tbody = document.getElementById('itemsTableBody');
      if (!tbody) return;

      if (this.itemsCache.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 40px;">No products match the selected filters.</td></tr>';
        return;
      }

      tbody.innerHTML = this.itemsCache.map(i => {
        const isLow = i.current_stock <= i.reorder_level;
        const isOut = i.current_stock <= 0;
        let stockBadge = `<span class="badge badge-success">In Stock (${i.current_stock} ${i.unit})</span>`;
        if (isOut) {
          stockBadge = `<span class="badge badge-danger">Out of Stock (0 ${i.unit})</span>`;
        } else if (isLow) {
          stockBadge = `<span class="badge badge-warning">Low Stock (${i.current_stock} ${i.unit})</span>`;
        }

        return `
          <tr>
            <td><code style="color: var(--accent-cyan); font-weight: 600;">${i.sku}</code></td>
            <td>
              <span style="font-weight: 600;">${i.name}</span>
              ${i.subcategory ? `<br><small style="color: var(--text-dim);">${i.subcategory}</small>` : ''}
            </td>
            <td>${i.category || 'General'}</td>
            <td>${i.hsn_code || '00000000'}</td>
            <td>${stockBadge}</td>
            <td>${this.formatCurrency(i.cost_price || 0)}</td>
            <td style="font-weight: 700;">${this.formatCurrency(i.selling_price || 0)}</td>
            <td>${i.tax_rate || 18}%</td>
            <td>
              <div class="action-group">
                <button class="action-btn" title="Adjust Stock" onclick="window.app.openStockAdjustModal(${i.id}, '${escape(i.name)}')">
                  📦 Stock
                </button>
                <button class="action-btn" title="Edit Product" onclick="window.app.openEditItemModal(${i.id})">
                  ✏️
                </button>
                <button class="action-btn danger" title="Delete Product" onclick="window.app.deleteItem(${i.id}, '${escape(i.name)}')">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load items:', err);
    }
  }

  openCreateItemModal() {
    document.getElementById('itemForm').reset();
    document.getElementById('itemId').value = '';
    document.getElementById('itemModalTitle').textContent = '📦 Add New Product';
    this.openModal('itemModal');
  }

  openEditItemModal(itemId) {
    const item = this.itemsCache.find(x => x.id === itemId);
    if (!item) return;

    document.getElementById('itemId').value = item.id;
    document.getElementById('itemName').value = item.name || '';
    document.getElementById('itemSku').value = item.sku || '';
    document.getElementById('itemHsn').value = item.hsn_code || '';
    document.getElementById('itemCategory').value = item.category || '';
    document.getElementById('itemSubcategory').value = item.subcategory || '';
    document.getElementById('itemUnit').value = item.unit || 'PCS';
    document.getElementById('itemCostPrice').value = item.cost_price || '';
    document.getElementById('itemSellingPrice').value = item.selling_price || '';
    document.getElementById('itemCurrentStock').value = item.current_stock || 0;
    document.getElementById('itemReorderLevel').value = item.reorder_level || 10;
    document.getElementById('itemTaxRate').value = parseInt(item.tax_rate) || 18;

    document.getElementById('itemModalTitle').textContent = `✏️ Edit Product - ${item.name}`;
    this.openModal('itemModal');
  }

  openStockAdjustModal(itemId, itemName) {
    document.getElementById('stockAdjustForm').reset();
    document.getElementById('adjustItemId').value = itemId;
    document.getElementById('adjustItemName').textContent = `Product: ${unescape(itemName)}`;
    this.openModal('stockAdjustModal');
  }

  async deleteItem(itemId, itemName) {
    if (!confirm(`Are you sure you want to delete product "${unescape(itemName)}"?`)) return;

    try {
      const res = await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast('Product successfully removed', 'success');
        this.loadItems();
      } else {
        this.showToast(data.error || 'Failed to delete product', 'error');
      }
    } catch (err) {
      this.showToast('Network error deleting product', 'error');
    }
  }

  // -------------------------------------------------------------
  // CUSTOMERS & SUPPLIERS CRM
  // -------------------------------------------------------------
  async loadContacts() {
    const q = document.getElementById('contactsSearchInput')?.value.trim() || '';
    const activeTab = document.querySelector('#contactsTypeTabs .tab-btn.active');
    const type = activeTab ? activeTab.getAttribute('data-type') : 'All';

    try {
      const res = await fetch(`/api/contacts?query=${encodeURIComponent(q)}&type=${encodeURIComponent(type)}`);
      if (!res.ok) return;
      const data = await res.json();
      this.contactsCache = data.contacts || [];

      const tbody = document.getElementById('contactsTableBody');
      if (!tbody) return;

      if (this.contactsCache.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 40px;">No contacts found.</td></tr>';
        return;
      }

      tbody.innerHTML = this.contactsCache.map(c => {
        const isCustomer = c.contact_type === 'Customer';
        const typeBadge = isCustomer
          ? '<span class="badge badge-info">Customer</span>'
          : '<span class="badge badge-warning">Supplier</span>';

        const bal = parseFloat(c.balance || 0);
        const balColor = bal > 0 ? 'var(--warning)' : (bal < 0 ? 'var(--success)' : 'var(--text-muted)');
        const balTag = bal > 0 ? ' (Due)' : (bal === 0 ? ' (Settled)' : ' (Advance)');

        return `
          <tr>
            <td>
              <span style="font-weight: 700; cursor: pointer; color: var(--accent-cyan);" onclick="window.app.openPartyLedgerModal(${c.id})" title="Click to view ledger">${c.name}</span>
            </td>
            <td>${c.company_name || '-'}</td>
            <td>${typeBadge}</td>
            <td>${c.phone || '-'}</td>
            <td>${c.place_of_supply || 'Uttar Pradesh'}</td>
            <td><code style="color: var(--accent-cyan);">${c.gstin || 'Unregistered'}</code></td>
            <td style="font-weight: 700; color: ${balColor}; cursor: pointer;" onclick="window.app.openPartyLedgerModal(${c.id})" title="Click to view running balance ledger">
              ${this.formatCurrency(bal)} <small style="font-size: 0.72rem; opacity: 0.85;">${balTag}</small>
            </td>
            <td>
              <div class="action-group">
                <button class="action-btn" title="View Full Party Ledger Statement" onclick="window.app.openPartyLedgerModal(${c.id})" style="font-weight: 600; color: var(--accent-cyan);">
                  📜 Ledger
                </button>
                <button class="action-btn" title="Edit Contact" onclick="window.app.openEditContactModal(${c.id})">
                  ✏️
                </button>
                <button class="action-btn danger" title="Delete Contact" onclick="window.app.deleteContact(${c.id}, '${escape(c.name)}')">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load contacts:', err);
    }
  }

  openCreateContactModal() {
    document.getElementById('contactForm').reset();
    document.getElementById('contactId').value = '';
    document.getElementById('contactPlaceOfSupply').value = 'Uttar Pradesh';
    document.getElementById('contactBalance').value = '0.00';
    document.getElementById('contactModalTitle').textContent = '👥 Add New Party';
    this.openModal('contactModal');
  }

  openEditContactModal(contactId) {
    const c = this.contactsCache.find(x => x.id === contactId);
    if (!c) return;

    document.getElementById('contactId').value = c.id;
    document.getElementById('contactType').value = c.contact_type || 'Customer';
    document.getElementById('contactName').value = c.name || '';
    document.getElementById('contactCompany').value = c.company_name || '';
    document.getElementById('contactPhone').value = c.phone || '';
    document.getElementById('contactEmail').value = c.email || '';
    document.getElementById('contactGstin').value = c.gstin || '';
    document.getElementById('contactPan').value = c.pan || '';
    document.getElementById('contactPlaceOfSupply').value = c.place_of_supply || 'Uttar Pradesh';
    document.getElementById('contactBalance').value = c.balance || 0;
    document.getElementById('contactAddress').value = c.address || '';

    document.getElementById('contactModalTitle').textContent = `✏️ Edit Party - ${c.name}`;
    this.openModal('contactModal');
  }

  async deleteContact(contactId, contactName) {
    if (!confirm(`Are you sure you want to delete contact "${unescape(contactName)}"?`)) return;

    try {
      const res = await fetch(`/api/contacts/${contactId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast('Party successfully deleted', 'success');
        this.loadContacts();
      } else {
        this.showToast(data.error || 'Failed to delete contact', 'error');
      }
    } catch (err) {
      this.showToast('Network error deleting contact', 'error');
    }
  }

  // -------------------------------------------------------------
  // GST TAX INVOICES & SALES ORDERS
  // -------------------------------------------------------------
  async loadSales() {
    const q = document.getElementById('salesSearchInput')?.value.trim().toLowerCase() || '';
    const status = document.getElementById('salesStatusFilter')?.value || 'All';

    try {
      const res = await fetch('/api/sales');
      if (!res.ok) return;
      const data = await res.json();
      let orders = data.sales_orders || [];

      if (status !== 'All') {
        orders = orders.filter(o => (o.payment_status === status || o.status === status));
      }

      if (q) {
        orders = orders.filter(o => 
          (o.invoice_number && o.invoice_number.toLowerCase().includes(q)) ||
          (o.customer_name && o.customer_name.toLowerCase().includes(q))
        );
      }

      const tbody = document.getElementById('salesTableBody');
      if (!tbody) return;

      if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 40px;">No tax invoices found.</td></tr>';
        return;
      }

      tbody.innerHTML = orders.map(s => {
        const isPaid = (s.payment_status === 'Paid' || s.status === 'Paid');
        const payToggleBtn = isPaid
          ? `<button class="action-btn" title="Click to mark as Unpaid" style="color: var(--warning);" onclick="window.app.toggleInvoicePaid(${s.id}, false, '${s.invoice_number}')">❌ Unpaid</button>`
          : `<button class="action-btn" title="Click to mark as Paid" style="color: var(--success); font-weight: 700;" onclick="window.app.toggleInvoicePaid(${s.id}, true, '${s.invoice_number}')">✅ Paid</button>`;

        return `
        <tr>
          <td><span style="font-weight: 700; color: var(--accent-cyan);">${s.invoice_number}</span></td>
          <td>${s.invoice_date}</td>
          <td>
            <span style="font-weight: 600; cursor: pointer;" onclick="window.app.openPartyLedgerModal(${s.customer_id})" title="Click to view Customer Ledger">${s.customer_name || 'N/A'}</span>
            ${s.customer_gstin ? `<br><small style="color: var(--text-dim);">GSTIN: ${s.customer_gstin}</small>` : ''}
          </td>
          <td>${this.formatCurrency(s.subtotal)}</td>
          <td>${this.formatCurrency((parseFloat(s.cgst_amount) || 0) + (parseFloat(s.sgst_amount) || 0))}</td>
          <td>${this.formatCurrency(s.igst_amount || 0)}</td>
          <td style="font-weight: 800; font-size: 0.95rem;">${this.formatCurrency(s.total_amount)}</td>
          <td>
            <span style="cursor: pointer;" onclick="window.app.toggleInvoicePaid(${s.id}, ${!isPaid}, '${s.invoice_number}')" title="Click to toggle Paid / Unpaid">
              ${this.renderStatusBadge(s.payment_status || s.status)}
            </span>
          </td>
          <td>
            <div class="action-group">
              ${payToggleBtn}
              <a href="/api/sales/${s.id}/pdf" target="_blank" class="action-btn" title="View PDF">
                📄 View
              </a>
              <a href="/api/sales/${s.id}/pdf?download=1" class="action-btn" title="Download PDF">
                ⬇️
              </a>
              <button class="action-btn danger" title="Delete Invoice & Restore Stock" onclick="window.app.deleteInvoice(${s.id}, '${s.invoice_number}')">
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `}).join('');
    } catch (err) {
      console.error('Failed to load sales orders:', err);
    }
  }

  async openCreateInvoiceModal() {
    document.getElementById('invoiceForm').reset();
    
    // Fetch next invoice number
    try {
      const numRes = await fetch('/api/sales/next-number');
      if (numRes.ok) {
        const numData = await numRes.json();
        document.getElementById('invNumber').value = numData.invoice_number;
      }
    } catch (e) {
      document.getElementById('invNumber').value = `INV-${new Date().getFullYear()}-001`;
    }

    // Set today's date (YYYY-MM-DD)
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('invDate').value = today;

    // Load Customers into dropdown
    await this.populateCustomersDropdown();

    // Reset line items and add 1 default row
    this.invoiceRows = [];
    document.getElementById('invoiceRowsTbody').innerHTML = '';
    this.addInvoiceRow();

    // Bind recalculate triggers
    document.getElementById('invFreightInput').oninput = () => this.recalculateInvoiceTotals();
    document.getElementById('invTaxMode').onchange = () => this.recalculateInvoiceTotals();
    document.getElementById('invAddRowBtn').onclick = () => this.addInvoiceRow();

    this.openModal('invoiceModal');
  }

  async populateCustomersDropdown() {
    const custSelect = document.getElementById('invCustomerSelect');
    if (!custSelect) return;

    // Fetch customers if cache empty
    if (!this.contactsCache || this.contactsCache.length === 0) {
      const res = await fetch('/api/contacts?type=Customer');
      if (res.ok) {
        const data = await res.json();
        this.contactsCache = data.contacts || [];
      }
    }

    const customers = this.contactsCache.filter(c => c.contact_type === 'Customer');
    custSelect.innerHTML = '<option value="">Select Customer...</option>';
    customers.forEach(c => {
      custSelect.innerHTML += `<option value="${c.id}" data-state="${c.place_of_supply || 'Uttar Pradesh'}" data-gstin="${c.gstin || ''}" data-address="${escape(c.address || '')}">${c.name} ${c.company_name ? `(${c.company_name})` : ''}</option>`;
    });

    custSelect.onchange = () => {
      const opt = custSelect.options[custSelect.selectedIndex];
      const state = opt.getAttribute('data-state') || 'Uttar Pradesh';
      const gstin = opt.getAttribute('data-gstin') || '';
      const address = unescape(opt.getAttribute('data-address') || '');

      document.getElementById('invCustomerDetailsBar').innerHTML = `
        <strong>GSTIN:</strong> ${gstin || 'Unregistered'} &bull; 
        <strong>Place of Supply:</strong> ${state} &bull; 
        <strong>Address:</strong> ${address || 'No address provided'}
      `;

      // Smart State GST determination
      const compState = (this.companyProfile && this.companyProfile.address && this.companyProfile.address.includes('Uttar Pradesh')) ? 'Uttar Pradesh' : 'Uttar Pradesh';
      const taxModeSelect = document.getElementById('invTaxMode');
      if (state.toLowerCase().trim() === compState.toLowerCase().trim()) {
        taxModeSelect.value = 'intra';
      } else {
        taxModeSelect.value = 'inter';
      }

      this.recalculateInvoiceTotals();
    };

    if (customers.length > 0) {
      custSelect.selectedIndex = 1;
      custSelect.dispatchEvent(new Event('change'));
    }
  }

  addInvoiceRow() {
    const rowId = Date.now() + Math.random().toString(36).substring(2, 7);
    const tbody = document.getElementById('invoiceRowsTbody');
    const tr = document.createElement('tr');
    tr.id = `row_${rowId}`;

    tr.innerHTML = `
      <td>
        <select class="form-select inv-item-select" style="padding: 6px;" required>
          <option value="">Select Item...</option>
          ${this.itemsCache.map(i => `<option value="${i.id}" data-hsn="${i.hsn_code || '00000000'}" data-unit="${i.unit || 'PCS'}" data-rate="${i.selling_price || 0}">${i.name} (${i.sku})</option>`).join('')}
        </select>
      </td>
      <td>
        <input type="text" class="inv-item-hsn" placeholder="HSN" style="text-align: center;">
      </td>
      <td>
        <input type="number" step="0.001" class="inv-item-qty" value="1" min="0.001" style="text-align: right;" required>
      </td>
      <td>
        <input type="text" class="inv-item-unit" value="PCS" style="text-align: center;">
      </td>
      <td>
        <input type="number" step="0.01" class="inv-item-rate" value="0.00" style="text-align: right;" required>
      </td>
      <td style="text-align: right; font-weight: 700; color: var(--text-main); white-space: nowrap;">
        <span class="inv-row-amount">₹ 0.00</span>
      </td>
      <td style="text-align: center;">
        <button type="button" class="action-btn danger" style="padding: 4px 7px;" onclick="window.app.removeInvoiceRow('${rowId}')">
          &times;
        </button>
      </td>
    `;

    tbody.appendChild(tr);

    const selectEl = tr.querySelector('.inv-item-select');
    const hsnEl = tr.querySelector('.inv-item-hsn');
    const qtyEl = tr.querySelector('.inv-item-qty');
    const unitEl = tr.querySelector('.inv-item-unit');
    const rateEl = tr.querySelector('.inv-item-rate');

    selectEl.onchange = () => {
      const opt = selectEl.options[selectEl.selectedIndex];
      if (opt && opt.value) {
        hsnEl.value = opt.getAttribute('data-hsn') || '00000000';
        unitEl.value = opt.getAttribute('data-unit') || 'PCS';
        rateEl.value = parseFloat(opt.getAttribute('data-rate') || 0).toFixed(2);
      }
      this.recalculateInvoiceTotals();
    };

    qtyEl.oninput = () => this.recalculateInvoiceTotals();
    rateEl.oninput = () => this.recalculateInvoiceTotals();

    this.recalculateInvoiceTotals();
  }

  removeInvoiceRow(rowId) {
    const tr = document.getElementById(`row_${rowId}`);
    const rows = document.querySelectorAll('#invoiceRowsTbody tr');
    if (rows.length <= 1) {
      this.showToast('At least one item row is required in invoice', 'warning');
      return;
    }
    if (tr) tr.remove();
    this.recalculateInvoiceTotals();
  }

  recalculateInvoiceTotals() {
    let subtotal = 0;
    const rows = document.querySelectorAll('#invoiceRowsTbody tr');

    rows.forEach(tr => {
      const qty = parseFloat(tr.querySelector('.inv-item-qty')?.value || 0);
      const rate = parseFloat(tr.querySelector('.inv-item-rate')?.value || 0);
      const amt = qty * rate;
      subtotal += amt;
      const amtSpan = tr.querySelector('.inv-row-amount');
      if (amtSpan) amtSpan.textContent = this.formatCurrency(amt);
    });

    const freight = parseFloat(document.getElementById('invFreightInput')?.value || 0);
    const taxable = subtotal + freight;

    const mode = document.getElementById('invTaxMode')?.value || 'intra';
    let cgst = 0, sgst = 0, igst = 0;

    const cgstRow = document.getElementById('invCgstRow');
    const sgstRow = document.getElementById('invSgstRow');
    const igstRow = document.getElementById('invIgstRow');

    if (mode === 'intra') {
      cgst = taxable * 0.09;
      sgst = taxable * 0.09;
      if (cgstRow) cgstRow.style.display = 'flex';
      if (sgstRow) sgstRow.style.display = 'flex';
      if (igstRow) igstRow.style.display = 'none';
    } else if (mode === 'inter') {
      igst = taxable * 0.18;
      if (cgstRow) cgstRow.style.display = 'none';
      if (sgstRow) sgstRow.style.display = 'none';
      if (igstRow) igstRow.style.display = 'flex';
    } else {
      if (cgstRow) cgstRow.style.display = 'none';
      if (sgstRow) sgstRow.style.display = 'none';
      if (igstRow) igstRow.style.display = 'none';
    }

    const rawTotal = taxable + cgst + sgst + igst;
    const grandTotal = Math.round(rawTotal);
    const roundOff = grandTotal - rawTotal;

    document.getElementById('invCalcSubtotal').textContent = this.formatCurrency(subtotal);
    document.getElementById('invCalcCgst').textContent = this.formatCurrency(cgst);
    document.getElementById('invCalcSgst').textContent = this.formatCurrency(sgst);
    document.getElementById('invCalcIgst').textContent = this.formatCurrency(igst);
    document.getElementById('invCalcRoundOff').textContent = this.formatCurrency(roundOff);
    document.getElementById('invCalcGrandTotal').textContent = this.formatCurrency(grandTotal);

    // Number to words
    document.getElementById('invAmountInWords').textContent = `Total in Words: ${this.numberToWords(grandTotal)}`;
  }

  async deleteInvoice(orderId, invNumber) {
    if (!confirm(`Delete Invoice #${invNumber}? This will automatically restore inventory stock levels.`)) return;

    try {
      const res = await fetch(`/api/sales/${orderId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast(`Invoice #${invNumber} deleted and stock restored`, 'success');
        this.loadSales();
      } else {
        this.showToast(data.error || 'Failed to delete invoice', 'error');
      }
    } catch (err) {
      this.showToast('Network error deleting invoice', 'error');
    }
  }

  // -------------------------------------------------------------
  // PURCHASE ORDERS
  // -------------------------------------------------------------
  async loadPurchases() {
    try {
      const res = await fetch('/api/purchases');
      if (!res.ok) return;
      const data = await res.json();
      const purchases = data.purchases || [];

      const tbody = document.getElementById('purchasesTableBody');
      if (!tbody) return;

      if (purchases.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 40px;">No purchase orders recorded yet.</td></tr>';
        return;
      }

      tbody.innerHTML = purchases.map(p => {
        const isPaid = (p.payment_status === 'Paid' || p.status === 'Paid');
        const payToggleBtn = isPaid
          ? `<button class="action-btn" title="Click to mark as Unpaid" style="color: var(--warning);" onclick="window.app.togglePurchasePaid(${p.id}, false, '${p.po_number}')">❌ Unpaid</button>`
          : `<button class="action-btn" title="Click to mark as Paid" style="color: var(--success); font-weight: 700;" onclick="window.app.togglePurchasePaid(${p.id}, true, '${p.po_number}')">✅ Paid</button>`;

        return `
        <tr>
          <td><span style="font-weight: 700; color: var(--accent-cyan);">${p.po_number}</span></td>
          <td>${p.order_date || p.po_date || '-'}</td>
          <td>
            <span style="font-weight: 600; cursor: pointer;" onclick="window.app.openPartyLedgerModal(${p.supplier_id})" title="Click to view Vendor Ledger">${p.supplier_name || 'N/A'}</span>
          </td>
          <td>${this.formatCurrency(p.subtotal)}</td>
          <td>${this.formatCurrency((parseFloat(p.cgst_amount) || 0) + (parseFloat(p.sgst_amount) || 0) + (parseFloat(p.igst_amount) || 0))}</td>
          <td style="font-weight: 800;">${this.formatCurrency(p.total_amount)}</td>
          <td>
            <span style="cursor: pointer;" onclick="window.app.togglePurchasePaid(${p.id}, ${!isPaid}, '${p.po_number}')" title="Click to toggle Paid / Unpaid">
              ${this.renderStatusBadge(p.payment_status || p.status)}
            </span>
          </td>
          <td>
            <div class="action-group">
              ${payToggleBtn}
              <a href="/api/purchases/${p.id}/pdf" target="_blank" class="action-btn" title="View Purchase PO PDF">
                📄 PO PDF
              </a>
            </div>
          </td>
        </tr>
      `}).join('');
    } catch (err) {
      console.error('Failed to load purchases:', err);
    }
  }

  openCreatePOModal() {
    this.showToast('Use Tax Invoices or contact supplier to record inbound stock', 'info');
  }

  // -------------------------------------------------------------
  // CUSTOMER POS & DISPATCHES
  // -------------------------------------------------------------
  async loadCustomerPOs() {
    try {
      const res = await fetch('/api/customer-pos');
      if (!res.ok) return;
      const data = await res.json();
      const pos = data.customer_pos || [];

      const tbody = document.getElementById('customerPosTableBody');
      if (!tbody) return;

      if (pos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 40px;">No Customer POs registered yet.</td></tr>';
        return;
      }

      tbody.innerHTML = pos.map(p => {
        const totalQty = parseFloat(p.total_quantity_kg || 0);
        const dispQty = parseFloat(p.total_dispatched_qty_kg || 0);
        const pendQty = Math.max(0, totalQty - dispQty);

        return `
          <tr>
            <td><code style="color: var(--accent-cyan); font-weight: 700;">${p.po_number}</code></td>
            <td>${p.customer_name || 'N/A'}</td>
            <td>${p.order_date || '-'}</td>
            <td>${totalQty.toFixed(2)} KG</td>
            <td style="color: var(--success); font-weight: 600;">${dispQty.toFixed(2)} KG</td>
            <td style="color: ${pendQty > 0 ? 'var(--warning)' : 'var(--text-muted)'}; font-weight: 700;">${pendQty.toFixed(2)} KG</td>
            <td>${this.renderStatusBadge(p.status)}</td>
            <td>
              <span class="badge badge-neutral">${((dispQty / (totalQty || 1)) * 100).toFixed(0)}% Dispatched</span>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load customer POs:', err);
    }
  }

  openCreateCustomerPOModal() {
    this.showToast('Customer PO tracker is actively synced with Tax Invoices via Buyer PO Ref field', 'info');
  }

  // -------------------------------------------------------------
  // PAYMENTS & LEDGER
  // -------------------------------------------------------------
  async loadPayments() {
    const q = document.getElementById('paymentsSearchInput')?.value.trim() || '';
    const activeTab = document.querySelector('#paymentsTypeTabs .tab-btn.active');
    const type = activeTab ? activeTab.getAttribute('data-type') : 'All';

    try {
      const res = await fetch(`/api/payments?query=${encodeURIComponent(q)}&type=${encodeURIComponent(type)}`);
      if (!res.ok) return;
      const data = await res.json();
      const payments = data.payments || [];
      const summary = data.summary || {};

      document.getElementById('paymentsTotalIn').textContent = this.formatCurrency(summary.total_in || 0);
      document.getElementById('paymentsTotalOut').textContent = this.formatCurrency(summary.total_out || 0);

      const tbody = document.getElementById('paymentsTableBody');
      if (!tbody) return;

      if (payments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 40px;">No payments recorded.</td></tr>';
        return;
      }

      tbody.innerHTML = payments.map(p => {
        const isIn = p.payment_type === 'Payment In';
        const badge = isIn
          ? '<span class="badge badge-success">📥 Payment In</span>'
          : '<span class="badge badge-warning">📤 Payment Out</span>';

        return `
          <tr>
            <td><code style="color: var(--accent-cyan); font-weight: 700;">${p.payment_number}</code></td>
            <td>${p.payment_date}</td>
            <td><span style="font-weight: 600;">${p.contact_name}</span></td>
            <td>${badge}</td>
            <td><span class="badge badge-neutral">${p.payment_mode || 'Cash'}</span></td>
            <td style="font-weight: 800; color: ${isIn ? 'var(--success)' : 'var(--warning)'}; font-size: 0.95rem;">
              ${isIn ? '+' : '-'} ${this.formatCurrency(p.amount)}
            </td>
            <td>${p.reference_no || p.notes || '-'}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load payments:', err);
    }
  }

  async toggleInvoicePaid(orderId, isPaid, invNum) {
    const statusVal = isPaid ? 'Paid' : 'Unpaid';
    try {
      const res = await fetch(`/api/sales/${orderId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: statusVal, payment_status: statusVal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast(`Invoice #${invNum} marked as ${statusVal}. Party balance updated!`, 'success');
        this.loadSales();
        this.loadContacts();
        this.loadPayments();
        this.loadDashboard();
      } else {
        this.showToast(data.error || 'Failed to update invoice status', 'error');
      }
    } catch (err) {
      this.showToast('Network error updating invoice status', 'error');
    }
  }

  async togglePurchasePaid(poId, isPaid, poNum) {
    const statusVal = isPaid ? 'Paid' : 'Unpaid';
    try {
      const res = await fetch(`/api/purchases/${poId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_status: statusVal, status: isPaid ? 'Received' : 'Issued' })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast(`Purchase Order #${poNum} marked as ${statusVal}. Vendor balance updated!`, 'success');
        this.loadPurchases();
        this.loadContacts();
        this.loadPayments();
        this.loadDashboard();
      } else {
        this.showToast(data.error || 'Failed to update PO status', 'error');
      }
    } catch (err) {
      this.showToast('Network error updating purchase order status', 'error');
    }
  }

  async openPartyLedgerModal(contactId) {
    try {
      const res = await fetch(`/api/contacts/${contactId}/ledger`);
      if (!res.ok) {
        this.showToast('Failed to load ledger', 'error');
        return;
      }
      const data = await res.json();
      if (!data.success || !data.ledger) {
        this.showToast(data.error || 'Ledger statement not found', 'error');
        return;
      }

      const ledger = data.ledger;
      const contact = ledger.contact;
      const isCust = contact.contact_type === 'Customer';

      document.getElementById('partyLedgerModalTitle').textContent = `📜 ${contact.name} - Party Ledger Statement`;
      document.getElementById('partyLedgerSubtitle').textContent = `${contact.company_name ? contact.company_name + ' | ' : ''}${isCust ? 'Customer (Buyer)' : 'Supplier / Vendor'}`;

      // Info Bar
      const addr = contact.address || 'No address registered';
      const gstin = contact.gstin || 'Unregistered';
      const phone = contact.phone || '-';
      document.getElementById('partyLedgerInfoBar').innerHTML = `
        <div><strong>👤 Contact:</strong> ${contact.name}</div>
        <div><strong>🏢 Business:</strong> ${contact.company_name || 'Individual'}</div>
        <div><strong>🏷️ Type:</strong> <span class="badge ${isCust ? 'badge-info' : 'badge-warning'}">${contact.contact_type}</span></div>
        <div><strong>📱 Phone:</strong> ${phone}</div>
        <div><strong>🆔 GSTIN:</strong> <code style="color: var(--accent-cyan);">${gstin}</code></div>
        <div style="width: 100%;"><strong>📍 Address:</strong> ${addr}</div>
      `;

      // KPI totals
      document.getElementById('ledgerTotalBilled').textContent = this.formatCurrency(ledger.total_billed || 0);
      document.getElementById('ledgerTotalSettled').textContent = this.formatCurrency(ledger.total_paid_received || 0);
      
      const netBal = parseFloat(ledger.net_balance || 0);
      const balColor = netBal > 0 ? 'var(--warning)' : (netBal < 0 ? 'var(--success)' : 'var(--text-muted)');
      const balLabel = netBal > 0 ? (isCust ? ' (Receivable Due)' : ' (Payable Due)') : (netBal === 0 ? ' (Settled)' : ' (Advance)');
      const netBalElem = document.getElementById('ledgerNetBalance');
      netBalElem.textContent = `${this.formatCurrency(netBal)}${balLabel}`;
      netBalElem.style.color = balColor;

      // Table rows
      const tbody = document.getElementById('partyLedgerTbody');
      const rows = ledger.rows || [];
      if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 30px;">No billing or payment transactions recorded for this party yet.</td></tr>';
      } else {
        tbody.innerHTML = rows.map(r => {
          const deb = parseFloat(r.debit || 0);
          const cred = parseFloat(r.credit || 0);
          const bal = parseFloat(r.balance || 0);
          const rowBalColor = bal > 0 ? 'var(--warning)' : (bal < 0 ? 'var(--success)' : 'var(--text-muted)');

          return `
            <tr>
              <td>${r.date || '-'}</td>
              <td><code style="color: var(--accent-cyan); font-weight: 600;">${r.ref_no || '-'}</code></td>
              <td>
                <span style="font-weight: 600;">${r.txn_type || '-'}</span>
                ${r.notes ? `<br><small style="color: var(--text-dim);">${r.notes}</small>` : ''}
              </td>
              <td style="text-align: right; ${deb > 0 ? 'font-weight: 600;' : 'color: var(--text-dim);'}">${deb > 0 ? this.formatCurrency(deb) : '-'}</td>
              <td style="text-align: right; ${cred > 0 ? 'color: var(--success); font-weight: 600;' : 'color: var(--text-dim);'}">${cred > 0 ? this.formatCurrency(cred) : '-'}</td>
              <td style="text-align: right; font-weight: 700; color: ${rowBalColor};">${this.formatCurrency(bal)}</td>
            </tr>
          `;
        }).join('');
      }

      // Bind record payment button
      const recBtn = document.getElementById('ledgerRecordPayBtn');
      if (recBtn) {
        recBtn.onclick = () => {
          this.closeModal('partyLedgerModal');
          this.openRecordPaymentModal(contact.id);
        };
      }

      this.openModal('partyLedgerModal');
    } catch (err) {
      console.error('Error opening party ledger modal:', err);
      this.showToast('Network error loading party ledger', 'error');
    }
  }

  openRecordPaymentModal(prefillContactId = null) {
    document.getElementById('paymentForm').reset();
    document.getElementById('payDate').value = new Date().toISOString().split('T')[0];

    const selectEl = document.getElementById('payContactSelect');
    if (selectEl) {
      selectEl.innerHTML = '<option value="">Select Party...</option>' +
        this.contactsCache.map(c => `<option value="${c.id}">${c.name} (${c.contact_type})</option>`).join('');
      if (prefillContactId) {
        selectEl.value = prefillContactId;
        const targetContact = this.contactsCache.find(x => x.id === parseInt(prefillContactId));
        if (targetContact) {
          const typeSelect = document.getElementById('payType');
          if (typeSelect) {
            typeSelect.value = targetContact.contact_type === 'Customer' ? 'Payment In' : 'Payment Out';
          }
          const amtInput = document.getElementById('payAmount');
          if (amtInput && targetContact.balance > 0) {
            amtInput.value = targetContact.balance;
          }
        }
      }
    }

    this.openModal('paymentModal');
  }

  // -------------------------------------------------------------
  // REPORTS & GSTR-1
  // -------------------------------------------------------------
  async loadReports() {
    try {
      const res = await fetch('/api/reports/gstr1');
      if (!res.ok) return;
      const data = await res.json();
      const totals = data.totals || {};

      document.getElementById('gstrTaxable').textContent = this.formatCurrency(totals.taxable || 0);
      document.getElementById('gstrCgst').textContent = this.formatCurrency(totals.cgst || 0);
      document.getElementById('gstrSgst').textContent = this.formatCurrency(totals.sgst || 0);
      document.getElementById('gstrIgst').textContent = this.formatCurrency(totals.igst || 0);

      // Render B2B Table
      const b2bTbody = document.getElementById('gstrB2bTableBody');
      if (b2bTbody) {
        if (!data.b2b || data.b2b.length === 0) {
          b2bTbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: var(--text-dim); padding: 20px;">No B2B invoices in active period.</td></tr>';
        } else {
          b2bTbody.innerHTML = data.b2b.map(r => `
            <tr>
              <td><span style="font-weight: 700; color: var(--accent-cyan);">${r.invoice_number}</span></td>
              <td>${r.invoice_date}</td>
              <td>${r.customer_name}</td>
              <td><code>${r.customer_gstin}</code></td>
              <td>${r.place_of_supply}</td>
              <td>${this.formatCurrency(r.subtotal)}</td>
              <td>${this.formatCurrency(r.cgst_amount)}</td>
              <td>${this.formatCurrency(r.sgst_amount)}</td>
              <td>${this.formatCurrency(r.igst_amount)}</td>
              <td style="font-weight: 700;">${this.formatCurrency(r.total_amount)}</td>
            </tr>
          `).join('');
        }
      }

      // Render B2C Table
      const b2cTbody = document.getElementById('gstrB2cTableBody');
      if (b2cTbody) {
        if (!data.b2c || data.b2c.length === 0) {
          b2cTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 20px;">No B2C invoices in active period.</td></tr>';
        } else {
          b2cTbody.innerHTML = data.b2c.map(r => `
            <tr>
              <td><span style="font-weight: 700; color: var(--accent-cyan);">${r.invoice_number}</span></td>
              <td>${r.invoice_date}</td>
              <td>${r.customer_name}</td>
              <td>${r.place_of_supply}</td>
              <td>${this.formatCurrency(r.subtotal)}</td>
              <td>${this.formatCurrency(r.cgst_amount)}</td>
              <td>${this.formatCurrency(r.sgst_amount)}</td>
              <td>${this.formatCurrency(r.igst_amount)}</td>
              <td style="font-weight: 700;">${this.formatCurrency(r.total_amount)}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  }

  // -------------------------------------------------------------
  // COMPANY PROFILE
  // -------------------------------------------------------------
  async loadCompanyProfile() {
    try {
      const res = await fetch('/api/company');
      if (!res.ok) return;
      const data = await res.json();
      const comp = data.company || {};
      this.companyProfile = comp;

      document.getElementById('compName').value = comp.name || '';
      document.getElementById('compGstin').value = comp.gstin || '';
      document.getElementById('compPan').value = comp.pan || '';
      document.getElementById('compMobile').value = comp.mobile || '';
      document.getElementById('compEmail').value = comp.email || '';
      document.getElementById('compAddress').value = comp.address || '';
      document.getElementById('compUdyam').value = comp.udyam_reg_no || '';
      document.getElementById('compFiscalYear').value = comp.current_fiscal_year || '2026-2027';

      document.getElementById('compBankName').value = comp.bank_name || '';
      document.getElementById('compBankBranch').value = comp.bank_branch || '';
      document.getElementById('compAccountNo').value = comp.account_no || '';
      document.getElementById('compIfscCode').value = comp.ifsc_code || '';

      const termsList = Array.isArray(comp.terms) ? comp.terms.join('\n') : (comp.terms || '');
      document.getElementById('compTerms').value = termsList;
    } catch (err) {
      console.error('Failed to load company profile:', err);
    }
  }

  // -------------------------------------------------------------
  // USER MANAGEMENT (ADMIN)
  // -------------------------------------------------------------
  async loadUsers() {
    try {
      const res = await fetch('/api/users');
      if (!res.ok) return;
      const data = await res.json();
      const users = data.users || [];

      const tbody = document.getElementById('usersTableBody');
      if (!tbody) return;

      tbody.innerHTML = users.map(u => `
        <tr>
          <td>#${u.id}</td>
          <td><code style="color: var(--accent-cyan); font-weight: 700;">${u.username}</code></td>
          <td><span style="font-weight: 600;">${u.full_name}</span></td>
          <td><span class="badge ${u.role === 'Admin' ? 'badge-primary' : 'badge-neutral'}">${u.role}</span></td>
          <td><span class="badge badge-success">${u.status}</span></td>
          <td>${u.created_at || 'Active'}</td>
          <td>
            <button class="action-btn danger" onclick="window.app.deleteUser(${u.id}, '${u.username}')">
              🗑️ Delete
            </button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  }

  openCreateUserModal() {
    document.getElementById('userForm')?.reset();
    document.getElementById('usrId').value = '';
    this.openModal('userModal');
  }

  async deleteUser(userId, username) {
    if (!confirm(`Delete user account "${username}"?`)) return;
    try {
      const res = await fetch(`/api/users/${userId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok && data.success) {
        this.showToast(`User ${username} deleted`, 'success');
        this.loadUsers();
      } else {
        this.showToast(data.error || 'Failed to delete user', 'error');
      }
    } catch (err) {
      this.showToast('Network error deleting user', 'error');
    }
  }

  // -------------------------------------------------------------
  // FORM SUBMISSION HANDLERS
  // -------------------------------------------------------------
  initForms() {
    // 1. Item Form
    document.getElementById('itemForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const itemId = document.getElementById('itemId').value;
      const body = {
        name: document.getElementById('itemName').value.trim(),
        sku: document.getElementById('itemSku').value.trim(),
        hsn_code: document.getElementById('itemHsn').value.trim(),
        category: document.getElementById('itemCategory').value,
        subcategory: document.getElementById('itemSubcategory').value.trim(),
        unit: document.getElementById('itemUnit').value,
        cost_price: parseFloat(document.getElementById('itemCostPrice').value || 0),
        selling_price: parseFloat(document.getElementById('itemSellingPrice').value || 0),
        current_stock: parseFloat(document.getElementById('itemCurrentStock').value || 0),
        reorder_level: parseFloat(document.getElementById('itemReorderLevel').value || 10),
        tax_rate: parseFloat(document.getElementById('itemTaxRate').value || 18)
      };

      const url = itemId ? `/api/items/${itemId}` : '/api/items';
      const method = itemId ? 'PUT' : 'POST';

      try {
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast(data.message || 'Product saved successfully!', 'success');
          this.closeModal('itemModal');
          this.loadItems();
          this.loadDashboard();
        } else {
          this.showToast(data.error || 'Failed to save product', 'error');
        }
      } catch (err) {
        this.showToast('Network error saving product', 'error');
      }
    });

    // 2. Stock Adjust Form
    document.getElementById('stockAdjustForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const itemId = document.getElementById('adjustItemId').value;
      const body = {
        adjustment_type: document.getElementById('adjustType').value,
        quantity: parseFloat(document.getElementById('adjustQty').value || 0),
        reason: document.getElementById('adjustReason').value.trim() || 'Manual adjustment'
      };

      try {
        const res = await fetch(`/api/items/${itemId}/adjust-stock`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast(data.message, 'success');
          this.closeModal('stockAdjustModal');
          this.loadItems();
          this.loadDashboard();
        } else {
          this.showToast(data.error || 'Failed to adjust stock', 'error');
        }
      } catch (err) {
        this.showToast('Network error adjusting stock', 'error');
      }
    });

    // 3. Contact Form
    document.getElementById('contactForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const contactId = document.getElementById('contactId').value;
      const body = {
        contact_type: document.getElementById('contactType').value,
        name: document.getElementById('contactName').value.trim(),
        company_name: document.getElementById('contactCompany').value.trim(),
        phone: document.getElementById('contactPhone').value.trim(),
        email: document.getElementById('contactEmail').value.trim(),
        gstin: document.getElementById('contactGstin').value.trim(),
        pan: document.getElementById('contactPan').value.trim(),
        place_of_supply: document.getElementById('contactPlaceOfSupply').value.trim(),
        balance: parseFloat(document.getElementById('contactBalance').value || 0),
        address: document.getElementById('contactAddress').value.trim()
      };

      const url = contactId ? `/api/contacts/${contactId}` : '/api/contacts';
      const method = contactId ? 'PUT' : 'POST';

      try {
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast(data.message || 'Party saved successfully!', 'success');
          this.closeModal('contactModal');
          this.loadContacts();
        } else {
          this.showToast(data.error || 'Failed to save contact', 'error');
        }
      } catch (err) {
        this.showToast('Network error saving contact', 'error');
      }
    });

    // 4. Invoice Form
    document.getElementById('invoiceForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const custSelect = document.getElementById('invCustomerSelect');
      const custId = custSelect.value;
      if (!custId) {
        this.showToast('Please select a customer', 'warning');
        return;
      }

      // Collect line items
      const rows = document.querySelectorAll('#invoiceRowsTbody tr');
      const itemRows = [];
      let subtotal = 0;

      rows.forEach(tr => {
        const itemSelect = tr.querySelector('.inv-item-select');
        const itemId = itemSelect?.value;
        const opt = itemSelect?.options[itemSelect.selectedIndex];
        const itemName = opt ? opt.text.split('(')[0].trim() : 'Item';
        const hsn = tr.querySelector('.inv-item-hsn')?.value.trim() || '00000000';
        const qty = parseFloat(tr.querySelector('.inv-item-qty')?.value || 0);
        const unit = tr.querySelector('.inv-item-unit')?.value.trim() || 'PCS';
        const rate = parseFloat(tr.querySelector('.inv-item-rate')?.value || 0);
        const amt = qty * rate;

        if (itemId && qty > 0) {
          subtotal += amt;
          itemRows.push({
            item_id: parseInt(itemId),
            item_name: itemName,
            hsn_code: hsn,
            quantity: qty,
            unit: unit,
            unit_price: rate,
            tax_rate: 18.0,
            discount: 0.0,
            tax_amount: (amt * 0.18),
            total_amount: amt
          });
        }
      });

      if (itemRows.length === 0) {
        this.showToast('Please add at least one product row to the invoice', 'warning');
        return;
      }

      const freight = parseFloat(document.getElementById('invFreightInput')?.value || 0);
      const taxable = subtotal + freight;
      const mode = document.getElementById('invTaxMode').value;

      let cgst = 0, sgst = 0, igst = 0;
      if (mode === 'intra') {
        cgst = taxable * 0.09;
        sgst = taxable * 0.09;
      } else if (mode === 'inter') {
        igst = taxable * 0.18;
      }

      const rawTotal = taxable + cgst + sgst + igst;
      const grandTotal = Math.round(rawTotal);
      const roundOff = grandTotal - rawTotal;

      const orderData = {
        invoice_number: document.getElementById('invNumber').value.trim(),
        customer_id: parseInt(custId),
        invoice_date: document.getElementById('invDate').value,
        payment_status: document.getElementById('invPaymentStatus').value,
        po_number: document.getElementById('invPoNumber').value.trim(),
        vehicle_no: document.getElementById('invVehicleNo').value.trim(),
        eway_bill_no: document.getElementById('invEwayBill').value.trim(),
        fiscal_year: '2026-2027',
        place_of_supply: custSelect.options[custSelect.selectedIndex].getAttribute('data-state') || 'Uttar Pradesh',
        subtotal: subtotal,
        freight: freight,
        cgst_amount: cgst,
        sgst_amount: sgst,
        igst_amount: igst,
        round_off: roundOff,
        total_amount: grandTotal,
        notes: document.getElementById('invNotes').value.trim()
      };

      try {
        const res = await fetch('/api/sales', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order: orderData, items: itemRows })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast('Tax Invoice created successfully!', 'success');
          this.closeModal('invoiceModal');
          
          // Open PDF directly in new tab
          if (data.id) {
            window.open(`/api/sales/${data.id}/pdf`, '_blank');
          }

          this.loadSales();
          this.loadDashboard();
        } else {
          this.showToast(data.error || 'Failed to create invoice', 'error');
        }
      } catch (err) {
        this.showToast('Network error creating invoice', 'error');
      }
    });

    // 5. Payment Form
    document.getElementById('paymentForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const body = {
        payment_type: document.getElementById('payType').value,
        contact_id: parseInt(document.getElementById('payContactSelect').value),
        amount: parseFloat(document.getElementById('payAmount').value || 0),
        payment_mode: document.getElementById('payMode').value,
        payment_date: document.getElementById('payDate').value,
        reference_no: document.getElementById('payRefNo').value.trim(),
        notes: document.getElementById('payNotes').value.trim()
      };

      try {
        const res = await fetch('/api/payments', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast('Payment successfully recorded!', 'success');
          this.closeModal('paymentModal');
          this.loadPayments();
          this.loadContacts();
          this.loadDashboard();
        } else {
          this.showToast(data.error || 'Failed to record payment', 'error');
        }
      } catch (err) {
        this.showToast('Network error recording payment', 'error');
      }
    });

    // 6. Company Profile Save
    document.getElementById('saveCompanyBtn')?.addEventListener('click', async (e) => {
      e.preventDefault();
      const body = {
        name: document.getElementById('compName').value.trim(),
        gstin: document.getElementById('compGstin').value.trim(),
        pan: document.getElementById('compPan').value.trim(),
        mobile: document.getElementById('compMobile').value.trim(),
        email: document.getElementById('compEmail').value.trim(),
        address: document.getElementById('compAddress').value.trim(),
        udyam_reg_no: document.getElementById('compUdyam').value.trim(),
        bank_name: document.getElementById('compBankName').value.trim(),
        bank_branch: document.getElementById('compBankBranch').value.trim(),
        account_no: document.getElementById('compAccountNo').value.trim(),
        ifsc_code: document.getElementById('compIfscCode').value.trim(),
        terms: document.getElementById('compTerms').value.trim()
      };

      try {
        const res = await fetch('/api/company', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast('Company profile updated successfully!', 'success');
        } else {
          this.showToast(data.error || 'Failed to update company profile', 'error');
        }
      } catch (err) {
        this.showToast('Network error saving profile', 'error');
      }
    });

    // 7. User Form
    document.getElementById('userForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const body = {
        username: document.getElementById('usrUsername').value.trim(),
        full_name: document.getElementById('usrFullName').value.trim(),
        role: document.getElementById('usrRole').value,
        password: document.getElementById('usrPassword').value.trim()
      };

      try {
        const res = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showToast(data.message, 'success');
          this.closeModal('userModal');
          this.loadUsers();
        } else {
          this.showToast(data.error || 'Failed to create user', 'error');
        }
      } catch (err) {
        this.showToast('Network error creating user', 'error');
      }
    });
  }

  // -------------------------------------------------------------
  // MODAL UTILITIES
  // -------------------------------------------------------------
  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('active');
  }

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
  }

  // -------------------------------------------------------------
  // TOAST NOTIFICATIONS
  // -------------------------------------------------------------
  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    toast.innerHTML = `
      <span style="font-size: 1.1rem;">${icons[type] || 'ℹ️'}</span>
      <span style="flex: 1;">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // -------------------------------------------------------------
  // HELPER FORMATTERS
  // -------------------------------------------------------------
  formatCurrency(amount) {
    const num = parseFloat(amount || 0);
    return '₹ ' + num.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  renderStatusBadge(status) {
    const st = (status || '').toLowerCase();
    if (st === 'paid') return '<span class="badge badge-success">Paid</span>';
    if (st === 'unpaid') return '<span class="badge badge-danger">Unpaid</span>';
    if (st === 'confirmed') return '<span class="badge badge-info">Confirmed</span>';
    if (st === 'cancelled') return '<span class="badge badge-neutral">Cancelled</span>';
    if (st === 'draft') return '<span class="badge badge-neutral">Draft</span>';
    return `<span class="badge badge-neutral">${status || 'Pending'}</span>`;
  }

  numberToWords(num) {
    const n = Math.round(Math.abs(num));
    if (n === 0) return 'Zero Rupees Only';

    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
      'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

    function convertLessThanThousand(val) {
      if (val === 0) return '';
      if (val < 20) return ones[val];
      if (val < 100) return tens[Math.floor(val / 10)] + (val % 10 !== 0 ? ' ' + ones[val % 10] : '');
      return ones[Math.floor(val / 100)] + ' Hundred' + (val % 100 !== 0 ? ' and ' + convertLessThanThousand(val % 100) : '');
    }

    let result = '';
    const crore = Math.floor(n / 10000000);
    const lakh = Math.floor((n % 10000000) / 100000);
    const thousand = Math.floor((n % 100000) / 1000);
    const remainder = n % 1000;

    if (crore > 0) result += convertLessThanThousand(crore) + ' Crore ';
    if (lakh > 0) result += convertLessThanThousand(lakh) + ' Lakh ';
    if (thousand > 0) result += convertLessThanThousand(thousand) + ' Thousand ';
    if (remainder > 0) result += convertLessThanThousand(remainder);

    return result.trim() + ' Rupees Only';
  }
}

// Global App Initialization
document.addEventListener('DOMContentLoaded', () => {
  window.app = new N3rahBookApp();
});
