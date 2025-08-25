#!/usr/bin/env python3

import sys
import time
import logging
sys.path.insert(0, '.')

from core.json_manager import JSONDataManager
from core.scraper import FacebookMarketplaceScraper
from config.settings import Settings

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_save_issue():
    """Test what happens when we scrape and save products"""
    
    print("🔍 DEBUGGING SAVE ISSUE")
    print("=" * 50)
    
    # Check current state
    print("\n1. Checking current products.json state...")
    manager = JSONDataManager()
    data = manager.load_data()
    print(f"Current products in JSON: {len(data.get('products', []))}")
    
    # Test hot reload save directly
    print("\n2. Testing hot reload save directly...")
    test_product = {
        'id': 'debug_test_12345',
        'title': 'DEBUG TEST - Save Issue Investigation',
        'price': {
            'amount': '12345',
            'currency': 'SEK',
            'raw_value': '12345 SEK'
        },
        'location': {
            'city': 'Stockholm',
            'distance': 'Unknown'
        },
        'marketplace_url': 'https://facebook.com/test',
        'seller': {'info': 'Test Seller'},
        'product_details': {'model': 'Test Model'},
        'images': [],
        'source': 'debug_test'
    }
    
    success = manager.add_product_hot_reload(test_product)
    print(f"Hot reload save success: {success}")
    
    # Check if it was saved
    updated_data = manager.load_data()
    print(f"Products after hot reload save: {len(updated_data.get('products', []))}")
    
    # Find our test product
    found_test = False
    for product in updated_data.get('products', []):
        if product.get('id') == 'debug_test_12345':
            found_test = True
            break
    print(f"Test product found in JSON: {found_test}")
    
    # Test batch save behavior
    print("\n3. Testing batch save behavior...")
    test_batch = [{
        'id': 'batch_test_67890',
        'title': 'BATCH TEST - Save Issue Investigation',
        'price': {'amount': '67890', 'currency': 'SEK'},
        'location': {'city': 'Stockholm'},
        'marketplace_url': 'https://facebook.com/batch_test',
        'seller': {'info': 'Batch Test Seller'},
        'product_details': {'model': 'Batch Test Model'},
        'images': [],
    }]
    
    batch_stats = manager.add_products_batch(test_batch)
    print(f"Batch save stats: {batch_stats}")
    
    # Final check
    final_data = manager.load_data()
    print(f"Final products count: {len(final_data.get('products', []))}")
    
    print("\n4. Checking cleanup behavior...")
    # Check if cleanup is removing products
    retention_hours = 48
    original_count = len(final_data.get('products', []))
    removed_count = manager.cleanup_old_data(final_data, retention_hours)
    print(f"Products before cleanup: {original_count}")
    print(f"Products removed by cleanup: {removed_count}")
    print(f"Products after cleanup: {len(final_data.get('products', []))}")
    
    if removed_count > 0:
        print("⚠️  CLEANUP IS REMOVING PRODUCTS - This might be the issue!")
        manager.save_data(final_data)
    
    # List current products for verification
    print("\n5. Current products in JSON:")
    current_data = manager.load_data()
    for i, product in enumerate(current_data.get('products', [])[:10], 1):
        title = product.get('title', 'NO TITLE')[:50]
        added_at = product.get('added_at', 'NO TIME')
        source = product.get('source', 'NO SOURCE')
        print(f"  {i}. {title}... | {added_at} | {source}")
    
    print("\n🎯 ANALYSIS COMPLETE!")

if __name__ == "__main__":
    test_save_issue()
