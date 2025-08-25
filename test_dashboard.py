#!/usr/bin/env python3

import sys
import threading
import time
import requests
import json
sys.path.insert(0, '.')

from web.app import create_app
from config.settings import Settings

def test_dashboard():
    """Test the dashboard endpoints"""
    
    # Create the app
    settings = Settings()
    app = create_app(settings)
    
    def run_app():
        app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
    
    # Start the app in a separate thread
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Starting Flask server...")
    time.sleep(2)
    
    base_url = "http://127.0.0.1:5555"
    
    try:
        # Test stats endpoint
        print("\n=== Testing /api/stats ===")
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            if data.get('success'):
                stats = data.get('data', {})
                print(f"Total listings: {stats.get('total_listings', 'N/A')}")
                print(f"Today: {stats.get('listings_today', 'N/A')}")
            else:
                print(f"Error: {data.get('error', 'Unknown')}")
        else:
            print(f"HTTP Error: {response.text}")
        
        # Test listings endpoint
        print("\n=== Testing /api/listings ===")
        response = requests.get(f"{base_url}/api/listings?limit=10", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            if data.get('success'):
                listings = data.get('data', [])
                print(f"Listings returned: {len(listings)}")
                
                for i, listing in enumerate(listings[:3], 1):
                    title = listing.get('title', 'NO TITLE')[:50]
                    price = listing.get('price_display', 'N/A')
                    created_at = listing.get('created_at', 'N/A')
                    print(f"  {i}. {title}... | {price} | {created_at}")
                
                # Show raw JSON for debugging
                print(f"\nFirst listing JSON sample:")
                if listings:
                    first = listings[0]
                    print(f"  ID: {first.get('id', 'N/A')}")
                    print(f"  Title: {first.get('title', 'N/A')}")
                    print(f"  Price: {first.get('price', {})}")
                    print(f"  Price Display: {first.get('price_display', 'N/A')}")
                    print(f"  Created At: {first.get('created_at', 'N/A')}")
                    print(f"  Added At: {first.get('added_at', 'N/A')}")
                    
            else:
                print(f"Error: {data.get('error', 'Unknown')}")
        else:
            print(f"HTTP Error: {response.text}")
        
        # Test main page
        print("\n=== Testing main dashboard page ===")
        response = requests.get(base_url, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Dashboard page loaded successfully")
            print(f"Dashboard available at: {base_url}")
            print("\n🎯 **SOLUTION**: Open your browser to http://127.0.0.1:5555 and check browser console (F12) for JavaScript errors!")
        else:
            print(f"Dashboard failed to load: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        print("Failed to connect to Flask server")
    
    print(f"\nServer is running on {base_url} - Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    test_dashboard()
