#!/bin/bash

# TradingAgents Production Deployment Script
echo "🚀 Starting TradingAgents Deployment..."

# 1. Pull latest images and build
echo "📦 Building production containers..."
docker-compose -f docker-compose.prod.yml build

# 2. Spin up the stack
echo "⚡ Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# 3. Initialize Ollama model
echo "🧠 Initializing AI model (Llama 3 8B)..."
# Wait for Ollama to be ready
sleep 15
docker exec trading-ollama ollama pull llama3:8b

echo "✅ Deployment Complete!"
echo "🌍 Your site is live at https://ecotron.co.in"
