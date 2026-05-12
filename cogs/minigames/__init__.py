from .minigames import KingsMinigames

__red_end_user_data_statement__ = "Nothing to delete."


async def setup(bot):
    await bot.add_cog(KingsMinigames(bot))
