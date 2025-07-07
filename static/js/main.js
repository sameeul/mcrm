// Main JavaScript for Secure Order Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const message = button.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Auto-refresh for dashboard (every 5 minutes)
    if (window.location.pathname === '/dashboard') {
        setInterval(function() {
            // Only refresh if user is still active (not idle)
            if (document.hasFocus()) {
                location.reload();
            }
        }, 300000); // 5 minutes
    }

    // Search form auto-submit delay
    const searchInputs = document.querySelectorAll('input[name="search"]');
    searchInputs.forEach(function(input) {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                if (input.value.length >= 3 || input.value.length === 0) {
                    input.form.submit();
                }
            }, 500);
        });
    });

    // Number input validation
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });

    // Price input formatting
    const priceInputs = document.querySelectorAll('input[step="0.01"]');
    priceInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Session timeout warning
    let sessionWarningShown = false;
    const sessionTimeout = 25 * 60 * 1000; // 25 minutes (5 minutes before 30-minute timeout)
    
    setTimeout(function() {
        if (!sessionWarningShown) {
            sessionWarningShown = true;
            showSessionWarning();
        }
    }, sessionTimeout);

    function showSessionWarning() {
        const warningHtml = `
            <div class="alert alert-warning alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x" 
                 style="z-index: 9999; margin-top: 20px;" role="alert">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Session Timeout Warning:</strong> Your session will expire in 5 minutes due to inactivity.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.body.insertAdjacentHTML('afterbegin', warningHtml);
    }

    // Reset session timeout on user activity
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    activityEvents.forEach(function(event) {
        document.addEventListener(event, function() {
            sessionWarningShown = false;
        }, true);
    });
});

// Utility functions
window.OrderManagement = {
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Show loading spinner
    showLoading: function(element) {
        const spinner = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>';
        element.innerHTML = spinner + element.innerHTML;
        element.disabled = true;
    },

    // Hide loading spinner
    hideLoading: function(element) {
        const spinner = element.querySelector('.spinner-border');
        if (spinner) {
            spinner.remove();
        }
        element.disabled = false;
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3" 
                 style="z-index: 9999;" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.querySelector('.toast:last-child');
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    },

    // Confirm action with custom modal
    confirmAction: function(title, message, confirmCallback) {
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmButton">Confirm</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const confirmButton = document.getElementById('confirmButton');
        
        confirmButton.addEventListener('click', function() {
            modal.hide();
            if (confirmCallback) {
                confirmCallback();
            }
        });
        
        modal.show();
        
        // Clean up modal after it's hidden
        document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.OrderManagement;
}
