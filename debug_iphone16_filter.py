#!/usr/bin/env python3
"""
DEBUG: iPhone 16 Filtering Issue
Let's test the exact products from your products.json file
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter
import json

def test_your_actual_products():
    """Test the exact products from your products.json file."""
    
    filter_engine = SmartProductFilter()
    
    search_query = "iPhone 16"
    
    # These are the actual products from your products.json
    actual_products = [
        # Product 1 from your JSON - iPhone 16 Pro
        {
            "id": "deep_1318213633035780",
            "title": "AU$1,800\niPhone 16 pro 256gb\nSydney, NSW"
        },
        
        # Product 2 from your JSON - iPhone 16 Pro Max
        {
            "id": "deep_1521339592373358", 
            "title": "AU$1,500\niPhone 16 Pro Max\nSydney, NSW"
        },
        
        # Let's also test what SHOULD be included
        {
            "id": "test_base_1",
            "title": "iPhone 16 128GB Black"
        },
        
        {
            "id": "test_base_2", 
            "title": "Apple iPhone 16 256GB Blue"
        }
    ]
    
    print("🔍 DEBUGGING: Your Actual iPhone 16 Filter Issue")
    print("=" * 70)
    print(f"Search Query: '{search_query}'")
    print(f"Testing {len(actual_products)} products from your JSON file...")
    print()
    
    # Test each product individually to see detailed parsing
    for i, product in enumerate(actual_products, 1):
        title = product['title']
        print(f"🔸 Product {i}: {title}")
        
        # Parse the target search
        target_info = filter_engine._parse_phone_model(search_query.lower())
        print(f"   Target parsed: {target_info}")
        
        # Parse the product title 
        product_info = filter_engine._parse_phone_model(title.lower())
        print(f"   Product parsed: {product_info}")
        
        # Test the filtering
        should_include, reason = filter_engine.should_include_product(title, search_query)
        
        if should_include:
            print(f"   ✅ RESULT: INCLUDED - {reason}")
        else:
            print(f"   ❌ RESULT: EXCLUDED - {reason}")
        print()
    
    print("=" * 70)
    
    # Now test with the batch filter method
    print("🧪 BATCH FILTERING TEST:")
    included, excluded = filter_engine.filter_product_list(actual_products, search_query)
    
    print(f"📊 RESULTS: {len(included)} INCLUDED, {len(excluded)} EXCLUDED")
    print()
    
    print("✅ INCLUDED PRODUCTS:")
    for product in included:
        print(f"  - {product['title']}")
    print()
    
    print("❌ EXCLUDED PRODUCTS:")
    for product in excluded:
        print(f"  - {product['title']}")
        print(f"    Reason: {product.get('exclusion_reason', 'Unknown')}")
    print()
    
    # Analysis
    pro_products = [p for p in actual_products if 'pro' in p['title'].lower()]
    base_products = [p for p in actual_products if 'pro' not in p['title'].lower()]
    
    print("🎯 ANALYSIS:")
    print(f"Total Pro variants tested: {len(pro_products)}")
    print(f"Total base iPhone 16 tested: {len(base_products)}")
    
    pro_included = len([p for p in included if 'pro' in p['title'].lower()])
    base_included = len([p for p in included if 'pro' not in p['title'].lower()])
    
    print(f"Pro variants included: {pro_included} (should be 0)")
    print(f"Base iPhone 16 included: {base_included} (should be {len(base_products)})")
    
    if pro_included > 0:
        print(f"\n❌ PROBLEM FOUND! Pro variants are being included when searching for 'iPhone 16'")
        print("The filter is not working correctly!")
        return False
    else:
        print(f"\n✅ Filter working correctly! Pro variants excluded, base models included.")
        return True

def test_iphone_pattern_directly():
    """Test the iPhone pattern directly."""
    print("\n🔬 DIRECT PATTERN TESTING:")
    print("=" * 50)
    
    import re
    
    # The actual iPhone pattern from the code
    iphone_pattern = r'iphone\s*(\d+)(\s*(pro\s*max|pro\s*plus|pro|plus\s*max|plus|max|mini|se|c|s))?'
    
    test_titles = [
        "iPhone 16",
        "iPhone 16 pro 256gb", 
        "iPhone 16 Pro Max",
        "AU$1,800 iPhone 16 pro 256gb Sydney, NSW",
        "AU$1,500 iPhone 16 Pro Max Sydney, NSW"
    ]
    
    for title in test_titles:
        match = re.search(iphone_pattern, title.lower())
        if match:
            print(f"Title: '{title}'")
            print(f"  Model: {match.group(1)}")
            print(f"  Variant: '{match.group(3) if match.group(3) else ''}'")
            print(f"  Groups: {match.groups()}")
        else:
            print(f"Title: '{title}' - NO MATCH")
        print()

if __name__ == "__main__":
    # Test your actual products
    success = test_your_actual_products()
    
    # Test the pattern directly
    test_iphone_pattern_directly()
    
    if not success:
        print("\n🚨 The filter needs to be debugged!")
        print("iPhone 16 Pro variants are being included when they should be excluded.")
    else:
        print("\n✅ Filter appears to be working correctly in this test!")
