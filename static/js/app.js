let currentItemNumber = null;
let currentItemName = null;
let priceChart = null;

// DOM elements
const itemInput = document.getElementById('itemInput');
const searchBtn = document.getElementById('searchBtn');
const currentItemDiv = document.getElementById('currentItem');
const optionsSection = document.getElementById('optionsSection');
const optionSelect = document.getElementById('optionSelect');
const errorMessage = document.getElementById('errorMessage');
const dataDisplay = document.getElementById('dataDisplay');
const chartContainer = document.getElementById('chartContainer');

// Event listeners
searchBtn.addEventListener('click', searchItem);
itemInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchItem();
    }
});
optionSelect.addEventListener('change', handleOptionChange);

// Functions
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
            optionsSection.style.display = 'none';
        } else {
            currentItemNumber = data.itemNumber;
            currentItemName = data.itemName;
            currentItemDiv.textContent = `The current item is: ${data.itemName}`;
            optionsSection.style.display = 'block';
            optionSelect.value = '';
        }
    })
    .catch(error => {
        showError('Error searching for item: ' + error.message);
    });
}

function handleOptionChange() {
    const option = optionSelect.value;
    
    if (!option || !currentItemNumber) {
        return;
    }
    
    hideError();
    dataDisplay.innerHTML = '';
    chartContainer.style.display = 'none';
    
    if (option === 'latest') {
        getLatestData();
    } else if (option === 'history') {
        get24HourHistory();
    }
}

function getLatestData() {
    fetch(`/api/latest/${currentItemNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                let displayText = '';
                displayText += `Insta Buy Price: ${data.high !== null ? data.high : 'N/A'}\n\n`;
                displayText += `Insta Sell Price: ${data.low !== null ? data.low : 'N/A'}\n\n`;
                displayText += `Margin: ${data.margin !== null ? data.margin : 'N/A'}`;
                
                if (data.minutesAgo !== null) {
                    displayText += `\n\nLast sold ${data.minutesAgo} minute(s) ago.`;
                }
                
                dataDisplay.textContent = displayText;
            }
        })
        .catch(error => {
            showError('Error fetching latest data: ' + error.message);
        });
}

function get24HourHistory() {
    fetch(`/api/history/${currentItemNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                let displayText = '';
                displayText += `Average High: ${data.avgHigh}\n\n`;
                displayText += `Average Low: ${data.avgLow}`;
                
                dataDisplay.textContent = displayText;
                
                // Display chart
                displayChart(data.chartData);
            }
        })
        .catch(error => {
            showError('Error fetching historical data: ' + error.message);
        });
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
            plugins: {
                legend: {
                    labels: {
                        color: '#fafafa'
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
                        color: '#fafafa'
                    },
                    grid: {
                        color: '#4a4a5e'
                    }
                }
            }
        }
    });
}
