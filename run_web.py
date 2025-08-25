#!/usr/bin/env python3
"""
Web Dashboard Test Script
Test the FastAPI web dashboard
"""

import sys
import os
import asyncio
import uvicorn

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from web.app import app

if __name__ == "__main__":
    print("🌐 Starting Smart Investment Bot Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔴 Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )