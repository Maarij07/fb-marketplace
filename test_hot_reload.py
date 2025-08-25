#!/usr/bin/env python3
"""
Test Hot Reload Functionality

This script tests the hot reload mechanism to ensure products are saved immediately
and appear in recent listings.
"""

import time
from datetime import datetime
from core.json_manager import JSONDataManager

def test_hot_reload():
    """Test the hot reload functionality."""
    print("🔥 Testing Hot Reload Functionality")
    print("=" * 50)
    
    # Initialize JSON manager
    json_manager = JSONDataManager()
    
    # Get current product count
    initial_products = json_manager.get_recent_products(10)
    print(f"📋 Initial product count: {len(initial_products)}")
    
    # Create test product
    test_product = {
        'title': f'🔥 Hot Reload Test Product - {datetime.now().strftime("%H:%M:%S")}',
        'price': {
            'amount': '1337',
            'currency': 'SEK',
            'raw_value': '1337 kr'
        },
        'location': {
            'city': 'Stockholm',
            'distance': 'Test',
            'raw_location': 'Stockholm Test Area'
        },
        'marketplace_url': f'https://facebook.com/marketplace/item/test{int(time.time())}',
        'seller': {
            'info': 'Hot Reload Test Seller',
            'profile': None
        },
        'product_details': {
            'model': 'Test iPhone',
            'storage': '128GB',
            'condition': 'New',
            'color': 'Hot Reload Red'
        },
        'images': [],
        'extraction_method': 'hot_reload_test',
        'data_quality': 'test',
        'source': 'hot_reload_test'
    }
    
    print(f"📦 Creating test product: {test_product['title']}")
    
    # Test hot reload save
    success = json_manager.add_product_hot_reload(test_product)
    
    if success:
        print("✅ Hot reload save successful!")
    else:
        print("❌ Hot reload save failed!")
        return False
    
    # Wait a moment
    time.sleep(0.5)
    
    # Get recent products to verify
    updated_products = json_manager.get_recent_products(10)
    print(f"📋 Updated product count: {len(updated_products)}")
    
    # Check if our test product is at the top
    if updated_products and updated_products[0]['title'] == test_product['title']:
        print("✅ Hot reload verified! Test product appears at the top of recent listings")
        print(f"🏷️  Product ID: {updated_products[0].get('id')}")
        print(f"🕒 Added at: {updated_products[0].get('added_at')}")
        print(f"🔥 Hot reload timestamp: {updated_products[0].get('hot_reload_timestamp')}")
        return True
    else:
        print("❌ Hot reload verification failed! Test product not found at the top")
        if updated_products:
            print(f"   Top product is: {updated_products[0]['title']}")
        return False

if __name__ == '__main__':
    success = test_hot_reload()
    if success:
        print("\n🎉 Hot reload functionality is working correctly!")
    else:
        print("\n💥 Hot reload functionality needs fixing!")
