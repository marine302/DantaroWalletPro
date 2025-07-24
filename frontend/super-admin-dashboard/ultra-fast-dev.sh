#!/bin/bash

# Ultra-fast development start script
echo "⚡ Ultra-Fast Dev Mode Starting..."

# Set memory options
export NODE_OPTIONS="--max-old-space-size=4096"
export NEXT_TELEMETRY_DISABLED=1

# Kill any processes on port 3020
lsof -ti:3020 | xargs kill -9 2>/dev/null || true

# Clean caches aggressively
echo "🧹 Cleaning all caches..."
rm -rf .next
rm -rf node_modules/.cache
rm -rf .swc

# Quick dependency check
if [ ! -f "node_modules/.package-lock.json" ]; then
  echo "📦 Quick install..."
  npm ci --prefer-offline --no-audit --no-fund --silent
fi

# Start with minimal logging
echo "🚀 Starting development server on port 3020..."
NODE_ENV=development npx next dev -p 3020 --turbo 2>/dev/null
