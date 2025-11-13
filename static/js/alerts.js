// Get CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

// DOM elements
const alertItemInput = document.getElementById('alertItemInput');
const alertType = document.getElementById('alertType');
const alertThreshold = document.getElementById('alertThreshold');
const createAlertBtn = document.getElementById('createAlertBtn');
const checkAlertsBtn = document.getElementById('checkAlertsBtn');
const alertsList = document.getElementById('alertsList');
const notificationsList = document.getElementById('notificationsList');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const alertAutocomplete = document.getElementById('alertAutocomplete');
const notificationBadge = document.getElementById('notificationBadge');

// State
let currentItemId = null;
let currentItemName = null;
let autocompleteTimeout = null;
let selectedSuggestionIndex = -1;

// Initialize
loadAlerts();
loadNotifications();
updateNotificationBadge();

// Event listeners
createAlertBtn.addEventListener('click', createAlert);
checkAlertsBtn.addEventListener('click', checkAlerts);
alertItemInput.addEventListener('input', handleAutocomplete);
alertItemInput.addEventListener('keydown', handleAutocompleteKeydown);

// Close autocomplete when clicking outside
document.addEventListener('click', (e) => {
    if (e.target !== alertItemInput) {
        closeAutocomplete();
    }
});

// Functions
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.add('show');
    setTimeout(() => {
        successMessage.classList.remove('show');
    }, 5000);
}

function handleAutocomplete() {
    clearTimeout(autocompleteTimeout);
    const query = alertItemInput.value.trim();
    
    if (query.length < 2) {
        closeAutocomplete();
        currentItemId = null;
        currentItemName = null;
        return;
    }
    
    // Debounce autocomplete requests
    autocompleteTimeout = setTimeout(() => {
        fetch(`/api/autocomplete?query=${encodeURIComponent(query)}`)
            .then(async response => {
                if (!response.ok) {
                    return [];
                }
                try {
                    return await response.json();
                } catch (e) {
                    console.error('Autocomplete parsing error:', e);
                    return [];
                }
            })
            .then(suggestions => {
                displaySuggestions(suggestions);
            })
            .catch(error => {
                console.error('Autocomplete error:', error);
            });
    }, 300);
}

function displaySuggestions(suggestions) {
    closeAutocomplete();
    selectedSuggestionIndex = -1;
    
    if (suggestions.length === 0) {
        return;
    }
    
    suggestions.forEach((suggestion, index) => {
        const div = document.createElement('div');
        div.className = 'autocomplete-item';
        div.textContent = suggestion;
        div.addEventListener('click', () => {
            alertItemInput.value = suggestion;
            currentItemName = suggestion;
            // Search for item ID
            searchItemId(suggestion);
            closeAutocomplete();
        });
        alertAutocomplete.appendChild(div);
    });
}

function closeAutocomplete() {
    alertAutocomplete.innerHTML = '';
    selectedSuggestionIndex = -1;
}

function handleAutocompleteKeydown(e) {
    const items = alertAutocomplete.getElementsByClassName('autocomplete-item');
    
    if (items.length === 0) {
        return;
    }
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedSuggestionIndex++;
        if (selectedSuggestionIndex >= items.length) {
            selectedSuggestionIndex = 0;
        }
        updateSelectedSuggestion(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedSuggestionIndex--;
        if (selectedSuggestionIndex < 0) {
            selectedSuggestionIndex = items.length - 1;
        }
        updateSelectedSuggestion(items);
    } else if (e.key === 'Enter' && selectedSuggestionIndex >= 0) {
        e.preventDefault();
        alertItemInput.value = items[selectedSuggestionIndex].textContent;
        currentItemName = items[selectedSuggestionIndex].textContent;
        searchItemId(currentItemName);
        closeAutocomplete();
    }
}

function updateSelectedSuggestion(items) {
    for (let i = 0; i < items.length; i++) {
        items[i].classList.remove('autocomplete-active');
    }
    if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < items.length) {
        items[selectedSuggestionIndex].classList.add('autocomplete-active');
    }
}

function searchItemId(itemName) {
    fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ itemName: itemName })
    })
    .then(async response => {
        if (!response.ok) {
            throw new Error('Item not found');
        }
        return await response.json();
    })
    .then(data => {
        currentItemId = data.itemNumber;
        currentItemName = data.itemName;
    })
    .catch(error => {
        console.error('Search error:', error);
        currentItemId = null;
    });
}

function createAlert() {
    const itemName = alertItemInput.value.trim();
    const type = alertType.value;
    const threshold = parseFloat(alertThreshold.value);
    
    if (!itemName) {
        showError('Please enter an item name');
        return;
    }
    
    if (!currentItemId) {
        showError('Please select a valid item from the suggestions');
        return;
    }
    
    if (!threshold || threshold <= 0 || threshold > 100) {
        showError('Threshold must be between 0 and 100');
        return;
    }
    
    createAlertBtn.disabled = true;
    createAlertBtn.textContent = 'Creating...';
    
    fetch('/api/alerts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            item_id: currentItemId,
            item_name: currentItemName,
            alert_type: type,
            threshold: threshold
        })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create alert');
        }
        return data;
    })
    .then(data => {
        showSuccess('Alert created successfully!');
        alertItemInput.value = '';
        currentItemId = null;
        currentItemName = null;
        alertThreshold.value = '5';
        loadAlerts();
    })
    .catch(error => {
        showError(error.message);
    })
    .finally(() => {
        createAlertBtn.disabled = false;
        createAlertBtn.textContent = 'Create Alert';
    });
}

function loadAlerts() {
    fetch('/api/alerts')
        .then(async response => {
            if (!response.ok) {
                throw new Error('Failed to load alerts');
            }
            return await response.json();
        })
        .then(alerts => {
            displayAlerts(alerts);
        })
        .catch(error => {
            console.error('Load alerts error:', error);
            alertsList.innerHTML = '<p class="error">Failed to load alerts</p>';
        });
}

function displayAlerts(alerts) {
    if (alerts.length === 0) {
        alertsList.innerHTML = '<p class="no-data">No alerts created yet. Create your first alert above!</p>';
        return;
    }
    
    alertsList.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertCard = document.createElement('div');
        alertCard.className = `alert-card ${alert.is_active ? 'active' : 'inactive'}`;
        
        const alertTypeLabel = {
            'spike': 'Price Spike ↑',
            'dip': 'Price Dip ↓',
            'fluctuation': 'Fluctuation ↕'
        }[alert.alert_type] || alert.alert_type;
        
        const lastChecked = alert.last_checked 
            ? `Last checked: ${formatDate(alert.last_checked)}`
            : 'Not checked yet';
        
        const lastTriggered = alert.last_triggered
            ? `<span class="triggered">Last triggered: ${formatDate(alert.last_triggered)}</span>`
            : '';
        
        alertCard.innerHTML = `
            <div class="alert-header">
                <h3>${alert.item_name}</h3>
                <div class="alert-actions">
                    <button class="btn-toggle" onclick="toggleAlert(${alert.id})" title="${alert.is_active ? 'Deactivate' : 'Activate'}">
                        ${alert.is_active ? '⏸' : '▶'}
                    </button>
                    <button class="btn-delete" onclick="deleteAlert(${alert.id})" title="Delete">
                        ✕
                    </button>
                </div>
            </div>
            <div class="alert-details">
                <p><strong>Type:</strong> ${alertTypeLabel}</p>
                <p><strong>Threshold:</strong> ${alert.threshold}%</p>
                ${alert.baseline_price ? `<p><strong>Baseline Price:</strong> ${alert.baseline_price.toLocaleString()} gp</p>` : ''}
                <p class="alert-status">${lastChecked}</p>
                ${lastTriggered}
            </div>
        `;
        
        alertsList.appendChild(alertCard);
    });
}

function toggleAlert(alertId) {
    fetch(`/api/alerts/${alertId}/toggle`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to toggle alert');
        }
        return data;
    })
    .then(data => {
        showSuccess(data.message);
        loadAlerts();
    })
    .catch(error => {
        showError(error.message);
    });
}

function deleteAlert(alertId) {
    if (!confirm('Are you sure you want to delete this alert?')) {
        return;
    }
    
    fetch(`/api/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete alert');
        }
        return data;
    })
    .then(data => {
        showSuccess(data.message);
        loadAlerts();
    })
    .catch(error => {
        showError(error.message);
    });
}

function checkAlerts() {
    checkAlertsBtn.disabled = true;
    checkAlertsBtn.textContent = 'Checking...';
    
    fetch('/api/check-alerts', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to check alerts');
        }
        return data;
    })
    .then(data => {
        showSuccess(data.message);
        loadAlerts();
        loadNotifications();
        updateNotificationBadge();
    })
    .catch(error => {
        showError(error.message);
    })
    .finally(() => {
        checkAlertsBtn.disabled = false;
        checkAlertsBtn.textContent = 'Check Now';
    });
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(async response => {
            if (!response.ok) {
                throw new Error('Failed to load notifications');
            }
            return await response.json();
        })
        .then(notifications => {
            displayNotifications(notifications);
        })
        .catch(error => {
            console.error('Load notifications error:', error);
            notificationsList.innerHTML = '<p class="error">Failed to load notifications</p>';
        });
}

function displayNotifications(notifications) {
    if (notifications.length === 0) {
        notificationsList.innerHTML = '<p class="no-data">No notifications yet. Alerts will appear here when triggered.</p>';
        return;
    }
    
    notificationsList.innerHTML = '';
    
    notifications.forEach(notif => {
        const notifCard = document.createElement('div');
        notifCard.className = `notification-card ${notif.is_read ? 'read' : 'unread'}`;
        
        const alertTypeIcon = {
            'spike': '↑',
            'dip': '↓',
            'fluctuation': '↕'
        }[notif.alert_type] || '';
        
        const changeClass = notif.price_change >= 0 ? 'positive' : 'negative';
        const changeSign = notif.price_change >= 0 ? '+' : '';
        
        notifCard.innerHTML = `
            <div class="notification-header">
                <h3>${alertTypeIcon} ${notif.item_name}</h3>
                <span class="notification-time">${formatDate(notif.created_at)}</span>
            </div>
            <div class="notification-details">
                <p><strong>Price Change:</strong> <span class="${changeClass}">${changeSign}${notif.price_change.toFixed(2)}%</span></p>
                ${notif.old_price ? `<p><strong>Old Price:</strong> ${notif.old_price.toLocaleString()} gp</p>` : ''}
                <p><strong>New Price:</strong> ${notif.new_price.toLocaleString()} gp</p>
            </div>
            ${!notif.is_read ? `<button class="btn-mark-read" onclick="markRead(${notif.id})">Mark as Read</button>` : ''}
        `;
        
        notificationsList.appendChild(notifCard);
    });
}

function markRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to mark notification as read');
        }
        return data;
    })
    .then(() => {
        loadNotifications();
        updateNotificationBadge();
    })
    .catch(error => {
        console.error('Mark read error:', error);
    });
}

function updateNotificationBadge() {
    fetch('/api/notifications/unread-count')
        .then(async response => {
            if (!response.ok) {
                throw new Error('Failed to get unread count');
            }
            return await response.json();
        })
        .then(data => {
            if (data.count > 0) {
                notificationBadge.textContent = data.count;
                notificationBadge.style.display = 'block';
            } else {
                notificationBadge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Update badge error:', error);
        });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Auto-refresh notifications every 30 seconds
setInterval(() => {
    updateNotificationBadge();
}, 30000);
