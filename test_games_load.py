import asyncio
from unittest.mock import MagicMock
from cogs.games import setup
import traceback

async def test():
    bot = MagicMock()
    bot.db = MagicMock()
    try:
        await setup(bot)
        print("Setup successful")
    except Exception as e:
        print("Setup failed!")
        traceback.print_exc()

asyncio.run(test())
