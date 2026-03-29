import aiosqlite
import json
import asyncio

class SQLiteCache:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path
        self._db = None
        
    async def init_db(self):
        self._db = await aiosqlite.connect(self.db_path)
        
        # Strings
        await self._db.execute('''
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Hashes (Dicts)
        await self._db.execute('''
            CREATE TABLE IF NOT EXISTS hash_kv (
                hash TEXT,
                key TEXT,
                value TEXT,
                PRIMARY KEY (hash, key)
            )
        ''')
        
        # Sets
        await self._db.execute('''
            CREATE TABLE IF NOT EXISTS set_kv (
                set_name TEXT,
                value TEXT,
                PRIMARY KEY (set_name, value)
            )
        ''')
        
        # Sorted Sets
        await self._db.execute('''
            CREATE TABLE IF NOT EXISTS zset_kv (
                zset_name TEXT,
                member TEXT,
                score REAL,
                PRIMARY KEY (zset_name, member)
            )
        ''')
        
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            
    # --- STRINGS ---
    async def get(self, key):
        async with self._db.execute("SELECT value FROM kv WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set(self, key, value):
        await self._db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, str(value)))
        await self._db.commit()

    async def delete(self, key):
        await self._db.execute("DELETE FROM kv WHERE key = ?", (key,))
        await self._db.execute("DELETE FROM hash_kv WHERE hash = ?", (key,))
        await self._db.execute("DELETE FROM set_kv WHERE set_name = ?", (key,))
        await self._db.execute("DELETE FROM zset_kv WHERE zset_name = ?", (key,))
        await self._db.commit()
        
    async def incr(self, key, amount=1):
        # Fetch current
        current = await self.get(key)
        if current is None:
            new_val = amount
        else:
            try:
                new_val = int(current) + amount
            except ValueError:
                new_val = amount
        await self.set(key, new_val)
        return new_val

    # --- HASHES ---
    async def hset(self, name, key, value):
        await self._db.execute("INSERT OR REPLACE INTO hash_kv (hash, key, value) VALUES (?, ?, ?)", (name, str(key), str(value)))
        await self._db.commit()

    async def hget(self, name, key):
        async with self._db.execute("SELECT value FROM hash_kv WHERE hash = ? AND key = ?", (name, str(key))) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def hdel(self, name, key):
        async with self._db.execute("DELETE FROM hash_kv WHERE hash = ? AND key = ?", (name, str(key))) as cursor:
            await self._db.commit()
            return cursor.rowcount > 0

    async def hgetall(self, name):
        async with self._db.execute("SELECT key, value FROM hash_kv WHERE hash = ?", (name,)) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    # --- SETS ---
    async def sadd(self, name, *values):
        count = 0
        for value in values:
            try:
                await self._db.execute("INSERT INTO set_kv (set_name, value) VALUES (?, ?)", (name, str(value)))
                count += 1
            except aiosqlite.IntegrityError:
                pass # Already exists
        await self._db.commit()
        return count

    async def srem(self, name, *values):
        count = 0
        for value in values:
            async with self._db.execute("DELETE FROM set_kv WHERE set_name = ? AND value = ?", (name, str(value))) as cursor:
                if cursor.rowcount > 0:
                    count += 1
        await self._db.commit()
        return count

    async def smembers(self, name):
        async with self._db.execute("SELECT value FROM set_kv WHERE set_name = ?", (name,)) as cursor:
            rows = await cursor.fetchall()
            return set(row[0] for row in rows)

    # --- SORTED SETS ---
    async def zincrby(self, name, amount, member):
        member_str = str(member)
        async with self._db.execute("SELECT score FROM zset_kv WHERE zset_name = ? AND member = ?", (name, member_str)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            new_score = float(row[0]) + amount
            await self._db.execute("UPDATE zset_kv SET score = ? WHERE zset_name = ? AND member = ?", (new_score, name, member_str))
        else:
            new_score = amount
            await self._db.execute("INSERT INTO zset_kv (zset_name, member, score) VALUES (?, ?, ?)", (name, member_str, new_score))
            
        await self._db.commit()
        return new_score

    async def zrevrange(self, name, start, end, withscores=False):
        # end is inclusive in Database
        limit = end - start + 1
        offset = start
        
        async with self._db.execute(
            "SELECT member, score FROM zset_kv WHERE zset_name = ? ORDER BY score DESC LIMIT ? OFFSET ?", 
            (name, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            
        if withscores:
            return [(row[0], row[1]) for row in rows]
        else:
            return [row[0] for row in rows]
