import asyncio
import os
from dotenv import load_dotenv
from cogs.utils.postgres_cache import PostgresCache

load_dotenv()

async def test():
    db = PostgresCache()
    await db.init_db()
    
    rows = await db.pool.fetch('SELECT * FROM zset_kv LIMIT 20')
    print("ALL ROWS IN ZSET_KV:")
    for row in rows:
        print(dict(row))
        
    res = await db.zrevrange(row['zset_name'], 0, -1, withscores=True)
    print("ZREVRANGE result:")
    print(res)
    
    await db.close()

asyncio.run(test())
