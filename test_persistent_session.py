#!/usr/bin/env python3
"""
Test script for persistent session scraping
Demonstrates the new functionality where Chrome stays open between searches
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scraper import FacebookMarketplaceScraper
from config.settings import Settings

def test_persistent_session():
    """Test the persistent session functionality."""
    print("🚀 Testing Persistent Session Feature")
    print("=" * 50)
    
    # Initialize settings
    settings = Settings()
    
    # Create scraper with persistent session enabled
    scraper = FacebookMarketplaceScraper(settings, persistent_session=True)
    
    try:
        print("\n1️⃣ Initializing session (login + navigate to marketplace)...")
        if not scraper.initialize_session():
            print("❌ Failed to initialize session")
            return False
        
        print("✅ Session initialized! Chrome is now open and logged in to Facebook Marketplace")
        
        # Test multiple quick searches
        search_queries = ["iphone 12", "iphone 13", "samsung s24"]
        
        for i, query in enumerate(search_queries, 2):
            print(f"\n{i}️⃣ Quick search for: '{query}'")
            print("   (Using existing session - no need to login again!)")
            
            results = scraper.quick_search(query)
            
            if results:
                print(f"   ✅ Found {len(results)} listings for '{query}'")
                # Show sample results
                for j, listing in enumerate(results[:2], 1):
                    title = listing.get('title', 'NO TITLE')[:40]
                    price = listing.get('price', {}).get('amount', 'N/A')
                    currency = listing.get('price', {}).get('currency', '')
                    print(f"      {j}. {title}... - {price} {currency}")
            else:
                print(f"   ⚠️  No listings found for '{query}'")
        
        print(f"\n🎉 Persistent session test completed!")
        print("Chrome window should still be open on Facebook Marketplace")
        print("You can manually search for other products in that same window")
        
        # Ask user if they want to close the session
        try:
            print(f"\n⏸️  Press Enter to close the session or Ctrl+C to keep it open...")
            input()
            scraper.close_session()
            print("✅ Session closed")
        except KeyboardInterrupt:
            print(f"\n📌 Session kept open! You can continue using the Chrome window.")
            print("The browser will close when the script ends.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup if user didn't choose to keep it open
        if hasattr(scraper, 'driver') and scraper.driver:
            try:
                scraper.close_session()
            except:
                pass

def show_instructions():
    """Show usage instructions for the persistent session feature."""
    print("\n📋 How to use Persistent Session:")
    print("-" * 40)
    print("1. Initialize session once (login + navigate to marketplace)")
    print("2. Use quick_search() multiple times with different queries")
    print("3. Chrome stays open between searches - much faster!")
    print("4. Close session when done")
    print("\nExample usage:")
    print("""
from core.scraper import FacebookMarketplaceScraper
from config.settings import Settings

settings = Settings()
scraper = FacebookMarketplaceScraper(settings, persistent_session=True)

# Initialize once
scraper.initialize_session()

# Search multiple times - fast!
scraper.quick_search("iphone 12")
scraper.quick_search("iphone 13") 
scraper.quick_search("samsung")

# Close when done
scraper.close_session()
    """)

if __name__ == "__main__":
    print("🔧 Facebook Marketplace Persistent Session Test")
    print("This test will keep Chrome open between multiple searches")
    print("making it much faster to search for different products!")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_instructions()
    else:
        success = test_persistent_session()
        if success:
            print("\n✅ Persistent session feature is working!")
        else:
            print("\n❌ Persistent session test failed")
        
        sys.exit(0 if success else 1)
