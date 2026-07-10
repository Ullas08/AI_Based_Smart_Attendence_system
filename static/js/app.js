/**
 * FaceAttend — Main JavaScript
 * Handles: theme toggle, sidebar, notifications, toast, date display
 */

// ── Theme Management ──────────────────────────────────────────────────────
const THEME_KEY = 'faceattend_theme';

function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || 'dark';
    applyTheme(saved);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
    }
    localStorage.setItem(THEME_KEY, theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ── Sidebar Management ────────────────────────────────────────────────────
const SIDEBAR_KEY = 'faceattend_sidebar';

function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    // Desktop collapsed state
    const collapsed = localStorage.getItem(SIDEBAR_KEY) === 'collapsed';
    if (collapsed) collapseSidebar(false);

    // Desktop toggle button
    const toggleBtn = document.getElementById('sidebarToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (sidebar.classList.contains('collapsed')) {
                expandSidebar();
            } else {
                collapseSidebar();
            }
        });
    }

    // Mobile menu button
    const mobileBtn = document.getElementById('mobileMenuBtn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 992 && sidebar.classList.contains('mobile-open')) {
            if (!sidebar.contains(e.target) && e.target !== mobileBtn) {
                sidebar.classList.remove('mobile-open');
            }
        }
    });
}

function collapseSidebar(save = true) {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.classList.add('collapsed');
    const icon = sidebar.querySelector('#sidebarToggle i');
    if (icon) icon.className = 'bi bi-chevron-right';
    if (save) localStorage.setItem(SIDEBAR_KEY, 'collapsed');
}

function expandSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.classList.remove('collapsed');
    const icon = sidebar.querySelector('#sidebarToggle i');
    if (icon) icon.className = 'bi bi-chevron-left';
    localStorage.setItem(SIDEBAR_KEY, 'expanded');
}

// ── Toast Notifications ───────────────────────────────────────────────────
const TOAST_ICONS = {
    success: 'bi-check-circle-fill',
    error:   'bi-x-circle-fill',
    info:    'bi-info-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
};

window.showToast = function(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
        <i class="bi ${TOAST_ICONS[type] || TOAST_ICONS.info} toast-icon"></i>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x"></i>
        </button>
    `;
    container.appendChild(toast);

    // Add to notification panel
    addNotification(message, type);

    setTimeout(() => {
        toast.style.animation = 'slideLeft 0.25s ease reverse';
        setTimeout(() => toast.remove(), 250);
    }, duration);
};

// ── Notification Panel ────────────────────────────────────────────────────
let notifCount = 0;

function addNotification(message, type) {
    const list = document.getElementById('notifList');
    const badge = document.getElementById('notifBadge');
    if (!list || !badge) return;

    const empty = list.querySelector('.notif-empty');
    if (empty) empty.remove();

    notifCount++;
    badge.textContent = notifCount;
    badge.style.display = 'flex';

    const item = document.createElement('div');
    item.className = 'notif-item';
    item.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px">
            <i class="bi ${TOAST_ICONS[type]} text-${type === 'error' ? 'danger' : type}" style="font-size:14px"></i>
            <span style="font-size:13px">${message}</span>
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${new Date().toLocaleTimeString()}</div>
    `;
    list.insertBefore(item, list.firstChild);
}

function initNotifications() {
    const btn = document.getElementById('notifBtn');
    const dropdown = document.getElementById('notifDropdown');
    if (!btn || !dropdown) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
        if (dropdown.classList.contains('open')) {
            notifCount = 0;
            const badge = document.getElementById('notifBadge');
            if (badge) badge.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== btn) {
            dropdown.classList.remove('open');
        }
    });
}

// ── Date Display ──────────────────────────────────────────────────────────
function initDateDisplay() {
    const el = document.getElementById('topbarDate');
    if (!el) return;

    const update = () => {
        el.textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'short', year: 'numeric',
            month: 'short', day: 'numeric'
        });
    };
    update();
    setInterval(update, 60000);
}

// ── Flash Message Auto-dismiss ────────────────────────────────────────────
function initFlashMessages() {
    const container = document.getElementById('flashContainer');
    if (!container) return;
    setTimeout(() => {
        container.querySelectorAll('.flash-alert').forEach(el => {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        });
    }, 5000);
}

// ── Initialize Everything ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    initNotifications();
    initDateDisplay();
    initFlashMessages();

    // Theme toggle button
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) themeBtn.addEventListener('click', toggleTheme);
});
