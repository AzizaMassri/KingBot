import discord
from discord.ext import commands, tasks
import time
import math

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
        self.db = bot.db
        self.cooldowns = {}
        self.msg_cooldown = 60 # seconds
        self.vc_xp_loop.start()

    def cog_unload(self):
        self.vc_xp_loop.cancel()

    def _get_level_from_xp(self, xp: int) -> int:
        return int(0.05 * (xp ** 0.5))

    def _get_xp_for_level(self, level: int) -> int:
        if level <= 0: return 0
        return int((float(level) / 0.05) ** 2)

    async def _get_user_color(self, user_id: int) -> discord.Color:
        color_hex = await self.db.get(f"user_color:{user_id}")
        if color_hex:
            try:
                return discord.Color(int(color_hex.strip('#'), 16))
            except:
                return discord.Color.dark_grey()
        return discord.Color.dark_grey()

    async def _process_level_up(self, member: discord.Member, old_level: int, new_level: int):
        if new_level <= old_level:
            return

        # 1.5x Kingshot Bucks from the previous one, starting at 10000 for level 1
        reward = int(10000 * (1.5 ** (new_level - 1)))
        
        current_balance = int(await self.db.get(f"ks_bucks:{member.id}") or 0)
        new_balance = current_balance + reward
        await self.db.set(f"ks_bucks:{member.id}", new_balance)

        embed = discord.Embed(
            title="👑 ROYAL PROMOTION SECURED! 👑",
            description=f"Attention! {member.mention} has been elevated to **Level {new_level}**! 🛡️ For the Kingdom! ⚔️\n\n🏰 **Royal Treasury Deposit:** `{reward:,} Kingshot Bucks` added to your reserves!",
            color=await self._get_user_color(member.id)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        target_channel = None
        saved_channel_id = await self.db.get(f"levelup_channel:{member.guild.id}")
        
        if saved_channel_id:
            target_channel = member.guild.get_channel(int(saved_channel_id))
        
        if target_channel:
            try:
                await target_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @tasks.loop(minutes=1)
    async def vc_xp_loop(self):
        """Grants the highest amount of XP to active Voice Chat sitters."""
        for guild in self.bot.guilds:
            db_key = f"xp_{guild.id}"
            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.bot:
                        continue
                    if member.voice and (member.voice.self_deaf or member.voice.deaf or member.voice.afk):
                        continue
                    
                    # Grant 40 XP per minute in Voice Chat (Very High)
                    granted_xp = 40.0
                    
                    old_xp = int(await self.db.zscore(db_key, str(member.id)) or 0)
                    old_level = self._get_level_from_xp(old_xp)
                    
                    new_xp = await self.db.zincrby(db_key, granted_xp, str(member.id))
                    new_level = self._get_level_from_xp(int(new_xp))

                    await self._process_level_up(member, old_level, new_level)
                    
    @vc_xp_loop.before_loop
    async def before_vc_xp_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        current_time = time.time()
        
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < self.msg_cooldown:
                return
        
        self.cooldowns[user_id] = current_time
        guild_id = message.guild.id
        
        content = message.content.strip()
        length = len(content)
        words = content.split()
        num_words = len(words)
        has_punctuation = any(p in content for p in ".!?")

        # Dynamic XP Calculation
        if length == 0:
            granted_xp = 1.0 # Only attachment/pure empty
        elif length < 10 or num_words < 3:
            granted_xp = 2.0 # Just emoji, gifs, or spam-type
        elif num_words >= 10 and has_punctuation:
            granted_xp = 15.0 # Structured sentences
            if length > 300:
                granted_xp = 25.0 # Max for very long texts
        else:
            granted_xp = 8.0 # Standard short messages

        db_key = f"xp_{guild_id}"
        old_xp = int(await self.db.zscore(db_key, str(user_id)) or 0)
        old_level = self._get_level_from_xp(old_xp)
        
        new_xp = await self.db.zincrby(db_key, granted_xp, str(user_id))
        new_level = self._get_level_from_xp(int(new_xp))

        await self._process_level_up(message.author, old_level, new_level)

    @commands.hybrid_command()
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
        
        filled_blocks = "🟥" * int(bars)
        empty_blocks = "⬛" * int(10 - bars)
        
        progress_bar = f"[{filled_blocks}{empty_blocks}] **{int(progress * 100)}%**"

        embed = discord.Embed(
            title=f"🏰 {member.display_name}'s Royal War Record 🏰",
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

    @commands.hybrid_command()
    async def leaderboard(self, ctx):
        """Displays the top 10 most active members currently in the server."""
        guild_id = ctx.guild.id
        db_key = f"xp_{guild_id}"

        # Fetch all members to filter out users who have left the server
        all_data = await self.db.zrevrange(db_key, 0, -1, withscores=True)
        
        leaderboard_data = []
        for user_id_b, xp in all_data:
            user_id = int(user_id_b)
            member = ctx.guild.get_member(user_id)
            
            if not member:
                try:
                    # In case chunking is off, manually fetch to verify they are still in server
                    member = await ctx.guild.fetch_member(user_id)
                except discord.NotFound:
                    continue
                    
            if member:
                leaderboard_data.append((member, xp))
                if len(leaderboard_data) >= 10:
                    break
        
        if not leaderboard_data:
            return await ctx.send("No one from this server is on the leaderboard yet!")

        embed = discord.Embed(
            title="👑 Royal Kingdom Leaderboard 👑",
            description="The most feared and respected warlords in the kingdom! 🐺\n\n",
            color=discord.Color.dark_red()
        )

        desc = ""
        for index, (member, xp) in enumerate(leaderboard_data):
            name = member.display_name
            level = self._get_level_from_xp(int(xp))
            
            medal = "👑" if index == 0 else "🦁" if index == 1 else "🐺" if index == 2 else "⚔️"
            desc += f"{medal} **#{index + 1}** • **{name}** — **Lv {level}** *( {int(xp):,} Glory )*\n"

        embed.description += desc
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def setcolor(self, ctx, hex_code: str = None):
        """Sets your custom profile embed color (e.g., !setcolor #FF0000)."""
        if not hex_code:
            return await ctx.send("❌ Usage: `!setcolor #HEXCODE` (e.g., `!setcolor #ff0000`)")
        
        if not hex_code.startswith('#'):
            hex_code = f"#{hex_code}"
            
        if len(hex_code) != 7:
            return await ctx.send("❌ Invalid hex code format. Use a 6-character hex like `#FF0000`")

        try:
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

    @commands.hybrid_command(aliases=["setbg", "setbackground"])
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

    @commands.hybrid_command(name="leveling_admin", aliases=["levelingconfig", "setlevelupchannel"])
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

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, member: discord.Member, amount: int):
        """[Admin Only] Instantly grants XP to a user."""
        guild_id = ctx.guild.id
        db_key = f"xp_{guild_id}"
        
        old_xp = int(await self.db.zscore(db_key, str(member.id)) or 0)
        old_level = self._get_level_from_xp(old_xp)
        
        new_xp = await self.db.zincrby(db_key, amount, str(member.id))
        new_level = self._get_level_from_xp(int(new_xp))
        
        await ctx.send(f"✅ Successfully granted **{amount} XP** to {member.mention}.")
        await self._process_level_up(member, old_level, new_level)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
