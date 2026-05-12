import discord
from discord.ext import commands
from discord import app_commands
import math

# Rates derived from spreadsheet sample (120 spins)
GEMS_PER_SPIN = 1350

# Rewards per spin (estimated averages)
REWARDS_PER_SPIN = {
    "hero_shards": 180 / 120,  # 1.5
    "suppression_skill_books": 124 / 120,  # ~1.033
    "expedition_skill_books": 124 / 120,  # ~1.033
    "general_speedups_1hr": 25 / 120,  # ~0.208
    "xp_10k": 26 / 120,  # ~0.217
    "iron_10k_x20": 3 / 120,  # ~0.025
    "stone_10k_x80": 3 / 120,  # ~0.025
    "wood_10k_x400": 3 / 120,  # ~0.025
    "bread_10k_x400": 3 / 120,  # ~0.025
    "training_speedups_1hr": 6 / 120,  # 0.05
    "construction_speedups_1hr": 6 / 120,  # 0.05
    "research_speedups_1hr": 6 / 120,  # 0.05
}

SHARDS_PER_SPIN = REWARDS_PER_SPIN["hero_shards"]


def calc_rewards_from_spins(spins: int) -> dict:
    gem_cost = spins * GEMS_PER_SPIN
    rewards = {k: math.floor(v * spins) for k, v in REWARDS_PER_SPIN.items()}
    return gem_cost, rewards


def calc_spins_from_shards(shards: int) -> tuple[int, int]:
    spins = math.ceil(shards / SHARDS_PER_SPIN)
    gem_cost = spins * GEMS_PER_SPIN
    return spins, gem_cost


def build_rewards_embed(spins: int, gems: int, rewards: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🎰 Spin Rewards Calculator",
        description=f"Estimated rewards for **{spins:,} spins** (~{gems:,} 💎 gems)",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="⚔️ Combat",
        value=(
            f"🧩 Hero Shards: **{rewards['hero_shards']:,}**\n"
            f"📖 Suppression Skill Books: **{rewards['suppression_skill_books']:,}**\n"
            f"📖 Expedition Skill Books: **{rewards['expedition_skill_books']:,}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="⏱️ Speed Ups",
        value=(
            f"⚡ General (1hr): **{rewards['general_speedups_1hr']:,}**\n"
            f"🏋️ Training (1hr): **{rewards['training_speedups_1hr']:,}**\n"
            f"🏗️ Construction (1hr): **{rewards['construction_speedups_1hr']:,}**\n"
            f"🔬 Research (1hr): **{rewards['research_speedups_1hr']:,}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="📦 Resources & XP",
        value=(
            f"✨ 10k XP: **{rewards['xp_10k']:,}**\n"
            f"⚙️ 10k Iron ×20: **{rewards['iron_10k_x20']:,}**\n"
            f"🪨 10k Stone ×80: **{rewards['stone_10k_x80']:,}**\n"
            f"🪵 10k Wood ×400: **{rewards['wood_10k_x400']:,}**\n"
            f"🍞 10k Bread ×400: **{rewards['bread_10k_x400']:,}**"
        ),
        inline=False,
    )
    embed.set_footer(
        text="Estimates based on probability — actual results may vary. Data from sgt_slayer3"
    )
    return embed


class SpinCalculatorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Calculate by Spins",
        style=discord.ButtonStyle.primary,
        emoji="🎰",
        custom_id="spincalc:by_spins",
    )
    async def by_spins(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(SpinInputModal())

    @discord.ui.button(
        label="Calculate by Shards",
        style=discord.ButtonStyle.secondary,
        emoji="🧩",
        custom_id="spincalc:by_shards",
    )
    async def by_shards(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(ShardsInputModal())


class SpinInputModal(discord.ui.Modal, title="Calculate by Spins"):
    spins = discord.ui.TextInput(
        label="Number of Spins", placeholder="e.g. 120", required=True, max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.spins.value.strip().replace(",", "")
        if not raw.isdigit() or int(raw) <= 0:
            return await interaction.response.send_message(
                "❌ Please enter a valid positive number of spins.", ephemeral=True
            )
        spins = int(raw)
        if spins > 100_000:
            return await interaction.response.send_message(
                "❌ Value too large (max 100,000 spins).", ephemeral=True
            )
        gem_cost, rewards = calc_rewards_from_spins(spins)
        embed = build_rewards_embed(spins, gem_cost, rewards)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ShardsInputModal(discord.ui.Modal, title="Calculate by Hero Shards"):
    shards = discord.ui.TextInput(
        label="How many Hero Shards do you need?",
        placeholder="e.g. 180",
        required=True,
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.shards.value.strip().replace(",", "")
        if not raw.isdigit() or int(raw) <= 0:
            return await interaction.response.send_message(
                "❌ Please enter a valid positive number of shards.", ephemeral=True
            )
        shards = int(raw)
        if shards > 1_000_000:
            return await interaction.response.send_message(
                "❌ Value too large (max 1,000,000 shards).", ephemeral=True
            )
        spins, gem_cost = calc_spins_from_shards(shards)
        embed = discord.Embed(
            title="🧩 Shards → Spins Calculator",
            description=(
                f"To get **{shards:,} Hero Shards** you need approximately:\n\n"
                f"🎰 **{spins:,} spins**\n"
                f"💎 **{gem_cost:,} gems**"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text="Estimates based on probability — actual results may vary. Data from sgt_slayer3"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SpinCalculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="spincalc",
        description="Calculate KingShot spin rewards or gems/shards needed.",
    )
    @app_commands.describe(
        spins="Number of spins to calculate rewards for",
        shards="Number of Hero Shards you need (calculates spins & gems required)",
    )
    async def spincalc(self, ctx, spins: int = None, shards: int = None):
        """Calculate KingShot spin rewards or how many spins/gems you need for shards."""
        if spins is not None and shards is not None:
            return await ctx.send(
                "❌ Please provide either `spins` or `shards`, not both.",
                ephemeral=True,
            )

        if spins is not None:
            if spins <= 0 or spins > 100_000:
                return await ctx.send(
                    "❌ Spins must be between 1 and 100,000.", ephemeral=True
                )
            gem_cost, rewards = calc_rewards_from_spins(spins)
            embed = build_rewards_embed(spins, gem_cost, rewards)
            return await ctx.send(embed=embed)

        if shards is not None:
            if shards <= 0 or shards > 1_000_000:
                return await ctx.send(
                    "❌ Shards must be between 1 and 1,000,000.", ephemeral=True
                )
            needed_spins, gem_cost = calc_spins_from_shards(shards)
            embed = discord.Embed(
                title="🧩 Shards → Spins Calculator",
                description=(
                    f"To get **{shards:,} Hero Shards** you need approximately:\n\n"
                    f"🎰 **{needed_spins:,} spins**\n"
                    f"💎 **{gem_cost:,} gems**"
                ),
                color=discord.Color.blue(),
            )
            embed.set_footer(
                text="Estimates based on probability — actual results may vary. Data from sgt_slayer3"
            )
            return await ctx.send(embed=embed)

        # No args — show interactive panel
        embed = discord.Embed(
            title="🎰 KingShot Spin Calculator",
            description=(
                "Use the buttons below to calculate spin rewards or how many spins/gems you need.\n\n"
                f"💎 **Cost per spin:** {GEMS_PER_SPIN:,} gems\n"
                f"🧩 **Hero Shards per spin:** ~{SHARDS_PER_SPIN:.2f}"
            ),
            color=discord.Color.gold(),
        )
        embed.set_footer(
            text="Estimates based on probability — actual results may vary. Data from sgt_slayer3"
        )
        await ctx.send(embed=embed, view=SpinCalculatorView())


async def setup(bot):
    await bot.add_cog(SpinCalculator(bot))
