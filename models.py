import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    """Model for casino users."""
    id = db.Column(db.String(32), primary_key=True)  # Discord user ID
    username = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Integer, default=1000)
    last_daily = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Transaction(db.Model):
    """Model for tracking all transactions."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Positive for wins, negative for losses/bets
    game_type = db.Column(db.String(32), nullable=False)  # 'slots', 'animated_slots', 'daily', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.String(256), nullable=True)  # Additional details about the transaction

    def __repr__(self):
        return f'<Transaction {self.id}: {self.amount}>'