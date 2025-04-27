import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
import os
import json
from utils.currency import parse_bet, format_currency
from utils.slots import run_slots_game

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """Cog for handling gambling related commands and functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.balances_file = os.path.join(self.data_dir, "user_balances.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load user balances
        self.user_balances = self._load_balances()
        
        # Default starting balance for new users
        self.default_balance = 1000
    
    def _load_balances(self):
        """Load user balances from json file."""
        try:
            if os.path.exists(self.balances_file):
                with open(self.balances_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading balances: {e}")
            return {}
    
    def _save_balances(self):
        """Save user balances to json file."""
        try:
            with open(self.balances_file, 'w') as f:
                json.dump(self.user_balances, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving balances: {e}")
    
    def get_balance(self, user_id):
        """
        Get balance for a user.
        
        Args:
            user_id (str): Discord user ID
            
        Returns:
            int: User's current balance
        """
        user_id = str(user_id)
        if user_id not in self.user_balances:
            self.user_balances[user_id] = self.default_balance
            self._save_balances()
        
        return self.user_balances[user_id]
    
    def update_balance(self, user_id, amount):
        """
        Update user balance by adding or subtracting an amount.
        
        Args:
            user_id (str): Discord user ID
            amount (int): Amount to add (positive) or subtract (negative)
            
        Returns:
            int: New balance
        """
        user_id = str(user_id)
        current = self.get_balance(user_id)
        new_balance = current + amount
        
        # Ensure balance doesn't go below zero
        if new_balance < 0:
            new_balance = 0
            
        self.user_balances[user_id] = new_balance
        self._save_balances()
        
        return new_balance
    
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
        self.update_balance(user_id, -bet_amount)
        
        # Run slots game
        result, visual, winnings, win_details = run_slots_game(bet_amount)
        
        # Update balance with winnings if any
        if winnings > 0:
            self.update_balance(user_id, winnings)
        
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
        self.update_balance(user_id, -bet_amount)
        
        # Run slots game
        result, visual, winnings, win_details = run_slots_game(bet_amount)
        
        # Update balance with winnings if any
        if winnings > 0:
            self.update_balance(user_id, winnings)
        
        # Create result embed
        new_balance = self.get_balance(user_id)
        embed = self._create_slots_embed(message.author, bet_amount, result, visual, winnings, win_details, new_balance)
        
        await message.reply(embed=embed)
    
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
