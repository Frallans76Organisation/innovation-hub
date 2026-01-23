#!/usr/bin/env python3
"""
Startup script for Innovation Hub - Module 1: Core Data Foundation
Run with: python start_new.py
"""

import uvicorn
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from innovation_hub.api.main import app
from innovation_hub.database import get_db
from innovation_hub.tests import create_seed_data, reset_database

def setup_database():
    """Set up database with initial data (only if empty)"""
    db = next(get_db())
    try:
        from innovation_hub.database import Idea

        # Check if database already has data
        idea_count = db.query(Idea).count()

        if idea_count > 0:
            print(f"✅ Database already initialized ({idea_count} ideas)")
            return True

        print("🔄 Setting up database for first time...")
        reset_database(db)
        create_seed_data(db)
        print("✅ Database ready!")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    finally:
        db.close()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Innovation Hub API Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    print("🏗️ Innovation Hub - Module 1: Core Data Foundation")
    print("=" * 50)

    # Setup database
    if not setup_database():
        exit(1)

    print("\n🚀 Starting Innovation Hub API...")
    print(f"📊 API: http://localhost:{args.port}")
    print(f"🔧 API Docs: http://localhost:{args.port}/docs")
    print(f"💡 Health Check: http://localhost:{args.port}/api/health")
    print(f"📈 Statistics: http://localhost:{args.port}/api/ideas/stats")
    print("\n" + "=" * 50)

    uvicorn.run(app, host=args.host, port=args.port)