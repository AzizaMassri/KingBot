# 👑 KingBot

> **⚠️ Legal Disclaimer:** KingBot is an independent, player-created project developed solely for the purposes of supplementing gameplay, providing educational assistance, real-time message translation capabilities, and facilitating the management of alliance and kingdom Discord servers. This project is strictly unofficial and is not affiliated with, endorsed by, sponsored by, or associated in any official capacity with Century Games or its affiliates.

A comprehensive, multi-purpose Discord bot tailored specifically for complex server management, interactive minigames, user leveling, and real-time cross-language AI translations.

## ✨ Features

* **Global AI Translations:** Powered by Google's `gemini-2.5-flash`, the bot seamlessly auto-translates live chat messages dynamically with highly optimized PostgreSQL caching for speed and cost efficiency.
* **Intelligent Moderation:** Full suite of admin commands natively built-in including `!kick`, `!ban`, `!mute`, `!lock`, `!purge`, and `!alias` management for server efficiency.
* **Ticketing System:** A sophisticated private channel support suite. Server Admins can deploy a unified portal using `!setup_tickets` to instantly generate secure support channels for users.
* **Onboarding System:** Intuitive, interactive modal setup for new members requiring an exact name format and presenting role selection via a customizable Admin dropdown UI. Completely togglable via `!togglecog Onboarding`.
* **Reaction Roles:** Modern, modal-based builder interface for custom server reaction roles.
* **Ghost Mode / Global Invisible:** Administrators can dynamically hide the bot from standard Discord user lists across all servers using the `!toggle_invisible` command, while retaining full functionality.
* **Leveling & Experience:** Users gain points for chatting and Voice Channel activity, unlocking embedded profile cards (`!rank`) that can be heavily customized with HEX colors and background images.
* **Economy Casino & Events:** Integrated "Kingshot Bucks" system featuring dynamic casino games (`!blackjack`, `!slotmachine`), competitive racing (`!race`), and high-stakes heists (`!heist`).
* **Century Games Arcade (Minigames):** A fully loaded Modal UI hub (`!minigames`) containing comprehensive categories of interactive games: King's Monopoly, Casino (Blackjack, Slots, Coinflip), Armada (Battleship), King's Execution (Hangman), Knight's Row (Connect 4), Swords & Shields (Tic-Tac-Toe), and Monarch's Mysteries. Commands seamlessly support both fully automated Button/Modal Dropdowns and standard text prefixes for complete backwards compatibility.
* **Advanced Music System:** High-quality, multithreaded audio playback via `!music`. Features a fully interactive UI, Apple Music/Spotify DRM-bypass parsing, and 24/7 internet radio streaming support.
* **Alliance Merger Tool:** Advanced data parsing system (`!merger`) capable of evaluating `.txt` and `.csv` rosters to sort members by power and distribute them optimally into Main and Academy alliances.
* **Educational Guides:** Work-in-progress manuals providing extensive information on Player Growth, Events, Facilities, Castles, and more, efficiently replacing the old custom calculators.
* **Voice Broadcasting:** Experimental `!karaoke` streaming that safely pipes audio feeds into Discord Voice Channels.

## 🛠️ Architecture & Technology Stack

* **Language:** Python 3.10+
* **Framework:** `discord.py` (v2.0+)
* **Asynchronous Processing:** `asyncio`, `aiohttp`, `aiofiles`
* **Translation Engine:** Google AI Studio (`google-genai`)
* **Caching & Storage:** PostgreSQL Database Engine (For dynamic settings, alias tables, economy mapping, global subscriptions)
* **Message Queuing:** RabbitMQ (`aio-pika`) (Ensures stability and manages high-throughput messaging for global chat translating)
* **Audio Processing:** `yt-dlp` and `PyNaCl`
* **Data Parsing:** `pandas`
* **Containerization:** Docker & Docker Compose (for the `translation_bot` worker infrastructure)

## 📋 Commands Overview

The bot comes with a highly modular `cogs/` extension framework.
For a complete list of commands, standard users can type `!help` in any channel. 
*(Note: Sensitive Moderation, Ticketing Configuration, and Onboarding settings are dynamically hidden into `!adminhelp` for designated server administrators).*

## 🚀 Getting Started

### Prerequisites

1.  **Discord Bot Token:** Acquired from the Discord Developer Portal.
2.  **Google AI Studio API Key:** For the Gemini API.
3.  **PostgreSQL Server:** Running locally or via Docker.
4.  **RabbitMQ Server:** Running locally or via Docker.
5.  **FFmpeg:** Required on the host machine for `yt-dlp` and voice audio broadcasting features (`!karaoke`).

### Environment Setup

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=kingbot
RABBITMQ_HOST=localhost
```

### Installation

1.  Clone the repository or navigate to the project directory.
2.  Install all dependencies via `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
3. Ensure your local instances or remote instances of PostgreSQL and RabbitMQ are running.
4. Start the bot:
    ```bash
    python bot.py
    ```

*Alternatively, the bot can be deployed entirely using its Docker infrastructure setup (e.g., `docker-compose up -d`).*

### Updating the Bot

When an update is pushed to the repository, you can easily pull the new changes and restart the bot to apply them.

1. Navigate to your bot's directory and pull the latest changes:
    ```bash
    git pull origin main
    ```

2. If any new dependencies were added, install them:
    ```bash
    pip install -r requirements.txt
    ```

3. Restart the bot depending on your deployment method:

    **If using Systemd (`kingbot.service`):**
    ```bash
    sudo systemctl restart kingbot
    ```

    **If using Docker:**
    ```bash
    docker-compose restart
    # Or if you need to rebuild the image
    docker-compose up -d --build
    ```

    **If running manually in a terminal:**
    Stop the script using `Ctrl+C` and restart it:
    ```bash
    python bot.py
    ```
