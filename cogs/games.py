import discord
from discord.ext import commands
import random
import asyncio
from cogs.economy import Economy
from cogs.utils.views import TranslatedView

class RaceLobbyView(TranslatedView):
    def __init__(self, host: discord.Member, bet: int, eco, animals, initial_animal: str):
        super().__init__(timeout=60.0)
        self.host = host
        self.bet = bet
        self.eco = eco
        self.animals = animals
        
        self.players = [host]
        self.racers = [initial_animal]
        self.player_names = [host.display_name]
        
    @discord.ui.button(label="Join Race", style=discord.ButtonStyle.success, emoji="🏇")
    async def join_race(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await self.send_translated(interaction, content="You are already in the race!", ephemeral=True)
            
        if len(self.players) >= 4:
            return await self.send_translated(interaction, content="The race is full!", ephemeral=True)
            
        if self.bet > 0 and await self.eco.get_balance(interaction.user.id) < self.bet:
            return await self.send_translated(interaction, content=f"You don't have enough Kingshot Bucks ({self.bet} needed)!", ephemeral=True)
            
        if self.bet > 0:
            await self.eco.remove_balance(interaction.user.id, self.bet)
            
        self.players.append(interaction.user)
        self.player_names.append(interaction.user.display_name)
        
        available_animals = [a for a in self.animals if a not in self.racers]
        chosen = random.choice(available_animals)
        self.racers.append(chosen)
        
        embed = interaction.message.embeds[0]
        desc = f"**Host:** {self.host.display_name}\n**Bet:** {self.bet} 💰\n\n**Racers ({len(self.players)}/4):**\n"
        for i in range(len(self.players)):
            desc += f"{self.racers[i]} {self.player_names[i]}\n"
        embed.description = desc
        
        if len(self.players) >= 4:
            self.stop()
            embed.title = "🏁 Race Starting! 🏁"
            await self.edit_translated(interaction, embed=embed, view=None)
        else:
            await self.edit_translated(interaction, embed=embed, view=self)

    @discord.ui.button(label="Start Now", style=discord.ButtonStyle.primary)
    async def start_early(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return await self.send_translated(interaction, content="Only the host can start the race early!", ephemeral=True)
        self.stop()
        embed = interaction.message.embeds[0]
        embed.title = "🏁 Race Starting! 🏁"
        await self.edit_translated(interaction, embed=embed, view=None)

class HeistLobbyView(TranslatedView):
    def __init__(self, host: discord.Member, cost: int, eco, title: str):
        super().__init__(timeout=60.0)
        self.host = host
        self.cost = cost
        self.eco = eco
        self.title = title
        
        self.players = [host]
        self.player_names = [host.display_name]
        
    @discord.ui.button(label="Join Heist", style=discord.ButtonStyle.danger, emoji="🐻")
    async def join_heist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await self.send_translated(interaction, content="You are already in the squad!", ephemeral=True)
            
        if len(self.players) >= 5:
            return await self.send_translated(interaction, content="The heist squad is full (max 5)!", ephemeral=True)
            
        if self.cost > 0 and await self.eco.get_balance(interaction.user.id) < self.cost:
            return await self.send_translated(interaction, content=f"You don't have enough Kingshot Bucks ({self.cost} needed)!", ephemeral=True)
            
        if self.cost > 0:
            await self.eco.remove_balance(interaction.user.id, self.cost)
            
        self.players.append(interaction.user)
        self.player_names.append(interaction.user.display_name)
        
        embed = interaction.message.embeds[0]
        desc = f"**Host:** {self.host.display_name}\n**Entry Cost:** {self.cost} 💰\n\n**Squad ({len(self.players)}/5):**\n"
        for name in self.player_names:
            desc += f"🐻 {name}\n"
        embed.description = desc
        
        if len(self.players) >= 5:
            self.stop()
            embed.title = f"🐻 Heist Starting: {self.title}"
            await self.edit_translated(interaction, embed=embed, view=None)
        else:
            await self.edit_translated(interaction, embed=embed, view=self)

    @discord.ui.button(label="Start Heist", style=discord.ButtonStyle.primary)
    async def start_early(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return await self.send_translated(interaction, content="Only the host can start the heist!", ephemeral=True)
        if len(self.players) < 2:
            return await self.send_translated(interaction, content="You need at least 2 bears (players) for a heist! Wait for others to join.", ephemeral=True)
            
        self.stop()
        embed = interaction.message.embeds[0]
        embed.title = f"🐻 Heist Starting: {self.title}"
        await self.edit_translated(interaction, embed=embed, view=None)

class HeistChoicesView(TranslatedView):
    def __init__(self, players, custom_choices, eco):
        super().__init__(timeout=45.0)
        self.players = players
        self.custom_choices = custom_choices
        self.eco = eco
        self.choices_made = {}
        
        for choice_name in custom_choices:
            btn = discord.ui.Button(label=choice_name, style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(choice_name)
            self.add_item(btn)

    def make_callback(self, choice_name):
        async def button_callback(interaction: discord.Interaction):
            if interaction.user not in self.players:
                return await self.send_translated(interaction, content="You are not part of this heist!", ephemeral=True)
            if interaction.user in self.choices_made:
                return await self.send_translated(interaction, content="You already made your choice!", ephemeral=True)
                
            self.choices_made[interaction.user] = choice_name
            await self.send_translated(interaction, content=f"You chose to: **{choice_name}**", ephemeral=True)
            
            if len(self.choices_made) >= sum(1 for p in self.players if not getattr(p, "bot", False)):
                self.stop()
                try:
                    await interaction.message.edit(view=None)
                except:
                    pass
        return button_callback

class RussianRouletteLobbyView(TranslatedView):
    def __init__(self, host: discord.Member, bet: int, eco):
        super().__init__(timeout=60.0)
        self.host = host
        self.bet = bet
        self.eco = eco
        self.players = [host]
        
    @discord.ui.button(label="Join Table", style=discord.ButtonStyle.danger, emoji="🔫")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await self.send_translated(interaction, content="You are already sitting at the table!", ephemeral=True)
            
        if len(self.players) >= 5:
            return await self.send_translated(interaction, content="The table is full (max 5)!", ephemeral=True)
            
        if self.bet > 0 and await self.eco.get_balance(interaction.user.id) < self.bet:
            return await self.send_translated(interaction, content=f"You don't have enough Kingshot Bucks ({self.bet} needed)!", ephemeral=True)
            
        if self.bet > 0:
            await self.eco.remove_balance(interaction.user.id, self.bet)
            
        self.players.append(interaction.user)
        
        embed = interaction.message.embeds[0]
        desc = f"**Host:** {self.host.display_name}\n**Buy-in:** {self.bet} 💰\n\n**Players ({len(self.players)}/5):**\n"
        for p in self.players:
            desc += f"👤 {p.display_name}\n"
        embed.description = desc
        
        if len(self.players) >= 5:
            self.stop()
            embed.title = "🔫 Russian Roulette Starting!"
            await self.edit_translated(interaction, embed=embed, view=None)
        else:
            await self.edit_translated(interaction, embed=embed, view=self)

    @discord.ui.button(label="Spin Cylinder (Start)", style=discord.ButtonStyle.primary)
    async def start_early(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            return await self.send_translated(interaction, content="Only the host can spin the cylinder to start!", ephemeral=True)
        if len(self.players) < 2:
            return await self.send_translated(interaction, content="You need somebody else to play with! 💀", ephemeral=True)
            
        self.stop()
        embed = interaction.message.embeds[0]
        embed.title = "🔫 Russian Roulette Starting!"
        await self.edit_translated(interaction, embed=embed, view=None)

class RussianRouletteGameView(TranslatedView):
    def __init__(self, players: list, bet: int, eco):
        super().__init__(timeout=30.0)
        self.players = players
        self.bet = bet
        self.eco = eco
        self.current_turn = 0
        self.bullet_chamber = random.randint(0, 5) # 6 shooter
        self.current_chamber = 0
        self.prize_pool = bet * len(players)
        
        # Funny commentary lines
        # Funny commentary lines
        self.survive_lines = [
            "*Click.* They sweat nervously, but survive.",
            "*Click.* \"I told you I was built different!\"",
            "*Click.* A sigh of relief echoes across the table.",
            "*Click.* The gun jams? Wait, no, just empty.",
            "*Click.* They stare death in the face and smile.",
            "*Click.* \"Easy money. Who's next?\"",
            "*Click.* They aggressively dab to assert dominance over death.",
            "*Click.* They let out a squeal that shatters glass, but live.",
            "*Click.* \"Did I win? Is it over? Can I go home?\"",
            "*Click.* They casually yawn. \"Boring.\"",
            "*Click.* They open one eye. Still alive? Nice.",
            "*Click.* They wipe sweat off their forehead with a trembling hand."
        ]
        
        self.die_lines = [
            "**BANG!** 💥 Brain soup. They're out.",
            "**BANG!** 💥 Right on the carpet. Someone get a mop.",
            "**BANG!** 💥 \"Wait I wasn't rea--\"",
            "**BANG!** 💥 Welp. Rest in pieces.",
            "**BANG!** 💥 Medic! Actually... don't bother.",
            "**BANG!** 💥 They folded like a lawn chair.",
            "**BANG!** 💥 Their soul immediately disconnected from the server.",
            "**BANG!** 💥 Boom, headshot! Someone clip that!",
            "**BANG!** 💥 Looks like they lost their mind! Literally.",
            "**BANG!** 💥 Does insurance cover that? Nope.",
            "**BANG!** 💥 They just got logged out of life.",
            "**BANG!** 💥 Press F to pay respects."
        ]

    async def update_board(self, interaction: discord.Interaction, extra_text=""):
        if len(self.players) == 1:
            # Winner!
            self.stop()
            winner = self.players[0]
            if self.bet > 0:
                await self.eco.add_balance(winner.id, self.prize_pool)
                extra_text += f"\n\n🏆 **{winner.display_name}** is the last one bleeding! They win the pot of **{self.prize_pool} 💰**!"
            else:
                extra_text += f"\n\n🏆 **{winner.display_name}** is the last one bleeding! They win absolutely nothing out of pure boredom!"
                
            embed = discord.Embed(
                title="🔫 Game Over",
                description=extra_text,
                color=discord.Color.gold()
            )
            return await self.edit_translated(interaction, embed=embed, view=None)

        # Loop turn to next active player
        self.current_turn = self.current_turn % len(self.players)
        current_player = self.players[self.current_turn]
        
        desc = extra_text + f"\n\nIt is **{current_player.display_name}'s** turn to pull the trigger!\n*(You have 30 seconds)*"
        embed = discord.Embed(
            title="🔫 Russian Roulette",
            description=desc,
            color=discord.Color.dark_red()
        )
        msg = await self.edit_translated(interaction, embed=embed, view=self)
        
        if getattr(current_player, "bot", False):
            # Let the bot spin in 2 seconds
            asyncio.create_task(self.bot_action(msg))

    async def bot_action(self, msg):
        await asyncio.sleep(2.0)
        await self.pull_trigger_logic(None)

    @discord.ui.button(label="Pull Trigger", style=discord.ButtonStyle.danger, emoji="💥")
    async def pull_trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_player = self.players[self.current_turn]
        
        if interaction.user != current_player:
            return await self.send_translated(interaction, content="It is NOT your turn! Don't be so eager to die.", ephemeral=True)
            
        await self.pull_trigger_logic(interaction)

    async def pull_trigger_logic(self, interaction: discord.Interaction):
        current_player = self.players[self.current_turn]
            
        # Check chamber
        if self.current_chamber == self.bullet_chamber:
            # Player dies
            dead_player = self.players.pop(self.current_turn)
            flavor = random.choice(self.die_lines)
            
            # Respin cylinder since someone died
            self.bullet_chamber = random.randint(0, 5)
            self.current_chamber = 0
            
            result_text = f"**{dead_player.display_name}** puts the gun to their head and pulls...\n{flavor}\n*(The cylinder has been spun again...)*"
        else:
            # Player lives
            flavor = random.choice(self.survive_lines)
            result_text = f"**{current_player.display_name}** puts the gun to their head and pulls...\n{flavor}\n*(The cylinder is spun again...)*"
            
            # Respin cylinder after survival so it's a 1/6 chance every pull
            self.bullet_chamber = random.randint(0, 5)
            self.current_chamber = 0
            self.current_turn += 1
            
        if interaction:
            await self.update_board(interaction, result_text)
        else:
            # Bot action uses a manual edit because there's no interaction context
            await self.update_board_manual(result_text)

    async def update_board_manual(self, extra_text=""):
        if len(self.players) == 1:
            self.stop()
            winner = self.players[0]
            if self.bet > 0:
                await self.eco.add_balance(winner.id, self.prize_pool)
                extra_text += f"\n\n🏆 **{winner.display_name}** is the last one bleeding! They win the pot of **{self.prize_pool} 💰**"
            else:
                extra_text += f"\n\n🏆 **{winner.display_name}** is the last one bleeding! They win absolutely nothing!"
            embed = discord.Embed(title="🔫 Game Over", description=extra_text, color=discord.Color.gold())
            if self.message:
                return await self.message.edit(embed=embed, view=None)
            
        self.current_turn = self.current_turn % len(self.players)
        current_player = self.players[self.current_turn]
        desc = extra_text + f"\n\nIt is **{current_player.display_name}'s** turn to pull the trigger!\n*(You have 30 seconds)*"
        embed = discord.Embed(title="🔫 Russian Roulette", description=desc, color=discord.Color.dark_red())
        if self.message:
            await self.message.edit(embed=embed, view=self)
        if getattr(current_player, "bot", False):
            asyncio.create_task(self.bot_action(None))

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.animals = [
            "🚀", "🛸", "🛰️", "☄️", "🌌", "👨‍🚀", "👽", "🔭", "🪐", "🌠", 
            "🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "⭐", "🌟",
            "💫", "🌞", "🌝", "🪐", "🛸", "🚀", "🛰️", "☄️", "🌌", "👨‍🚀"
        ]
        
    @property
    def eco(self):
        return self.bot.get_cog("Economy")

    def render_track(self, racers, positions, track_length, player_names):
        track_str = "🏁 **The Great Space Race!** 🏁\n\n"
        max_name_len = max([len(n) for n in player_names]) if player_names else 0
        
        for i, racer in enumerate(racers):
            pos = positions[i]
            line = ""
            for j in range(track_length):
                if j == pos:
                    line += racer
                else:
                    line += "—"
            line += " 🏁"
            
            name = player_names[i].rjust(max_name_len)
            track_str += f"`{name}` | {line}\n"
        return track_str

    @commands.command(name="race")
    async def race_command(self, ctx, arg1: str = None, arg2: int = None):
        """Host a multiplayer space race! Others can join. Example: `!race 🚀 100`"""
        user_id = ctx.author.id

        my_animal = None
        bet = 0

        # Parse arguments
        if arg1 is not None and arg2 is not None:
            my_animal = arg1
            bet = arg2
        elif arg1 is not None:
            if arg1.isdigit():
                bet = int(arg1)
            else:
                my_animal = arg1

        if bet < 0:
            return await ctx.send("❌ Nice try, no negative bets allowed.")
            
        if await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to make that bet!")
            
        if my_animal and my_animal not in self.animals:
            return await ctx.send(f"❌ '{my_animal}' is not a valid space racer! Try one of these: {' '.join(self.animals[:5])}...")
            
        if not my_animal:
            my_animal = random.choice(self.animals)

        # Deduct host bet
        if bet > 0:
            await self.eco.remove_balance(user_id, bet)

        embed = discord.Embed(
            title="🏁 Multiplayer Race Lobby 🏁",
            description=f"**Host:** {ctx.author.display_name}\n**Bet:** {bet} 💰\n\n⏳ *Waiting for others to join! Click the button! (60s)*\n\n**Racers (1/4):**\n{my_animal} {ctx.author.display_name}\n",
            color=discord.Color.green()
        )
        
        view = RaceLobbyView(ctx.author, bet, self.eco, self.animals, my_animal)
        msg = await ctx.send(embed=embed, view=view)
        
        await view.wait()
        
        players = view.players
        player_names = view.player_names
        racers = view.racers
        
        num_racers = len(players)
        # Add bot players if needed to make it at least 4 racers for competition
        while num_racers < 4:
            bot_animal = random.choice([a for a in self.animals if a not in racers])
            racers.append(bot_animal)
            player_names.append(f"Bot {num_racers}")
            num_racers += 1

        track_length = 20
        positions = [0] * num_racers
        
        race_msg = await ctx.send(self.render_track(racers, positions, track_length, player_names))
        
        winner_idx = None
        
        # Race loop
        while winner_idx is None:
            await asyncio.sleep(1.5)
            for i in range(num_racers):
                move = random.choice([0, 1, 2])
                positions[i] += move
                if positions[i] >= track_length - 1:
                    positions[i] = track_length - 1
                    if winner_idx is None:
                        winner_idx = i
            
            await race_msg.edit(content=self.render_track(racers, positions, track_length, player_names))
            
            if winner_idx is not None:
                break
                
        winner_name = player_names[winner_idx]
        winner_animal = racers[winner_idx]
        
        win_msg = f"🎉 The winner is {winner_animal} **{winner_name}**! 🎉"
        
        # Handle payouts
        if bet > 0:
            if winner_idx < len(players): # A real player won
                winnings = bet * num_racers # Winner takes all pool (including bots!)
                winner_id = players[winner_idx].id
                new_bal = await self.eco.add_balance(winner_id, winnings)
                win_msg += f"\n💰 **{winner_name}** won the prize pool and earned **{winnings} Bucks**! (New Balance: {new_bal})"
            else:
                win_msg += f"\n💸 The bot won! Everyone lost their bet of {bet} Bucks. Better luck next time!"

        # Tag the losers
        loser_mentions = [p.mention for i, p in enumerate(players) if i != winner_idx]
        if loser_mentions:
            win_msg += f"\n\n💀 Better luck next time, losers: {' '.join(loser_mentions)}"

        await ctx.send(win_msg)

    @commands.command(name="heist", aliases=["raid"])
    async def bear_raid(self, ctx, difficulty: int = None):
        """Host a multiplayer bear raid! Need 2+ players. `!heist 1-5`"""
        if not difficulty or difficulty < 1 or difficulty > 5:
            embed = discord.Embed(
                title="🐻 Heist Difficulties",
                description="Use `!heist <1-5>` to launch a raid! Higher difficulties have worse odds but incredible payouts!\n\n"
                            "```diff\n"
                            "+ Level 1: Peasant Village 🛖\n"
                            "  Cost: 50 | Win Chance: 75% | Reward: 60-130\n\n"
                            "+ Level 2: Knight's Fortress 🏰\n"
                            "  Cost: 150 | Win Chance: 60% | Reward: 200-450\n\n"
                            "+ Level 3: Baron's Keep 🛡️\n"
                            "  Cost: 500 | Win Chance: 45% | Reward: 800-1600\n\n"
                            "+ Level 4: King's Castle 👑\n"
                            "  Cost: 1500 | Win Chance: 30% | Reward: 2500-5500\n\n"
                            "+ Level 5: Emperor's Vault 🐉\n"
                            "  Cost: 5000 | Win Chance: 15% | Reward: 15k-55k\n"
                            "```",
                color=discord.Color.dark_red()
            )
            return await ctx.send(embed=embed)

        user_id = ctx.author.id

        heist_stories = {
            1: {
                "cost": 50, "win_chance": 75, "min_rew": 60, "max_rew": 130, "title": "Peasant Village 🛖",
                "story1": "The squad rolls up to a quiet village. There's an unguarded honey stash, but an angry farmer holds a pitchfork.",
                "choices1": {
                    "Eat Honey": {"mod": -10, "text": "Threw caution to the wind and gorged on honey! You're sticky, but energized!"},
                    "Ooga Booga": {"mod": 10, "text": "Hit 'em with the OOGA BOOGA! The farmer dropped his pitchfork and fled!"},
                    "Ninja Mode": {"mod": 5, "text": "Did a literal combat roll past the farmer. Very stealthy. Very cool."}
                },
                "story2": "You breached the town square! The village elder is guarding the piggy bank aggressively.",
                "choices2": {
                    "Flex Muscles": {"mod": 5, "rew_mult": 1.2, "text": "Flexed your biceps! The elder was so intimidated he handed over the keys."},
                    "Dance Off": {"mod": 15, "rew_mult": 1.0, "text": "Hit the Griddy! The elder respected the moves and let you pass!"},
                    "Dropkick Vault": {"mod": -15, "rew_mult": 2.0, "text": "Dropkicked the piggy bank! Shards and coins flew everywhere! Massive loot!"}
                }
            },
            2: {
                "cost": 150, "win_chance": 60, "min_rew": 200, "max_rew": 450, "title": "Knight's Fortress 🏰",
                "story1": "The squad reaches a stone fortress. A very smug knight refuses to let you cross the drawbridge.",
                "choices1": {
                    "Slap Knight": {"mod": 10, "text": "Walked up and slapped the knight! His armor rattled as he fell over!"},
                    "Catapult Toss": {"mod": -5, "text": "Loaded yourselves into a catapult and yeeted over the wall!"},
                    "Yell Insults": {"mod": 5, "text": "Called him a tin can! He cried and ran away."}
                },
                "story2": "You're inside the keep! The armory is heavily locked, but the kitchen has an unattended roast turkey.",
                "choices2": {
                    "Raid Armory": {"mod": -10, "rew_mult": 2.0, "text": "Chewed through the locks and stole shiny, expensive swords!"},
                    "Eat Turkey": {"mod": 15, "rew_mult": 1.0, "text": "Ate the King's turkey! The squad is absolutely vibing now."},
                    "Steal the Chef": {"mod": 0, "rew_mult": 1.5, "text": "Kidnapped the royal chef for a ransom! High IQ play."}
                }
            },
            3: {
                "cost": 500, "win_chance": 45, "min_rew": 800, "max_rew": 1600, "title": "Baron's Keep 🛡️",
                "story1": "The Baron is throwing a massive, pretentious VIP party. There are bouncers at the door.",
                "choices1": {
                    "Crash Party": {"mod": 10, "text": "Kicked the door off its hinges and ruined the DJ's set!"},
                    "Fake ID": {"mod": 5, "text": "Showed a completely fake driver's license. The bouncer bought it!"},
                    "Raid Buffet": {"mod": -5, "text": "Fought three nobles simply to eat their caviar. Worth it!"}
                },
                "story2": "The Baron's elite SWAT guards swarm the hallways, tasers drawn!",
                "choices2": {
                    "Matrix Dodge": {"mod": -15, "rew_mult": 2.5, "text": "Dodged the tasers in slow-motion and looted the secret vault!"},
                    "Defenestration": {"mod": 20, "rew_mult": 1.0, "text": "Threw yourself out a glass window to escape with whatever you had!"},
                    "Flashbang": {"mod": 0, "rew_mult": 1.5, "text": "Tossed a flashbang, totally blinding them while you emptied the register!"}
                }
            },
            4: {
                "cost": 1500, "win_chance": 30, "min_rew": 2500, "max_rew": 5500, "title": "King's Castle 👑",
                "story1": "The King's royal guards are completely armed to the teeth, blocking the golden gates.",
                "choices1": {
                    "Berserker Rage": {"mod": 10, "text": "Went completely feral! The guards screamed and abandoned their posts!"},
                    "Give Bitcoin": {"mod": -5, "text": "Bribed them with crypto. They let you in while checking their portfolios!"},
                    "Sewer Pipe": {"mod": 5, "text": "Crawled through a literal sewer pipe. You smell awful, but you're in."}
                },
                "story2": "You reached the Royal Treasury! The King himself is throwing literal gold bars to stop you!",
                "choices2": {
                    "Catch Gold": {"mod": -10, "rew_mult": 2.0, "text": "Caught the flying gold bars with your teeth like an absolute unit!"},
                    "Tackle King": {"mod": -20, "rew_mult": 3.0, "text": "Spear-tackled the King through a table and stole his Rolex!"},
                    "Vacuum Cleaner": {"mod": 10, "rew_mult": 1.2, "text": "Pulled out an industrial vacuum and sucked up all the loose gems!"}
                }
            },
            5: {
                "cost": 5000, "win_chance": 15, "min_rew": 15000, "max_rew": 55000, "title": "Emperor's Vault 🐉",
                "story1": "A massive, breathing dragon guards the Emperor's Vault! It stares at you, preparing to breathe fire.",
                "choices1": {
                    "Offer Scooby Snack": {"mod": 20, "text": "Tossed a single Scooby Snack. The dragon wagged its tail and ate it!"},
                    "Suplex Dragon": {"mod": -10, "text": "Grabbed the dragon by the tail and suplexed it! Anime style!"},
                    "Play Dead": {"mod": 5, "text": "Dropped to the floor and played dead. The dragon got bored and slept."}
                },
                "story2": "The dragon's fire breath accidentally melted the vault door open! The alarm is blaring!",
                "choices2": {
                    "Loot in the Fire": {"mod": -25, "rew_mult": 4.0, "text": "Ran straight through roaring flames! Singed eyebrows, but legendary payout!"},
                    "Call an Uber": {"mod": 15, "rew_mult": 1.1, "text": "Grabbed whatever was closest and immediately called an Uber out of there!"},
                    "Fire Extinguisher": {"mod": 0, "rew_mult": 2.0, "text": "Sprayed an extinguisher everywhere, blinding the guards while you shoved diamonds in your pockets!"}
                }
            }
        }


        level = heist_stories[difficulty]
        cost = level["cost"]

        if await self.eco.get_balance(user_id) < cost:
            return await ctx.send(f"❌ You need **{cost} Kingshot Bucks** to host this {level['title']} raid!")

        await self.eco.remove_balance(user_id, cost)

        embed = discord.Embed(
            title=f"🐻 Multiplayer Heist Lobby: {level['title']}",
            description=f"**Host:** {ctx.author.display_name}\n**Entry Cost:** {cost} 💰\n\n⏳ *Waiting for squad members to join! Click the button! (60s)*\n\n**Squad (1/5):**\n🐻 {ctx.author.display_name}\n",
            color=discord.Color.dark_red()
        )

        view = HeistLobbyView(ctx.author, cost, self.eco, level['title'])
        msg = await ctx.send(embed=embed, view=view)
        
        await view.wait()
        
        players = view.players
        
        if len(players) < 2:
            players.append(ctx.guild.me)
            await ctx.send(f"🤖 Not enough humans joined, so **{ctx.guild.me.display_name}** stepped in to help pull off the heist!")

        # PHASE 1
        story1_embed = discord.Embed(
            title=f"⚔️ Phase 1: {level['title']}",
            description=f"*{level['story1']}*\n\n**Every player must make their own choice below!**",
            color=discord.Color.blue()
        )
        
        choices_view1 = HeistChoicesView(players, level["choices1"], self.eco)
        story1_msg = await ctx.send(embed=story1_embed, view=choices_view1)
        await choices_view1.wait()

        # Disable buttons on phase 1 message gracefully
        for child in choices_view1.children:
            child.disabled = True
        try:
            await story1_msg.edit(view=choices_view1)
        except: pass

        # PHASE 2
        story2_embed = discord.Embed(
            title=f"⚔️ Phase 2: {level['title']}",
            description=f"*{level['story2']}*\n\n**Every player must make their own choice below!**",
            color=discord.Color.purple()
        )
        choices_view2 = HeistChoicesView(players, level["choices2"], self.eco)
        story2_msg = await ctx.send(embed=story2_embed, view=choices_view2)
        await choices_view2.wait()
        
        for child in choices_view2.children:
            child.disabled = True
        try:
            await story2_msg.edit(view=choices_view2)
        except: pass

        # Resolve outcomes individually
        results_desc = ""
        for p in players:
            # Phase 1 pick
            c1_name = choices_view1.choices_made.get(p)
            if not c1_name:
                c1_name = random.choice(list(level["choices1"].keys()))
                results_desc += f"💤 **{p.display_name}** fell asleep in Part 1 and blindly did: **{c1_name}**...\n"
                
            # Phase 2 pick
            c2_name = choices_view2.choices_made.get(p)
            if not c2_name:
                c2_name = random.choice(list(level["choices2"].keys()))
                results_desc += f"💤 **{p.display_name}** fell asleep in Part 2 and blindly did: **{c2_name}**...\n"
                
            c1_data = level["choices1"][c1_name]
            c2_data = level["choices2"][c2_name]
            
            win_chance = level["win_chance"] + c1_data["mod"] + c2_data["mod"]
            
            roll = random.randint(1, 100)
            if roll <= win_chance:
                base_reward = random.randint(level["min_rew"], level["max_rew"])
                reward = int(base_reward * c2_data["rew_mult"])
                await self.eco.add_balance(p.id, reward)
                results_desc += f"✅ **{p.display_name}**\n*Phase 1:* {c1_data['text']}\n*Phase 2:* {c2_data['text']}\n🏆 **Escaped with +{reward} 💰!**\n\n"
            else:
                results_desc += f"❌ **{p.display_name}**\n*Phase 1:* {c1_data['text']}\n*Phase 2:* {c2_data['text']}\n🚔 **Busted! Chased out & lost {cost} 💰!**\n\n"
                
        results_embed = discord.Embed(
            title="🏆 Heist Results",
            description=results_desc,
            color=discord.Color.gold()
        )
        await ctx.send(embed=results_embed)

    @commands.command(name="roulette")
    async def roulette_command(self, ctx, bet: int = 0):
        """Host a game of Russian Roulette! Up to 5 players. Example: `!roulette 100`"""
        user_id = ctx.author.id

        if bet < 0:
            return await ctx.send("❌ Negative bets aren't allowed. Try again.")
            
        if bet > 0 and await self.eco.get_balance(user_id) < bet:
            return await ctx.send("❌ You don't have enough Kingshot Bucks to host that buy-in!")

        # Deduct host bet initially
        if bet > 0:
            await self.eco.remove_balance(user_id, bet)

        embed = discord.Embed(
            title="🔫 Russian Roulette Lobby",
            description=f"**Host:** {ctx.author.display_name}\n**Buy-in:** {bet} 💰\n\n⏳ *Waiting for victims to join! (60s)*\n\n**Players (1/5):**\n👤 {ctx.author.display_name}\n",
            color=discord.Color.dark_red()
        )
        
        lobby_view = RussianRouletteLobbyView(ctx.author, bet, self.eco)
        msg = await ctx.send(embed=embed, view=lobby_view)
        
        await lobby_view.wait()
        
        players = lobby_view.players
        
        if len(players) < 2:
            players.append(ctx.guild.me)
            await ctx.send(f"🤖 Not enough victims joined, so **{ctx.guild.me.display_name}** sits down at the table!")

        # Shuffle player order
        random.shuffle(players)
        
        game_view = RussianRouletteGameView(players, bet, self.eco)
        
        start_embed = discord.Embed(
            title="🔫 Russian Roulette Starting",
            description=f"The cylinder is loaded with 1 bullet and 5 empty chambers.\nThe cylinder is given a harsh spin and slammed shut.\n\nIt is **{players[0].display_name}'s** turn to pull the trigger!\n*(You have 30 seconds to pull)*",
            color=discord.Color.dark_red()
        )
        
        msg = await ctx.send(embed=start_embed, view=game_view)
        game_view.message = msg
        
        # If the first player is a bot, kick off the bot action loop automatically!
        if getattr(players[0], "bot", False):
            asyncio.create_task(game_view.bot_action(None))
            
        await game_view.wait()

async def setup(bot):
    await bot.add_cog(Games(bot))
