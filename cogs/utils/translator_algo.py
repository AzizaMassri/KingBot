import re
import asyncio
import time

# Constants for Margin Calculation
# Target monthly quota before reaching peak degradation. 
IDEAL_VOLUME_CAP = 40000000 
B_MIN = 15
B_MAX = 250

def get_complexity_score(content: str) -> int:
    """
    Evaluates how complex a string is to translate.
    Returns an integer score. Higher == more complex.
    """
    if not content:
        return 0
        
    score = len(content)
    
    # Check for sentence structuring punctuation
    punct_count = len(re.findall(r'[.?;!]', content))
    score += (punct_count * 5)
    
    # Penalize very short strings indicating conversational fluff
    if len(content) < 25:
        score -= 10
        
    # Check for capitalization variance (all caps is usually simple/shouting)
    if content.isupper():
         score -= 15
         
    return max(0, score)

def get_translation_boundary(server_total_usage: int) -> float:
    """
    Returns the dynamic boundary score `B`. 
    If complexity `X` >= `B`, the premium model is used. 
    If `X` < `B`, the fallback model is used.
    """
    ratio = server_total_usage / IDEAL_VOLUME_CAP
    
    if ratio > 1.2:
        return float('inf') # Hard boundary: protect margin
        
    # Exponential sliding curve. As ratio grows, boundary rockets up.
    boundary = B_MIN + (B_MAX - B_MIN) * (ratio ** 2)
    return boundary

def decide_translation_route(content: str, current_usage: int) -> str:
    """
    Decides the translation routing strategy based on sliding algorithm.
    Returns: 'gemini-2.5-flash', 'gemini-2.5-flash-8b', or 'googletrans'
    """
    score = get_complexity_score(content)
    boundary = get_translation_boundary(current_usage)
    
    if boundary == float('inf'):
        # Maximum degradation triggered
        return 'googletrans'
        
    if score >= boundary:
        return 'gemini-2.5-flash'
    else:
        return 'gemini-2.5-flash-8b'

def perform_google_translate_fallback(text: str, target_language: str) -> str:
    """
    Synchronous GoogleTranslator fallback for limit protection.
    Includes retry logic for transient failures (503, timeouts, etc).
    """
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target=target_language.lower()[:50])
            result = translator.translate(text)
            if result:
                return result
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle 503 Service Unavailable and similar transient errors
            if any(code in error_str for code in ['503', 'service unavailable', 'temporarily unavailable']):
                if attempt < max_retries - 1:
                    # Exponential backoff: 0.5s, 1s, 1.5s
                    time.sleep(retry_delay * (attempt + 1))
                    continue
            
            # Handle timeout and connection errors
            if any(err in error_str for err in ['timeout', 'connection refused', 'connection error']):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
            
            # Log unexpected errors
            print(f"Google Translate fallback error (attempt {attempt + 1}/{max_retries}): {e}")
            
            # If this is the last attempt, fail silently
            if attempt == max_retries - 1:
                return ""
    
    return ""
