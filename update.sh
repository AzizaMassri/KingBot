#!/bin/bash
# KingBot Graceful Update Script
set -euo pipefail

echo "⬇️ Pulling latest approved changes from GitHub..."
git pull origin master

echo "🧹 Pruning system to reclaim disk space..."
docker system prune -a -f || true
sudo journalctl --vacuum-time=3d 2>/dev/null || true
sudo apt-get clean 2>/dev/null || true

echo "🏗️ Rebuilding and starting the container..."
docker compose up -d --build kingbot-app

echo "✅ Update complete! KingBot is back online."
