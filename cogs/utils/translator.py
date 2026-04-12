import discord
import hashlib
import os
import asyncio
from google import genai



# Local helper to reconstruct cache keys properly
def get_cache_key(text: str, language: str) -> str:
    normalized_string = f"{text.strip().lower()}_{language.lower()}"
    return hashlib.md5(normalized_string.encode()).hexdigest()

async def translate_content(text: str, target_locale: discord.Locale, bot=None, guild_id=None) -> str:
    """
    Translates the given text to the target locale. 
    Skips Translation if locale is English. 
    """
    if not text:
        return text

    # Handle standard English locals efficiently
    if target_locale in [discord.Locale.american_english, discord.Locale.british_english]:
        return text

    if bot is None or not hasattr(bot, 'db'):
        return text

    cache = bot.db
    target_language = target_locale.value
    cache_key = get_cache_key(text, target_language)
    cached_translation = await cache.get(cache_key)

    if cached_translation:
        return cached_translation

    # Fetch exclusion keywords from Postgres
    exclusion_list = await cache.smembers("translator_exclusion_keywords")
    exclusion_str = ""
    if exclusion_list:
        words = ", ".join([f"'{w}'" for w in exclusion_list])
        exclusion_str = f" CRITICAL INSTRUCTION: Do NOT translate or alter these specific keywords under any circumstances: {words}."

    prompt = f"Translate the following to {target_language}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard. Keep exact formatting/emojis, and output ONLY the raw translation with no preamble.{exclusion_str}\n\n\"{text}\""

    # Quota check
    if guild_id:
        from cogs.utils.tiers import increment_translation_usage
        allowed = await increment_translation_usage(bot, guild_id, len(text))
        if not allowed:
            # Drop the translation if they hit their quota
            return text

    try:
        def translate_text():
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            return response.text
        
        translation = await asyncio.to_thread(translate_text)
        translation = translation.strip() if translation else text
        
        # Save to redis, expire in 86400 (1 day)
        await cache.setex(cache_key, 86400, translation)
        return translation
    except Exception as e:
        print(f"Translation Error: {e}")
        return text # If Gemini fails, fallback to rendering original text.
