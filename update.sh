#!/bin/bash
# KingBot Graceful Update Script
#
# This script is designed to cleanly update the bot while intentionally AVOIDING
# aggressive Docker teardowns that trigger Ubuntu AppArmor and iptables networking bugs.

set -euo pipefail

echo "🛑 Stopping the KingBot container to release OS network/volume locks..."
docker compose stop kingbot-app 2>/dev/null || true

echo "⬇️ Pulling latest approved changes from GitHub..."
git pull origin master

echo "🏗️ Rebuilding and starting the stack (app + dependencies)..."
if docker compose up -d --build kingbot-app; then
  echo "✅ Update complete! KingBot is back online asynchronously."
else
  echo "❌ docker compose failed."
  echo ""
  echo "If you saw 'permission denied' stopping postgres, clear the stuck container then retry:"
  echo "  sudo docker kill kingbot_postgres 2>/dev/null || true"
  echo "  sudo docker rm -f kingbot_postgres kingbot_rabbitmq kingbot_app 2>/dev/null || true"
  echo "  sudo docker ps -a --filter name=kingbot_postgres   # rm -f any extra Created duplicates by ID"
  echo "  sudo docker compose up -d"
  exit 1
fi
