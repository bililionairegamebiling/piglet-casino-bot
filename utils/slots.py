import random
import logging
import os
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

# Define slot symbols with corresponding image files and emojis
SYMBOLS = {
    "SEVEN": {"emoji": "7️⃣", "file": "sseven.png", "name": "Seven"},
    "DIAMOND": {"emoji": "💎", "file": "sdiamond.png", "name": "Diamond"},
    "BAR": {"emoji": "🎰", "file": "sbar.png", "name": "Bar"},
    "BELL": {"emoji": "🔔", "file": "sbell.png", "name": "Bell"},
    "SHOE": {"emoji": "👞", "file": "sshoe.png", "name": "Horseshoe"},
    "LEMON": {"emoji": "🍋", "file": "slemon.png", "name": "Lemon"},
    "MELON": {"emoji": "🍉", "file": "smelon.png", "name": "Watermelon"},
    "HEART": {"emoji": "❤️", "file": "sheart.png", "name": "Heart"},
    "CHERRY": {"emoji": "🍒", "file": "scherry.png", "name": "Cherry"},
}

# Verify that all image files exist
for symbol_key, symbol_data in SYMBOLS.items():
    file_path = Path(f"assets/slot_symbols/{symbol_data['file']}")
    if not file_path.exists():
        logger.warning(f"Image file for {symbol_key} not found: {file_path}")
        # Set image_available flag as string to avoid type issues
        symbol_data["image_available"] = "no"
    else:
        symbol_data["image_available"] = "yes"
        symbol_data["path"] = str(file_path)

# Define slots symbols and their payout rates (in multiplier format)
PAYOUTS = {
    "SEVEN": {3: 500, 2: 25},      # x3=50000:100 (500x), x2=2500:100 (25x)
    "DIAMOND": {3: 25, 2: 10},     # x3=2500:100 (25x), x2=1000:100 (10x)
    "BAR": {3: 5, 2: 3},           # x3=500:100 (5x), x2=300:100 (3x)
    "BELL": {3: 3, 2: 2},          # x3=300:100 (3x), x2=200:100 (2x)
    "SHOE": {3: 2, 2: 1},          # x3=200:100 (2x), x2=100:100 (1x)
    "LEMON": {3: 1, 2: 1},         # x3=100:100 (1x), x2=100:100 (1x)
    "MELON": {3: 0.75, 2: 1},      # x3=300:400 (0.75x), x2=100:100 (1x)
    "HEART": {3: 0.5, 2: 0.75},    # x3=100:200 (0.5x), x2=300:400 (0.75x)
    "CHERRY": {3: 0.5, 2: 0.25},   # x3=100:200 (0.5x), x2=100:400 (0.25x)
}

# Define probabilities for each symbol (higher value = less frequent)
SYMBOL_WEIGHTS = {
    "SEVEN": 1,    # Rarest
    "DIAMOND": 2, 
    "BAR": 4,
    "BELL": 6,
    "SHOE": 10,
    "LEMON": 14,
    "MELON": 16,
    "HEART": 20,
    "CHERRY": 25,  # Most common
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
        row_emojis = []
        for symbol_key in row:
            row_emojis.append(SYMBOLS[symbol_key]["emoji"])
        visual.append(" ".join(row_emojis))
    
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
                symbol_name = SYMBOLS[symbol]["name"]
                symbol_emoji = SYMBOLS[symbol]["emoji"]
                win_details = f"{count}x {symbol_name} {symbol_emoji} ({payout}x)"
    
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
