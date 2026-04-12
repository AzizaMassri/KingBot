import discord
from discord.ext import commands
import random
from cogs.economy import Economy
from cogs.utils.views import TranslatedView

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @property
    def eco(self):
        return self.bot.get_cog("Economy")

    @commands.hybrid_group(invoke_without_command=True, aliases=["bet"])
    async def casino(self, ctx):
        """Play Casino games for Kingshot Bucks!"""
        embed = discord.Embed(
            title="🎰 Kingshot Casino 🎰",
            description="Welcome to the Casino! Gamble your Kingshot Bucks here.",
            color=discord.Color.gold()
        )
        embed.add_field(name="🃏 `!bj <bet>`", value="Play a hand of Blackjack against the dealer!", inline=False)
        embed.add_field(name="🪙 `!coinflip <heads/tails> <bet>`", value="Double your money with a 50/50 chance!", inline=False)
        embed.add_field(name="🎲 `!roll <bet>`", value="Roll a 100-sided die. Roll > 66 to win 2x, > 90 to win 3x, 100 to win 10x!", inline=False)
        embed.add_field(name="🎰 `!slots <bet>`", value="Spin the slot machine! Match 2 for 2x, Match 3 for 5x, Match 3 🍒 for 10x!", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["cf"])
    async def coinflip(self, ctx, choice: str = None, bet: str = "0"):
        """Flip a coin! Example: `!coinflip heads 100`"""
        try:
            bet = int(bet)
        except ValueError:
            return await ctx.send("❌ Please provide a valid number for your bet.")
            
        if not choice or bet <= 0:
            return await ctx.send("❌ Usage: `!coinflip <heads/tails> <amount>`")
            
        choice = choice.lower()
        if choice not in ["heads", "tails", "h", "t"]:
            return await ctx.send("❌ You must pick `heads` or `tails`.")
            
        if choice == "h": choice = "heads"
        if choice == "t": choice = "tails"
            
        user_id = ctx.author.id
        if await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to make that bet!")
            
        await self.eco.remove_balance(user_id, bet)
        
        result = random.choice(["heads", "tails"])
        
        if choice == result:
            winnings = bet * 2
            new_bal = await self.eco.add_balance(user_id, winnings)
            embed = discord.Embed(
                title="🪙 Coin Flip: WIN!",
                description=f"The coin landed on **{result.upper()}**!\n\nYou won **{winnings} 💰**!\nNew Balance: **{new_bal} 💰**",
                color=discord.Color.green()
            )
        else:
            remaining_bal = await self.eco.get_balance(user_id)
            embed = discord.Embed(
                title="🪙 Coin Flip: LOSS!",
                description=f"The coin landed on **{result.upper()}**!\n\nYou lost your bet of **{bet} 💰**.\nRemaining Balance: **{remaining_bal} 💰**",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["bj", "21"])
    async def blackjack(self, ctx, bet: str = "0"):
        """Play Blackjack against the dealer! Example: `!bj 100`"""
        try:
            bet = int(bet)
        except ValueError:
            return await ctx.send("❌ Please provide a valid number for your bet.")
            
        if bet <= 0:
            return await ctx.send("❌ Usage: `!bj <amount>`")
            
        user_id = ctx.author.id
        if await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to make that bet!")
            
        await self.eco.remove_balance(user_id, bet)
        
        view = BlackjackView(ctx, bet, self.eco)
        embed = await view.generate_embed()
        
        msg = await ctx.send(embed=embed, view=view)
        
        # Check for immediate natural blackjack
        if await view.check_blackjack(msg):
            return

    @commands.hybrid_command()
    async def roll(self, ctx, bet: str = "0"):
        """Roll a 100-sided die! Example: `!roll 100`"""
        try:
            bet = int(bet)
        except ValueError:
            return await ctx.send("❌ Please provide a valid number for your bet.")
            
        if bet <= 0:
            return await ctx.send("❌ Usage: `!roll <amount>`")
            
        user_id = ctx.author.id
        if await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to make that bet!")
            
        await self.eco.remove_balance(user_id, bet)
        
        roll_num = random.randint(1, 100)
        
        multiplier = 0
        if roll_num == 100:
            multiplier = 10
        elif roll_num >= 90:
            multiplier = 3
        elif roll_num >= 66:
            multiplier = 2
            
        if multiplier > 0:
            winnings = bet * multiplier
            new_bal = await self.eco.add_balance(user_id, winnings)
            embed = discord.Embed(
                title=f"🎲 Rolled a {roll_num}! WIN!",
                description=f"You won **{multiplier}x** your bet!\n\nPayout: **{winnings} 💰**\nNew Balance: **{new_bal} 💰**",
                color=discord.Color.green()
            )
        else:
            remaining_bal = await self.eco.get_balance(user_id)
            embed = discord.Embed(
                title=f"🎲 Rolled a {roll_num}! LOSS!",
                description=f"You needed a 66 or higher to win.\n\nYou lost your bet of **{bet} 💰**.\nRemaining Balance: **{remaining_bal} 💰**",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["slotmachine"])
    async def slots(self, ctx, bet: str = "0"):
        """Spin the slots! Example: `!slots 100`"""
        try:
            bet = int(bet)
        except ValueError:
            return await ctx.send("❌ Please provide a valid number for your bet.")
            
        if bet <= 0:
            return await ctx.send("❌ Usage: `!slots <amount>`")
            
        user_id = ctx.author.id
        if await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to make that bet!")
            
        await self.eco.remove_balance(user_id, bet)
        
        # Initial spinning message
        spin_embed = discord.Embed(
            title="🎰 Spinning... 🎰",
            description="**[ ⏳ | ⏳ | ⏳ ]**\n\n*Rolling the reels...*",
            color=discord.Color.gold()
        )
        msg = await ctx.send(embed=spin_embed)
        
        import asyncio
        await asyncio.sleep(1.5)
        
        symbols = ["🍒", "🍋", "🍇", "🔔", "💎", "⭐", "7️⃣"]
        weights = [25, 20, 20, 15, 10, 8, 2] # 🍒 is most common, 7️⃣ is rarest
        
        results = random.choices(symbols, weights=weights, k=3)
        
        matches = len(set(results))
        
        multiplier = 0
        winnings_text = ""
        
        if matches == 1: # All 3 match
            if results[0] == "7️⃣":
                multiplier = 50
                winnings_text = "JACKPOT!!! 50x PAYOUT!"
            elif results[0] == "⭐" or results[0] == "💎":
                multiplier = 20
                winnings_text = "MEGA WIN! 20x PAYOUT!"
            elif results[0] == "🍒":
                multiplier = 10
                winnings_text = "CHERRY BOMB! 10x PAYOUT!"
            else:
                multiplier = 5
                winnings_text = "TRIPLE MATCH! 5x PAYOUT!"
        elif matches == 2: # 2 match
            multiplier = 2
            winnings_text = "DOUBLE MATCH! 2x PAYOUT!"
            
        if multiplier > 0:
            winnings = bet * multiplier
            new_bal = await self.eco.add_balance(user_id, winnings)
            color = discord.Color.green()
            desc = f"**[ {results[0]} | {results[1]} | {results[2]} ]**\n\n{winnings_text}\nYou won **{winnings} 💰**!\nNew Balance: **{new_bal} 💰**"
            title = "🎰 Slots: WIN! 🎰"
        else:
            color = discord.Color.red()
            remaining_bal = await self.eco.get_balance(user_id)
            desc = f"**[ {results[0]} | {results[1]} | {results[2]} ]**\n\nNo matches!\nYou lost your bet of **{bet} 💰**.\nRemaining Balance: **{remaining_bal} 💰**"
            title = "🎰 Slots: LOSS 🎰"
            
        embed = discord.Embed(title=title, description=desc, color=color)
        await msg.edit(embed=embed)

class BlackjackView(TranslatedView):
    def __init__(self, ctx, bet: int, eco):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.bet = bet
        self.eco = eco
        self.deck = self._build_deck()
        self.player_hand = [self._draw(), self._draw()]
        self.dealer_hand = [self._draw(), self._draw()]

    def _build_deck(self):
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
        random.shuffle(deck)
        return deck

    def _draw(self):
        return self.deck.pop()

    def _calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            r = card['rank']
            if r in ['J', 'Q', 'K']:
                score += 10
            elif r == 'A':
                aces += 1
                score += 11
            else:
                score += int(r)
        
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
            
        return score

    def _format_hand(self, hand, hide_second=False):
        if hide_second and len(hand) > 1:
            return f"[{hand[0]['rank']}{hand[0]['suit']}] [❓❓]"
        return " ".join([f"[{c['rank']}{c['suit']}]" for c in hand])

    async def generate_embed(self, game_over=False, player_won=False, draw=False, blackjack=False):
        p_score = self._calculate_score(self.player_hand)
        d_score = self._calculate_score(self.dealer_hand)
        
        desc = ""
        color = discord.Color.gold()
        title = "🃏 Blackjack"
        
        if not game_over:
            desc = f"**{self.ctx.author.display_name}'s Hand** (Score: {p_score})\n{self._format_hand(self.player_hand)}\n\n**Dealer's Hand**\n{self._format_hand(self.dealer_hand, True)}"
        else:
            if draw:
                title = "🃏 Blackjack: PUSH (Tie)"
                desc = f"You tied with the dealer. Bet refunded.\n\n"
                color = discord.Color.light_grey()
                await self.eco.add_balance(self.ctx.author.id, self.bet) # Refund
            elif player_won:
                winnings = self.bet * (2.5 if blackjack else 2) 
                new_bal = await self.eco.add_balance(self.ctx.author.id, int(winnings))
                title = "🃏 Blackjack: YOU WIN!"
                desc = f"{'**BLACKJACK!** ' if blackjack else ''}You won **{int(winnings)} 💰**!\nNew Balance: **{new_bal} 💰**\n\n"
                color = discord.Color.green()
            else:
                remaining_bal = await self.eco.get_balance(self.ctx.author.id)
                title = "🃏 Blackjack: YOU LOSE!"
                desc = f"You lost your bet of **{self.bet} 💰**.\nRemaining Balance: **{remaining_bal} 💰**\n\n"
                color = discord.Color.red()
                
            desc += f"**{self.ctx.author.display_name}'s Hand** (Score: {p_score})\n{self._format_hand(self.player_hand)}\n\n"
            desc += f"**Dealer's Hand** (Score: {d_score})\n{self._format_hand(self.dealer_hand)}"
            
        embed = discord.Embed(title=title, description=desc, color=color)
        return embed

    async def check_blackjack(self, interaction):
        p_score = self._calculate_score(self.player_hand)
        d_score = self._calculate_score(self.dealer_hand)
        
        if p_score == 21 and d_score == 21:
            self.stop()
            self.clear_items()
            embed = await self.generate_embed(game_over=True, draw=True)
            if isinstance(interaction, discord.Interaction):
                await self.edit_translated(interaction, embed=embed, view=self)
            else:
                await interaction.edit(embed=embed, view=self)
            return True
        elif p_score == 21:
            self.stop()
            self.clear_items()
            embed = await self.generate_embed(game_over=True, player_won=True, blackjack=True)
            if isinstance(interaction, discord.Interaction):
                await self.edit_translated(interaction, embed=embed, view=self)
            else:
                await interaction.edit(embed=embed, view=self)
            return True
        elif d_score == 21:
            self.stop()
            self.clear_items()
            embed = await self.generate_embed(game_over=True, player_won=False)
            if isinstance(interaction, discord.Interaction):
                await self.edit_translated(interaction, embed=embed, view=self)
            else:
                await interaction.edit(embed=embed, view=self)
            return True
            
        return False

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, custom_id="hit")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await self.send_translated(interaction, content="This isn't your game!", ephemeral=True)
            
        self.player_hand.append(self._draw())
        p_score = self._calculate_score(self.player_hand)
        
        if p_score > 21:
            self.stop()
            self.clear_items()
            embed = await self.generate_embed(game_over=True, player_won=False)
            await self.edit_translated(interaction, embed=embed)
        elif p_score == 21:
            await self.stand_button.callback(interaction) # Auto stand on 21
        else:
            embed = await self.generate_embed()
            await self.edit_translated(interaction, embed=embed)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger, custom_id="stand")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await self.send_translated(interaction, content="This isn't your game!", ephemeral=True)
            
        self.stop()
        self.clear_items()
        
        # Dealer plays
        while self._calculate_score(self.dealer_hand) < 17:
             self.dealer_hand.append(self._draw())
             
        p_score = self._calculate_score(self.player_hand)
        d_score = self._calculate_score(self.dealer_hand)
        
        if d_score > 21 or p_score > d_score:
            embed = await self.generate_embed(game_over=True, player_won=True)
            await self.edit_translated(interaction, embed=embed)
        elif p_score < d_score:
            embed = await self.generate_embed(game_over=True, player_won=False)
            await self.edit_translated(interaction, embed=embed)
        else:
            embed = await self.generate_embed(game_over=True, draw=True)
            await self.edit_translated(interaction, embed=embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))
