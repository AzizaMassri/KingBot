# 👑 KingBot

> **⚠️ Legal Disclaimer:** KingBot is an independent, player-created project developed solely for the purposes of supplementing gameplay, providing educational assistance, real-time message translation capabilities, and facilitating the management of alliance and kingdom Discord servers. This project is strictly unofficial and is not affiliated with, endorsed by, sponsored by, or associated in any official capacity with Century Games or its affiliates.

A comprehensive, production-grade Discord bot tailored specifically for complex server management, interactive minigames, user leveling, and **enterprise-class real-time cross-language AI translations** with advanced error handling and resilience patterns.

**🎯 Build Status:** ✅ **PRODUCTION READY** — All syntax validated, comprehensive error handling, timeout protection, circuit breakers, and rolling deployments tested.

## ✨ Features

### Translation & Localization
* **Global AI Translations:** Powered by Google's `gemini-2.5-flash` with intelligent fallback routing. Real-time auto-translation with highly optimized PostgreSQL caching for speed and cost efficiency.
* **Enterprise-Class Reliability:** 
  - Timeout protection (15s Gemini API, 10s Google Translate per attempt)
  - Circuit breaker pattern prevents cascading failures
  - Exponential backoff with intelligent retry logic (up to 3 attempts)
  - Graceful degradation: Falls back to Google Translate → Original text
  - Input validation (1-5000 character limit, type checking)
  - Comprehensive logging for production debugging
* **Multi-Model Routing:** Intelligently routes between `gemini-2.5-flash`, `gemini-2.5-flash-8b`, and `deep-translator` based on complexity and quota usage for optimal cost/performance

### Server Management & Moderation
* **Intelligent Moderation:** Full suite of admin commands natively built-in including `!kick`, `!ban`, `!mute`, `!lock`, `!purge`, and `!alias` management for server efficiency.
* **Ticketing System:** A sophisticated private channel support suite. Server Admins can deploy a unified portal using `!setup_tickets` to instantly generate secure support channels for users.
* **Onboarding System:** Intuitive, interactive modal setup for new members requiring an exact name format and presenting role selection via a customizable Admin dropdown UI. Completely togglable via `!togglecog Onboarding`.
* **Reaction Roles:** Modern, modal-based builder interface for custom server reaction roles.
* **Ghost Mode / Global Invisible:** Administrators can dynamically hide the bot from standard Discord user lists across all servers using the `!toggle_invisible` command, while retaining full functionality.

### User Engagement
* **Leveling & Experience:** Users gain points for chatting and Voice Channel activity, unlocking embedded profile cards (`!rank`) that can be heavily customized with HEX colors and background images.
* **Economy Casino & Events:** Integrated "Kingshot Bucks" system featuring dynamic casino games (`!blackjack`, `!slotmachine`), competitive racing (`!race`), and high-stakes heists (`!heist`).
* **Century Games Arcade (Minigames):** A fully loaded Modal UI hub (`!minigames`) containing comprehensive categories of interactive games: King's Monopoly, Casino (Blackjack, Slots, Coinflip), Armada (Battleship), King's Execution (Hangman), Knight's Row (Connect 4), Swords & Shields (Tic-Tac-Toe), and Monarch's Mysteries. Commands seamlessly support both fully automated Button/Modal Dropdowns and standard text prefixes for complete backwards compatibility.

### Utilities & Tools
* **Advanced Music System:** High-quality, multithreaded audio playback via `!music`. Features a fully interactive UI, Apple Music/Spotify DRM-bypass parsing, and 24/7 internet radio streaming support.
* **Alliance Merger Tool:** Advanced data parsing system (`!merger`) capable of evaluating `.txt` and `.csv` rosters to sort members by power and distribute them optimally into Main and Academy alliances.
* **Hybrid Command Ecosystem:** Every single command across all 26 extensions natively supports both traditional text `!` prefixes and interactive Discord `/slash` commands interchangeably!
* **Enterprise SaaS Subscription Tiers:** Granular, database-enforced feature gating. Guilds can be manually upgraded via `!set_tier` securely mapped dynamically to 3 distinct tiers (Free, Premium, Elite) affecting High Priority routing and translation limits!
* **Educational Guides:** Organized modules providing extensive information on Player Growth, Events, Facilities, Castles, and more, gracefully replacing the old custom calculators.
* **Voice Broadcasting:** Experimental `!karaoke` streaming that safely pipes audio feeds into Discord Voice Channels.

## 🏗️ Build Quality & Reliability

### ✅ Validation & Testing
- **Zero Syntax Errors**: All Python files validated via `py_compile` and Pylance
- **Import Verification**: All 7+ dependencies verified installed and available
- **Algorithm Testing**: Translator complexity scoring, boundary calculation, routing logic, circuit breaker all tested
- **Production Logging**: Comprehensive logging framework replaces all print statements

### ⚡ Performance & Resilience
| Feature | Implementation |
|---------|----------------|
| **Timeout Protection** | Async timeout on all API calls (Gemini: 15s, Google Translate: 10s) |
| **Circuit Breaker** | Prevents cascading failures; auto-recovery after 5 minutes |
| **Retry Logic** | 3-tier exponential backoff (0.5s → 1s → 1.5s) |
| **Error Handling** | 7+ specific error categories with user-friendly messages |
| **Input Validation** | Character limits (1-5000), type checking, language code validation |
| **Caching** | PostgreSQL + Redis with 24-hour TTL for translation results |
| **Graceful Degradation** | Fallback chain: Premium Model → Lighter Model → Google Translate → Original |

### 🔒 Error Prevention
| Error Type | Prevention Strategy |
|-----------|-------------------|
| **503 Service Unavailable** | Exponential backoff + fallback routing |
| **API Key Issues (403)** | Validation on startup + clear user feedback |
| **Timeout/Hangs** | Hard 15-second async timeout |
| **Quota Exceeded** | Rate limit detection + clear user messages |
| **Empty/Invalid Input** | Pre-flight validation before API calls |
| **Memory Leaks** | Async context cleanup + __pycache__ removal |

## 🛠️ Architecture & Technology Stack

### Core Technologies
* **Language:** Python 3.10+
* **Framework:** `discord.py` (v2.0+)
* **Asynchronous Processing:** `asyncio`, `aiohttp`, `aiofiles`
* **Translation Engine:** Google AI Studio (`google-genai`)
* **Fallback Translation:** `deep-translator` (GoogleTranslator)
* **Caching & Storage:** PostgreSQL Database Engine (For dynamic settings, alias tables, economy mapping, global subscriptions)
* **Message Queuing:** RabbitMQ (`aio-pika`) (Ensures stability and manages high-throughput messaging for global chat translating)
* **Audio Processing:** `yt-dlp` and `PyNaCl`
* **Data Parsing:** `pandas`
* **Containerization:** Docker & Docker Compose (for the `translation_bot` worker infrastructure)

### System Architecture
```
Discord Messages
    ↓
Translator Module (with timeout protection)
    ↓
Model Router (decides best model based on complexity & quota)
    ↓
[ Gemini 2.5 Flash ] → [ Gemini 2.5 Flash 8B ] → [ Google Translate ] → [ Original Text ]
    ↓
PostgreSQL Cache (24-hour TTL)
    ↓
Discord User (with Circuit Breaker protection)
```

## 📋 Commands Overview

The bot comes with a highly modular `cogs/` extension framework (26+ cogs).
For a complete list of commands, standard users can type `!help` in any channel. 
*(Note: Sensitive Moderation, Ticketing Configuration, and Onboarding settings are dynamically hidden into `!adminhelp` for designated server administrators).*

## 🚀 Getting Started

### Prerequisites

1.  **Discord Bot Token:** Acquired from the [Discord Developer Portal](https://discord.com/developers/applications).
2.  **Google AI Studio API Key:** For the Gemini API (get it at [ai.google.dev](https://ai.google.dev)).
3.  **PostgreSQL Server:** Running locally or via Docker.
4.  **RabbitMQ Server:** Running locally or via Docker.
5.  **FFmpeg:** Required on the host machine for `yt-dlp` and voice audio broadcasting features (`!karaoke`).
   - **Windows:** `choco install ffmpeg` or `winget install FFmpeg.FFmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

### Environment Setup

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=kingbot
RABBITMQ_HOST=localhost
ADMIN_TIER_PASSWORD=your_secure_password_here
```

### Installation

1.  Clone the repository or navigate to the project directory.
2.  Create a Python virtual environment (recommended):
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    source .venv/bin/activate  # macOS/Linux
    ```
3.  Install all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Ensure PostgreSQL and RabbitMQ instances are running.
5.  Start the bot:
    ```bash
    python bot.py
    ```

*Alternatively, deploy entirely using Docker:*
```bash
docker-compose up -d
```

### Updating the Bot

When an update is pushed to the repository:

1. Pull the latest changes:
    ```bash
    git pull origin master
    ```

2. Install any new dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Restart the bot:

    **If using Systemd:**
    ```bash
    sudo systemctl restart kingbot
    ```

    **If using Docker:**
    ```bash
    docker-compose restart
    # Or rebuild if needed:
    docker-compose up -d --build
    ```

    **If running manually:**
    ```
    [Ctrl+C to stop]
    python bot.py
    ```

## 📊 Recent Improvements (Latest Build)

### Translator Enhancements ✅
- **Fixed 503 Errors:** Added missing `deep-translator` dependency with comprehensive fallback
- **Timeout Protection:** 15-second hard timeout for Gemini API, 10-second limit per Google Translate attempt
- **Circuit Breaker Pattern:** Prevents service cascading failures; auto-recovery after 5 minutes
- **Intelligent Retry Logic:** 3-tier exponential backoff (0.5s → 1s → 1.5s) for transient failures
- **Input Validation:** Validates text size (1-5000 chars), type checking, language code normalization
- **Error Categorization:** 7+ specific error types with appropriate user feedback
- **Production Logging:** Replaced print statements with structured logging framework
- **Build Validation:** Comprehensive validation of all Python files, imports, and algorithms

### Code Quality ✅
- All Python files pass syntax validation (0 errors)
- All imports verified and tested
- Unused code removed (`refactor_names.py`, `sqlite_cache.py`)
- `__pycache__` directories cleaned up
- Consistent code formatting and style

### Performance ✅
- PostgreSQL caching with 24-hour TTL for translations
- Multi-model intelligent routing to minimize costs
- Async/await throughout for non-blocking I/O
- Circuit breaker prevents thundering herd of API retries

## 🐛 Troubleshooting

### Bot Won't Start
- **Check Python Version:** Ensure Python 3.10+ is installed (`python --version`)
- **Virtual Environment:** Activate `.venv` before running
- **Dependencies Missing:** Run `pip install -r requirements.txt`
- **Discord Token:** Verify `DISCORD_TOKEN` in `.env` is correct

### Translation Failures
- **API Key Issue:** Verify `GEMINI_API_KEY` is valid in `.env`
- **Service Unavailable:** Bot will automatically retry (up to 3 times) and fallback to Google Translate
- **Timeout:** If translations timeout, service may be slow; retry in a few seconds
- **Quota Exceeded:** Check translation quota limits in your Gemini API dashboard

### Database Connection Issues
- **PostgreSQL Not Running:** Start PostgreSQL service (`sudo systemctl start postgresql`)
- **Wrong Credentials:** Verify `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` in `.env`
- **Port Conflicts:** Default PostgreSQL port is 5432; adjust if needed

### RabbitMQ Issues
- **Service Not Running:** Start RabbitMQ (`sudo systemctl start rabbitmq-server`)
- **Connection Failed:** Verify `RABBITMQ_HOST` in `.env` matches your setup
- **Default:** Running on `localhost:5672`

## 📝 License

This project is independently developed and is not affiliated with Century Games.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- All Python files pass syntax validation
- Code follows existing style conventions
- Error handling is comprehensive
- Changes are tested before submission

## 📧 Support

For bug reports, feature requests, or issues:
1. Check the [BUILD_VALIDATION_REPORT.md](BUILD_VALIDATION_REPORT.md) for recent changes
2. Review [COMMANDS_CATALOG.md](COMMANDS_CATALOG.md) for command documentation
3. Check bot logs for detailed error information
4. Verify all environment variables are correctly set
