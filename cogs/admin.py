import discord
from discord.ext import commands
import sys
import os
from cogs.utils.views import TranslatedView

class AdminConfirmView(TranslatedView):
    def __init__(self, ctx, action_name: str, callback_coro):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.action_name = action_name
        self.callback_coro = callback_coro

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await self.send_translated(interaction, content="You cannot confirm this action.", ephemeral=True)
        
        for child in self.children:
            child.disabled = True
        
        try:
            await interaction.message.edit(content=f"Confirmed {self.action_name}.", view=self)
        except discord.HTTPException:
            pass
            
        self.stop()
        await self.callback_coro()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await self.send_translated(interaction, content="You cannot cancel this action.", ephemeral=True)
        
        for child in self.children:
            child.disabled = True
        
        try:
            await interaction.message.edit(content=f"Cancelled {self.action_name}.", view=self)
        except discord.HTTPException:
            pass
            
        self.stop()

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="restart", aliases=["reboot"])
    @commands.has_permissions(administrator=True)
    async def restart_bot(self, ctx):
        """Restarts the bot. Works best if run through a process manager like Docker."""
        async def do_restart():
            await ctx.send("🔄 Restarting bot...")
            sys.exit(0)
            
        view = AdminConfirmView(ctx, "bot restart", do_restart)
        await ctx.send("Are you sure you want to restart the bot?", view=view)

    @commands.command(name="reload")
    @commands.has_permissions(administrator=True)
    async def reload_cog(self, ctx, extension: str):
        """Reloads a specific cog without fully restarting the bot."""
        async def do_reload():
            try:
                await self.bot.reload_extension(f"cogs.{extension}")
                await ctx.send(f"✅ Successfully reloaded `cogs.{extension}`")
            except Exception as e:
                await ctx.send(f"❌ Failed to reload `cogs.{extension}`: {e}")
                
        view = AdminConfirmView(ctx, f"reload of cogs.{extension}", do_reload)
        await ctx.send(f"Are you sure you want to reload `cogs.{extension}`?", view=view)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        """Syncs slash and context menu commands instantly to this server."""
        # Force sync to the current guild to bypass the 1-hour global cache delay
        synced = await self.bot.tree.sync(guild=ctx.guild)
        self.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Fast-Synced **{len(synced)}** app commands specifically to `{ctx.guild.name}`. (Refresh your Discord client via Ctrl+R if you still don't see them!)")

    @commands.command(name="toggle_command", aliases=["toggle"])
    @commands.has_permissions(administrator=True)
    async def toggle_command(self, ctx, command_name: str = None):
        """Toggles any bot command to be Admin-only. Type '!toggle list' to see all disabled commands."""
        if not command_name:
            return await ctx.send("❌ Usage: `!toggle <CommandName>` or `!toggle list`.")
            
        if command_name.lower() == "list":
            # List all disabled commands
            pattern = f"cmd_disabled:{ctx.guild.id}:*"
            keys = await self.bot.db.keys(pattern)
            if not keys:
                return await ctx.send("✅ There are currently no commands/cogs disabled in this server.")
                
            disabled_cmds = []
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    cmd_name = parts[2]
                    disabled_cmds.append(f"`!{cmd_name}`")
                    
            embed = discord.Embed(
                title="🚫 Disabled Commands",
                description="The following commands are currently strictly locked to **Admin-Only** for this server:\n\n" + ", ".join(disabled_cmds),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await ctx.send(f"❌ Could not find a command named `{command_name}`.")
            
        key = f"cmd_disabled:{ctx.guild.id}:{cmd.name}"
        is_disabled = await self.bot.db.get(key)
        
        if is_disabled:
            await self.bot.db.delete(key)
            await ctx.send(f"✅ The command `{cmd.name}` is now **ENABLED** for all users in this server.")
        else:
            await self.bot.db.set(key, "1")
            await ctx.send(f"🚫 The command `{cmd.name}` is now **DISABLED** (Admin-only) in this server.")

    @commands.command(name="toggle_cog", aliases=["togglecog"])
    @commands.has_permissions(administrator=True)
    async def toggle_cog(self, ctx, cog_name: str = None):
        """Toggles an entire cog on or off for this server."""
        if not cog_name:
            return await ctx.send("❌ Usage: `!togglecog <CogName>`. Example: `!togglecog Calculators`.")
            
        # Find the cog (case-insensitive)
        target_cog = None
        for name, cog in self.bot.cogs.items():
            if name.lower() == cog_name.lower():
                target_cog = cog
                break
                
        if not target_cog:
            return await ctx.send(f"❌ Could not find a module named `{cog_name}`.")
            
        commands_list = target_cog.get_commands()
        if not commands_list:
            return await ctx.send(f"⚠️ The `{target_cog.qualified_name}` module doesn't have any toggleable commands.")
            
        # Check if the FIRST command in the cog is disabled to guess if we're enabling or disabling
        first_cmd_key = f"cmd_disabled:{ctx.guild.id}:{commands_list[0].name}"
        is_disabled = await self.bot.db.get(first_cmd_key)
        
        count = 0
        if is_disabled:
            # Re-enable all
            for cmd in commands_list:
                key = f"cmd_disabled:{ctx.guild.id}:{cmd.name}"
                await self.bot.db.delete(key)
                count += 1
            await self.bot.db.delete(f"cog_disabled:{ctx.guild.id}:{target_cog.qualified_name}")
            await ctx.send(f"✅ **ENABLED** `{target_cog.qualified_name}`. Restored access to **{count}** commands in this server.")
        else:
            # Disable all
            for cmd in commands_list:
                key = f"cmd_disabled:{ctx.guild.id}:{cmd.name}"
                await self.bot.db.set(key, "1")
                count += 1
            await self.bot.db.set(f"cog_disabled:{ctx.guild.id}:{target_cog.qualified_name}", "1")
            await ctx.send(f"🚫 **DISABLED** `{target_cog.qualified_name}`. Locked **{count}** commands as Admin-Only in this server.")

    @commands.command(name="toggle_invisible", aliases=["invisible"])
    @commands.has_permissions(administrator=True)
    async def toggle_invisible(self, ctx):
        """Toggles the global visibility (online/invisible) of the bot."""
        # Must be owner to use this normally but admin works natively for the guild owner requirement
        is_invisible = await self.bot.db.get("kingbot_global_invisible")
        
        if is_invisible == "1":
            await self.bot.db.delete("kingbot_global_invisible")
            await self.bot.change_presence(status=discord.Status.online)
            await ctx.send("👁️ **KingBot is now ONLINE globally.** All servers can now see the bot in the member list.")
        else:
            await self.bot.db.set("kingbot_global_invisible", "1")
            await self.bot.change_presence(status=discord.Status.invisible)
            await ctx.send("👻 **KingBot is now INVISIBLE globally.** The bot is successfully hidden in the offline members list across all servers.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
