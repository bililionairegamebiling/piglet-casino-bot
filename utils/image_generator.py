import os
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# Define constants
SYMBOL_SIZE = 180
REEL_WIDTH = 200
BACKGROUND_COLOR = (40, 40, 40, 255)  # Dark gray background
SYMBOL_COLORS = {
    "7️⃣": (255, 215, 0, 255),     # Gold
    "💎": (0, 191, 255, 255),      # Deep sky blue
    "🎰": (255, 69, 0, 255),       # Red-orange
    "🔔": (255, 215, 0, 255),      # Gold
    "👞": (139, 69, 19, 255),      # Brown
    "🍋": (255, 255, 0, 255),      # Yellow
    "🍉": (255, 0, 0, 255),        # Red
    "❤️": (255, 0, 0, 255),        # Red
    "🍒": (139, 0, 0, 255),        # Dark red
}

def generate_slots_assets():
    """Generate all required slot machine assets."""
    assets_dir = os.path.join("assets", "slots")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create reel image
    reel_path = os.path.join(assets_dir, "reel.png")
    facade_path = os.path.join(assets_dir, "facade.png")
    
    if not os.path.exists(reel_path):
        _generate_reel_image(reel_path)
        logger.info(f"Generated reel image at {reel_path}")
    
    if not os.path.exists(facade_path):
        _generate_facade_image(facade_path)
        logger.info(f"Generated facade image at {facade_path}")
    
    return {
        "reel": reel_path,
        "facade": facade_path
    }

def _generate_reel_image(output_path):
    """Generate the slot machine reel image with all symbols."""
    # Get symbols from slots module
    from utils.slots import PAYOUTS
    symbols = list(PAYOUTS.keys())
    
    # Calculate reel height (symbols repeated in blocks of 6)
    num_blocks = 6
    reel_height = SYMBOL_SIZE * len(symbols) * num_blocks
    
    # Create a new image for the reel
    reel = Image.new('RGBA', (REEL_WIDTH, reel_height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(reel)
    
    # Try to get a font for drawing text (use default if not available)
    try:
        font = ImageFont.truetype("Arial", 120)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw each symbol multiple times to create blocks
    for block in range(num_blocks):
        for i, symbol in enumerate(symbols):
            y_pos = (block * len(symbols) + i) * SYMBOL_SIZE
            
            # Draw symbol background
            color = SYMBOL_COLORS.get(symbol, (255, 255, 255, 255))
            draw.rectangle(
                (10, y_pos + 10, REEL_WIDTH - 10, y_pos + SYMBOL_SIZE - 10),
                fill=(color[0], color[1], color[2], 100),  # Semi-transparent
                outline=(255, 255, 255, 180),
                width=2
            )
            
            # Get text size - Pillow's newer versions use get_text_dimensions instead of textsize
            try:
                # For newer Pillow versions
                if hasattr(draw, "textbbox"):
                    bbox = draw.textbbox((0, 0), symbol, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                # Fallback for any version
                else:
                    # Use simple estimation based on font size
                    font_size = 120
                    text_width = font_size
                    text_height = font_size
            except:
                # Fallback dimensions
                text_width, text_height = 100, 100
            
            # Draw the symbol text
            draw.text(
                (REEL_WIDTH // 2 - text_width // 2, y_pos + SYMBOL_SIZE // 2 - text_height // 2),
                symbol,
                fill=(255, 255, 255, 255),
                font=font
            )
    
    # Save the reel image
    reel.save(output_path)

def _generate_facade_image(output_path):
    """Generate the slot machine facade image."""
    # Dimensions must match with 3 reels side by side
    width = REEL_WIDTH * 3 + 50  # Reels plus padding
    height = SYMBOL_SIZE * 3     # Show 3 symbols vertically
    
    # Create a new image for the facade
    facade = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(facade)
    
    # Draw the outline of the machine
    draw.rectangle(
        (0, 0, width - 1, height - 1),
        fill=(0, 0, 0, 0),
        outline=(255, 215, 0, 255),  # Gold
        width=5
    )
    
    # Draw the view frame around the middle row
    frame_top = SYMBOL_SIZE
    frame_bottom = SYMBOL_SIZE * 2
    
    # Left frame line
    draw.line(
        [(20, frame_top), (20, frame_bottom)],
        fill=(255, 215, 0, 255),
        width=5
    )
    
    # Right frame line
    draw.line(
        [(width - 20, frame_top), (width - 20, frame_bottom)],
        fill=(255, 215, 0, 255),
        width=5
    )
    
    # Top frame line
    draw.line(
        [(20, frame_top), (width - 20, frame_top)],
        fill=(255, 215, 0, 255),
        width=5
    )
    
    # Bottom frame line
    draw.line(
        [(20, frame_bottom), (width - 20, frame_bottom)],
        fill=(255, 215, 0, 255),
        width=5
    )
    
    # Draw dividers between reels
    for i in range(1, 3):
        x = 25 + REEL_WIDTH * i
        draw.line(
            [(x, 0), (x, height)],
            fill=(255, 215, 0, 255),
            width=3
        )
    
    # Save the facade image
    facade.save(output_path)

if __name__ == "__main__":
    # If run directly, generate all assets
    generate_slots_assets()