"""
McDonald's Outlet API Server

Simple script to run the FastAPI application for McDonald's outlet management.
"""

import uvicorn
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Configuration
    host = "127.0.0.1"  # localhost
    port = 8000         # default port
    reload = True       # auto-reload on code changes
    
    print("🍟 McDonald's Outlet API Server")
    print("=" * 50)
    print(f"Starting server at: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Alternative Docs: http://{host}:{port}/redoc")
    print("=" * 50)
    print("Available Endpoints:")
    print("  GET  /                - Health check")
    print("  POST /scrape-outlets  - Scrape outlets (no DB save)")
    print("  POST /save-outlets    - Scrape and save to DB")
    print("  POST /save-data       - Save provided data to DB")
    print("  GET  /outlets         - Get saved outlets from DB")
    print("=" * 50)
    print("Press Ctrl+C to stop the server\n")
    
    # Start the server
    try:
        uvicorn.run(
            "src.api.mcdonalds_api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 