#!/bin/bash

echo "Starting Flappy Kiro development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start containers
echo "Building and starting containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🎮 Game: http://localhost:3000"
    echo "🔧 API: http://localhost:5000"
    echo "📊 Jaeger (Tracing): http://localhost:16686"
    echo ""
    echo "To stop: docker-compose down"
    echo "To view logs: docker-compose logs -f"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi