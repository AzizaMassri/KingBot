import discord
from discord.ext import commands
import json
import os
import aiofiles
from cogs.utils.views import TranslatedView

class EventsDropdown(discord.ui.Select):
    def __init__(self, data, title_prefix="Event Info"):
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
                 print(f"Events Cog Auto-Translate Error: {e}")
                 pass
                 
        # If no global auto-translator, we render the standard English with TranslatedView
        await view.send_translated(interaction, embed=embed, view=view)


class EventsView(TranslatedView):
    def __init__(self, data, bot, title_prefix="Event Info"):
        super().__init__()
        self.bot = bot
        self.add_item(EventsDropdown(data, title_prefix=title_prefix))

class EventsCog(commands.Cog):
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
             print(f"Failed to load Castle DB in events cog: {e}")
             
        try:
             async with aiofiles.open(self.facility_db_path, mode='r', encoding='utf-8') as f:
                 content = await f.read()
                 self.facility_db_data = json.loads(content)
        except Exception as e:
             print(f"Failed to load Facility DB in events cog: {e}")

    @commands.group(name="events", aliases=["event"], invoke_without_command=True)
    async def events_command(self, ctx):
        embed = discord.Embed(
            title="🗺️ Kingshot Event Guides 🗺️",
            description=(
                "Welcome to the Events Directory! To view guide information, use one of the specific event subcommands below:\n\n"
                "`!castle` - View information and strategies for the Kingdom of Power (KvK) Castle Battle.\n"
                "`!facility` - View information and strategies for Sanctuaries, Outposts, and Fortresses."
            ),
            color=discord.Color.brand_green()
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
                     title=f"🗺️ Kingshot Event Guides ({target_lang.capitalize()}) 🗺️",
                     description=translation,
                     color=discord.Color.brand_green()
                 )
                 t_embed.set_footer(text="Translated via Global Translator")
                 return await ctx.send(embed=t_embed)
             except:
                 pass
                 
        await ctx.send(embed=embed)
        
    @events_command.command(name="castle")
    async def events_castle_subcommand(self, ctx):
        """View information and strategies for the Kingdom of Power (KvK) Castle Battle."""
        await self.castle_command(ctx)
        
    @events_command.command(name="facility", aliases=["sanctuary", "outpost", "fortress"])
    async def events_facility_subcommand(self, ctx):
        """View information and strategies for Sanctuaries, Outposts, and Fortresses."""
        await self.facility_command(ctx)

    @commands.group(name="castle", invoke_without_command=True)
    async def castle_command(self, ctx):
        if not self.castle_db_data:
            return await ctx.send("The Castle database is currently unavailable or still loading. Please try again later.", ephemeral=True)
            
        embed = discord.Embed(
            title="🗺️ Kingshot KvK & Castle Battle 🗺️",
            description="Select an event strategy or mechanic from the dropdown below to learn more!",
            color=discord.Color.dark_purple()
        )
        
        view = EventsView(self.castle_db_data, self.bot, title_prefix="Kingshot Castle Battle")
        
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
        
        view = EventsView(self.facility_db_data, self.bot, title_prefix="Facility Battle")
        
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
    await bot.add_cog(EventsCog(bot))
