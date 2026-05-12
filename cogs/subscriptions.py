import discord
from discord.ext import commands
import os
import time


class Subscriptions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="set_tier")
    async def set_tier(
        self, ctx, guild_id: str = None, tier: int = None, password: str = None
    ):
        """Authorizes a given guild for a specific Subscription Tier."""
        if not guild_id or not tier or not password:
            return await ctx.send("❌ Usage: `!set_tier <guild_id> <tier> <password>`")

        env_password = os.getenv("ADMIN_TIER_PASSWORD")
        if not env_password:
            return await ctx.send(
                "❌ FATAL: `ADMIN_TIER_PASSWORD` environment variable is not configured. Setup suspended."
            )

        if password != env_password:
            # We don't want to alert them that it's a password issue natively to prevent brute-forcing, but since it's admin command..
            return await ctx.send("❌ Access Denied: Invalid Authorization Password.")

        if tier not in [1, 2, 3]:
            return await ctx.send(
                "❌ Invalid Tier. Must be 1 (Free), 2 (Premium), or 3 (Elite)."
            )

        try:
            # Set the tier
            await self.bot.db.set(f"guild_tier:{guild_id}", str(tier))

            # Reset their timestamp to give them 30 days from literally right now
            current_time = int(time.time())
            await self.bot.db.set(
                f"trans_chars_reset:{guild_id}", str(current_time + 2592000)
            )
            await self.bot.db.set(f"trans_chars:{guild_id}", "0")

            embed = discord.Embed(
                title="✅ Enterprise Subscription Updated",
                description=f"Guild ID `{guild_id}` has been authorized for **Tier {tier}**.\nTheir translation quotas and 30-day token cycle have been fully artificially reset starting now.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Database update failed: {e}")

    @commands.hybrid_command(name="check_quota")
    async def check_quota(self, ctx, guild_id: int = None):
        """Check the translation limits and usage for a guild."""
        if not guild_id:
            # Default to current guild
            if not ctx.guild:
                return await ctx.send("❌ Please specify a guild ID.")
            guild_id = ctx.guild.id

        try:
            from cogs.utils.tiers import get_guild_tier, TRANSLATION_LIMITS

            tier = await get_guild_tier(self.bot, guild_id)
            limit = TRANSLATION_LIMITS.get(tier, 5000)

            usage = await self.bot.db.get(f"trans_chars:{guild_id}")
            usage = int(usage) if usage else 0

            reset_ts = await self.bot.db.get(f"trans_chars_reset:{guild_id}")
            reset_str = f"<t:{reset_ts}:R>" if reset_ts else "Never Used"

            embed = discord.Embed(
                title=f"📊 Quota Status for {guild_id}", color=discord.Color.blue()
            )
            embed.add_field(name="Current Tier", value=f"Tier {tier}", inline=False)
            if limit == float("inf"):
                embed.add_field(
                    name="Allocated Usage",
                    value="**UNLIMITED** characters allowed.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Allocated Usage",
                    value=f"Used `{usage}` / `{limit}` characters.",
                    inline=False,
                )

            embed.add_field(
                name="Reset Cycle", value=f"Cycle completes: {reset_str}", inline=False
            )

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Internal Retrieval Exception: {e}")


async def setup(bot):
    await bot.add_cog(Subscriptions(bot))
