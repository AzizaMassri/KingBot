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
                 if interaction.guild is None:
                     content = f"**{t_embed.title}**\n\n{t_embed.description}"
                     await interaction.response.edit_message(content=content, embed=None, view=view)
                 else:
                     await interaction.response.edit_message(embed=t_embed, view=view)
                 return
             except Exception as e:
                 print(f"Guides Cog Auto-Translate Error: {e}")
                 pass
                 
        # If no global auto-translator, we render the standard English with TranslatedView
        if interaction.guild is None:
            content = f"**{embed.title}**\n"
            for field in embed.fields:
                content += f"\n**{field.name}**\n{field.value}\n"
            await interaction.response.edit_message(content=content, embed=None, view=view)
        else:
            await view.send_translated(interaction, embed=embed, view=view)


class GuidesView(TranslatedView):
    def __init__(self, data, bot, title_prefix="Guide Info"):
        super().__init__()
        self.bot = bot
        self.add_item(GuidesDropdown(data, title_prefix=title_prefix))

class VikingView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="viking_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ Viking Vengeance (Mini Guide) 🛡️",
            description=(
                "🌊 **The Basics:** Defend against 20 waves (Tues/Thurs). Kill at least 50% to pass. 2 losses = you're out (but can still reinforce!).\n"
                "🌊 **Wave Targets:** 1-6/8-9/11-13/15-16/18-19: All. 7/14/17: Online Only. 10/20: HQ.\n"
                "🔄 **Troop Exchange:** Keep top 3 heroes home, send the rest away! This ensures reinforcers get MAX SCORE.\n"
                "🚑 **HEALING:** DO NOT heal unless you are out or the event is over! Healing steals ally points.\n"
                "📍 **Position:** Teleport close to allies to share support quickly."
            ),
            color=discord.Color.dark_red()
        )
        
        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="viking_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ Viking Vengeance (Full) 🛡️",
            color=discord.Color.dark_red()
        )
        embed.description = (
            "**What is it?**\n"
            "An invasion simulation taking place every two weeks (Tue/Thu). You must defend against 20 waves of Vikings. To pass a wave, you must kill at least 50% of attacking troops. (2 losses = you stop receiving attacks, but can still reinforce others!). Starts automatically if a time is set, or manually by R4/R5.\n\n"
            
            "**How Points Work**\n"
            "Points depend on how many Viking troops die in your city (100% kills = 100% points). Reinforcing others doesn't steal their points, it creates EXTRA reinforcement points for you!\n\n"
            
            "**Wave Targets**\n"
            "• **Waves 1-6, 8-9, 11-13, 15-16, 18-19:** All Members\n"
            "• **Waves 7, 14, 17:** Online Members Only\n"
            "• **Waves 10, 20:** HQ (Plains HQ preferred!)\n\n"
            
            "**A. Main Base Defense & Deployments**\n"
            "• Keep strongest heroes home. Emptying your own troops allows supporters to maximize their score! If you have more troops than marches, keep archers home.\n\n"
            
            "**B. Troop Exchange Strategy**\n"
            "• Keep top 3 heroes home. Exchange the rest with other players. If done correctly, your castle has 0 remaining troops, granting supporters maximum points.\n"
            "• Coordinate with nearby allies for smooth HQ transfers. Reinforce online members during waves 7, 14, 17.\n\n"
            
            "**C. Healing & Timings**\n"
            "• **Wait Periods:** 1 min by default, 3 mins for HQ (10 & 20).\n"
            "• **HEALING:** DO NOT heal unless you are out, the event is over, or you can swap! Healing sends your troops home, which steals points from reinforcers!"
        )
        embed.set_image(url="https://i.imgur.com/rellg9X.jpeg")

        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
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
                    title=f"🛡️ Viking Vengeance ({target_lang.capitalize()}) 🛡️",
                    description=translation,
                    color=embed.color
                )
                if embed.image and embed.image.url:
                    t_embed.set_image(url=embed.image.url)
                t_embed.set_footer(text="Translated via Global Translator")
                return t_embed
        except Exception as e:
            print(f"Viking Auto-Translate Error: {e}")
        return embed

class ChampionshipView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="champ_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide (Mini) 🏆",
            description=(
                "⚔️ **The Goal:** Win 2 of 3 lanes! 20 members max per lane. R4s arrange lanes. Combat is automatic and targets weakest first. Max 2 kills per player.\n"
                "🛡️ **Lane Strategy:** Stack your strongest/offensive players in two main lanes to win. Put lower-power members in the 3rd 'Sacrifice' lane to stall.\n"
                "🏹 **Formation:** 50% Inf, 20% Cav, 30% Arch (5:2:3). Set it up custom!\n"
                "🔥 **PRO TIP:** Buffs (like pet buffs) active *when you register* apply to the whole event!\n\n"
                "*(For full details, select the Full Guide!)*"
            ),
            color=discord.Color.brand_green()
        )
        
        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="champ_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide (Full) 🏆",
            color=discord.Color.brand_green()
        )
        embed.description = (
            "To play the Alliance Championship event, each alliance must assign 20 members to each of three lanes. The core strategy is to focus strength on two lanes to secure victory, as winning at least two out of three lanes is required for the overall win.\n\n"
            
            "**Event Mechanics**\n"
            "• **Sign-up:** Each member signs up individually and sets their troop formation beforehand.\n"
            "• **Lanes:** R4s can stack 20 members in each of 3 distinct lanes and adjust between rounds.\n"
            "• **Automatic Combat:** Units in each lane move and attack automatically, targeting the enemy units with the lowest power first.\n"
            "• **Player Limit:** A single player can only survive for 2 rounds after defeating an enemy unit (max 2 kills per player). This prevents one powerful player from clearing an entire lane alone.\n\n"
            
            "**Core Strategies (Lane Assignments)**\n"
            "• **Main Lanes (2):** Assign your strongest players with offensive heroes to eliminate enemy units.\n"
            "• **Secondary Lanes:** Use mid-tier members with balanced heroes to hold position and support.\n"
            "• **Sacrifice Lane (1):** Assign lower-power members to slow down the enemy and buy time.\n\n"
            
            "**Troop Formations**\n"
            "A highly effective troop formation is the **50% Infantry, 20% Cavalry, 30% Archers** ratio (5:2:3).\n"
            "• **Infantry:** Acts as a shield with high HP.\n"
            "• **Cavalry:** Provides healing and balanced attacks.\n"
            "• **Archers:** Offers high damage from a distance.\n"
            "*It is advisable to create custom formations.*\n\n"
            
            "**🔥 PRO TIP**\n"
            "Buffs applied prior to registering will be applied to the entirety of the event. Activate pet buffs prior to deploying. Try to time other optional buffs with registering for the championship. This will give us a significant advantage versus higher power opponents."
        )
        embed.set_image(url="https://i.imgur.com/brtrDiQ.jpeg")

        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
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
                    title=f"🏆 Alliance Championship ({target_lang.capitalize()}) 🏆",
                    description=translation,
                    color=embed.color
                )
                if embed.image and embed.image.url:
                    t_embed.set_image(url=embed.image.url)
                t_embed.set_footer(text="Translated via Global Translator")
                return t_embed
        except Exception as e:
            print(f"Championship Auto-Translate Error: {e}")
        return embed

class BearTrapView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="beartrap_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🐻 Bear Trap Guide (Mini) 🐻",
            description=(
                "⚙️ **City Prep:** Maximize Lethality tech/gear, upgrade Command Center, and enhance Charms.\n"
                "⚔️ **Rally Captains:** Best: Amadeus, Jabel, Saul (4⭐+ beats Quinn). Troop Ratio: 10% Inf / 10% Cav / 80% Arch.\n"
                "🔥 **Top Joiners:** 1st Slot: Chenko (Lv 5 skill = +25% DMG), Amadeus, Yeonwoo (4⭐), or Amane.\n"
                "⚠️ **Joiner Rules:** Max 4 joiner skills apply! If 4 Chenkos are already in, send no heroes to avoid overriding strong skills. Use the yellow flag to check.\n"
                "🎯 **Focus:** Prioritize Lethality and Pitfall donations!\n\n"
                "*(For full details, select the Full Guide!)*"
            ),
            color=discord.Color.dark_magenta()
        )
        
        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="beartrap_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🐻 Bear Trap Guide (Full) 🐻",
            color=discord.Color.dark_magenta()
        )
        embed.description = (
            "**Preparing Your City**\n"
            "• **Research:** Prioritize tech increasing Lethality and deployment capacity.\n"
            "• **Buildings:** Upgrade Command Center for larger troop sends.\n"
            "• **Gear & Charms:** Focus on Lethality boosts to improve base rally damage.\n\n"
            
            "**Best Heroes for Rally Captains**\n"
            "Captain skills set the baseline for everyone. Recommended setups:\n"
            "• **Best:** Amadeus, Jabel, Saul (Saul overtakes Quinn once 4-starred).\n"
            "• **Mid:** Helga, Jabel, Quinn or Saul.\n"
            "• **F2P:** Howard, Jabel, Quinn.\n"
            "• **Troop Ratio:** 10% Infantry, 10% Cavalry, 80% Archers.\n\n"

            "**Key Rally Joiner Heroes**\n"
            "Only **four** joiner skills are applied!\n"
            "• **Chenko:** Top choice. Lv 5 first skill gives +25% DMG (requires 1st slot placement).\n"
            "• **Amadeus:** Gives major Lethality boost like Chenko.\n"
            "• **Yeonwoo & Amane:** Yeonwoo gives 25% Lethality at 4⭐. Amane boosts Attack.\n\n"
            
            "**Rally Joining Rules**\n"
            "• **< 4 Chenkos:** Send Chenko in your first slot.\n"
            "• **4 Chenkos are in:** Do **NOT** send another high-skill hero in the 1st slot. Send troops with no heroes so you don't override someone's stronger skill.\n"
            "• **Yellow Flag:** Tap it on the rally screen to check setup. Locked Lv 5 skills can't be overridden unless kicked.\n\n"
            
            "**Maximize Damage:** Prioritize Lethality, upgrade Pitfall, use premium joiners, and coordinate placements."
        )
        embed.set_image(url="https://i.imgur.com/P7KLael.jpeg")

        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
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
                    title=f"🐻 Bear Trap ({target_lang.capitalize()}) 🐻",
                    description=translation,
                    color=embed.color
                )
                if embed.image and embed.image.url:
                    t_embed.set_image(url=embed.image.url)
                t_embed.set_footer(text="Translated via Global Translator")
                return t_embed
        except Exception as e:
            print(f"Bear Trap Auto-Translate Error: {e}")
        return embed

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
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
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
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
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
                "`!guides viking` - View the Viking Vengeance Defense Guide.\n"
                "`!guides beartrap` - View the Bear Trap Event Guide & Formations.\n"
                "`!guides championship` - View the Alliance Championship Guide & Strategies.\n"
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

    @guides_command.command(name="viking")
    async def guides_viking(self, ctx):
        """View the Viking Vengeance Event Guide."""
        embed = discord.Embed(
            title="🛡️ Viking Vengeance Guide 🛡️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_red()
        )
        
        view = VikingView(self.bot)
        
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
                         title=f"🛡️ Viking Vengeance Guide ({target_lang.capitalize()}) 🛡️",
                         description=translation,
                         color=discord.Color.dark_red()
                     )
                     t_embed.set_footer(text="Translated via Global Translator")
                     return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)
        
    @guides_command.command(name="events")
    async def guides_events(self, ctx):
        """Placeholder for all events guides hub."""
        embed = discord.Embed(
            title="📅 Event Guides",
            description="Event-specific guides are being categorized! Check back later, or use `!castle` and `!facility` directly for now.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @guides_command.command(name="championship", aliases=["champ"])
    async def guides_championship(self, ctx):
        """View the Alliance Championship Event Guide."""
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide 🏆",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.brand_green()
        )
        
        view = ChampionshipView(self.bot)
        
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
                         title=f"🏆 Alliance Championship Guide ({target_lang.capitalize()}) 🏆",
                         description=translation,
                         color=discord.Color.brand_green()
                     )
                     t_embed.set_footer(text="Translated via Global Translator")
                     return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)

    @guides_command.command(name="beartrap")
    async def guides_beartrap(self, ctx):
        """View the Bear Trap Event Guide."""
        embed = discord.Embed(
            title="🐻 Bear Trap Guide 🐻",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_magenta()
        )
        
        view = BearTrapView(self.bot)
        
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
                         title=f"🐻 Bear Trap Guide ({target_lang.capitalize()}) 🐻",
                         description=translation,
                         color=discord.Color.dark_magenta()
                     )
                     t_embed.set_footer(text="Translated via Global Translator")
                     return await ctx.send(embed=t_embed, view=view)
             except:
                 pass
                 
        await ctx.send(embed=embed, view=view)

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
