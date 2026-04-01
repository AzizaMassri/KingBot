# 🎵 KingBot Music Integration Guide

KingBot features a highly advanced, multi-threaded music streaming module (`!music`) capable of playing direct links, YouTube searches, Apple Music, Spotify, Tidal, Deezer, and ambient Internet Radio (`.m3u` / `.pls`). 

This guide outlines how to ensure the bot can fetch and play everything flawlessly.

## Prerequisites

### 1. FFmpeg is Required
Because the Music system dynamically buffers live streaming media into Discord, you **must** have `ffmpeg` installed on your host machine to process the PCM audio.
- **Docker:** If you are running the bot via the provided `docker-compose.yml`, `ffmpeg` is **already built-in** to the Dockerfile. You don't need to do anything.
- **Native Windows/Linux:** You must install FFmpeg and add it to your system PATH.

### 2. Multi-Service Streaming (Spotify, Apple Music, Deezer)
To ensure uninterrupted playback across DRM-protected platforms like Spotify and Apple Music, KingBot utilizes an intelligent metadata bypass:
- When a user links a Spotify or Apple Music song, the bot reads the track name and artist.
- It then pipes this query seamlessly into `yt-dlp` to fetch the highest quality, DRM-free YouTube equivalent in milliseconds.

> [!TIP]
> **No API Keys Required:** Unlike older bots, `yt-dlp` does this without requiring you to manually register Spotify Developer credentials, saving you setup time and preventing expired tokens from breaking the server!

## Smart Admin Limits
To protect your VPS / host machine from running out of memory or getting IP-banned by YouTube:
1. **Queue Size:** Standard users can queue up to 100 items per server.
2. **Duration Limits:** Standard VODs (videos/MP3s) are limited to 3 hours maximum per track. 
3. **Live Streams:** If a user links an internet radio stream or a 24/7 Live YouTube stream, the duration limit is automatically bypassed, allowing for infinite background ambience.

*Note: Server Administrators automatically bypass the 100-item queue restriction!*
