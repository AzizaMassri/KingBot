import discord
from discord.ext import commands
import os
from google import genai

class BaseGuideView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

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
                    title=f"{embed.title} ({target_lang.capitalize()})",
                    description=translation,
                    color=embed.color
                )
                if embed.image and getattr(embed.image, 'url', None):
                    t_embed.set_image(url=embed.image.url)
                t_embed.set_footer(text="Translated via Global Translator")
                return t_embed
        except Exception as e:
            print(f"Guide Auto-Translate Error: {e}")
        return embed

    async def update_message(self, interaction, embed):
        target_lang = await self.get_target_lang(interaction.user.id)
        if target_lang:
            embed = await self.translate_embed(embed, target_lang)
            
        if interaction.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(content=content, embed=None, view=self)
        else:
            await interaction.response.edit_message(content=None, embed=embed, view=self)


class VikingView(BaseGuideView):
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
        await self.update_message(interaction, embed)

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
        await self.update_message(interaction, embed)


class ChampionshipView(BaseGuideView):
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
        await self.update_message(interaction, embed)

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
        await self.update_message(interaction, embed)


class BearTrapView(BaseGuideView):
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
        await self.update_message(interaction, embed)

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
        await self.update_message(interaction, embed)


class TimelineView(BaseGuideView):
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
        await self.update_message(interaction, embed)

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
        embed.set_image(url="https://i.imgur.com/qtn62GE.png") 
        await self.update_message(interaction, embed)


class CastleView(BaseGuideView):
    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="castle_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏰 King's Castle & KvK (Mini Guide) 🏰",
            description=(
                "👑 **Goal:** First to occupy for 2.5hrs continuously, or longest total accumulation.\n"
                "🎯 **Defenses:** Hold Castle & Turrets (Turrets fire on occupants unless you hold BOTH!). Red Zone teleports random cities!\n"
                "🛡️ **Formations:** Attack: 50% Inf, 20% Cav, 30% Arch. Defense: 60% Inf, 20% Cav, 20% Arch.\n"
                "🚨 **Healing:** NEVER 'Heal All'. Heal in 30-45min batches & mash alliance 'Help' for instant free heals!\n"
                "⚔️ **Reinforcing:** Send pure Infantry without heroes so you don't override defensive buffs!"
            ),
            color=discord.Color.purple()
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="castle_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
             title="🏰 King's Castle & KvK (Full) 🏰",
             color=discord.Color.purple()
        )
        embed.description = (
            "**Event Overview**\n"
            "First to hold the Castle for 2.5 hours continuously wins. Otherwise, longest total accumulation wins. Whomever controls it awards server-wide titles and buffs.\n\n"
            "**Map Mechanics**\n"
            "• **Alert/Red Zone:** 2 hours before shields drop, cities here randomly get teleported away.\n"
            "• **Turrets (4):** Fire on the alliance in the Castle. If you hold both Castle & Turret, it stops firing. You must hold turrets to survive.\n\n"
            "**Formations & Troops**\n"
            "• **Attack (50% Inf / 20% Cav / 30% Arch):** High DPS (Archers) behind a thick tank wall (Infantry) to break garrisons.\n"
            "• **Defense (60% Inf / 20% Cav / 20% Arch):** Maximizes HP to soak damage. Archers are risky here.\n"
            "• **Garrison Reinforcements:** Pure Infantry. Send WITHOUT HEROES so you don't override the Whale captain's top tier skills.\n\n"
            "**Advanced Tactics**\n"
            "• **Batch Healing:** Troops only die if the Infirmary is 100% full. Never 'Heal All'. Heal in 30m batches, press 'Help', and let alliance finish it instantly.\n"
            "• **Double Rallies:** Unseat a mega-whale by staggering a Meat Shield rally to hit 1s before the Whale Kill Shot rally.\n\n"
            "**KvK Phase (Kingdom of Power)**\n"
            "• **Phase 2:** 5 days of resource points prep.\n"
            "• **Phase 3:** 6 hours of combat on loser's server.\n"
            "• **Phase 4:** Triage (recover 90% dead troops via satchels)."
        )
        await self.update_message(interaction, embed)


class FacilityView(BaseGuideView):
    @discord.ui.button(label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="fac_mini")
    async def mini_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🗺️ Sancs, Forts & Outposts (Mini Guide) 🗺️",
            description=(
                "🚩 **Connection:** Outposts MUST touch alliance Banners. Sanctuaries & Fortresses DO NOT (just teleport)!\n"
                "⏱️ **Winning:** Outposts require 15-30 mins depending on level. Sancs/Forts need 30 mins continuous! Or hold at 2hr expiry.\n"
                "🩸 **Losses:** Outpost Lv.4 is a LETHAL 10% perm loss! Sancs/Forts/Others are 0% perm loss (Infirmary only).\n"
                "🤝 **Rebels:** NEVER solo rebel NPCs! Mass rally so the entire alliance gets 15x 'First Capture' loot.\n"
                "⚔️ **Defensive Ratio:** Reinforce garrisons with PURE Infantry without heroes to save the stats!"
            ),
            color=discord.Color.blue()
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="fac_full")
    async def full_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
             title="🗺️ Sancs, Forts & Outposts (Full) 🗺️",
             color=discord.Color.blue()
        )
        embed.description = (
            "**Territory & Requirements**\n"
            "• **Outposts:** Alliance Banners MUST physically touch them.\n"
            "• **Sanctuaries & Fortresses:** No connection required. Teleport directly. Voted by R4/R5.\n\n"
            "**Battle & Mechanics**\n"
            "• Starts occupied by NPC Rebels. Defeating them grants 'First Capture' rewards.\n"
            "• **Win Conditions:** Sancs/Forts require 30 mins contiguous hold. Outposts are 15-30 mins based on level. Alternatively, be the alliance holding at the final 2-hour event expiry marker.\n\n"
            "**Troop Losses**\n"
            "• **Sancs & Forts:** 0% loss (severely injured go to infirmary).\n"
            "• **Outposts Lv.1-3:** 0% loss.\n"
            "• **Outposts Lv.4:** ⚠️ 10% PERMANENT TROOP LOSS.\n\n"
            "**Advanced Defenses**\n"
            "• **Grid Positioning:** Teleport aligning with the FLAT side of the grid, not corners.\n"
            "• **NEVER Solo Rebels:** An alliance mega-rally shares huge loot with everyone. Soloing robs you of this.\n"
            "• **Snipe:** If unable to hold for 30m, jump in during the final 10 mins and hold it until the 2-hour mark locks the winner.\n"
            "• **Reinforcements:** Repeated attacks kill Infantry first. You MUST constantly reinforce the garrison with PURE INFANTRY to keep the ratio stable (no heroes)."
        )
        await self.update_message(interaction, embed)


class GuidesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_or_translate_guide(self, ctx, embed, view=None):
        target_lang = None
        try:
             target_lang = await self.bot.db.hget('global_translator_subs', str(ctx.author.id))
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
                         title=f"{embed.title} ({target_lang.capitalize()})",
                         description=translation,
                         color=embed.color
                     )
                     t_embed.set_footer(text="Translated via Global Translator")
                     embed = t_embed
             except:
                 pass
                 
        if ctx.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, 'url', None):
                content += f"\n{embed.image.url}"
            if view:
                await ctx.send(content=content, view=view)
            else:
                await ctx.send(content=content)
        else:
            if view:
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed)

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
        await self.send_or_translate_guide(ctx, embed)
        
    @guides_command.command(name="events")
    async def guides_events(self, ctx):
        """Placeholder for all events guides hub."""
        embed = discord.Embed(
            title="📅 Event Guides",
            description="Event-specific guides are being categorized! Check back later, or use `!castle` and `!facility` directly for now.",
            color=discord.Color.gold()
        )
        await self.send_or_translate_guide(ctx, embed)

    @guides_command.command(name="viking")
    async def guides_viking(self, ctx):
        """View the Viking Vengeance Event Guide."""
        embed = discord.Embed(
            title="🛡️ Viking Vengeance Guide 🛡️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_red()
        )
        await self.send_or_translate_guide(ctx, embed, view=VikingView(self.bot))

    @guides_command.command(name="championship", aliases=["champ"])
    async def guides_championship(self, ctx):
        """View the Alliance Championship Event Guide."""
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide 🏆",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.brand_green()
        )
        await self.send_or_translate_guide(ctx, embed, view=ChampionshipView(self.bot))

    @guides_command.command(name="beartrap")
    async def guides_beartrap(self, ctx):
        """View the Bear Trap Event Guide."""
        embed = discord.Embed(
            title="🐻 Bear Trap Guide 🐻",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_magenta()
        )
        await self.send_or_translate_guide(ctx, embed, view=BearTrapView(self.bot))

    @guides_command.command(name="timeline")
    async def guides_timeline(self, ctx):
        """View the Server Kingdom Journey Timeline."""
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline 🏰",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.gold()
        )
        await self.send_or_translate_guide(ctx, embed, view=TimelineView(self.bot))

    @commands.group(name="castle", aliases=["kvk"], invoke_without_command=True)
    async def castle_command(self, ctx):
        embed = discord.Embed(
            title="🏰 King's Castle & KvK Guide 🏰",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.purple()
        )
        await self.send_or_translate_guide(ctx, embed, view=CastleView(self.bot))

    @commands.group(name="facility", aliases=["sanctuary", "outpost", "fortress"], invoke_without_command=True)
    async def facility_command(self, ctx):
        embed = discord.Embed(
            title="🗺️ Sanctuaries, Outposts & Fortresses Guide 🗺️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue()
        )
        await self.send_or_translate_guide(ctx, embed, view=FacilityView(self.bot))

async def setup(bot):
    await bot.add_cog(GuidesCog(bot))
