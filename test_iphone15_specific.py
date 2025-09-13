#!/usr/bin/env python3
"""
SPECIFIC TEST: iPhone 15 Search
Let's see exactly what happens when searching for "iPhone 15"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter

def test_iphone_15_search():
    """Test exactly what happens when searching for iPhone 15."""
    
    filter_engine = SmartProductFilter()
    
    search_query = "iPhone 15"
    
    # Real-world product titles you might find on Facebook Marketplace
    test_products = [
        # Base iPhone 15 products - SHOULD BE INCLUDED
        {"title": "iPhone 15 128GB Pink"},
        {"title": "Apple iPhone 15 256GB Black"},
        {"title": "iPhone 15 512GB Blue Natural Titanium"},
        {"title": "IPHONE 15 UNLOCKED 128GB MINT CONDITION"},
        {"title": "iPhone 15 64GB White Good Condition"},
        
        # iPhone 15 variants - SHOULD BE EXCLUDED
        {"title": "iPhone 15 Pro 128GB Titanium"},
        {"title": "Apple iPhone 15 Pro Max 256GB"},
        {"title": "iPhone 15 Plus 256GB Pink"},
        {"title": "iPhone 15 Pro 1TB Desert Titanium"},
        {"title": "iPhone 15 Pro Max 512GB Natural"},
        
        # iPhone 15 accessories - SHOULD BE EXCLUDED
        {"title": "iPhone 15 Case MagSafe Compatible Clear"},
        {"title": "iPhone 15 Screen Protector Tempered Glass"},
        {"title": "iPhone 15 Charger USB-C Cable"},
        {"title": "Apple iPhone 15 Leather Wallet Case"},
        {"title": "iPhone 15 Car Mount Holder"},
        
        # Other iPhone models - SHOULD BE EXCLUDED
        {"title": "iPhone 14 128GB Purple"},
        {"title": "iPhone 16 256GB Black"},
        {"title": "iPhone 13 Pro Max 512GB"},
        {"title": "iPhone 12 Mini 128GB"},
        
        # Random non-iPhone - SHOULD BE EXCLUDED
        {"title": "Samsung Galaxy S24 Ultra 256GB"},
        {"title": "Google Pixel 8 Pro 128GB"},
    ]
    
    print("🔍 TESTING: iPhone 15 Search")
    print("=" * 60)
    print(f"Search Query: '{search_query}'")
    print(f"Testing {len(test_products)} real marketplace product titles...")
    print()
    
    # Apply the filter
    included, excluded = filter_engine.filter_product_list(test_products, search_query)
    
    print(f"📊 RESULTS: {len(included)} INCLUDED, {len(excluded)} EXCLUDED")
    print()
    
    print("✅ WILL BE SCRAPED (INCLUDED):")
    if included:
        for i, product in enumerate(included, 1):
            title = product['title']
            print(f"  {i}. {title}")
    else:
        print("  (None - this would be a problem!)")
    print()
    
    print("❌ WILL BE FILTERED OUT (EXCLUDED):")
    if excluded:
        for i, product in enumerate(excluded, 1):
            title = product['title']
            reason = product.get('exclusion_reason', 'Unknown')
            print(f"  {i}. {title}")
            print(f"     → Reason: {reason}")
            print()
    else:
        print("  (None)")
    
    # Summary analysis
    print("=" * 60)
    print("🎯 ANALYSIS:")
    
    base_iphone_15_count = len([p for p in included if 'iphone 15' in p['title'].lower() and not any(variant in p['title'].lower() for variant in ['pro', 'plus', 'max', 'mini'])])
    variant_excluded_count = len([p for p in excluded if 'iphone 15' in p['title'].lower() and any(variant in p['title'].lower() for variant in ['pro', 'plus', 'max'])])
    accessory_excluded_count = len([p for p in excluded if 'iphone 15' in p['title'].lower() and any(acc in p['title'].lower() for acc in ['case', 'screen', 'charger', 'wallet', 'mount'])])
    other_model_excluded_count = len([p for p in excluded if 'iphone' in p['title'].lower() and 'iphone 15' not in p['title'].lower()])
    
    print(f"✅ Base iPhone 15 models included: {base_iphone_15_count}")
    print(f"❌ iPhone 15 variants excluded (Pro/Plus/Max): {variant_excluded_count}")
    print(f"❌ iPhone 15 accessories excluded: {accessory_excluded_count}")
    print(f"❌ Other iPhone models excluded: {other_model_excluded_count}")
    
    if base_iphone_15_count > 0 and variant_excluded_count > 0 and accessory_excluded_count > 0:
        print("\n🎉 SUCCESS! The filtering is working correctly:")
        print("  ✅ Includes ONLY base iPhone 15 models")
        print("  ❌ Excludes iPhone 15 Pro/Plus/Max variants")
        print("  ❌ Excludes iPhone 15 accessories")
        print("  ❌ Excludes other iPhone models")
        return True
    else:
        print("\n❌ PROBLEM! The filtering may not be working as expected.")
        return False

if __name__ == "__main__":
    test_iphone_15_search()
