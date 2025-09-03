# Discord Valorant Bot - Docker Deployment

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your tokens
nano .env
```

### 2. Docker Compose (Recommended)
```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f valorant-bot

# Stop the bot
docker-compose down
```

### 3. Manual Docker Build
```bash
# Build image
docker build -t valorant-bot .

# Run container
docker run -d \
  --name valorant-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  valorant-bot
```

## Configuration

### Required Environment Variables
- `DISCORD_TOKEN` - Discord bot token
- `VALORANT_API_KEY` - Henrik Valorant API key

### Optional Environment Variables
- `DISCORD_GUILD_ID` - Test guild ID for faster command sync
- `DEFAULT_REGION` - Default region (ap, na, eu, kr, latam, br)

## Management Commands

```bash
# View container status
docker-compose ps

# View logs (live)
docker-compose logs -f

# Restart bot
docker-compose restart valorant-bot

# Update and rebuild
docker-compose build --no-cache
docker-compose up -d

# Clean up
docker-compose down -v
```

## Data Persistence

- Bot data stored in `./data/` directory
- Logs stored in `./logs/` directory  
- Automatic restart on container failure

## Troubleshooting

### Check bot status
```bash
docker-compose logs valorant-bot
```

### Enter container for debugging
```bash
docker-compose exec valorant-bot bash
```

### Reset data
```bash
docker-compose down
rm -rf data/
docker-compose up -d
```

## Production Deployment

1. Set `restart: always` in docker-compose.yml
2. Use proper logging configuration
3. Set up monitoring/alerting
4. Regular backups of data directory