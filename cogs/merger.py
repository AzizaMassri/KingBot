import discord
from discord.ext import commands
import io
import re
from cogs.utils.tiers import requires_tier, Tier

POWER_REGEX = re.compile(r'^(.*?)[,\s]+([\d,\.]+[mMkKbB]?)$')

class MergerModal(discord.ui.Modal, title="Alliance Merger Data"):
    alliance1_name = discord.ui.TextInput(
        label="Alliance 1 Name",
        placeholder="e.g. [RUN] Runners",
        max_length=50,
        required=True
    )
    alliance1_data = discord.ui.TextInput(
        label="Alliance 1 Members (Name,Power)",
        style=discord.TextStyle.paragraph,
        placeholder="Player1,5.5M\nPlayer2,4.2M\n(Max 100 players)",
        required=True
    )
    alliance2_name = discord.ui.TextInput(
        label="Alliance 2 Name",
        placeholder="e.g. [COD] Coders",
        max_length=50,
        required=True
    )
    alliance2_data = discord.ui.TextInput(
        label="Alliance 2 Members (Name,Power)",
        style=discord.TextStyle.paragraph,
        placeholder="Player1,5.5M\nPlayer2,4.2M\n(Max 100 players)",
        required=True
    )
    include_academy = discord.ui.TextInput(
        label="Include Academy File? (Y/N)",
        placeholder="Y",
        default="Y",
        max_length=5,
        required=False
    )

    def parse_power(self, power_str):
        power_str = str(power_str).replace(',', '').strip()
        if power_str.upper().endswith('M'):
            return float(power_str[:-1]) * 1000000
        elif power_str.upper().endswith('K'):
            return float(power_str[:-1]) * 1000
        elif power_str.upper().endswith('B'):
            return float(power_str[:-1]) * 1000000000
        return float(power_str)

    def parse_data(self, data_str, alliance_name=None):
        # Using splitlines() handles \r\n, \n, and \r generically
        lines = data_str.splitlines()
        # Only take up to 100 lines per alliance
        lines = lines[:100]
        
        parsed_data = []
        for line in lines:
            line_stripped = line.strip()
            # Skip empty lines or header if pasted
            if not line_stripped or line_stripped.lower().startswith('name,power'):
                continue
            
            match = POWER_REGEX.search(line_stripped)
            if match:
                name = match.group(1).strip()
                power = match.group(2).strip()
                if name.startswith('"') and name.endswith('"'):
                    name = name[1:-1]
                if alliance_name:
                    name = f"[{alliance_name}] {name}"
                parsed_data.append({'Name': name, 'Power': power})
            else:
                # Fallback purely comma separation
                parts = line_stripped.rsplit(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    power = parts[1].strip()
                    # Remove quotes if they exist around the name
                    if name.startswith('"') and name.endswith('"'):
                        name = name[1:-1]
                    if alliance_name:
                        name = f"[{alliance_name}] {name}"
                    parsed_data.append({'Name': name, 'Power': power})
        
        return parsed_data

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        generate_academy = True
        if self.include_academy.value and self.include_academy.value.strip().upper() in ['N', 'NO', 'F', 'FALSE', '0']:
            generate_academy = False

        # Parse the input data
        data1 = self.parse_data(self.alliance1_data.value, self.alliance1_name.value)
        data2 = self.parse_data(self.alliance2_data.value, self.alliance2_name.value)

        # Check if we have valid data
        if not data1 and not data2:
            await interaction.followup.send("❌ Error: No valid data could be parsed from your inputs.", ephemeral=True)
            return

        # Combine the data
        combined_data = data1 + data2

        # Apply the conversion and sort
        try:
            for row in combined_data:
                row['RawPower'] = self.parse_power(row['Power'])
        except Exception as e:
            await interaction.followup.send(f"❌ Error parsing power values: {e}. Please ensure format is Name,Power (e.g. User,5.5M)", ephemeral=True)
            return
            
        combined_data.sort(key=lambda x: x['RawPower'], reverse=True)

        # Split the roster at the 100-member limit (or max capacity)
        MAX_CAPACITY = 100
        main_alliance = combined_data[:MAX_CAPACITY]
        academy = combined_data[MAX_CAPACITY:]

        embed = discord.Embed(
            title=f"🤝 {self.alliance1_name.value} & {self.alliance2_name.value} Merger 🤝",
            color=discord.Color.gold(),
            description=(
                f"**TOTAL COMBINED MEMBERS:** {len(combined_data)}\n"
                f"**MAIN ALLIANCE CAPACITY:** {MAX_CAPACITY}\n"
                f"**MEMBERS ROUTED TO ACADEMY:** {len(academy)}\n"
            )
        )

        # Create output strings for clean text file attachments
        main_output = "=" * 50 + "\n"
        main_output += f"🏆 {self.alliance1_name.value} & {self.alliance2_name.value} - MAIN ALLIANCE 🏆\n"
        main_output += "=" * 50 + "\n\n"
        main_output += f"TOTAL COMBINED MEMBERS: {len(combined_data)}\n"
        main_output += f"MAIN ALLIANCE CAPACITY: {MAX_CAPACITY}\n\n"
        main_output += f"--- MAIN ALLIANCE ROSTER (TOP {MAX_CAPACITY}) ---\n"
        for i, row in enumerate(main_alliance):
            main_output += f"{i+1}. {row['Name']} - {row['Power']}\n"

        main_file_io = io.BytesIO(main_output.encode("utf-8"))
        main_file = discord.File(main_file_io, filename="Main_Alliance_Roster.txt")
        files_to_send = [main_file]

        if academy and generate_academy:
            academy_output = "=" * 50 + "\n"
            academy_output += f"🛡️ {self.alliance1_name.value} & {self.alliance2_name.value} - ACADEMY ALLIANCE 🛡️\n"
            academy_output += "=" * 50 + "\n\n"
            academy_output += f"MEMBERS ROUTED TO ACADEMY: {len(academy)}\n\n"
            academy_output += "--- ACADEMY ALLIANCE ROSTER ---\n"
            for i, row in enumerate(academy):
                academy_output += f"{i+1}. {row['Name']} - {row['Power']}\n"
            
            academy_file_io = io.BytesIO(academy_output.encode("utf-8"))
            academy_file = discord.File(academy_file_io, filename="Academy_Alliance_Roster.txt")
            files_to_send.append(academy_file)

        # To give it extra shine, let's put the top 10 as an embed field preview!
        top_10 = ""
        for i, row in enumerate(main_alliance[:10]):
            top_10 += f"**{i+1}.** {row['Name']} (`{row['Power']}`)\n"
        
        if top_10:
            embed.add_field(name="🏆 Main Alliance Top 10", value=top_10, inline=False)
            
        # Top 10 Academy
        if academy and generate_academy:
            top_10_academy = ""
            for i, row in enumerate(academy[:10]):
                top_10_academy += f"**{i+1}.** {row['Name']} (`{row['Power']}`)\n"
            if top_10_academy:
                embed.add_field(name="🛡️ Academy Top 10 Preview", value=top_10_academy, inline=False)
            
        embed.set_footer(text="Download the attached .txt files for the full sorted rosters!")
        
        await interaction.followup.send(embed=embed, files=files_to_send)

class MergerLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Launch Interactive Menu", style=discord.ButtonStyle.primary, emoji="🚀", custom_id="btn_merger_launch")
    async def launch_tool(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MergerModal())

class AllianceMerger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    async def cog_load(self):
        self.bot.add_view(MergerLaunchView())

    def parse_power(self, power_str):
        power_str = str(power_str).replace(',', '').strip()
        if power_str.upper().endswith('M'):
            return float(power_str[:-1]) * 1000000
        elif power_str.upper().endswith('K'):
            return float(power_str[:-1]) * 1000
        elif power_str.upper().endswith('B'):
            return float(power_str[:-1]) * 1000000000
        return float(power_str)

    def parse_data(self, data_str, alliance_name=None):
        # Using splitlines() handles \r\n, \n, and \r generically
        lines = data_str.splitlines()
        
        parsed_data = []
        for line in lines:
            line_stripped = line.strip()
            # Skip empty lines or header if pasted
            if not line_stripped or line_stripped.lower().startswith('name,power'):
                continue
            
            match = POWER_REGEX.search(line_stripped)
            if match:
                name = match.group(1).strip()
                power = match.group(2).strip()
                if name.startswith('"') and name.endswith('"'):
                    name = name[1:-1]
                if alliance_name:
                    name = f"[{alliance_name}] {name}"
                parsed_data.append({'Name': name, 'Power': power})
            else:
                # Fallback purely comma separation
                parts = line_stripped.rsplit(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    power = parts[1].strip()
                    # Remove quotes if they exist around the name
                    if name.startswith('"') and name.endswith('"'):
                        name = name[1:-1]
                    if alliance_name:
                        name = f"[{alliance_name}] {name}"
                    parsed_data.append({'Name': name, 'Power': power})
        
        return parsed_data

    @commands.command(name="merger", description="Calculates an alliance merger roster.", aliases=["projectmeteor"])
    @requires_tier(Tier.ELITE)
    async def merger(self, ctx, *, input_text: str = None):
        """Calculates an alliance merger roster and provides formatted setup files."""
        alliance1_name = "Alliance 1"
        alliance2_name = "Alliance 2"
        raw_data = ""
        generate_academy = True
        
        if input_text:
            if '--mainonly' in input_text.lower() or '--main-only' in input_text.lower():
                generate_academy = False
                input_text = re.sub(r'(?i)--main-?only', '', input_text).strip()

            parts = input_text.split('|', 2)
            if len(parts) == 3:
                alliance1_name = parts[0].strip()
                alliance2_name = parts[1].strip()
                raw_data = parts[2].strip()
            elif len(parts) == 2:
                 alliance1_name = parts[0].strip()
                 raw_data = parts[1].strip()
            else:
                 raw_data = parts[0].strip()
                 
        parsed_lists = []
        if raw_data:
            parsed_lists.append(self.parse_data(raw_data, "Mixed/Unknown"))
            
        # Check for attachments (.txt or .csv files)
        if ctx.message.attachments:
            for i, attachment in enumerate(ctx.message.attachments):
                if attachment.filename.endswith(('.txt', '.csv')):
                    try:
                        file_content = await attachment.read()
                        f_data = file_content.decode('utf-8')
                        
                        # Assign alliance name to files if we have exactly 2 files
                        a_name = None
                        if len(ctx.message.attachments) == 2:
                            if i == 0: a_name = alliance1_name
                            elif i == 1: a_name = alliance2_name
                            
                        parsed_lists.append(self.parse_data(f_data, a_name))
                    except:
                        await ctx.send(f"⚠️ Could not read attachment {attachment.filename}.")
        
        if not parsed_lists:
            embed = discord.Embed(
                title="🤝 Alliance Merger Tool",
                description=(
                    "You can provide data by either pasting it directly in the command, or attaching `.txt`/`.csv` files!\n\n"
                    "**Format:**\n"
                    "`!merger [Alliance1 Name] | [Alliance2 Name] | [Data]`\n\n"
                    "**Example 1 (Direct Paste):**\n"
                    "```\n!merger [RUN] Runners | [COD] Coders |\n"
                    "Player1,5.5M\nPlayer2,4.2M\nPlayer3,1.1M\n```\n"
                    "**Example 2 (Files):**\n"
                    "`!merger [RUN] Runners | [COD] Coders` *(and attach your 2 text files!)*\n\n"
                    "*(Tip: Add `--main-only` anywhere in the command to only generate the Main Alliance file)*\n\n"
                    "**Alternatively, click the button below to use the interactive menu!**"
                ),
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, view=MergerLaunchView())

        # Combine parsed lists
        combined_data = []
        for lst in parsed_lists:
            combined_data.extend(lst)

        # Check if we have valid data
        if not combined_data:
            return await ctx.send("❌ Error: No valid `Name,Power` data could be parsed from your input or files.")

        # Apply the conversion and sort
        try:
            for row in combined_data:
                row['RawPower'] = self.parse_power(row['Power'])
        except Exception as e:
            return await ctx.send(f"❌ Error parsing power values: {e}. Please ensure format is Name,Power (e.g. User,5.5M)")
            
        combined_data.sort(key=lambda x: x['RawPower'], reverse=True)

        # Split the roster at the 100-member limit (or max capacity)
        MAX_CAPACITY = 100
        main_alliance = combined_data[:MAX_CAPACITY]
        academy = combined_data[MAX_CAPACITY:]

        embed = discord.Embed(
            title=f"🤝 {alliance1_name} & {alliance2_name} Merger 🤝",
            color=discord.Color.gold(),
            description=(
                f"**TOTAL COMBINED MEMBERS:** {len(combined_data)}\n"
                f"**MAIN ALLIANCE CAPACITY:** {MAX_CAPACITY}\n"
                f"**MEMBERS ROUTED TO ACADEMY:** {len(academy)}\n"
            )
        )

        # Create output strings for clean text file attachments
        main_output = "=" * 50 + "\n"
        main_output += f"🏆 {alliance1_name} & {alliance2_name} - MAIN ALLIANCE 🏆\n"
        main_output += "=" * 50 + "\n\n"
        main_output += f"TOTAL COMBINED MEMBERS: {len(combined_data)}\n"
        main_output += f"MAIN ALLIANCE CAPACITY: {MAX_CAPACITY}\n\n"
        main_output += f"--- MAIN ALLIANCE ROSTER (TOP {MAX_CAPACITY}) ---\n"
        for i, row in enumerate(main_alliance):
            main_output += f"{i+1}. {row['Name']} - {row['Power']}\n"

        main_file_io = io.BytesIO(main_output.encode("utf-8"))
        main_file = discord.File(main_file_io, filename="Main_Alliance_Roster.txt")
        files_to_send = [main_file]

        if academy and generate_academy:
            academy_output = "=" * 50 + "\n"
            academy_output += f"🛡️ {alliance1_name} & {alliance2_name} - ACADEMY ALLIANCE 🛡️\n"
            academy_output += "=" * 50 + "\n\n"
            academy_output += f"MEMBERS ROUTED TO ACADEMY: {len(academy)}\n\n"
            academy_output += "--- ACADEMY ALLIANCE ROSTER ---\n"
            for i, row in enumerate(academy):
                academy_output += f"{i+1}. {row['Name']} - {row['Power']}\n"
            
            academy_file_io = io.BytesIO(academy_output.encode("utf-8"))
            academy_file = discord.File(academy_file_io, filename="Academy_Alliance_Roster.txt")
            files_to_send.append(academy_file)

        # To give it extra shine, let's put the top 10 as an embed field preview!
        top_10 = ""
        for i, row in enumerate(main_alliance[:10]):
            top_10 += f"**{i+1}.** {row['Name']} (`{row['Power']}`)\n"
        
        if top_10:
            embed.add_field(name="🏆 Main Alliance Top 10", value=top_10, inline=False)
            
        # Top 10 Academy
        if academy and generate_academy:
            top_10_academy = ""
            for i, row in enumerate(academy[:10]):
                top_10_academy += f"**{i+1}.** {row['Name']} (`{row['Power']}`)\n"
            if top_10_academy:
                embed.add_field(name="🛡️ Academy Top 10 Preview", value=top_10_academy, inline=False)
            
        embed.set_footer(text="Download the attached .txt files for the full sorted rosters!")
        
        await ctx.send(embed=embed, files=files_to_send)

async def setup(bot):
    await bot.add_cog(AllianceMerger(bot))
