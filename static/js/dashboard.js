/* ═══════════════════════════════════════════════════════════════
   Collection P2P — Dashboard JS
   Theme toggle + interactions + animations
   ═══════════════════════════════════════════════════════════════ */

// ── Theme Toggle ─────────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('col-theme');
    const theme = saved || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('col-theme', next);
}

// Apply theme ASAP (before DOMContentLoaded to prevent flash)
initTheme();

// ── DOM Ready ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-floating');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s, transform 0.5s';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
    });

    // Staggered fade-in animation for cards
    const animateEls = document.querySelectorAll('.animate-in');
    animateEls.forEach(function(el, i) {
        el.style.animationDelay = (i * 0.06) + 's';
    });

    // Select all checkbox
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateSelectedCount();
        });
    }

    // Row checkboxes
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    rowCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateSelectedCount);
    });
});

// ── Selection Helpers ────────────────────────────────────────
function updateSelectedCount() {
    const checked = document.querySelectorAll('.row-checkbox:checked');
    const assignBtn = document.getElementById('bulkAssignBtn');
    const deleteBtn = document.getElementById('bulkDeleteBtn');
    const selCount = document.getElementById('selectedCount');
    const delCount = document.getElementById('deleteCount');

    if (selCount) selCount.textContent = checked.length;
    if (delCount) delCount.textContent = checked.length;

    if (assignBtn) assignBtn.disabled = checked.length === 0;
    if (deleteBtn) deleteBtn.disabled = checked.length === 0;
}

function getSelectedIds() {
    const checked = document.querySelectorAll('.row-checkbox:checked');
    return Array.from(checked).map(cb => cb.value).join(',');
}

function submitAssign() {
    const ids = getSelectedIds();
    if (!ids) return;
    document.getElementById('assignCustomerIds').value = ids;
    document.getElementById('assignForm').submit();
}

function submitBulkDelete(url) {
    const ids = getSelectedIds();
    if (!ids) return;
    const count = document.querySelectorAll('.row-checkbox:checked').length;
    if (confirm(`Yakin ingin menghapus secara permanen ${count} customer yang dipilih?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'customer_ids';
        input.value = ids;
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    }
}

function confirmDelete(url, name) {
    if (confirm(`Hapus customer "${name}"?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        document.body.appendChild(form);
        form.submit();
    }
}
