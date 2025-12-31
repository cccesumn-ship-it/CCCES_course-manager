// Course Management System - Main JavaScript File

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Auto-hide alerts
    autoHideAlerts();
    
    // Confirm delete actions
    setupDeleteConfirmations();
    
    // Form validation
    setupFormValidation();
    
    // Search functionality
    setupSearch();
    
    // Table sorting
    setupTableSorting();
});

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap Popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Auto-hide alerts after 5 seconds
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Setup delete confirmations
function setupDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// Form validation
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {            

if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Table sorting
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(this.parentElement.children).indexOf(this);
            const currentOrder = this.getAttribute('data-order') || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Sort rows
            rows.sort(function(a, b) {
                const aValue = a.children[columnIndex].textContent.trim();
                const bValue = b.children[columnIndex].textContent.trim();
                
                if (newOrder === 'asc') {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });
            
            // Update table
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
            
            // Update header
            sortableHeaders.forEach(function(h) {
                h.removeAttribute('data-order');
            });
            this.setAttribute('data-order', newOrder);
        });
    });
}

// Show loading spinner
function showLoading(button) {
    if (button) {
        button.classList.add('loading');
        button.disabled = true;
    }
}

// Hide loading spinner
function hideLoading(button) {
    if (button) {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);    
const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Copy to clipboard
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
        if (button) {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(function() {
                button.innerHTML = originalText;
            }, 2000);
        }
    }).catch(function(err) {
        showToast('Failed to copy to clipboard', 'danger');
        console.error('Could not copy text: ', err);
    });
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(function(col) {
            csvRow.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(csvRow.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Print table
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Print</title>');
    printWindow.document.write('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">');
    printWindow.document.write('<style>body { padding: 20px; } table { width: 100%; }</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write(table.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

// Bulk selection for checkboxes
function setupBulkSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBulkActionButtons();
        });
    }
    
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    rowCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            updateBulkActionButtons();
        });
    });
}

// Update bulk action buttons based on selection
function updateBulkActionButtons() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn')    

if (checkedBoxes.length > 0) {
        bulkActionButtons.forEach(function(btn) {
            btn.disabled = false;
        });
    } else {
        bulkActionButtons.forEach(function(btn) {
            btn.disabled = true;
        });
    }
}

// Get selected IDs from checkboxes
function getSelectedIds() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const ids = [];
    checkedBoxes.forEach(function(checkbox) {
        ids.push(checkbox.value);
    });
    return ids;
}

// AJAX form submission
function submitFormAjax(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        
        showLoading(submitButton);
        
        fetch(form.action, {
            method: form.method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(submitButton);
            if (data.success) {
                if (successCallback) successCallback(data);
                showToast(data.message || 'Operation successful!', 'success');
            } else {
                if (errorCallback) errorCallback(data);
                showToast(data.message || 'Operation failed!', 'danger');
            }
        })
        .catch(error => {
            hideLoading(submitButton);
            if (errorCallback) errorCallback(error);
            showToast('An error occurred. Please try again.', 'danger');
            console.error('Error:', error);
        });
    });
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format date
function formatDate(dateString, format = 'short') {
    const date = new Date(dateString);
    const options = format === 'short' 
        ? { year: 'numeric', month: 'short', day: 'numeric' }
        : { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return date.toLocaleDateString('en-US', options);
}

// Validate email format
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate phone number
function isValidPhone(phone) {
    const re = /^[\d\s\-\(\)\+]+$/;
    return re.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Setup auto-resize for all textareas
document.querySelectorAll('textarea.auto-resize').forEach(function(textarea) {
    textarea.addEventListener('input', function() {
        autoResizeTextarea(this);
    });
    // Initial resize
    autoResizeTextarea(textarea);
});

// Character counter for inputs
function setupCharacterCounter() {
    const inputs = document.querySelectorAll('[data-max-length]');
    inputs.forEach(function(input) {
        const maxLength = input.getAttribute('data-max-length');
        const counterId = input.id + '-counter';
        
        // Create counter element       

const counter = document.createElement('small');
        counter.id = counterId;
        counter.className = 'text-muted';
        input.parentElement.appendChild(counter);
        
        // Update counter
        function updateCounter() {
            const remaining = maxLength - input.value.length;
            counter.textContent = remaining + ' characters remaining';
            if (remaining < 0) {
                counter.classList.add('text-danger');
                counter.classList.remove('text-muted');
            } else {
                counter.classList.remove('text-danger');
                counter.classList.add('text-muted');
            }
        }
        
        input.addEventListener('input', updateCounter);
        updateCounter(); // Initial count
    });
}

// File size validation
function validateFileSize(input, maxSizeMB = 10) {
    const files = input.files;
    let valid = true;
    
    for (let i = 0; i < files.length; i++) {
        const fileSizeMB = files[i].size / 1024 / 1024;
        if (fileSizeMB > maxSizeMB) {
            showToast(`File "${files[i].name}" exceeds ${maxSizeMB}MB limit`, 'danger');
            valid = false;
        }
    }
    
    if (!valid) {
        input.value = '';
    }
    
    return valid;
}

// Confirm navigation away from unsaved changes
function setupUnsavedChangesWarning() {
    let formChanged = false;
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                formChanged = true;
            });
        });
        
        form.addEventListener('submit', function() {
            formChanged = false;
        });
    });
    
    window.addEventListener('beforeunload', function(e) {
        if (formChanged) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });
}

// Initialize character counter on page load
setupCharacterCounter();

// Export functions for global use
window.showToast = showToast;
window.copyToClipboard = copyToClipboard;
window.exportTableToCSV = exportTableToCSV;
window.printTable = printTable;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.getSelectedIds = getSelectedIds;
window.isValidEmail = isValidEmail;
window.isValidPhone = isValidPhone;
window.formatDate = formatDate;
window.validateFileSize = validateFileSize;