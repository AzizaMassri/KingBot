"""
Original Port Author: Flame442 (FlameCogs)
https://github.com/Flame442/FlameCogs/tree/master/monopoly
Ported to discord.py specifically for KingBot & Kingshot (Century Games) Branding.
"""
import discord
from discord.ext import commands
import json


from typing import Union
import asyncio, os

def humanize_list(items):
    if len(items) == 0: return ''
    if len(items) == 1: return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]

def pagify(text, shorten_by=8):
    # Extremely basic pagify
    pages = []
    while len(text) > 2000 - shorten_by:
        idx = text.rfind('\n', 0, 2000 - shorten_by)
        if idx == -1: idx = 2000 - shorten_by
        pages.append(text[:idx])
        text = text[idx:]
    if text: pages.append(text)
    return pages

async def menu(ctx, pages, controls=None):
    for i, p in enumerate(pages):
        await ctx.send(p) # Basic dump instead of heavy pagination

class BasicConfig:
    def __init__(self, bot):
        self.bot = bot
        self.filename = os.path.join(os.path.dirname(__file__), 'data', 'monopoly_data.json')
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {}

    def _save(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def _guild(self, guild):
        gid = str(guild.id)
        if gid not in self.data:
            self.data[gid] = {
                'doMention': False,
                'startCash': 1500,
                'incomeValue': 200,
                'luxuryValue': 100,
                'doAuction': True,
                'bailValue': 50,
                'maxJailRolls': 3,
                'doDoubleGo': False,
                'goValue': 200,
                'freeParkingValue': None,
                'hotelLimit': 12,
                'houseLimit': 32,
                'timeoutValue': 60,
                'minRaise': 1,
                'darkMode': False,
                'useThreads': False,
                'saves': {}
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

    class SavesConf:
        def __init__(self, conf, guild):
            self.conf = conf
            self.guild = guild
        async def __call__(self):
            return self.conf._guild(self.guild)['saves']
        async def __aenter__(self):
            return self.conf._guild(self.guild)['saves']
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self.conf._save()

    def guild(self, guild):
        class GuildConf:
            def __init__(self, conf, g):
                self.conf = conf
                self.g = g
            async def all(self):
                return self.conf._guild(self.g)
            @property
            def doMention(self): return conf.ConfigVal('doMention', self.conf, self.g)
            @property
            def startCash(self): return conf.ConfigVal('startCash', self.conf, self.g)
            @property
            def incomeValue(self): return conf.ConfigVal('incomeValue', self.conf, self.g)
            @property
            def luxuryValue(self): return conf.ConfigVal('luxuryValue', self.conf, self.g)
            @property
            def doAuction(self): return conf.ConfigVal('doAuction', self.conf, self.g)
            @property
            def bailValue(self): return conf.ConfigVal('bailValue', self.conf, self.g)
            @property
            def maxJailRolls(self): return conf.ConfigVal('maxJailRolls', self.conf, self.g)
            @property
            def doDoubleGo(self): return conf.ConfigVal('doDoubleGo', self.conf, self.g)
            @property
            def goValue(self): return conf.ConfigVal('goValue', self.conf, self.g)
            @property
            def freeParkingValue(self): return conf.ConfigVal('freeParkingValue', self.conf, self.g)
            @property
            def hotelLimit(self): return conf.ConfigVal('hotelLimit', self.conf, self.g)
            @property
            def houseLimit(self): return conf.ConfigVal('houseLimit', self.conf, self.g)
            @property
            def timeoutValue(self): return conf.ConfigVal('timeoutValue', self.conf, self.g)
            @property
            def minRaise(self): return conf.ConfigVal('minRaise', self.conf, self.g)
            @property
            def darkMode(self): return conf.ConfigVal('darkMode', self.conf, self.g)
            @property
            def useThreads(self): return conf.ConfigVal('useThreads', self.conf, self.g)
            def saves(self): return conf.SavesConf(self.conf, self.g)
        conf = self
        return GuildConf(conf, guild)

from .game import MonopolyGame
from .views import GetPlayersView


class Monopoly(commands.Cog):
	"""Play monopoly with 2-8 people."""
	def __init__(self, bot):
		self.bot = bot
		self.games = []
		self.config = BasicConfig(bot)

	@commands.guild_only()
	@commands.group(invoke_without_command=True) 
	async def monopoly(self, ctx, savefile: str=None):
		"""
		Play monopoly with 2-8 people.
		
		Use the optional parameter "savefile" to load a saved game.
		"""
		if [game for game in self.games if game.channel == ctx.channel]:
			return await ctx.send('A game is already running in this channel.')
		channel = ctx.channel
		startCash = await self.config.guild(ctx.guild).startCash()
		if savefile is not None:
			saves = await self.config.guild(ctx.guild).saves()
			if savefile not in saves:
				return await ctx.send(
					'There is no save file with that name.\n'
					'Is it saved in another guild?\n'
					f'Use `{ctx.prefix}monopoly list` to list save files.'
				)
			data = saves[savefile]
			if ctx.author.id not in data['uid']:
				return await ctx.send('You are not a player in that game!')
			initial_message = await ctx.send(f'Using save file `{savefile}`')
			if (
				await self.config.guild(ctx.guild).useThreads()
				and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
				and ctx.channel.type is discord.ChannelType.text
			):
				try:
					channel = await initial_message.create_thread(
						name='Monopoly',
						reason='Automated thread for Monopoly.',
					)
				except discord.HTTPException:
					pass
			game = MonopolyGame(ctx, channel, data=data)
			self.games.append(game)
		else:
			view = GetPlayersView(ctx, 8)
			initial_message = await ctx.send(view.generate_message(), view=view)
			if (
				await self.config.guild(ctx.guild).useThreads()
				and ctx.channel.permissions_for(ctx.guild.me).create_public_threads
				and ctx.channel.type is discord.ChannelType.text
			):
				try:
					channel = await initial_message.create_thread(
						name='Monopoly',
						reason='Automated thread for Monopoly.',
					)
				except discord.HTTPException:
					pass
			await view.wait()
			players = view.players
			if len(players) < 2:
				return await channel.send('Nobody else wants to play, shutting down.')
			uid = []
			for player in players[:8]:
				if isinstance(player, discord.Member):
					uid.append(player.id)
				else:
					uid.append(player)
			if [game for game in self.games if game.ctx.channel == ctx.channel]:
				return await channel.send('Another game started in this channel while setting up.')
			game = MonopolyGame(ctx, channel, startCash=startCash, uid=uid)
			self.games.append(game)
	
	@monopoly.command(name='list')
	async def monopoly_list(self, ctx):
		"""List available save files."""
		saves = await self.config.guild(ctx.guild).saves()
		if not saves:
			return await ctx.send('There are no save files in this server.')
		savenames_in = '\n'.join(name for name in saves if ctx.author.id in saves[name]['uid'])
		savenames_out = '\n'.join(name for name in saves if ctx.author.id not in saves[name]['uid'])
		msg = ''
		if savenames_in:
			msg += f'\n[Saves you are in]\n{savenames_in}\n'
		if savenames_out:
			msg += f'\n[Saves you are not in]\n{savenames_out}\n'
		pages = [f'```ini{m}```' for m in pagify(msg, shorten_by=15)]
		c = DEFAULT_CONTROLS if len(pages) > 1 else {"\N{CROSS MARK}": close_menu}
		await menu(ctx, pages, c)		
	
	@commands.has_permissions(administrator=True)
	@monopoly.command()
	async def delete(self, ctx, *savefiles: str):
		"""
		Delete one or more save files.
		
		This cannot be undone.
		"""
		if not savefiles:
			return await ctx.send_help()
		success = []
		fail = []
		async with self.config.guild(ctx.guild).saves() as saves:
			for file in savefiles:
				if file not in saves:
					fail.append(file)
					continue
				del saves[file]
				success.append(file)
		msg = ''
		if success:
			msg += f'The following savefiles were deleted: `{humanize_list(success)}`\n'
		if fail:
			msg += f'The following savefiles were not found: `{humanize_list(fail)}`\n'
		await ctx.send(msg)

	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	@commands.command()
	async def monopolystop(self, ctx):
		"""Stop the game of monopoly in this channel."""
		wasGame = False
		for game in [g for g in self.games if g.channel == ctx.channel]:
			game._task.cancel()
			wasGame = True
		if wasGame: #prevents multiple messages if more than one game exists for some reason
			await ctx.send('The game was stopped successfully.')
		else:
			await ctx.send('There is no ongoing game in this channel.')
	
	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	@commands.group(invoke_without_command=True)
	async def monopolyset(self, ctx):
		"""Config options for monopoly."""
		await ctx.send_help()
		cfg = await self.config.guild(ctx.guild).all()
		msg = (
			'Hold auctions: {doAuction}\n'
			'Bail price: {bailValue}\n'
			'Double go: {doDoubleGo}\n'
			'Free parking reward: {freeParkingValue}\n'
			'Go reward: {goValue}\n'
			'Hotel Limit: {hotelLimit}\n'
			'House limit: {houseLimit}\n'
			'Income tax: {incomeValue}\n'
			'Luxury tax: {luxuryValue}\n'
			'Max jail rolls: {maxJailRolls}\n'
			'Mention on turn: {doMention}\n'
			'Minimum auction increase: {minRaise}\n'
			'Starting cash: {startCash}\n'
			'Timeout length: {timeoutValue}\n'
			'Dark mode: {darkMode}\n'
			'Game contained to a thread: {useThreads}\n'
		).format_map(cfg)
		await ctx.send(f'```py\n{msg}```')
	
	@monopolyset.command()
	async def auction(self, ctx, value: bool=None):
		"""
		Set if properties should be auctioned when passed on.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doAuction()
			if v:
				await ctx.send('Passed properties are being auctioned.')
			else:
				await ctx.send('Passed properties are not being auctioned.')
		else:
			await self.config.guild(ctx.guild).doAuction.set(value)
			if value:
				await ctx.send('Passed properties will be auctioned.')
			else:
				await ctx.send('Passed properties will not be auctioned.')
	
	@monopolyset.command()
	async def bail(self, ctx, value: int=None):
		"""
		Set how much bail should cost.
		
		Defaults to 50.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).bailValue()
			await ctx.send(f'Bail currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).bailValue.set(value)
			await ctx.send(f'Bail will now cost ${value}.')
	
	@monopolyset.command()
	async def darkmode(self, ctx, value: bool=None):
		"""
		Set if the board should be a darker varient.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).darkMode()
			if v:
				await ctx.send('The board is currently the darker version.')
			else:
				await ctx.send('The board is currently the lighter version.')
		else:
			await self.config.guild(ctx.guild).darkMode.set(value)
			if value:
				await ctx.send('The board will now be the darker version.')
			else:
				await ctx.send('The board will now be the lighter version.')
	
	@monopolyset.command()
	async def doublego(self, ctx, value: bool=None):
		"""
		Set if landing on go should double the amount of money given.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doDoubleGo()
			if v:
				await ctx.send('Go value is doubled when landed on.')
			else:
				await ctx.send('Go value is not doubled when landed on.')
		else:
			await self.config.guild(ctx.guild).doDoubleGo.set(value)
			if value:
				await ctx.send('Go value will now be doubled when landed on.')
			else:
				await ctx.send('Go value will no longer be doubled when landed on.')
	
	@monopolyset.command()
	async def freeparking(self, ctx, value: Union[int, str]=None):
		"""
		Set the reward for landing on free parking.
		
		Use an integer to set a static reward.
		Use "none" for no reward.
		Use "tax" to use the sum of taxes and fees as the reward.
		Defaults to none.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).freeParkingValue()
			if v is None:
				await ctx.send('There is currently no reward for landing on free parking.')
			elif v == 'tax':
				await ctx.send(
					'The reward for landing on free parking is currently '
					'the sum of taxes and fees.'
				)
			else:
				await ctx.send(f'The reward for landing on free parking is currently ${v}.')
		else:
			if isinstance(value, int):
				await self.config.guild(ctx.guild).freeParkingValue.set(value)
				await ctx.send(f'The reward for landing on free parking is now ${value}.')
			else:
				if value.lower() == 'none':
					await self.config.guild(ctx.guild).freeParkingValue.set(None)
					await ctx.send('There is now no reward for landing on free parking.')
				elif value.lower() == 'tax':
					await self.config.guild(ctx.guild).freeParkingValue.set('tax')
					await ctx.send(
						'The reward for landing on free parking is now '
						'the sum of taxes and fees.'
					)
				else:
					await ctx.send('That is not a valid value.')

				
	@monopolyset.command()
	async def go(self, ctx, value: int=None):
		"""
		Set the base value of passing go.
		
		Defaults to 200.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).goValue()
			await ctx.send(f'You currently get ${v} from passing go.')
		else:
			await self.config.guild(ctx.guild).goValue.set(value)
			await ctx.send(f'You will now get ${value} from passing go.')
	
	@monopolyset.command()
	async def hotellimit(self, ctx, value: int=None):
		"""
		Set a limit on the number of hotels that can be bought.
		
		Use -1 to disable the limit.
		Defaults to 12.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).hotelLimit()
			if v == -1:
				await ctx.send('There is currently no limit on the number of hotels.')
			else:
				await ctx.send(f'The hotel limit is currently set to {v}.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			await self.config.guild(ctx.guild).hotelLimit.set(value)
			if value == -1:
				await ctx.send('There is now no limit on the number of hotels.')
			else:
				await ctx.send(f'The hotel limit is now set to {value}.')
				
	@monopolyset.command()
	async def houselimit(self, ctx, value: int=None):
		"""
		Set a limit on the number of houses that can be bought.
		
		Use -1 to disable the limit.
		Defaults to 32.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).houseLimit()
			if v == -1:
				await ctx.send('There is currently no limit on the number of houses.')
			else:
				await ctx.send(f'The house limit is currently set to {v}.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			await self.config.guild(ctx.guild).houseLimit.set(value)
			if value == -1:
				await ctx.send('There is now no limit on the number of houses.')
			else:
				await ctx.send(f'The house limit is now set to {value}.')
	
	@monopolyset.command()
	async def income(self, ctx, value: int=None):
		"""
		Set how much Income Tax should cost.
		
		Defaults to 200.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).incomeValue()
			await ctx.send(f'Income Tax currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).incomeValue.set(value)
			await ctx.send(f'Income Tax will now cost ${value}.')
	
	@monopolyset.command()
	async def luxury(self, ctx, value: int=None):
		"""
		Set how much Luxury Tax should cost.
		
		Defaults to 100.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).luxuryValue()
			await ctx.send(f'Luxury Tax currently costs ${v}.')
		else:
			await self.config.guild(ctx.guild).luxuryValue.set(value)
			await ctx.send(f'Luxury Tax will now cost ${value}.')
	
	@monopolyset.command()
	async def maxjailrolls(self, ctx, value: int=None):
		"""
		Set the maximum number of rolls in jail before bail has to be paid.
		
		Defaults to 3.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).maxJailRolls()
			await ctx.send(f'The maximum number of rolls in jail is {v}.')
		elif value < 0:
			await ctx.send('Players cannot spend a negative number of turns in jail.')
		else:
			await self.config.guild(ctx.guild).maxJailRolls.set(value)
			await ctx.send(f'The maximum number of rolls in jail is now {value}.')
	
	@monopolyset.command()
	async def mention(self, ctx, value: bool=None):
		"""
		Set if players should be mentioned when their turn begins.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).doMention()
			if v:
				await ctx.send('Players are being mentioned when their turn begins.')
			else:
				await ctx.send('Players are not being mentioned when their turn begins.')
		else:
			await self.config.guild(ctx.guild).doMention.set(value)
			if value:
				await ctx.send('Players will be mentioned when their turn begins.')
			else:
				await ctx.send('Players will not be mentioned when their turn begins.')
	
	@monopolyset.command()
	async def minraise(self, ctx, value: int=None):
		"""
		Set the minimum raise in auctions.
		
		Defaults to 1.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).minRaise()
			await ctx.send(f'The minimum raise is ${v}.')
		elif value <= 0:
			return await ctx.send('The minimum raise must be positive.')
		else:
			await self.config.guild(ctx.guild).minRaise.set(value)
			await ctx.send(f'The minimum raise is now ${value}.')
	
	@monopolyset.command()
	async def startingcash(self, ctx, value: int=None):
		"""
		Set how much money players should start the game with.
		
		Defaults to 1500.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).startCash()
			await ctx.send(f'Players are starting with ${v}.')
		elif value < 0:
			return await ctx.send('Players cannot start the game in debt. This isn\'t real life.')
		else:
			await self.config.guild(ctx.guild).startCash.set(value)
			await ctx.send(f'Players will start with ${value}.')

	@monopolyset.command()
	async def thread(self, ctx, value: bool=None):
		"""
		Set if a thread should be created per-game to contain game messages.
		
		Defaults to False.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).useThreads()
			if v:
				await ctx.send('The game is currently run in a per-game thread.')
			else:
				await ctx.send('The game is not currently run in a thread.')
		else:
			await self.config.guild(ctx.guild).useThreads.set(value)
			if value:
				await ctx.send('The game will now be run in a per-game thread.')
			else:
				await ctx.send('The game will not be run in a thread.')
	
	@monopolyset.command()
	async def timeout(self, ctx, value: int=None):
		"""
		Set the amount of time before the game times out.
		
		Value is in seconds.
		Use -1 to disable the timeout.
		Defaults to 60.
		This value is server specific.
		"""
		if value is None:
			v = await self.config.guild(ctx.guild).timeoutValue()
			if v is None:
				await ctx.send('There is currently no timeout.')
			else:
				await ctx.send(f'The timeout is currently set to {v} seconds.')
		else:
			if value < -1:
				return await ctx.send('That is not a valid value.')
			if value == -1:
				await self.config.guild(ctx.guild).timeoutValue.set(None)
				await ctx.send('There is no longer a timeout.')
			else:
				await self.config.guild(ctx.guild).timeoutValue.set(value)
				await ctx.send(f'The timeout is now set to {value} seconds.')

	def cog_unload(self):
		return [game._task.cancel() for game in self.games]


