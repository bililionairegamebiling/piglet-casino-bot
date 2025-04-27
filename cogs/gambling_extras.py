import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
from utils.currency import parse_bet, format_currency
from utils.db_service import check_work_reward, get_user_balance, update_user_balance

logger = logging.getLogger(__name__)

class GamblingExtras(commands.Cog):
    """Additional gambling games and utility commands."""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("GamblingExtras cog initialized")
    
    @app_commands.command(
        name="work",
        description="Work to earn some coins (available every 10 minutes)"
    )
    async def work(self, interaction: discord.Interaction):
        """Command to work for coins."""
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        success, message, amount = check_work_reward(user_id, username)
        
        if success:
            color = discord.Color.green()
            title = "💼 Work Completed"
        else:
            color = discord.Color.red()
            title = "💼 Work Not Available"
        
        embed = discord.Embed(
            title=title,
            description=message,
            color=color
        )
        
        embed.set_author(name=f"{interaction.user.name}'s Work", icon_url=interaction.user.display_avatar.url)
        
        if success:
            balance = get_user_balance(user_id)
            embed.add_field(name="Current Balance", value=format_currency(balance), inline=True)
        
        embed.set_footer(text="Piglet Casino | Try your luck with /slots!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="coinflip",
        description="Flip a coin and bet on the outcome"
    )
    @app_commands.describe(
        bet="Amount to bet",
        choice="Heads or Tails"
    )
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Heads", value="heads"),
            app_commands.Choice(name="Tails", value="tails")
        ]
    )
    async def coinflip(self, interaction: discord.Interaction, bet: str, choice: str):
        """Flip a coin and bet on the outcome."""
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        # Get user balance and parse bet
        balance = get_user_balance(user_id)
        
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
        update_user_balance(user_id, username, -bet_amount, "coinflip", "Bet placed")
        
        # Flip the coin (50/50 chance)
        result = random.choice(["heads", "tails"])
        
        # Determine if player won
        win = choice == result
        
        # Create result embed
        if win:
            winnings = bet_amount  # 2x the bet (return + profit)
            update_user_balance(user_id, username, winnings * 2, "coinflip", f"Win: {result}")
            
            title = f"🪙 You won {format_currency(winnings)}! 🪙"
            color = discord.Color.green()
        else:
            title = "🪙 Better luck next time! 🪙"
            color = discord.Color.red()
        
        # Get emoji for result
        result_emoji = "🟡" if result == "heads" else "⚪"
        
        new_balance = get_user_balance(user_id)
        
        embed = discord.Embed(
            title=title,
            description=f"The coin landed on **{result.upper()}** {result_emoji}",
            color=color
        )
        
        embed.set_author(name=f"{interaction.user.name}'s Coinflip", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Your Choice", value=choice.upper(), inline=True)
        embed.add_field(name="Bet", value=format_currency(bet_amount), inline=True)
        embed.add_field(name="Balance", value=format_currency(new_balance), inline=True)
        embed.set_footer(text="Piglet Casino | Try your luck again with /coinflip!")
        
        await interaction.followup.send(embed=embed)
        
async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(GamblingExtras(bot))