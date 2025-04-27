import os
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

def setup_bot():
    """
    Set up the Discord bot with necessary configurations and load all cogs.
    
    Returns:
        commands.Bot: Configured bot instance
    """
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    # Initialize bot with command prefix and intents
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("!"),
        intents=intents,
        help_command=None,
        case_insensitive=True,
    )
    
    # Register event handlers
    @bot.event
    async def on_ready():
        """Event triggered when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} guilds")
        
        # Set the bot's status
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, 
                name="Piglet Casino | /slots"
            )
        )
        
        # Register slash commands globally
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    @bot.event
    async def on_message(message):
        """
        Event triggered when a message is sent in a channel the bot can see.
        Handles command processing and mention detection.
        """
        # Ignore messages from the bot itself
        if message.author.bot:
            return
            
        # Check for mention commands (alternatives to slash commands)
        if bot.user.mentioned_in(message) and not message.mention_everyone:
            content = message.content.lower()
            
            # Check for slots commands
            slots_keywords = ["slots", "sl", "slot"]
            # Check if any of the slots keywords are in the content
            if any(keyword in content for keyword in slots_keywords):
                # Extract bet amount
                parts = content.split()
                bet = "1"  # Default bet amount
                try:
                    # Find the slots keyword in the message
                    for i, part in enumerate(parts):
                        if part.lower() in slots_keywords:
                            # Look for bet amount after the command
                            if i + 1 < len(parts):
                                bet = parts[i + 1]
                            break
                    
                    # Get the gambling cog and run the slots command
                    cog = bot.get_cog("Gambling")
                    if cog:
                        # For debugging
                        logger.info(f"Executing slots command with bet: {bet}")
                        await cog.slots_command(message, bet)
                except Exception as e:
                    logger.error(f"Error processing slots command: {e}")
                return
                
            # Check for coinflip commands
            coinflip_keywords = ["coinflip", "coin", "flip"]
            if any(keyword in content for keyword in coinflip_keywords):
                parts = content.split()
                try:
                    bet_str = "1"  # Default bet
                    choice = "heads"  # Default choice
                    
                    for i, part in enumerate(parts):
                        if part.lower() in coinflip_keywords:
                            # Look for choice and bet amount after the command
                            for j in range(i + 1, min(len(parts), i + 4)):
                                if parts[j].lower() in ["heads", "head", "h"]:
                                    choice = "heads"
                                elif parts[j].lower() in ["tails", "tail", "t"]:
                                    choice = "tails"
                                elif parts[j].isdigit() or parts[j].lower() in ["all", "max"]:
                                    bet_str = parts[j]
                            
                            # Call the coinflip method
                            import random
                            from utils.currency import parse_bet, format_currency
                            from utils.db_service import get_user_balance, update_user_balance
                            
                            user_id = str(message.author.id)
                            username = message.author.name
                            
                            # Parse bet and validate
                            balance = get_user_balance(user_id)
                            try:
                                bet_amount = parse_bet(bet_str, balance)
                            except ValueError as e:
                                await message.channel.send(f"Error: {str(e)}")
                                break
                            
                            if bet_amount <= 0:
                                await message.channel.send("Bet amount must be greater than 0.")
                                break
                            
                            if bet_amount > balance:
                                await message.channel.send(f"You don't have enough funds! Your balance is {format_currency(balance)}.")
                                break
                            
                            # Deduct bet
                            update_user_balance(user_id, username, -bet_amount, "coinflip", "Bet placed")
                            
                            # Flip the coin
                            result = random.choice(["heads", "tails"])
                            result_emoji = "🟡" if result == "heads" else "⚪"
                            
                            # Determine win/loss
                            win = choice == result
                            if win:
                                winnings = bet_amount  # 1x profit
                                update_user_balance(user_id, username, bet_amount * 2, "coinflip", f"Win: {result}")
                                await message.channel.send(f"🪙 The coin landed on **{result.upper()}** {result_emoji}! You won {format_currency(winnings)}! New balance: {format_currency(get_user_balance(user_id))}")
                            else:
                                await message.channel.send(f"🪙 The coin landed on **{result.upper()}** {result_emoji}! You lost {format_currency(bet_amount)}. New balance: {format_currency(get_user_balance(user_id))}")
                            
                            break
                except Exception as e:
                    logger.error(f"Error processing coinflip command: {e}")
                    await message.channel.send("Error processing coinflip command. Try using the slash command `/coinflip` instead.")
                return
                
            # Check for blackjack commands
            blackjack_keywords = ["blackjack", "bj", "21"]
            if any(keyword in content for keyword in blackjack_keywords):
                parts = content.split()
                try:
                    bet_str = "1"  # Default bet
                    
                    for i, part in enumerate(parts):
                        if part.lower() in blackjack_keywords and i + 1 < len(parts):
                            bet_str = parts[i + 1]
                            
                            # Redirect to the slash command for blackjack
                            await message.channel.send(f"Starting a blackjack game with bet: {bet_str}. Use the slash command `/blackjack {bet_str}` for a better experience with buttons!")
                            break
                except Exception as e:
                    logger.error(f"Error processing blackjack command: {e}")
                    await message.channel.send("Error processing blackjack command. Try using the slash command `/blackjack` instead.")
                return
        
        # Process regular commands
        await bot.process_commands(message)
    
    # Load cogs
    @bot.event
    async def setup_hook():
        """Asynchronous setup for the bot."""
        try:
            # Load the gambling cog
            from cogs.gambling import Gambling
            await bot.add_cog(Gambling(bot))
            logger.info("Loaded Gambling cog")
            
            # Load the animated slots cog
            from cogs.animated_slots import AnimatedSlots
            await bot.add_cog(AnimatedSlots(bot))
            logger.info("Loaded AnimatedSlots cog")
            
            # Load gambling extras cog
            from cogs.gambling_extras import GamblingExtras
            await bot.add_cog(GamblingExtras(bot))
            logger.info("Loaded GamblingExtras cog")
            
            # Load blackjack cog
            from cogs.blackjack import Blackjack
            await bot.add_cog(Blackjack(bot))
            logger.info("Loaded Blackjack cog")
        except Exception as e:
            logger.error(f"Error loading cogs: {e}")
    
    return bot
