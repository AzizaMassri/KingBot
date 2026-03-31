#!/bin/bash
# KingBot Graceful Update Script
#
# This script is designed to cleanly update the bot while intentionally AVOIDING
# aggressive Docker teardowns that trigger Ubuntu AppArmor and iptables networking bugs.

echo "🛑 Stopping the KingBot container to release OS network/volume locks..."
docker compose stop kingbot-app

echo "⬇️ Pulling latest approved changes from GitHub..."
git pull origin master

echo "🏗️ Rebuilding and starting the new container..."
# Using --build on a single specific container prevents recreating unaffected services like postgres
# explicitly skipping 'down' ensures the virtual iptables network is never destroyed
docker compose up -d --build kingbot-app

echo "✅ Update complete! KingBot is back online asynchronously."
