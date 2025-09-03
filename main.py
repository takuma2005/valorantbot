#!/usr/bin/env python3
"""
Discord Valorant Bot - Main Entry Point
Northflank compatible with health check endpoint
"""
import asyncio
import threading
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    """Simple health check handler"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "valorant-bot"}')
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"message": "Valorant Discord Bot is running!"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_health_server():
    """Start health check server on port 8000"""
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
        print("Health check server started on http://0.0.0.0:8000")
        server.serve_forever()
    except Exception as e:
        print(f"Failed to start health server: {e}")

async def main():
    """Main application entry point"""
    print("=" * 50)
    print("🤖 Starting Valorant Discord Bot")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)
    
    # Start health check server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Set environment variables directly
    os.environ['DISCORD_TOKEN'] = 'MTQwMDE5MzIyMjgxMDE0NDk0Mg.GzdOxi.eFkGpEzE2QW2nknnTlvgU85FNZm7h6oqO3MnhE'
    os.environ['VALORANT_API_KEY'] = 'HDEV-a6371732-b2b9-467c-92d0-47b438225d48'
    os.environ['DEFAULT_REGION'] = 'ap'
    
    print("✅ Environment variables configured")
    
    # Import and start Discord bot
    try:
        from bot import main as bot_main
        print("🚀 Starting Discord bot...")
        await bot_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)