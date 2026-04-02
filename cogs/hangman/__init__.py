from .hangman import KingsExecution

async def setup(bot):
    await bot.add_cog(KingsExecution(bot))
