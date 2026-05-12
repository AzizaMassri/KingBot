import discord
from discord.ext import commands


class UIContext(commands.Context):
    def __init__(self, interaction: discord.Interaction, bot: commands.Bot, command):
        self.interaction = interaction
        self.message = interaction.message
        self.bot = bot
        self.author = interaction.user
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.command = command
        self.me = interaction.guild.me if interaction.guild else None

    async def send(self, *args, **kwargs):
        if not self.interaction.response.is_done():
            return await self.interaction.response.send_message(*args, **kwargs)
        else:
            return await self.interaction.followup.send(*args, **kwargs)


class GameInputModal(discord.ui.Modal):
    def __init__(self, title, inputs, callback):
        super().__init__(title=title)
        self._callback = callback
        self.inputs = inputs
        self.ui_inputs = []
        for i in inputs:
            text_input = discord.ui.TextInput(
                label=i.get("label"),
                placeholder=i.get("placeholder", ""),
                required=i.get("required", True),
            )
            self.ui_inputs.append(text_input)
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        values = [i.value for i in self.ui_inputs]
        await self._callback(interaction, *values)


class MinigameHubView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

        # We start with only the select menu visible
        self.select_menu = discord.ui.Select(
            placeholder="Select a game category...",
            options=[
                discord.SelectOption(
                    label="Casino & Betting",
                    emoji="🎰",
                    description="Blackjack, Coinflip, Slots, Roll",
                ),
                discord.SelectOption(
                    label="Board Games",
                    emoji="🎲",
                    description="Monopoly, Connect 4, Tic-Tac-Toe, Armada",
                ),
                discord.SelectOption(
                    label="Interactive Games",
                    emoji="🕹️",
                    description="Heist, Race, execution, Roulette",
                ),
            ],
            custom_id="hub_game_select",
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)
        self.current_buttons = []

    def clear_buttons(self):
        for btn in self.current_buttons:
            self.remove_item(btn)
        self.current_buttons = []

    async def select_callback(self, interaction: discord.Interaction):
        choice = self.select_menu.values[0]
        self.clear_buttons()

        # Configure buttons based on category
        if choice == "Casino & Betting":
            self.add_game_button(
                "Coinflip", "🪙", discord.ButtonStyle.primary, self.launch_coinflip
            )
            self.add_game_button(
                "Blackjack", "🃏", discord.ButtonStyle.primary, self.launch_blackjack
            )
            self.add_game_button(
                "Roll", "🎲", discord.ButtonStyle.primary, self.launch_roll
            )
            self.add_game_button(
                "Slots", "🎰", discord.ButtonStyle.primary, self.launch_slots
            )
        elif choice == "Board Games":
            self.add_game_button(
                "Monopoly", "🎩", discord.ButtonStyle.success, self.launch_monopoly
            )
            self.add_game_button(
                "Battleship", "🚢", discord.ButtonStyle.success, self.launch_armada
            )
            self.add_game_button(
                "Connect 4", "🔴", discord.ButtonStyle.success, self.launch_connect4
            )
            self.add_game_button(
                "Tic-Tac-Toe", "❌", discord.ButtonStyle.success, self.launch_tictactoe
            )
        elif choice == "Interactive Games":
            self.add_game_button(
                "Race", "🏁", discord.ButtonStyle.danger, self.launch_race
            )
            self.add_game_button(
                "Heist", "🐻", discord.ButtonStyle.danger, self.launch_heist
            )
            self.add_game_button(
                "Russian Roulette",
                "🔫",
                discord.ButtonStyle.danger,
                self.launch_roulette,
            )
            self.add_game_button(
                "Execution", "🪢", discord.ButtonStyle.danger, self.launch_execution
            )

        await interaction.response.edit_message(view=self)

    def add_game_button(self, label, emoji, style, callback):
        btn = discord.ui.Button(label=label, emoji=emoji, style=style)
        btn.callback = callback
        self.current_buttons.append(btn)
        self.add_item(btn)

    async def invoke_command(self, interaction, command_name, *args, **kwargs):
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await interaction.response.send_message(
                f"❌ Command `{command_name}` not found or disabled.", ephemeral=True
            )
        ctx = UIContext(interaction, self.bot, cmd)
        try:
            await ctx.invoke(cmd, *args, **kwargs)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"An error occurred: {e}", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"An error occurred: {e}", ephemeral=True
                )

    # === CASINO ===
    async def launch_coinflip(self, interaction: discord.Interaction):
        inputs = [
            {"label": "Heads or Tails?", "placeholder": "heads/tails"},
            {"label": "Bet Amount", "placeholder": "100"},
        ]

        async def on_submit(inter, choice, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "coinflip", choice, bet)

        await interaction.response.send_modal(
            GameInputModal("Play Coinflip", inputs, on_submit)
        )

    async def launch_blackjack(self, interaction: discord.Interaction):
        inputs = [{"label": "Bet Amount", "placeholder": "100"}]

        async def on_submit(inter, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "blackjack", bet)

        await interaction.response.send_modal(
            GameInputModal("Play Blackjack", inputs, on_submit)
        )

    async def launch_roll(self, interaction: discord.Interaction):
        inputs = [{"label": "Bet Amount", "placeholder": "100"}]

        async def on_submit(inter, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "roll", bet)

        await interaction.response.send_modal(
            GameInputModal("Play Roll", inputs, on_submit)
        )

    async def launch_slots(self, interaction: discord.Interaction):
        inputs = [{"label": "Bet Amount", "placeholder": "100"}]

        async def on_submit(inter, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "slots", bet)

        await interaction.response.send_modal(
            GameInputModal("Play Slots", inputs, on_submit)
        )

    # === BOARD GAMES ===
    async def launch_monopoly(self, interaction: discord.Interaction):
        await self.invoke_command(interaction, "monopoly", savefile=None)

    async def launch_armada(self, interaction: discord.Interaction):
        # Armada asks for an opponent user
        inputs = [
            {
                "label": "Opponent ID (Leave blank to invite any)",
                "placeholder": "ID or blank",
                "required": False,
            }
        ]

        async def on_submit(inter, opponent_id):
            opponent = None
            if opponent_id:
                try:
                    opponent = inter.guild.get_member(int(opponent_id))
                    if not opponent:
                        return await inter.response.send_message(
                            "Member not found.", ephemeral=True
                        )
                except Exception:
                    return await inter.response.send_message(
                        "Invalid ID.", ephemeral=True
                    )
            await self.invoke_command(inter, "armada", opponent)

        await interaction.response.send_modal(
            GameInputModal("Battleship", inputs, on_submit)
        )

    async def launch_connect4(self, interaction: discord.Interaction):
        inputs = [
            {
                "label": "Opponent ID (Leave blank to play bot)",
                "placeholder": "ID or blank",
                "required": False,
            }
        ]

        async def on_submit(inter, opponent_id):
            opponent = None
            if opponent_id:
                try:
                    opponent = inter.guild.get_member(int(opponent_id))
                    if not opponent:
                        return await inter.response.send_message(
                            "Member not found.", ephemeral=True
                        )
                except Exception:
                    return await inter.response.send_message(
                        "Invalid ID.", ephemeral=True
                    )
            await self.invoke_command(inter, "connectfour", opponent)

        await interaction.response.send_modal(
            GameInputModal("Connect 4", inputs, on_submit)
        )

    async def launch_tictactoe(self, interaction: discord.Interaction):
        inputs = [
            {
                "label": "Opponent ID (Leave blank to play bot)",
                "placeholder": "ID or blank",
                "required": False,
            }
        ]

        async def on_submit(inter, opponent_id):
            opponent = None
            if opponent_id:
                try:
                    opponent = inter.guild.get_member(int(opponent_id))
                    if not opponent:
                        return await inter.response.send_message(
                            "Member not found.", ephemeral=True
                        )
                except Exception:
                    return await inter.response.send_message(
                        "Invalid ID.", ephemeral=True
                    )
            await self.invoke_command(inter, "swordsandshields", opponent)

        await interaction.response.send_modal(
            GameInputModal("Tic-Tac-Toe", inputs, on_submit)
        )

    # === INTERACTIVE ===
    async def launch_race(self, interaction: discord.Interaction):
        inputs = [
            {"label": "Animal/Racer", "placeholder": "🐢"},
            {"label": "Bet Amount", "placeholder": "100"},
        ]

        async def on_submit(inter, animal, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "race", animal, bet)

        await interaction.response.send_modal(
            GameInputModal("Host Race", inputs, on_submit)
        )

    async def launch_heist(self, interaction: discord.Interaction):
        inputs = [{"label": "Difficulty (1-5)", "placeholder": "1"}]

        async def on_submit(inter, diff):
            try:
                diff = int(diff)
            except Exception:
                return await inter.response.send_message(
                    "Difficulty must be a number 1-5.", ephemeral=True
                )
            await self.invoke_command(inter, "heist", diff)

        await interaction.response.send_modal(
            GameInputModal("Start Heist", inputs, on_submit)
        )

    async def launch_roulette(self, interaction: discord.Interaction):
        inputs = [{"label": "Bet Amount", "placeholder": "100"}]

        async def on_submit(inter, bet):
            try:
                bet = int(bet)
            except Exception:
                return await inter.response.send_message(
                    "Bet must be a number.", ephemeral=True
                )
            await self.invoke_command(inter, "roulette", bet)

        await interaction.response.send_modal(
            GameInputModal("Russian Roulette", inputs, on_submit)
        )

    async def launch_execution(self, interaction: discord.Interaction):
        await self.invoke_command(interaction, "execution")
