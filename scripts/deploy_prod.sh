#!/bin/bash

# TradingAgents Production Deployment Script
echo "🚀 Starting TradingAgents Deployment..."

# 0. Clean state and pull
echo "🔄 Updating code from git..."
git fetch origin main
git reset --hard origin/main

# 1. Pull latest images and build
echo "📦 Building production containers..."
docker compose -f docker-compose.prod.yml build --no-cache

# 2. Spin down and clean up to avoid conflicts
echo "🧹 Cleaning up old containers..."
docker compose -f docker-compose.prod.yml down --remove-orphans

# 3. Spin up the stack
echo "⚡ Starting services..."
docker compose -f docker-compose.prod.yml up -d

# 3. Initialize Ollama model
echo "🧠 Initializing AI model (Llama 3 8B)..."
echo "Waiting for Ollama to start..."
sleep 15
docker exec trading-ollama ollama pull llama3:8b

echo "✅ Deployment Complete!"
echo "🌍 Your site is live at https://ecotron.co.in"
