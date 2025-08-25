#!/usr/bin/env python3
"""
Test hot reload save functionality with a simulated scraped product.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.json_manager import JSONDataManager
from datetime import datetime
import json

def test_hot_reload_save():
    """Test hot reload save with a simulated deep scraped product."""
    
    json_manager = JSONDataManager()
    
    print("🧪 Testing Hot Reload Save Function...")
    print("=" * 50)
    
    # Get initial count
    initial_products = json_manager.get_recent_products(limit=3)
    initial_count = len(initial_products)
    print(f"📊 Initial products count: {initial_count}")
    
    # Create a realistic deep scraped product structure
    simulated_deep_product = {
        'basic_info': {
            'title': 'iPhone 11 Pro Max - TEST Hot Reload Deep Scraping',
            'product_id': 'test_123456789',
            'url': 'https://facebook.com/marketplace/item/123456789',
            'price': {
                'amount': '4500',
                'currency': 'SEK',
                'raw_price_text': 'SEK4,500'
            },
            'location': {
                'city': 'Stockholm',
                'area': 'Södermalm'
            }
        },
        'seller_details': {
            'seller_name': 'Test Seller Deep',
            'profile_url': 'https://facebook.com/test.seller'
        },
        'product_comprehensive': {
            'model_name': 'iPhone 11 Pro Max',
            'storage': '128GB',
            'condition': 'Good',
            'color': 'Space Gray',
            'images': [
                'https://example.com/image1.jpg',
                'https://example.com/image2.jpg'
            ]
        },
        'marketplace_metadata': {
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_method': 'deep_scraping_test'
        }
    }
    
    print(f"📦 Simulating deep scraped product: {simulated_deep_product['basic_info']['title'][:50]}...")
    
    # Convert to standard format (simulate the scraper's conversion)
    def convert_to_standard_format(deep_data):
        """Convert deep scraped data to standard format (simulating scraper behavior)."""
        basic_info = deep_data.get('basic_info', {})
        seller_details = deep_data.get('seller_details', {})
        product_comp = deep_data.get('product_comprehensive', {})
        
        return {
            'id': f"deep_{basic_info.get('product_id', 'test_id')}",
            'title': basic_info.get('title', 'Unknown'),
            'price': {
                'amount': basic_info.get('price', {}).get('amount', '0'),
                'currency': basic_info.get('price', {}).get('currency', 'SEK'),
                'raw_value': basic_info.get('price', {}).get('raw_price_text', 'N/A')
            },
            'location': basic_info.get('location', {}),
            'marketplace_url': basic_info.get('url', ''),
            'seller': {
                'info': seller_details.get('seller_name', 'Private Seller'),
                'profile': seller_details.get('profile_url')
            },
            'product_details': {
                'model': product_comp.get('model_name', 'Unknown'),
                'storage': product_comp.get('storage', 'Unknown'),
                'condition': product_comp.get('condition', 'Unknown'),
                'color': product_comp.get('color', 'Unknown')
            },
            'images': product_comp.get('images', [])[:3],
            'extraction_method': 'deep_scraper',
            'data_quality': 'comprehensive',
            'added_at': datetime.now().isoformat(),
            'source': 'deep_marketplace_scraper',
            'hot_reload_timestamp': datetime.now().isoformat(),
            'scraping_status': 'completed',
            'scraping_method': 'deep'
        }
    
    # Convert the deep data to standard format
    standard_product = convert_to_standard_format(simulated_deep_product)
    
    print("🔥 Testing hot reload save...")
    
    # Test the hot reload save function
    success = json_manager.add_product_hot_reload(standard_product)
    
    if success:
        print("✅ Hot reload save successful!")
    else:
        print("❌ Hot reload save failed!")
        return
    
    # Check if the product appears in recent listings
    new_products = json_manager.get_recent_products(limit=5)
    new_count = len(new_products)
    
    print(f"📊 After save products count: {new_count}")
    print(f"📈 New products added: {new_count - initial_count}")
    
    print("\n📋 Recent products after hot reload save:")
    for i, product in enumerate(new_products[:3], 1):
        title = product.get('title', 'Unknown')[:50]
        timestamp = product.get('added_at', 'Unknown')
        hot_reload = product.get('hot_reload', False)
        method = product.get('scraping_method', 'standard')
        
        hot_indicator = "🔥" if hot_reload else "  "
        method_indicator = "🔬" if method == 'deep' else "📦"
        
        print(f"  {i}. {hot_indicator}{method_indicator} {title}... | {timestamp}")
    
    # Verify the hot reload product is at the top
    if new_products and new_products[0].get('hot_reload') and 'TEST Hot Reload' in new_products[0].get('title', ''):
        print("\n✅ SUCCESS: Hot reload product appears at top of recent listings!")
        print("🔥 Hot reload functionality is working correctly!")
        
        # Show the full product details
        print(f"\n📱 Saved Product Details:")
        saved_product = new_products[0]
        print(f"   Title: {saved_product.get('title')}")
        print(f"   Price: {saved_product.get('price', {}).get('amount')} {saved_product.get('price', {}).get('currency')}")
        print(f"   Method: {saved_product.get('scraping_method')}")
        print(f"   Hot Reload: {saved_product.get('hot_reload')}")
        print(f"   Timestamp: {saved_product.get('hot_reload_timestamp')}")
        
    else:
        print("\n❌ ISSUE: Hot reload product not found at top of recent listings")
        print("🔍 Let me check what went wrong...")
        
        if new_products:
            first_product = new_products[0]
            print(f"   First product: {first_product.get('title', 'Unknown')[:50]}...")
            print(f"   Hot reload flag: {first_product.get('hot_reload', False)}")

if __name__ == "__main__":
    test_hot_reload_save()
