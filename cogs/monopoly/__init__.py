from .monopoly import Monopoly

async def setup(bot):
    await bot.add_cog(Monopoly(bot))
