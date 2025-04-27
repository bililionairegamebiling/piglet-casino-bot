import random
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Define slots symbols and their payout rates
PAYOUTS = {
    "7️⃣": {3: 500, 2: 25},
    "💎": {3: 25, 2: 10},
    "🎰": {3: 5, 2: 3},
    "🔔": {3: 3, 2: 2},
    "👞": {3: 2, 2: 1},
    "🍋": {3: 1, 2: 1},
    "🍉": {3: 0.75, 2: 1},
    "❤️": {3: 0.5, 2: 0.75},
    "🍒": {3: 0.5, 2: 0.25},
}

# Define probabilities for each symbol (higher value = less frequent)
SYMBOL_WEIGHTS = {
    "7️⃣": 1,    # Rarest
    "💎": 2, 
    "🎰": 4,
    "🔔": 6,
    "👞": 10,
    "🍋": 14,
    "🍉": 16,
    "❤️": 20,
    "🍒": 25,    # Most common
}

def generate_slots_result():
    """
    Generate a random slots result.
    
    Returns:
        list: 3x3 matrix of slot symbols
    """
    # Create weighted list of symbols based on their weights
    symbols = []
    for symbol, weight in SYMBOL_WEIGHTS.items():
        symbols.extend([symbol] * weight)
    
    # Generate 3x3 grid of random symbols
    result = []
    for _ in range(3):
        row = [random.choice(symbols) for _ in range(3)]
        result.append(row)
    
    return result

def format_visual_result(result):
    """
    Format a visual representation of the slots result.
    
    Args:
        result (list): 3x3 matrix of slot symbols
        
    Returns:
        str: Formatted visual representation
    """
    visual = []
    for row in result:
        visual.append(" ".join(row))
    
    return "\n".join(visual)

def check_win(result):
    """
    Check for winning combinations in the slots result.
    
    Args:
        result (list): 3x3 matrix of slot symbols
        
    Returns:
        tuple: (best_payout, win_details) - payout multiplier and details of the win
    """
    # Check rows
    best_payout = 0
    win_details = None
    
    # Check each row
    for row in result:
        counter = Counter(row)
        payout, details = calculate_payout(counter)
        if payout > best_payout:
            best_payout = payout
            win_details = details
    
    # Check diagonals
    # Main diagonal (top-left to bottom-right)
    diagonal1 = [result[i][i] for i in range(3)]
    counter = Counter(diagonal1)
    payout, details = calculate_payout(counter)
    if payout > best_payout:
        best_payout = payout
        win_details = details
    
    # Secondary diagonal (top-right to bottom-left)
    diagonal2 = [result[i][2-i] for i in range(3)]
    counter = Counter(diagonal2)
    payout, details = calculate_payout(counter)
    if payout > best_payout:
        best_payout = payout
        win_details = details
    
    return best_payout, win_details

def calculate_payout(counter):
    """
    Calculate payout based on symbol counter.
    
    Args:
        counter (Counter): Counter of symbols
        
    Returns:
        tuple: (payout_multiplier, win_details) - the payout multiplier and details
    """
    best_payout = 0
    win_details = None
    
    for symbol, count in counter.items():
        if symbol in PAYOUTS and count in PAYOUTS[symbol]:
            payout = PAYOUTS[symbol][count]
            if payout > best_payout:
                best_payout = payout
                win_details = f"{count}x {symbol} ({payout}x)"
    
    return best_payout, win_details

def run_slots_game(bet_amount):
    """
    Run a complete slots game.
    
    Args:
        bet_amount (int): Amount being bet
        
    Returns:
        tuple: (result, visual, winnings, win_details) - game results
    """
    # Generate random slots result
    result = generate_slots_result()
    
    # Format visual representation
    visual = format_visual_result(result)
    
    # Check for wins
    multiplier, win_details = check_win(result)
    
    # Calculate winnings
    winnings = int(bet_amount * multiplier)
    
    return result, visual, winnings, win_details
