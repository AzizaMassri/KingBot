import discord
from discord.ext import commands

class CoreCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["help"])
    async def bothelp(self, ctx, command_name: str = None):
        """Displays the comprehensive bot command guide or specific help for a command."""
        if command_name:
            command_name = command_name.lower().lstrip(ctx.prefix)
            cmd = self.bot.get_command(command_name)
            if not cmd:
                return await ctx.send(f"❌ I don't have a command named `{command_name}`.")
                
            embed = discord.Embed(title=f"Command: !{cmd.name}", description=cmd.help or "No instructions or documentation provided.", color=discord.Color.blue())
            
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
                
            if isinstance(cmd, commands.Group):
                subcmds = [c.name for c in cmd.commands if not c.hidden]
                if subcmds:
                    embed.add_field(name="Subcommands", value=", ".join([f"`{c}`" for c in subcmds]), inline=False)
                    
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="👑 KingBot Complete Command Guide",
            description="Welcome to the **KingBot** documentation!\nThese commands can be used in ANY text channel in the server.",
            color=discord.Color.green()
        )
        
        for cog_name, cog in sorted(self.bot.cogs.items()):
            user_cmds = []
            for cmd in cog.get_commands():
                if cmd.hidden: continue
                # Identify if command is admin-only via its checks
                is_admin = False
                for chk in cmd.checks:
                    if 'has_permissions' in chk.__qualname__ or 'has_guild_permissions' in chk.__qualname__:
                        is_admin = True
                        break
                
                # Check if it's manually disabled in this server
                if ctx.guild:
                    is_disabled = await self.bot.db.get(f"cmd_disabled:{ctx.guild.id}:{cmd.name}")
                    if is_disabled: continue
                    
                if not is_admin:
                    user_cmds.append(cmd)
                    
            if user_cmds:
                # Group them up nicely
                cmd_strings = [f"`!{c.name}`" for c in user_cmds]
                if cmd_strings:
                    embed.add_field(name=f"🟩 {cog_name}", value=" ".join(cmd_strings), inline=False)

        embed.set_footer(text="Type !help <command> for detailed info on a specific tool.")
        
        try:
            user = self.bot.get_user(ctx.author.id) or await self.bot.fetch_user(ctx.author.id)
            await user.send(embed=embed)
            if ctx.guild:
                 await ctx.send(f"✅ {ctx.author.mention}, I've sent you a DM with the detailed KingBot command guide!")
        except Exception:
            await ctx.send(f"⚠️ {ctx.author.mention}, I cannot send you a DM due to your privacy settings. Here is the guide:", embed=embed)

    @commands.hybrid_command(name="adminhelp", aliases=["helpadmin"])
    @commands.has_permissions(administrator=True)
    async def adminhelp(self, ctx):
        """Displays the comprehensive administrative command guide."""
        embed = discord.Embed(
            title="👑 KingBot Administrative Command Guide",
            description="Confidential Settings, Configuration, and Moderation Tools.",
            color=discord.Color.red()
        )
        
        for cog_name, cog in sorted(self.bot.cogs.items()):
            admin_cmds = []
            for cmd in cog.get_commands():
                if cmd.hidden: continue
                is_admin = False
                for chk in cmd.checks:
                    if 'has_permissions' in chk.__qualname__ or 'has_guild_permissions' in chk.__qualname__:
                        is_admin = True
                        break
                        
                if is_admin:
                    admin_cmds.append(cmd)
                    
            if admin_cmds:
                cmd_strings = [f"`!{c.name}`" for c in admin_cmds]
                if cmd_strings:
                    embed.add_field(name=f"🟥 {cog_name}", value=" ".join(cmd_strings), inline=False)
                    
        embed.set_footer(text="Use these tools to configure your server. For standard interactions, view regular !help.")

        try:
            user = self.bot.get_user(ctx.author.id) or await self.bot.fetch_user(ctx.author.id)
            await user.send(embed=embed)
            if ctx.guild:
                 await ctx.send(f"🔐 {ctx.author.mention}, I've sent you a secure DM with the Administrator command rulebook!")
        except Exception:
            await ctx.send(f"⚠️ {ctx.author.mention}, I cannot send you a DM due to your privacy settings. Here is the admin guide:", embed=embed)

    @commands.hybrid_command(name="invite")
    @commands.has_permissions(administrator=True)
    async def get_invite(self, ctx):
        """Generates an invite link for server administrators to add this bot to other servers."""
        client_id = self.bot.user.id
        permissions = discord.Permissions(administrator=True).value
        invite_url = (
            "https://discord.com/api/oauth2/authorize"
            f"?client_id={client_id}&permissions={permissions}&scope=bot%20applications.commands"
        )
        
        embed = discord.Embed(
            title="🔗 Add KingBot to another server!",
            description=(
                f"[Click here to invite me!]({invite_url})\n\n"
                "*Includes bot + slash command scopes. Requires Server Manager / Administrator permissions to add.*"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoreCommands(bot))
