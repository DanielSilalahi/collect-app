// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert-floating');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s, transform 0.5s';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
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
