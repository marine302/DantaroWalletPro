#!/bin/bash

# Quick development script for Dantaro Super Admin Dashboard
echo "🚀 Starting Quick Development Environment..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "next" 2>/dev/null || true
pkill -f "node.*3000" 2>/dev/null || true

# Clean Next.js cache
echo "🗑️ Cleaning cache..."
rm -rf .next 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true

# Quick install check
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install --prefer-offline --no-audit --no-fund
fi

# Start development server
echo "🌟 Starting development server..."
NODE_ENV=development PORT=3000 npm run dev
