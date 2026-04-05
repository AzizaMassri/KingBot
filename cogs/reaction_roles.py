import discord
from discord.ext import commands
from discord import app_commands
import re

class ReactionRoleModal(discord.ui.Modal, title='Reaction Role Builder'):
    menu_title = discord.ui.TextInput(
        label='Menu Title',
        placeholder='e.g., Pronouns',
        required=True,
        max_length=100
    )

    menu_description = discord.ui.TextInput(
        label='Menu Description',
        placeholder='e.g., Select your pronouns below!',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    roles_input = discord.ui.TextInput(
        label='Roles & Emojis (Emoji @Role per line)',
        placeholder='👧 @She/Her\n👦 @He/Him\n👾 123456789012345678\n✨ They/Them',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=3000
    )

    def __init__(self, target_channel: discord.TextChannel):
        super().__init__()
        self.target_channel = target_channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        lines = self.roles_input.value.strip().split('\n')
        view = discord.ui.View(timeout=None)
        
        added_roles = []
        invalid_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                invalid_lines.append(f"`{line}` (Missing space between emoji and role)")
                continue
                
            emoji_str = parts[0]
            role_str = parts[1].strip()
            
            # Find the role
            role = None
            
            # 1. Check for Ping <@&1234...>
            match = re.match(r'<@&!?([0-9]+)>', role_str)
            if match:
                role = interaction.guild.get_role(int(match.group(1)))
            # 2. Check for raw ID
            elif role_str.isdigit():
                role = interaction.guild.get_role(int(role_str))
            # 3. Check for exact Name (strip bleeding @ if they just typed @Name manually)
            else:
                name_to_find = role_str[1:] if role_str.startswith('@') else role_str
                role = discord.utils.get(interaction.guild.roles, name=name_to_find)
                if not role:
                    try:
                        role = await interaction.guild.create_role(
                            name=name_to_find, 
                            reason="Reaction Role Builder automatic creation"
                        )
                    except discord.Forbidden:
                        invalid_lines.append(f"`{line}` (Missing Manage Roles permission to create role)")
                        continue
                    except Exception as e:
                        invalid_lines.append(f"`{line}` (Failed to create role)")
                        continue
                        
            if role:
                try:
                    button = discord.ui.Button(
                        custom_id=f"rr_{role.id}", 
                        label=role.name, 
                        emoji=emoji_str, 
                        style=discord.ButtonStyle.secondary
                    )
                    view.add_item(button)
                    added_roles.append(f"{emoji_str} {role.mention}")
                except Exception as e:
                    invalid_lines.append(f"`{line}` (Invalid Emoji or Button Limit Reached)")
            else:
                invalid_lines.append(f"`{line}` (Role not found)")

        if not added_roles:
            err_msg = "❌ Failed to create the menu. No valid roles were found in your input."
            if invalid_lines:
                err_msg += "\n\n⚠️ **Errors:**\n" + "\n".join(invalid_lines)
            return await interaction.followup.send(err_msg, ephemeral=True)
            
        embed = discord.Embed(
            title=self.menu_title.value,
            description=self.menu_description.value,
            color=discord.Color.blurple()
        )
        
        try:
            await self.target_channel.send(embed=embed, view=view)
        except discord.Forbidden:
            return await interaction.followup.send(f"❌ I don't have permission to send messages in {self.target_channel.mention}!", ephemeral=True)
            
        success_msg = f"✅ Successfully built and posted the Reaction Role Menu in {self.target_channel.mention}!\n\n**Added Roles:**\n" + "\n".join(added_roles)
        if invalid_lines:
            success_msg += "\n\n⚠️ **Skipped the following invalid lines:**\n" + "\n".join(invalid_lines)
            
        await interaction.followup.send(success_msg, ephemeral=True)

class BuilderLaunchView(discord.ui.View):
    def __init__(self, target_channel: discord.TextChannel, author: discord.Member):
        super().__init__(timeout=300)
        self.target_channel = target_channel
        self.author = author

    @discord.ui.button(label="Launch Builder 🛠️", style=discord.ButtonStyle.success)
    async def launch_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Only the command author can launch this builder.", ephemeral=True)
            
        await interaction.response.send_modal(ReactionRoleModal(self.target_channel))
        
        # Cleanup the launcher message
        try:
            await interaction.message.delete()
        except:
            pass
        self.stop()

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reactionroles", aliases=["rr", "build_roles", "rrbuilder"])
    @commands.has_permissions(administrator=True)
    async def reactionroles(self, ctx, channel: discord.TextChannel = None):
        """Launches the modern, interactive Reaction Role Builder Modal."""
        if not channel:
            channel = ctx.channel
            
        embed = discord.Embed(
            title="🛠️ Reaction Role Builder",
            description=f"Click the button below to launch the interactive UI builder.\nThe generated menu will be posted to {channel.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(text="This launch panel will expire in 5 minutes.")
        
        view = BuilderLaunchView(channel, ctx.author)
        message = await ctx.send(embed=embed, view=view)
        
        # Optionally delete the command invocation to keep it clean
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # We only care about Custom ID Component interactions for Reaction Roles
        if interaction.type != discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("rr_"):
            return
            
        # The custom_id format is rr_{role.id}
        try:
            role_id = int(custom_id[3:])
        except ValueError:
            return # Malformed Custom ID
            
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ This role no longer exists on the server!", ephemeral=True)
            
        # Check permissions to manage roles
        if not interaction.guild.me.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ I lack the `Manage Roles` permission to assign this to you.", ephemeral=True)
            
        # Check if bot's top role is high enough
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ My role hierarchy is too low! Please move the bot's role above the requested role in Server Settings.", ephemeral=True)

        # Toggle the role
        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role, reason="Reaction Role Menu")
                await interaction.response.send_message(f"➖ Removed **{role.name}**.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to remove role: {e}", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role, reason="Reaction Role Menu")
                await interaction.response.send_message(f"➕ Added **{role.name}**.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to add role: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
