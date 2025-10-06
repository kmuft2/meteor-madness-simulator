#!/usr/bin/env python3
"""
Start the Meteor Madness Simulator API server
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    print("=" * 70)
    print("🚀 Starting Meteor Madness Simulator API")
    print("=" * 70)
    print(f"Server: http://{settings.api_host}:{settings.api_port}")
    print(f"Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print("=" * 70)
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
