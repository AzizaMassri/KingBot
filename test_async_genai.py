import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

text = "Hello world"
target = "Spanish"
exclusion_str = ""

prompt = f"Translate the following text to {target}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"{text}\"{exclusion_str}"

def fetch():
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    if not response.text:
        raise ValueError("Empty response from AI")
    return response.text.strip()

async def main():
    loop = asyncio.get_event_loop()
    try:
        translation = await loop.run_in_executor(None, fetch)
        print("TRANSLATION:", translation)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(main())
