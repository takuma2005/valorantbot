# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Valorant Leaderboard Discord Bot (Python) - displays server member Valorant rankings using the Henrik Valorant API.

## Development Commands
- `pip install -r requirements.txt` - Install dependencies
- `python bot.py` - Start the bot
- Copy `.env.example` to `.env` and configure before first run

## Architecture
- **Entry point**: `bot.py` - main bot initialization and event handling
- **Commands**: `src/commands/` - Discord.py cog implementations
  - `leaderboard.py` - displays server rankings
  - `register.py` - player account registration  
  - `unregister.py` - remove player registration
  - `rank.py` - individual player rank lookup
  - `auto_update.py` - 5-minute automatic leaderboard updates
- **API Integration**: `src/valorant_api.py` - async Valorant API client
- **Data Management**: `src/data_manager.py` - JSON-based player data storage
- **Storage**: `data/` directory with guild-specific JSON files

## Key Dependencies
- discord.py 2.3+ - Discord API integration with slash commands
- aiohttp - Async HTTP requests to Valorant API
- python-dotenv - Environment variable management

## Environment Configuration
Required in `.env`:
- `DISCORD_TOKEN` - Discord bot token
- `DISCORD_GUILD_ID` - Test guild ID (optional, for faster command sync)
- `VALORANT_API_KEY` - Henrik Valorant API key from their Discord
- `DEFAULT_REGION` - default region (ap, na, eu, kr, latam, br)

## API Integration Details
Uses Henrik Valorant API (https://github.com/Henrik-3/unofficial-valorant-api):
- Rate limits: 30 req/min (Basic) or 90 req/min (Advanced)
- Endpoints: `/v2/account/`, `/v3/mmr/` for player data
- Supports all major regions
- Returns competitive rank and RR (ranking rating) data

## Data Storage
JSON file storage in `data/` directory with guild-specific files. For production, consider migrating to database (SQLite, PostgreSQL, MongoDB).

## Python-Specific Notes
- Uses discord.py cogs for command organization
- Async/await pattern for non-blocking API calls
- Type hints for better code maintainability
- Asyncio semaphore for API rate limiting

## Security Considerations  
- Environment variables for sensitive tokens
- Input validation and sanitization
- Rate limiting with asyncio semaphore
- Comprehensive error handling for API failures