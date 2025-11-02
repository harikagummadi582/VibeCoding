# Flappy Kiro

An arcade-style game where you control Ghosty, a ghost that navigates through walls with gaps. Built with HTML/JavaScript frontend and Python/Flask backend.

## Features

- 🎮 3 difficulty levels (Easy, Medium, Hard)
- 🏆 Global leaderboard with username validation
- 📊 OpenTelemetry logging and tracing
- 🐳 Containerized for local testing and cloud deployment
- 👻 Smooth gameplay with physics-based movement

## Quick Start

```bash
# Make start script executable and run
./start-dev.sh

# Or manually with docker-compose
docker-compose up --build
```

**Access Points:**

- 🎮 Game: http://localhost:3000
- 🔧 API: http://localhost:5000
- 📊 Jaeger Tracing: http://localhost:16686

## Game Controls

- **Spacebar**: Make Ghosty fly up
- **Gravity**: Ghosty falls automatically
- **Goal**: Navigate through wall gaps to score points

## Difficulty Levels

- **Easy**: Slower walls, larger gaps, gentler physics
- **Medium**: Balanced gameplay
- **Hard**: Fast walls, small gaps, challenging physics

## Architecture

- **Frontend**: HTML/CSS/JavaScript with Canvas API
- **Backend**: Python Flask REST API
- **Storage**: JSON file-based leaderboard
- **Monitoring**: OpenTelemetry with Jaeger tracing
- **Containerization**: Docker with docker-compose

## API Endpoints

- `POST /scores` - Submit high score
- `GET /leaderboard` - Get top 20 scores
- `GET /stats` - Game statistics
- `POST /logs` - Frontend logging endpoint
- `GET /health` - Health check

## Development

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```
