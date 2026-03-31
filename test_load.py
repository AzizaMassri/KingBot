import asyncio
import traceback
from unittest.mock import AsyncMock
from cogs.games import setup

async def t():
    b = AsyncMock()
    b.db = AsyncMock()
    try:
        await setup(b)
        print('Valid')
    except Exception:
        traceback.print_exc()

asyncio.run(t())
