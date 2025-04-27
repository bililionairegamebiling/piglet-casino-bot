import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
from datetime import datetime, timedelta
from utils.currency import parse_bet, format_currency
from utils.db_service import check_work_reward, get_user_balance, update_user_balance, get_user_transactions, get_or_create_user

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
    
    @app_commands.command(
        name="profile",
        description="View your casino profile and transaction history"
    )
    async def profile(self, interaction: discord.Interaction):
        """Command to view user profile and transaction history."""
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        # Get user and transaction data
        user = get_or_create_user(user_id, username)
        transactions = get_user_transactions(user_id, limit=5)
        balance = user.balance
        
        # Create embed
        embed = discord.Embed(
            title="🎰 Casino Profile",
            description=f"Here's your casino profile information, {interaction.user.mention}!",
            color=discord.Color.gold()
        )
        
        embed.set_author(name=f"{username}'s Profile", icon_url=interaction.user.display_avatar.url)
        
        # Add main stats
        embed.add_field(name="Balance", value=format_currency(balance), inline=True)
        embed.add_field(name="Account Age", value=f"{(datetime.utcnow() - user.created_at).days} days", inline=True)
        
        # Add reward timers
        daily_status = "Available Now! 🎁" 
        if user.last_daily:
            time_since_daily = datetime.utcnow() - user.last_daily
            if time_since_daily < timedelta(hours=20):
                time_left = timedelta(hours=20) - time_since_daily
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                daily_status = f"Available in {hours}h {minutes}m ⏳"
        
        work_status = "Available Now! 💼"
        if user.last_work:
            time_since_work = datetime.utcnow() - user.last_work
            if time_since_work < timedelta(minutes=10):
                time_left = timedelta(minutes=10) - time_since_work
                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                work_status = f"Available in {minutes}m {seconds}s ⏳"
                
        embed.add_field(name="Daily Reward", value=daily_status, inline=True)
        embed.add_field(name="Work Reward", value=work_status, inline=True)
        
        # Add recent transactions if available
        if transactions:
            embed.add_field(name="\u200b", value="\u200b", inline=False)  # Spacer
            embed.add_field(name="Recent Transactions", value="\u200b", inline=False)
            
            for transaction in transactions:
                # Format timestamp
                time_ago = datetime.utcnow() - transaction.timestamp
                if time_ago < timedelta(minutes=1):
                    time_str = "just now"
                elif time_ago < timedelta(hours=1):
                    time_str = f"{int(time_ago.total_seconds() // 60)}m ago"
                elif time_ago < timedelta(days=1):
                    time_str = f"{int(time_ago.total_seconds() // 3600)}h ago"
                else:
                    time_str = f"{time_ago.days}d ago"
                
                # Format amount with color and sign
                if transaction.amount > 0:
                    amount_str = f"**+{format_currency(transaction.amount)}**"
                else:
                    amount_str = f"**-{format_currency(abs(transaction.amount))}**"
                
                # Format game type
                game_type = transaction.game_type.replace('_', ' ').title()
                
                # Add transaction field
                embed.add_field(
                    name=f"{game_type} ({time_str})",
                    value=f"{amount_str} - {transaction.details or 'No details'}",
                    inline=False
                )
        else:
            embed.add_field(
                name="Recent Transactions", 
                value="No recent transactions found.", 
                inline=False
            )
        
        embed.set_footer(text="Piglet Casino | Try your luck with /slots, /coinflip, or /blackjack!")
        
        await interaction.response.send_message(embed=embed)
        
async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(GamblingExtras(bot))