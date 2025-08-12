#!/usr/bin/env python3
"""
Debug script to test custom scraping functionality
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scheduler import SchedulerManager
from config.settings import Settings

def debug_custom_scrape():
    """Debug custom scraping to find the issue."""
    print("Testing custom scraping functionality...")
    
    # Initialize components
    settings = Settings()
    scheduler_manager = SchedulerManager(settings)
    
    # Test custom scraping
    print("\n=== Running Custom Scrape for 'iphone 16' ===")
    result = scheduler_manager.run_custom_scraping("iphone 16")
    
    print(f"Scraping result: {json.dumps(result, indent=2)}")
    
    # Check what's in the JSON file after scraping
    print("\n=== Checking JSON file contents ===")
    try:
        with open('./products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        total_products = len(data.get('products', []))
        print(f"Total products in JSON: {total_products}")
        
        # Check recent products
        recent_products = [
            p for p in data.get('products', [])
            if 'iphone 14' in p.get('title', '').lower()
        ]
        print(f"iPhone 14 products: {len(recent_products)}")
        
        if recent_products:
            print("\nSample iPhone 14 product:")
            sample = recent_products[0]
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Added at: {sample.get('added_at', 'N/A')}")
            print(f"  Source: {sample.get('source', 'N/A')}")
        
        # Check scraping sessions
        sessions = data.get('scraping_sessions', [])
        if sessions:
            print(f"\nLast scraping session:")
            last_session = sessions[-1]
            print(f"  Search query: {last_session.get('search_keywords', 'N/A')}")
            print(f"  Status: {last_session.get('status', 'N/A')}")
            print(f"  Listings found: {last_session.get('listings_found', 'N/A')}")
            print(f"  New listings: {last_session.get('new_listings', 'N/A')}")
            print(f"  Errors: {last_session.get('errors_count', 'N/A')}")
            if last_session.get('error_details'):
                print(f"  Error details: {last_session['error_details']}")
                
    except Exception as e:
        print(f"Error reading JSON file: {e}")
    
    return result.get('success', False)

if __name__ == "__main__":
    success = debug_custom_scrape()
    print(f"\n{'✅' if success else '❌'} Custom scraping {'succeeded' if success else 'failed'}")
