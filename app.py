import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from models import db, User, Alert, AlertNotification

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///osrs_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@osrsmarket.com')

# Initialize database
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Mail
if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
    raise RuntimeError("MAIL_USERNAME and MAIL_PASSWORD must be set in environment variables for email functionality.")
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Check if data is None (malformed request)
            if data is None:
                return jsonify({'error': 'Invalid request format'}), 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            # Validate input
            if not username or not email or not password:
                return jsonify({'error': 'All fields are required'}), 400
            
            if len(username) < 3 or len(username) > 80:
                return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400
            
            if len(password) < 8:
                return jsonify({'error': 'Password must be at least 8 characters'}), 400
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already registered'}), 400
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Log the user in
            login_user(user)
            
            return jsonify({'success': True, 'message': 'Registration successful'})
        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            return jsonify({'error': 'An error occurred during registration'}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Check if data is None (malformed request)
            if data is None:
                return jsonify({'error': 'Invalid request format'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            user = User.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful'})
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return jsonify({'error': 'An error occurred during login'}), 500
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    """User account page"""
    return render_template('account.html')

@app.route('/api/account/email-notifications', methods=['POST'])
@login_required
def toggle_email_notifications():
    """Toggle email notifications for the current user"""
    if not current_user.is_premium:
        return jsonify({'error': 'Email notifications are only available for premium users'}), 403
    
    try:
        data = request.get_json()
        # Check if data is None (malformed request)
        if data is None:
            return jsonify({'error': 'Invalid request format'}), 400
        enabled = data.get('enabled', True)
        
        current_user.email_notifications_enabled = bool(enabled)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enabled': current_user.email_notifications_enabled,
            'message': f'Email notifications {"enabled" if current_user.email_notifications_enabled else "disabled"}'
        })
    except Exception as e:
        app.logger.error(f"Toggle email notifications error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred'}), 500

def send_alert_email(user, notification):
    """Send email notification for triggered alert"""
    if not user.email_notifications_enabled or not user.is_premium:
        return
    
    # Only send email if mail is properly configured
    if not app.config.get('MAIL_USERNAME'):
        app.logger.warning("Email notifications not configured")
        return
    
    try:
        alert_type_text = {
            'spike': 'Price Spike',
            'dip': 'Price Dip',
            'fluctuation': 'Price Fluctuation'
        }.get(notification.alert_type, 'Price Change')
        
        subject = f"OSRS Market Alert: {notification.item_name} - {alert_type_text}"
        
        change_direction = "increased" if notification.price_change > 0 else "decreased"
        
        body = f"""
Hello {user.username},

Your price alert for {notification.item_name} has been triggered!

Alert Type: {alert_type_text}
Old Price: {notification.old_price:,} GP
New Price: {notification.new_price:,} GP
Change: {abs(notification.price_change):.2f}% {change_direction}

Visit the OSRS Market app to view more details: https://osrs-market.example.com/

---
This is an automated message from OSRS Market. To disable email notifications, visit your account settings.
"""

        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #222;">
    <h2>OSRS Market Alert</h2>
    <p>Hello <strong>{user.username}</strong>,</p>
    <p>Your price alert for <strong>{notification.item_name}</strong> has been triggered!</p>
    <table style="border-collapse: collapse; margin-top: 10px;">
      <tr>
        <td style="padding: 4px 8px;"><strong>Alert Type:</strong></td>
        <td style="padding: 4px 8px;">{alert_type_text}</td>
      </tr>
      <tr>
        <td style="padding: 4px 8px;"><strong>Old Price:</strong></td>
        <td style="padding: 4px 8px;">{notification.old_price:,} GP</td>
      </tr>
      <tr>
        <td style="padding: 4px 8px;"><strong>New Price:</strong></td>
        <td style="padding: 4px 8px;">{notification.new_price:,} GP</td>
      </tr>
      <tr>
        <td style="padding: 4px 8px;"><strong>Change:</strong></td>
        <td style="padding: 4px 8px;">{abs(notification.price_change):.2f}% {change_direction}</td>
      </tr>
    </table>
    <p style="margin-top: 16px;">
      <a href="https://osrs-market.example.com/" style="background: #007bff; color: #fff; padding: 8px 16px; text-decoration: none; border-radius: 4px;">View Alert Details</a>
    </p>
    <hr>
    <small>This is an automated message from OSRS Market. To disable email notifications, visit your account settings.</small>
  </body>
</html>
"""

        msg = Message(subject, recipients=[user.email], body=body, html=html)
        mail.send(msg)
        app.logger.info(f"Sent email notification to {user.email} for alert {notification.id}")
    except Exception as e:
        app.logger.error(f"Failed to send email notification: {str(e)}")
        # Record the failure in the database for monitoring/retry
        try:
            notification.email_status = 'failed'
            notification.email_error = str(e)
            db.session.commit()
        except Exception as db_e:
            app.logger.error(f"Failed to record email failure in DB: {str(db_e)}")
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
        try:
            response = requests.get("https://www.osrsbox.com/osrsbox-db/items-summary.json", timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes
            item_list_cache = response.json()
        except Exception as e:
            app.logger.error(f"Error fetching item list: {str(e)}")
            # Return empty dict if we can't fetch the item list
            item_list_cache = {}
    return item_list_cache

def item_search(d, name):
    """Search for an item by name"""
    for key in d:
        if d[key].get('name') == name:
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

@app.route('/alerts')
@login_required
def alerts():
    """Serve the alerts management page"""
    # Check if user is premium
    if not current_user.is_premium:
        flash('Price alerts are only available for premium users.')
        return redirect(url_for('account'))
    return render_template('alerts.html')

@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get all alerts for the current user"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Price alerts are only available for premium users'}), 403
    
    try:
        user_alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
        return jsonify([alert.to_dict() for alert in user_alerts])
    except Exception as e:
        app.logger.error(f"Get alerts error: {str(e)}")
        return jsonify({'error': 'Unable to fetch alerts'}), 500

@app.route('/api/alerts', methods=['POST'])
@login_required
def create_alert():
    """Create a new alert"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Price alerts are only available for premium users'}), 403
    
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({'error': 'Invalid request format'}), 400
        
        item_id = data.get('item_id', '').strip()
        item_name = data.get('item_name', '').strip()
        alert_type = data.get('alert_type', '').strip()
        threshold = data.get('threshold')
        
        # Validate input
        if not item_id or not item_name or not alert_type:
            return jsonify({'error': 'Item ID, name, and alert type are required'}), 400
        
        if alert_type not in ['spike', 'dip', 'fluctuation']:
            return jsonify({'error': 'Invalid alert type. Must be spike, dip, or fluctuation'}), 400
        
        try:
            threshold = float(threshold)
            if threshold <= 0 or threshold > 100:
                return jsonify({'error': 'Threshold must be between 0 and 100'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid threshold value'}), 400
        
        # Get current price as baseline
        baseline_price = None
        try:
            price_response = requests.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest?id={item_id}",
                headers=headers,
                timeout=5
            ).json()
            
            if 'data' in price_response and item_id in price_response['data']:
                item_data = price_response['data'][item_id]
                # Use average of high and low as baseline
                high = item_data.get('high')
                low = item_data.get('low')
                if high and low:
                    baseline_price = (high + low) // 2
                elif high:
                    baseline_price = high
                elif low:
                    baseline_price = low
        except Exception as e:
            app.logger.warning(f"Could not fetch baseline price: {str(e)}")
        
        # Create alert
        alert = Alert(
            user_id=current_user.id,
            item_id=item_id,
            item_name=item_name,
            alert_type=alert_type,
            threshold=threshold,
            baseline_price=baseline_price,
            is_active=True
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        app.logger.error(f"Create alert error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while creating the alert'}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete an alert"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Price alerts are only available for premium users'}), 403
    
    try:
        alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alert deleted successfully'})
        
    except Exception as e:
        app.logger.error(f"Delete alert error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while deleting the alert'}), 500

@app.route('/api/alerts/<int:alert_id>/toggle', methods=['POST'])
@login_required
def toggle_alert(alert_id):
    """Toggle alert active status"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Price alerts are only available for premium users'}), 403
    
    try:
        alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.is_active = not alert.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Alert {"activated" if alert.is_active else "deactivated"}',
            'is_active': alert.is_active
        })
        
    except Exception as e:
        app.logger.error(f"Toggle alert error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while toggling the alert'}), 500

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get all notifications for the current user"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Notifications are only available for premium users'}), 403
    
    try:
        notifications = AlertNotification.query.filter_by(
            user_id=current_user.id
        ).order_by(AlertNotification.created_at.desc()).limit(50).all()
        
        return jsonify([notif.to_dict() for notif in notifications])
        
    except Exception as e:
        app.logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Unable to fetch notifications'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Notifications are only available for premium users'}), 403
    
    try:
        notification = AlertNotification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        app.logger.error(f"Mark notification read error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Notifications are only available for premium users'}), 403
    
    try:
        count = AlertNotification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({'count': count})
        
    except Exception as e:
        app.logger.error(f"Get unread count error: {str(e)}")
        return jsonify({'error': 'Unable to fetch unread count'}), 500

@app.route('/api/check-alerts', methods=['POST'])
@login_required
def check_alerts_manually():
    """Manually trigger alert checking for current user"""
    # Check if user is premium
    if not current_user.is_premium:
        return jsonify({'error': 'Price alerts are only available for premium users'}), 403
    
    try:
        alerts = Alert.query.filter_by(user_id=current_user.id, is_active=True).all()
        triggered_count = 0
        
        for alert in alerts:
            try:
                # Fetch current price
                price_response = requests.get(
                    f"https://prices.runescape.wiki/api/v1/osrs/latest?id={alert.item_id}",
                    headers=headers,
                    timeout=5
                ).json()
                
                if 'data' not in price_response or alert.item_id not in price_response['data']:
                    continue
                
                item_data = price_response['data'][alert.item_id]
                high = item_data.get('high')
                low = item_data.get('low')
                
                if not high and not low:
                    continue
                
                # Calculate current price (average of high and low)
                current_price = None
                if high and low:
                    current_price = (high + low) // 2
                elif high:
                    current_price = high
                elif low:
                    current_price = low
                
                # Update baseline if not set
                if alert.baseline_price is None:
                    alert.baseline_price = current_price
                    alert.last_checked = datetime.utcnow()
                    continue
                
                # Calculate price change percentage
                price_change = ((current_price - alert.baseline_price) / alert.baseline_price) * 100
                
                # Check if alert should trigger
                should_trigger = False
                if alert.alert_type == 'spike' and price_change >= alert.threshold:
                    should_trigger = True
                elif alert.alert_type == 'dip' and price_change <= -alert.threshold:
                    should_trigger = True
                elif alert.alert_type == 'fluctuation' and abs(price_change) >= alert.threshold:
                    should_trigger = True
                
                if should_trigger:
                    # Create notification
                    notification = AlertNotification(
                        alert_id=alert.id,
                        user_id=current_user.id,
                        item_id=alert.item_id,
                        item_name=alert.item_name,
                        alert_type=alert.alert_type,
                        old_price=alert.baseline_price,
                        new_price=current_price,
                        price_change=price_change,
                        is_read=False
                    )
                    db.session.add(notification)
                    db.session.flush()  # Flush to get notification ID
                    
                    # Send email notification
                    send_alert_email(current_user, notification)
                    
                    # Update alert
                    alert.last_triggered = datetime.utcnow()
                    alert.baseline_price = current_price  # Reset baseline
                    triggered_count += 1
                
                alert.last_checked = datetime.utcnow()
                
            except Exception as e:
                app.logger.error(f"Error checking alert {alert.id}: {str(e)}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Checked {len(alerts)} alerts, {triggered_count} triggered',
            'checked': len(alerts),
            'triggered': triggered_count
        })
        
    except Exception as e:
        app.logger.error(f"Check alerts error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while checking alerts'}), 500

if __name__ == '__main__':
    import os
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=8080)
