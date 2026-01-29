// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', function() {

    // --- Message Alert Handling ---
    
    const messagesContainer = document.querySelector('.messages-container');
    if (messagesContainer) {
        const alerts = messagesContainer.querySelectorAll('.alert');
        
        // 1. Auto-hide flash messages after 5 seconds
        alerts.forEach(function(alert) {
            setTimeout(function() {
                // Add a fade-out effect
                alert.style.opacity = '0';
                
                // Remove the element after the fade-out transition
                setTimeout(function() {
                    alert.remove();
                }, 500); // Must match the CSS transition time
            }, 5000); // 5000ms = 5 seconds
        });
    }

    // 2. Make all .close-btn elements work
    // This replaces the inline 'onclick' and is better practice
    // We use event delegation on the container for efficiency
    if (messagesContainer) {
        messagesContainer.addEventListener('click', function(event) {
            // Check if the clicked element is a .close-btn
            if (event.target.classList.contains('close-btn')) {
                // Find the closest .alert parent
                const alert = event.target.closest('.alert');
                if (alert) {
                    // Trigger the fade-out effect
                    alert.style.opacity = '0';
                    
                    // Remove the element after the transition
                    setTimeout(function() {
                        alert.remove();
                    }, 500); // Must match the CSS transition time
                }
            }
        });
    }

});