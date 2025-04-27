"""
Database service utilities for Piglet Casino Bot.
Contains functions to interact with the database models.
"""
import logging
from datetime import datetime
from models import db, User, Transaction

logger = logging.getLogger(__name__)

def get_or_create_user(user_id, username):
    """
    Get a user from the database or create if not exists.
    
    Args:
        user_id (str): Discord user ID
        username (str): Discord username
        
    Returns:
        User: User database object
    """
    user = User.query.get(user_id)
    
    if not user:
        user = User(id=user_id, username=username, balance=1000)
        db.session.add(user)
        db.session.commit()
        
        # Log the transaction for new user bonus
        add_transaction(user_id, 1000, 'new_user', 'New user bonus')
        logger.info(f"Created new user {username} with ID {user_id}")
    
    return user

def get_user_balance(user_id):
    """
    Get balance for a user from the database.
    
    Args:
        user_id (str): Discord user ID
        
    Returns:
        int: User's current balance
    """
    user = User.query.get(user_id)
    
    if not user:
        return 0
    
    return user.balance

def update_user_balance(user_id, username, amount, game_type, details=None):
    """
    Update user balance and record the transaction.
    
    Args:
        user_id (str): Discord user ID
        username (str): Discord username
        amount (int): Amount to add (positive) or subtract (negative)
        game_type (str): Type of game or transaction
        details (str, optional): Additional details about transaction
        
    Returns:
        int: New balance
    """
    user = get_or_create_user(user_id, username)
    
    # Update user balance
    user.balance += amount
    db.session.commit()
    
    # Record transaction
    add_transaction(user_id, amount, game_type, details)
    
    return user.balance

def add_transaction(user_id, amount, game_type, details=None):
    """
    Add a transaction record to the database.
    
    Args:
        user_id (str): Discord user ID
        amount (int): Amount of transaction
        game_type (str): Type of game or transaction
        details (str, optional): Additional details about transaction
    """
    transaction = Transaction(
        user_id=user_id, 
        amount=amount, 
        game_type=game_type,
        details=details
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return transaction

def get_user_transactions(user_id, limit=10):
    """
    Get recent transactions for a user.
    
    Args:
        user_id (str): Discord user ID
        limit (int): Maximum number of transactions to return
        
    Returns:
        list: List of Transaction objects
    """
    return Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.timestamp.desc()
    ).limit(limit).all()

def get_leaderboard(limit=10):
    """
    Get leaderboard of users with highest balances.
    
    Args:
        limit (int): Maximum number of users to return
        
    Returns:
        list: List of User objects
    """
    return User.query.order_by(User.balance.desc()).limit(limit).all()

# Function removed to fix duplicate declaration

def check_daily_reward(user_id, username):
    """
    Check if user can claim daily reward and process it if possible.
    
    Args:
        user_id (str): Discord user ID
        username (str): Discord username
        
    Returns:
        tuple: (bool success, str message, int amount or None)
    """
    user = get_or_create_user(user_id, username)
    
    now = datetime.utcnow()
    
    # If user has never claimed or last claim was more than 20 hours ago
    if not user.last_daily or (now - user.last_daily).total_seconds() > 20 * 3600:
        # Give reward (random amount between 100-500)
        import random
        reward = random.randint(100, 500)
        
        # Update user record
        user.balance += reward
        user.last_daily = now
        db.session.commit()
        
        # Record transaction
        add_transaction(user_id, reward, 'daily', 'Daily reward')
        
        return True, f"You claimed {reward} coins as your daily reward!", reward
    
    # Calculate time until next reward
    seconds_left = 20 * 3600 - (now - user.last_daily).total_seconds()
    hours = int(seconds_left // 3600)
    minutes = int((seconds_left % 3600) // 60)
    
    return False, f"You can claim your next daily reward in {hours}h {minutes}m", None

def check_work_reward(user_id, username):
    """
    Check if user can claim work reward and process it if possible.
    Work reward is available every 10 minutes.
    
    Args:
        user_id (str): Discord user ID
        username (str): Discord username
        
    Returns:
        tuple: (bool success, str message, int amount or None)
    """
    user = get_or_create_user(user_id, username)
    
    now = datetime.utcnow()
    
    # Check if last_work is None
    if user.last_work is None:
        user.last_work = datetime(2000, 1, 1)  # Set to distant past to allow immediate work
        db.session.commit()
    
    # If user has never worked or last work was more than 10 minutes ago
    if not user.last_work or (now - user.last_work).total_seconds() > 10 * 60:
        # Give reward (random amount between 50-200)
        import random
        reward = random.randint(50, 200)
        
        # Update user record
        user.balance += reward
        user.last_work = now
        db.session.commit()
        
        # Record transaction
        add_transaction(user_id, reward, 'work', 'Work reward')
        
        # Generate a work message
        work_messages = [
            f"You worked hard at the casino and earned {reward} coins!",
            f"You helped clean the slot machines and earned {reward} coins!",
            f"You served drinks to gamblers and received {reward} coins in tips!",
            f"You fixed a broken slot machine and got paid {reward} coins!",
            f"You dealt cards at the blackjack table and earned {reward} coins!",
            f"You welcomed guests at the casino entrance and earned {reward} coins!",
            f"You worked as a cashier and earned {reward} coins!"
        ]
        
        message = random.choice(work_messages)
        return True, message, reward
    
    # Calculate time until next reward
    seconds_left = 10 * 60 - (now - user.last_work).total_seconds()
    minutes = int(seconds_left // 60)
    seconds = int(seconds_left % 60)
    
    return False, f"You can work again in {minutes}m {seconds}s", None