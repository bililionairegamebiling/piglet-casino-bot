import re
import logging

logger = logging.getLogger(__name__)

def parse_bet(bet_str, max_balance):
    """
    Parse a bet string into a numeric value.
    
    Args:
        bet_str (str): Bet string to parse (can include k, m, b, max, all)
        max_balance (int): Maximum available balance
        
    Returns:
        int: Parsed bet amount
        
    Raises:
        ValueError: If bet string is invalid
    """
    # Handle "max" or "m" bet
    if bet_str.lower() in ['m', 'max']:
        return max_balance
    
    # Handle "all" or "a" bet
    if bet_str.lower() in ['a', 'all', 'allin', 'all-in']:
        return max_balance
    
    # Handle numeric values with suffixes (e.g., 1k, 2.5m)
    bet_str = bet_str.lower().strip()
    
    # Match pattern like 1k, 2.5m, 100, etc.
    pattern = r'^(\d+(\.\d+)?)([kmb])?$'
    match = re.match(pattern, bet_str)
    
    if not match:
        raise ValueError("Invalid bet format. Use a number, or 'm'/'max' for maximum bet.")
    
    amount = float(match.group(1))
    suffix = match.group(3)
    
    # Apply multiplier based on suffix
    if suffix == 'k':
        amount *= 1000
    elif suffix == 'm':
        amount *= 1000000
    elif suffix == 'b':
        amount *= 1000000000
    
    # Convert to integer (floor value)
    return int(amount)

def format_currency(amount):
    """
    Format a currency amount with appropriate suffix.
    
    Args:
        amount (int/float): Amount to format
        
    Returns:
        str: Formatted currency string
    """
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"{amount / 1_000:.2f}K"
    else:
        return f"{amount:,}"
