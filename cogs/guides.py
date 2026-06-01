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
            return await self.bot.db.hget("global_translator_subs", str(user_id))
        except Exception:
            return None

    async def translate_embed(self, embed, target_lang):
        prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            if response and response.text:
                translation = response.text.strip()
                t_embed = discord.Embed(
                    title=f"{embed.title} ({target_lang.capitalize()})",
                    description=translation,
                    color=embed.color,
                )
                if embed.image and getattr(embed.image, "url", None):
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
            if embed.image and getattr(embed.image, "url", None):
                content += f"\n{embed.image.url}"
            await interaction.response.edit_message(
                content=content, embed=None, view=self
            )
        else:
            await interaction.response.edit_message(
                content=None, embed=embed, view=self
            )


class VikingView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="viking_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🛡️ Viking Vengeance Guide 🛡️",
            description=(
                "🌊 **The Basics:** Defend against 20 waves (Tues/Thurs). Kill at least 50% to pass. 2 losses = you're out (but can still reinforce!).\n"
                "🌊 **Wave Targets:** 1-6/8-9/11-13/15-16/18-19: All. 7/14/17: Online Only. 10/20: HQ.\n"
                "🔄 **Troop Exchange:** Keep top 3 heroes home, send the rest away! This ensures reinforcers get MAX SCORE.\n"
                "🚑 **HEALING:** DO NOT heal unless you are out or the event is over! Healing steals ally points.\n"
                "📍 **Position:** Teleport close to allies to share support quickly."
            ),
            color=discord.Color.dark_red(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="viking_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🛡️ Viking Vengeance (Full) 🛡️", color=discord.Color.dark_red()
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
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="champ_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide 🏆",
            description=(
                "⚔️ **The Goal:** Win 2 of 3 lanes! 20 members max per lane. R4s arrange lanes. Combat is automatic and targets weakest first. Max 2 kills per player.\n"
                "🛡️ **Lane Strategy:** Stack your strongest/offensive players in two main lanes to win. Put lower-power members in the 3rd 'Sacrifice' lane to stall.\n"
                "🏹 **Formation:** 50% Inf, 20% Cav, 30% Arch (5:2:3). Set it up custom!\n"
                "🔥 **PRO TIP:** Buffs (like pet buffs) active *when you register* apply to the whole event!\n\n"
                "*(For full details, select the Full Guide!)*"
            ),
            color=discord.Color.brand_green(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="champ_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide (Full) 🏆",
            color=discord.Color.brand_green(),
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
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="beartrap_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🐻 Bear Trap Guide 🐻",
            description=(
                "⚙️ **City Prep:** Maximize Lethality tech/gear, upgrade Command Center, and enhance Charms.\n"
                "⚔️ **Rally Captains:** Best: Amadeus, Jabel, Saul (4⭐+ beats Quinn). Troop Ratio: 10% Inf / 10% Cav / 80% Arch.\n"
                "🔥 **Top Joiners:** 1st Slot: Chenko (Lv 5 skill = +25% DMG), Amadeus, Yeonwoo (4⭐), or Amane.\n"
                "⚠️ **Joiner Rules:** Max 4 joiner skills apply! If 4 Chenkos are already in, send no heroes to avoid overriding strong skills. Use the yellow flag to check.\n"
                "🎯 **Focus:** Prioritize Lethality and Pitfall donations!\n\n"
                "*(For full details, select the Full Guide!)*"
            ),
            color=discord.Color.dark_magenta(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="beartrap_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🐻 Bear Trap Guide (Full) 🐻", color=discord.Color.dark_magenta()
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
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="timeline_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline 🏰",
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
            color=discord.Color.gold(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="timeline_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
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
            color=discord.Color.gold(),
        )
        embed.set_image(url="https://i.imgur.com/qtn62GE.png")
        await self.update_message(interaction, embed)


class CastleView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="castle_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🏰 King's Castle & KvK Guide 🏰",
            description=(
                "👑 **Goal:** First to occupy for 2.5hrs continuously, or longest total accumulation.\n"
                "🎯 **Defenses:** Hold Castle & Turrets (Turrets fire on occupants unless you hold BOTH!). Red Zone teleports random cities!\n"
                "🛡️ **Formations:** Attack: 50% Inf, 20% Cav, 30% Arch. Defense: 60% Inf, 20% Cav, 20% Arch.\n"
                "🚨 **Healing:** NEVER 'Heal All'. Heal in 30-45min batches & mash alliance 'Help' for instant free heals!\n"
                "⚔️ **Reinforcing:** Send pure Infantry without heroes so you don't override defensive buffs!"
            ),
            color=discord.Color.purple(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="castle_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🏰 King's Castle & KvK (Full) 🏰", color=discord.Color.purple()
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
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="fac_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🗺️ Sancs, Forts & Outposts Guide 🗺️",
            description=(
                "🚩 **Connection:** Outposts MUST touch alliance Banners. Sanctuaries & Fortresses DO NOT (just teleport)!\n"
                "⏱️ **Winning:** Outposts require 15-30 mins depending on level. Sancs/Forts need 30 mins continuous! Or hold at 2hr expiry.\n"
                "🩸 **Losses:** Outpost Lv.4 is a LETHAL 10% perm loss! Sancs/Forts/Others are 0% perm loss (Infirmary only).\n"
                "🤝 **Rebels:** NEVER solo rebel NPCs! Mass rally so the entire alliance gets 15x 'First Capture' loot.\n"
                "⚔️ **Defensive Ratio:** Reinforce garrisons with PURE Infantry without heroes to save the stats!"
            ),
            color=discord.Color.blue(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="fac_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🗺️ Sancs, Forts & Outposts (Full) 🗺️", color=discord.Color.blue()
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


class OasisView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="oasis_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌴 Oasis Island Guide 🌴",
            description=(
                "💧 **Essence Farming:** Log in 2x/day. Rush Reservoir Lv.4 for 2nd worker. Place touching cacti/chests. Reset pathing by exit/re-enter. Clear for Purifiers.\n"
                "🏗️ **Building:** Early buy T1 greys for quests. Then T3 blues. Avoid type limits & 50% recycle nerf.\n"
                "📈 **Stats:** Phase 1: Economy boosts. Phase 2: Lethality/Health. Golden Sunset Wonder. Water allies daily.\n"
                "⚔️ **Combat:** Rally leader gets island stats; joiners send damage heroes left. Bear Hunt: 10% Inf/10% Cav/80% Arch."
            ),
            color=discord.Color.teal(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="oasis_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌴 KINGSHOT MEGA-ALLIANCE: ULTIMATE OASIS ISLAND GUIDE 🌴",
            color=discord.Color.teal(),
        )
        embed.description = (
            "Oasis Island (unlocks at Town Center Lv. 19) is Kingshot's hidden engine for massive, permanent stat scaling. Based on the current competitive meta and StratGameSloth's \"Build Smart & Grow FAST\" video, here is how our alliance will out-scale the server from Day 1.\n\n"
            "💧 1. ESSENCE FARMING & WORKER PATHING HACKS\n"
            "Water Essence is your island currency. The Fountain of Life caps at 12 hours of storage—log in twice a day or you are bleeding free progression!\n"
            "Rush Reservoir Lv. 4: This is priority #1! It unlocks a 2nd worker, instantly doubling your cactus-clearing speed and passive essence income.\n"
            "Micromanage the Reservoir: Workers physically walk to chop cacti. Move your Reservoir directly touching the cacti or hidden chests you want to harvest to completely eliminate travel time.\n"
            "Reset Pathing AI: If your workers target the wrong cactus across the map, simply exit the island and re-enter. This resets their AI targeting RNG!\n"
            'The Purifier Rush: Focus purely on clearing all cacti. Once the island is clear, your Reservoirs permanently convert into "Purifiers," generating passive essence forever.\n\n'
            '🏗️ 2. BUILDING STRATEGY & THE "QUEST EXPLOIT"\n'
            'The Early Quest Hack: Buy the cheapest 1x1 Grey (T1) items for 1,000 essence early on. This rapidly knocks out the "Make X Shop Purchases" quests, giving you a massive early water injection to reinvest.\n'
            "Pivot to Blue (T3): Once your Fountain hits Lv. 4, stop buying Greys/Greens! Blue buildings have the absolute best Essence-to-Prosperity ratio (15 water per prosperity vs. 20 for greys).\n"
            '⛔ Mistake 1 - The "Type Limit" Trap: Every decoration has a strict limit. If an item\'s limit is 4/4, placing a 5th gives ZERO stats and ZERO prosperity. Extra copies are purely cosmetic and a massive waste of early water. Only use duplicates to upgrade buildings!\n'
            "⛔ Mistake 2 - The 50% Recycle Nerf: NEVER sell items back to the Recycle Shop unless absolutely desperate. The devs nerfed it to a 50% refund. If you need space for better buildings, simply Store your old items to preserve your overall build value.\n\n"
            "📈 3. STAT BOOSTING & ALLIANCE SYNERGY\n"
            "Phase 1 (Economy): First, upgrade buildings that provide Construction, Research, and Training Speed. These compound your account's growth immensely over your first month.\n"
            "Phase 2 (Combat): When upgrading combat stats, always prioritize Lethality and Health over Attack/Defense. Focus heavily on Infantry HP (your frontline sponge) and Archer Lethality (your main DPS).\n"
            "Golden Sunset Wonder: Push your Fountain to Lv. 10 to unlock this lighthouse. Buy the blueprints weekly from the Marketplace for insane endgame PvP buffs (Squad Vitality).\n"
            "Water Your Allies (6-Hour Rule): You and your ally BOTH gain bonus Water Essence by watering each other's Fountains. You can help a player once every 6 hours. Make it a daily habit to sweep the alliance member list! Coordinated alliances get an infinite essence loop here.\n\n"
            "📌- Do not waste your early water, follow the pathing tricks, and we will effortlessly dominate this server. Together we conquer!\n\n"
            "**Image Guide:** https://i.imgur.com/ZbX964l.jpeg\n"
            "**Optimal Chest Path:** https://i.imgur.com/WpXdI1P.png"
        )
        embed.set_image(url="https://i.imgur.com/ZbX964l.jpeg")
        await self.update_message(interaction, embed)


class DrillCampView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide",
        style=discord.ButtonStyle.primary,
        custom_id="drillcamp_mini",
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="⛺ Drill Camp Guide ⛺",
            description=(
                "⛺ **Rule:** Only level 5 heroes! Everyone else copies their level in Drill Camp.\n"
                "🚫 **Warning:** XP from leveling non-instructors is NOT refunded in Drill Camp! Reset them first.\n"
                "⭐ **Stats:** Hero level matters less (mostly Troop cap). Core combat strength is from Stars & Gear.\n"
                "❌ **Shop:** NEVER buy XP from shops. It's less valuable late game.\n"
                "🔄 **Slots:** Keep important rally joiners leveled. Drop unused/weak PvE heroes first."
            ),
            color=discord.Color.orange(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="drillcamp_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="⛺ Drill Camp Guide ⛺", color=discord.Color.orange()
        )
        embed.description = (
            "**What Drill Camp Does**\n"
            "Drill Camp lets you level only 5 heroes and have the rest copy their level.\n"
            "• **Instructors:** Your 5 main leveled heroes\n"
            "• **Drill Slots:** Other heroes match the lowest instructor level\n\n"
            "**Core Rule: Only level 5 heroes. Ever.**\n"
            "Everyone else goes into Drill Camp. If you’re leveling extra heroes outside of that, you’re wasting XP.\n\n"
            "**Avoid This Mistake**\n"
            "If you level a hero, then put them into Drill Camp, that XP is **NOT** refunded. It’s stuck there.\n"
            "*Fix it:* Remove the hero from Drill Camp, reset their level, and put them back in (has a cooldown).\n\n"
            "**Does Hero Level Even Matter?**\n"
            "Not as much as you think. It affects Conquest stats, Troop capacity, and Escort size. It does NOT affect Expedition attack/defense, Health/lethality, or Core combat strength (these come from Star level, Gear & Widgets).\n\n"
            "**Who Should Be Instructors / Go in Drill Camp?**\n"
            "Instructors don't matter much. Don't overthink it. For slots, prioritize heroes you actively use. Ignore low-impact or unused heroes.\n\n"
            "**Mid/Late Game Shift**\n"
            "Eventually, you max your 5 instructors (~Level 80) and XP becomes slower to gain/less valuable short-term. **Do NOT waste currency buying XP from shops.**\n\n"
            "**Late Game Problem: Too Many Heroes**\n"
            "You’ll hit a point where you have more heroes than Drill slots. Keep core combat/rally heroes inside. Leave unused PvE heroes at level 1.\n"
            "*Sneaky Optimization:* Even a level 1 hero can use maxed skills in rallies (but lower level = fewer troops sent). Keep important rally/join heroes leveled, drop low-impact PvE heroes first."
        )
        # Placeholder for the requested image link
        embed.set_image(url="https://i.imgur.com/placeholder.jpeg")
        await self.update_message(interaction, embed)


class ExpeditionCombatView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide",
        style=discord.ButtonStyle.primary,
        custom_id="expedition_mini",
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="⚔️ Expedition Combat Guide ⚔️",
            description=(
                "⚔️ **Roles:** Infantry (Tanks/Soak Damage) > Cavalry (Counter) > Archers (DPS/Win Fights).\n"
                "⚙️ **Stats:** Lethality & Health are best! Archers need Lethality; Infantry need Health.\n"
                "📈 **Buffs:** Multiplicative buffs (Heroes/Widgets) decide outcomes. They scale harder late game.\n"
                "🔥 **Rallies:** Rally leader stats matter most! Joiners' troop buffs don't apply. Send correct heroes.\n"
                "🏥 **Losses:** ALWAYS have infirmary space! High-risk fights with a full infirmary = permanent troop loss."
            ),
            color=discord.Color.red(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="expedition_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="⚔️ Expedition Combat Guide ⚔️", color=discord.Color.red()
        )
        embed.description = (
            "**Troop Roles (Core Foundation)**\n"
            "Combat follows a loose counter system:\n"
            "• **Infantry → beats Cavalry:** Tanks. High health/defense. Front line.\n"
            "• **Cavalry → beats Archers:** Balanced stats. Can bypass frontline (20% chance).\n"
            "• **Archers → beats Infantry:** Main damage dealers. High attack/lethality, low survivability.\n"
            "👉 *Takeaway:* Infantry = soak damage, Archers = deal damage, Cavalry = situational counter.\n\n"
            "**Key Combat Stats & Mechanics**\n"
            "Battles are automated, turn-based simulations. Most units hit the frontline first. If your frontline dies, your backline gets exposed fast.\n"
            "• **Health & defense:** How much damage a troop can take.\n"
            "• **Lethality & attack:** Damage dealt, weakens enemy troops.\n"
            "Health & defense vs lethality & attack are multiplied together. The narrower the stat difference, the higher the multiplier! Since defense/attack are usually naturally higher, prioritize Health and Lethality.\n"
            "👉 *Best focus:* Archers → Lethality, Infantry → Health.\n\n"
            "**Buffs & Rallies**\n"
            "• **Standard (Additive):** Research, gear, buildings.\n"
            "• **Multiplicative:** Hero abilities, titles, widgets (Game-changing!).\n"
            "• **Rallies:** Rally leader stats = everything. Joiners' standard buffs do NOT apply! If joining, send correct troops and the correct hero.\n\n"
            "**Troop Casualties**\n"
            "Lightly Injured return immediately. Injured go to the infirmary. Losses are permanently gone. If infirmary is full, extra troops DIE. Always keep space!\n"
            "👉 *High-Risk:* Attacking player cities, Level 4 outposts. *Safer:* Defending structures, PvE."
        )
        embed.set_image(url="https://i.imgur.com/placeholder.jpeg")
        await self.update_message(interaction, embed)


class PlaybookView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="playbook_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="👑 The Definitive Kingshot Playbook 👑",
            description=(
                "👑 **The Golden Rule:** HOARD EVERYTHING! Spend gems/speedups only on high-yield events.\n"
                "🏗️ **Economy:** Rush TC19, then prioritize military at TC23/26/30. Alt farm accounts are mandatory!\n"
                "💎 **VIP:** Rush VIP 6 for 2nd march queue. Never buy mystery items at full price.\n"
                "🧬 **Heroes:** Hoard for 120 HoG spins. Don't waste gems on Gen 1.\n"
                "⚔️ **Rallies:** Put strong joiner heroes in the left slot. Bear Hunt: 10% Inf / 10% Cav / 80% Arch.\n"
                "⚖️ **Endgame:** The TrueGold T11 wall is huge. Stop at TG5 if F2P!"
            ),
            color=discord.Color.gold(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="playbook_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="👑 THE DEFINITIVE KINGSHOT PLAYBOOK 👑", color=discord.Color.gold()
        )
        embed.description = (
            "📜 **THE GOLDEN RULE**\n"
            "**HOARD EVERYTHING.** Patience is your primary currency. Spreading resources thinly across daily activities = catastrophic late-game failure. Only spend Gems, speedups, and assets during high-yield, designated events.\n\n"
            "🏗️ **BASE & RESOURCE ECONOMY**\n"
            "• **TC Rushing:** Push relentlessly to TC19 (unlocks Island).\n"
            "• **Military Spikes:** At TC23, TC26, and TC30, immediately pivot all focus to military buildings (Barracks, Range, Stable) over economy.\n"
            "• **Speedups:** DO NOT use troop training speedups until you unlock T7 troops.\n"
            "• **Farm Accounts (Mandatory):** For the TC28-30 resource drought, build an alt account. Keep the farm's storehouse at Level 1 (no protection cap) and attack it with your main to siphon RSS.\n"
            "• **Decree Exploit:** Stack them in this exact order: Urgent Mobilization ➡️ Productivity Day (100% buff) ➡️ Rush Job (doubles the 5-day instant yield).\n\n"
            "💎 **VIP & STORE PRIORITIES**\n"
            "• **VIP 6:** Rush this ASAP (unlocks 2nd march queue).\n"
            "• **VIP 7:** Next priority (daily Mythic hero shard).\n"
            "• **Artisan's Vision:** The ultimate late-game bottleneck for gear. Buy with Gilded Threads/Satin (100% value). NEVER break down Artisan's Vision into lower materials. Max buy from Swordland & KvK shops.\n"
            "• **Mystery Store:** Buy Widget Chests (50% off). Never buy full price.\n\n"
            "🧬 **HERO GENERATIONAL META**\n"
            "• **Gen 1:** Ignore premium heroes (Helga/Amadeus) if F2P. Stick to Jabel, Quinn, and Howard. Get Saul to 3-stars strictly for his massive building speed buff.\n"
            "• **Gen 2 Prep:** Hoard 465 Mythic Shards for Day 70-80 to instantly drop a 4-star Zoe or Marlin.\n"
            "• **Hero Roulette / HoG:** Save Gems for exactly 120 spins (max milestones). Split your spins across HoG Day 2 & Day 3 to double-dip on points. Stop spending the second you hit the final milestone.\n\n"
            "⚔️ **COMBAT & RALLY DYNAMICS**\n"
            "• **Rally Joiners (The Lead Hero Trick):** The game ignores joiner hero gear. It only calculates your Lead Hero's top-right skill (Lethality/Attack). Put Chenko, Yeonwoo, or Amane in your primary left slot to massively buff the whale leading the rally.\n"
            '• **The Pitfall (Bear Hunt) 1/1/8 Rule:** Maximum damage ratio is 10% Infantry / 10% Cavalry / 80% Archers. You need the 10% melee to bypass the game\'s hidden "zero-troop" damage penalty.\n'
            "• **Arena Snipe:** Save your 10 daily attacks for the last 1-10 minutes before 00:00 UTC server reset to secure your rank.\n\n"
            "🛡️ **GEAR & PETS**\n"
            "• **Gear Focus:** Only upgrade your top 3 main march heroes. Priority: Infantry Gloves & Chest (Survivability) ➡️ Cavalry/Archers Helmets & Boots (Lethality).\n"
            "• **Pets:** Bison is vital for instantly draining RSS tiles. Lynx gives 35-60 instant Stamina.\n"
            "• **Note on Stamina:** It has a hidden overcap! Use Lynx/items to hoard past 200/200 before major events. Keep re-rolling Pet Refining until you lock in Infantry Health and Archer Lethality.\n\n"
            "⚖️ **ENDGAME: THE TRUEGOLD ERA (TC30+)**\n"
            "• **Gathering:** Force your marches to gather Iron and Stone. The Truegold Crucible demands equal RSS, and those two are the slowest to farm. Do your 6x daily Crucible refinements without fail.\n"
            "• **The F2P T11 Wall:** The Truegold Dust cost for T11 is astronomical (13.4k Dust). If you are a low spender, STOP at Truegold 5 (TG5). Maximize your T10 troops—a fully scaled TG8 T10 march will destroy an under-researched T11 march."
        )
        embed.set_image(url="https://i.imgur.com/placeholder.jpeg")
        await self.update_message(interaction, embed)


class WhaleView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="whale_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🐳 Whale Guide 🐳",
            description=(
                "👑 **Leadership:** Whales lead strong rallies. Success requires active, well-coordinated joiners!\n"
                "⚙️ **Investment 1:** Prioritize **Hero Gear**, it gives huge stat boosts. Gold Gear/Lucky Chests > Mithril.\n"
                "🧬 **Investment 2:** Max season heroes/widgets early. 5-star Amadeus ASAP (Top tier hero into Gen 6).\n"
                "📈 **Stats:** Prioritize Health & Lethality (Inf Health / Arch Lethality). Use Charms, Tech, and Pets for this.\n"
                "⚔️ **Troops:** POWER ≠ STATS! Troops boost event points but inflate matchmaking. Invest in evergreen stats!"
            ),
            color=discord.Color.blue(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide", style=discord.ButtonStyle.secondary, custom_id="whale_full"
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🐳 Whale Guide (Full) 🐳", color=discord.Color.blue()
        )
        embed.description = (
            "**Rally Leadership & Stability**\n"
            "A whale’s role goes beyond raw power. It’s about leadership, consistency, and creating value. Lead rallies that win & deal max damage. Active, well-coordinated joiners create a win-win environment. Maintain order and protect the alliance.\n\n"
            "**#1 Investment: Hero Gear**\n"
            "Provides massive stat boosts without diminishing returns. Highly recommended to focus investment here.\n"
            "**Cost (1 Piece):** XP (574.3k), Hammers (2.1k), Mithril (150), Mythic Pieces (90).\n"
            "**Priority:** Gold gear & lucky chests > Mithril > hammers > XP.\n\n"
            "**Next Investment: Heroes & Amadeus**\n"
            "• **Season Heroes:** Always max season heroes. Refer to the timeline for next gen heroes.\n"
            "• **Advantage:** Massive advantage having max heroes when a new generation starts.\n"
            "• **Widgets:** The most important investment (adds multiplicative stats). Max them! ($1/widget). Buy discounted in Mystery shop, Buccaneer Bounty, etc.\n"
            "• **Amadeus:** The most important hero in the game (relevant into Gen 6). Available in first 3 Hall of Governors or VIP7. 5-star him ASAP.\n\n"
            "**Priority Stats & Items**\n"
            "Health & lethality are most important. Use optimizer tools.\n"
            "• **Rank:** 1. Inf Health 2. Arch Lethality 3. Inf Def 4. Arch Atk 5. Cav Lethality 6. Cav Atk\n"
            "• Focus on items boosting these (Charms, Tech, Oasis, Taming marks). These are forever investments.\n\n"
            "**Troops (Not Evergreen)**\n"
            "After ~1.5M troops, there's little account progression.\n"
            "• **Pros:** Event points (KvK/Strongest Governor). More troops = more kills.\n"
            "• **Cons:** Matchmaking uses overall power. POWER ≠ STATS! Training drains speedups. Vikings: more home troops = fewer points.\n"
            "• **Verdict:** Don't hold back training or using them! Focus on evergreen stats."
        )
        embed.set_image(url="https://i.imgur.com/placeholder.jpeg")
        await self.update_message(interaction, embed)


class TransferView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="transfer_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌐 Kingdom Transfer Event 🌐",
            description=(
                "♻️ **Timing:** Every 30–45 days. Takes a week with prep, invite, and open ticket phases.\n"
                "📝 **Requirements:** Must be under power limit, leave alliance, and lack active battles/roles (King). Requires Transfer Passes!\n"
                "🕰️ **Phases:** Sun-Tue: Pre-Transfer. Wed-Thu: Invitational. Fri-Sat: Open Transfer.\n"
                "💳 **Passes:** Price scales up from $5 to $100. Resets monthly!\n"
                "⚙️ **Effects:** City moves to Badland with 24h shield. Arena points reset, shop resets, and unprotected resources are lost."
            ),
            color=discord.Color.blue(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="transfer_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🌐 Kingdom Transfer Event (Full) 🌐", color=discord.Color.blue()
        )
        embed.description = (
            "**Event Time:** 2026.4.12 00:00:00(UTC) - 2026.4.18 23:59:59(UTC)\n"
            "**Frequency:** Every 30–45 days\n\n"
            "**Kingdom Groups**\n"
            "• Group 1: 1 to 175\n"
            "• Group 2: 176 to 417\n"
            "• Group 3: 418 to 674\n"
            "• Group 4: 675 to 1007\n"
            "• Group 5: 1008 to 1159\n"
            "• Group 6: 1160 to 1221\n"
            "• Group 7: 1222 to 1331\n\n"
            "**Transfer Requirements**\n"
            "• Power must be below the transfer limit\n"
            "• Town Center must meet level requirement (depends on kingdom age)\n"
            "• No active battles during transfer\n"
            "• Must leave your alliance first\n"
            "• Cannot be King or Transfer Manager\n"
            "• At least 25 days since last transfer\n"
            "• Max 4 characters per kingdom\n"
            "• Requires Transfer Passes (1–50 depending on Power and rank)\n"
            "• Both kingdoms must be from the same generation\n\n"
            "**Event Phases**\n"
            "1️⃣ **Pre-Transfer (3 days, Sun–Tue):** Kings set Power limits, open chat, and players plan transfers.\n"
            "2️⃣ **Invitational Transfer (2 days, Wed–Thu):**\n"
            "  - Leading Kingdoms: 20 invites + 10 open slots.\n"
            "  - Ordinary Kingdoms: 35 invites + 3 special slots (for players above Power limit).\n"
            "3️⃣ **Open Transfer (2 days, Fri–Sat):**\n"
            "  - Leading Kingdoms: 10 open slots.\n"
            "  - Ordinary Kingdoms: 20 open slots. First come, first served.\n\n"
            "💳 **Transfer Pass Packs:** 1 Pass $5, 2 Passes $10, 3 Passes $20, 4 Passes $50, 5 Passes $100 (15 available). Resets monthly.\n\n"
            "**Transfer Effects**\n"
            "• City moves to Badland + 24h shield\n"
            "• Removed from chats\n"
            "• Arena Points reset to 1000\n"
            "• Event progress continues if active in both kingdoms; otherwise rewards sent by mail\n"
            "• Shop and bundle purchases reset\n"
            "• Excess resources beyond Storehouse protection are lost"
        )
        embed.set_image(url="https://i.imgur.com/placeholder.jpeg")
        await self.update_message(interaction, embed)


class DailyOpsView(BaseGuideView):
    @discord.ui.button(
        label="Mini Guide", style=discord.ButtonStyle.primary, custom_id="dailyops_mini"
    )
    async def mini_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🚀 Daily Operations Directive 🚀",
            description=(
                "⏱️ **Rotations:** Clear Conquest & Island Water every 8h. Gather Iron/Stone.\n"
                "⚔️ **Map Clears:** Claim 2x stamina. Do 50/50 terrors. Clear all intel. Arena before reset.\n"
                "🤝 **Alliance & Pets:** Max donations, clear gifts. Do pet missions & pop skills.\n"
                "💸 **Store Sweeps:** Buy 50% off Widget Chests. Wipe Nomadic RSS trades. Buy VIP/Speedups. Max 5% gem bank.\n"
                "👑 **Endgame (TC30+):** 6x TG Refinements! Truegold Dust daily. Use Decree Exploit.\n"
                "🛑 **Rule:** 100% queue uptime! Max daily chests. Minimums on non-KvK events."
            ),
            color=discord.Color.brand_red(),
        )
        await self.update_message(interaction, embed)

    @discord.ui.button(
        label="Full Guide",
        style=discord.ButtonStyle.secondary,
        custom_id="dailyops_full",
    )
    async def full_guide(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="🚀 Daily Operations Directive (Full) 🚀",
            color=discord.Color.brand_red(),
        )
        embed.description = (
            "> *Execute the matrix daily. Do not bleed efficiency.*\n\n"
            "**⏱️ 8-HOUR ROTATIONS**\n"
            "• **Conquest:** Clear every 8h to prevent token cap.\n"
            "• **Island Water:** Collect & use all 3 daily top-ups.\n"
            "• **Gathering:** Reset 4 marches. Prioritize **Iron/Stone** for Truegold.\n\n"
            "**⚔️ STAMINA & MAP CLEARS**\n"
            "• **Stamina Drops:** Claim 2x daily free recharges.\n"
            "• **Terrors:** Auto-join rallies until 50/50 cap. Manually kill 5 daily for top-tier loot.\n"
            "• **Intel:** Complete ALL missions. (Grants Truegold at TC30).\n"
            "• **Arena:** Do challenges right before 0:00 UTC reset to maximize placement.\n\n"
            "**🤝 ALLIANCE & PETS**\n"
            "• **Contributions:** Max out tech donations whenever online. Clear gift menu constantly.\n"
            "• **Pets:** Complete all 4 daily missions. Pop skills (Bison RSS drain, Lynx stamina) on cooldown.\n\n"
            "**💸 STORE SWEEPS**\n"
            "• **Mystery Store:** Refresh and buy **Widget Chests ONLY** (50% off).\n"
            "• **Nomadic Store:** Wipe out all RSS-to-RSS exchanges.\n"
            "• **Alliance Store:** Buy Speedups, VIP points, Teleports. **NO healing speedups.**\n"
            "• **Dailies:** Deposit max gems into 5% daily bank. Grab free VIP & Deal chests.\n\n"
            "**👑 ENDGAME ECONOMY (TC30+)**\n"
            "• **Truegold Crucible:** Execute 6x refinements daily. Do not miss this.\n"
            "• **War Academy:** Exchange Gold for Truegold Dust daily.\n"
            "• **Decree Exploit:** Fire in this exact order: `Urgent Mobilization` ➡️ `Productivity Day` (100% buff) ➡️ `Rush Job` (doubles the payout).\n\n"
            "**🛑 THE GOLDEN RULES**\n"
            "1. **100% Uptime:** Never let training or research queues idle.\n"
            "2. **Event Discipline:** Do non-KvK events strictly to minimum reward thresholds.\n"
            "3. **Daily Missions:** 100% completion for max chests."
        )
        await self.update_message(interaction, embed)


class GuidesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_or_translate_guide(self, ctx, embed, view=None):
        target_lang = None
        try:
            target_lang = await self.bot.db.hget(
                "global_translator_subs", str(ctx.author.id)
            )
        except Exception:
            pass

        if target_lang:
            prompt = f"Translate the following to {target_lang}. Be concise and strictly literal. No AI fluff.\nTitle: {embed.title}\nDescription: {embed.description}"
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                if response and response.text:
                    translation = response.text.strip()
                    t_embed = discord.Embed(
                        title=f"{embed.title} ({target_lang.capitalize()})",
                        description=translation,
                        color=embed.color,
                    )
                    t_embed.set_footer(text="Translated via Global Translator")
                    embed = t_embed
            except Exception:
                pass

        if ctx.guild is None:
            content = f"**{embed.title}**\n\n{embed.description}"
            if embed.image and getattr(embed.image, "url", None):
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

    @commands.hybrid_group(
        name="guides", aliases=["guide"], invoke_without_command=True
    )
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
                "`!guides oasis` - View the Oasis Island Guide.\n"
                "`!guides drillcamp` - View the Drill Camp Hero Leveling Guide.\n"
                "`!guides expedition` - View the Expedition Combat & Stats Guide.\n"
                "`!guides playbook` - View the Definitive Kingshot Playbook.\n"
                "`!guides whale` - View the Whale Guide.\n"
                "`!guides transfer` - View the Kingdom Transfer Event Guide.\n"
                "`!guides dailyops` - View the Daily Operations Directive.\n"
                "`!castle` - View information and strategies for the Kingdom of Power (KvK) Castle Battle.\n"
                "`!facility` - View information and strategies for Sanctuaries, Outposts, and Fortresses."
            ),
            color=discord.Color.green(),
        )
        await self.send_or_translate_guide(ctx, embed)

    @guides_command.command(name="events")
    async def guides_events(self, ctx):
        """Placeholder for all events guides hub."""
        embed = discord.Embed(
            title="📅 Event Guides",
            description="Event-specific guides are being categorized! Check back later, or use `!castle` and `!facility` directly for now.",
            color=discord.Color.gold(),
        )
        await self.send_or_translate_guide(ctx, embed)

    @guides_command.command(name="viking")
    async def guides_viking(self, ctx):
        """View the Viking Vengeance Event Guide."""
        embed = discord.Embed(
            title="🛡️ Viking Vengeance Guide 🛡️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_red(),
        )
        await self.send_or_translate_guide(ctx, embed, view=VikingView(self.bot))

    @guides_command.command(name="championship", aliases=["champ"])
    async def guides_championship(self, ctx):
        """View the Alliance Championship Event Guide."""
        embed = discord.Embed(
            title="🏆 Alliance Championship Guide 🏆",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.brand_green(),
        )
        await self.send_or_translate_guide(ctx, embed, view=ChampionshipView(self.bot))

    @guides_command.command(name="beartrap")
    async def guides_beartrap(self, ctx):
        """View the Bear Trap Event Guide."""
        embed = discord.Embed(
            title="🐻 Bear Trap Guide 🐻",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.dark_magenta(),
        )
        await self.send_or_translate_guide(ctx, embed, view=BearTrapView(self.bot))

    @guides_command.command(name="oasis")
    async def guides_oasis(self, ctx):
        """View the Oasis Island Guide."""
        embed = discord.Embed(
            title="🌴 Oasis Island Guide 🌴",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.teal(),
        )
        await self.send_or_translate_guide(ctx, embed, view=OasisView(self.bot))

    @guides_command.command(name="drillcamp", aliases=["drill"])
    async def guides_drillcamp(self, ctx):
        """View the Drill Camp Guide."""
        embed = discord.Embed(
            title="⛺ Drill Camp Guide ⛺",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.orange(),
        )
        await self.send_or_translate_guide(ctx, embed, view=DrillCampView(self.bot))

    @guides_command.command(name="expedition", aliases=["combat"])
    async def guides_expedition(self, ctx):
        """View the Expedition Combat Guide."""
        embed = discord.Embed(
            title="⚔️ Expedition Combat Guide ⚔️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.red(),
        )
        await self.send_or_translate_guide(
            ctx, embed, view=ExpeditionCombatView(self.bot)
        )

    @guides_command.command(name="playbook", aliases=["definitive"])
    async def guides_playbook(self, ctx):
        """View the Definitive Kingshot Playbook."""
        embed = discord.Embed(
            title="👑 The Definitive Kingshot Playbook 👑",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.gold(),
        )
        await self.send_or_translate_guide(ctx, embed, view=PlaybookView(self.bot))

    @guides_command.command(name="dailyops", aliases=["daily"])
    async def guides_dailyops(self, ctx):
        """View the Daily Operations Directive."""
        embed = discord.Embed(
            title="🚀 Daily Operations Directive 🚀",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.brand_red(),
        )
        await self.send_or_translate_guide(ctx, embed, view=DailyOpsView(self.bot))

    @guides_command.command(name="whale")
    async def guides_whale(self, ctx):
        """View the Whale Guide."""
        embed = discord.Embed(
            title="🐳 Whale Guide 🐳",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue(),
        )
        await self.send_or_translate_guide(ctx, embed, view=WhaleView(self.bot))

    @guides_command.command(name="transfer")
    async def guides_transfer(self, ctx):
        """View the Kingdom Transfer Guide."""
        embed = discord.Embed(
            title="🌐 Kingdom Transfer Event 🌐",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue(),
        )
        await self.send_or_translate_guide(ctx, embed, view=TransferView(self.bot))

    @guides_command.command(name="timeline")
    async def guides_timeline(self, ctx):
        """View the Server Kingdom Journey Timeline."""
        embed = discord.Embed(
            title="🏰 Kingdom Journey Timeline 🏰",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.gold(),
        )
        await self.send_or_translate_guide(ctx, embed, view=TimelineView(self.bot))

    @commands.hybrid_group(name="castle", aliases=["kvk"], invoke_without_command=True)
    async def castle_command(self, ctx):
        embed = discord.Embed(
            title="🏰 King's Castle & KvK Guide 🏰",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.purple(),
        )
        await self.send_or_translate_guide(ctx, embed, view=CastleView(self.bot))

    @commands.hybrid_group(
        name="facility",
        aliases=["sanctuary", "outpost", "fortress"],
        invoke_without_command=True,
    )
    async def facility_command(self, ctx):
        embed = discord.Embed(
            title="🗺️ Sanctuaries, Outposts & Fortresses Guide 🗺️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue(),
        )
        await self.send_or_translate_guide(ctx, embed, view=FacilityView(self.bot))

    @commands.hybrid_command(name="drillcamp", aliases=["drill"])
    async def drillcamp_command(self, ctx):
        """View the Drill Camp Guide."""
        embed = discord.Embed(
            title="⛺ Drill Camp Guide ⛺",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.orange(),
        )
        await self.send_or_translate_guide(ctx, embed, view=DrillCampView(self.bot))

    @commands.hybrid_command(name="expedition", aliases=["combat"])
    async def expedition_command(self, ctx):
        """View the Expedition Combat Guide."""
        embed = discord.Embed(
            title="⚔️ Expedition Combat Guide ⚔️",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.red(),
        )
        await self.send_or_translate_guide(
            ctx, embed, view=ExpeditionCombatView(self.bot)
        )

    @commands.hybrid_command(name="playbook", aliases=["definitive"])
    async def playbook_command(self, ctx):
        """View the Definitive Kingshot Playbook."""
        embed = discord.Embed(
            title="👑 The Definitive Kingshot Playbook 👑",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.gold(),
        )
        await self.send_or_translate_guide(ctx, embed, view=PlaybookView(self.bot))

    @commands.hybrid_command(name="whale")
    async def whale_command(self, ctx):
        """View the Whale Guide."""
        embed = discord.Embed(
            title="🐳 Whale Guide 🐳",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue(),
        )
        await self.send_or_translate_guide(ctx, embed, view=WhaleView(self.bot))

    @commands.hybrid_command(name="transfer")
    async def transfer_command(self, ctx):
        """View the Kingdom Transfer Guide."""
        embed = discord.Embed(
            title="🌐 Kingdom Transfer Event 🌐",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.blue(),
        )
        await self.send_or_translate_guide(ctx, embed, view=TransferView(self.bot))

    @commands.hybrid_command(name="dailyops", aliases=["daily"])
    async def dailyops_command(self, ctx):
        """View the Daily Operations Directive."""
        embed = discord.Embed(
            title="🚀 Daily Operations Directive 🚀",
            description="Please select either the short **Mini Guide** or the detailed **Full Guide** using the buttons below.",
            color=discord.Color.brand_red(),
        )
        await self.send_or_translate_guide(ctx, embed, view=DailyOpsView(self.bot))


async def setup(bot):
    await bot.add_cog(GuidesCog(bot))
