import discord
from discord.ext import commands


class TranslationKeywords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_key = "translator_exclusion_keywords"

    @commands.hybrid_group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def keyword(self, ctx):
        """Manage global keywords that should NOT be translated by the AI."""
        await ctx.send(
            "❌ Usage: `!keyword add <word>`, `!keyword remove <word>`, or `!keyword list`"
        )

    @keyword.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_keyword(self, ctx, *, word: str):
        """Adds a keyword to the global translation exclusion list."""
        try:
            await self.bot.db.sadd(self.db_key, word)
            await ctx.send(
                f"✅ Added `{word}` to the translation exclusion list. The bot will no longer translate this word."
            )
        except Exception as e:
            await ctx.send(f"❌ Error saving keyword: {e}")

    @keyword.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_keyword(self, ctx, *, word: str):
        """Removes a keyword from the global translation exclusion list."""
        try:
            removed = await self.bot.db.srem(self.db_key, word)
            if removed:
                await ctx.send(
                    f"✅ Removed `{word}` from the translation exclusion list."
                )
            else:
                await ctx.send(f"⚠️ `{word}` was not found in the exclusion list.")
        except Exception as e:
            await ctx.send(f"❌ Error removing keyword: {e}")

    @keyword.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_keywords(self, ctx):
        """Lists all currently configured translation exclusion keywords."""
        try:
            keywords = await self.bot.db.smembers(self.db_key)
            if keywords:
                sorted_keywords = sorted(list(keywords))
                formatted_list = "\n".join([f"• `{w}`" for w in sorted_keywords])
                embed = discord.Embed(
                    title="🛡️ Translation Exclusion Keywords",
                    description="The AI is strictly instructed NOT to translate or alter these words:\n"
                    + formatted_list,
                    color=discord.Color.blue(),
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("ℹ️ The translation exclusion list is currently empty.")
        except Exception as e:
            await ctx.send(f"❌ Error fetching keywords: {e}")


async def setup(bot):
    await bot.add_cog(TranslationKeywords(bot))
