let currentItemNumber = null;
let currentItemName = null;
let priceChart = null;
let autocompleteTimeout = null;
let selectedSuggestionIndex = -1;
let fullChartData = []; // Store complete chart data for filtering

// Get CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

// DOM elements
const itemInput = document.getElementById('itemInput');
const searchBtn = document.getElementById('searchBtn');
const currentItemDiv = document.getElementById('currentItem');
const errorMessage = document.getElementById('errorMessage');
const dataDisplay = document.getElementById('dataDisplay');
const chartContainer = document.getElementById('chartContainer');
const timeSlider = document.getElementById('timeSlider');
const timeRangeDisplay = document.getElementById('timeRangeDisplay');
const quickAlertSection = document.getElementById('quickAlertSection');
const quickAlertBtn = document.getElementById('quickAlertBtn');

// Create autocomplete container
const autocompleteContainer = document.createElement('div');
autocompleteContainer.id = 'autocomplete';
autocompleteContainer.className = 'autocomplete-items';
itemInput.parentNode.insertBefore(autocompleteContainer, itemInput.nextSibling);

// Event listeners
searchBtn.addEventListener('click', searchItem);
itemInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchItem();
    }
});
itemInput.addEventListener('input', handleAutocomplete);
itemInput.addEventListener('keydown', handleAutocompleteKeydown);
timeSlider.addEventListener('input', handleTimeSliderChange);
if (quickAlertBtn) {
    quickAlertBtn.addEventListener('click', showQuickAlertModal);
}

// Close autocomplete when clicking outside
document.addEventListener('click', (e) => {
    if (e.target !== itemInput) {
        closeAutocomplete();
    }
});

// Functions
function handleAutocomplete() {
    clearTimeout(autocompleteTimeout);
    const query = itemInput.value.trim();
    
    if (query.length < 2) {
        closeAutocomplete();
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
            itemInput.value = suggestion;
            closeAutocomplete();
        });
        autocompleteContainer.appendChild(div);
    });
}

function closeAutocomplete() {
    autocompleteContainer.innerHTML = '';
    selectedSuggestionIndex = -1;
}

function handleAutocompleteKeydown(e) {
    const items = autocompleteContainer.getElementsByClassName('autocomplete-item');
    
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
        itemInput.value = items[selectedSuggestionIndex].textContent;
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

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

function hideError() {
    errorMessage.classList.remove('show');
}

function searchItem() {
    const itemName = itemInput.value.trim();
    
    if (!itemName) {
        showError('Please enter an item name');
        return;
    }
    
    hideError();
    closeAutocomplete();
    dataDisplay.innerHTML = '';
    chartContainer.style.display = 'none';
    
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
            // Try to parse error message from response
            let errorMessage = 'Error searching for item';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // If response isn't JSON, use status text
                errorMessage = `Error: ${response.statusText || response.status}`;
            }
            throw new Error(errorMessage);
        }
        try {
            return await response.json();
        } catch (e) {
            throw new Error('Failed to parse response data');
        }
    })
    .then(data => {
        if (data.error) {
            showError(data.error);
            currentItemNumber = null;
            currentItemName = null;
            currentItemDiv.textContent = '';
            if (quickAlertSection) {
                quickAlertSection.style.display = 'none';
            }
        } else {
            currentItemNumber = data.itemNumber;
            currentItemName = data.itemName;
            currentItemDiv.textContent = `The current item is: ${data.itemName}`;
            // Show quick alert button if user is authenticated
            if (quickAlertSection) {
                quickAlertSection.style.display = 'block';
            }
            // Automatically load both latest and historical data
            loadAllData();
        }
    })
    .catch(error => {
        showError('Error searching for item: ' + error.message);
        currentItemNumber = null;
        currentItemName = null;
        currentItemDiv.textContent = '';
    });
}

function loadAllData() {
    // Load both latest and historical data
    Promise.all([
        fetch(`/api/latest/${currentItemNumber}`).then(async res => {
            if (!res.ok) {
                let errorMessage = 'Error fetching latest data';
                try {
                    const errorData = await res.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = `Error: ${res.statusText || res.status}`;
                }
                return { error: errorMessage };
            }
            try {
                return await res.json();
            } catch (e) {
                return { error: 'Failed to parse response data' };
            }
        }),
        fetch(`/api/history/${currentItemNumber}`).then(async res => {
            if (!res.ok) {
                let errorMessage = 'Error fetching historical data';
                try {
                    const errorData = await res.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = `Error: ${res.statusText || res.status}`;
                }
                return { error: errorMessage };
            }
            try {
                return await res.json();
            } catch (e) {
                return { error: 'Failed to parse response data' };
            }
        })
    ])
    .then(([latestData, historyData]) => {
        if (latestData.error || historyData.error) {
            showError(latestData.error || historyData.error);
        } else {
            displayCombinedData(latestData, historyData);
        }
    })
    .catch(error => {
        showError('Error fetching data: ' + error.message);
    });
}

function displayCombinedData(latestData, historyData) {
    // Display insta buy/sell and 24-hour averages
    let displayText = '';
    displayText += `Insta Buy Price: ${latestData.high !== null ? latestData.high : 'N/A'}\n\n`;
    displayText += `Insta Sell Price: ${latestData.low !== null ? latestData.low : 'N/A'}\n\n`;
    displayText += `Margin: ${latestData.margin !== null ? latestData.margin : 'N/A'}`;
    
    if (latestData.minutesAgo !== null) {
        displayText += `\n\nLast sold ${latestData.minutesAgo} minute(s) ago.`;
    }
    
    displayText += `\n\n24 Hour Average High: ${historyData.avgHigh}`;
    displayText += `\n24 Hour Average Low: ${historyData.avgLow}`;
    
    dataDisplay.textContent = displayText;
    
    // Store full chart data and display chart
    fullChartData = historyData.chartData;
    displayChart(fullChartData);
}

function handleTimeSliderChange() {
    const hours = parseInt(timeSlider.value);
    timeRangeDisplay.textContent = `${hours} hour${hours !== 1 ? 's' : ''}`;
    
    // Filter chart data based on selected time range
    if (fullChartData.length > 0) {
        const dataPointsPerHour = 12; // 5-minute intervals = 12 per hour
        const pointsToShow = hours * dataPointsPerHour;
        const filteredData = fullChartData.slice(-pointsToShow);
        updateChart(filteredData);
    }
}

function displayChart(chartData) {
    chartContainer.style.display = 'block';
    
    // Destroy existing chart if it exists
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Prepare data for Chart.js
    const labels = chartData.map(d => d.timestamp).filter(t => t !== null);
    const avgLowPrices = chartData.map(d => d.avgLowPrice);
    const avgHighPrices = chartData.map(d => d.avgHighPrice);
    
    const ctx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Avg Low Price',
                    data: avgLowPrices,
                    borderColor: '#4169e1',
                    backgroundColor: 'rgba(65, 105, 225, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Avg High Price',
                    data: avgHighPrices,
                    borderColor: '#a020f0',
                    backgroundColor: 'rgba(160, 32, 240, 0.1)',
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fafafa'
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(38, 39, 48, 0.95)',
                    titleColor: '#fafafa',
                    bodyColor: '#fafafa',
                    borderColor: '#a020f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return 'Time: ' + context[0].label;
                        },
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            if (value !== null) {
                                return label + ': ' + value.toLocaleString() + ' gp';
                            }
                            return label + ': N/A';
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x',
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#fafafa',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#4a4a5e'
                    }
                },
                y: {
                    ticks: {
                        color: '#fafafa',
                        callback: function(value) {
                            return value.toLocaleString() + ' gp';
                        }
                    },
                    grid: {
                        color: '#4a4a5e'
                    }
                }
            }
        }
    });
}

function updateChart(chartData) {
    if (!priceChart) return;
    
    // Update chart data
    const labels = chartData.map(d => d.timestamp).filter(t => t !== null);
    const avgLowPrices = chartData.map(d => d.avgLowPrice);
    const avgHighPrices = chartData.map(d => d.avgHighPrice);
    
    priceChart.data.labels = labels;
    priceChart.data.datasets[0].data = avgLowPrices;
    priceChart.data.datasets[1].data = avgHighPrices;
    priceChart.update();
}

function showQuickAlertModal() {
    if (!currentItemNumber || !currentItemName) {
        showError('Please search for an item first');
        return;
    }
    
    const alertType = prompt(
        `Create alert for ${currentItemName}\n\n` +
        `Choose alert type:\n` +
        `1. Price Spike (increase)\n` +
        `2. Price Dip (decrease)\n` +
        `3. Any Fluctuation\n\n` +
        `Enter 1, 2, or 3:`,
        '1'
    );
    
    if (!alertType || !['1', '2', '3'].includes(alertType)) {
        return;
    }
    
    const threshold = prompt(
        `Enter threshold percentage (0-100):\n\n` +
        `Example: Enter 5 for 5% change`,
        '5'
    );
    
    if (!threshold) {
        return;
    }
    
    const thresholdNum = parseFloat(threshold);
    if (isNaN(thresholdNum) || thresholdNum <= 0 || thresholdNum > 100) {
        showError('Invalid threshold. Must be between 0 and 100');
        return;
    }
    
    const alertTypeMap = {
        '1': 'spike',
        '2': 'dip',
        '3': 'fluctuation'
    };
    
    // Create alert via API
    fetch('/api/alerts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            item_id: currentItemNumber,
            item_name: currentItemName,
            alert_type: alertTypeMap[alertType],
            threshold: thresholdNum
        })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create alert');
        }
        return data;
    })
    .then(() => {
        alert(`Alert created successfully for ${currentItemName}!\n\nYou can manage your alerts from the Alerts page.`);
    })
    .catch(error => {
        showError('Failed to create alert: ' + error.message);
    });
}
