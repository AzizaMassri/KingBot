import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

async def get_commands():
    async with aiohttp.ClientSession() as session:
        # First get the application ID
        headers = {"Authorization": f"Bot {TOKEN}"}
        async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as resp:
            data = await resp.json()
            app_id = data.get("id")
            
        print(f"App ID: {app_id}")
        
        # Now get global commands
        url = f"https://discord.com/api/v10/applications/{app_id}/commands"
        async with session.get(url, headers=headers) as resp:
            cmds = await resp.json()
            
            print(f"Found {len(cmds)} global commands")
            for c in cmds:
                print(f"- {c.get('name')} (Type: {c.get('type')})")
if __name__ == "__main__":
    asyncio.run(get_commands())
