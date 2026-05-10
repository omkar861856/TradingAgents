#!/bin/bash

echo "🚀 Setting up TradingAgents Ollama models..."

# Check if ollama is running
if ! docker ps | grep -q "trading-ollama"; then
    echo "❌ Error: trading-ollama container is not running."
    echo "Run 'docker-compose up -d' first."
    exit 1
fi

echo "📦 Pulling Qwen3 (8B) - Default Analyst..."
docker exec -it trading-ollama ollama pull qwen3

echo "📦 Pulling GLM-4.7-Flash (30B) - For Deep Thinking..."
docker exec -it trading-ollama ollama pull glm-4.7-flash:latest

echo "✅ Ollama setup complete!"
