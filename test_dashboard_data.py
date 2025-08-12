#!/usr/bin/env python3
"""
Test script to verify dashboard data loading and formatting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.json_manager import JSONDataManager

def test_data_loading():
    """Test loading and formatting of product data."""
    print("Testing dashboard data loading...")
    
    # Initialize JSON manager
    json_manager = JSONDataManager()
    
    # Get system stats
    print("\n=== System Statistics ===")
    stats = json_manager.get_system_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Get recent products
    print("\n=== Recent Products ===")
    products = json_manager.get_recent_products(limit=5)
    print(f"Found {len(products)} products")
    
    if products:
        for i, product in enumerate(products[:3], 1):
            print(f"\nProduct {i}:")
            print(f"  Title: {product.get('title', 'N/A')}")
            print(f"  Price: {product.get('price', {}).get('amount', 'N/A')} {product.get('price', {}).get('currency', 'N/A')}")
            print(f"  Location: {product.get('location', {}).get('city', 'N/A')}")
            print(f"  Seller: {product.get('seller_name', 'N/A')}")
            print(f"  Added at: {product.get('added_at', 'N/A')}")
            print(f"  Created at: {product.get('created_at', 'N/A')}")
    else:
        print("No products found!")
    
    return len(products) > 0

if __name__ == "__main__":
    success = test_data_loading()
    if success:
        print("\n✅ Test passed - Products are available for dashboard")
    else:
        print("\n❌ Test failed - No products found")
    
    sys.exit(0 if success else 1)
