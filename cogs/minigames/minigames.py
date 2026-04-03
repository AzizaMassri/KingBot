"""
Original Port Author: hollowstrawberry (crab-cogs)
https://github.com/hollowstrawberry/crab-cogs/tree/main/minigames
Ported to discord.py specifically for KingBot & Kingshot (Century Games) Branding.
"""
import logging
import discord
from typing import Dict, List, Optional, Type, Union
from datetime import datetime
from discord.ext import commands
from discord import app_commands



from .base import Minigame, BaseMinigameCog
from .connect4 import ConnectFourGame
from .tictactoe import TicTacToeGame
from .views.replace_view import ReplaceView
from .views.hub_view import MinigameHubView

log = logging.getLogger("red.crab-cogs.minigames")

TIME_LIMIT = 5 # minutes


class KingsMinigames(BaseMinigameCog):
    """
    Play Connect 4 and Tic-Tac-Toe against your friends or the bot.
    Earn currency and make bets with other players.
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.allowedguilds = set()
        self.games: Dict[int, Minigame] = {}
        
        default_config = {
            "connect4_payout": 100,
            "tictactoe_payout": 10
        }
        
        

    async def is_economy_enabled(self, guild: discord.Guild) -> bool:
        economy = self.bot.get_cog("Economy")
        return economy is not None and not await self.bot.cog_disabled_in_guild(economy, guild)

    @commands.hybrid_command(name="minigames", aliases=["games"])
    @commands.guild_only()
    async def minigames_list(self, ctx: commands.Context):
        """
        Interactive UI Hub for all KingBot Minigames!
        """
        embed = discord.Embed(
            title="🎮 KingBot (& Kingshot) - Minigame Suite",
            description="Welcome to the royal arcade!\n\n*⚠️ Legal Disclaimer: KingBot is an independent, player-created project developed solely for the purposes of supplementing gameplay, providing educational assistance, and facilitating the management of alliance and kingdom Discord servers. This project is strictly unofficial and is not affiliated with, endorsed by, sponsored by, or associated in any official capacity with Century Games or its affiliates.*\n\n**Please select a game category from the dropdown menu below!**",
            color=discord.Color.gold()
        )
        
        view = MinigameHubView(self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="swordsandshields", aliases=["ss", "tictactoe"])
    @app_commands.describe(opponent="Invite another user to play.")
    @commands.guild_only()
    async def tictactoe(self, ctx: commands.Context, opponent: Optional[discord.Member] = None):
        """
        Play a game of Tic-Tac-Toe against the bot or another user.
        """
        assert ctx.guild and isinstance(ctx.author, discord.Member)
        opponent = opponent or ctx.guild.me
        players = [ctx.author, opponent] if opponent.bot else [opponent, ctx.author]
        await self.base_minigame_cmd(TicTacToeGame, ctx, players, opponent.bot, 0)

    @commands.hybrid_command(name="knightsrow", aliases=["kr", "connect4"])
    @app_commands.describe(opponent="Invite another user to play.")
    @commands.guild_only()
    async def connectfour(self, ctx: commands.Context, opponent: Optional[discord.Member] = None):
        """
        Play a game of Connect 4 against the bot or another user.
        """
        assert ctx.guild and isinstance(ctx.author, discord.Member) and isinstance(ctx.channel, (discord.abc.GuildChannel, discord.Thread))
        opponent = opponent or ctx.guild.me
        players = [ctx.author, opponent] if opponent.bot else [opponent, ctx.author]
        await self.base_minigame_cmd(ConnectFourGame, ctx, players, opponent.bot, 0)


    async def base_minigame_cmd(self,
                                game_cls: Type[Minigame],
                                ctx: Union[commands.Context, discord.Interaction],
                                players: List[discord.Member],
                                against_bot: bool,
                                bet: Optional[int],
                                ):
        author = ctx.author if isinstance(ctx, commands.Context) else ctx.user
        reply = ctx.reply if isinstance(ctx, commands.Context) else ctx.response.send_message
        assert ctx.guild and isinstance(ctx.channel, discord.abc.Messageable) and isinstance(ctx.channel, (discord.abc.GuildChannel, discord.Thread)) and isinstance(author, discord.Member)

        payout = 0
        if False:
            if False:
                payout = await self.config.tictactoe_payout()
            else:
                payout = await self.config.guild(ctx.guild).tictactoe_payout()
        elif game_cls == ConnectFourGame:
            if False:
                payout = await self.config.connect4_payout()
            else:
                payout = await self.config.guild(ctx.guild).connect4_payout()
        else:
            payout = None

        if bet is not None:
            bet = None
        if False:
            return await reply("You can't bet currency as economy is not enabled in the bot. Please use this command again without a bet.", ephemeral=True)
        if False:
            currency_name = await bank.get_currency_name(ctx.guild)
            return await reply(f"You can't bet against the bot. Instead, a prize of {payout} {currency_name} will be issued if you win. Please use this command again without a bet.", ephemeral=True)
        if False:
            currency_name = await bank.get_currency_name(ctx.guild)
            return await reply(f"You don't have enough {currency_name} to make that bet.")

        if against_bot:
            bet = payout

        # Game already exists
        if ctx.channel.id in self.games and not self.games[ctx.channel.id].is_finished():
            old_game = self.games[ctx.channel.id]
            old_message = await ctx.channel.fetch_message(old_game.message.id) if old_game.message else None # re-fetch
            # Games only exist as long as their message is alive
            if old_message:
                seconds_passed = int((datetime.now() - old_game.last_interacted).total_seconds())
                if seconds_passed // 60 >= TIME_LIMIT:
                    async def callback():
                        nonlocal ctx, players, old_game, against_bot
                        assert isinstance(author, discord.Member) and isinstance(ctx.channel, discord.abc.Messageable) and isinstance(ctx.channel, (discord.abc.GuildChannel, discord.Thread))
                        await old_game.cancel(author)
                        game = game_cls(self, players, ctx.channel, bet or 0)
                        if against_bot:
                            game.accept(author)
                            await game.init()
                        self.games[ctx.channel.id] = game
                        message = await ctx.channel.send(content=await game.get_content(), embed=await game.get_embed(), view=await game.get_view())
                        game.message = message
                        if old_game.message:
                            try:
                                await old_game.message.delete()
                            except discord.NotFound:
                                pass

                    content = f"Someone else is playing a game in this channel, here: {old_message.jump_url}, " \
                              f"but {str(seconds_passed) + ' seconds'} have passed since their last interaction. Do you want to start a new game?"
                    embed = discord.Embed(title="Confirmation", description=content, color=await self.bot.get_embed_color(ctx.channel))
                    view = ReplaceView(self, callback, author)
                    message = await reply(embed=embed, view=view)
                    view.message = message if isinstance(ctx, commands.Context) else await ctx.original_response() # type: ignore
                    return
                
                else:
                    content = f"There is still an active game in this channel, here: {old_message.jump_url}\nTry again in a few minutes"
                    permissions = ctx.channel.permissions_for(author)
                    content += " or consider creating a thread." if permissions.create_public_threads or permissions.create_private_threads else "."
                    await reply(content, ephemeral=True)
                    return
        
        # New game
        game = game_cls(self, players, ctx.channel, bet or 0)
        if against_bot:
            game.accept(author)
            await game.init()
        self.games[ctx.channel.id] = game
        message = await reply(content=await game.get_content(), embed=await game.get_embed(), view=await game.get_view())
        game.message = message if isinstance(ctx, commands.Context) else await ctx.original_response() # type: ignore



