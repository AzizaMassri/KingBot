import discord
from discord.ext import commands
import time
import random
import asyncio

class TransferBucksModal(discord.ui.Modal, title='Bank Transfer (Admin)'):
    user_id = discord.ui.TextInput(label='Target User ID', placeholder='e.g. 123456789012345678', required=True)
    amount = discord.ui.TextInput(label='Amount of Kingshot Bucks', placeholder='e.g. 500', required=True)
    action_type = discord.ui.TextInput(label='Action (GIVE or TAKE)', placeholder='GIVE or TAKE', required=True, max_length=4)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_id = int(self.user_id.value.strip())
            amt = int(self.amount.value.strip())
            action = self.action_type.value.strip().upper()
        except ValueError:
            return await interaction.response.send_message("❌ Invalid numbers provided.", ephemeral=True)

        if amt <= 0:
            return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            
        target = interaction.guild.get_member(target_id)
        if not target:
            return await interaction.response.send_message("❌ Cannot find that User ID in this server.", ephemeral=True)

        if action == "GIVE":
            current_time = time.time()
            cooldown_key = f"give_bucks_cd:{interaction.user.id}:{target_id}"
            last_give_str = await self.cog.db.get(cooldown_key)
            cooldown = 7200 # 2 hours
            
            if last_give_str:
                last_give = float(last_give_str)
                if current_time - last_give < cooldown:
                    rem = cooldown - (current_time - last_give)
                    h, r = divmod(int(rem), 3600)
                    m, _ = divmod(r, 60)
                    return await interaction.response.send_message(f"⏳ You must wait **{h}h {m}m** before giving bucks to {target.display_name} again!", ephemeral=True)
                    
            new_val = await self.cog.add_balance(target.id, amt)
            await self.cog.db.set(cooldown_key, str(current_time))
            embed = discord.Embed(title="💸 Funds Transferred", description=f"You gave **{amt} 💰** to {target.mention}.\nNew Balance: **{new_val}**.", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
            
        elif action == "TAKE":
            success = await self.cog.remove_balance(target.id, amt)
            current = await self.cog.get_balance(target.id)
            if success:
                embed = discord.Embed(title="💸 Funds Confiscated", description=f"You took **{amt} 💰** from {target.mention}.\nNet Balance: **{current}**.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ {target.display_name} only has {current} Kingshot Bucks! You cannot take {amt}.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Action must be exactly 'GIVE' or 'TAKE'.", ephemeral=True)


class EconomyConfigModal(discord.ui.Modal, title='Economy Base Config'):
    collect_cd_hours = discord.ui.TextInput(label='!collect Cooldown (Hours)', placeholder='e.g. 2', default='2', required=True)

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = float(self.collect_cd_hours.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number provided.", ephemeral=True)
            
        seconds = int(val * 3600)
        await self.cog.db.set(f"config_collect_cd:{self.guild_id}", str(seconds))
        await interaction.response.send_message(f"✅ Users can now `!collect` every **{val} hours**.", ephemeral=True)


class PrinceWilliamConfigModal(discord.ui.Modal, title='Prince William Setup'):
    channel_id = discord.ui.TextInput(label='Drop Channel ID', placeholder='Where he spawns', required=True)
    msg_threshold = discord.ui.TextInput(label='Chat Threshold', placeholder='Messages before spawn (e.g. 500)', required=True)
    cd_hours = discord.ui.TextInput(label='Cooldown Time (Hours)', placeholder='e.g. 6', required=True)
    reward_amount = discord.ui.TextInput(label='Reward Amount', placeholder='e.g. 1500', required=True)

    def __init__(self, cog, guild_id, current_defaults):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        
        # Populate defaults
        self.channel_id.default = current_defaults.get("channel", "")
        self.msg_threshold.default = current_defaults.get("threshold", "500")
        self.cd_hours.default = current_defaults.get("cooldown", "6")
        self.reward_amount.default = current_defaults.get("reward", "1000")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            c_id = int(self.channel_id.value.strip())
            thresh = int(self.msg_threshold.value.strip())
            cd_h = float(self.cd_hours.value.strip())
            rew = int(self.reward_amount.value.strip())
        except Exception:
            return await interaction.response.send_message("❌ Cannot parse inputs. Please use raw numbers.", ephemeral=True)
            
        # Verify channel exists
        ch = interaction.guild.get_channel(c_id)
        if not ch:
            return await interaction.response.send_message("❌ Invalid Channel ID. Ensure the bot has access to it.", ephemeral=True)

        await self.cog.db.hset(f"prince_config:{self.guild_id}", "channel", str(c_id))
        await self.cog.db.hset(f"prince_config:{self.guild_id}", "threshold", str(thresh))
        await self.cog.db.hset(f"prince_config:{self.guild_id}", "cooldown", str(int(cd_h * 3600)))
        await self.cog.db.hset(f"prince_config:{self.guild_id}", "reward", str(rew))
        
        await interaction.response.send_message(f"👑 Prince William is configured! He will spawn in {ch.mention} every `{thresh}` messages (limit: `{cd_h}h` cooldown) dropping `{rew}` Bucks!", ephemeral=True)


class EconomyAdminView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Give/Take Bucks", style=discord.ButtonStyle.primary, emoji="💸")
    async def transfer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TransferBucksModal(self.cog))

    @discord.ui.button(label="Base Timers", style=discord.ButtonStyle.secondary, emoji="⏱️")
    async def timers_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EconomyConfigModal(self.cog, self.guild_id))

    @discord.ui.button(label="Configure Prince William", style=discord.ButtonStyle.success, emoji="👑")
    async def prince_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = await self.cog.db.hgetall(f"prince_config:{self.guild_id}")
        defaults = {}
        if cfg:
            defaults["channel"] = cfg.get("channel", "")
            defaults["threshold"] = cfg.get("threshold", "500")
            # convert back backwards
            cd_sec = int(cfg.get("cooldown", "21600"))
            defaults["cooldown"] = str(cd_sec / 3600)
            defaults["reward"] = cfg.get("reward", "1000")
            
        await interaction.response.send_modal(PrinceWilliamConfigModal(self.cog, self.guild_id, defaults))


class PrinceWilliamDropView(discord.ui.View):
    def __init__(self, cog, reward: int):
        super().__init__(timeout=120.0) # 120 seconds active
        self.cog = cog
        self.reward = reward
        self.claimed_users = set()

    @discord.ui.button(label="Claim Loot!", style=discord.ButtonStyle.success, emoji="💰", custom_id="prince_claim")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.claimed_users:
            return await interaction.response.send_message("❌ **Greedy peasant!** You have already claimed your share!", ephemeral=True)
            
        self.claimed_users.add(interaction.user.id)
        await self.cog.add_balance(interaction.user.id, self.reward)
        await interaction.response.send_message(f"💰 You humbly accepted **{self.reward} Kingshot Bucks** from the Prince!", ephemeral=True)
        
    async def on_timeout(self):
        # Time is up! 
        for child in self.children:
            child.disabled = True
            
        try:
            if self.message:
                await self.message.edit(view=self)
                embed = discord.Embed(
                    title="👑 The Royal Carriage Departs...",
                    description="\"My royal carriage awaits! Spend your loot wisely, peasants—until next time!\"",
                    color=discord.Color.dark_magenta()
                )
                await self.message.reply(embed=embed)
        except Exception: pass


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_balance(self, user_id):
        balance = await self.db.get(f"ks_bucks:{user_id}")
        return int(balance) if balance else 0

    async def add_balance(self, user_id, amount):
        return await self.db.incr(f"ks_bucks:{user_id}", amount)

    async def remove_balance(self, user_id, amount):
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                key = f"ks_bucks:{user_id}"
                val = await conn.fetchval("SELECT value FROM kv WHERE key = $1 FOR UPDATE", key)
                current = int(float(val)) if val else 0
                
                if current >= amount:
                    new_balance = current - amount
                    await conn.execute('''
                        INSERT INTO kv (key, value) VALUES ($1, $2)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    ''', key, str(new_balance))
                    return True
                return False

    @commands.group(invoke_without_command=True, aliases=["minigame"])
    async def minigames(self, ctx):
        """Interactive Kingshot Bucks Minigames!"""
        embed = discord.Embed(
            title="🎮 Kingshot Bucks Minigames 🎮",
            description="Play games to earn **Kingshot Bucks 💰**!\nUse `!` followed by the command below to play.",
            color=discord.Color.gold()
        )
        embed.add_field(name="🐻 `!heist <1-5>`", value="Send bear warriors on a medieval raid. Higher difficulty = bigger rewards!", inline=False)
        embed.add_field(name="🏁 `!race <Animal> <Bet>`", value="Bet Kingshot Bucks on a random animal race. Example: `!race 🐢 100`", inline=False)
        embed.add_field(name="💰 `!collect`", value="Claim your idle free Kingshot Bucks periodically.", inline=False)
        embed.add_field(name="🏦 `!economy` / `!bank`", value="Access the main economy dashboard.", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["bank", "bal"])
    async def economy(self, ctx, member: discord.Member = None):
        """Check your Kingshot Bucks balance and stats!"""
        target = member or ctx.author
        bal = await self.get_balance(target.id)
        
        embed = discord.Embed(title="🏦 Bank of Kingshot", color=discord.Color.green())
        embed.description = f"**{target.display_name}** currently has **{bal}** Kingshot Bucks 💰!\n\nUse `!collect` to claim idle funds."
        await ctx.send(embed=embed)

    @commands.command(name="economy_admin", aliases=["ecoconfig"])
    @commands.has_permissions(administrator=True)
    async def economy_admin(self, ctx):
        """[Admin Only] Central Economy Dashboard."""
        embed = discord.Embed(
            title="👑 Kingdom Financial Dashboard",
            description="Use the buttons below to tweak passive incomes, configure Prince William, and adjust user balances securely.",
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed, view=EconomyAdminView(self, ctx.guild.id))

    @commands.command()
    async def collect(self, ctx):
        """Collect passive Kingshot Bucks."""
        user_id = ctx.author.id
        last_collect_str = await self.db.get(f"last_collect:{user_id}")
        current_time = time.time()
        
        # Check custom cooldown length
        custom_cd = await self.db.get(f"config_collect_cd:{ctx.guild.id}")
        cooldown = int(custom_cd) if custom_cd else 7200 
        
        if last_collect_str:
            last_collect = float(last_collect_str)
            if current_time - last_collect < cooldown:
                remaining_time = cooldown - (current_time - last_collect)
                hours, remainder = divmod(int(remaining_time), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ **{ctx.author.display_name}**, the vault is still generating your bucks! Come back in **{hours}h {minutes}m**.")

        reward = random.randint(250, 500)
        new_balance = await self.add_balance(user_id, reward)
        
        await self.db.set(f"last_collect:{user_id}", str(current_time))
        
        embed = discord.Embed(
            title="💰 Collection Successful!", 
            description=f"You collected your idle income of **{reward} Kingshot Bucks**!\n\nNew Balance: **{new_balance}** 💰", 
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    # Legacy commands strictly wrapping the logic (for backup functionality as requested)
    @commands.command(aliases=["givemoney"])
    @commands.has_permissions(administrator=True)
    async def givebucks(self, ctx, member: discord.Member, amount: int):
        """[Admin Only] Give Kingshot Bucks text-command."""
        if amount <= 0: return await ctx.send("❌ Amount must be positive.")
        current_time = time.time()
        cooldown_key = f"give_bucks_cd:{ctx.author.id}:{member.id}"
        last_give_str = await self.db.get(cooldown_key)
        cooldown = 7200
        if last_give_str and current_time - float(last_give_str) < cooldown:
            rem = cooldown - (current_time - float(last_give_str))
            h, r = divmod(int(rem), 3600)
            m, _ = divmod(r, 60)
            return await ctx.send(f"⏳ You must wait **{h}h {m}m** before giving bucks to {member.display_name} again!")
            
        new_balance = await self.add_balance(member.id, amount)
        await self.db.set(cooldown_key, str(current_time))
        await ctx.send(f"💸 An admin gave **{amount} Kingshot Bucks** to **{member.display_name}**! (New: {new_balance})")

    @commands.command(aliases=["takemoney"])
    @commands.has_permissions(administrator=True)
    async def takebucks(self, ctx, member: discord.Member, amount: int):
        """[Admin Only] Take Kingshot Bucks text-command."""
        if amount <= 0: return await ctx.send("❌ Amount must be positive.")
        success = await self.remove_balance(member.id, amount)
        current = await self.get_balance(member.id)
        if success:
            await ctx.send(f"💸 An admin confiscated **{amount} Kingshot Bucks** from **{member.display_name}**! (Net: {current})")
        else:
            await ctx.send(f"❌ **{member.display_name}** only has {current} Kingshot Bucks! You cannot take {amount}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        guild_id = message.guild.id
        user_id = message.author.id
        current_time = time.time()
        
        # 1. Chat Income Logic
        cooldown_key = f"chat_income_cooldown:{user_id}"
        last_chat = await self.db.get(cooldown_key)
        if not last_chat or current_time - float(last_chat) >= 60:
            reward = random.randint(1, 10)
            await self.add_balance(user_id, reward)
            await self.db.set(cooldown_key, str(current_time))

        # 2. Prince William Event Engine
        cfg = await self.db.hgetall(f"prince_config:{guild_id}")
        if not cfg or not cfg.get("channel"):
            return # Prince William is not configured
            
        channel_id = int(cfg["channel"])
        threshold = int(cfg.get("threshold", 500))
        cooldown = int(cfg.get("cooldown", 21600))
        reward = int(cfg.get("reward", 1000))
        
        # Tick global message tracker safely
        msg_count_key = f"prince_msg_count:{guild_id}"
        new_count = await self.db.incr(msg_count_key, 1)

        if new_count >= threshold:
            # Check drop cooldown to avoid spamming him if they talk too fast
            last_drop = await self.db.get(f"prince_last_drop:{guild_id}")
            if not last_drop or current_time - float(last_drop) >= cooldown:
                # RESET COUNTER TO ZERO AND FIRE THE EVENT!
                await self.db.set(msg_count_key, "0")
                await self.db.set(f"prince_last_drop:{guild_id}", str(current_time))
                
                channel = message.guild.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="👑 ROYAL ARRIVAL 👑",
                        description="\"Greetings peasants! It is I, Prince William! Sponsored strictly by Kingshot - by Century Games! Who here desires fresh loot?!\"",
                        color=discord.Color.gold()
                    )
                    try:
                        view = PrinceWilliamDropView(self, reward)
                        msg = await channel.send(embed=embed, view=view)
                        view.message = msg # Set message reference for later editing
                    except discord.Forbidden:
                        print("Forbidden from writing in Prince William channel!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        user_id = member.id
        current_time = time.time()
        join_time_key = f"vc_join_time:{user_id}"
        
        if before.channel is None and after.channel is not None:
            await self.db.set(join_time_key, str(current_time))
        elif before.channel is not None and after.channel is None:
            join_time_str = await self.db.get(join_time_key)
            if join_time_str:
                time_spent = current_time - float(join_time_str)
                minutes_spent = int(time_spent // 60)
                if minutes_spent > 0:
                    await self.add_balance(user_id, minutes_spent * 5)
                await self.db.delete(join_time_key)

async def setup(bot):
    await bot.add_cog(Economy(bot))
