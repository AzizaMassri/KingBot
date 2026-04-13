#!/usr/bin/env python3
"""
Build validation script - validates translator components without running the full bot
"""

import sys
import os

# Add cogs directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_translator_algo():
    """Test translator algorithm without API calls"""
    print("Testing translator_algo.py...")
    
    try:
        from cogs.utils.translator_algo import (
            get_complexity_score, 
            get_translation_boundary,
            decide_translation_route,
            validate_translation_input,
            CircuitBreaker
        )
        
        # Test complexity scoring
        assert get_complexity_score("Hello world") > 0
        assert get_complexity_score("") == 0
        print("✓ Complexity scoring works")
        
        # Test boundary calculation
        boundary_low = get_translation_boundary(0)
        boundary_high = get_translation_boundary(50000000)
        assert boundary_low < boundary_high or boundary_high == float('inf')
        print("✓ Translation boundary calculation works")
        
        # Test routing decision
        route = decide_translation_route("Hello world", 100)
        assert route in ['gemini-2.5-flash', 'gemini-2.5-flash-8b', 'googletrans']
        print("✓ Translation routing works")
        
        # Test input validation
        is_valid, error = validate_translation_input("Hello", "English")
        assert is_valid == True
        print("✓ Input validation works")
        
        is_valid, error = validate_translation_input("", "English")
        assert is_valid == False
        print("✓ Input validation catches empty text")
        
        # Test circuit breaker
        breaker = CircuitBreaker(failure_threshold=3, recovery_time=10)
        assert breaker.can_attempt() == True
        breaker.record_failure()
        assert breaker.can_attempt() == True
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open == True
        assert breaker.can_attempt() == False
        breaker.record_success()
        assert breaker.is_open == False
        print("✓ Circuit breaker works")
        
        print("✅ All translator_algo tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ translator_algo test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test that all critical imports are available"""
    print("Testing imports...")
    
    try:
        import discord
        print("✓ discord.py installed")
        
        from google import genai
        print("✓ google-genai installed")
        
        # deep_translator may not be installed yet in venv
        try:
            from deep_translator import GoogleTranslator
            print("✓ deep-translator installed")
        except ImportError:
            print("⚠ deep-translator not yet installed (will be installed on first run)")
        
        import asyncpg
        print("✓ asyncpg installed")
        
        print("✅ All critical imports are available!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Missing import: {e}\n")
        return False


def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        'bot.py',
        'requirements.txt',
        'cogs/quick_translator.py',
        'cogs/utils/translator.py',
        'cogs/utils/translator_algo.py',
        '.env'
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.startswith('.env'):
            # .env is optional but recommended for testing
            if os.path.exists(file_path):
                print(f"✓ {file_path} exists")
            else:
                print(f"⚠ {file_path} not found (create for local testing)")
            continue
            
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    if all_exist:
        print("✅ All required files present!\n")
    else:
        print("❌ Some files are missing!\n")
    
    return all_exist


def main():
    """Run all validation tests"""
    print("=" * 50)
    print("KingBot Build Validation")
    print("=" * 50 + "\n")
    
    results = {
        'File Structure': test_file_structure(),
        'Imports': test_imports(),
        'Translator Algorithm': test_translator_algo(),
    }
    
    print("=" * 50)
    print("VALIDATION RESULTS")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "PASS ✅" if passed else "FAIL ❌"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 Build validation PASSED! Ready for deployment.")
        return 0
    else:
        print("\n⚠ Build validation FAILED. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
