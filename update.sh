#!/bin/bash
# KingBot Graceful Update Script
#
# This script is designed to cleanly update the bot while intentionally AVOIDING
# aggressive Docker teardowns that trigger Ubuntu AppArmor and iptables networking bugs.

set -euo pipefail

echo "🛑 Stopping the KingBot container to release OS network/volume locks..."
docker compose stop kingbot-app 2>/dev/null || true

echo "⬇️ Pulling latest approved changes from GitHub..."
git pull https://ROCKETexecdevs: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@github.com/ROCKETexecdevs/KingBot.git master

echo "🧹 Pruning system to reclaim disk space (safely preserving databases/volumes)..."
docker system prune -a -f || true
sudo journalctl --vacuum-time=3d 2>/dev/null || true
sudo apt-get clean 2>/dev/null || true

echo "🏗️ Rebuilding and starting the stack (app + dependencies)..."
if docker compose up -d --build kingbot-app; then
  echo "✅ Update complete! KingBot is back online asynchronously."
else
  echo "❌ docker compose failed."
  echo ""
  echo "Check: sudo docker compose ps && sudo docker logs kingbot_rabbitmq && sudo docker logs kingbot_postgres"
  echo "If a dependency is stuck, recreate: sudo docker rm -f kingbot_rabbitmq kingbot_postgres kingbot_app 2>/dev/null; sudo docker compose up -d"
  exit 1
fi
