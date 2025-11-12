let allTrades = [];
let filteredTrades = [];

// DOM elements
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');
const tradesContainer = document.getElementById('tradesContainer');
const tradesTableBody = document.getElementById('tradesTableBody');
const minMarginInput = document.getElementById('minMargin');
const minROIInput = document.getElementById('minROI');
const filterBtn = document.getElementById('filterBtn');
const resetBtn = document.getElementById('resetBtn');

// Event listeners
filterBtn.addEventListener('click', applyFilter);
resetBtn.addEventListener('click', resetFilter);

// Load trades on page load
window.addEventListener('DOMContentLoaded', loadGoodTrades);

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    loading.style.display = 'none';
}

function hideError() {
    errorMessage.classList.remove('show');
}

function loadGoodTrades() {
    loading.style.display = 'block';
    hideError();
    
    fetch('/api/good-trades')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch good trades');
            }
            return response.json();
        })
        .then(trades => {
            if (trades.error) {
                showError(trades.error);
                return;
            }
            
            allTrades = trades;
            filteredTrades = trades;
            displayTrades(filteredTrades);
            loading.style.display = 'none';
            tradesContainer.classList.add('show');
        })
        .catch(error => {
            console.error('Error loading trades:', error);
            showError('Failed to load good trades. Please try again later.');
        });
}

function displayTrades(trades) {
    tradesTableBody.innerHTML = '';
    
    if (trades.length === 0) {
        tradesTableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">No trades match your filter criteria.</td></tr>';
        return;
    }
    
    trades.forEach(trade => {
        const row = document.createElement('tr');
        
        // Format time
        let timeDisplay = 'N/A';
        let timeClass = '';
        if (trade.minutesAgo !== null) {
            if (trade.minutesAgo < 5) {
                timeDisplay = 'Just now';
                timeClass = 'recent';
            } else if (trade.minutesAgo < 60) {
                timeDisplay = `${trade.minutesAgo} min ago`;
                timeClass = 'recent';
            } else if (trade.minutesAgo < 1440) { // Less than 24 hours
                const hours = Math.floor(trade.minutesAgo / 60);
                timeDisplay = `${hours} hour${hours !== 1 ? 's' : ''} ago`;
                timeClass = 'moderate';
            } else {
                const days = Math.floor(trade.minutesAgo / 1440);
                timeDisplay = `${days} day${days !== 1 ? 's' : ''} ago`;
                timeClass = 'old';
            }
        }
        
        // Determine ROI class
        let roiClass = '';
        if (trade.roi >= 10) {
            roiClass = 'high-roi';
        } else if (trade.roi >= 5) {
            roiClass = 'positive';
        }
        
        row.innerHTML = `
            <td>${escapeHtml(trade.name)}</td>
            <td>${formatNumber(trade.low)} gp</td>
            <td>${formatNumber(trade.high)} gp</td>
            <td>${formatNumber(trade.tax)} gp</td>
            <td class="positive">${formatNumber(trade.margin)} gp</td>
            <td class="${roiClass}">${trade.roi}%</td>
            <td class="${timeClass}">${timeDisplay}</td>
        `;
        
        tradesTableBody.appendChild(row);
    });
}

function applyFilter() {
    const minMargin = parseInt(minMarginInput.value) || 0;
    const minROI = parseFloat(minROIInput.value) || 0;
    
    filteredTrades = allTrades.filter(trade => {
        return trade.margin >= minMargin && trade.roi >= minROI;
    });
    
    displayTrades(filteredTrades);
}

function resetFilter() {
    minMarginInput.value = '0';
    minROIInput.value = '0';
    filteredTrades = allTrades;
    displayTrades(filteredTrades);
}

function formatNumber(num) {
    return num.toLocaleString('en-US');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
