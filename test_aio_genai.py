import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def main():
    prompt = "Translate 'hello world' to Spanish"
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print("ASYNC TRANSLATION:", response.text)
    except Exception as e:
        print("ASYNC ERROR:", e)

asyncio.run(main())
