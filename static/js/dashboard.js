// LogHive - Frontend JavaScript

// Global state
let sitesData = [];
let currentSite = 'all';
let currentLogSearchSite = 'all';
let historyChart = null;

// ==================== Initialization ====================



async function loadData() {
    try {
        const response = await fetch('/api/summary');
        if (!response.ok) throw new Error('Failed to load data');
        sitesData = await response.json();

        renderTabs();
        renderCards();
        updateOverviewStats();
    } catch (error) {
        console.error('Error loading data:', error);
        showEmptyState();
    }
}

// Refresh data function with modern visual feedback
async function refreshData() {
    const refreshBtn = event?.currentTarget;
    const icon = refreshBtn?.querySelector('svg');

    // Disable button during refresh
    if (refreshBtn) {
        refreshBtn.disabled = true;
    }

    // Add spinning animation to the icon using CSS class
    if (icon) {
        icon.classList.add('spinning');
    }

    // Add loading state to cards
    const statsOverview = document.getElementById('stats-overview');
    const sitesGrid = document.getElementById('sites-grid');

    if (statsOverview) {
        statsOverview.style.opacity = '0.5';
        statsOverview.style.pointerEvents = 'none';
    }

    if (sitesGrid) {
        sitesGrid.style.opacity = '0.5';
        sitesGrid.style.pointerEvents = 'none';
    }

    try {
        await loadData();

        // Fade in effect for updated content
        if (statsOverview) {
            statsOverview.style.transition = 'opacity 0.3s ease-in';
            statsOverview.style.opacity = '0';
            setTimeout(() => {
                statsOverview.style.opacity = '1';
                statsOverview.style.pointerEvents = 'auto';
            }, 100);
        }

        if (sitesGrid) {
            sitesGrid.style.transition = 'opacity 0.3s ease-in';
            sitesGrid.style.opacity = '0';
            setTimeout(() => {
                sitesGrid.style.opacity = '1';
                sitesGrid.style.pointerEvents = 'auto';
            }, 100);
        }

        // Show success toast
        showToast('資料已更新', 'success');

        // Also update button text for feedback
        if (refreshBtn) {
            const btnText = refreshBtn.querySelector('span');
            if (btnText) {
                const originalText = btnText.textContent;
                btnText.textContent = '已更新';

                // Add success color class specifically for success state
                refreshBtn.style.borderColor = 'var(--accent-secondary)';
                refreshBtn.style.color = 'var(--accent-secondary)';

                setTimeout(() => {
                    btnText.textContent = originalText;
                    refreshBtn.style.borderColor = '';
                    refreshBtn.style.color = '';
                }, 1500);
            }
        }

    } catch (error) {
        console.error('Error refreshing data:', error);
        showToast('重新載入資料失敗', 'error');

        // Restore opacity on error
        if (statsOverview) {
            statsOverview.style.opacity = '1';
            statsOverview.style.pointerEvents = 'auto';
        }
        if (sitesGrid) {
            sitesGrid.style.opacity = '1';
            sitesGrid.style.pointerEvents = 'auto';
        }
    } finally {
        // Stop spinning animation
        if (icon) {
            icon.classList.remove('spinning');
        }

        // Re-enable button
        if (refreshBtn) {
            refreshBtn.disabled = false;
        }
    }
}

// Modern toast notification function
function showToast(message, type = 'success') {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;

    const icon = type === 'success'
        ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
           </svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
           </svg>`;

    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-message">${message}</div>
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}


// ==================== Demo Data ====================

async function seedDemoData() {
    const btn = event?.currentTarget;
    let originalHtml = '';

    // Add loading state
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.disabled = true;
        // Use a spinner icon and change text
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spinning">
                <line x1="12" y1="2" x2="12" y2="6"></line>
                <line x1="12" y1="18" x2="12" y2="22"></line>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                <line x1="2" y1="12" x2="6" y2="12"></line>
                <line x1="18" y1="12" x2="22" y2="12"></line>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
            </svg>
            處理中...
        `;
    }

    try {
        const response = await fetch('/api/demo/seed');
        const result = await response.json();

        if (response.ok && result.success) {
            // Update button to success state
            if (btn) {
                btn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    載入完成
                `;
                btn.style.borderColor = 'var(--accent-secondary)';
                btn.style.color = 'var(--accent-secondary)';
            }

            showToast('測試數據已載入，頁面將重新整理', 'success');

            // Wait a bit for the toast to be seen before reloading
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            // Restore button on logic error
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
            showToast(result.error || result.message || '載入測試數據失敗', 'error');
        }
    } catch (error) {
        console.error('Error seeding data:', error);
        // Restore button on exception
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
        showToast('載入測試數據失敗', 'error');
    }
}

// ==================== Rendering ====================

function renderTabs() {
    const tabsContainer = document.getElementById('site-tabs');

    // Get unique sites
    const sites = [...new Set(sitesData.map(d => d.site))];

    let html = `<button class="site-tab ${currentSite === 'all' ? 'active' : ''}" onclick="filterBySite('all')">全部</button>`;

    sites.forEach(site => {
        html += `<button class="site-tab ${currentSite === site ? 'active' : ''}" onclick="filterBySite('${site}')">${site}</button>`;
    });

    tabsContainer.innerHTML = html;
}

function renderCards() {
    const grid = document.getElementById('sites-grid');

    // Filter data by current site
    let filteredData = sitesData;
    if (currentSite !== 'all') {
        filteredData = sitesData.filter(d => d.site === currentSite);
    }

    if (filteredData.length === 0) {
        grid.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">📭</div>
                <p>尚無數據，請點擊「載入測試數據」或等待 Agent 回報</p>
            </div>
        `;
        return;
    }

    // Group by site and sub_site
    const grouped = {};
    filteredData.forEach(item => {
        const key = `${item.site}-${item.sub_site}`;
        if (!grouped[key]) {
            grouped[key] = {
                site: item.site,
                sub_site: item.sub_site,
                servers: []
            };
        }
        grouped[key].servers.push(item);
    });

    let html = '';
    Object.values(grouped).forEach(group => {
        html += renderSiteCard(group);
    });

    grid.innerHTML = html;
}

function renderSiteCard(group) {
    const { site, sub_site, servers } = group;

    let serversHtml = '';
    servers.forEach(server => {
        const sizeFormatted = formatSize(server.size_mb);
        const avgGrowth = server.monthly_avg_growth || 0;
        const growthFormatted = formatSize(Math.abs(avgGrowth));
        const growthClass = avgGrowth >= 0 ? 'positive' : 'negative';
        const growthIcon = avgGrowth >= 0
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>`
            : `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;

        // NOTE: User requested to REMOVE Log Link from Dashboard view
        // So we just render the basic info

        serversHtml += `
            <div class="server-item" onclick="showDetails('${site}', '${sub_site}', '${server.server_type}')">
                <div class="server-info">
                    <span class="server-name">${formatServerType(server.server_type)}</span>
                    <span class="server-path">/data</span>
                </div>
                <div class="server-right-panel">
                    <div class="server-stats">
                        <div class="server-size">${sizeFormatted}</div>
                        <div class="server-growth ${growthClass}">
                            ${growthIcon} ${growthFormatted} / 月均
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    return `
        <div class="site-card">
            <div class="site-card-header">
                <div class="site-name">
                    ${sub_site}
                    <span class="badge">${site}</span>
                </div>
            </div>
            <div class="site-card-body">
                ${serversHtml}
            </div>
        </div>
    `;
}

// ==================== Log Search Logic ====================

function renderLogSearchTabs() {
    const tabsContainer = document.getElementById('log-search-tabs');
    const sites = [...new Set(sitesData.map(d => d.site))];

    let html = `<button class="site-tab ${currentLogSearchSite === 'all' ? 'active' : ''}" onclick="filterLogSearchBySite('all')">全部</button>`;

    sites.forEach(site => {
        html += `<button class="site-tab ${currentLogSearchSite === site ? 'active' : ''}" onclick="filterLogSearchBySite('${site}')">${site}</button>`;
    });

    tabsContainer.innerHTML = html;
}

function filterLogSearchBySite(site) {
    currentLogSearchSite = site;
    renderLogSearchTabs();
    renderLogSearch();
}

function renderLogSearch() {
    const container = document.getElementById('log-search-grid');

    // Filter data by current tab
    let filteredData = sitesData;
    if (currentLogSearchSite !== 'all') {
        filteredData = filteredData.filter(d => d.site === currentLogSearchSite);
    }

    if (filteredData.length === 0) {
        container.innerHTML = '<p class="no-data-text">尚無資料</p>';
        return;
    }

    // Group by sub_site
    const grouped = {};
    filteredData.forEach(item => {
        if (!grouped[item.sub_site]) {
            grouped[item.sub_site] = {
                items: [],
                site: item.site // keep reference to parent site
            };
        }
        grouped[item.sub_site].items.push(item);
    });

    // Sort sub_sites (optional, alphabetical)
    const sortedSubSites = Object.keys(grouped).sort();

    let html = '';
    sortedSubSites.forEach(subSite => {
        const group = grouped[subSite];
        const { site, items } = group;

        let cardsHtml = '';
        items.forEach(server => {
            const typeName = formatServerType(server.server_type);
            cardsHtml += `
                <a href="/" class="log-search-card">
                    <div class="log-card-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </div>
                    <div class="log-card-info">
                        <h3>${typeName}</h3>
                        <p>點擊返回主頁</p>
                    </div>
                </a>
            `;
        });

        html += `
            <div class="sub-site-group">
                <div class="sub-site-header">
                    <h2>${subSite}</h2>
                    <span class="sub-site-badge">${site}</span>
                </div>
                <div class="sub-site-grid">
                    ${cardsHtml}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ==================== View Switching ====================

function switchView(viewName) {
    // Update Sidebar
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
        if (el.getAttribute('onclick').includes(viewName)) {
            el.classList.add('active');
        }
    });

    // Update Main Content
    document.querySelectorAll('.view-section').forEach(el => {
        el.style.display = 'none';
        el.classList.remove('active');
    });

    const activeView = document.getElementById(`${viewName}-view`);
    if (activeView) {
        activeView.style.display = 'block';
        setTimeout(() => activeView.classList.add('active'), 10); // Fade in
    }

    // Specific Logic
    if (viewName === 'log-search') {
        renderLogSearchTabs();
        renderLogSearch();
    }

    // Auto-close sidebar on mobile
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.remove('active');
        document.querySelector('.sidebar-overlay').classList.remove('active');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

// ==================== Theme Toggle ====================

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme);
}

function applyTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcons(savedTheme);
}

function updateThemeIcons(theme) {
    const sunIcons = document.querySelectorAll('.sun-icon');
    const moonIcons = document.querySelectorAll('.moon-icon');

    if (theme === 'light') {
        sunIcons.forEach(icon => icon.style.display = 'none');
        moonIcons.forEach(icon => icon.style.display = 'block');
    } else {
        sunIcons.forEach(icon => icon.style.display = 'block');
        moonIcons.forEach(icon => icon.style.display = 'none');
    }
}

// ==================== User Menu ====================

function toggleUserMenu(event) {
    if (event) event.stopPropagation();

    // Find the dropdown relative to the clicked element (works for both desktop and mobile)
    const container = event.currentTarget.closest('.user-menu-container');
    const dropdown = container ? container.querySelector('.dropdown-menu') : null;
    const button = event.currentTarget;

    if (dropdown) {
        // close other open dropdowns first to avoid confusion
        document.querySelectorAll('.dropdown-menu.show').forEach(d => {
            if (d !== dropdown) {
                d.classList.remove('show');
                // Find and update aria-expanded for other buttons
                const otherButton = d.closest('.user-menu-container').querySelector('[aria-expanded]');
                if (otherButton) otherButton.setAttribute('aria-expanded', 'false');
            }
        });

        const isShowing = dropdown.classList.toggle('show');

        // Update aria-expanded
        if (button && button.hasAttribute('aria-expanded')) {
            button.setAttribute('aria-expanded', isShowing ? 'true' : 'false');
        }
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', (event) => {
    // If click is not inside a user menu container, close all open dropdowns
    if (!event.target.closest('.user-menu-container')) {
        document.querySelectorAll('.dropdown-menu.show').forEach(dropdown => {
            dropdown.classList.remove('show');
            // Update aria-expanded
            const button = dropdown.closest('.user-menu-container').querySelector('[aria-expanded]');
            if (button) button.setAttribute('aria-expanded', 'false');
        });
    }
});

// ==================== Sidebar Collapse ====================

function toggleSidebarCollapse() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');

    // Save state
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed);
}

function initSidebarState() {
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const sidebar = document.getElementById('sidebar');

    // Only apply collapsed state on desktop by default
    if (isCollapsed && window.innerWidth > 768) {
        sidebar.classList.add('collapsed');
    }
}

// Initialize theme and sidebar on load
document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    initSidebarState();
    loadData();
});

function updateOverviewStats() {
    // Count unique sub-sites
    const subSites = new Set(sitesData.map(d => `${d.site}-${d.sub_site}`));
    document.getElementById('total-sites').textContent = subSites.size || '-';

    // Site_B total size
    const siteBSize = sitesData
        .filter(d => d.site === 'Site_B')
        .reduce((sum, d) => sum + (d.size_mb || 0), 0);
    document.getElementById('siteb-size').textContent = formatSize(siteBSize);

    // Site_A total size
    const siteASize = sitesData
        .filter(d => d.site === 'Site_A')
        .reduce((sum, d) => sum + (d.size_mb || 0), 0);
    document.getElementById('sitea-size').textContent = formatSize(siteASize);

    // Total 30-day growth
    const totalGrowth = sitesData.reduce((sum, d) => sum + (d.growth_30d || 0), 0);
    document.getElementById('avg-growth').textContent = formatSize(totalGrowth);
}

function showEmptyState() {
    const grid = document.getElementById('sites-grid');
    grid.innerHTML = `
        <div class="no-data">
            <div class="no-data-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"></polyline>
                    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path>
                </svg>
            </div>
            <p>尚無數據，請點擊「載入測試數據」或等待 Agent 回報</p>
        </div>
    `;

    document.getElementById('total-sites').textContent = '-';
    document.getElementById('siteb-size').textContent = '-';
    document.getElementById('sitea-size').textContent = '-';
    document.getElementById('avg-growth').textContent = '-';
}

// ==================== Filtering ====================

function filterBySite(site) {
    currentSite = site;
    renderTabs();
    renderCards();
}

// ==================== Modal & Chart ====================

async function showDetails(site, subSite, serverType) {
    const modal = document.getElementById('detail-modal');
    const title = document.getElementById('modal-title');
    const statsContainer = document.getElementById('modal-stats');

    title.textContent = `${subSite} - ${formatServerType(serverType)}`;
    modal.classList.add('active');

    try {
        // Fetch history data
        const response = await fetch(`/api/history/${site}/${subSite}/${serverType}?days=30`);
        const history = await response.json();

        // Fetch month production data
        const monthResponse = await fetch(`/api/month-production/${site}/${subSite}/${serverType}`);
        const monthData = await monthResponse.json();

        // Render chart
        renderChart(history);

        // Render stats with current month, previous month, and average
        const currentData = sitesData.find(d =>
            d.site === site && d.sub_site === subSite && d.server_type === serverType
        );

        statsContainer.innerHTML = `
            <div class="modal-stat">
                <div class="modal-stat-value">${formatSize(currentData?.size_mb || 0)}</div>
                <div class="modal-stat-label">目前大小</div>
            </div>
            <div class="modal-stat">
                <div class="modal-stat-value">${formatSize(monthData.current_month_growth || 0)}</div>
                <div class="modal-stat-label">當月產量</div>
            </div>
            <div class="modal-stat">
                <div class="modal-stat-value">${formatSize(monthData.previous_month_growth || 0)}</div>
                <div class="modal-stat-label">前月產量</div>
            </div>
            <div class="modal-stat">
                <div class="modal-stat-value">${formatSize(currentData?.monthly_avg_growth || 0)}</div>
                <div class="modal-stat-label">每月平均產量</div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading details:', error);
        statsContainer.innerHTML = '<p>載入詳細資料失敗</p>';
    }
}

function renderChart(history) {
    const ctx = document.getElementById('history-chart').getContext('2d');

    // Destroy existing chart
    if (historyChart) {
        historyChart.destroy();
    }

    const labels = history.map(h => {
        const date = new Date(h.recorded_at);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    const data = history.map(h => h.size_mb);

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '資料夾大小 (MB)',
                data: data,
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#58a6ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#8b949e'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#8b949e',
                        callback: function (value) {
                            return formatSize(value);
                        }
                    }
                }
            }
        }
    });
}

function closeModal() {
    const modal = document.getElementById('detail-modal');
    modal.classList.remove('active');
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ==================== Utilities ====================

function formatSize(mb) {
    if (mb === null || mb === undefined || isNaN(mb)) return '-';

    if (mb >= 1024 * 1024) {
        return (mb / (1024 * 1024)).toFixed(2) + ' TB';
    } else if (mb >= 1024) {
        return (mb / 1024).toFixed(2) + ' GB';
    } else {
        return mb.toFixed(1) + ' MB';
    }
}

function formatServerType(type) {
    const names = {
        'log_server': 'Log Server',
        'backup_server': 'Backup Server',
        'backup_log_server': 'Backup Log Server'
    };
    return names[type] || type;
}
