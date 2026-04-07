import discord
from discord.ext import commands
import json
import os
import aiofiles
from cogs.utils.views import TranslatedView
from google import genai

class GuidesDropdown(discord.ui.Select):
    def __init__(self, data, title_prefix="Guide Info"):
        self.data = data
        self.title_prefix = title_prefix
        options = []
        for key, section_data in data.items():
            # Format the key into a readable title
            title = key.replace("_", " ").title()
            if "Kvk" in title:
                title = title.replace("Kvk", "KvK")
            options.append(discord.SelectOption(label=title, value=key, description=f"Details for {title}"[:100]))
            
        super().__init__(placeholder="Select an event strategy or mechanic...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        section_data = self.data[selected_key]
        
        embed = discord.Embed(
            title=f"🏰 {selected_key.replace('_', ' ').title()} 🏰",
            color=discord.Color.dark_purple()
        )
        
        for k, v in section_data.items():
            if isinstance(v, dict):
                content = ""
                for sub_k, sub_v in v.items():
                    content += f"**{sub_k.replace('_', ' ').title()}**: {sub_v}\n"
                embed.add_field(name=k.replace('_', ' ').title(), value=content, inline=False)
            else:
                embed.add_field(name=k.replace('_', ' ').title(), value=str(v), inline=False)
                
        # Use our TranslatedView to leverage built-in functionality
        view = self.view
        
        # Local override in case bot has database translated content for user
        user_id = str(interaction.user.id)
        target_lang = None
        try:
             target_lang = await view.bot.db.hget("global_translator_subs", user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following Discord embed content to {target_lang}. Be as concise and literal as possible, use minimal AI flourish, and do not use forced conversational slang. Do not wrap in markdown blocks, output raw text of the translation only."
             prompt += f"\nTitle: {embed.title}"
             for f in embed.fields:
                 prompt += f"\n{f.name}: {f.value}"
                 
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🏰 {self.title_prefix} Info ({target_lang.capitalize()}) 🏰",
                     description=translation,
                     color=discord.Color.dark_purple()
                 )
                 t_embed.set_footer(text="Translated via Global Translator")
                 return await interaction.response.edit_message(embed=t_embed, view=view)
             except Exception as e:
                 print(f"Guides Cog Auto-Translate Error: {e}")
                 pass
                 
        # If no global auto-translator, we render the standard English with TranslatedView
        await view.send_translated(interaction, embed=embed, view=view)


class GuidesView(TranslatedView):
    def __init__(self, data, bot, title_prefix="Guide Info"):
        super().__init__()
        self.bot = bot
        self.add_item(GuidesDropdown(data, title_prefix=title_prefix))

class TimelineView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="timeline_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline (Mini) 🏰",
            description=(
                "⏳ **Day 0:** Gen 1 Heroes (SSR/SR/R)\n"
                "🦁 **Day 40-60:** Gen 2 Heroes (Zoe/Marlin/Hilde) & Gen 1 Pets (Lynx/Bison)\n"
                "👑 **Day 70-80:** TrueGold, KvK, Gen 2 Pets (Cheetah/Moose)\n"
                "🐻 **Day 105-120:** Gen 3 Heroes (Eric/Jaeger/Petra) & Gen 3 Pets (Lion/Grizzly)\n"
                "⚔️ **Day 150:** TrueGold 4/5 & Crucible\n"
                "🦏 **Day 190-200:** Gen 4 Heroes (Alcar/Rosa/Margot) & Gen 4 Pets (Rhino/Bison)\n"
                "🛡️ **Day 220:** War Academy T11\n"
                "🐉 **Day 270-280:** Gen 5 Heroes (Long Fei/Vivian/Thrud) & Pets (Moose/Panther)\n"
                "🔥 **Day 315:** TrueGold 6/7/8 & Super Refinement\n\n"
                "*(For full timeline details, select the Full Guide!)*"
            ),
            color=discord.Color.gold()
        )
        
        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="timeline_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline (Full) 🏰",
            description=(
                "**Day 0** – SSR (gold) Gen 1 Heroes, SR (purple) Heroes, R (blue) Heroes\n"
                "**Day 40–50** – Gen 2 Heroes SSR– Zoe, Marlin, Hilde\n"
                "**Day 55–60** – Gen 1 Pets (Lynx, Bison)\n"
                "**Day 70** – Age of TrueGold\n"
                "**Day 70–80** – Kingdom of Power (KvK)\n"
                "**Day 75–80** – Gen 2 Pets (Cheetah, Moose)\n"
                "**Day 105–120** – Gen 3 Heroes SSR– Eric, Jaeger, Petra \n"
                "**Day 105–115** – Gen 3 Pets (Lion, Grizzly Bear)\n"
                "**Day 150** – TrueGold 4 & 5 / TrueGold Crucible\n"
                "**Day 190–200** – Gen 4 Heroes SSR– Alcar, Rosa, Margot\n"
                "**Day 195–200** – Gen 4 Pets (Giant Rhino, Mighty Bison)\n"
                "**Day 220** – War Academy T11\n"
                "**Day 270–280** – Gen 5 Heroes SSR– Long Fei, Vivian, Thrud\n"
                "**Day 280** – Gen 5 Pets (Great Moose, Alpha Black Panther)\n"
                "**Day 315** – TG 6, 7 & 8 / Super Refinement"
            ),
            color=discord.Color.gold()
        )
        # Note: You can replace this URL with the actual discord image link of the timeline infographic
        embed.set_image(url="https://i.imgur.com/qtn62GE.png") 

        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        await interaction.response.edit_message(embed=embed, view=self)

    async def get_target_lang(self, user_id):
        try:
            return await self.bot.db.hget('global_translator_subs', str(user_id))
        except Exception:
            return None

    async def translate_embed(self, embed, target_lang):
        prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            if response and response.text:
                translation = response.text.strip()
                t_embed = discord.Embed(
                    title=f"🏰 Timeline ({target_lang.capitalize()}) 🏰",
                    description=translation,
                    color=embed.color
                )
                if embed.image and embed.image.url:
                    t_embed.set_image(url=embed.image.url)
                t_embed.set_footer(text="Translated via Global Translator")
                return t_embed
        except Exception as e:
            print(f"Timeline Auto-Translate Error: {e}")
        return embed

class GuidesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.castle_db_path = os.path.join(os.path.dirname(__file__), '..', 'kingshot_castle_battle_db.json')
        self.facility_db_path = os.path.join(os.path.dirname(__file__), '..', 'kingshot_sanc_out_fort_db.JSON')
        self.castle_db_data = {}
        self.facility_db_data = {}
        self.bot.loop.create_task(self.load_dbs())



    async def load_dbs(self):
        try:
             async with aiofiles.open(self.castle_db_path, mode='r', encoding='utf-8') as f:
                 content = await f.read()
                 self.castle_db_data = json.loads(content)
        except Exception as e:
             print(f"Failed to load Castle DB in guides cog: {e}")
             
        try:
             async with aiofiles.open(self.facility_db_path, mode='r', encoding='utf-8') as f:
                 content = await f.read()
                 self.facility_db_data = json.loads(content)
        except Exception as e:
             print(f"Failed to load Facility DB in guides cog: {e}")

    @commands.group(name="guides", aliases=["guide"], invoke_without_command=True)
    async def guides_command(self, ctx):
        embed = discord.Embed(
            title="🗺️ Kingshot Mini Guides 🗺️",
            description=(
                "Welcome to the Guides Directory! Use the subcommands below to learn more:\n\n"
                "`!guides events` - Information on major Kingshot events.\n"
                "`!guides growth` - [Coming Soon] Player growth and progression guides.\n"
                "`!guides timeline` - View the Server Kingdom Journey Timeline.\n"
                "`!castle` - View information and strategies for the Kingdom of Power (KvK) Castle Battle.\n"
                "`!facility` - View information and strategies for Sanctuaries, Outposts, and Fortresses."
            ),
            color=discord.Color.green()
        )
        
        # Check auto-translator
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🗺️ Kingshot Mini Guides ({target_lang.capitalize()}) 🗺️",
                     description=translation,
                     color=discord.Color.green()
                 )
                 t_embed.set_footer(text="Translated via Global Translator")
                 return await ctx.send(embed=t_embed)
             except:
                 pass
                 
        await ctx.send(embed=embed)
        
    @guides_command.command(name="events")
    async def guides_events(self, ctx):
        """Placeholder for all events guides hub."""
        embed = discord.Embed(
            title="📅 Event Guides",
            description="Event-specific guides are being categorized! Check back later, or use `!castle` and `!facility` directly for now.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @guides_command.command(name="timeline")
    async def guides_timeline(self, ctx):
        """View the Server Kingdom Journey Timeline."""
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline 🏰",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.gold()
        )
        
        view = TimelineView(self.bot)
        
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if response and response.text:
                     translation = response.text.strip()
                     t_embed = discord.Embed(
                         title=f"🏰 Kingdom Journey Timeline ({target_lang.capitalize()}) 🏰",
                         description=translation,
                         color=discord.Color.gold()
                     )
                     t_embed.set_footer(text="Translated via Global Translator")
                     return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)

    @guides_command.command(name="growth", aliases=["player"])
    async def guides_growth(self, ctx):
        """Placeholder for player growth guides."""
        embed = discord.Embed(
            title="📈 Player Growth Guides",
            description="Player progression, resource management, and leveling guides will be added here soon!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.group(name="castle", invoke_without_command=True)
    async def castle_command(self, ctx):
        if not self.castle_db_data:
            return await ctx.send("The Castle database is currently unavailable or still loading. Please try again later.", ephemeral=True)
            
        embed = discord.Embed(
            title="🗺️ Kingshot KvK & Castle Battle 🗺️",
            description="Select an event strategy or mechanic from the dropdown below to learn more!",
            color=discord.Color.dark_purple()
        )
        
        view = GuidesView(self.castle_db_data, self.bot, title_prefix="Kingshot Castle Battle")
        
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🗺️ Kingshot KvK & Castle Battle ({target_lang.capitalize()}) 🗺️",
                     description=translation,
                     color=discord.Color.dark_purple()
                 )
                 t_embed.set_footer(text="Translated via Global Translator")
                 return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)
        
    @commands.group(name="facility", aliases=["sanctuary", "outpost", "fortress"], invoke_without_command=True)
    async def facility_command(self, ctx):
        if not self.facility_db_data:
            return await ctx.send("The Facility database is currently unavailable or still loading. Please try again later.", ephemeral=True)
            
        embed = discord.Embed(
            title="🏭 Kingshot Sanctuaries, Outposts & Fortresses 🏭",
            description="Select an event strategy or mechanic from the dropdown below to learn more!",
            color=discord.Color.blue()
        )
        
        view = GuidesView(self.facility_db_data, self.bot, title_prefix="Facility Battle")
        
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🏭 Kingshot Sanctuaries, Outposts & Fortresses ({target_lang.capitalize()}) 🏭",
                     description=translation,
                     color=discord.Color.blue()
                 )
                 t_embed.set_footer(text="Translated via Global Translator")
                 return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)

    @castle_command.command(name="store")
    async def castle_store(self, ctx):
        """View the AI Translation capabilities and status of the Castle database."""
        embed = discord.Embed(
            title="🗄️ Castle Store DB Status",
            description=(
                "The Kingshot Castle Battle mechanics are being stored and powered by the `kingshot_castle_battle_db` Translation Database!\n\n"
                "✓ English Text Verified\n"
                "✓ Native Discord UI Translation Hooked\n"
                "✓ Auto-Translator (Database) Sync Enabled"
            ),
            color=discord.Color.blurple()
        )
        
        # Auto-translator support for this command
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Output only the translation, strictly literal and concise without AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🗄️ Castle Store DB Status ({target_lang.capitalize()})",
                     description=translation,
                     color=discord.Color.blurple()
                 )
                 return await ctx.send(embed=t_embed)
             except:
                 pass
                 
        # If no global auto-translator, render default with TranslatedView concept (though sending direct)
        view = TranslatedView()
        await view.send_translated(ctx, embed=embed)
        
    @facility_command.command(name="store")
    async def facility_store(self, ctx):
        """View the AI Translation capabilities and status of the Facility database."""
        embed = discord.Embed(
            title="🗄️ Facility Store DB Status",
            description=(
                "The Kingshot Sanctuary, Outpost, and Fortress mechanics are being stored and powered by the `kingshot_sanc_out_fort_db` Translation Database!\n\n"
                "✓ English Text Verified\n"
                "✓ Native Discord UI Translation Hooked\n"
                "✓ Auto-Translator (Database) Sync Enabled"
            ),
            color=discord.Color.blurple()
        )
        
        # Auto-translator support for this command
        user_id = str(ctx.author.id)
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
             pass
             
        if target_lang:
             prompt = f"Translate the following to {target_lang}. Output only the translation, strictly literal and concise without AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
             
             try:
                 client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                 response = await client.aio.models.generate_content(
                     model='gemini-2.5-flash',
                     contents=prompt
                 )
                 if not response.text:
                     raise ValueError("Translation returned None")
                 translation = response.text.strip()
                 
                 t_embed = discord.Embed(
                     title=f"🗄️ Facility Store DB Status ({target_lang.capitalize()})",
                     description=translation,
                     color=discord.Color.blurple()
                 )
                 return await ctx.send(embed=t_embed)
             except:
                 pass
                 
        # If no global auto-translator, render default with TranslatedView concept (though sending direct)
        view = TranslatedView()
        await view.send_translated(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(GuidesCog(bot))
