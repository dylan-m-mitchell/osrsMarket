let currentItemNumber = null;
let currentItemName = null;
let priceChart = null;
let autocompleteTimeout = null;
let selectedSuggestionIndex = -1;
let fullChartData = []; // Store complete chart data for filtering

// DOM elements
const itemInput = document.getElementById('itemInput');
const searchBtn = document.getElementById('searchBtn');
const currentItemDiv = document.getElementById('currentItem');
const errorMessage = document.getElementById('errorMessage');
const dataDisplay = document.getElementById('dataDisplay');
const chartContainer = document.getElementById('chartContainer');
const timeSlider = document.getElementById('timeSlider');
const timeRangeDisplay = document.getElementById('timeRangeDisplay');

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
            .then(response => response.json())
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
        },
        body: JSON.stringify({ itemName: itemName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            currentItemNumber = null;
            currentItemName = null;
            currentItemDiv.textContent = '';
        } else {
            currentItemNumber = data.itemNumber;
            currentItemName = data.itemName;
            currentItemDiv.textContent = `The current item is: ${data.itemName}`;
            // Automatically load both latest and historical data
            loadAllData();
        }
    })
    .catch(error => {
        showError('Error searching for item: ' + error.message);
    });
}

function loadAllData() {
    // Load both latest and historical data
    Promise.all([
        fetch(`/api/latest/${currentItemNumber}`).then(res => res.json()),
        fetch(`/api/history/${currentItemNumber}`).then(res => res.json())
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
