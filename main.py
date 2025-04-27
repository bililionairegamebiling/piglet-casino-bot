import os
import logging
import threading
from flask import Flask, render_template, jsonify
from bot import setup_bot

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Homepage route that displays bot status and info."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API route to check bot status."""
    return jsonify({
        'status': 'online',
        'name': 'Piglet Casino Bot',
        'description': 'A Discord bot that implements a virtual casino with slots gambling functionality and virtual currency system'
    })

def run_discord_bot():
    """
    Function to run the Discord bot in a separate thread.
    """
    # Get token from environment variable
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        return
    
    # Setup and run bot
    bot = setup_bot()
    
    logger.info("Starting Piglet Casino Bot...")
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Error running bot: {e}")

def main():
    """
    Main entry point for the application.
    Runs the Discord bot in a separate thread.
    """
    # Create and start bot thread
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # This will only be reached when running the file directly
    # When run through gunicorn, only the Flask app will be used
    if __name__ == "__main__":
        run_discord_bot()

# Initialize bot thread when imported by gunicorn
if os.environ.get('GUNICORN_CMD_ARGS') is not None:
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True
    bot_thread.start()

# Run main function when executed directly
if __name__ == "__main__":
    main()
