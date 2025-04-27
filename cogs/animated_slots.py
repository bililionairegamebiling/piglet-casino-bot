import os
import random
import bisect
import discord
from discord.ext import commands
from discord import app_commands
import logging
from PIL import Image
import tempfile

from utils.currency import parse_bet, format_currency
from utils.image_generator import generate_slots_assets
from utils.slots import PAYOUTS

logger = logging.getLogger(__name__)

class AnimatedSlots(commands.Cog):
    """Cog for handling animated slots functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.assets = generate_slots_assets()
        
        # Import Gambling cog for currency management
        self.gambling_cog = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        """On ready, get reference to Gambling cog."""
        self.gambling_cog = self.bot.get_cog("Gambling")
        if not self.gambling_cog:
            logger.warning("Gambling cog not found, animated slots will have limited functionality")
    
    def get_symbol_index(self, position):
        """Get the symbol at a given position on the reel."""
        # Each symbol is SYMBOL_SIZE pixels tall, and there are 9 symbols total
        # repeated in 6 blocks, so 54 total positions
        symbol_index = position % 9  # 9 different symbols
        # Convert to 0-based index in PAYOUTS keys
        return symbol_index
    
    def get_symbol_from_index(self, index):
        """Get the symbol string from its index."""
        symbols = list(PAYOUTS.keys())
        if index is not None and 0 <= index < len(symbols):
            return symbols[index]
        else:
            # Return default symbol if index is invalid
            return "🍒"
    
    def calculate_win(self, s1, s2, s3):
        """Calculate win based on symbol indices."""
        # Convert indices to actual symbols
        symbols = list(PAYOUTS.keys())
        sym1 = symbols[s1 % 9]
        sym2 = symbols[s2 % 9]
        sym3 = symbols[s3 % 9]
        
        result = {
            "win": False,
            "amount": 0,
            "symbol": None,
            "count": 0,
            "multiplier": 0
        }
        
        # Check for 3 matching symbols
        if sym1 == sym2 == sym3:
            if sym1 in PAYOUTS and 3 in PAYOUTS[sym1]:
                result["win"] = True
                result["symbol"] = sym1
                result["count"] = 3
                result["multiplier"] = PAYOUTS[sym1][3]
        
        # Check for 2 matching symbols
        elif sym1 == sym2 or sym1 == sym3 or sym2 == sym3:
            matching_symbol = None
            if sym1 == sym2:
                matching_symbol = sym1
            elif sym1 == sym3:
                matching_symbol = sym1
            elif sym2 == sym3:
                matching_symbol = sym2
                
            if matching_symbol in PAYOUTS and 2 in PAYOUTS[matching_symbol]:
                result["win"] = True
                result["symbol"] = matching_symbol
                result["count"] = 2
                result["multiplier"] = PAYOUTS[matching_symbol][2]
        
        return result
    
    @app_commands.command(
        name="animated_slots",
        description="Try your luck with animated slots!"
    )
    @app_commands.describe(bet="The amount to bet. Use `m` for max and `a` for all in")
    async def animated_slots(self, interaction: discord.Interaction, bet: str):
        """Animated slot machine command with slash command support."""
        await interaction.response.defer()
        
        if not self.gambling_cog:
            await interaction.followup.send("Error: Currency system not available")
            return
        
        user_id = str(interaction.user.id)
        
        # Get user balance and parse bet
        balance = self.gambling_cog.get_balance(user_id)
        
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
        self.gambling_cog.update_balance(user_id, -bet_amount)
        
        # Run slots animation
        try:
            # Load assets
            reel = Image.open(self.assets["reel"]).convert('RGBA')
            facade = Image.open(self.assets["facade"]).convert('RGBA')
            
            rw, rh = reel.size
            item = 180  # Symbol height
            items = rh // item
            
            # Generate random positions for each reel
            s1 = random.randint(1, items-1)
            s2 = random.randint(1, items-1)
            s3 = random.randint(1, items-1)
            
            # Force a win sometimes (12% chance)
            win_rate = 12/100
            if random.random() < win_rate:
                symbols_weights = [3.5, 7, 15, 25, 55]  # Weights for symbols
                x = round(random.random()*100, 1)
                pos = bisect.bisect(symbols_weights, x)
                s1 = pos + (random.randint(1, (items//6)-1) * 6)
                s2 = pos + (random.randint(1, (items//6)-1) * 6)
                s3 = pos + (random.randint(1, (items//6)-1) * 6)
                # Ensure no reel hits the last symbol
                s1 = s1 - 6 if s1 >= items else s1
                s2 = s2 - 6 if s2 >= items else s2
                s3 = s3 - 6 if s3 >= items else s3
            
            # Create animation frames
            images = []
            speed = 6
            for i in range(1, (item//speed)+1):
                bg = Image.new('RGBA', facade.size, color=(40, 40, 40, 255))
                bg.paste(reel, (25 + rw*0, 100-(speed * i * s1)))
                bg.paste(reel, (25 + rw*1, 100-(speed * i * s2)))
                bg.paste(reel, (25 + rw*2, 100-(speed * i * s3)))
                bg.alpha_composite(facade)
                images.append(bg)
            
            # Save as GIF
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as temp:
                fp = temp.name
            
            images[0].save(
                fp,
                save_all=True,
                append_images=images[1:],
                duration=50,  # Duration of each frame in ms
                loop=0        # Loop forever
            )
            
            # Calculate symbol indices in the middle row
            sym1_idx = self.get_symbol_index(s1)
            sym2_idx = self.get_symbol_index(s2)
            sym3_idx = self.get_symbol_index(s3)
            
            # Get actual symbols
            sym1 = self.get_symbol_from_index(sym1_idx)
            sym2 = self.get_symbol_from_index(sym2_idx)
            sym3 = self.get_symbol_from_index(sym3_idx)
            middle_row = f"{sym1} {sym2} {sym3}"
            
            # Calculate win
            win_result = self.calculate_win(sym1_idx, sym2_idx, sym3_idx)
            
            # Process results
            if win_result["win"]:
                winnings = int(bet_amount * win_result["multiplier"])
                self.gambling_cog.update_balance(user_id, winnings)
                result = ('won', winnings)
                win_details = f"{win_result['count']}x {win_result['symbol']} ({win_result['multiplier']}x)"
            else:
                result = ('lost', bet_amount)
                win_details = None
                winnings = 0
            
            new_balance = self.gambling_cog.get_balance(user_id)
            
            # Create result embed
            if result[0] == 'won':
                title = f"🎰 You won {format_currency(winnings)}! 🎰"
                color = discord.Color.green()
            else:
                title = "🎰 Better luck next time! 🎰"
                color = discord.Color.red()
            
            embed = discord.Embed(
                title=title,
                description=f"**{middle_row}**",
                color=color
            )
            
            embed.set_author(name=f"{interaction.user.name}'s Slot Machine", icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Bet", value=format_currency(bet_amount), inline=True)
            
            # Add win details if available
            if win_details:
                embed.add_field(name="Match", value=win_details, inline=True)
            
            embed.add_field(name="Balance", value=format_currency(new_balance), inline=True)
            embed.set_footer(text="Piglet Casino | Try your luck again with /animated_slots!")
            
            # Send the GIF and embed
            file = discord.File(fp, filename="slots.gif")
            embed.set_image(url=f"attachment://slots.gif")
            
            await interaction.followup.send(file=file, embed=embed)
            
            # Clean up temp file
            try:
                os.unlink(fp)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in animated slots: {e}")
            await interaction.followup.send(f"An error occurred: {e}")
    
    @commands.command(name="animated_slots", aliases=["aslots", "asl"])
    async def animated_slots_command(self, ctx, bet_str: str = "1"):
        """Command version of animated slots for text commands."""
        if not self.gambling_cog:
            await ctx.reply("Error: Currency system not available")
            return
        
        user_id = str(ctx.author.id)
        
        # Get user balance and parse bet
        balance = self.gambling_cog.get_balance(user_id)
        
        try:
            bet_amount = parse_bet(bet_str, balance)
        except ValueError as e:
            await ctx.reply(f"Error: {str(e)}")
            return
        
        # Check if bet is valid
        if bet_amount <= 0:
            await ctx.reply("Bet amount must be greater than 0.")
            return
        
        if bet_amount > balance:
            await ctx.reply(f"You don't have enough funds! Your balance is {format_currency(balance)}.")
            return
        
        # Update balance (deduct bet)
        self.gambling_cog.update_balance(user_id, -bet_amount)
        
        # Run slots animation
        try:
            # Load assets
            reel = Image.open(self.assets["reel"]).convert('RGBA')
            facade = Image.open(self.assets["facade"]).convert('RGBA')
            
            rw, rh = reel.size
            item = 180  # Symbol height
            items = rh // item
            
            # Generate random positions for each reel
            s1 = random.randint(1, items-1)
            s2 = random.randint(1, items-1)
            s3 = random.randint(1, items-1)
            
            # Force a win sometimes (12% chance)
            win_rate = 12/100
            if random.random() < win_rate:
                symbols_weights = [3.5, 7, 15, 25, 55]  # Weights for symbols
                x = round(random.random()*100, 1)
                pos = bisect.bisect(symbols_weights, x)
                s1 = pos + (random.randint(1, (items//6)-1) * 6)
                s2 = pos + (random.randint(1, (items//6)-1) * 6)
                s3 = pos + (random.randint(1, (items//6)-1) * 6)
                # Ensure no reel hits the last symbol
                s1 = s1 - 6 if s1 >= items else s1
                s2 = s2 - 6 if s2 >= items else s2
                s3 = s3 - 6 if s3 >= items else s3
            
            # Create animation frames
            images = []
            speed = 6
            for i in range(1, (item//speed)+1):
                bg = Image.new('RGBA', facade.size, color=(40, 40, 40, 255))
                bg.paste(reel, (25 + rw*0, 100-(speed * i * s1)))
                bg.paste(reel, (25 + rw*1, 100-(speed * i * s2)))
                bg.paste(reel, (25 + rw*2, 100-(speed * i * s3)))
                bg.alpha_composite(facade)
                images.append(bg)
            
            # Save as GIF
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as temp:
                fp = temp.name
            
            images[0].save(
                fp,
                save_all=True,
                append_images=images[1:],
                duration=50,  # Duration of each frame in ms
                loop=0        # Loop forever
            )
            
            # Calculate symbol indices in the middle row
            sym1_idx = self.get_symbol_index(s1)
            sym2_idx = self.get_symbol_index(s2)
            sym3_idx = self.get_symbol_index(s3)
            
            # Get actual symbols
            sym1 = self.get_symbol_from_index(sym1_idx)
            sym2 = self.get_symbol_from_index(sym2_idx)
            sym3 = self.get_symbol_from_index(sym3_idx)
            middle_row = f"{sym1} {sym2} {sym3}"
            
            # Calculate win
            win_result = self.calculate_win(sym1_idx, sym2_idx, sym3_idx)
            
            # Process results
            if win_result["win"]:
                winnings = int(bet_amount * win_result["multiplier"])
                self.gambling_cog.update_balance(user_id, winnings)
                result = ('won', winnings)
                win_details = f"{win_result['count']}x {win_result['symbol']} ({win_result['multiplier']}x)"
            else:
                result = ('lost', bet_amount)
                win_details = None
                winnings = 0
            
            new_balance = self.gambling_cog.get_balance(user_id)
            
            # Create result embed
            if result[0] == 'won':
                title = f"🎰 You won {format_currency(winnings)}! 🎰"
                color = discord.Color.green()
            else:
                title = "🎰 Better luck next time! 🎰"
                color = discord.Color.red()
            
            embed = discord.Embed(
                title=title,
                description=f"**{middle_row}**",
                color=color
            )
            
            embed.set_author(name=f"{ctx.author.name}'s Slot Machine", icon_url=ctx.author.display_avatar.url)
            embed.add_field(name="Bet", value=format_currency(bet_amount), inline=True)
            
            # Add win details if available
            if win_details:
                embed.add_field(name="Match", value=win_details, inline=True)
            
            embed.add_field(name="Balance", value=format_currency(new_balance), inline=True)
            embed.set_footer(text="Piglet Casino | Try your luck again with /animated_slots!")
            
            # Send the GIF and embed
            file = discord.File(fp, filename="slots.gif")
            embed.set_image(url=f"attachment://slots.gif")
            
            await ctx.reply(file=file, embed=embed)
            
            # Clean up temp file
            try:
                os.unlink(fp)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in animated slots: {e}")
            await ctx.reply(f"An error occurred: {e}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AnimatedSlots(bot))