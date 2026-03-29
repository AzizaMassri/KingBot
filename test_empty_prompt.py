import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

prompt = f"Translate the following text to Spanish. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"\""

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    print("RESPONSE:", response.text)
except Exception as e:
    print("ERROR:", e)
