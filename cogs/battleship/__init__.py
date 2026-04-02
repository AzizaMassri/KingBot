from .battleship import KingsArmada

async def setup(bot):
    await bot.add_cog(KingsArmada(bot))
