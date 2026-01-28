#!/bin/bash
# Quick start script for Docker Compose setup

set -e

echo "🚀 Starting Bookly with Docker Compose"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your API keys before continuing!"
        echo ""
        read -p "Press Enter after editing .env, or Ctrl+C to cancel..."
    else
        echo "❌ No .env.example found. Please create .env manually."
        exit 1
    fi
fi

echo "📦 Building and starting containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access your application:"
echo "   Frontend:     http://localhost:5173"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Analytics:    http://localhost:5173/analytics"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose stop"
echo ""
echo "🗑️  Stop and remove (keeps database):"
echo "   docker-compose down"
echo ""
echo "💾 Database data is persisted in volume: postgres_data"
echo ""
