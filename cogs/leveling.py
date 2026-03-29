import discord
from discord.ext import commands
import time

class LevelUpChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(channel_types=[discord.ChannelType.text], placeholder="Select the Level Up Notification Channel...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = self.values[0]
        await self.bot.db.set(f"levelup_channel:{interaction.guild.id}", channel.id)
        await interaction.followup.send(f"✅ Level Up notifications will now be permanently broadcasted in {channel.mention}.", ephemeral=True)

class LevelUpConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(LevelUpChannelSelect(bot))

    @discord.ui.button(label="Disable Notifications (Clear)", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def clear_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.delete(f"levelup_channel:{interaction.guild.id}")
        await interaction.followup.send("✅ Level Up notifications have been completely disabled.", ephemeral=True)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Using the same database connection from bot.py
        self.db = bot.db
        self.cooldowns = {}
        self.points_per_msg = 5
        self.msg_cooldown = 60 # seconds

    def _get_level_from_xp(self, xp: int) -> int:
        return int(0.1 * (xp ** 0.5))

    def _get_xp_for_level(self, level: int) -> int:
        if level == 0: return 0
        return int((float(level) / 0.1) ** 2)

    async def _get_user_color(self, user_id: int) -> discord.Color:
        color_hex = await self.db.get(f"user_color:{user_id}")
        if color_hex:
            try:
                return discord.Color(int(color_hex.strip('#'), 16))
            except:
                return discord.Color.dark_grey()
        return discord.Color.dark_grey()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        current_time = time.time()
        
        # Check Cooldown
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < self.msg_cooldown:
                return
        
        self.cooldowns[user_id] = current_time

        # XP Multiplier Logic (March 8, 2026 -> March 15, 2026)
        # Exactly 7 days from right now in Unix seconds
        seven_days_from_now = 1773611390
        
        # Base Points
        granted_xp = float(self.points_per_msg)
        
        if current_time < seven_days_from_now:
            granted_xp *= 5.0 # 5x Faster
        else:
            granted_xp *= 2.5 # 2.5x Faster
            
        guild_id = message.guild.id
        db_key = f"xp_{guild_id}"
        
        old_xp = int(await self.db.zscore(db_key, str(user_id)) or 0)
        old_level = self._get_level_from_xp(old_xp)
        
        new_xp = await self.db.zincrby(db_key, granted_xp, str(user_id))
        new_level = self._get_level_from_xp(int(new_xp))

        # Check for Level Up
        if new_level > old_level:
            reward = 1000 + (new_level - 1) * 100
            current_balance = int(await self.db.get(f"ks_bucks:{user_id}") or 0)
            new_balance = current_balance + reward
            await self.db.set(f"ks_bucks:{user_id}", new_balance)
            
            embed = discord.Embed(
                title="👑 ROYAL PROMOTION SECURED! 👑",
                description=f"Attention! {message.author.mention} has been elevated to **Level {new_level}**! 🛡️ For the Kingdom! ⚔️\n\n🏰 **Royal Treasury Deposit:** `{reward} Kingshot Bucks` added to your reserves!",
                color=await self._get_user_color(user_id)
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            # Check if an admin set a specific Level-Up announcement channel
            target_channel = None
            saved_channel_id = await self.db.get(f"levelup_channel:{guild_id}")
            
            if saved_channel_id:
                target_channel = message.guild.get_channel(int(saved_channel_id))
            
            if target_channel:
                try:
                    await target_channel.send(embed=embed)
                except discord.Forbidden:
                    pass


    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        """Displays your current rank, level, and XP."""
        member = member or ctx.author
        guild_id = ctx.guild.id
        db_key = f"xp_{guild_id}"

        xp = int(await self.db.zscore(db_key, str(member.id)) or 0)
        level = self._get_level_from_xp(xp)
        rank = await self.db.zrevrank(db_key, str(member.id))
        rank_str = f"#{rank + 1}" if rank is not None else "Unranked"

        # Calculate progress
        current_level_xp = self._get_xp_for_level(level)
        next_level_xp = self._get_xp_for_level(level + 1)
        xp_needed = next_level_xp - current_level_xp
        xp_gained = xp - current_level_xp
        
        progress = xp_gained / xp_needed if xp_needed > 0 else 0
        bars = int(progress * 10)
        
        military_ranks = ["Squire", "Man-at-Arms", "Knight", "Captain", "Lord", "Baron", "Duke", "King"]
        title_rank = military_ranks[min(level // 5, len(military_ranks)-1)]

        bars = int(progress * 10)
        
        # War themed progress bar
        filled_blocks = "🟥" * int(bars)
        empty_blocks = "⬛" * int(10 - bars)
        
        progress_bar = f"[{filled_blocks}{empty_blocks}] **{int(progress * 100)}%**"

        embed = discord.Embed(
            title=f"🏰 {member.name}'s Royal War Record 🏰",
            color=await self._get_user_color(member.id)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        bg_url = await self.db.get(f"user_bg:{member.id}")
        if bg_url:
            embed.set_image(url=bg_url)
        embed.add_field(name="👑 Royal Title", value=f"**{title_rank}**", inline=True)
        embed.add_field(name="⚔️ War Level", value=f"**{level}**", inline=True)
        embed.add_field(name="🛡️ Kingdom Rank", value=f"**{rank_str}**", inline=True)
        embed.add_field(name="🔥 Total Glory", value=f"**{xp:,}**", inline=True)
        embed.add_field(name=f"⚔️ Next Rank (Lv. {level+1})", value=f"**{xp_gained:,} / {xp_needed:,} Glory**\n{progress_bar}", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx):
        """Displays the top 10 most active members."""
        guild_id = ctx.guild.id
        db_key = f"xp_{guild_id}"

        leaderboard_data = await self.db.zrevrange(db_key, 0, 9, withscores=True)
        
        if not leaderboard_data:
            return await ctx.send("No one is on the leaderboard yet!")

        embed = discord.Embed(
            title="👑 Royal Kingdom Leaderboard 👑",
            description="The most feared and respected warlords in the kingdom! 🐺\n\n",
            color=discord.Color.dark_red()
        )

        desc = ""
        for index, (user_id_b, xp) in enumerate(leaderboard_data):
            user_id = int(user_id_b)
            member = ctx.guild.get_member(user_id)
            name = member.name if member else f"Unknown Warrior ({user_id})"
            level = self._get_level_from_xp(int(xp))
            
            medal = "👑" if index == 0 else "🦁" if index == 1 else "🐺" if index == 2 else "⚔️"
            desc += f"{medal} **#{index + 1}** • **{name}** — **Lv {level}** *( {int(xp):,} Glory )*\n"

        embed.description += desc
        await ctx.send(embed=embed)

    @commands.command()
    async def setcolor(self, ctx, hex_code: str = None):
        """Sets your custom profile embed color (e.g., !setcolor #FF0000)."""
        if not hex_code:
            return await ctx.send("❌ Usage: `!setcolor #HEXCODE` (e.g., `!setcolor #ff0000`)")
        
        if not hex_code.startswith('#'):
            hex_code = f"#{hex_code}"
            
        if len(hex_code) != 7:
            return await ctx.send("❌ Invalid hex code format. Use a 6-character hex like `#FF0000`")

        try:
            # Validate hex
            int(hex_code.strip('#'), 16)
        except ValueError:
            return await ctx.send("❌ Invalid hex code format.")

        await self.db.set(f"user_color:{ctx.author.id}", hex_code)
        
        embed = discord.Embed(
            title="War Colors Applied!",
            description=f"Your profile color is now set to **{hex_code}**.",
            color=discord.Color(int(hex_code.strip('#'), 16))
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["setbg", "setbackground"])
    async def setimage(self, ctx, url: str = None):
        """Sets a custom background image for your !rank card."""
        if not url:
            return await ctx.send("❌ Usage: `!setimage <image_url>`\nExample: `!setimage https://example.com/image.png`")
            
        if not (url.startswith('http://') or url.startswith('https://')):
            return await ctx.send("❌ Invalid URL format! Ensure it starts with `http://` or `https://`.")
        
        embed = discord.Embed(
            title="Background Updated!",
            description="Your `!rank` profile background has been updated.",
            color=discord.Color.dark_grey()
        )
        try:
            embed.set_image(url=url)
            await ctx.send(embed=embed)
            await self.db.set(f"user_bg:{ctx.author.id}", url)
        except Exception:
            await ctx.send("❌ Discord could not load that image URL. Please try a different direct link.")

    @commands.command(name="leveling_admin", aliases=["levelingconfig", "setlevelupchannel"])
    @commands.has_permissions(administrator=True)
    async def leveling_admin(self, ctx):
        """[Admin Only] Interactive Dashboard to configure Level Up notifications."""
        saved_channel_id = await self.db.get(f"levelup_channel:{ctx.guild.id}")
        status = f"<#{saved_channel_id}>" if saved_channel_id else "Disabled"
        
        embed = discord.Embed(
            title="⚔️ Leveling System Configurator",
            description=f"Configure where Royal Promotion (Level Up) broadcasts occur.\n\n**Current Setup:** {status}\n\nUse the dropdown below to assign a specific channel, or click the ❌ button to completely disable global broadcasts.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=LevelUpConfigView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, member: discord.Member, amount: int):
        """[Admin Only] Instantly grants XP to a user, bypassing cooldowns."""
        guild_id = ctx.guild.id
        db_key = f"xp_{guild_id}"
        
        # Calculate old level for potential level up notification
        old_xp = int(await self.db.zscore(db_key, str(member.id)) or 0)
        old_level = self._get_level_from_xp(old_xp)
        
        new_xp = await self.db.zincrby(db_key, amount, str(member.id))
        new_level = self._get_level_from_xp(int(new_xp))
        
        await ctx.send(f"✅ Successfully granted **{amount} XP** to {member.mention}.")
        
        # Check for Level Up
        if new_level > old_level:
            reward = 1000 + (new_level - 1) * 100
            current_balance = int(await self.db.get(f"ks_bucks:{member.id}") or 0)
            new_balance = current_balance + reward
            await self.db.set(f"ks_bucks:{member.id}", new_balance)
            
            embed = discord.Embed(
                title="🎖️ PROMOTION SECURED! 🎖️",
                description=f"Attention! {member.mention} has advanced to **Level {new_level}**! 🫡 Keep pushing forward! ⚔️\n\n🏦 **War Chest Deposit:** `{reward} Kingshot Bucks` added to your reserves!",
                color=await self._get_user_color(member.id)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            target_channel = None
            saved_channel_id = await self.db.get(f"levelup_channel:{guild_id}")
            
            if saved_channel_id:
                target_channel = ctx.guild.get_channel(int(saved_channel_id))
            
            if target_channel:
                try:
                    await target_channel.send(embed=embed)
                except discord.Forbidden:
                    pass


async def setup(bot):
    await bot.add_cog(Leveling(bot))
