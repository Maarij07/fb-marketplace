#!/usr/bin/env python3
"""
Debug Recent Scraping Activity
"""

from core.json_manager import JSONDataManager
from datetime import datetime, timedelta
import json

def debug_recent_activity():
    print("🔍 Debug: Recent Scraping Activity")
    print("=" * 50)
    
    jm = JSONDataManager()
    data = jm.load_data()
    
    products = data.get('products', [])
    sessions = data.get('scraping_sessions', [])
    
    print(f"📊 Total products: {len(products)}")
    print(f"📋 Total sessions: {len(sessions)}")
    
    # Check recent products (last 24 hours)
    now = datetime.now()
    recent_cutoff = now - timedelta(hours=24)
    
    recent_products = []
    for p in products:
        added_at_str = p.get('added_at', '')
        try:
            if 'T' in added_at_str:
                added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                if added_at.tzinfo is not None:
                    added_at = added_at.replace(tzinfo=None)
                if added_at >= recent_cutoff:
                    recent_products.append(p)
        except:
            pass
    
    print(f"\n🕒 Products added in last 24 hours: {len(recent_products)}")
    print("-" * 40)
    
    for i, p in enumerate(recent_products[:10]):
        title = p.get('title', 'NO TITLE')[:50]
        added_at = p.get('added_at', 'Unknown')[:19]
        method = p.get('extraction_method', 'unknown')
        hot_reload = '🔥' if p.get('hot_reload') else ''
        scraping_method = p.get('scraping_method', 'N/A')
        
        print(f"{i+1:2}. {hot_reload} {title}")
        print(f"    Added: {added_at}")
        print(f"    Method: {method} ({scraping_method})")
        print()
    
    # Check recent sessions
    print("\n📝 Recent scraping sessions:")
    print("-" * 40)
    
    for i, session in enumerate(sessions[-5:]):
        start_time = session.get('start_time', 'Unknown')[:19]
        status = session.get('status', 'unknown')
        listings_found = session.get('listings_found', 0)
        new_listings = session.get('new_listings', 0)
        keywords = session.get('search_keywords', 'Unknown')
        
        print(f"{i+1}. {start_time} - {keywords}")
        print(f"   Status: {status}")
        print(f"   Found: {listings_found}, New: {new_listings}")
        if session.get('error_details'):
            print(f"   Errors: {session['error_details']}")
        print()

if __name__ == '__main__':
    debug_recent_activity()
