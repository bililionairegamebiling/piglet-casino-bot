from PIL import Image, ImageDraw, ImageFont
import os

# Define constants
SYMBOL_SIZE = 180
SYMBOL_COLORS = {
    "SEVEN": (255, 0, 0, 255),       # Red
    "DIAMOND": (0, 191, 255, 255),   # Deep sky blue
    "BAR": (255, 120, 0, 255),       # Orange
    "BELL": (255, 215, 0, 255),      # Gold
    "SHOE": (139, 69, 19, 255),      # Brown
    "LEMON": (255, 255, 0, 255),     # Yellow
    "MELON": (0, 255, 0, 255),       # Green
    "HEART": (255, 0, 0, 255),       # Red
    "CHERRY": (139, 0, 0, 255),      # Dark red
}

# Define text for each symbol
SYMBOL_TEXT = {
    "SEVEN": "7",
    "DIAMOND": "♦",
    "BAR": "BAR",
    "BELL": "🔔",
    "SHOE": "👞",
    "LEMON": "🍋",
    "MELON": "🍉",
    "HEART": "❤",
    "CHERRY": "🍒",
}

# Define file names
SYMBOL_FILES = {
    "SEVEN": "sseven.png",
    "DIAMOND": "sdiamond.png",
    "BAR": "sbar.png",
    "BELL": "sbell.png",
    "SHOE": "sshoe.png",
    "LEMON": "slemon.png",
    "MELON": "smelon.png",
    "HEART": "sheart.png",
    "CHERRY": "scherry.png",
}

def generate_symbol_image(symbol_key):
    """Generate an image for a slot symbol."""
    # Create a new image for the symbol
    img = Image.new('RGBA', (SYMBOL_SIZE, SYMBOL_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Get color for the symbol
    color = SYMBOL_COLORS.get(symbol_key, (255, 255, 255, 255))
    
    # Draw a circle for the background
    padding = 10
    diameter = SYMBOL_SIZE - 2 * padding
    draw.ellipse(
        (padding, padding, padding + diameter, padding + diameter),
        fill=color,
        outline=(255, 255, 255, 255),
        width=3
    )
    
    # Get symbol text
    text = SYMBOL_TEXT.get(symbol_key, "?")
    
    # Try to get a font for drawing text
    try:
        font = ImageFont.truetype("Arial", 100)
    except IOError:
        try:
            # Fallback to DejaVuSans
            font = ImageFont.truetype("DejaVuSans.ttf", 100)
        except IOError:
            # Final fallback to default
            font = ImageFont.load_default()
    
    # Calculate text position
    try:
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Simple estimation
            text_width = 100
            text_height = 100
    except:
        text_width, text_height = 80, 80
    
    # Draw the text
    text_x = SYMBOL_SIZE // 2 - text_width // 2
    text_y = SYMBOL_SIZE // 2 - text_height // 2
    
    # Use white text color for dark backgrounds
    if sum(color[:3]) < 500:  # If background is dark
        text_color = (255, 255, 255, 255)
    else:
        text_color = (0, 0, 0, 255)
        
    draw.text(
        (text_x, text_y),
        text,
        fill=text_color,
        font=font
    )
    
    return img

def main():
    """Generate all slot symbol images."""
    output_dir = "assets/slot_symbols"
    os.makedirs(output_dir, exist_ok=True)
    
    for symbol_key, file_name in SYMBOL_FILES.items():
        img = generate_symbol_image(symbol_key)
        output_path = os.path.join(output_dir, file_name)
        img.save(output_path)
        print(f"Generated {symbol_key} image at {output_path}")

if __name__ == "__main__":
    main()