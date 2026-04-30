import discord
from discord.ext import commands
from cogs.utils.tiers import requires_tier, Tier

class OnboardingModal(discord.ui.Modal, title='Setup Your Profile'):
    in_game_name = discord.ui.TextInput(
        label='In-Game Name ([Alliance Tag]Name)',
        style=discord.TextStyle.short,
        placeholder='e.g. [COD]ShadowHunter or [CoD]Player',
        required=True,
        max_length=30,
    )

    def __init__(self, bot, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user = interaction.user
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            return await interaction.followup.send("⚠️ Could not find the server. Make sure you haven't left!")
            
        member = guild.get_member(user.id)
        if not member:
            return await interaction.followup.send("⚠️ You do not appear to be in the server anymore.")
        

        in_game_name = self.in_game_name.value.strip()
        new_nickname = in_game_name

        # 1. Update Nickname
        try:
            await member.edit(nick=new_nickname[:32])
        except discord.Forbidden:
            await interaction.followup.send("⚠️ I couldn't change your nickname (My role is too low), but I will proceed.", ephemeral=True)

        # 3. Present Role Picker instead of removing the role directly
        try:
            custom_roles = await self.bot.db.smembers(f"onboarding_roles:{self.guild_id}")
        except:
            custom_roles = None
            
        view = RolePickerView(self.bot, self.guild_id, custom_roles)
        msg_text = (
            "✅ **Name accepted!** Please select your **preferred language** AND your **current rank** below to complete setup and unlock chat.\n\n"
            "**Note:** Officer and Leader roles are assigned by the server owner. If you are an Officer or Leader, please tag Rocket instead!"
        )
        await interaction.followup.send(msg_text, view=view, ephemeral=True)


class RolePickerDropdown(discord.ui.Select):
    def __init__(self, bot, guild_id: int, custom_roles=None):
        self.bot = bot
        self.guild_id = guild_id
        
        # Default fallback options if the server admin hasn't configured any custom ones yet
        options = [
            discord.SelectOption(label="Academy", description="Select this if you are in the Academy"),
            discord.SelectOption(label="R2", description="Select this if you are an R2"),
            discord.SelectOption(label="R3", description="Select this if you are an R3"),
        ]
        
        # Override the hardcoded defaults with the custom roles (we sort them for consistency)
        if custom_roles:
            options = [discord.SelectOption(label=r) for r in sorted(list(custom_roles))]
            
        super().__init__(placeholder="Select your Alliance role...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = self.bot.get_guild(self.guild_id)
        
        if not guild:
            return await interaction.followup.send("⚠️ Could not find the associated server.", ephemeral=True)
            
        member = guild.get_member(interaction.user.id)
        if not member:
            return await interaction.followup.send("⚠️ You do not appear to be in the server anymore.", ephemeral=True)
            
        role_name = self.values[0]
        
        # Add the selected role
        target_role = discord.utils.get(guild.roles, name=role_name)
        if target_role:
            try:
                await member.add_roles(target_role, reason="Onboarding Role Selection")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Missing permissions to assign the `{role_name}` role.", ephemeral=True)
        else:
            await interaction.followup.send(f"⚠️ Could not find the `{role_name}` role in the server.", ephemeral=True)
            
        # Remove Onboarding restriction role
        onboarding_role = discord.utils.get(guild.roles, name="Onboarding")
        if onboarding_role and onboarding_role in member.roles:
            try:
                await member.remove_roles(onboarding_role, reason="Onboarding completed")
                await interaction.followup.send(f"✅ **Setup complete!** You have been given the `{role_name}` role and your chat is unlocked.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to remove your `Onboarding` role.", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ **Setup complete!** You have been given the `{role_name}` role.", ephemeral=True)

        # Trigger Custom Welcome Message in Server
        channel = None
        welcome_channel_id = await self.bot.db.get(f"welcome_channel:{guild.id}")
        if welcome_channel_id:
            channel = guild.get_channel(int(welcome_channel_id))
            if not channel:
                channel = self.bot.get_channel(int(welcome_channel_id))
            if not channel:
                try:
                    channel = await guild.fetch_channel(int(welcome_channel_id))
                except:
                    pass

        if channel:
            custom_greeting = await self.bot.db.get(f"welcome_msg:{guild.id}:{role_name.upper()}")
            if not custom_greeting:
                custom_greeting = await self.bot.db.get(f"welcome_msg:{guild.id}:GENERAL")
                
            if custom_greeting:
                greeting_text = custom_greeting.replace("{user}", member.mention)
                await channel.send(greeting_text)
            else:
                await channel.send(f"👋 Welcome to the server, {member.mention}! You have joined as **{role_name}**.")

class RolePickerView(discord.ui.View):
    def __init__(self, bot, guild_id: int, custom_roles=None):
        super().__init__(timeout=None)
        from cogs.utils.ui import LanguageDropdown
        
        # Provide a custom id suffix combining the user ID so the view maintains state properly if needed,
        # but onboarding ephemeral views actually don't usually need persistent custom_ids.
        # We'll just instantiate the Dropdown.
        self.add_item(LanguageDropdown(bot))
        self.add_item(RolePickerDropdown(bot, guild_id, custom_roles))


class StartOnboardingView(discord.ui.View):
    def __init__(self, bot, guild_id: int = None):
        super().__init__(timeout=None)
        self.bot = bot
        
        # We need to handle both dynamic ID creation (new joined users) and static (old buttons)
        custom_id = f"btn_start_onboarding:{guild_id}" if guild_id else "btn_start_onboarding"
        
        button = discord.ui.Button(
            label="Setup Profile", 
            style=discord.ButtonStyle.success, 
            custom_id=custom_id
        )
        self.add_item(button)

# --- Admin Configuration UI ---

class AdminRoleSelect(discord.ui.RoleSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(placeholder="Choose a role to add to Onboarding...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_role = self.values[0]
        
        if selected_role.is_bot_managed() or selected_role.is_integration() or selected_role.is_default():
            return await interaction.followup.send(f"❌ You cannot use `{selected_role.name}` because it is managed by Discord/integrations.", ephemeral=True)
            
        try:
            await self.bot.db.sadd(f"onboarding_roles:{interaction.guild.id}", selected_role.name)
            await interaction.followup.send(f"✅ Added `{selected_role.name}` to the onboarding dropdown.", ephemeral=True)
        except Exception as e:
            print(f"Failed to add role to Database: {e}")
            await interaction.followup.send("❌ Error saving role.", ephemeral=True)

class AdminRemoveRoleSelect(discord.ui.Select):
    def __init__(self, bot, current_roles):
        self.bot = bot
        options = [discord.SelectOption(label=r) for r in current_roles][:25] # max 25 options allowed by Discord
        super().__init__(placeholder="Select a configured role to remove...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_role = self.values[0]
        try:
            await self.bot.db.srem(f"onboarding_roles:{interaction.guild.id}", selected_role)
            await interaction.followup.send(f"✅ Removed `{selected_role}` from the onboarding dropdown.", ephemeral=True)
        except Exception as e:
            print(f"Failed to remove role from Database: {e}")
            await interaction.followup.send("❌ Error removing role.", ephemeral=True)

class OnboardingAdminView(discord.ui.View):
    def __init__(self, bot, current_roles: list):
        super().__init__(timeout=None)
        self.bot = bot
        
        # 1. Component to select a native discord Role to add
        self.add_item(AdminRoleSelect(bot))
        
        # 2. Component to drop an existing customized role
        if current_roles:
            self.add_item(AdminRemoveRoleSelect(bot, current_roles))

    @discord.ui.button(label="Reset All Roles to Default", style=discord.ButtonStyle.danger, row=2)
    async def reset_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            await self.bot.db.delete(f"onboarding_roles:{interaction.guild.id}")
            await interaction.followup.send("✅ Cleared all custom onboarding roles. Reset back to defaults (Academy, R2, R3).", ephemeral=True)
        except Exception as e:
            print(f"Failed to reset roles in Database: {e}")
            await interaction.followup.send("❌ Error clearing roles.", ephemeral=True)


class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # We only register the old static view because new dynamic ones use a listener
        self.bot.add_view(StartOnboardingView(self.bot))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            
            # Handle new dynamic buttons that are mapped exactly to the server
            if custom_id.startswith("btn_start_onboarding:"):
                try:
                    guild_id = int(custom_id.split(":")[1])
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        return await interaction.response.send_message("❌ Cannot find the server you are trying to join. Please rejoin!", ephemeral=True)
                        
                    modal = OnboardingModal(self.bot, guild_id)
                    await interaction.response.send_modal(modal)
                except Exception as e:
                    print(f"Error in dynamic onboarding button: {e}")
            
            # Legacy fallback for old buttons without a guild ID mapped
            elif custom_id == "btn_start_onboarding":
                user_id = interaction.user.id
                target_guild = None
                
                # Prioritize the server where the interaction actually happened (if not in DM)
                if interaction.guild:
                    target_guild = interaction.guild
                else:
                    # Prioritize finding the server where this user currently has the Onboarding role
                    for guild in self.bot.guilds:
                        member = guild.get_member(user_id)
                        role = discord.utils.get(guild.roles, name="Onboarding") if guild else None
                        if member and role and role in member.roles:
                            target_guild = guild
                            break
                        
                # Fallback to any shared server if not timed out
                if not target_guild:
                    for guild in self.bot.guilds:
                        if guild.get_member(user_id):
                            target_guild = guild
                            break
                            
                if not target_guild:
                    return await interaction.response.send_message("❌ Cannot find the server you are trying to join. Please rejoin!", ephemeral=True)
                    
                modal = OnboardingModal(self.bot, target_guild.id)
                await interaction.response.send_modal(modal)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    @requires_tier(Tier.PREMIUM)
    async def setonboardingchannel(self, ctx, channel: discord.TextChannel = None):
        """Sets the channel where onboarding members can talk."""
        if not channel:
            return await ctx.send("❌ Usage: `!setonboardingchannel #channel`")
            
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="Onboarding")
        if not role:
            try:
                role = await guild.create_role(name="Onboarding", reason="Auto-created for new member gating")
                await ctx.send("✅ Created the `Onboarding` role.")
            except discord.Forbidden:
                return await ctx.send("❌ Missing permissions to create roles.")

        # Ensure role cannot speak in ANY text channel
        msg = await ctx.send("⏳ Updating channel permissions to restrict the `Onboarding` role... This may take a moment.")
        for c in guild.text_channels:
            try:
                await c.set_permissions(role, send_messages=False, reason="Onboarding restrictions update")
            except discord.Forbidden:
                pass
                
        # Allow speaking ONLY in the selected channel
        try:
            await channel.set_permissions(role, send_messages=True, reason="Allowed onboarding channel")
        except discord.Forbidden:
            return await ctx.send("❌ Missing permissions to modify channel permissions.")

        await self.bot.db.set(f"onboarding_channel:{guild.id}", channel.id)
        await msg.edit(content=f"✅ Onboarding members will now only be able to speak in {channel.mention}.")

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    @requires_tier(Tier.PREMIUM)
    async def onboarding_admin(self, ctx):
        """Configure which roles appear in the onboarding dropdown for this server."""
        try:
            custom_roles = await self.bot.db.smembers(f"onboarding_roles:{ctx.guild.id}")
            roles_list = sorted(list(custom_roles)) if custom_roles else []
            
            embed = discord.Embed(
                title="🔧 Onboarding Role Configuration",
                description="Use the UI elements below to easily map server roles that should appear in the Onboarding Setup dropdown.",
                color=discord.Color.blue()
            )
            
            if roles_list:
                embed.add_field(name="Current Configured Roles", value="\n".join([f"• `{r}`" for r in roles_list]), inline=False)
            else:
                embed.add_field(name="Current Configured Roles", value="*Using defaults (`Academy`, `R2`, `R3`)*", inline=False)
                
            view = OnboardingAdminView(self.bot, roles_list)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error in onboarding admin: {e}")
            await ctx.send("❌ An error occurred connecting to configuration data.")

    @commands.hybrid_command(name="onboarding_roles")
    @commands.has_permissions(administrator=True)
    @requires_tier(Tier.PREMIUM)
    async def onboarding_roles_list(self, ctx):
        """View the list of roles currently configured for the onboarding menu."""
        try:
            custom_roles = await self.bot.db.smembers(f"onboarding_roles:{ctx.guild.id}")
            if custom_roles:
                roles_list = sorted(list(custom_roles))
                formatted_list = "\n".join([f"• `{r}`" for r in roles_list])
                embed = discord.Embed(
                    title="📋 Onboarding Roles",
                    description="The following roles are currently configured for new members to select during onboarding:\n\n" + formatted_list,
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="📋 Onboarding Roles",
                    description="No custom roles are configured. The system is currently using the default roles:\n\n• `Academy`\n• `R2`\n• `R3`",
                    color=discord.Color.orange()
                )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred connecting to configuration data: {e}")

    @commands.hybrid_command(name="onboarding_add")
    @commands.has_permissions(administrator=True)
    @requires_tier(Tier.PREMIUM)
    async def onboarding_add_role(self, ctx, *, role_name: str):
        """Add a role to the onboarding dropdown menu."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ The role `{role_name}` does not exist in this server. Please check the spelling.")
            
        if role.is_bot_managed() or role.is_integration() or role.is_default():
            return await ctx.send(f"❌ You cannot use `{role.name}` because it is managed by Discord/integrations.")
            
        try:
            await self.bot.db.sadd(f"onboarding_roles:{ctx.guild.id}", role.name)
            await ctx.send(f"✅ Added `{role.name}` to the onboarding dropdown.")
        except Exception as e:
            await ctx.send(f"❌ Error saving role: {e}")

    @commands.hybrid_command(name="onboarding_remove")
    @commands.has_permissions(administrator=True)
    @requires_tier(Tier.PREMIUM)
    async def onboarding_remove_role(self, ctx, *, role_name: str):
        """Remove a role from the onboarding dropdown menu."""
        try:
            result = await self.bot.db.srem(f"onboarding_roles:{ctx.guild.id}", role_name)
            if result:
                await ctx.send(f"✅ Removed `{role_name}` from the onboarding dropdown.")
            else:
                await ctx.send(f"❌ The role `{role_name}` is not currently configured in the onboarding menu. (Check `!onboarding_roles`)")
        except Exception as e:
            await ctx.send(f"❌ Error removing role: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Check if Onboarding is disabled in this server
        try:
            is_disabled = await self.bot.db.get(f"cog_disabled:{member.guild.id}:Onboarding")
            if is_disabled:
                return
        except Exception:
            pass

        # Assign Onboarding Role to restrict chat
        try:
            role = discord.utils.get(member.guild.roles, name="Onboarding")
            if role:
                await member.add_roles(role, reason="Name-lock pending")
            else:
                print(f"Onboarding role not found in {member.guild.name}")
        except Exception as e:
            print(f"Failed to assign Onboarding role to {member.display_name}: {e}")

        # Send instructions with Interactive Buttons in the onboarding channel
        welcome_msg = (
            f"🎉 Warmest welcomes to **{member.guild.name}**, {member.mention}! We are absolutely thrilled to have you here! \n\n"
            "To jump in, start chatting, and fully experience our community, we just need you to set up your profile quickly.\n"
            "**Note:** Please make sure you use your actual **In-Game Name**. Try to include your alliance tag if you have one (e.g., `[COD]ShadowHunter`).\n\n"
            "Click the button below to get started! **Please note: You have 24 hours to complete this setup.**"
        )
        
        channel_id = await self.bot.db.get(f"onboarding_channel:{member.guild.id}")
        
        channel = None
        if channel_id:
            try:
                channel = member.guild.get_channel(int(channel_id))
                if not channel:
                    channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    # Final fallback: fetch from API to ensure we don't bypass a valid channel purely due to caching
                    channel = await member.guild.fetch_channel(int(channel_id))
            except Exception as e:
                print(f"Failed to resolve onboarding channel ID {channel_id}: {e}")

        if channel:
            try:
                view = StartOnboardingView(self.bot, member.guild.id)
                await channel.send(welcome_msg, view=view)
            except Exception as e:
                print(f"Could not send onboarding message to channel {channel.name}: {e}")
                # If we fail to send in the channel, we should still fallback to DM
                try:
                    view = StartOnboardingView(self.bot, member.guild.id)
                    await member.send(welcome_msg, view=view)
                except discord.Forbidden:
                    pass
        else:
            try:
                view = StartOnboardingView(self.bot, member.guild.id)
                await member.send(welcome_msg, view=view)
            except discord.Forbidden:
                print(f"Could not send DM to {member.display_name} (DMs disabled).")

        # The 24-hour time limit kick has been removed by request

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
