import discord
from discord.ext import commands, tasks
import random
import json
import os
from datetime import datetime, timedelta, timezone
from cogs.utils.views import TranslatedView, TranslatedModal

class RenameModal(TranslatedModal, title='Claim Your Prize: Rename the Loser!'):
    new_name = discord.ui.TextInput(
        label='New Kingshot Name',
        placeholder='e.g., The Noob, Bot Fodder',
        min_length=1,
        max_length=32,
    )

    def __init__(self, winner: discord.Member, loser: discord.Member):
        super().__init__()
        self.winner = winner
        self.loser = loser

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        roles = [r.name.upper() for r in self.loser.roles]
        proposed_name = self.new_name.value.strip()
        
        # Enforce R4/R5 rule: Name must be similar to original
        if "R4" in roles or "R5" in roles:
            # Appending the funny name to their actual name to keep leadership recognizable
            final_name = f"{self.loser.display_name} ({proposed_name})"[:32]
        else:
            final_name = proposed_name

        original_name = self.loser.display_name
        
        try:
            await self.loser.edit(nick=final_name)
            
            # Calculate expiration: 2 days from now, specifically at 0 UTC
            exp_date = datetime.now(timezone.utc) + timedelta(days=2)
            exp_date = exp_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            payload = {
                "guild_id": self.loser.guild.id,
                "original_name": original_name,
                "expires_at": exp_date.timestamp()
            }
            # Save persistently inside Postgres asynchronously, preventing Event Loop Blocking!
            await self.loser.client.db.set(f"kingshot_loser:{self.loser.id}", json.dumps(payload))

            await self.send_translated(interaction, content=f"🌋 **NAME CHANGE APPLIED!** 🌋\n{self.loser.mention} is now known as **{final_name}** until {exp_date.strftime('%Y-%m-%d 00:00 UTC')}.")
            
        except discord.Forbidden:
            await self.send_translated(interaction, content=f"❌ I lack the permissions to rename {self.loser.mention}. Make sure my bot role is higher than theirs in the server settings!", ephemeral=True)

class DuelAcceptView(TranslatedView):
    def __init__(self, challenger: discord.Member, challenged: discord.Member):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.challenged = challenged

    @discord.ui.button(label="Accept Duel", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged.id:
            await self.send_translated(interaction, content="This duel isn't for you!", ephemeral=True)
            return

        await interaction.response.defer()
        self.stop()
        await self.process_duel(interaction)

    async def process_duel(self, interaction: discord.Interaction):
        c_wins = 0
        t_wins = 0
        log = []

        # Best of 3 rolls
        for round_num in range(1, 4):
            c_roll = sum(random.randint(1, 6) for _ in range(3))
            t_roll = sum(random.randint(1, 6) for _ in range(3))
            
            if c_roll > t_roll:
                c_wins += 1
                winner = self.challenger.display_name
            elif t_roll > c_roll:
                t_wins += 1
                winner = self.challenged.display_name
            else:
                winner = "Tie"

            log.append(f"**Round {round_num}:** {self.challenger.display_name} ({c_roll}) vs {self.challenged.display_name} ({t_roll}) - *{winner} wins round*")

            if c_wins == 2 or t_wins == 2:
                break # Someone won best of 3 early

        if c_wins > t_wins:
            match_winner, match_loser = self.challenger, self.challenged
        elif t_wins > c_wins:
            match_winner, match_loser = self.challenged, self.challenger
        else:
            await self.send_translated(interaction, content="\n".join(log) + "\n\n**It's a dead tie! Both players survive today.**")
            return

        result_msg = "\n".join(log) + f"\n\n👑 **{match_winner.mention} WINS THE DUEL!** 👑\n{match_loser.mention}, prepare to be renamed!"
        
        # View for the winner to claim the prize
        class RenameView(TranslatedView):
            @discord.ui.button(label="Rename Loser", style=discord.ButtonStyle.danger, emoji="🎲")
            async def rename_btn(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != match_winner.id:
                    await self.send_translated(btn_interaction, content="Only the winner gets to pick the name!", ephemeral=True)
                    return
                await btn_interaction.response.send_modal(RenameModal(match_winner, match_loser))
                self.stop()

        await self.send_translated(interaction, content=result_msg, view=RenameView())

class DiceGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nickname_reverter.start()

    def cog_unload(self):
        self.nickname_reverter.cancel()

    @commands.hybrid_command(name="diceduel", description="Challenge a fellow member to a dice duel for renaming rights!")
    async def diceduel(self, ctx, opponent: discord.Member):
        if opponent.bot:
            await ctx.send("You can't duel a bot! We have silicon hides.")
            return
        if opponent == ctx.author:
            await ctx.send("You can't duel yourself. Get back in the game!")
            return

        embed = discord.Embed(
            title="🎲 Kingshot ᴅɪᴄᴇ ᴅᴜᴇʟ 🎲",
            description=f"{ctx.author.mention} has challenged {opponent.mention}!\n\n**Rules:** Both roll 3 dice. Best of 3 rolls wins!\n**Stakes:** Loser is renamed by the winner for 2 days (resets 0 UTC).\n*(Funny & Kind... no meanie weenies!!!)*",
            color=discord.Color.red()
        )
        await ctx.send(content=opponent.mention, embed=embed, view=DuelAcceptView(ctx.author, opponent))

    @tasks.loop(minutes=30)
    async def nickname_reverter(self):
        """Background task to check for expired nicknames natively using the Database Cache."""
        now = datetime.now(timezone.utc).timestamp()
        
        try:
            keys = await self.bot.db.keys("kingshot_loser:*")
            if not keys: return
            
            for key in keys:
                data_str = await self.bot.db.get(key)
                if not data_str: continue
                
                data = json.loads(data_str)
                if now >= data["expires_at"]:
                    guild = self.bot.get_guild(data["guild_id"])
                    if guild:
                        user_id = int(key.split(":")[1])
                        member = guild.get_member(user_id)
                        if member:
                            try:
                                await member.edit(nick=data["original_name"])
                                print(f"Reverted nickname for {member.display_name}")
                            except discord.Forbidden:
                                print(f"Failed to revert nickname for {user_id}: Missing permissions.")
                    
                    # Delete record entirely after reverting
                    await self.bot.db.delete(key)
        except Exception as e:
            print(f"Dice Game DB Loop Error: {e}")

    @nickname_reverter.before_loop
    async def before_reverter(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DiceGame(bot))
