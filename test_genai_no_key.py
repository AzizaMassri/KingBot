import os
from google import genai

client = genai.Client(api_key=None)

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Say hello"
    )
    print("Success")
except Exception as e:
    print(f"ERROR: {e}")
