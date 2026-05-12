import discord
from discord.ext import commands
import asyncio


class PanelConfigModal(discord.ui.Modal, title="Customize Ticket Panel"):
    panel_title = discord.ui.TextInput(
        label="Panel Title", default="📞 Contact Server Support", max_length=100
    )
    panel_desc = discord.ui.TextInput(
        label="Panel Description",
        style=discord.TextStyle.paragraph,
        default="Need help? Click the button below to instantly spawn a secure, private room where you can speak directly and confidentially with our moderation team.",
        max_length=1000,
    )
    btn_label = discord.ui.TextInput(
        label="Button Label", default="Open Support Ticket", max_length=80
    )
    btn_emoji = discord.ui.TextInput(label="Button Emoji", default="✉️", max_length=10)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.hset(
            f"ticket_config:{interaction.guild_id}",
            "panel_title",
            self.panel_title.value,
        )
        await self.bot.db.hset(
            f"ticket_config:{interaction.guild_id}", "panel_desc", self.panel_desc.value
        )
        await self.bot.db.hset(
            f"ticket_config:{interaction.guild_id}", "btn_label", self.btn_label.value
        )
        await self.bot.db.hset(
            f"ticket_config:{interaction.guild_id}", "btn_emoji", self.btn_emoji.value
        )
        await interaction.followup.send(
            "✅ Public Ticket Panel details successfully updated and saved to Database!",
            ephemeral=True,
        )


class WelcomeConfigModal(discord.ui.Modal, title="Customize Ticket Welcome"):
    welcome_text = discord.ui.TextInput(
        label="Welcome Text (Use {user} for mention)",
        style=discord.TextStyle.paragraph,
        default="Welcome {user}!\n\nPlease describe your issue or concern in full detail here. A member of the staff team will be with you shortly to assist.\n\nTo lock and archive this ticket, click the button below.",
        max_length=2000,
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.hset(
            f"ticket_config:{interaction.guild_id}",
            "welcome_text",
            self.welcome_text.value,
        )
        await interaction.followup.send(
            "✅ Internal Ticket Welcome message successfully updated and saved to Database!",
            ephemeral=True,
        )


class TicketChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Instantly deploy ticket panel to a channel...",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = self.values[0]

        # Load custom panel details from DB
        title = (
            await self.bot.db.hget(
                f"ticket_config:{interaction.guild_id}", "panel_title"
            )
            or "📞 Contact Server Support"
        )
        desc = (
            await self.bot.db.hget(
                f"ticket_config:{interaction.guild_id}", "panel_desc"
            )
            or "Need help? Click the button below to instantly spawn a secure, private room where you can speak directly and confidentially with our moderation team."
        )
        btn_lbl = (
            await self.bot.db.hget(f"ticket_config:{interaction.guild_id}", "btn_label")
            or "Open Support Ticket"
        )
        btn_emj = (
            await self.bot.db.hget(f"ticket_config:{interaction.guild_id}", "btn_emoji")
            or "✉️"
        )

        embed = discord.Embed(title=title, description=desc, color=discord.Color.gold())
        view = discord.ui.View(timeout=None)

        # Fix missing emoji string issue (Discord UI accepts strings for emojis)
        create_btn = discord.ui.Button(
            label=btn_lbl,
            style=discord.ButtonStyle.primary,
            custom_id="btn_ticket_create",
            emoji=btn_emj,
        )
        view.add_item(create_btn)

        try:
            await channel.send(embed=embed, view=view)
            await interaction.followup.send(
                f"✅ Ticket panel successfully deployed to {channel.mention}!",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error sending to {channel.mention}: {e}", ephemeral=True
            )


class TicketConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(TicketChannelSelect(bot))

    @discord.ui.button(
        label="Edit Public Panel Details",
        style=discord.ButtonStyle.secondary,
        emoji="🎨",
        row=1,
    )
    async def edit_panel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(PanelConfigModal(self.bot))

    @discord.ui.button(
        label="Edit Ticket Welcome Text",
        style=discord.ButtonStyle.secondary,
        emoji="📝",
        row=1,
    )
    async def edit_welcome(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(WelcomeConfigModal(self.bot))


class Ticketing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "btn_ticket_create":
            await self._handle_ticket_create(interaction)

        elif custom_id == "btn_ticket_close":
            await self._handle_ticket_close(interaction)

    async def _handle_ticket_create(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name="🎟️ Tickets")
        if not category:
            try:
                category = await guild.create_category("🎟️ Tickets")
            except discord.Forbidden:
                return await interaction.followup.send(
                    "❌ Error: I don't have permission to create channels or categories.",
                    ephemeral=True,
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            ),
        }

        clean_name = "".join(
            c for c in user.display_name if c.isalnum() or c in ("_", "-")
        ).lower()
        if not clean_name:
            clean_name = "user"

        try:
            ticket_channel = await guild.create_text_channel(
                f"ticket-{clean_name}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket created by {user.display_name}",
            )
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Failed to create ticket channel: {e}", ephemeral=True
            )

        view = discord.ui.View(timeout=None)
        close_btn = discord.ui.Button(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            custom_id="btn_ticket_close",
            emoji="🔒",
        )
        view.add_item(close_btn)

        # Load custom welcome text from database
        custom_welcome = await self.bot.db.hget(
            f"ticket_config:{guild.id}", "welcome_text"
        )
        if custom_welcome:
            desc = custom_welcome.replace("{user}", user.mention)
        else:
            desc = f"Welcome {user.mention}!\n\nPlease describe your issue or concern in full detail here. A member of the staff team will be with you shortly to assist.\n\nTo lock and archive this ticket, click the button below."

        embed = discord.Embed(
            title="🎟️ Support Ticket", description=desc, color=discord.Color.blue()
        )

        await ticket_channel.send(f"{user.mention}", embed=embed, view=view)
        await interaction.followup.send(
            f"✅ Ticket successfully created! Please head over to {ticket_channel.mention}",
            ephemeral=True,
        )

    async def _handle_ticket_close(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(
            title="🔒 Closing Ticket",
            description="This ticket is being archived and will be permanently deleted in 5 seconds...",
            color=discord.Color.red(),
        )
        await interaction.channel.send(embed=embed)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(
                reason=f"Ticket closed by {interaction.user.display_name}"
            )
        except Exception:
            pass

    @commands.hybrid_command(
        name="setup_tickets", aliases=["tickets_admin", "ticketconfig"]
    )
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """Interactive Admin Dashboard for configuring and deploying the Ticket System."""
        embed = discord.Embed(
            title="🎟️ Ticket System Configurator",
            description="Customize how your tickets look using the buttons below, and then instantly deploy the 'Open Support Ticket' panel into any text channel using the dropdown menu!\\nAll specific text details are saved natively to the bot's database.",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed, view=TicketConfigView(self.bot))


async def setup(bot):
    await bot.add_cog(Ticketing(bot))
