import asyncio
import os
from dotenv import load_dotenv
from cogs.utils.postgres_cache import PostgresCache

load_dotenv()

async def test():
    db = PostgresCache()
    await db.init_db()
    
    # Insert a dummy value
    await db.pool.execute("INSERT INTO zset_kv (zset_name, member, score) VALUES ('test_zset', '123', 100) ON CONFLICT DO NOTHING")
    
    # Test LIMIT NULL
    rows1 = await db.pool.fetch('''
        SELECT member, score FROM zset_kv 
        WHERE zset_name = $1 
        ORDER BY score DESC 
        LIMIT $2 OFFSET $3
    ''', 'test_zset', None, 0)
    print("LIMIT NULL returned:", rows1)
    
    # Test LIMIT 999999
    rows2 = await db.pool.fetch('''
        SELECT member, score FROM zset_kv 
        WHERE zset_name = $1 
        ORDER BY score DESC 
        LIMIT $2 OFFSET $3
    ''', 'test_zset', 999999, 0)
    print("LIMIT 999999 returned:", rows2)

    await db.pool.close()

asyncio.run(test())
