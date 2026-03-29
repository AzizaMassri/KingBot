import discord
from discord.ext import commands
import time

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_balance(self, user_id):
        balance = await self.db.get(f"ks_bucks:{user_id}")
        return int(balance) if balance else 0

    async def add_balance(self, user_id, amount):
        current = await self.get_balance(user_id)
        new_balance = current + amount
        await self.db.set(f"ks_bucks:{user_id}", new_balance)
        return new_balance

    async def remove_balance(self, user_id, amount):
        current = await self.get_balance(user_id)
        if current >= amount:
            new_balance = current - amount
            await self.db.set(f"ks_bucks:{user_id}", new_balance)
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
        embed.add_field(name="🐻 `!heist <1-5>`", value="Send bear warriors on a medieval raid. Higher difficulty = bigger rewards, but higher risk of failure! Costs Bucks to start.", inline=False)
        embed.add_field(name="🏁 `!race <Animal> <Bet>`", value="Bet Kingshot Bucks on a random animal race. Example: `!race 🐢 100`", inline=False)
        embed.add_field(name="🎲 `!diceduel <@User>`", value="Challenge another member to a Best of 3 dice battle! The winner gets to rename the loser for 48 hours! 🦖", inline=False)
        embed.add_field(name="💰 `!collect`", value="Claim your idle free Kingshot Bucks every 3 hours.", inline=False)
        embed.add_field(name="🏦 `!bank`", value="Check your current Kingshot Bucks balance.", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["bank", "bal"])
    async def balance(self, ctx, member: discord.Member = None):
        """Check your Kingshot Bucks balance!"""
        target = member or ctx.author
        bal = await self.get_balance(target.id)
        
        embed = discord.Embed(title="🏦 Bank of Kingshot", color=discord.Color.green())
        embed.description = f"**{target.display_name}** currently has **{bal}** Kingshot Bucks 💰!"
        await ctx.send(embed=embed)

    @commands.command()
    async def collect(self, ctx):
        """Collect passive Kingshot Bucks every 3 hours."""
        user_id = ctx.author.id
        last_collect_str = await self.db.get(f"last_collect:{user_id}")
        current_time = time.time()
        
        # 3 hours cooldown = 10800 seconds
        cooldown = 10800 
        
        if last_collect_str:
            last_collect = float(last_collect_str)
            if current_time - last_collect < cooldown:
                remaining_time = cooldown - (current_time - last_collect)
                hours, remainder = divmod(int(remaining_time), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ **{ctx.author.display_name}**, the vault is still generating your bucks! Come back in **{hours}h {minutes}m**.")

        # Give between 250 - 500 bucks
        import random
        reward = random.randint(250, 500)
        new_balance = await self.add_balance(user_id, reward)
        
        await self.db.set(f"last_collect:{user_id}", str(current_time))
        
        embed = discord.Embed(
            title="💰 Collection Successful!", 
            description=f"You collected your idle income of **{reward} Kingshot Bucks**!\n\nNew Balance: **{new_balance}** 💰", 
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["addbucks", "givemoney"])
    @commands.has_permissions(administrator=True)
    async def givebucks(self, ctx, member: discord.Member, amount: int):
        """[Admin Only] Give Kingshot Bucks to a user."""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive.")
            
        new_balance = await self.add_balance(member.id, amount)
        embed = discord.Embed(
            title="💸 Funds Transferred",
            description=f"An admin gave **{amount} Kingshot Bucks** to **{member.display_name}**!\nTheir new balance is **{new_balance}** 💰.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        user_id = message.author.id
        current_time = time.time()
        cooldown_key = f"chat_income_cooldown:{user_id}"
        
        last_chat = await self.db.get(cooldown_key)
        
        # 60 second cooldown for chat income
        if not last_chat or current_time - float(last_chat) >= 60:
            import random
            reward = random.randint(1, 10) # 1 to 10 bucks per message
            await self.add_balance(user_id, reward)
            await self.db.set(cooldown_key, str(current_time))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
            
        user_id = member.id
        current_time = time.time()
        join_time_key = f"vc_join_time:{user_id}"
        
        # Joined a VC
        if before.channel is None and after.channel is not None:
            await self.db.set(join_time_key, str(current_time))
            
        # Left a VC
        elif before.channel is not None and after.channel is None:
            join_time_str = await self.db.get(join_time_key)
            if join_time_str:
                join_time = float(join_time_str)
                time_spent = current_time - join_time
                
                # Award 5 bucks per minute spent in VC
                minutes_spent = int(time_spent // 60)
                
                if minutes_spent > 0:
                    reward = minutes_spent * 5
                    await self.add_balance(user_id, reward)
                    
                await self.db.delete(join_time_key)

async def setup(bot):
    await bot.add_cog(Economy(bot))
