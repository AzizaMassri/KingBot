import discord
from discord.ext import commands

class WelcomeRoleModal(discord.ui.Modal, title='Set Welcome Message'):
    def __init__(self, bot, role_id):
        super().__init__()
        self.bot = bot
        self.role_id = role_id
        
        self.welcome_msg = discord.ui.TextInput(
            label='Message (Use {user} for mention)',
            style=discord.TextStyle.paragraph,
            placeholder="Welcome {user} to the elite squad!",
            required=True,
            max_length=2000
        )
        self.add_item(self.welcome_msg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(int(self.role_id))
        if not role:
            return await interaction.followup.send("❌ Error: Role not found.", ephemeral=True)
            
        await self.bot.db.set(f"welcome_msg:{interaction.guild_id}:{role.name.upper()}", self.welcome_msg.value)
        await interaction.followup.send(f"✅ Welcome message for **{role.name}** successfully set and saved to the database!", ephemeral=True)

class WelcomeChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(channel_types=[discord.ChannelType.text], placeholder="Select the main Welcome Channel...", min_values=1, max_values=1, row=0)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = self.values[0]
        await self.bot.db.set(f"welcome_channel:{interaction.guild_id}", channel.id)
        await interaction.followup.send(f"✅ Welcome messages will now be successfully posted in {channel.mention}.", ephemeral=True)

class WelcomeRoleSelect(discord.ui.RoleSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(placeholder="Configure a message for a specific Role...", min_values=1, max_values=1, row=1)

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        await interaction.response.send_modal(WelcomeRoleModal(self.bot, role.id))

class WelcomeConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(WelcomeChannelSelect(bot))
        self.add_item(WelcomeRoleSelect(bot))

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.hybrid_command(name="welcome_admin", aliases=["welcomeconfig", "setwelcomechannel", "setwelcome"])
    @commands.has_permissions(administrator=True)
    async def welcome_admin(self, ctx):
        """Interactive Admin Dashboard for configuring Welcome Messages."""
        embed = discord.Embed(
            title="👋 Welcome System Configurator",
            description="Use the dropdowns below to fully configure how new users are greeted!\n\n**1.** Select a Welcome Channel to broadcast greetings.\n**2.** Select a Role to instantly pop-up a text editor where you can write a customized welcome message for whenever someone receives that specific role.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=WelcomeConfigView(self.bot))

async def setup(bot):
    await bot.add_cog(Welcome(bot))
