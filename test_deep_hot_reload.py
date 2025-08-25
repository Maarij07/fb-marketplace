#!/usr/bin/env python3
"""
Test script to verify hot reload functionality during deep scraping.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.scraper import FacebookMarketplaceScraper
from core.json_manager import JSONDataManager
import time
import logging

def test_deep_hot_reload():
    """Test hot reload functionality during a small deep scraping session."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize scraper and JSON manager
    from config.settings import Settings
    settings = Settings()
    scraper = FacebookMarketplaceScraper(settings)
    json_manager = JSONDataManager()
    
    print("🧪 Testing Deep Scraping Hot Reload...")
    print("=" * 50)
    
    # Get initial product count
    initial_products = json_manager.get_recent_products(limit=5)
    initial_count = len(initial_products)
    print(f"📊 Initial products count: {initial_count}")
    
    # Display current recent products
    if initial_products:
        print("\n📋 Current recent products:")
        for i, product in enumerate(initial_products[:3], 1):
            title = product.get('title', 'Unknown')[:40]
            timestamp = product.get('added_at', 'Unknown')
            hot_reload = product.get('hot_reload', False)
            method = product.get('scraping_method', 'standard')
            print(f"  {i}. {title}... | {timestamp} | Hot: {hot_reload} | Method: {method}")
    
    print("\n🔍 Starting deep scrape test (max 2 products)...")
    
    try:
        # Run a small deep scrape
        deep_results = scraper.deep_scrape_marketplace("iPhone 11", max_products=2)
        
        print(f"\n✅ Deep scrape completed. Found {len(deep_results)} products")
        
        # Wait a moment for saves to complete
        time.sleep(2)
        
        # Check recent products again
        new_products = json_manager.get_recent_products(limit=10)
        new_count = len(new_products)
        
        print(f"📊 After scraping products count: {new_count}")
        print(f"📈 New products added: {new_count - initial_count}")
        
        # Display recent products to see hot reload ones
        print("\n📋 Recent products (looking for hot reload products):")
        hot_reload_count = 0
        deep_method_count = 0
        
        for i, product in enumerate(new_products[:8], 1):
            title = product.get('title', 'Unknown')[:40]
            timestamp = product.get('added_at', 'Unknown')
            hot_reload = product.get('hot_reload', False)
            method = product.get('scraping_method', 'standard')
            
            if hot_reload:
                hot_reload_count += 1
            if method == 'deep':
                deep_method_count += 1
                
            hot_indicator = "🔥" if hot_reload else "  "
            method_indicator = "🔬" if method == 'deep' else "📦"
            
            print(f"  {i}. {hot_indicator}{method_indicator} {title}... | {timestamp}")
        
        print(f"\n📈 Summary:")
        print(f"   Hot reload products: {hot_reload_count}")
        print(f"   Deep method products: {deep_method_count}")
        print(f"   Total new products: {new_count - initial_count}")
        
        if hot_reload_count > 0:
            print("✅ Hot reload is working for deep scraping!")
        else:
            print("❌ Hot reload not detected - investigating...")
            
            # Check for any products with deep method
            if deep_method_count > 0:
                print("🔍 Found deep products but no hot reload flag - checking recent log...")
            else:
                print("🔍 No deep products found - checking if scraping succeeded...")
        
    except Exception as e:
        logger.error(f"Deep scrape test failed: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_deep_hot_reload()
