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
            if any(cmd in content for cmd in [" slots ", " sl ", " slot "]):
                # Extract bet amount
                parts = content.split()
                try:
                    for i, part in enumerate(parts):
                        if part.lower() in ["slots", "sl", "slot"] and i + 1 < len(parts):
                            bet = parts[i + 1]
                            cog = bot.get_cog("Gambling")
                            if cog:
                                await cog.slots_command(message, bet)
                            break
                except Exception as e:
                    logger.error(f"Error processing mention command: {e}")
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
        except Exception as e:
            logger.error(f"Error loading cogs: {e}")
    
    return bot
