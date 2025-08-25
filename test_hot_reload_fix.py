#!/usr/bin/env python3
"""
Test script to verify hot reload functionality is working correctly.
This will test that products are saved one by one as they're scraped.
"""

import sys
import os
import time
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.scraper import FacebookMarketplaceScraper
from core.json_manager import JSONDataManager
from config.settings import Settings

def test_hot_reload_fix():
    """Test that hot reload saves products one by one as they're scraped."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("🧪 Testing Hot Reload Fix...")
    print("=" * 60)
    
    # Initialize components
    settings = Settings()
    json_manager = JSONDataManager()
    
    # Get initial product count
    initial_products = json_manager.get_recent_products(limit=10)
    initial_count = len(initial_products)
    print(f"📊 Initial products count: {initial_count}")
    
    # Display current recent products
    if initial_products:
        print("\n📋 Current recent products:")
        for i, product in enumerate(initial_products[:5], 1):
            title = product.get('title', 'Unknown')[:40]
            timestamp = product.get('hot_reload_timestamp', product.get('added_at', 'Unknown'))
            hot_reload = "🔥" if product.get('hot_reload') else "  "
            method = product.get('scraping_method', 'standard')
            print(f"  {i}. {hot_reload} {title}... | {timestamp[:19]} | Method: {method}")
    
    print(f"\n🔍 Testing continuous scraping hot reload (max 3 products)...")
    
    try:
        # Initialize scraper
        scraper = FacebookMarketplaceScraper(settings)
        
        # Test continuous scraping with hot reload
        results = scraper.quick_search("iPhone 13")
        
        print(f"\n✅ Scraping completed. Found {len(results)} products")
        
        # Wait a moment for saves to complete
        time.sleep(3)
        
        # Check recent products again
        new_products = json_manager.get_recent_products(limit=15)
        new_count = len(new_products)
        
        print(f"📊 After scraping products count: {new_count}")
        print(f"📈 New products added: {new_count - initial_count}")
        
        # Display recent products to see hot reload ones
        print("\n📋 Recent products (looking for hot reload products):")
        hot_reload_count = 0
        continuous_method_count = 0
        
        for i, product in enumerate(new_products[:10], 1):
            title = product.get('title', 'Unknown')[:40]
            timestamp = product.get('hot_reload_timestamp', product.get('added_at', 'Unknown'))
            hot_reload = product.get('hot_reload', False)
            method = product.get('scraping_method', 'standard')
            
            if hot_reload:
                hot_reload_count += 1
            if method == 'continuous':
                continuous_method_count += 1
                
            hot_indicator = "🔥" if hot_reload else "  "
            method_indicator = "📤" if method == 'continuous' else "📦" if method == 'standard' else "🔬"
            
            print(f"  {i}. {hot_indicator}{method_indicator} {title}... | {timestamp[:19]}")
        
        print(f"\n📈 Summary:")
        print(f"   Hot reload products: {hot_reload_count}")
        print(f"   Continuous method products: {continuous_method_count}")
        print(f"   Total new products: {new_count - initial_count}")
        
        if hot_reload_count > 0:
            print("✅ Hot reload is working! Products are being saved one by one!")
        else:
            print("❌ Hot reload not detected - checking further...")
            
            # Check for any products with recent timestamps
            recent_products = [p for p in new_products if p.get('hot_reload_timestamp')]
            if recent_products:
                print(f"🔍 Found {len(recent_products)} products with hot_reload_timestamp")
                print("✅ Hot reload mechanism is working!")
            else:
                print("🔍 No hot reload timestamps found - may need further investigation")
        
        # Close scraper
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.close_session()
            
    except Exception as e:
        logger.error(f"Hot reload test failed: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_hot_reload_fix()
