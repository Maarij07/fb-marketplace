#!/usr/bin/env python
"""
Start the Facebook Marketplace Dashboard
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from web.app import create_app

if __name__ == '__main__':
    settings = Settings()
    app = create_app(settings)
    
    print("\n" + "="*50)
    print("Facebook Marketplace Dashboard")
    print("="*50)
    print("\n📊 Dashboard starting...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("\n✅ Backend is now reading from products.json")
    print("✅ SQLite database has been removed")
    print("✅ Posted dates should now show the actual Facebook post dates")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
