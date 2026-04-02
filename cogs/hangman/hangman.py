"""
Original Port Author: Flame442 (FlameCogs)
https://github.com/Flame442/FlameCogs/tree/master/hangman
Ported to discord.py specifically for KingBot & Kingshot (Century Games) Branding.
"""
import discord


from discord.ext import commands


from random import randint
import asyncio, os


class KingsExecution(commands.Cog):
	"""Play Kings Execution! Guess the password to save the peasant."""
	def __init__(self, bot):
		self.bot = bot
		self.doEdit = True
		self.man = [
			(
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |       \n'
				'   |       \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |   |   \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|  \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |       \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  /    \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   O   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  / \\ \n'
				'   |       \n'
			), (
				'    ___    \n'
				'   |   |   \n'
				'   |   X   \n'
				'   |  \\|/ \n'
				'   |   |   \n'
				'   |  / \\ \n'
				'   |       \n'
			)
		]

	@staticmethod
	def _get_message(word, guessed):
		"""Returns a string of the guessing text."""
		p = ''
		for l in word:
			if l not in 'abcdefghijklmnopqrstuvwxyz': #auto print non letter characters
				p += l + ' '
			elif l in guessed: #print already guessed characters
				p += l + ' '
			else:
				p += '_ ' 
		p += '    ('
		for l in guessed:
			if l not in word:
				p += l #add the incorrect guessed letters
		p += ')'
		return p

	@commands.command(aliases=["hangman"])
	async def execution(self, ctx):
		"""Play Kings Execution! Guess the password to save the peasant."""

		try:
			fp = os.path.join(os.path.dirname(__file__), 'data', 'words.txt')
			f = open(fp)
		except FileNotFoundError:
			await ctx.send("The King's dictionary is missing!")
			return
		wordlist = [line.strip().lower() for line in f]
		word = wordlist[randint(0,len(wordlist)-1)] #pick and format random word
		guessed = ''
		fails = 0
		game = True
		err = 0
		boardmsg = None
		check = lambda m: (
			m.channel == ctx.message.channel 
			and m.author == ctx.message.author 
			and len(m.content) == 1 
			and m.content.lower() in 'abcdefghijklmnopqrstuvwxyz'
		)
		while game:
			p = self._get_message(word, guessed)
			p = f'```{self.man[fails]}\n{p}```'
			if err == 1:
				p += 'You already guessed that letter, fool!\n'
			if boardmsg is None or not doEdit:
				boardmsg = await ctx.send(p+'Guess:')
			else:
				await boardmsg.edit(content=str(p+'Guess:'))
			try:
				umsg = await self.bot.wait_for('message', check=check, timeout=60)
			except asyncio.TimeoutError:
				return await ctx.send(
					f'Canceling selection. You took too long. The execution proceeds.\nThe word was {word}.'
				)
			t = umsg.content.lower()
			if doEdit:
				await asyncio.sleep(.2)
				try:
					await umsg.delete()
				except (discord.errors.Forbidden, discord.errors.NotFound):
					pass
			if t in guessed:
				err = 1
				continue
			err = 0
			guessed += t
			if t not in word:
				fails += 1
				if fails == 6: #too many fails
					p = self._get_message(word, guessed)
					p = f'```{self.man[fails]}\n{p}```The guillotine drops! Execution complete.\nThe word was {word}.'
					if doEdit:
						await boardmsg.edit(content=p)
					else:
						await ctx.send(p)
					game = False
					continue
			#guessed entire word
			if not (set('abcdefghijklmnopqrstuvwxyz') & set(word)) - set(guessed):
				p = self._get_message(word, guessed)
				p = f"```\n{self.man[fails]}\n{p}```You guessed the King's password and spared the peasant!\nThe word was {word}."
				if doEdit:
					await boardmsg.edit(content=p)
				else:
					await ctx.send(p)
				game = False
	

