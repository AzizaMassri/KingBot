import discord
from discord.ext import commands

class BotLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_log_channel(self, guild):
        if not guild:
            return None
        channel_id = await self.db.get(f"botlog_channel:{guild.id}")
        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if not channel:
                channel = self.bot.get_channel(int(channel_id))
            if not channel:
                try:
                    channel = await guild.fetch_channel(int(channel_id))
                except:
                    pass
            return channel
        return None

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel where all bot activity will be logged."""
        if not channel:
            return await ctx.send("❌ Usage: `!setlogchannel #channel`")
            
        await self.db.set(f"botlog_channel:{ctx.guild.id}", channel.id)
        await ctx.send(f"✅ Bot activity logs will now be sent to {channel.mention}.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        from cogs.utils.tiers import PremiumRequiredError, AppPremiumRequiredError, build_premium_embed
        
        # Check against both unwrapped and wrapped CommandInvokeError instances
        original_error = getattr(error, "original", error)

        if isinstance(original_error, (PremiumRequiredError, AppPremiumRequiredError)):
            req_tier = getattr(original_error, 'required_tier', 3)
            try:
                await ctx.send(embed=build_premium_embed(req_tier))
            except:
                pass
            return

        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)

        channel = await self.get_log_channel(ctx.guild)
        if not channel:
            return

        cmd_text = ctx.message.content if ctx.message else f"/{ctx.command.name}"
        embed = discord.Embed(
            title="❌ Command Error",
            description=f"**User**: {ctx.author.mention} (`{ctx.author.id}`)\n**Command**: `{cmd_text}`\n**Error**: {str(error)}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return

        embed = discord.Embed(
            title="👋 Member Joined",
            description=f"{member.mention} (`{member.id}`)\n**Account Created**: <t:{int(member.created_at.timestamp())}:R>",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return

        embed = discord.Embed(
            title="🚪 Member Left",
            description=f"{member.mention} (`{member.id}`)\n**Joined Server**: <t:{int(member.joined_at.timestamp()) if member.joined_at else 0}:R>",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # We need to iterate over guilds to send the startup message since it might be in different guilds
        for guild in self.bot.guilds:
            channel = await self.get_log_channel(guild)
            if not channel:
                continue
                
            embed = discord.Embed(
                title="✅ Bot Restarted",
                description=f"The bot has successfully reconnected to Discord and loaded all modules.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
            try:
                await channel.send(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(BotLogs(bot))
