import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
import os
from utils.currency import parse_bet, format_currency
from utils.slots import run_slots_game
from utils.db_service import get_user_balance, update_user_balance, get_or_create_user, check_daily_reward, get_leaderboard

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """Cog for handling gambling related commands and functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        # Default starting balance for new users (handled in db_service now)
        self.default_balance = 1000
        logger.info("Gambling cog initialized with database support")
    
    def get_balance(self, user_id):
        """
        Get balance for a user.
        
        Args:
            user_id (str): Discord user ID
            
        Returns:
            int: User's current balance
        """
        user_id = str(user_id)
        return get_user_balance(user_id)
    
    def update_balance(self, user_id, amount, game_type="general", details=None):
        """
        Update user balance by adding or subtracting an amount.
        
        Args:
            user_id (str): Discord user ID
            amount (int): Amount to add (positive) or subtract (negative)
            game_type (str): Type of game ('slots', 'animated_slots', etc.)
            details (str, optional): Additional details about the transaction
            
        Returns:
            int: New balance
        """
        user_id = str(user_id)
        
        # Get user from guild if possible to record username
        try:
            user = self.bot.get_user(int(user_id))
            username = user.name if user else f"User_{user_id}"
        except:
            username = f"User_{user_id}"
        
        # Ensure we don't go below zero (handled in db_service, but double check)
        if amount < 0:
            current = get_user_balance(user_id)
            if current + amount < 0:
                amount = -current  # Only subtract what's available
        
        return update_user_balance(user_id, username, amount, game_type, details)
    
    @app_commands.command(
        name="slots",
        description="Try your luck in the slots!"
    )
    @app_commands.describe(bet="The amount to bet. Use `m` for max and `a` for all in")
    async def slots(self, interaction: discord.Interaction, bet: str):
        """Slot machine command with slash command support."""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        # Get user balance and parse bet
        balance = self.get_balance(user_id)
        
        try:
            bet_amount = parse_bet(bet, balance)
        except ValueError as e:
            await interaction.followup.send(f"Error: {str(e)}")
            return
        
        # Check if bet is valid
        if bet_amount <= 0:
            await interaction.followup.send("Bet amount must be greater than 0.")
            return
        
        if bet_amount > balance:
            await interaction.followup.send(f"You don't have enough funds! Your balance is {format_currency(balance)}.")
            return
        
        # Update balance (deduct bet)
        self.update_balance(user_id, -bet_amount, "slots", "Bet placed")
        
        # Run slots game
        result, visual, winnings, win_details = run_slots_game(bet_amount)
        
        # Update balance with winnings if any
        if winnings > 0:
            self.update_balance(user_id, winnings, "slots", f"Win: {win_details}")
        
        # Create result embed
        new_balance = self.get_balance(user_id)
        embed = self._create_slots_embed(interaction.user, bet_amount, result, visual, winnings, win_details, new_balance)
        
        await interaction.followup.send(embed=embed)
    
    async def slots_command(self, message, bet_str):
        """Process slots command from message mention."""
        user_id = str(message.author.id)
        
        # Get user balance and parse bet
        balance = self.get_balance(user_id)
        
        try:
            bet_amount = parse_bet(bet_str, balance)
        except ValueError as e:
            await message.reply(f"Error: {str(e)}")
            return
        
        # Check if bet is valid
        if bet_amount <= 0:
            await message.reply("Bet amount must be greater than 0.")
            return
        
        if bet_amount > balance:
            await message.reply(f"You don't have enough funds! Your balance is {format_currency(balance)}.")
            return
        
        # Update balance (deduct bet)
        self.update_balance(user_id, -bet_amount, "slots", "Bet placed")
        
        # Run slots game
        result, visual, winnings, win_details = run_slots_game(bet_amount)
        
        # Update balance with winnings if any
        if winnings > 0:
            self.update_balance(user_id, winnings, "slots", f"Win: {win_details}")
        
        # Create result embed
        new_balance = self.get_balance(user_id)
        embed = self._create_slots_embed(message.author, bet_amount, result, visual, winnings, win_details, new_balance)
        
        await message.reply(embed=embed)
    
    @app_commands.command(
        name="balance",
        description="Check your current balance"
    )
    async def balance(self, interaction: discord.Interaction):
        """Command to check your balance."""
        user_id = str(interaction.user.id)
        balance = self.get_balance(user_id)
        
        embed = discord.Embed(
            title="💰 Casino Balance 💰",
            description=f"Your current balance is **{format_currency(balance)}**",
            color=discord.Color.gold()
        )
        
        embed.set_author(name=f"{interaction.user.name}'s Balance", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Piglet Casino | Try your luck with /slots!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="daily",
        description="Collect your daily reward"
    )
    async def daily(self, interaction: discord.Interaction):
        """Command to collect daily reward."""
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        success, message, amount = check_daily_reward(user_id, username)
        
        if success:
            color = discord.Color.green()
            title = "✅ Daily Reward Claimed"
        else:
            color = discord.Color.red()
            title = "❌ Daily Reward Not Available"
        
        embed = discord.Embed(
            title=title,
            description=message,
            color=color
        )
        
        embed.set_author(name=f"{interaction.user.name}'s Daily Reward", icon_url=interaction.user.display_avatar.url)
        
        if success:
            balance = self.get_balance(user_id)
            embed.add_field(name="Current Balance", value=format_currency(balance), inline=True)
        
        embed.set_footer(text="Piglet Casino | Try your luck with /slots!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="leaderboard",
        description="See the richest players in the casino"
    )
    async def leaderboard(self, interaction: discord.Interaction):
        """Command to view the leaderboard of richest players."""
        await interaction.response.defer()
        
        top_users = get_leaderboard(10)
        
        if not top_users:
            await interaction.followup.send("No users found on the leaderboard yet.")
            return
        
        embed = discord.Embed(
            title="🏆 Casino Leaderboard 🏆",
            description="The richest players in Piglet Casino",
            color=discord.Color.gold()
        )
        
        for i, user in enumerate(top_users, 1):
            # Try to get Discord username
            try:
                discord_user = self.bot.get_user(int(user.id))
                display_name = discord_user.name if discord_user else user.username
            except:
                display_name = user.username
            
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{emoji} {display_name}",
                value=format_currency(user.balance),
                inline=False
            )
        
        embed.set_footer(text="Piglet Casino | Try your luck with /slots!")
        
        await interaction.followup.send(embed=embed)
    
    def _create_slots_embed(self, user, bet_amount, result, visual, winnings, win_details, new_balance):
        """Create an embed for slots result."""
        if winnings > 0:
            title = f"🎰 You won {format_currency(winnings)}! 🎰"
            color = discord.Color.green()
        else:
            title = "🎰 Better luck next time! 🎰"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title=title,
            description=f"**{visual}**",
            color=color
        )
        
        embed.set_author(name=f"{user.name}'s Slot Machine", icon_url=user.display_avatar.url)
        embed.add_field(name="Bet", value=format_currency(bet_amount), inline=True)
        
        # Add win details if available
        if win_details:
            embed.add_field(name="Match", value=win_details, inline=True)
        
        embed.add_field(name="Balance", value=format_currency(new_balance), inline=True)
        embed.set_footer(text="Piglet Casino | Try your luck again with /slots!")
        
        return embed

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Gambling(bot))