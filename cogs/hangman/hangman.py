import os

"""
Original Port Author: Flame442 (FlameCogs)
Ported to discord.py specifically for KingBot & Kingshot (Century Games) Branding.
"""
import discord
from discord.ext import commands
from random import randint


class ExecutionModal(discord.ui.Modal, title="King's Execution"):
    guess = discord.ui.TextInput(
        label="Enter A Single Letter:",
        style=discord.TextStyle.short,
        placeholder="Type a letter from A to Z...",
        required=True,
        max_length=1,
        min_length=1,
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        await self.view.process_guess(interaction, self.guess.value.lower())


class ExecutionView(discord.ui.View):
    def __init__(self, cog, ctx, word):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx
        self.word = word
        self.guessed = ""
        self.fails = 0
        self.boardmsg = None

    async def on_timeout(self):
        if self.boardmsg:
            try:
                for c in self.children:
                    c.disabled = True
                await self.boardmsg.edit(
                    content=f"Game Over (Timeout). The word was {self.word}.", view=self
                )
            except Exception:
                pass

    @discord.ui.button(label="🩸 Guess Letter", style=discord.ButtonStyle.danger)
    async def guess_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "Only the executioner can play this round!", ephemeral=True
            )
        await interaction.response.send_modal(ExecutionModal(self))

    async def process_guess(self, interaction: discord.Interaction, letter: str):
        if letter not in "abcdefghijklmnopqrstuvwxyz":
            return await interaction.response.send_message(
                "You must guess an alphabet letter!", ephemeral=True
            )

        if letter in self.guessed:
            p = self.cog._get_message(self.word, self.guessed)
            p = f"```{self.cog.man[self.fails]}\n{p}```You already guessed '{letter}', fool!\n"
            return await interaction.response.edit_message(content=p, view=self)

        self.guessed += letter
        if letter not in self.word:
            self.fails += 1
            if self.fails == 6:
                p = self.cog._get_message(self.word, self.guessed)
                p = f"```{self.cog.man[self.fails]}\n{p}```The guillotine drops! Execution complete.\nThe word was {self.word}."
                for c in self.children:
                    c.disabled = True
                self.stop()
                return await interaction.response.edit_message(content=p, view=self)

        if not (set("abcdefghijklmnopqrstuvwxyz") & set(self.word)) - set(self.guessed):
            p = self.cog._get_message(self.word, self.guessed)
            p = f"```\n{self.cog.man[self.fails]}\n{p}```You guessed the King's password and spared the peasant!\nThe word was {self.word}."
            for c in self.children:
                c.disabled = True
            self.stop()
            return await interaction.response.edit_message(content=p, view=self)

        p = self.cog._get_message(self.word, self.guessed)
        p = f"```{self.cog.man[self.fails]}\n{p}```"
        await interaction.response.edit_message(content=p, view=self)


class KingsExecution(commands.Cog):
    """🎲 Kings Execution (Hangman) Game Modules

    These commands contain the royal execution game!
    """

    def __init__(self, bot):
        self.bot = bot
        self.doEdit = True
        self.man = [
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |       \n"
                "   |       \n"
                "   |       \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |   |   \n"
                "   |   |   \n"
                "   |       \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |  \\|  \n"
                "   |   |   \n"
                "   |       \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |  \\|/ \n"
                "   |   |   \n"
                "   |       \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |  \\|/ \n"
                "   |   |   \n"
                "   |  /    \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   O   \n"
                "   |  \\|/ \n"
                "   |   |   \n"
                "   |  / \\ \n"
                "   |       \n"
            ),
            (
                "    ___    \n"
                "   |   |   \n"
                "   |   X   \n"
                "   |  \\|/ \n"
                "   |   |   \n"
                "   |  / \\ \n"
                "   |       \n"
            ),
        ]

    @staticmethod
    def _get_message(word, guessed):
        """Returns a string of the guessing text."""
        p = ""
        for l in word:
            if l not in "abcdefghijklmnopqrstuvwxyz":
                p += l + " "
            elif l in guessed:
                p += l + " "
            else:
                p += "_ "
        p += "    ("
        for l in guessed:
            if l not in word:
                p += l
        p += ")"
        return p

    @commands.hybrid_command(aliases=["hangman"])
    async def execution(self, ctx):
        """Play Kings Execution! Guess the password to save the peasant.

        **How to Play:**
        A random word from the King's dictionary is chosen and masked. You must guess the missing letters.
        To play, click the red **🩸 Guess Letter** button attached to the game board. A popup will appear where you can securely type a single alphabet letter without spamming the chat channel!

        If you guess incorrectly 6 times, the guillotine drops and you lose!
        """
        try:
            fp = os.path.join(os.path.dirname(__file__), "data", "words.txt")
            f = open(fp)
        except FileNotFoundError:
            await ctx.send("The King's dictionary is missing!")
            return

        wordlist = [line.strip().lower() for line in f]
        word = wordlist[randint(0, len(wordlist) - 1)]

        view = ExecutionView(self, ctx, word)
        p = self._get_message(word, view.guessed)
        p = f"```{self.man[view.fails]}\n{p}```"
        view.boardmsg = await ctx.send(content=p, view=view)


async def setup(bot):
    await bot.add_cog(KingsExecution(bot))
