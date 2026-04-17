import re
import asyncio
import time
from typing import Optional

# Constants for Margin Calculation
# Target monthly quota before reaching peak degradation. 
IDEAL_VOLUME_CAP = 40000000 
B_MIN = 15
B_MAX = 250

# Request size limits (in characters)
MAX_REQUEST_SIZE = 5000
MIN_REQUEST_SIZE = 1

# Timeout constants (seconds)
GOOGLE_TRANSLATE_TIMEOUT = 10
GEMINI_API_TIMEOUT = 15

# Circuit breaker settings
FAILURE_THRESHOLD = 5
RECOVERY_TIME = 300  # 5 minutes


class CircuitBreaker:
    """Simple circuit breaker to prevent repeated failures."""
    def __init__(self, failure_threshold: int = FAILURE_THRESHOLD, recovery_time: int = RECOVERY_TIME):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
    
    def can_attempt(self) -> bool:
        if not self.is_open:
            return True
        
        # Check if recovery time has passed
        if time.time() - self.last_failure_time > self.recovery_time:
            self.is_open = False
            self.failure_count = 0
            return True
        
        return False


# Global circuit breakers for each service
google_translate_breaker = CircuitBreaker()


def validate_translation_input(text: str, target_language: str) -> tuple[bool, Optional[str]]:
    """
    Validates translation input before API call.
    Returns: (is_valid, error_message)
    """
    if not text or not isinstance(text, str):
        return False, "Text cannot be empty"
    
    if not target_language or not isinstance(target_language, str):
        return False, "Target language must be specified"
    
    text_length = len(text.strip())
    if text_length < MIN_REQUEST_SIZE:
        return False, "Text is too short to translate"
    
    if text_length > MAX_REQUEST_SIZE:
        return False, f"Text is too long (max {MAX_REQUEST_SIZE} characters)"
    
    return True, None


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
    if server_total_usage <= 0:
        return B_MIN
    
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
    Includes retry logic with exponential backoff for transient failures.
    """
    # Check circuit breaker first
    if not google_translate_breaker.can_attempt():
        return ""
    
    # Validate input
    is_valid, error_msg = validate_translation_input(text, target_language)
    if not is_valid:
        return ""
    
    max_retries = 3
    base_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            from deep_translator import GoogleTranslator
            
            # Pass the full language name (lowercased); deep_translator handles name resolution
            lang_code = target_language.lower()
            translator = GoogleTranslator(source='auto', target=lang_code)
            
            # Execute translation with timeout protection
            result = translator.translate(text)
            
            if result and isinstance(result, str) and result.strip():
                google_translate_breaker.record_success()
                return result.strip()
            
            # Empty result - possibly a transient issue
            if attempt < max_retries - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
            
        except ImportError:
            # deep_translator not installed
            print("ERROR: deep_translator library not installed. Install with: pip install deep-translator")
            return ""
        except Exception as e:
            error_str = str(e).lower()
            
            # Categorize the error
            is_transient = any(code in error_str for code in [
                '503', 'service unavailable', 'temporarily unavailable',
                'timeout', 'connection refused', 'connection error',
                'temporary', 'try again', 'busy'
            ])
            
            # Log with attempt counter
            print(f"Google Translate attempt {attempt + 1}/{max_retries} failed: {e}")
            
            # Retry on transient errors
            if is_transient and attempt < max_retries - 1:
                # Exponential backoff: 0.5s, 1s, 1.5s
                time.sleep(base_delay * (attempt + 1))
                continue
            
            # Permanent error or last attempt
            if attempt == max_retries - 1:
                google_translate_breaker.record_failure()
            
            # Don't retry on permanent errors
            if not is_transient:
                break
    
    return ""
