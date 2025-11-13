"""Database models for user authentication"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, nullable=False, default=False)
    email_notifications_enabled = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationship to alerts
    alerts = db.relationship('Alert', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Alert(db.Model):
    """Alert model for price change notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    item_id = db.Column(db.String(20), nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # 'spike', 'dip', 'fluctuation'
    threshold = db.Column(db.Float, nullable=False)  # Percentage change threshold
    baseline_price = db.Column(db.Integer, nullable=True)  # Baseline price for comparison
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_checked = db.Column(db.DateTime, nullable=True)
    last_triggered = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Alert {self.id}: {self.item_name} ({self.alert_type})>'
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'alert_type': self.alert_type,
            'threshold': self.threshold,
            'baseline_price': self.baseline_price,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }


class AlertNotification(db.Model):
    """Alert notification model for storing triggered alerts"""
    __tablename__ = 'alert_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    item_id = db.Column(db.String(20), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)
    old_price = db.Column(db.Integer, nullable=True)
    new_price = db.Column(db.Integer, nullable=False)
    price_change = db.Column(db.Float, nullable=False)  # Percentage change
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    alert = db.relationship('Alert', backref='notifications')
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<AlertNotification {self.id}: {self.item_name}>'
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'alert_type': self.alert_type,
            'old_price': self.old_price,
            'new_price': self.new_price,
            'price_change': self.price_change,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
