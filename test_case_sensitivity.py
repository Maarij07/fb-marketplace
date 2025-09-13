#!/usr/bin/env python3
"""
Test to verify the case sensitivity issue with iPad search
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter

def test_ipad_case_sensitivity():
    """Test the exact iPad case sensitivity issue."""
    
    filter_engine = SmartProductFilter()
    
    # Your EXACT search with capital IPad
    search_query = "Apple IPad 9th generation 64GB Grey excellent condition"
    
    test_products = [
        # The product you want to find (exact match but different case)
        "Apple iPad 9th generation 64GB Grey excellent condition",  # lowercase iPad
        "Apple IPad 9th generation 64GB Grey excellent condition",  # uppercase IPad (matches search)
        
        # The Cabramatta product that was being included incorrectly
        "Apple iPad 9th-64g. Wifi only. Pick up Cabramatta",
    ]
    
    print("🔍 CASE SENSITIVITY TEST")
    print("=" * 80)
    print(f"Search Query: '{search_query}'")
    print(f"Note: Search has 'IPad' with capital P")
    print()
    
    for i, product_title in enumerate(test_products, 1):
        # Direct test of the substring match
        search_lower = search_query.lower()
        product_lower = product_title.lower()
        
        print(f"{i}. Product: '{product_title}'")
        print(f"   Search (lowercase): '{search_lower}'")
        print(f"   Product (lowercase): '{product_lower}'")
        print(f"   Is search in product? {search_lower in product_lower}")
        
        # Now test with the filter
        should_include, reason = filter_engine.should_include_product(product_title, search_query)
        
        status = "✅ INCLUDED" if should_include else "❌ EXCLUDED"
        print(f"   Filter Result: {status}")
        print(f"   Reason: {reason}")
        print()

if __name__ == "__main__":
    test_ipad_case_sensitivity()
    
    print("\n🎯 ANALYSIS:")
    print("The substring match IS case-insensitive (using .lower())")
    print("So 'Apple IPad' (capital P) WILL match 'Apple iPad' (lowercase p)")
    print()
    print("This means:")
    print("✅ 'Apple iPad 9th generation 64GB Grey excellent condition' WILL be included")
    print("❌ 'Apple iPad 9th-64g. Wifi only. Pick up Cabramatta' will NOT be included")
    print("   (because the full search string is not found in the Cabramatta product)")
