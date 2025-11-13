import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

headers = {
    'User-Agent': 'osrsMarket app',
    'From': 'dlnmtchll@gmail.com' 
}

# Cache for item list
item_list_cache = None

def get_item_list():
    """Get and cache the item list"""
    global item_list_cache
    if item_list_cache is None:
        response = requests.get("https://www.osrsbox.com/osrsbox-db/items-summary.json", timeout=5)
        item_list_cache = response.json()
    return item_list_cache

def item_search(d, name):
    """Search for an item by name"""
    for key in d:
        for value in d[key]:
            if d[key][value] == name:
                return key
    return None

def avg_high(d):
    """Calculate average high price"""
    sum_val = 0
    counter = 0
    for key in d:
        low = key['avgHighPrice']
        if low is not None:
            sum_val += low
            counter += 1
    return sum_val // counter if counter > 0 else 0

def avg_low(d):
    """Calculate average low price"""
    sum_val = 0
    counter = 0
    for key in d:
        high = key['avgLowPrice']
        if high is not None:
            sum_val += high
            counter += 1
    return sum_val // counter if counter > 0 else 0

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    """Get item name suggestions for autocomplete"""
    try:
        query = request.args.get('query', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify([])
        
        item_list = get_item_list()
        suggestions = []
        
        # Search for items that match the query
        for item_id in item_list:
            item_name = item_list[item_id].get('name', '')
            if item_name and query in item_name.lower():
                suggestions.append(item_name)
                # Limit to 10 suggestions
                if len(suggestions) >= 10:
                    break
        
        return jsonify(suggestions)
    except Exception as e:
        app.logger.error(f"Autocomplete error: {str(e)}")
        return jsonify([])

@app.route('/api/search', methods=['POST'])
def search_item():
    """Search for an item by name"""
    try:
        data = request.get_json()
        item_name = data.get('itemName', '')
        
        if not item_name:
            return jsonify({'error': 'Item name is required'}), 400
        
        # Normalize item name
        item_name = item_name.strip().lower().capitalize()
        
        item_list = get_item_list()
        item_number = item_search(item_list, item_name)
        
        if item_number is None:
            return jsonify({'error': 'Item not found. Please check spelling and spacing.'}), 404
        
        return jsonify({
            'itemNumber': item_number,
            'itemName': item_name
        })
    except Exception as e:
        # Log error for debugging but don't expose details to user
        app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'An error occurred while searching for the item'}), 500

@app.route('/api/latest/<item_number>', methods=['GET'])
def get_latest_data(item_number):
    """Get latest market data for an item"""
    try:
        req = requests.get(
            f"https://prices.runescape.wiki/api/v1/osrs/latest?id={item_number}", 
            headers=headers,
            timeout=5
        ).json()
        
        if 'data' not in req or item_number not in req['data']:
            return jsonify({'error': 'No data available for this item'}), 404
        
        item_data = req['data'][item_number]
        
        # Calculate time since last sale
        high_time = item_data.get('highTime')
        if high_time:
            time = datetime.fromtimestamp(high_time)
            now = datetime.now()
            minutes_ago = (now - time).total_seconds() / 60
        else:
            minutes_ago = None
        
        high = item_data.get('high')
        low = item_data.get('low')
        
        # Calculate margin (including 1% tax)
        if high and low:
            tax = (high * 0.01) // 1
            margin = high - low - tax
        else:
            tax = None
            margin = None
        
        return jsonify({
            'high': high,
            'low': low,
            'tax': tax,
            'margin': margin,
            'minutesAgo': int(minutes_ago) if minutes_ago else None
        })
    except Exception as e:
        app.logger.error(f"Latest data error: {str(e)}")
        return jsonify({'error': 'Unable to fetch latest market data. Please try again later.'}), 500

@app.route('/api/history/<item_number>', methods=['GET'])
def get_24hr_data(item_number):
    """Get 24-hour historical data for an item"""
    try:
        response = requests.get(
            f'https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id={item_number}', 
            headers=headers,
            timeout=5
        )
        data = response.json()
        
        if 'data' not in data:
            return jsonify({'error': 'No historical data available'}), 404
        
        time_series_data = data['data']
        
        # Calculate averages
        avg_low_price = avg_low(time_series_data)
        avg_high_price = avg_high(time_series_data)
        
        # Prepare chart data
        chart_data = []
        for value in time_series_data:
            timestamp = value.get('timestamp')
            if timestamp:
                time = datetime.fromtimestamp(timestamp)
                time_str = time.strftime("%H:%M")
            else:
                time_str = None
            
            chart_data.append({
                'timestamp': time_str,
                'avgLowPrice': value.get('avgLowPrice'),
                'avgHighPrice': value.get('avgHighPrice'),
                'highPriceVolume': value.get('highPriceVolume'),
                'lowPriceVolume': value.get('lowPriceVolume')
            })
        
        return jsonify({
            'avgLow': avg_low_price,
            'avgHigh': avg_high_price,
            'chartData': chart_data
        })
    except Exception as e:
        app.logger.error(f"Historical data error: {str(e)}")
        return jsonify({'error': 'Unable to fetch historical data. Please try again later.'}), 500

@app.route('/trades')
def trades():
    """Serve the good trades page"""
    return render_template('trades.html')

@app.route('/api/good-trades', methods=['GET'])
def get_good_trades():
    """Get a list of items with good trading margins"""
    try:
        # Fetch latest prices for all items
        response = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/latest",
            headers=headers,
            timeout=10
        )
        latest_data = response.json()
        
        if 'data' not in latest_data:
            return jsonify({'error': 'Unable to fetch market data'}), 500
        
        # Get item list to map IDs to names
        item_list = get_item_list()
        
        # Analyze items for good trades
        good_trades = []
        
        for item_id, price_data in latest_data['data'].items():
            high = price_data.get('high')
            low = price_data.get('low')
            
            # Only consider items with both buy and sell prices
            if high is None or low is None or high <= 0 or low <= 0:
                continue
            
            # Calculate margin (including 1% tax on sell price)
            tax = int(high * 0.01)
            margin = high - low - tax
            
            # Only include items with positive margin
            if margin <= 0:
                continue
            
            # Calculate ROI percentage
            roi = (margin / low) * 100 if low > 0 else 0
            
            # Get item name
            item_name = item_list.get(item_id, {}).get('name', f'Item {item_id}')
            
            # Check if trade is recent (within last hour)
            high_time = price_data.get('highTime', 0)
            low_time = price_data.get('lowTime', 0)
            most_recent = max(high_time, low_time)
            minutes_ago = (datetime.now().timestamp() - most_recent) / 60 if most_recent > 0 else float('inf')
            
            good_trades.append({
                'id': item_id,
                'name': item_name,
                'high': high,
                'low': low,
                'tax': tax,
                'margin': margin,
                'roi': round(roi, 2),
                'minutesAgo': int(minutes_ago) if minutes_ago != float('inf') else None
            })
        
        # Sort by a combination of margin and ROI
        # Prioritize items with good margin (at least 100gp) and reasonable ROI
        good_trades.sort(key=lambda x: (
            x['margin'] if x['margin'] >= 100 else x['margin'] * 0.1,  # Penalize small margins
            x['roi']
        ), reverse=True)
        
        # Return top 100 trades
        return jsonify(good_trades[:100])
        
    except Exception as e:
        app.logger.error(f"Good trades error: {str(e)}")
        return jsonify({'error': 'Unable to fetch good trades data'}), 500

if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
