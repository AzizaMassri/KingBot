import discord
from discord.ext import commands
import math
import os
from google import genai

# Database from trooptraining.html
TROOP_DATA = {
    0: {"name": "None / Fresh", "time": 0, "points": 0, "hog": 0, "bread": 0, "wood": 0, "stone": 0, "iron": 0},
    1: {"name": "T1", "time": 12, "points": 3, "hog": 90, "bread": 23, "wood": 34, "stone": 6, "iron": 2},
    2: {"name": "T2", "time": 17, "points": 4, "hog": 120, "bread": 36, "wood": 54, "stone": 9, "iron": 4},
    3: {"name": "T3", "time": 24, "points": 5, "hog": 180, "bread": 58, "wood": 86, "stone": 15, "iron": 5},
    4: {"name": "T4", "time": 32, "points": 8, "hog": 265, "bread": 75, "wood": 111, "stone": 19, "iron": 6},
    5: {"name": "T5", "time": 44, "points": 12, "hog": 385, "bread": 97, "wood": 144, "stone": 24, "iron": 8},
    6: {"name": "T6", "time": 60, "points": 18, "hog": 595, "bread": 117, "wood": 173, "stone": 29, "iron": 10},
    7: {"name": "T7", "time": 83, "points": 25, "hog": 830, "bread": 175, "wood": 258, "stone": 44, "iron": 14},
    8: {"name": "T8", "time": 113, "points": 35, "hog": 1130, "bread": 349, "wood": 516, "stone": 87, "iron": 28},
    9: {"name": "T9", "time": 131, "points": 45, "hog": 1485, "bread": 872, "wood": 1290, "stone": 217, "iron": 70},
    10: {"name": "T10", "time": 152, "points": 60, "hog": 1960, "bread": 1740, "wood": 2579, "stone": 433, "iron": 140},
    11: {"name": "T11", "time": 180, "points": 75, "hog": 2500, "bread": 4357, "wood": 6448, "stone": 1081, "iron": 349},
}

BUILDING_DATA = {
    1: {"time": 0, "wood": 0, "stone": 0, "iron": 0, "bread": 0, "gold": 0},
    2: {"time": 6, "wood": 180, "stone": 0, "iron": 0, "bread": 0, "gold": 0},
    3: {"time": 60, "wood": 805, "stone": 0, "iron": 0, "bread": 0, "gold": 0},
    4: {"time": 180, "wood": 1800, "stone": 360, "iron": 0, "bread": 0, "gold": 0},
    5: {"time": 600, "wood": 7600, "stone": 1500, "iron": 0, "bread": 0, "gold": 0},
    6: {"time": 1800, "wood": 19000, "stone": 3800, "iron": 960, "bread": 0, "gold": 0},
    7: {"time": 3600, "wood": 69000, "stone": 13000, "iron": 3400, "bread": 0, "gold": 0},
    8: {"time": 9000, "wood": 120000, "stone": 25000, "iron": 6300, "bread": 0, "gold": 0},
    9: {"time": 16200, "wood": 260000, "stone": 52000, "iron": 13000, "bread": 0, "gold": 0},
    10: {"time": 21600, "wood": 460000, "stone": 92000, "iron": 23000, "bread": 0, "gold": 0},
    11: {"time": 27000, "wood": 1300000, "stone": 260000, "iron": 65000, "bread": 1300000, "gold": 0},
    12: {"time": 32400, "wood": 1600000, "stone": 330000, "iron": 84000, "bread": 1600000, "gold": 0},
    13: {"time": 39600, "wood": 2300000, "stone": 470000, "iron": 110000, "bread": 2300000, "gold": 0},
    14: {"time": 50400, "wood": 3100000, "stone": 630000, "iron": 150000, "bread": 3100000, "gold": 0},
    15: {"time": 64800, "wood": 4600000, "stone": 930000, "iron": 230000, "bread": 4600000, "gold": 0},
    16: {"time": 109680, "wood": 5900000, "stone": 1100000, "iron": 290000, "bread": 5900000, "gold": 0},
    17: {"time": 131640, "wood": 9300000, "stone": 1800000, "iron": 480000, "bread": 9300000, "gold": 0},
    18: {"time": 157980, "wood": 12000000, "stone": 2500000, "iron": 620000, "bread": 12000000, "gold": 0},
    19: {"time": 237000, "wood": 15000000, "stone": 3100000, "iron": 780000, "bread": 15000000, "gold": 0},
    20: {"time": 296280, "wood": 21000000, "stone": 4300000, "iron": 1000000, "bread": 21000000, "gold": 0},
    21: {"time": 385140, "wood": 27000000, "stone": 5400000, "iron": 1300000, "bread": 27000000, "gold": 0},
    22: {"time": 577740, "wood": 36000000, "stone": 7200000, "iron": 1800000, "bread": 36000000, "gold": 0},
    23: {"time": 808800, "wood": 44000000, "stone": 8900000, "iron": 2200000, "bread": 44000000, "gold": 0},
    24: {"time": 1132380, "wood": 60000000, "stone": 12000000, "iron": 3000000, "bread": 60000000, "gold": 0},
    25: {"time": 1585320, "wood": 81000000, "stone": 16000000, "iron": 4000000, "bread": 81000000, "gold": 0},
    26: {"time": 1823160, "wood": 100000000, "stone": 21000000, "iron": 5200000, "bread": 100000000, "gold": 0},
    27: {"time": 2187780, "wood": 140000000, "stone": 24000000, "iron": 7400000, "bread": 140000000, "gold": 0},
    28: {"time": 2515920, "wood": 190000000, "stone": 39000000, "iron": 9900000, "bread": 190000000, "gold": 0},
    29: {"time": 2893320, "wood": 240000000, "stone": 49000000, "iron": 12000000, "bread": 240000000, "gold": 0},
    30: {"time": 3472020, "wood": 300000000, "stone": 60000000, "iron": 15000000, "bread": 300000000, "gold": 0},
    # TG phase totals (x5 of the phase requirement)
    31: {"time": 604800 * 5, "wood": 67000000 * 5, "stone": 13000000 * 5, "iron": 3300000 * 5, "bread": 67000000 * 5, "gold": 132 * 5},
    32: {"time": 777600 * 5, "wood": 72000000 * 5, "stone": 14000000 * 5, "iron": 3600000 * 5, "bread": 72000000 * 5, "gold": 158 * 5},
    33: {"time": 950400 * 5, "wood": 79000000 * 5, "stone": 15000000 * 5, "iron": 3900000 * 5, "bread": 79000000 * 5, "gold": 238 * 5},
    34: {"time": 1036800 * 5, "wood": 82000000 * 5, "stone": 16000000 * 5, "iron": 4100000 * 5, "bread": 82000000 * 5, "gold": 280 * 5},
    35: {"time": 1209600 * 5, "wood": 84000000 * 5, "stone": 16800000 * 5, "iron": 4200000 * 5, "bread": 84000000 * 5, "gold": 335 * 5},
    36: {"time": 1296000 * 5, "wood": 96000000 * 5, "stone": 19200000 * 5, "iron": 4800000 * 5, "bread": 96000000 * 5, "gold": 200 * 5},
    37: {"time": 1555200 * 5, "wood": 100000000 * 5, "stone": 21000000 * 5, "iron": 5400000 * 5, "bread": 100000000 * 5, "gold": 240 * 5},
    38: {"time": 1728000 * 5, "wood": 130000000 * 5, "stone": 26000000 * 5, "iron": 6600000 * 5, "bread": 130000000 * 5, "gold": 240 * 5},
}

BUILDING_MULTIPLIERS = {
    "Town Center": 1.00,
    "Academy": 0.85,
    "Embassy": 0.70,
    "Camps": 0.60,
    "Infirmary/Command": 0.50
}

def parse_building_level(level_str):
    level_str = level_str.strip().upper()
    if level_str.startswith("TG"):
        try:
            val = int(level_str[2:])
            if 1 <= val <= 8:
                return 30 + val
        except ValueError:
            pass
    try:
        val = int(level_str)
        if 1 <= val <= 30:
            return val
    except ValueError:
        pass
    return None

def format_building_level(level_int):
    if level_int > 30:
        return f"TG{level_int - 30}"
    return str(level_int)

def format_time(seconds):
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)

class StatsModal(discord.ui.Modal, title='Enter Training Stats'):
    capacity = discord.ui.TextInput(
        label='Base Training Capacity',
        placeholder='e.g., 2500',
        required=True,
        max_length=6
    )
    speed = discord.ui.TextInput(
        label='Total Training Speed (%)',
        placeholder='e.g., 145.5',
        required=True,
        max_length=6
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cap = int(self.capacity.value.replace(',', '').strip())
            spd = float(self.speed.value.replace('%', '').strip())
            if cap <= 0 or spd < 0:
                raise ValueError
            self.calculator_view.base_capacity = cap
            self.calculator_view.base_speed = spd
            
            # Update the view so the user knows they entered it
            self.calculator_view.children[2].label = f"Stats Set: {cap} Cap | {spd}% Spd"
            self.calculator_view.children[2].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid numbers. Please enter raw numbers (e.g., 2500 for capacity and 145.5 for speed).", ephemeral=True)

class CurrentTierSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="None (Train Fresh)", value="0", default=True)
        ]
        for i in range(1, 11):
            options.append(discord.SelectOption(label=f"T{i} (Promote)", value=str(i)))
        super().__init__(placeholder="Select Starting Tier (or Fresh)", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_tier = int(self.values[0])
        # Update default options
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class TargetTierSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for i in range(1, 12):
            options.append(discord.SelectOption(label=f"Target: T{i}", value=str(i), default=(i==10)))
        super().__init__(placeholder="Select Target Tier", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.target_tier = int(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)


class TroopCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.base_capacity = 0
        self.base_speed = 0.0
        self.current_tier = 0
        self.target_tier = 10
        self.has_state_buff = False
        self.has_city_buff = False
        
        self.add_item(CurrentTierSelect())
        self.add_item(TargetTierSelect())

    @discord.ui.button(label="Input Base Stats", style=discord.ButtonStyle.primary, row=2)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StatsModal(self))

    @discord.ui.button(label="Toggle State Title (+50% Spd, +200 Cap)", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_state(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.has_state_buff = not self.has_state_buff
        button.style = discord.ButtonStyle.success if self.has_state_buff else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Toggle City Enhance (Cap x3)", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_city(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.has_city_buff = not self.has_city_buff
        button.style = discord.ButtonStyle.success if self.has_city_buff else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=4)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.base_capacity == 0:
            return await interaction.response.send_message("❌ Please input your base stats first! Click 'Input Base Stats'.", ephemeral=True)
            
        if self.current_tier >= self.target_tier:
            return await interaction.response.send_message("❌ Target tier must be higher than current tier!", ephemeral=True)

        await interaction.response.defer()

        # Math Logic
        final_cap = self.base_capacity
        final_speed = self.base_speed

        if self.has_state_buff:
            final_cap += 200
            final_speed += 50
            
        if self.has_city_buff:
            final_cap *= 3

        t_current = TROOP_DATA[self.current_tier]
        t_target = TROOP_DATA[self.target_tier]

        time_diff = int(t_target["time"]) - int(t_current["time"])
        pts_diff = int(t_target["points"]) - int(t_current["points"])
        hog_diff = int(t_target["hog"]) - int(t_current["hog"])

        total_time_seconds = (time_diff * final_cap) / (1 + (final_speed / 100.0))
        total_pts = pts_diff * final_cap
        total_hog = hog_diff * final_cap
        
        bread_cost = (int(t_target.get("bread", 0)) - int(t_current.get("bread", 0))) * final_cap
        wood_cost = (int(t_target.get("wood", 0)) - int(t_current.get("wood", 0))) * final_cap
        stone_cost = (int(t_target.get("stone", 0)) - int(t_current.get("stone", 0))) * final_cap
        iron_cost = (int(t_target.get("iron", 0)) - int(t_current.get("iron", 0))) * final_cap

        eff_pts_sec = total_pts / total_time_seconds if total_time_seconds > 0 else 0
        eff_hog_sec = total_hog / total_time_seconds if total_time_seconds > 0 and total_hog > 0 else 0

        action_text = "Training Fresh" if self.current_tier == 0 else "Promoting"
        embed = discord.Embed(
            title="⚔️ Kingshot Troop Calculator Results",
            color=discord.Color.gold()
        )
        embed.add_field(name="Action", value=f"{action_text} **T{self.target_tier}** (from {t_current['name']})", inline=False)
        embed.add_field(name="Queue Size", value=f"{final_cap:,} Troops", inline=True)
        embed.add_field(name="Training Speed", value=f"+{final_speed:,.1f}%", inline=True)
        embed.add_field(name="Total Time Required", value=f"⏳ **{format_time(total_time_seconds)}**", inline=False)
        
        embed.add_field(name="Resource Cost", value=f"🍞 {bread_cost:,} Bread\n🪵 {wood_cost:,} Wood\n🪨 {stone_cost:,} Stone\n⛏️ {iron_cost:,} Iron", inline=False)
        embed.add_field(name="Yield", value=f"⭐ **{total_pts:,}** General/KvK Points\n🏆 **{total_hog:,}** HoG Points", inline=False)
        
        if total_hog > 0:
            embed.add_field(name="Efficiency ROI", value=f"📈 **{eff_hog_sec:.2f}** HoG Points per second of speedup", inline=False)
            
            # Educational pro tip
            if self.current_tier > 0:
                fresh_time = int(t_target["time"]) * final_cap / (1 + (final_speed / 100.0))
                fresh_hog = int(t_target["hog"]) * final_cap
                fresh_eff = (fresh_hog / fresh_time) if fresh_time > 0 else 0
                if eff_hog_sec > fresh_eff:
                    ratio = eff_hog_sec / fresh_eff if fresh_eff > 0 else 1
                    embed.set_footer(text=f"Pro Tip: Promoting is {ratio:.1f}x more speedup-efficient for points than training fresh!")

        # Global Translator Hook
        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            # Reconstruct embed text to translate
            text_to_translate = (
                f"Action: {action_text} T{self.target_tier} (from {t_current['name']})\n"
                f"Queue Size: {final_cap:,} Troops\n"
                f"Training Speed: +{final_speed:,.1f}%\n"
                f"Total Time Required: {format_time(total_time_seconds)}\n"
                f"Resource Cost: {bread_cost:,} Bread, {wood_cost:,} Wood, {stone_cost:,} Stone, {iron_cost:,} Iron\n"
                f"Yield: {total_pts:,} General/KvK Points, {total_hog:,} HoG Points\n"
            )
            if total_hog > 0:
                text_to_translate += f"Efficiency ROI: {eff_hog_sec:.2f} HoG Points per second of speedup\n"
                if self.current_tier > 0 and eff_hog_sec > fresh_eff:
                    ratio = eff_hog_sec / fresh_eff if fresh_eff > 0 else 1
                    text_to_translate += f"Pro Tip: Promoting is {ratio:.1f}x more speedup-efficient for points than training fresh!"
            
            prompt = f"Translate the following calculator results to {target_lang}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard. Keep ALL numbers/formatting, use minimal AI flourish, and output ONLY the raw translation:\n\n\"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if not response.text:
                    raise ValueError("Empty translation from AI")
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"⚔️ Kingshot Troop Calculator Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.gold()
                )
                if embed.footer.text:
                    t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in calculator: {e}")
                # Fallback to English if it fails
                pass 

        await interaction.followup.send(embed=embed)


class BuildingStatsModal(discord.ui.Modal, title='Enter Building Info'):
    current_level = discord.ui.TextInput(
        label='Current Level (1-30, or TG1-8)',
        placeholder='e.g., 20 or TG4',
        required=True,
        max_length=4
    )
    target_level = discord.ui.TextInput(
        label='Target Level (1-30, or TG1-8)',
        placeholder='e.g., 25 or TG5',
        required=True,
        max_length=4
    )
    speed = discord.ui.TextInput(
        label='Total Construction Speed (%)',
        placeholder='e.g., 345.5',
        required=True,
        max_length=6
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            curr = parse_building_level(self.current_level.value)
            tgt = parse_building_level(self.target_level.value)
            spd = float(self.speed.value.replace('%', '').strip())
            
            if curr is None or tgt is None or spd < 0:
                raise ValueError
                
            self.calculator_view.current_level = curr
            self.calculator_view.target_level = tgt
            self.calculator_view.base_speed = spd
            
            self.calculator_view.children[1].label = f"Set: Lv.{curr}->Lv.{tgt} | {spd}% Spd"
            self.calculator_view.children[1].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid numbers. Use 1-30 or TG1-8 for levels, and flat numbers for speed.", ephemeral=True)

class BuildingTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Town Center", value="Town Center", default=True),
            discord.SelectOption(label="Academy", value="Academy"),
            discord.SelectOption(label="Embassy", value="Embassy"),
            discord.SelectOption(label="Military Camps", value="Camps"),
            discord.SelectOption(label="Command / Infirmary", value="Infirmary/Command"),
        ]
        super().__init__(placeholder="Select Building Type", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.building_type = self.values[0]
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

PREREQ_MAP = {
    11: "Camps", 12: "Infirmary/Command", 13: "Camps", 14: "Camps", 15: "Camps",
    16: "Academy", 17: "Camps", 18: "Camps", 19: "Camps", 20: "Academy",
    21: "Camps", 22: "Camps", 23: "Camps", 24: "Academy", 25: "Camps",
    26: "Camps", 27: "Camps", 28: "Academy", 29: "Camps", 30: "Camps",
    31: "Academy", 32: "Camps", 33: "Camps", 34: "Camps", 35: "Camps",
    36: "Camps", 37: "Camps", 38: "Camps"
}

class BuildingCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.building_type = "Town Center"
        self.current_level = 0
        self.target_level = 0
        self.base_speed = 0.0
        self.has_double_time = False
        self.include_prereqs = False
        
        self.add_item(BuildingTypeSelect())

    @discord.ui.button(label="Input Levels & Speed", style=discord.ButtonStyle.primary, row=1)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuildingStatsModal(self))

    @discord.ui.button(label="Toggle Double Time (20% Red.)", style=discord.ButtonStyle.secondary, row=2)
    async def toggle_double_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.has_double_time = not self.has_double_time
        button.style = discord.ButtonStyle.success if self.has_double_time else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Toggle Incl. Prerequisites", style=discord.ButtonStyle.secondary, row=2)
    async def toggle_prereqs(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.include_prereqs = not self.include_prereqs
        button.style = discord.ButtonStyle.success if self.include_prereqs else discord.ButtonStyle.secondary
        if self.include_prereqs and self.building_type != "Town Center":
            return await interaction.response.send_message("ℹ️ Prerequisites will only be calculated when 'Town Center' is selected.", ephemeral=True)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=3)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_level == 0:
            return await interaction.response.send_message("❌ Please input your levels and speed first! Click 'Input Levels & Speed'.", ephemeral=True)
            
        if self.current_level >= self.target_level:
            return await interaction.response.send_message("❌ Target level must be higher than current level!", ephemeral=True)

        if self.include_prereqs and self.building_type != "Town Center":
            return await interaction.response.send_message("❌ Prerequisites can only be calculated when the Town Center is selected.", ephemeral=True)

        await interaction.response.defer()

        total_base_seconds = 0
        total_wood = 0
        total_stone = 0
        total_iron = 0
        total_bread = 0
        total_gold = 0
        
        main_multiplier = BUILDING_MULTIPLIERS[self.building_type]
        
        # Iteratively sum costs for every level upgrade from current_level + 1 to target_level
        for L in range(self.current_level + 1, self.target_level + 1):
            lvl_data = BUILDING_DATA.get(L)
            if not lvl_data:
                continue
                
            # Add Primary Building
            total_base_seconds += (lvl_data["time"] * main_multiplier)
            total_wood += lvl_data["wood"]
            total_stone += lvl_data["stone"]
            total_iron += lvl_data["iron"]
            total_bread += lvl_data["bread"]
            total_gold += lvl_data["gold"]
            
            # Prerequisite Math
            if self.include_prereqs and self.building_type == "Town Center" and L >= 11:
                prereq_lvl_data = BUILDING_DATA.get(L - 1)
                if prereq_lvl_data:
                    req_type = PREREQ_MAP.get(L, "Camps")
                    embassy_mult = BUILDING_MULTIPLIERS["Embassy"]
                    req_mult = BUILDING_MULTIPLIERS[req_type]
                    
                    total_base_seconds += (prereq_lvl_data["time"] * embassy_mult)
                    total_base_seconds += (prereq_lvl_data["time"] * req_mult)
                    
                    # Add generic resources for prereqs (assuming same resource footprint as TC)
                    total_wood += (prereq_lvl_data["wood"] * 2)
                    total_stone += (prereq_lvl_data["stone"] * 2)
                    total_iron += (prereq_lvl_data["iron"] * 2)
                    total_bread += (prereq_lvl_data["bread"] * 2)
                    total_gold += (prereq_lvl_data["gold"] * 2)
                    
        # Apply Speed Divisor
        divisor = 1.0 + (self.base_speed / 100.0)
        buffed_time = total_base_seconds / divisor
        
        # Apply Double Time
        if self.has_double_time:
            buffed_time *= 0.80
            
        embed = discord.Embed(
            title="🔨 Kingshot Building Calculator Results",
            color=discord.Color.green()
        )
        action_text = f"Upgrading **{self.building_type}** from {format_building_level(self.current_level)} ➔ {format_building_level(self.target_level)}"
        if self.include_prereqs:
            action_text += " *(Incl. Prerequisites)*"
            
        embed.add_field(name="Action", value=action_text, inline=False)
        embed.add_field(name="Construction Speed", value=f"+{self.base_speed:,.1f}%", inline=True)
        embed.add_field(name="Double Time", value="✅ Active (-20%)" if self.has_double_time else "❌ Inactive", inline=True)
        
        embed.add_field(name="Total Time Required", value=f"⏳ **{format_time(buffed_time)}**", inline=False)
        
        res_str = ""
        if total_bread > 0: res_str += f"🍞 {int(total_bread):,} Bread\n"
        if total_wood > 0: res_str += f"🪵 {int(total_wood):,} Wood\n"
        if total_stone > 0: res_str += f"🪨 {int(total_stone):,} Stone\n"
        if total_iron > 0: res_str += f"⛏️ {int(total_iron):,} Iron\n"
        if total_gold > 0: res_str += f"🟡 {int(total_gold):,} True Gold"
        
        if not res_str: res_str = "None"
        embed.add_field(name="Resource Cost", value=res_str, inline=False)

        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = (
                f"Action: {action_text}\n"
                f"Construction Speed: +{self.base_speed:,.1f}%\n"
                f"Double Time: {'Active' if self.has_double_time else 'Inactive'}\n"
                f"Total Time Required: {format_time(buffed_time)}\n"
                f"Resource Cost: \n{res_str}"
            )
            prompt = f"Translate the following building calculator results to {target_lang}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard. Keep ALL numbers/formatting, use minimal AI flourish, and output ONLY the raw translation:\n\n\"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if not response.text:
                    raise ValueError("Empty translation from AI")
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🔨 Kingshot Building Calculator Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.green()
                )
                t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in building calc: {e}")
                pass

        await interaction.followup.send(embed=embed)


CHARM_DATA = {
    1: {"guides": 5, "designs": 5, "secrets": 0},
    2: {"guides": 40, "designs": 15, "secrets": 0},
    3: {"guides": 60, "designs": 40, "secrets": 0},
    4: {"guides": 80, "designs": 100, "secrets": 0},
    5: {"guides": 100, "designs": 200, "secrets": 0},
    6: {"guides": 120, "designs": 300, "secrets": 0},
    7: {"guides": 140, "designs": 400, "secrets": 0},
    8: {"guides": 200, "designs": 400, "secrets": 0},
    9: {"guides": 300, "designs": 400, "secrets": 0},
    10: {"guides": 420, "designs": 420, "secrets": 0},
    11: {"guides": 560, "designs": 420, "secrets": 0},
    12: {"guides": 580, "designs": 450, "secrets": 15},
    13: {"guides": 580, "designs": 450, "secrets": 30},
    14: {"guides": 600, "designs": 500, "secrets": 45},
    15: {"guides": 600, "designs": 500, "secrets": 70},
    16: {"guides": 650, "designs": 550, "secrets": 100},
}

GEAR_DATA = [
    {"name": "Green 0", "alloy": 1500, "polish": 150, "plans": 0, "amber": 0},
    {"name": "Green 1", "alloy": 3800, "polish": 400, "plans": 0, "amber": 0},
    {"name": "Blue 0", "alloy": 7000, "polish": 700, "plans": 0, "amber": 0},
    {"name": "Blue 1", "alloy": 9700, "polish": 950, "plans": 0, "amber": 0},
    {"name": "Blue 2", "alloy": 0, "polish": 0, "plans": 45, "amber": 0},
    {"name": "Blue 3", "alloy": 0, "polish": 0, "plans": 50, "amber": 0},
    {"name": "Purple 0", "alloy": 0, "polish": 0, "plans": 60, "amber": 0},
    {"name": "Purple 1", "alloy": 0, "polish": 0, "plans": 70, "amber": 0},
    {"name": "Purple 2", "alloy": 6500, "polish": 650, "plans": 40, "amber": 0},
    {"name": "Purple 3", "alloy": 8000, "polish": 800, "plans": 50, "amber": 0},
    {"name": "Purple T10", "alloy": 10000, "polish": 950, "plans": 60, "amber": 0},
    {"name": "Purple T11", "alloy": 11000, "polish": 1100, "plans": 70, "amber": 0},
    {"name": "Purple T12", "alloy": 13000, "polish": 1300, "plans": 85, "amber": 0},
    {"name": "Purple T13", "alloy": 15000, "polish": 1600, "plans": 100, "amber": 0},
    {"name": "Gold 0", "alloy": 22000, "polish": 2200, "plans": 40, "amber": 0},
    {"name": "Gold 1", "alloy": 23000, "polish": 2300, "plans": 40, "amber": 0},
    {"name": "Gold 2", "alloy": 25000, "polish": 2500, "plans": 45, "amber": 0},
    {"name": "Gold 3", "alloy": 26000, "polish": 2600, "plans": 45, "amber": 0},
    {"name": "Gold T10", "alloy": 28000, "polish": 2800, "plans": 45, "amber": 0},
    {"name": "Gold T11", "alloy": 30000, "polish": 3000, "plans": 55, "amber": 0},
    {"name": "Gold T12", "alloy": 32000, "polish": 3200, "plans": 55, "amber": 0},
    {"name": "Gold T13", "alloy": 35000, "polish": 3400, "plans": 55, "amber": 0},
    {"name": "Gold T20", "alloy": 38000, "polish": 3600, "plans": 55, "amber": 0},
    {"name": "Gold T21", "alloy": 43000, "polish": 4300, "plans": 75, "amber": 0},
    {"name": "Gold T22", "alloy": 45000, "polish": 4600, "plans": 80, "amber": 0},
    {"name": "Gold T23", "alloy": 48000, "polish": 5000, "plans": 85, "amber": 0},
    {"name": "Red 0", "alloy": 50000, "polish": 530, "plans": 85, "amber": 10},
    {"name": "Red 1", "alloy": 52000, "polish": 560, "plans": 90, "amber": 10},
    {"name": "Red 2", "alloy": 54000, "polish": 590, "plans": 95, "amber": 10},
    {"name": "Red 3", "alloy": 56000, "polish": 620, "plans": 100, "amber": 10},
    {"name": "Red T1 Base", "alloy": 59000, "polish": 670, "plans": 110, "amber": 15},
    {"name": "Red T1 1", "alloy": 61000, "polish": 700, "plans": 115, "amber": 15},
    {"name": "Red T1 2", "alloy": 63000, "polish": 730, "plans": 120, "amber": 15},
    {"name": "Red T1 3", "alloy": 65000, "polish": 760, "plans": 125, "amber": 15},
    {"name": "Red T2 Base", "alloy": 68000, "polish": 810, "plans": 135, "amber": 20},
    {"name": "Red T2 1", "alloy": 70000, "polish": 840, "plans": 140, "amber": 20},
    {"name": "Red T2 2", "alloy": 72000, "polish": 870, "plans": 145, "amber": 20},
    {"name": "Red T2 3", "alloy": 74000, "polish": 900, "plans": 150, "amber": 20},
    {"name": "Red T3 Base", "alloy": 77000, "polish": 950, "plans": 160, "amber": 25},
    {"name": "Red T3 1", "alloy": 80000, "polish": 990, "plans": 165, "amber": 25},
    {"name": "Red T3 2", "alloy": 83000, "polish": 1030, "plans": 170, "amber": 25},
    {"name": "Red T3 3", "alloy": 86000, "polish": 1070, "plans": 180, "amber": 25},
    {"name": "Red T4 Base", "alloy": 120000, "polish": 1500, "plans": 250, "amber": 40},
    {"name": "Red T4 1", "alloy": 140000, "polish": 1650, "plans": 275, "amber": 40},
    {"name": "Red T4 2", "alloy": 160000, "polish": 1800, "plans": 300, "amber": 40},
    {"name": "Red T4 3", "alloy": 180000, "polish": 1950, "plans": 0, "amber": 0},
]

HERO_MASTERY_DATA = {
    1: 10, 2: 20, 3: 30, 4: 40, 5: 50,
    6: 60, 7: 70, 8: 80, 9: 90, 10: 100
}

HERO_LEGENDARY_DATA = {
    1: {"stones": 0, "mithril": 0, "mythic_gear": 2},     # 0 -> Red 1 (Ascension)
    2: {"stones": 110, "mithril": 10, "mythic_gear": 3},  # Red 1 -> Red 20
    3: {"stones": 120, "mithril": 20, "mythic_gear": 5},  # Red 20 -> Red 40
    4: {"stones": 130, "mithril": 30, "mythic_gear": 5},  # Red 40 -> Red 60
    5: {"stones": 140, "mithril": 40, "mythic_gear": 10}, # Red 60 -> Red 80
    6: {"stones": 150, "mithril": 50, "mythic_gear": 10}, # Red 80 -> Red 100
}

HERO_EXCLUSIVE_DATA = {
    1: 5, 2: 10, 3: 15, 4: 20, 5: 25,
    6: 30, 7: 35, 8: 40, 9: 45, 10: 50
}

HERO_SHARD_DATA = {
    0: [1, 1, 1, 1, 1, 5],         # 10 shards total
    1: [5, 5, 5, 5, 5, 15],        # 40 shards total
    2: [15, 15, 15, 15, 15, 40],   # 115 shards total
    3: [40, 40, 40, 40, 40, 100],  # 300 shards total
    4: [100, 100, 100, 100, 100, 100] # 600 shards total
}


def parse_gear_tier(level_str):
    if not level_str: return None
    # Map synonyms like 'Mythic' -> 'Gold', 'Legendary' -> 'Red', 'Epic' -> 'Purple'
    clean = str(level_str).strip().upper().replace("-STAR", "").replace(" ", "")
    clean = clean.replace("MYTHIC", "GOLD").replace("LEGENDARY", "RED").replace("EPIC", "PURPLE").replace("RARE", "BLUE").replace("UNCOMMON", "GREEN")
    for i, g in enumerate(GEAR_DATA):
        g_name = g["name"].upper().replace("-STAR", "").replace(" ", "")
        if clean == g_name:
            return i
    return None

class GearStatsModal(discord.ui.Modal, title='Enter Gear Tiers'):
    current_tier = discord.ui.TextInput(
        label='Current Tier (e.g. Green 0, Gold T11)',
        placeholder='e.g., Purple 3 or Red T1 Base',
        required=True,
        max_length=25
    )
    target_tier = discord.ui.TextInput(
        label='Target Tier (e.g. Red T4 3)',
        placeholder='e.g., Gold T23 or Red T2 1',
        required=True,
        max_length=25
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        curr_idx = parse_gear_tier(self.current_tier.value)
        tgt_idx = parse_gear_tier(self.target_tier.value)
        
        if curr_idx is None or tgt_idx is None:
            return await interaction.response.send_message("❌ Invalid tiers. Please type them exactly like 'Blue 2', 'Gold T20', 'Red T1 Base', or 'Red T4 3'.", ephemeral=True)
            
        self.calculator_view.current_idx = curr_idx
        self.calculator_view.target_idx = tgt_idx
        
        lbl_curr = GEAR_DATA[curr_idx]["name"]
        lbl_tgt = GEAR_DATA[tgt_idx]["name"]
        
        self.calculator_view.children[1].label = f"Set: {lbl_curr} ➔ {lbl_tgt}"
        self.calculator_view.children[1].style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self.calculator_view)

class GearQuantitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Calculate for 1 Piece", value="1", default=True),
            discord.SelectOption(label="Calculate for 3 Pieces (Set Bonus)", value="3"),
            discord.SelectOption(label="Calculate for 6 Pieces (Set Bonus)", value="6"),
        ]
        super().__init__(placeholder="Select Quantity", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.quantity = int(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class GovernorGearCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.quantity = 1
        self.current_idx = -1
        self.target_idx = -1
        
        self.add_item(GearQuantitySelect())

    @discord.ui.button(label="Input Tiers", style=discord.ButtonStyle.primary, row=1)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GearStatsModal(self))

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=2)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_idx == -1 or self.current_idx == -1:
            return await interaction.response.send_message("❌ Please input your tiers first! Click 'Input Tiers'.", ephemeral=True)
            
        if self.current_idx >= self.target_idx:
            return await interaction.response.send_message("❌ Target tier must be higher than current tier!", ephemeral=True)

        await interaction.response.defer()

        total_alloy = 0
        total_polish = 0
        total_plans = 0
        total_amber = 0
        
        for i in range(self.current_idx + 1, self.target_idx + 1):
            tier = GEAR_DATA[i]
            total_alloy += tier["alloy"]
            total_polish += tier["polish"]
            total_plans += tier["plans"]
            total_amber += tier["amber"]
            
        total_alloy *= self.quantity
        total_polish *= self.quantity
        total_plans *= self.quantity
        total_amber *= self.quantity
        
        lbl_curr = GEAR_DATA[self.current_idx]["name"]
        lbl_tgt = GEAR_DATA[self.target_idx]["name"]
        
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator Results",
            color=discord.Color.red()
        )
        action_text = f"Upgrading **{self.quantity}x Gear Piece(s)** from {lbl_curr} ➔ {lbl_tgt}"
        
        embed.add_field(name="Action", value=action_text, inline=False)
        
        res_str = ""
        if total_alloy > 0: res_str += f"🔩 {int(total_alloy):,} Hardened Alloy\n"
        if total_polish > 0: res_str += f"🧪 {int(total_polish):,} Polishing Fluid\n"
        if total_plans > 0: res_str += f"📜 {int(total_plans):,} Design Blueprints\n"
        if total_amber > 0: res_str += f"🟡 {int(total_amber):,} True Gold / Amber"
        
        if not res_str: res_str = "None"
        embed.add_field(name="Total Resource Cost", value=res_str, inline=False)
        
        if self.quantity >= 3:
            bonus_text = "🛡️ **3-Piece Bonus Activated:** Global Defense % Boost for ALL troops!"
            if self.quantity == 6:
                bonus_text += "\n⚔️ **6-Piece Bonus Activated:** Global Attack % Boost for ALL troops!"
            embed.add_field(name="Set Bonuses", value=bonus_text, inline=False)
        else:
            embed.set_footer(text="Pro Tip: Upgrading gear in sets of 3 or 6 triggers massive global army buffs!")

        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = (
                f"Action: {action_text}\n"
                f"Total Resource Cost: \n{res_str}\n"
            )
            if self.quantity >= 3:
                text_to_translate += "Set Bonuses Activated! 3/6 piece Defense and Attack boost unlocked."
            
            prompt = f"Translate the following calculator results to {target_lang}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard. Keep ALL numbers/formatting, use minimal AI flourish, and output ONLY the raw translation:\n\n\"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if not response.text:
                    raise ValueError("Empty translation from AI")
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🛡️ Kingshot Governor Gear Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.red()
                )
                if embed.footer.text:
                    t_embed.set_footer(text="Translated via Global Translator. " + embed.footer.text)
                else:
                    t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in gear calc: {e}")
                pass

        await interaction.followup.send(embed=embed)

class CharmStatsModal(discord.ui.Modal, title='Enter Charm Info'):
    current_level = discord.ui.TextInput(
        label='Current Level (0-15)',
        placeholder='e.g., 0 or 10',
        required=True,
        max_length=2
    )
    target_level = discord.ui.TextInput(
        label='Target Level (1-16)',
        placeholder='e.g., 5 or 16',
        required=True,
        max_length=2
    )
    cur_guides = discord.ui.TextInput(
        label='Owned Guides (Optional)',
        placeholder='e.g., 100',
        required=False,
        max_length=6
    )
    cur_designs = discord.ui.TextInput(
        label='Owned Designs (Optional)',
        placeholder='e.g., 50',
        required=False,
        max_length=6
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            curr = int(self.current_level.value.strip())
            tgt = int(self.target_level.value.strip())
            cg_val = self.cur_guides.value.replace(',', '').strip()
            cd_val = self.cur_designs.value.replace(',', '').strip()
            cg = int(cg_val) if cg_val else 0
            cd = int(cd_val) if cd_val else 0

            if curr < 0 or curr > 15 or tgt < 1 or tgt > 16:
                raise ValueError
                
            self.calculator_view.current_level = curr
            self.calculator_view.target_level = tgt
            self.calculator_view.cur_guides = cg
            self.calculator_view.cur_designs = cd
            
            lbl_text = f"Levels: {curr}➔{tgt} | Inv: {cg}G, {cd}D"
            self.calculator_view.children[1].label = lbl_text
            self.calculator_view.children[1].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid info. Make sure levels are 0-16 and inventory numbers are integers.", ephemeral=True)

class CharmQuantitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="1 Charm", value="1", default=True),
            discord.SelectOption(label="3 Charms [1 Gear Piece]", value="3"),
            discord.SelectOption(label="6 Charms", value="6"),
            discord.SelectOption(label="18 Charms [Max Profile]", value="18"),
        ]
        super().__init__(placeholder="Select Quantity", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.quantity = int(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class GovernorCharmCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.quantity = 1
        self.current_level = -1
        self.target_level = -1
        self.cur_guides = 0
        self.cur_designs = 0
        self.exchange_opened = False
        
        self.add_item(CharmQuantitySelect())

    @discord.ui.button(label="Input Levels & Inventory", style=discord.ButtonStyle.primary, row=1)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CharmStatsModal(self))

    @discord.ui.button(label="Toggle Exchange Shop Opened", style=discord.ButtonStyle.secondary, row=2)
    async def toggle_exchange(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.exchange_opened = not self.exchange_opened
        button.style = discord.ButtonStyle.success if self.exchange_opened else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=3)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_level == -1 or self.target_level == -1:
            return await interaction.response.send_message("❌ Please input your levels first! Click 'Input Levels & Inventory'.", ephemeral=True)
            
        if self.current_level >= self.target_level:
            return await interaction.response.send_message("❌ Target level must be higher than current level!", ephemeral=True)

        await interaction.response.defer()

        total_guides = 0
        total_designs = 0
        total_secrets = 0
        
        for i in range(self.current_level + 1, self.target_level + 1):
            total_guides += CHARM_DATA[i]["guides"]
            total_designs += CHARM_DATA[i]["designs"]
            total_secrets += CHARM_DATA[i]["secrets"]
            
        total_guides *= self.quantity
        total_designs *= self.quantity
        total_secrets *= self.quantity
        
        rem_guides = total_guides - self.cur_guides
        rem_designs = total_designs - self.cur_designs
        
        conversion_text = ""
        # 2:1 conversion math if exchange shop is open
        if self.exchange_opened:
            if rem_guides < 0 and rem_designs > 0:
                excess_guides = abs(rem_guides)
                can_convert_to_designs = excess_guides // 2
                converting_guides = min(can_convert_to_designs, rem_designs) * 2
                rem_designs -= converting_guides // 2
                rem_guides += converting_guides
                if converting_guides > 0:
                    conversion_text += f"\n*Auto-converted {converting_guides:,} excess Guides into {converting_guides // 2:,} Designs!*"
                    
            elif rem_designs < 0 and rem_guides > 0:
                excess_designs = abs(rem_designs)
                can_convert_to_guides = excess_designs // 2
                converting_designs = min(can_convert_to_guides, rem_guides) * 2
                rem_guides -= converting_designs // 2
                rem_designs += converting_designs
                if converting_designs > 0:
                    conversion_text += f"\n*Auto-converted {converting_designs:,} excess Designs into {converting_designs // 2:,} Guides!*"

        rem_guides = max(0, rem_guides)
        rem_designs = max(0, rem_designs)
        total_secrets = max(0, total_secrets)
        
        embed = discord.Embed(
            title="✨ Kingshot Governor Charm Calculator Results",
            color=discord.Color.purple()
        )
        action_text = f"Upgrading **{self.quantity}x Charm(s)** from Lv.{self.current_level} ➔ Lv.{self.target_level}"
        
        embed.add_field(name="Action", value=action_text, inline=False)
        
        raw_res = f"📘 {total_guides:,} Guides\n📜 {total_designs:,} Designs\n🔮 {total_secrets:,} Enigmatic Jewels/Secrets"
        embed.add_field(name="Base Requirements", value=raw_res, inline=False)
        
        shortfall_text = ""
        if self.cur_guides > 0 or self.cur_designs > 0:
            if rem_guides <= 0 and rem_designs <= 0 and total_secrets <= 0:
                shortfall_text = "✅ **None! You have enough materials!**"
            else:
                if rem_guides > 0: shortfall_text += f"📘 {rem_guides:,} Guides Needed\n"
                if rem_designs > 0: shortfall_text += f"📜 {rem_designs:,} Designs Needed\n"
                if total_secrets > 0: shortfall_text += f"🔮 {total_secrets:,} Secrets Needed\n"
                if not shortfall_text: shortfall_text = "✅ **None! You have enough materials!**"
                
            if conversion_text:
                shortfall_text += conversion_text
                
            embed.add_field(name="Remaining Shortfall (Post-Inventory)", value=shortfall_text, inline=False)
            
        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = (
                f"Action: {action_text}\n"
                f"Base Requirements: {total_guides:,} Guides, {total_designs:,} Designs, {total_secrets:,} Secrets\n"
            )
            if self.cur_guides > 0 or self.cur_designs > 0:
                text_to_translate += f"Remaining Shortfall: {shortfall_text.replace('✅ ', '')}\n"
            
            prompt = f"Translate the following calculator results to {target_lang}. Maintain ALL numbers and gaming context exactly: \"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"✨ Kingshot Governor Charm Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.purple()
                )
                t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in charm calc: {e}")
                pass

        await interaction.followup.send(embed=embed)

class HeroStatsModal(discord.ui.Modal, title='Enter Gear Levels'):
    current_level = discord.ui.TextInput(
        label='Current Level (e.g., 0)',
        placeholder='Mastery/Excl: 0-10, Legendary: 0-6',
        required=True,
        max_length=2
    )
    target_level = discord.ui.TextInput(
        label='Target Level (e.g., 5)',
        placeholder='Mastery/Excl: 1-10, Legendary: 1-6',
        required=True,
        max_length=2
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            curr = int(self.current_level.value.strip())
            tgt = int(self.target_level.value.strip())
            
            if curr < 0 or curr > 10 or tgt < 1 or tgt > 10:
                raise ValueError
                
            self.calculator_view.current_level = curr
            self.calculator_view.target_level = tgt
            
            lbl_text = f"Set Levels: {curr} ➔ {tgt}"
            self.calculator_view.children[2].label = lbl_text
            self.calculator_view.children[2].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid levels.", ephemeral=True)

class HeroCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Mastery Forging", value="mastery", default=True),
            discord.SelectOption(label="Legendary Empowerment", value="legendary"),
            discord.SelectOption(label="Exclusive Weapons", value="exclusive")
        ]
        super().__init__(placeholder="Select Category", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.category = self.values[0]
        self.view.current_level = -1
        self.view.target_level = -1
        self.view.children[2].label = "Input Levels"
        self.view.children[2].style = discord.ButtonStyle.primary
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class HeroQuantitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="1 Piece", value="0.25", default=True),
            discord.SelectOption(label="1 Hero Set (4 Gears / 1 Excl.)", value="1"),
            discord.SelectOption(label="2 Hero Sets", value="2"),
            discord.SelectOption(label="3 Hero Sets", value="3"),
            discord.SelectOption(label="4 Hero Sets", value="4"),
            discord.SelectOption(label="5 Hero Sets", value="5"),
        ]
        super().__init__(placeholder="Select Quantity", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.quantity = float(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class HeroGearCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.category = "mastery"
        self.quantity = 0.25
        self.current_level = -1
        self.target_level = -1
        
        self.add_item(HeroCategorySelect())
        self.add_item(HeroQuantitySelect())

    @discord.ui.button(label="Input Levels", style=discord.ButtonStyle.primary, row=2)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(HeroStatsModal(self))

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=3)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_level == -1 or self.target_level == -1:
            return await interaction.response.send_message("❌ Please input your levels first!", ephemeral=True)
            
        if self.current_level >= self.target_level:
            return await interaction.response.send_message("❌ Target level must be higher than current level!", ephemeral=True)

        if self.category == "legendary" and self.target_level > 6:
            return await interaction.response.send_message("❌ Legendary max level is 6 (Red +100).", ephemeral=True)

        await interaction.response.defer()

        total_stones = 0
        total_mithril = 0
        total_mythic = 0
        total_widgets = 0

        for i in range(self.current_level + 1, self.target_level + 1):
            if self.category == "mastery":
                total_stones += HERO_MASTERY_DATA[i]
            elif self.category == "legendary":
                total_stones += HERO_LEGENDARY_DATA[i]["stones"]
                total_mithril += HERO_LEGENDARY_DATA[i]["mithril"]
                total_mythic += HERO_LEGENDARY_DATA[i]["mythic_gear"]
            elif self.category == "exclusive":
                total_widgets += HERO_EXCLUSIVE_DATA[i]

        mult = self.quantity
        if mult == 0.25:
            gear_pieces = 1
            excl_pieces = 1
        else:
            gear_pieces = 4 * int(mult)
            excl_pieces = int(mult)

        if self.category in ["mastery", "legendary"]:
            total_stones = int(total_stones * gear_pieces)
            total_mithril = int(total_mithril * gear_pieces)
            total_mythic = int(total_mythic * gear_pieces)
        else:
            total_widgets = int(total_widgets * excl_pieces)

        embed = discord.Embed(title="🛡️ Kingshot Hero Gear Calculator", color=discord.Color.gold())
        
        cat_name = self.category.replace("_", " ").title()
        action_text = f"{cat_name}: Lv.{self.current_level} ➔ Lv.{self.target_level}\n"
        if mult == 0.25:
            action_text += "For: 1 Gear Piece"
        else:
            action_text += f"For: {int(mult)} Hero Sets"
            
        embed.add_field(name="Action", value=action_text, inline=False)
        
        res_str = ""
        if total_stones > 0: res_str += f"💎 {total_stones:,} Essence Stones\n"
        if total_mithril > 0: res_str += f"💠 {total_mithril:,} Mithril\n"
        if total_mythic > 0: res_str += f"👕 {total_mythic:,} Duplicate Mythic Gear Pieces\n"
        if total_widgets > 0: res_str += f"🧩 {total_widgets:,} Exclusive Widgets\n"
        if not res_str: res_str = "None"
        
        embed.add_field(name="Total Resource Cost", value=res_str, inline=False)
        
        warnings = []
        if self.category == "mastery":
            warnings.append("🚨 **Reforge Penalty:** Reforging a Mastery item permanently destroys 50% of the Essence Stones. Do not reforge unless absolutely necessary.")
            
        if mult >= 4:
            warnings.append("⚠️ **F2P EFFICIENCY WARNING:** You only need 3 sets of Mythic gear (1 Inf, 1 Marksman, 1 Lancer) to maximize your PvP output! Building a 4th or 5th set F2P is a massive waste of Essence Stones and Mithril. Strip secondary heroes naked to pay for the Ascension of your main 3.")
            
        if warnings:
            embed.add_field(name="Warnings & Tips", value="\n\n".join(warnings), inline=False)
            
        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = f"Action: {action_text}\nCost: {res_str}"
            if warnings:
                text_to_translate += "\nWarnings: " + " ".join(warnings)
                
            prompt = f"Translate the following calculator results to {target_lang}. Maintain ALL numbers and gaming context exactly: \"{text_to_translate}\""
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash', contents=prompt
                )
                return response.text.strip()
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🛡️ Kingshot Hero Gear Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.gold()
                )
                t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception:
                pass

        await interaction.followup.send(embed=embed)

class ShardStatsModal(discord.ui.Modal, title='Enter Hero Progress'):
    current_star = discord.ui.TextInput(
        label='Current Star (0-4)',
        placeholder='e.g., 2',
        required=True,
        max_length=1
    )
    current_tier = discord.ui.TextInput(
        label='Current Tier (0-5)',
        placeholder='e.g., 4',
        required=True,
        max_length=1
    )
    target_star = discord.ui.TextInput(
        label='Target Star (1-5)',
        placeholder='e.g., 4',
        required=True,
        max_length=1
    )
    target_tier = discord.ui.TextInput(
        label='Target Tier (0-5)',
        placeholder='0 is Base Star. e.g., 0',
        required=True,
        max_length=1
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cs = int(self.current_star.value.strip())
            ct = int(self.current_tier.value.strip())
            ts = int(self.target_star.value.strip())
            tt = int(self.target_tier.value.strip())
            
            if cs < 0 or cs > 4 or ct < 0 or ct > 5 or ts < 1 or ts > 5 or tt < 0 or tt > 5:
                raise ValueError
                
            self.calculator_view.curr_star = cs
            self.calculator_view.curr_tier = ct
            self.calculator_view.tgt_star = ts
            self.calculator_view.tgt_tier = tt
            
            lbl_text = f"★ {cs}.{ct} ➔ ★ {ts}.{tt}"
            self.calculator_view.children[1].label = lbl_text
            self.calculator_view.children[1].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid levels. Stars must be 0-5, Tiers must be 0-5.", ephemeral=True)

class GemConverterModal(discord.ui.Modal, title='Enter Gems for Lucky Wheel'):
    gems_input = discord.ui.TextInput(
        label='Total Gems to Spend',
        placeholder='e.g., 480000',
        required=True,
        max_length=9
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            gems = int(self.gems_input.value.replace(',', '').strip())
            if gems < 0: raise ValueError
            
            self.calculator_view.gems = gems
            
            lbl_text = f"💎 {gems:,} Gems"
            self.calculator_view.children[1].label = lbl_text
            self.calculator_view.children[1].style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self.calculator_view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid Gem amount. Please enter a positive number.", ephemeral=True)

class ShardCalculatorModeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Calculate Shard Costs", value="shards", default=True, description="Calculate fragments needed to upgrade."),
            discord.SelectOption(label="Lucky Wheel Gem Converter", value="wheel", description="Convert Gems into expected Shard yields.")
        ]
        super().__init__(placeholder="Select Mode", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.mode = self.values[0]
        
        if self.view.mode == "shards":
            self.view.children[1].label = "Input Star/Tier progress"
        else:
            self.view.children[1].label = "Input Total Gems"
            
        self.view.children[1].style = discord.ButtonStyle.primary
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
            
        await interaction.response.edit_message(view=self.view)

class HeroShardCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.mode = "shards"
        
        self.curr_star = -1
        self.curr_tier = -1
        self.tgt_star = -1
        self.tgt_tier = -1
        
        self.gems = -1
        
        self.add_item(ShardCalculatorModeSelect())

    @discord.ui.button(label="Input Star/Tier progress", style=discord.ButtonStyle.primary, row=1)
    async def input_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.mode == "shards":
            await interaction.response.send_modal(ShardStatsModal(self))
        else:
            await interaction.response.send_modal(GemConverterModal(self))

    def _get_cumulative_shards(self, star, tier):
        total = 0
        for s in range(star):
            total += sum(HERO_SHARD_DATA[s])
        
        if star < 5:
            for t in range(tier):
                total += HERO_SHARD_DATA[star][t]
        return total

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=2)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(title="🧩 Kingshot Hero Shard Calculator", color=discord.Color.blue())
        warnings = []
        action_text = ""
        res_str = ""

        if self.mode == "shards":
            if self.curr_star == -1:
                return await interaction.followup.send("❌ Please input your current/target progress first!", ephemeral=True)
                
            curr_cumulative = self._get_cumulative_shards(self.curr_star, self.curr_tier)
            tgt_cumulative = self._get_cumulative_shards(self.tgt_star, self.tgt_tier)
            
            if curr_cumulative >= tgt_cumulative:
                return await interaction.followup.send("❌ Target progress must be higher than current progress!", ephemeral=True)
                
            shards_needed = tgt_cumulative - curr_cumulative
            
            action_text = f"★ {self.curr_star} (Tier {self.curr_tier}) ➔ ★ {self.tgt_star} (Tier {self.tgt_tier})"
            res_str = f"🧩 **{shards_needed:,} Shards needed**."
            
            if self.tgt_star == 5:
                warnings.append("⚠️ **F2P EFFICIENCY WARNING**: The 5th Star costs 600 Shards! Mathematically, the final star costs more than the first 4 stars combined, but only holds roughly 30% of the hero's total stats. Unless this hero is a \"Lucky Wheel\" hero that you are spinning for with Gems, it is highly recommended to stop at 4-Stars and save your General Shards to instantly 4-Star a brand-new hero in the next generation!")

        else:
            if self.gems == -1:
                return await interaction.followup.send("❌ Please input your Gem amount first!", ephemeral=True)
                
            # 120 spins costs roughly 159,000 gems yielding ~180 shards.
            events = self.gems / 159000
            yielded = int(events * 180)
            
            action_text = f"Lucky Wheel Spin for 💎 {self.gems:,} Gems"
            res_str = f"🧩 Expected Yield: **~{yielded:,} Shards**\n"
            
            curr_shards = 0
            final_star = 0
            final_tier = 0
            
            for s in range(5):
                for t in range(6):
                    cost = HERO_SHARD_DATA[s][t]
                    if curr_shards + cost <= yielded:
                        curr_shards += cost
                        final_tier = t + 1
                        if final_tier == 6:
                            final_star = s + 1
                            final_tier = 0
                    else:
                        break
                if curr_shards + HERO_SHARD_DATA[s][t] > yielded:
                    break
                    
            res_str += f"📈 That takes a locked hero straight to **★ {final_star} (Tier {final_tier})**!"

        embed.add_field(name="Action", value=action_text, inline=False)
        embed.add_field(name="Result", value=res_str, inline=False)
        
        if warnings:
            embed.add_field(name="Warnings & Tips", value="\n\n".join(warnings), inline=False)
            
        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = f"Action: {action_text}\nResult: {res_str}"
            if warnings:
                text_to_translate += "\nWarnings: " + " ".join(warnings)
                
            prompt = f"Translate the following calculator results to {target_lang}. Maintain ALL numbers and gaming context exactly: \"{text_to_translate}\""
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash', contents=prompt
                )
                return response.text.strip()
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🧩 Kingshot Hero Shard Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.blue()
                )
                t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception:
                pass

        await interaction.followup.send(embed=embed)


GEAR_DATA = [
    {"name": "Green 0", "alloy": 1500, "polish": 150, "plans": 0, "amber": 0},
    {"name": "Green 1", "alloy": 3800, "polish": 400, "plans": 0, "amber": 0},
    {"name": "Blue 0", "alloy": 7000, "polish": 700, "plans": 0, "amber": 0},
    {"name": "Blue 1", "alloy": 9700, "polish": 950, "plans": 0, "amber": 0},
    {"name": "Blue 2", "alloy": 0, "polish": 0, "plans": 45, "amber": 0},
    {"name": "Blue 3", "alloy": 0, "polish": 0, "plans": 50, "amber": 0},
    {"name": "Purple 0", "alloy": 0, "polish": 0, "plans": 60, "amber": 0},
    {"name": "Purple 1", "alloy": 0, "polish": 0, "plans": 70, "amber": 0},
    {"name": "Purple 2", "alloy": 6500, "polish": 650, "plans": 40, "amber": 0},
    {"name": "Purple 3", "alloy": 8000, "polish": 800, "plans": 50, "amber": 0},
    {"name": "Purple T10", "alloy": 10000, "polish": 950, "plans": 60, "amber": 0},
    {"name": "Purple T11", "alloy": 11000, "polish": 1100, "plans": 70, "amber": 0},
    {"name": "Purple T12", "alloy": 13000, "polish": 1300, "plans": 85, "amber": 0},
    {"name": "Purple T13", "alloy": 15000, "polish": 1600, "plans": 100, "amber": 0},
    {"name": "Gold 0", "alloy": 22000, "polish": 2200, "plans": 40, "amber": 0},
    {"name": "Gold 1", "alloy": 23000, "polish": 2300, "plans": 40, "amber": 0},
    {"name": "Gold 2", "alloy": 25000, "polish": 2500, "plans": 45, "amber": 0},
    {"name": "Gold 3", "alloy": 26000, "polish": 2600, "plans": 45, "amber": 0},
    {"name": "Gold T10", "alloy": 28000, "polish": 2800, "plans": 45, "amber": 0},
    {"name": "Gold T11", "alloy": 30000, "polish": 3000, "plans": 55, "amber": 0},
    {"name": "Gold T12", "alloy": 32000, "polish": 3200, "plans": 55, "amber": 0},
    {"name": "Gold T13", "alloy": 35000, "polish": 3400, "plans": 55, "amber": 0},
    {"name": "Gold T20", "alloy": 38000, "polish": 3600, "plans": 55, "amber": 0},
    {"name": "Gold T21", "alloy": 43000, "polish": 4300, "plans": 75, "amber": 0},
    {"name": "Gold T22", "alloy": 45000, "polish": 4600, "plans": 80, "amber": 0},
    {"name": "Gold T23", "alloy": 48000, "polish": 5000, "plans": 85, "amber": 0},
    {"name": "Red 0", "alloy": 50000, "polish": 530, "plans": 85, "amber": 10},
    {"name": "Red 1", "alloy": 52000, "polish": 560, "plans": 90, "amber": 10},
    {"name": "Red 2", "alloy": 54000, "polish": 590, "plans": 95, "amber": 10},
    {"name": "Red 3", "alloy": 56000, "polish": 620, "plans": 100, "amber": 10},
    {"name": "Red T1 Base", "alloy": 59000, "polish": 670, "plans": 110, "amber": 15},
    {"name": "Red T1 1", "alloy": 61000, "polish": 700, "plans": 115, "amber": 15},
    {"name": "Red T1 2", "alloy": 63000, "polish": 730, "plans": 120, "amber": 15},
    {"name": "Red T1 3", "alloy": 65000, "polish": 760, "plans": 125, "amber": 15},
    {"name": "Red T2 Base", "alloy": 68000, "polish": 810, "plans": 135, "amber": 20},
    {"name": "Red T2 1", "alloy": 70000, "polish": 840, "plans": 140, "amber": 20},
    {"name": "Red T2 2", "alloy": 72000, "polish": 870, "plans": 145, "amber": 20},
    {"name": "Red T2 3", "alloy": 74000, "polish": 900, "plans": 150, "amber": 20},
    {"name": "Red T3 Base", "alloy": 77000, "polish": 950, "plans": 160, "amber": 25},
    {"name": "Red T3 1", "alloy": 80000, "polish": 990, "plans": 165, "amber": 25},
    {"name": "Red T3 2", "alloy": 83000, "polish": 1030, "plans": 170, "amber": 25},
    {"name": "Red T3 3", "alloy": 86000, "polish": 1070, "plans": 180, "amber": 25},
    {"name": "Red T4 Base", "alloy": 120000, "polish": 1500, "plans": 250, "amber": 40},
    {"name": "Red T4 1", "alloy": 140000, "polish": 1650, "plans": 275, "amber": 40},
    {"name": "Red T4 2", "alloy": 160000, "polish": 1800, "plans": 300, "amber": 40},
    {"name": "Red T4 3", "alloy": 180000, "polish": 1950, "plans": 0, "amber": 0},
]


def parse_gear_tier(level_str):
    if not level_str: return None
    # Map synonyms like 'Mythic' -> 'Gold', 'Legendary' -> 'Red', 'Epic' -> 'Purple'
    clean = str(level_str).strip().upper().replace("-STAR", "").replace(" ", "")
    clean = clean.replace("MYTHIC", "GOLD").replace("LEGENDARY", "RED").replace("EPIC", "PURPLE").replace("RARE", "BLUE").replace("UNCOMMON", "GREEN")
    for i, g in enumerate(GEAR_DATA):
        g_name = g["name"].upper().replace("-STAR", "").replace(" ", "")
        if clean == g_name:
            return i
    return None

class GearStatsModal(discord.ui.Modal, title='Enter Gear Tiers'):
    current_tier = discord.ui.TextInput(
        label='Current Tier (e.g. Green 0, Gold T11)',
        placeholder='e.g., Purple 3 or Red T1 Base',
        required=True,
        max_length=25
    )
    target_tier = discord.ui.TextInput(
        label='Target Tier (e.g. Red T4 3)',
        placeholder='e.g., Gold T23 or Red T2 1',
        required=True,
        max_length=25
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        curr_idx = parse_gear_tier(self.current_tier.value)
        tgt_idx = parse_gear_tier(self.target_tier.value)
        
        if curr_idx is None or tgt_idx is None:
            return await interaction.response.send_message("❌ Invalid tiers. Please type them exactly like 'Blue 2', 'Gold T20', 'Red T1 Base', or 'Red T4 3'.", ephemeral=True)
            
        self.calculator_view.current_idx = curr_idx
        self.calculator_view.target_idx = tgt_idx
        
        lbl_curr = GEAR_DATA[curr_idx]["name"]
        lbl_tgt = GEAR_DATA[tgt_idx]["name"]
        
        self.calculator_view.children[1].label = f"Set: {lbl_curr} ➔ {lbl_tgt}"
        self.calculator_view.children[1].style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self.calculator_view)

class GearQuantitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Calculate for 1 Piece", value="1", default=True),
            discord.SelectOption(label="Calculate for 3 Pieces (Set Bonus)", value="3"),
            discord.SelectOption(label="Calculate for 6 Pieces (Set Bonus)", value="6"),
        ]
        super().__init__(placeholder="Select Quantity", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.quantity = int(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class GovernorGearCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.quantity = 1
        self.current_idx = -1
        self.target_idx = -1
        
        self.add_item(GearQuantitySelect())

    @discord.ui.button(label="Input Tiers", style=discord.ButtonStyle.primary, row=1)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GearStatsModal(self))

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=2)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_idx == -1 or self.current_idx == -1:
            return await interaction.response.send_message("❌ Please input your tiers first! Click 'Input Tiers'.", ephemeral=True)
            
        if self.current_idx >= self.target_idx:
            return await interaction.response.send_message("❌ Target tier must be higher than current tier!", ephemeral=True)

        await interaction.response.defer()

        total_alloy = 0
        total_polish = 0
        total_plans = 0
        total_amber = 0
        
        for i in range(self.current_idx + 1, self.target_idx + 1):
            tier = GEAR_DATA[i]
            total_alloy += tier["alloy"]
            total_polish += tier["polish"]
            total_plans += tier["plans"]
            total_amber += tier["amber"]
            
        total_alloy *= self.quantity
        total_polish *= self.quantity
        total_plans *= self.quantity
        total_amber *= self.quantity
        
        lbl_curr = GEAR_DATA[self.current_idx]["name"]
        lbl_tgt = GEAR_DATA[self.target_idx]["name"]
        
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator Results",
            color=discord.Color.red()
        )
        action_text = f"Upgrading **{self.quantity}x Gear Piece(s)** from {lbl_curr} ➔ {lbl_tgt}"
        
        embed.add_field(name="Action", value=action_text, inline=False)
        
        res_str = ""
        if total_alloy > 0: res_str += f"🔩 {int(total_alloy):,} Hardened Alloy\n"
        if total_polish > 0: res_str += f"🧪 {int(total_polish):,} Polishing Fluid\n"
        if total_plans > 0: res_str += f"📜 {int(total_plans):,} Design Blueprints\n"
        if total_amber > 0: res_str += f"🟡 {int(total_amber):,} True Gold / Amber"
        
        if not res_str: res_str = "None"
        embed.add_field(name="Total Resource Cost", value=res_str, inline=False)
        
        if self.quantity >= 3:
            bonus_text = "🛡️ **3-Piece Bonus Activated:** Global Defense % Boost for ALL troops!"
            if self.quantity == 6:
                bonus_text += "\n⚔️ **6-Piece Bonus Activated:** Global Attack % Boost for ALL troops!"
            embed.add_field(name="Set Bonuses", value=bonus_text, inline=False)
        else:
            embed.set_footer(text="Pro Tip: Upgrading gear in sets of 3 or 6 triggers massive global army buffs!")

        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = await self.bot.db.hget('global_translator_subs', user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = (
                f"Action: {action_text}\n"
                f"Total Resource Cost: \n{res_str}\n"
            )
            if self.quantity >= 3:
                text_to_translate += "Set Bonuses Activated! 3/6 piece Defense and Attack boost unlocked."
            
            prompt = f"Translate the following calculator results to {target_lang}. Maintain ALL numbers and gaming context exactly: \"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🛡️ Kingshot Governor Gear Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.red()
                )
                if embed.footer.text:
                    t_embed.set_footer(text="Translated via Global Translator. " + embed.footer.text)
                else:
                    t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in gear calc: {e}")
                pass

        await interaction.followup.send(embed=embed)


GEAR_DATA = [
    {"name": "Green 0", "alloy": 1500, "polish": 150, "plans": 0, "amber": 0},
    {"name": "Green 1", "alloy": 3800, "polish": 400, "plans": 0, "amber": 0},
    {"name": "Blue 0", "alloy": 7000, "polish": 700, "plans": 0, "amber": 0},
    {"name": "Blue 1", "alloy": 9700, "polish": 950, "plans": 0, "amber": 0},
    {"name": "Blue 2", "alloy": 0, "polish": 0, "plans": 45, "amber": 0},
    {"name": "Blue 3", "alloy": 0, "polish": 0, "plans": 50, "amber": 0},
    {"name": "Purple 0", "alloy": 0, "polish": 0, "plans": 60, "amber": 0},
    {"name": "Purple 1", "alloy": 0, "polish": 0, "plans": 70, "amber": 0},
    {"name": "Purple 2", "alloy": 6500, "polish": 650, "plans": 40, "amber": 0},
    {"name": "Purple 3", "alloy": 8000, "polish": 800, "plans": 50, "amber": 0},
    {"name": "Purple T10", "alloy": 10000, "polish": 950, "plans": 60, "amber": 0},
    {"name": "Purple T11", "alloy": 11000, "polish": 1100, "plans": 70, "amber": 0},
    {"name": "Purple T12", "alloy": 13000, "polish": 1300, "plans": 85, "amber": 0},
    {"name": "Purple T13", "alloy": 15000, "polish": 1600, "plans": 100, "amber": 0},
    {"name": "Gold 0", "alloy": 22000, "polish": 2200, "plans": 40, "amber": 0},
    {"name": "Gold 1", "alloy": 23000, "polish": 2300, "plans": 40, "amber": 0},
    {"name": "Gold 2", "alloy": 25000, "polish": 2500, "plans": 45, "amber": 0},
    {"name": "Gold 3", "alloy": 26000, "polish": 2600, "plans": 45, "amber": 0},
    {"name": "Gold T10", "alloy": 28000, "polish": 2800, "plans": 45, "amber": 0},
    {"name": "Gold T11", "alloy": 30000, "polish": 3000, "plans": 55, "amber": 0},
    {"name": "Gold T12", "alloy": 32000, "polish": 3200, "plans": 55, "amber": 0},
    {"name": "Gold T13", "alloy": 35000, "polish": 3400, "plans": 55, "amber": 0},
    {"name": "Gold T20", "alloy": 38000, "polish": 3600, "plans": 55, "amber": 0},
    {"name": "Gold T21", "alloy": 43000, "polish": 4300, "plans": 75, "amber": 0},
    {"name": "Gold T22", "alloy": 45000, "polish": 4600, "plans": 80, "amber": 0},
    {"name": "Gold T23", "alloy": 48000, "polish": 5000, "plans": 85, "amber": 0},
    {"name": "Red 0", "alloy": 50000, "polish": 530, "plans": 85, "amber": 10},
    {"name": "Red 1", "alloy": 52000, "polish": 560, "plans": 90, "amber": 10},
    {"name": "Red 2", "alloy": 54000, "polish": 590, "plans": 95, "amber": 10},
    {"name": "Red 3", "alloy": 56000, "polish": 620, "plans": 100, "amber": 10},
    {"name": "Red T1 Base", "alloy": 59000, "polish": 670, "plans": 110, "amber": 15},
    {"name": "Red T1 1", "alloy": 61000, "polish": 700, "plans": 115, "amber": 15},
    {"name": "Red T1 2", "alloy": 63000, "polish": 730, "plans": 120, "amber": 15},
    {"name": "Red T1 3", "alloy": 65000, "polish": 760, "plans": 125, "amber": 15},
    {"name": "Red T2 Base", "alloy": 68000, "polish": 810, "plans": 135, "amber": 20},
    {"name": "Red T2 1", "alloy": 70000, "polish": 840, "plans": 140, "amber": 20},
    {"name": "Red T2 2", "alloy": 72000, "polish": 870, "plans": 145, "amber": 20},
    {"name": "Red T2 3", "alloy": 74000, "polish": 900, "plans": 150, "amber": 20},
    {"name": "Red T3 Base", "alloy": 77000, "polish": 950, "plans": 160, "amber": 25},
    {"name": "Red T3 1", "alloy": 80000, "polish": 990, "plans": 165, "amber": 25},
    {"name": "Red T3 2", "alloy": 83000, "polish": 1030, "plans": 170, "amber": 25},
    {"name": "Red T3 3", "alloy": 86000, "polish": 1070, "plans": 180, "amber": 25},
    {"name": "Red T4 Base", "alloy": 120000, "polish": 1500, "plans": 250, "amber": 40},
    {"name": "Red T4 1", "alloy": 140000, "polish": 1650, "plans": 275, "amber": 40},
    {"name": "Red T4 2", "alloy": 160000, "polish": 1800, "plans": 300, "amber": 40},
    {"name": "Red T4 3", "alloy": 180000, "polish": 1950, "plans": 0, "amber": 0},
]


def parse_gear_tier(level_str):
    if not level_str: return None
    # Map synonyms like 'Mythic' -> 'Gold', 'Legendary' -> 'Red', 'Epic' -> 'Purple'
    clean = str(level_str).strip().upper().replace("-STAR", "").replace(" ", "")
    clean = clean.replace("MYTHIC", "GOLD").replace("LEGENDARY", "RED").replace("EPIC", "PURPLE").replace("RARE", "BLUE").replace("UNCOMMON", "GREEN")
    for i, g in enumerate(GEAR_DATA):
        g_name = g["name"].upper().replace("-STAR", "").replace(" ", "")
        if clean == g_name:
            return i
    return None

class GearStatsModal(discord.ui.Modal, title='Enter Gear Tiers'):
    current_tier = discord.ui.TextInput(
        label='Current Tier (e.g. Green 0, Gold T11)',
        placeholder='e.g., Purple 3 or Red T1 Base',
        required=True,
        max_length=25
    )
    target_tier = discord.ui.TextInput(
        label='Target Tier (e.g. Red T4 3)',
        placeholder='e.g., Gold T23 or Red T2 1',
        required=True,
        max_length=25
    )

    def __init__(self, view):
        super().__init__()
        self.calculator_view = view

    async def on_submit(self, interaction: discord.Interaction):
        curr_idx = parse_gear_tier(self.current_tier.value)
        tgt_idx = parse_gear_tier(self.target_tier.value)
        
        if curr_idx is None or tgt_idx is None:
            return await interaction.response.send_message("❌ Invalid tiers. Please type them exactly like 'Blue 2', 'Gold T20', 'Red T1 Base', or 'Red T4 3'.", ephemeral=True)
            
        self.calculator_view.current_idx = curr_idx
        self.calculator_view.target_idx = tgt_idx
        
        lbl_curr = GEAR_DATA[curr_idx]["name"]
        lbl_tgt = GEAR_DATA[tgt_idx]["name"]
        
        self.calculator_view.children[1].label = f"Set: {lbl_curr} ➔ {lbl_tgt}"
        self.calculator_view.children[1].style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self.calculator_view)

class GearQuantitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Calculate for 1 Piece", value="1", default=True),
            discord.SelectOption(label="Calculate for 3 Pieces (Set Bonus)", value="3"),
            discord.SelectOption(label="Calculate for 6 Pieces (Set Bonus)", value="6"),
        ]
        super().__init__(placeholder="Select Quantity", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.quantity = int(self.values[0])
        for opt in self.options:
            opt.default = (opt.value == self.values[0])
        await interaction.response.edit_message(view=self.view)

class GovernorGearCalculatorView(discord.ui.View):
    def __init__(self, bot=None, gemini_client=None):
        super().__init__(timeout=600)
        self.bot = bot
        self.gemini_client = gemini_client
        self.quantity = 1
        self.current_idx = -1
        self.target_idx = -1
        
        self.add_item(GearQuantitySelect())

    @discord.ui.button(label="Input Tiers", style=discord.ButtonStyle.primary, row=1)
    async def input_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GearStatsModal(self))

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.danger, row=2)
    async def calculate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_idx == -1 or self.current_idx == -1:
            return await interaction.response.send_message("❌ Please input your tiers first! Click 'Input Tiers'.", ephemeral=True)
            
        if self.current_idx >= self.target_idx:
            return await interaction.response.send_message("❌ Target tier must be higher than current tier!", ephemeral=True)

        await interaction.response.defer()

        total_alloy = 0
        total_polish = 0
        total_plans = 0
        total_amber = 0
        
        for i in range(self.current_idx + 1, self.target_idx + 1):
            tier = GEAR_DATA[i]
            total_alloy += tier["alloy"]
            total_polish += tier["polish"]
            total_plans += tier["plans"]
            total_amber += tier["amber"]
            
        total_alloy *= self.quantity
        total_polish *= self.quantity
        total_plans *= self.quantity
        total_amber *= self.quantity
        
        lbl_curr = GEAR_DATA[self.current_idx]["name"]
        lbl_tgt = GEAR_DATA[self.target_idx]["name"]
        
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator Results",
            color=discord.Color.red()
        )
        action_text = f"Upgrading **{self.quantity}x Gear Piece(s)** from {lbl_curr} ➔ {lbl_tgt}"
        
        embed.add_field(name="Action", value=action_text, inline=False)
        
        res_str = ""
        if total_alloy > 0: res_str += f"🔩 {int(total_alloy):,} Hardened Alloy\n"
        if total_polish > 0: res_str += f"🧪 {int(total_polish):,} Polishing Fluid\n"
        if total_plans > 0: res_str += f"📜 {int(total_plans):,} Design Blueprints\n"
        if total_amber > 0: res_str += f"🟡 {int(total_amber):,} True Gold / Amber"
        
        if not res_str: res_str = "None"
        embed.add_field(name="Total Resource Cost", value=res_str, inline=False)
        
        if self.quantity >= 3:
            bonus_text = "🛡️ **3-Piece Bonus Activated:** Global Defense % Boost for ALL troops!"
            if self.quantity == 6:
                bonus_text += "\n⚔️ **6-Piece Bonus Activated:** Global Attack % Boost for ALL troops!"
            embed.add_field(name="Set Bonuses", value=bonus_text, inline=False)
        else:
            embed.set_footer(text="Pro Tip: Upgrading gear in sets of 3 or 6 triggers massive global army buffs!")

        user_id = str(interaction.user.id)
        target_lang = None
        try:
            target_lang = self.bot.db.hget("global_translator_subs", user_id)
        except Exception:
            pass

        if target_lang:
            text_to_translate = (
                f"Action: {action_text}\n"
                f"Total Resource Cost: \n{res_str}\n"
            )
            if self.quantity >= 3:
                text_to_translate += "Set Bonuses Activated! 3/6 piece Defense and Attack boost unlocked."
            
            prompt = f"Translate the following calculator results to {target_lang}. Maintain ALL numbers and gaming context exactly: \"{text_to_translate}\""
            
            def fetch_translation():
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                return response.text.strip()
                
            try:
                translation = await self.bot.loop.run_in_executor(None, fetch_translation)
                t_embed = discord.Embed(
                    title=f"🛡️ Kingshot Governor Gear Results ({target_lang.capitalize()})",
                    description=translation,
                    color=discord.Color.red()
                )
                if embed.footer.text:
                    t_embed.set_footer(text="Translated via Global Translator. " + embed.footer.text)
                else:
                    t_embed.set_footer(text="Translated via Global Translator")
                await interaction.followup.send(embed=t_embed)
                return
            except Exception as e:
                print(f"Translation failed in gear calc: {e}")
                pass

        await interaction.followup.send(embed=embed)

class Calculators(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Synchronous client for quick on-demand translation tasks
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    @commands.command(aliases=["troop_calculator", "tc", "troops"])
    async def troopcalculator(self, ctx):
        """Interactive Troop Training and Promotion Calculator for Kingshot."""
        view = TroopCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="⚔️ Kingshot Troop Calculator",
            description=(
                "Use this tool to calculate exact training times, point yields, and speedup efficiency.\n\n"
                "**1.** Select your starting tier (or Fresh).\n"
                "**2.** Select your target tier.\n"
                "**3.** Click **Input Base Stats** to enter your base capacity and speed %.\n"
                "**4.** Toggle any temporary buffs you plan to use.\n"
                "**5.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.blue()
        )
        # For a standard command, we send the message using ctx instead of interaction.response
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["building_calculator", "bc", "buildings"])
    async def buildingcalculator(self, ctx):
        """Interactive Building Calculator for Kingshot."""
        view = BuildingCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🔨 Kingshot Building Calculator",
            description=(
                "Use this tool to calculate building times and resource costs.\n\n"
                "**1.** Select your building type.\n"
                "**2.** Click **Input Levels & Speed** to enter your current/target levels (e.g., 20 or TG4).\n"
                "**3.** Toggle **Double Time** or **Prerequisites** if needed.\n"
                "**4.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=view)


    @commands.command(aliases=["governor_calculator", "gc", "gear"])
    async def governorcalc(self, ctx):
        """Interactive Governor Gear Calculator for Kingshot."""
        view = GovernorGearCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator",
            description=(
                "Use this tool to precisely calculate the massive resource costs of pushing end-game Governor Gear.\n\n"
                "**1.** Select if you want to calculate for 1 piece or a Set (3 / 6 pieces).\n"
                "**2.** Click **Input Tiers** to type your current and target tiers (e.g., Green 0, Blue 3, Gold T20, Red T4 Base).\n"
                "**3.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=view)


    @commands.command(aliases=["governor_calculator", "gc", "gear"])
    async def governorcalc(self, ctx):
        """Interactive Governor Gear Calculator for Kingshot."""
        view = GovernorGearCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator",
            description=(
                "Use this tool to precisely calculate the massive resource costs of pushing end-game Governor Gear.\n\n"
                "**1.** Select if you want to calculate for 1 piece or a Set (3 / 6 pieces).\n"
                "**2.** Click **Input Tiers** to type your current and target tiers (e.g., Green 0, Blue 3, Gold T20, Red T4 Base).\n"
                "**3.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=view)


    @commands.command(aliases=["governor_calculator", "gc", "gear"])
    async def governorcalc(self, ctx):
        """Interactive Governor Gear Calculator for Kingshot."""
        view = GovernorGearCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🛡️ Kingshot Governor Gear Calculator",
            description=(
                "Use this tool to precisely calculate the massive resource costs of pushing end-game Governor Gear.\n\n"
                "**1.** Select if you want to calculate for 1 piece or a Set (3 / 6 pieces).\n"
                "**2.** Click **Input Tiers** to type your current and target tiers (e.g., Green 0, Blue 3, Gold T20, Red T4 Base).\n"
                "**3.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=view)

    @commands.group(invoke_without_command=True, aliases=["calc", "calculators"])
    async def calculator(self, ctx):
        """Interactive Calculators!"""
        embed = discord.Embed(
            title="🧮 Kingshot Calculators 🧮",
            description="Use the interactive commands below to access our custom calculators!",
            color=discord.Color.blue()
        )
        embed.add_field(name="⚔️ `!troopcalculator`", value="Calculate exactly how long training or promoting troops will take, and prove the T9->T10 point efficiency meta!", inline=False)
        embed.add_field(name="🔨 `!buildingcalculator`", value="Calculate structure build times, specific resource costs, and automatically sum prerequisite queues!", inline=False)
        embed.add_field(name="🛡️ `!governorcalc`", value="Calculate exact Material costs for Governor Gear from Green all the way to Red T4!", inline=False)
        embed.add_field(name="🛡️ `!governorcalc`", value="Calculate exact Material costs for Governor Gear from Green all the way to Red T4!", inline=False)
        embed.add_field(name="🛡️ `!governorcalc`", value="Calculate exact Material costs for Governor Gear from Green all the way to Red T4!", inline=False)
        embed.add_field(name="✨ `!charmcalc`", value="Calculate Charm Guides, Designs, and auto-convert Exchange Shop deficits!", inline=False)
        embed.add_field(name="⭐ `!herocalc`", value="Calculate Hero Gear Mastery, Legendary Ascension, and Exclusive Widgets!", inline=False)
        embed.add_field(name="🧩 `!shardcalc`", value="Calculate Hero Shard Micro-Phases and Lucky Wheel Gem Conversion Costs!", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["shard_calculator", "sc", "shards"])
    async def shardcalc(self, ctx):
        """Interactive Hero Shard Calculator for Kingshot."""
        view = HeroShardCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🧩 Kingshot Hero Shard Calculator",
            description=(
                "Precisely calculate the shard costs for Micro-Phases and analyze Lucky Wheel expectations.\n\n"
                "**1.** Select the Mode (Shard Calculator or Gem Converter).\n"
                "**2.** Input your Star/Tier targets or Gem totals.\n"
                "**3.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["hero_calculator", "hc", "herogear"])
    async def herocalc(self, ctx):
        """Interactive Hero Gear Calculator for Kingshot."""
        view = HeroGearCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="🛡️ Kingshot Hero Gear Calculator",
            description=(
                "Precisely calculate Hero Gear Mastery, Legendary Ascension, and Exclusive Weapon Widgets.\n\n"
                "**1.** Select the Upgrade Category.\n"
                "**2.** Select the Quantity (Number of Hero Sets).\n"
                "**3.** Click **Input Levels** to provide targets.\n"
                "**4.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["charm_calculator", "cc", "charms"])
    async def charmcalc(self, ctx):
        """Interactive Governor Charm Calculator for Kingshot."""
        view = GovernorCharmCalculatorView(self.bot, self.gemini_client)
        embed = discord.Embed(
            title="✨ Kingshot Governor Charm Calculator",
            description=(
                "Use this tool to precisely calculate the costs of upgrading Governor Charms.\n\n"
                "**1.** Select if you want to calculate for 1, 3, 6, or 18 charms.\n"
                "**2.** Click **Input Levels & Inventory** to provide your targets.\n"
                "**3.** Toggle **Exchange Shop** if you have unlocked the 2:1 conversion (Lv.11).\n"
                "**4.** Click **Calculate**! 🚀"
            ),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    cog = Calculators(bot)
    await bot.add_cog(cog)
