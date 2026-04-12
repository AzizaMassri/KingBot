import discord
from discord.ext import commands
from discord import app_commands
import re
from cogs.utils.tiers import requires_tier, Tier

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
        valid_items = []
        invalid_lines = []
        added_roles = []
        
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
                # Auto-create the role if it was a name input and didn't exist
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
                valid_items.append((line, role, emoji_str))
            else:
                invalid_lines.append(f"`{line}` (Role not found)")

        if not valid_items:
            err_msg = "❌ Failed to create the menu. No valid roles were found in your input."
            if invalid_lines:
                err_msg += "\n\n⚠️ **Errors:**\n" + "\n".join(invalid_lines)
            return await interaction.followup.send(err_msg, ephemeral=True)
            
        options_list = []
        for i, (line, role, emoji_str) in enumerate(valid_items):
            try:
                options_list.append(discord.SelectOption(
                    label=role.name,
                    value=str(role.id),
                    emoji=emoji_str
                ))
                added_roles.append(f"{emoji_str} {role.mention}")
            except Exception as e:
                invalid_lines.append(f"`{line}` (Invalid Emoji or Limit Reached)")

        if not added_roles:
            err_msg = "❌ Failed to create the menu. No valid emojis were found in your input."
            if invalid_lines:
                err_msg += "\n\n⚠️ **Errors:**\n" + "\n".join(invalid_lines)
            return await interaction.followup.send(err_msg, ephemeral=True)
            
        view = discord.ui.View(timeout=None)
        select = discord.ui.Select(
            custom_id="rr_select",
            placeholder="Select your roles...",
            min_values=0,
            max_values=len(options_list),
            options=options_list
        )
        view.add_item(select)
            
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
    @requires_tier(Tier.PREMIUM)
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
        if custom_id != "rr_select":
            return
            
        if not interaction.guild.me.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ I lack the `Manage Roles` permission to update your roles.", ephemeral=True)

        selected_role_ids = [int(v) for v in interaction.data.get("values", [])]
        
        # Get all role ids available in this specific select menu
        component = interaction.message.components[0].children[0]
        available_role_ids = [int(opt.value) for opt in component.options]
        
        roles_to_add = []
        roles_to_remove = []
        
        for r_id in available_role_ids:
            role = interaction.guild.get_role(r_id)
            if not role: continue
            
            if interaction.guild.me.top_role <= role: continue
            
            if r_id in selected_role_ids:
                if role not in interaction.user.roles:
                    roles_to_add.append(role)
            else:
                if role in interaction.user.roles:
                    roles_to_remove.append(role)

        added_names = []
        removed_names = []
        
        if roles_to_add:
            try:
                await interaction.user.add_roles(*roles_to_add, reason="Reaction Role Menu")
                added_names = [r.name for r in roles_to_add]
            except Exception:
                pass
                
        if roles_to_remove:
            try:
                await interaction.user.remove_roles(*roles_to_remove, reason="Reaction Role Menu")
                removed_names = [r.name for r in roles_to_remove]
            except Exception:
                pass
                
        msg_parts = []
        if added_names:
            msg_parts.append(f"➕ Added: {', '.join(added_names)}")
        if removed_names:
            msg_parts.append(f"➖ Removed: {', '.join(removed_names)}")
            
        if not msg_parts:
            msg = "Your roles have been updated! (No changes made)"
        else:
            msg = "\n".join(msg_parts)
            
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
