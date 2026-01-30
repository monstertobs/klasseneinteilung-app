// Auto-dismiss alerts after 5 seconds with smooth animation
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Delete confirmation dialog
function confirmDelete(message) {
    return confirm(message || 'Wirklich löschen?');
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const inputs = form.querySelectorAll('[required]');
    let isValid = true;

    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            input.style.borderColor = '#ff3b30';
            isValid = false;
        } else {
            input.style.borderColor = '';
        }
    });

    return isValid;
}

// Password match check
function checkPasswordMatch() {
    const password = document.getElementById('password');
    const passwordConfirm = document.getElementById('password_confirm');

    if (password && passwordConfirm) {
        if (password.value !== passwordConfirm.value) {
            passwordConfirm.setCustomValidity('Passwörter stimmen nicht überein');
        } else {
            passwordConfirm.setCustomValidity('');
        }
    }
}

// Event listeners for password fields
document.addEventListener('DOMContentLoaded', function() {
    const passwordConfirm = document.getElementById('password_confirm');
    if (passwordConfirm) {
        passwordConfirm.addEventListener('input', checkPasswordMatch);
        document.getElementById('password').addEventListener('input', checkPasswordMatch);
    }
});
