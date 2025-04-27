import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
from utils.currency import parse_bet, format_currency
from utils.db_service import get_user_balance, update_user_balance

logger = logging.getLogger(__name__)

# Card suits and values
SUITS = ["♠️", "♥️", "♦️", "♣️"]
VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class BlackjackGame:
    """Class to represent a blackjack game."""
    
    def __init__(self, player_id, bet_amount):
        self.player_id = player_id
        self.bet_amount = bet_amount
        self.player_hand = []
        self.dealer_hand = []
        self.deck = self._create_deck()
        self.status = "active"  # active, player_bust, dealer_bust, player_win, dealer_win, push
        self.message = None  # Store the message for updating
        
        # Deal initial cards
        self.player_hand.append(self._deal_card())
        self.dealer_hand.append(self._deal_card())
        self.player_hand.append(self._deal_card())
        self.dealer_hand.append(self._deal_card())
        
        # Check for player blackjack
        if self.calculate_score(self.player_hand) == 21:
            if self.calculate_score(self.dealer_hand) == 21:
                self.status = "push"  # Both have blackjack, push
            else:
                self.status = "player_blackjack"  # Player has blackjack
    
    def _create_deck(self):
        """Create a new shuffled deck of cards."""
        deck = [f"{v}{s}" for s in SUITS for v in VALUES]
        random.shuffle(deck)
        return deck
    
    def _deal_card(self):
        """Deal a card from the deck."""
        if not self.deck:
            self.deck = self._create_deck()  # Reshuffle if needed
        return self.deck.pop()
    
    def calculate_score(self, hand):
        """Calculate the score of a hand."""
        score = 0
        ace_count = 0
        
        for card in hand:
            value = card[:-2]  # Remove the suit
            if value in ["J", "Q", "K"]:
                score += 10
            elif value == "A":
                score += 11
                ace_count += 1
            else:
                score += int(value)
        
        # Adjust for aces if needed (A can be 1 or 11)
        while score > 21 and ace_count > 0:
            score -= 10
            ace_count -= 1
            
        return score
    
    def player_hit(self):
        """Player takes a hit (draws a card)."""
        self.player_hand.append(self._deal_card())
        score = self.calculate_score(self.player_hand)
        
        if score > 21:
            self.status = "player_bust"
        
        return score
    
    def player_stand(self):
        """Player stands, dealer plays."""
        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand)
        
        # Dealer hits until 17 or higher
        while dealer_score < 17:
            self.dealer_hand.append(self._deal_card())
            dealer_score = self.calculate_score(self.dealer_hand)
        
        if dealer_score > 21:
            self.status = "dealer_bust"
        elif dealer_score > player_score:
            self.status = "dealer_win"
        elif dealer_score < player_score:
            self.status = "player_win"
        else:
            self.status = "push"  # Equal scores
        
        return dealer_score
    
    def get_result(self):
        """Get the final result of the game."""
        if self.status == "player_blackjack":
            return 1.5 * self.bet_amount  # Blackjack pays 3:2
        elif self.status in ["player_win", "dealer_bust"]:
            return self.bet_amount  # Win pays 1:1
        elif self.status == "push":
            return 0  # Push returns the bet
        else:  # dealer_win, player_bust
            return -self.bet_amount  # Lose
    
    def format_hand(self, hand, hide_second=False):
        """Format a hand for display."""
        if hide_second and len(hand) > 1:
            return f"{hand[0]} ??"
        return " ".join(hand)
    
    def create_embed(self, username, avatar_url, hide_dealer=True):
        """Create an embed for the current game state."""
        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand) if not hide_dealer else self.calculate_score([self.dealer_hand[0]])
        
        # Determine display values based on game state
        if self.status == "active":
            title = "🃏 Blackjack Game in Progress"
            color = discord.Color.blue()
            footer = "Hit to draw another card, or Stand to end your turn."
            dealer_display = f"Dealer's Hand: {self.format_hand(self.dealer_hand, hide_dealer)}"
            if hide_dealer:
                dealer_display += f" (Showing: {dealer_score})"
            else:
                dealer_display += f" (Score: {dealer_score})"
        else:
            # Game is over, show full results
            if self.status == "player_blackjack":
                title = "🃏 BLACKJACK! You win 3:2 on your bet!"
                color = discord.Color.gold()
            elif self.status == "player_bust":
                title = "🃏 Bust! You went over 21."
                color = discord.Color.red()
            elif self.status == "dealer_bust":
                title = "🃏 Dealer busts! You win!"
                color = discord.Color.green()
            elif self.status == "player_win":
                title = "🃏 You win!"
                color = discord.Color.green()
            elif self.status == "dealer_win":
                title = "🃏 Dealer wins."
                color = discord.Color.red()
            else:  # push
                title = "🃏 Push! It's a tie."
                color = discord.Color.light_grey()
                
            dealer_display = f"Dealer's Hand: {self.format_hand(self.dealer_hand)} (Score: {self.calculate_score(self.dealer_hand)})"
            footer = "Game over. Use /blackjack to play again!"
        
        embed = discord.Embed(
            title=title,
            color=color
        )
        
        embed.set_author(name=f"{username}'s Blackjack Game", icon_url=avatar_url)
        embed.add_field(name="Your Bet", value=format_currency(self.bet_amount), inline=True)
        
        # Show result if game is over
        if self.status != "active":
            result = self.get_result()
            if result > 0:
                embed.add_field(name="Result", value=f"You won {format_currency(result)}", inline=True)
            elif result < 0:
                embed.add_field(name="Result", value=f"You lost {format_currency(abs(result))}", inline=True)
            else:
                embed.add_field(name="Result", value="Push (bet returned)", inline=True)
        
        embed.add_field(name="\u200b", value="\u200b", inline=False)  # Spacer
        embed.add_field(name=f"Your Hand: {self.format_hand(self.player_hand)} (Score: {player_score})", value="\u200b", inline=False)
        embed.add_field(name=dealer_display, value="\u200b", inline=False)
        embed.set_footer(text=footer)
        
        return embed


class Blackjack(commands.Cog):
    """Blackjack game commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # Store active games by player ID
        logger.info("Blackjack cog initialized")
    
    @app_commands.command(
        name="blackjack", 
        description="Play a game of Blackjack"
    )
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: str):
        """Start a new blackjack game."""
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        # Check if user already has an active game
        if user_id in self.active_games:
            await interaction.response.send_message("You already have an active blackjack game! Finish it before starting a new one.", ephemeral=True)
            return
        
        # Get user balance and parse bet
        balance = get_user_balance(user_id)
        
        try:
            bet_amount = parse_bet(bet, balance)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
            return
        
        # Check if bet is valid
        if bet_amount <= 0:
            await interaction.response.send_message("Bet amount must be greater than 0.", ephemeral=True)
            return
        
        if bet_amount > balance:
            await interaction.response.send_message(f"You don't have enough funds! Your balance is {format_currency(balance)}.", ephemeral=True)
            return
        
        # Create a new blackjack game
        game = BlackjackGame(user_id, bet_amount)
        
        # Deduct bet from balance
        update_user_balance(user_id, username, -bet_amount, "blackjack", "Bet placed")
        
        # Store the game
        self.active_games[user_id] = game
        
        # Create buttons for hit and stand
        view = BlackjackView(self, game)
        
        # Send initial game state
        embed = game.create_embed(interaction.user.name, interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Store the message for updating
        message = await interaction.original_response()
        game.message = message
        
        # Handle immediate blackjack or push
        if game.status != "active":
            result = game.get_result()
            if result >= 0:  # Win or push
                update_user_balance(user_id, username, bet_amount + result, "blackjack", f"Result: {game.status}")
            # Update the message with new embed and remove buttons
            await message.edit(embed=game.create_embed(interaction.user.name, interaction.user.display_avatar.url, hide_dealer=False), view=None)
            # Remove the game
            if user_id in self.active_games:
                del self.active_games[user_id]


class BlackjackView(discord.ui.View):
    """View for blackjack game buttons."""
    
    def __init__(self, cog, game):
        super().__init__(timeout=180)  # 3 minute timeout
        self.cog = cog
        self.game = game
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hit button - draw another card."""
        if str(interaction.user.id) != self.game.player_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
            
        # Player takes a hit
        self.game.player_hit()
        
        # Check if player busted
        if self.game.status == "player_bust":
            # Game over, update message
            await interaction.response.edit_message(
                embed=self.game.create_embed(interaction.user.name, interaction.user.display_avatar.url, hide_dealer=False), 
                view=None
            )
            # Remove the game
            if self.game.player_id in self.cog.active_games:
                del self.cog.active_games[self.game.player_id]
        else:
            # Update the game state
            await interaction.response.edit_message(
                embed=self.game.create_embed(interaction.user.name, interaction.user.display_avatar.url)
            )
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stand button - end turn and let dealer play."""
        if str(interaction.user.id) != self.game.player_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
            
        # Player stands, dealer plays
        self.game.player_stand()
        
        # Game is over, process result
        user_id = self.game.player_id
        username = interaction.user.name
        result = self.game.get_result()
        
        if result >= 0:  # Win or push
            update_user_balance(user_id, username, self.game.bet_amount + result, "blackjack", f"Result: {self.game.status}")
        
        # Update message with final result
        await interaction.response.edit_message(
            embed=self.game.create_embed(interaction.user.name, interaction.user.display_avatar.url, hide_dealer=False),
            view=None
        )
        
        # Remove the game
        if user_id in self.cog.active_games:
            del self.cog.active_games[user_id]
    
    async def on_timeout(self):
        """Handle timeout - automatically stand."""
        if self.game.status == "active" and self.game.message:
            # Player stands, dealer plays
            self.game.player_stand()
            
            # Process result
            user_id = self.game.player_id
            result = self.game.get_result()
            
            # Try to get username from bot's cache
            user = self.cog.bot.get_user(int(user_id))
            username = user.name if user else "Player"
            
            if result >= 0:  # Win or push
                update_user_balance(user_id, username, self.game.bet_amount + result, "blackjack", f"Result: {self.game.status} (timeout)")
            
            # Update message with final result
            try:
                await self.game.message.edit(
                    embed=self.game.create_embed(username, user.display_avatar.url if user else None, hide_dealer=False),
                    view=None
                )
            except:
                logger.error(f"Failed to update blackjack game message on timeout for {user_id}")
            
            # Remove the game
            if user_id in self.cog.active_games:
                del self.cog.active_games[user_id]


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Blackjack(bot))