import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import html
import random

class TriviaView(discord.ui.View):
    def __init__(self, bot, question_data: dict, timeout=30.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.question_data = question_data
        self.correct_answer = html.unescape(question_data['correct_answer'])
        self.incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
        
        self.all_answers = self.incorrect_answers + [self.correct_answer]
        # Shuffle answers
        random.shuffle(self.all_answers)
        
        # Track who answered what: {user_id: answer_text}
        self.user_answers = {}
        
        for ans in self.all_answers:
            self.add_item(TriviaButton(label=ans, custom_id=ans))
            
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self.user_answers:
            await interaction.response.send_message("You have already answered this question!", ephemeral=True)
            return False
        return True

class TriviaButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, custom_id=custom_id)
        
    async def callback(self, interaction: discord.Interaction):
        view: TriviaView = self.view
        view.user_answers[interaction.user.id] = self.label
        await interaction.response.send_message(f"Your answer '{self.label}' has been locked in!", ephemeral=True)

class MonarchsMysteries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Track if a trivia game is active in a channel
        self.active_games = set()

    @commands.hybrid_command(name="monarchsmysteries", aliases=["trivia", "mm"])
    @commands.guild_only()
    async def start_trivia(self, ctx: commands.Context):
        """
        Start a 21-question game of Monarch's Mysteries (Trivia)!
        """
        if ctx.channel.id in self.active_games:
            return await ctx.send("A game of Monarch's Mysteries is already running in this channel!")
            
        self.active_games.add(ctx.channel.id)
        
        await ctx.send("👑 **The Monarch's Mysteries are beginning!** Gather round...\nFetching 21 questions from the royal archives...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # amount=21
                async with session.get("https://opentdb.com/api.php?amount=21") as resp:
                    if resp.status != 200:
                        self.active_games.remove(ctx.channel.id)
                        return await ctx.send("The royal archives are temporarily sealed (API Error). Try again later!")
                    data = await resp.json()
                    
            if data['response_code'] != 0:
                self.active_games.remove(ctx.channel.id)
                return await ctx.send("Failed to retrieve questions. Try again later.")
                
            questions = data['results']
            
            # Leaderboard tracking: {user_id: score}
            scores = {}
            participant_names = {}
            
            for i, q in enumerate(questions, 1):
                category = html.unescape(q['category'])
                difficulty = q['difficulty'].capitalize()
                question_text = html.unescape(q['question'])
                
                embed = discord.Embed(
                    title=f"Question {i} / 21",
                    description=f"**{question_text}**",
                    color=discord.Color.gold()
                )
                embed.set_footer(text=f"Category: {category} | Difficulty: {difficulty} | You have 30 seconds!")
                
                view = TriviaView(self.bot, q, timeout=30.0)
                msg = await ctx.send(embed=embed, view=view)
                
                # Wait 30 seconds for the time limit
                await asyncio.sleep(30.0)
                
                # Time's up, tally answers
                for child in view.children:
                    child.disabled = True
                    if child.label == view.correct_answer:
                        child.style = discord.ButtonStyle.success
                    else:
                        child.style = discord.ButtonStyle.danger
                
                # Fetch fresh users so we can display their names
                correct_users = []
                for user_id, chosen_answer in view.user_answers.items():
                    # Record name if new
                    if user_id not in participant_names:
                        member = ctx.guild.get_member(user_id)
                        if member:
                            participant_names[user_id] = member.display_name
                        else:
                            participant_names[user_id] = "Unknown Knight"
                            
                    if chosen_answer == view.correct_answer:
                        scores[user_id] = scores.get(user_id, 0) + 1
                        correct_users.append(participant_names[user_id])
                
                result_text = f"⏳ **Time's up!** The correct answer was **{view.correct_answer}**\n"
                if correct_users:
                    result_text += f"Correctly answered by: {', '.join(correct_users)}"
                else:
                    result_text += "No one got this right!"
                    
                await msg.edit(content=result_text, embed=embed, view=view)
                
                if i < 21:
                    await asyncio.sleep(5.0)
                    
            # End of game leaderboard
            self.active_games.remove(ctx.channel.id)
            
            leaderboard_embed = discord.Embed(
                title="👑 Monarch's Mysteries - Final Standings!",
                color=discord.Color.purple()
            )
            
            if not scores:
                leaderboard_embed.description = "No one scored any points! The royal jester laughs at you all."
            else:
                # Sort descending
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                
                desc = ""
                for rank, (user_id, score) in enumerate(sorted_scores, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📜"
                    desc += f"{medal} **{participant_names[user_id]}**: {score} points\n"
                    
                leaderboard_embed.description = desc
                
            await ctx.send(embed=leaderboard_embed)
            
        except Exception as e:
            if ctx.channel.id in self.active_games:
                self.active_games.remove(ctx.channel.id)
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(MonarchsMysteries(bot))
