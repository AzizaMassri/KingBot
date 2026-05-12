"""
Original Port Author: Flame442 (FlameCogs)
https://github.com/Flame442/FlameCogs/tree/master/battleship
Ported to discord.py specifically for KingBot & Kingshot (Century Games) Branding.
"""

import discord
from discord.ext import commands
import json
import os

from .game import ArmadaGame
from .ai import BattleshipAI
from .views import ConfirmView, GetPlayersView


class BasicConfig:
    def __init__(self, bot):
        self.bot = bot
        self.filename = os.path.join(
            os.path.dirname(__file__), "data", "armada_data.json"
        )
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        return {}

    def _save(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    def _guild(self, guild):
        gid = str(guild.id)
        if gid not in self.data:
            self.data[gid] = {
                "extraHit": True,
                "doMention": False,
                "doImage": True,
                "useThreads": False,
            }
        return self.data[gid]

    class ConfigVal:
        def __init__(self, key, conf, guild):
            self.key = key
            self.conf = conf
            self.guild = guild

        async def __call__(self):
            return self.conf._guild(self.guild)[self.key]

        async def set(self, val):
            self.conf._guild(self.guild)[self.key] = val
            self.conf._save()

    def guild(self, guild):
        class GuildConf:
            def __init__(self, conf, g):
                self.conf = conf
                self.g = g

            async def all(self):
                return self.conf._guild(self.g)

            @property
            def extraHit(self):
                return conf.ConfigVal("extraHit", self.conf, self.g)

            @property
            def doMention(self):
                return conf.ConfigVal("doMention", self.conf, self.g)

            @property
            def doImage(self):
                return conf.ConfigVal("doImage", self.conf, self.g)

            @property
            def useThreads(self):
                return conf.ConfigVal("useThreads", self.conf, self.g)

        conf = self
        return GuildConf(conf, guild)


class KingsArmada(commands.Cog):
    """Play King's Armada with one other person."""

    def __init__(self, bot):
        self.bot = bot
        self.games = []
        self.config = BasicConfig(bot)

    @commands.guild_only()
    @commands.hybrid_command(aliases=["battleship"])
    async def armada(self, ctx, opponent: discord.Member = None):
        """Start a game of King's Armada."""
        if [game for game in self.games if game.channel == ctx.channel]:
            return await ctx.send("A game is already running in this channel.")

        if opponent is None:
            view = GetPlayersView(ctx, 2)
            initial_message = await ctx.send(view.generate_message(), view=view)
        elif opponent == ctx.guild.me or opponent.bot:
            opponent = BattleshipAI(name="KingBots Armada AI")
            initial_message = await ctx.send(
                f"You have challenged {opponent.display_name} to a game of King's Armada!"
            )
            view = None
        else:
            view = ConfirmView(opponent)
            initial_message = await ctx.send(
                f"{opponent.mention} You have been challenged to a game of King's Armada by {ctx.author.display_name}!",
                view=view,
            )

        channel = ctx.channel
        if (
            await self.config.guild(ctx.guild).useThreads()
            and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
            and ctx.channel.type is discord.ChannelType.text
        ):
            try:
                channel = await initial_message.create_thread(
                    name="Armada",
                    reason="Automated thread for Armada.",
                )
            except discord.HTTPException:
                pass

        if view:
            await view.wait()

        if opponent is None:
            if not view:
                return
            players = view.players
        elif isinstance(opponent, BattleshipAI):
            players = [ctx.author, opponent]
        else:
            if not view or not view.result:
                await channel.send(
                    f"{opponent.display_name} does not want to play, shutting down."
                )
                return
            players = [ctx.author, opponent]

        if len(players) < 2:
            return await channel.send("Nobody else wants to play, shutting down.")
        players = players[:2]

        if [game for game in self.games if game.channel == channel]:
            return await channel.send(
                "Another game started in this channel while setting up."
            )

        await channel.send(
            "A game of battleship will be played between "
            f'{" and ".join(p.display_name for p in players)}.'
        )
        game = ArmadaGame(ctx, channel, *players)
        self.games.append(game)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.hybrid_command()
    async def armadastop(self, ctx):
        """Stop the game of King's Armada in this channel."""
        wasGame = False
        for game in [g for g in self.games if g.channel == ctx.channel]:
            game._task.cancel()
            wasGame = True
        if (
            wasGame
        ):  # prevent multiple messages if more than one game exists for some reason
            await ctx.send("The game was stopped successfully.")
        else:
            await ctx.send("There is no ongoing game in this channel.")

    @commands.hybrid_command()
    async def armadaboard(self, ctx, channel: discord.TextChannel = None):
        """
        View your current board from an ongoing game in your DMs.

        Specify the channel ID of the channel the game is in.
        """
        if channel is None:
            channel = ctx.channel
        game = [game for game in self.games if game.channel.id == channel.id]
        if not game:
            return await ctx.send(
                "There is no game in that channel or that channel does not exist."
            )
        game = [g for g in game if ctx.author.id in [m.id for m in g.player]]
        if not game:
            return await ctx.send("You are not in that game.")
        game = game[0]
        p = [m.id for m in game.player].index(ctx.author.id)
        await game.send_board(p, 1, ctx.author, "")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.hybrid_group(invoke_without_command=True)
    async def armadaset(self, ctx):
        """Config options for King's Armada."""
        await ctx.send_help()
        cfg = await self.config.guild(ctx.guild).all()
        msg = (
            "Extra shot on hit: {extraHit}\n"
            "Mention on turn: {doMention}\n"
            "Display the board using an image: {doImage}\n"
            "Game contained to a thread: {useThreads}\n"
        ).format_map(cfg)
        await ctx.send(f"```py\n{msg}```")

    @armadaset.command()
    async def extra(self, ctx, value: bool = None):
        """
        Set if an extra shot should be given after a hit.

        Defaults to True.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).extraHit()
            if v:
                await ctx.send("You are currently able to shoot again after a hit.")
            else:
                await ctx.send("You are currently not able to shoot again after a hit.")
        else:
            await self.config.guild(ctx.guild).extraHit.set(value)
            if value:
                await ctx.send("You will now be able to shoot again after a hit.")
            else:
                await ctx.send("You will no longer be able to shoot again after a hit.")

    @armadaset.command()
    async def mention(self, ctx, value: bool = None):
        """
        Set if players should be mentioned when their turn begins.

        Defaults to False.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).doMention()
            if v:
                await ctx.send("Players are being mentioned when their turn begins.")
            else:
                await ctx.send(
                    "Players are not being mentioned when their turn begins."
                )
        else:
            await self.config.guild(ctx.guild).doMention.set(value)
            if value:
                await ctx.send("Players will be mentioned when their turn begins.")
            else:
                await ctx.send("Players will not be mentioned when their turn begins.")

    @armadaset.command()
    async def imgboard(self, ctx, value: bool = None):
        """
        Set if the board should be displayed using an image.

        Defaults to True.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).doImage()
            if v:
                await ctx.send("The board is currently displayed using an image.")
            else:
                await ctx.send("The board is currently displayed using text.")
        else:
            await self.config.guild(ctx.guild).doImage.set(value)
            if value:
                await ctx.send("The board will now be displayed using an image.")
            else:
                await ctx.send("The board will now be displayed using text.")

    @armadaset.command()
    async def thread(self, ctx, value: bool = None):
        """
        Set if a thread should be created per-game to contain game messages.

        Defaults to False.
        This value is server specific.
        """
        if value is None:
            v = await self.config.guild(ctx.guild).useThreads()
            if v:
                await ctx.send("The game is currently run in a per-game thread.")
            else:
                await ctx.send("The game is not currently run in a thread.")
        else:
            await self.config.guild(ctx.guild).useThreads.set(value)
            if value:
                await ctx.send("The game will now be run in a per-game thread.")
            else:
                await ctx.send("The game will not be run in a thread.")

    def cog_unload(self):
        return [game._task.cancel() for game in self.games]
