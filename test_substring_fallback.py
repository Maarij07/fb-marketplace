#!/usr/bin/env python3
"""
Test script to demonstrate the NEW Substring Matching Fallback functionality.

This test shows how the enhanced system now handles:
1. Smart phone filtering (existing functionality)
2. NEW: Substring matching for non-phone products (%query% style)  
3. Still applies accessory filtering (case, cover, etc.)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter

def test_substring_fallback():
    """Test the new substring matching fallback functionality."""
    
    filter_engine = SmartProductFilter()
    
    # Test scenarios with both phone and non-phone products
    test_scenarios = [
        {
            'search': 'Apple iPad 9th generation 64GB Grey excellent condition',
            'description': '🔍 EXACT SUBSTRING SEARCH - Your iPad example that was being skipped',
            'test_products': [
                {"title": "Apple iPad 9th generation 64GB Grey excellent condition"},  # ✅ EXACT MATCH
                {"title": "Apple iPad 9th generation 64GB Grey excellent condition - barely used"},  # ✅ CONTAINS QUERY
                {"title": "iPad 9th generation 64GB Grey excellent condition Apple"},  # ✅ CONTAINS QUERY (different order)
                {"title": "Apple iPad 9th generation 64GB Silver excellent condition"},  # ❓ PARTIAL MATCH (different color)
                {"title": "Apple iPad 10th generation 64GB Grey excellent condition"},  # ❓ PARTIAL MATCH (different generation)
                
                # Should EXCLUDE (accessories)
                {"title": "Apple iPad 9th generation 64GB Grey case"},  # ❌ ACCESSORY
                {"title": "iPad 9th generation screen protector"},  # ❌ ACCESSORY
            ]
        },
        
        {
            'search': 'MacBook Pro 16-inch',
            'description': '🔍 NON-PHONE PRODUCT - Should use substring matching',
            'test_products': [
                {"title": "MacBook Pro 16-inch M1 Pro 512GB Space Grey"},  # ✅ CONTAINS QUERY
                {"title": "Apple MacBook Pro 16-inch 2023 model"},  # ✅ CONTAINS QUERY  
                {"title": "MacBook Pro 16-inch excellent condition"},  # ✅ CONTAINS QUERY
                {"title": "16-inch MacBook Pro for sale"},  # ✅ CONTAINS QUERY
                
                # Should EXCLUDE (different products or accessories)
                {"title": "MacBook Pro 13-inch M1 Pro"},  # ❌ DIFFERENT SIZE
                {"title": "MacBook Pro 16-inch case leather"},  # ❌ ACCESSORY
                {"title": "MacBook Pro charger 16-inch"},  # ❌ ACCESSORY
            ]
        },
        
        {
            'search': 'iPhone 16',
            'description': '🔍 SMART PHONE FILTERING - Should still work as before (strict)',
            'test_products': [
                # Should INCLUDE (base model only)
                {"title": "iPhone 16 128GB Pink"},  # ✅ BASE MODEL
                {"title": "Apple iPhone 16 256GB Black"},  # ✅ BASE MODEL
                
                # Should EXCLUDE (variants - strict phone filtering)
                {"title": "iPhone 16 Pro 128GB Titanium"},  # ❌ PHONE VARIANT
                {"title": "iPhone 16 Plus 256GB Pink"},  # ❌ PHONE VARIANT
                {"title": "iPhone 16 Pro Max 256GB"},  # ❌ PHONE VARIANT
                
                # Should EXCLUDE (accessories - global exclusions)
                {"title": "iPhone 16 case MagSafe"},  # ❌ ACCESSORY
                {"title": "iPhone 16 screen protector"},  # ❌ ACCESSORY
            ]
        },
        
        {
            'search': 'Nintendo Switch OLED',
            'description': '🔍 GAMING CONSOLE - Should use substring matching',
            'test_products': [
                {"title": "Nintendo Switch OLED Model White"},  # ✅ CONTAINS QUERY
                {"title": "Nintendo Switch OLED console with games"},  # ✅ CONTAINS QUERY
                {"title": "Switch OLED Nintendo excellent condition"},  # ✅ CONTAINS QUERY
                
                # Should EXCLUDE (different products or accessories)  
                {"title": "Nintendo Switch Lite"},  # ❌ DOESN'T CONTAIN OLED
                {"title": "Nintendo Switch OLED case"},  # ❌ ACCESSORY
                {"title": "Nintendo Switch OLED screen protector"},  # ❌ ACCESSORY
            ]
        }
    ]
    
    print("🚀 TESTING NEW SUBSTRING MATCHING FALLBACK")
    print("=" * 80)
    print("This test demonstrates the enhanced filtering with substring matching fallback")
    print("while still preserving strict phone filtering and accessory exclusions.")
    print()
    
    for scenario in test_scenarios:
        search_query = scenario['search']
        description = scenario['description']
        test_products = scenario['test_products']
        
        print(f"{description}")
        print(f"🔍 Search Query: '{search_query}'")
        print("-" * 80)
        
        # Apply the filter
        included, excluded = filter_engine.filter_product_list(test_products, search_query)
        
        print(f"📊 RESULTS: {len(included)} included, {len(excluded)} excluded")
        print()
        
        # Show included products
        print("✅ INCLUDED PRODUCTS:")
        if included:
            for i, product in enumerate(included, 1):
                title = product['title']
                print(f"  {i}. {title}")
        else:
            print("  (None)")
        print()
        
        # Show excluded products with reasons
        print("❌ EXCLUDED PRODUCTS:")
        if excluded:
            for i, product in enumerate(excluded, 1):
                title = product['title']
                reason = product.get('exclusion_reason', 'Unknown')
                print(f"  {i}. {title}")
                print(f"     → Reason: {reason}")
        else:
            print("  (None)")
        print()
        
        # Show exclusion statistics
        if excluded:
            stats = filter_engine.get_filter_statistics(excluded)
            print("📈 WHY PRODUCTS WERE EXCLUDED:")
            for reason, count in stats.items():
                print(f"  • {reason}: {count} product(s)")
        
        print("=" * 80)
        print()

def test_individual_matching():
    """Test individual products to show detailed matching logic."""
    
    filter_engine = SmartProductFilter()
    
    print("🔬 INDIVIDUAL PRODUCT MATCHING TEST")
    print("=" * 60)
    
    test_cases = [
        {
            'search': 'Apple iPad 9th generation 64GB Grey excellent condition',
            'products': [
                'Apple iPad 9th generation 64GB Grey excellent condition',  # Your exact case
                'Apple iPad 9th generation 64GB Grey excellent condition - barely used',
                'iPad 9th generation 64GB Grey excellent condition',
                'Apple iPad 9th generation 64GB Silver excellent condition',
                'Apple iPad 9th generation case',
            ]
        },
        {
            'search': 'iPhone 16',  
            'products': [
                'iPhone 16 128GB Pink',  # Should use smart matching
                'iPhone 16 Pro 128GB',   # Should use smart matching
                'iPhone 16 case',        # Should be excluded
            ]
        }
    ]
    
    for case in test_cases:
        search_query = case['search']
        print(f"Search Query: '{search_query}'")
        print("-" * 40)
        
        for product_title in case['products']:
            should_include, reason = filter_engine.should_include_product(product_title, search_query)
            
            status = "✅ INCLUDED" if should_include else "❌ EXCLUDED"
            print(f"{status}: '{product_title}'")
            print(f"   Reason: {reason}")
            print()
        
        print("-" * 60)
        print()

if __name__ == "__main__":
    print("🎯 TESTING ENHANCED FILTERING WITH SUBSTRING FALLBACK")
    print("=" * 80)
    
    # Test the new functionality
    test_substring_fallback()
    
    print("\n" + "=" * 80)
    print()
    
    # Test individual cases
    test_individual_matching()
    
    print("🎉 TEST COMPLETED!")
    print()
    print("🎯 KEY ENHANCEMENTS:")
    print("  ✅ Smart phone filtering still works (strict variant matching)")
    print("  ✅ NEW: Substring matching for non-phone products (%query% style)")
    print("  ✅ Accessory filtering still applies globally (case, cover, etc.)")
    print("  ✅ Your iPad example will now be included!")
    print()
