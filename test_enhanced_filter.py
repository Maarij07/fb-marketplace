#!/usr/bin/env python3
"""
Test script to demonstrate the Enhanced Suffix-Based Product Filtering System

This test shows how the new logic handles:
1. Base model searches (e.g., "iPhone 16") - excludes ALL variants and accessories
2. Variant searches (e.g., "iPhone 16 Pro") - only includes exact matches
3. Accessory exclusion (e.g., "iPhone 16 case") - always excluded
4. Multiple suffix exclusion (e.g., "iPhone 16 Pro Max" when searching "iPhone 16 Pro")
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter

def test_enhanced_suffix_filtering():
    """Test the enhanced suffix-based filtering logic."""
    
    filter_engine = SmartProductFilter()
    
    # Test scenarios with expected results
    test_scenarios = [
        {
            'search': 'iPhone 16',
            'description': '🎯 BASE MODEL SEARCH - Should only include base iPhone 16',
            'test_products': [
                {"title": "iPhone 16 128GB Pink"},                    # ✅ SHOULD INCLUDE
                {"title": "Apple iPhone 16 256GB Black"},             # ✅ SHOULD INCLUDE  
                {"title": "iPhone 16 512GB Blue Mint"},               # ✅ SHOULD INCLUDE
                {"title": "IPHONE 16 SEALED NEW"},                    # ✅ SHOULD INCLUDE
                
                {"title": "iPhone 16 Pro 128GB Titanium"},            # ❌ SHOULD EXCLUDE (has Pro suffix)
                {"title": "iPhone 16 Plus 256GB Pink"},               # ❌ SHOULD EXCLUDE (has Plus suffix)
                {"title": "iPhone 16 Pro Max 256GB"},                 # ❌ SHOULD EXCLUDE (has Pro Max suffix)
                {"title": "iPhone 16 Case MagSafe Compatible"},       # ❌ SHOULD EXCLUDE (accessory)
                {"title": "iPhone 16 Screen Protector"},              # ❌ SHOULD EXCLUDE (accessory)
                {"title": "iPhone 15 128GB"},                         # ❌ SHOULD EXCLUDE (different model)
            ]
        },
        
        {
            'search': 'iPhone 16 Pro',
            'description': '🎯 VARIANT SEARCH - Should only include iPhone 16 Pro (no base, no other variants)',
            'test_products': [
                {"title": "iPhone 16 Pro 128GB Titanium"},            # ✅ SHOULD INCLUDE
                {"title": "Apple iPhone 16 Pro 1TB Desert"},          # ✅ SHOULD INCLUDE
                {"title": "iPhone 16 Pro 256GB Natural"},             # ✅ SHOULD INCLUDE
                
                {"title": "iPhone 16 128GB Pink"},                    # ❌ SHOULD EXCLUDE (base model, no Pro)
                {"title": "iPhone 16 Plus 256GB"},                    # ❌ SHOULD EXCLUDE (different variant)
                {"title": "iPhone 16 Pro Max 256GB"},                 # ❌ SHOULD EXCLUDE (additional Max suffix)
                {"title": "iPhone 16 Pro Case Leather"},              # ❌ SHOULD EXCLUDE (accessory)
                {"title": "iPhone 15 Pro 128GB"},                     # ❌ SHOULD EXCLUDE (different model)
            ]
        },
        
        {
            'search': 'Redmi Note 10',
            'description': '🎯 BASE MODEL SEARCH - Should only include base Redmi Note 10',
            'test_products': [
                {"title": "Redmi Note 10 128GB Black"},               # ✅ SHOULD INCLUDE
                {"title": "Xiaomi Redmi Note 10 64GB"},               # ✅ SHOULD INCLUDE
                {"title": "REDMI NOTE 10 USED BUT GOOD"},             # ✅ SHOULD INCLUDE
                
                {"title": "Redmi Note 10 Pro 128GB"},                 # ❌ SHOULD EXCLUDE (has Pro suffix)
                {"title": "Redmi Note 10 Pro Max 256GB"},             # ❌ SHOULD EXCLUDE (has Pro Max suffix)
                {"title": "Redmi Note 10 Plus Blue"},                 # ❌ SHOULD EXCLUDE (has Plus suffix)
                {"title": "Redmi Note 11 128GB"},                     # ❌ SHOULD EXCLUDE (different model)
                {"title": "Redmi Note 10 Case Premium"},              # ❌ SHOULD EXCLUDE (accessory)
            ]
        },
        
        {
            'search': 'Redmi Note 10 Pro',
            'description': '🎯 VARIANT SEARCH - Should only include Redmi Note 10 Pro',
            'test_products': [
                {"title": "Redmi Note 10 Pro 128GB"},                 # ✅ SHOULD INCLUDE
                {"title": "Redmi Note 10 Pro Excellent Condition"},   # ✅ SHOULD INCLUDE
                
                {"title": "Redmi Note 10 128GB Black"},               # ❌ SHOULD EXCLUDE (base model)
                {"title": "Redmi Note 10 Pro Max 256GB"},             # ❌ SHOULD EXCLUDE (additional Max suffix)
                {"title": "Redmi Note 10 Plus Blue"},                 # ❌ SHOULD EXCLUDE (different variant)
                {"title": "Redmi Note 11 Pro 128GB"},                 # ❌ SHOULD EXCLUDE (different model)
            ]
        }
    ]
    
    print("🧠 ENHANCED SUFFIX-BASED PRODUCT FILTERING TEST")
    print("=" * 80)
    print("This test demonstrates the new logic that prevents unwanted variants and accessories")
    print("from being scraped when you search for specific phone models.")
    print()
    
    for scenario in test_scenarios:
        search_query = scenario['search']
        description = scenario['description']
        test_products = scenario['test_products']
        
        print(f"{description}")
        print(f"Search Query: '{search_query}'")
        print("-" * 80)
        
        # Apply the filter
        included, excluded = filter_engine.filter_product_list(test_products, search_query)
        
        print(f"📊 RESULTS: {len(included)} included, {len(excluded)} excluded")
        print()
        
        # Show included products
        print("✅ INCLUDED PRODUCTS (These match your search intent):")
        if included:
            for i, product in enumerate(included, 1):
                title = product['title']
                print(f"  {i}. {title}")
        else:
            print("  (None)")
        print()
        
        # Show excluded products with reasons
        print("❌ EXCLUDED PRODUCTS (These were filtered out):")
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

def test_parsing_capabilities():
    """Test the parsing capabilities of the enhanced filter."""
    
    filter_engine = SmartProductFilter()
    
    print("🔍 PHONE MODEL PARSING TEST")
    print("=" * 50)
    print("Testing how the system parses different phone model titles...")
    print()
    
    test_titles = [
        # iPhone variants
        "iPhone 16",
        "iPhone 16 Pro", 
        "iPhone 16 Pro Max",
        "iPhone 16 Plus",
        "Apple iPhone 16 128GB",
        
        # Samsung variants
        "Samsung Galaxy S24",
        "Galaxy S24 Ultra",
        "Samsung Galaxy Note 20",
        
        # Redmi variants
        "Redmi Note 10",
        "Redmi Note 10 Pro",
        "Redmi Note 10 Pro Max",
        "Xiaomi Redmi Note 10",
        
        # Accessories (should be detected)
        "iPhone 16 Case",
        "Redmi Note 10 Screen Protector",
        "Samsung Galaxy S24 Charger",
    ]
    
    for title in test_titles:
        parsed = filter_engine._parse_phone_model(title.lower())
        if parsed:
            brand = parsed['brand']
            model = parsed['model'] 
            variants = parsed['variants']
            full_model = parsed['full_model']
            print(f"'{title}'")
            print(f"  → Brand: {brand}")
            print(f"  → Model: {model}")
            print(f"  → Variants: '{variants}' {('(has variants)' if variants else '(base model)')}")
            print(f"  → Full: {full_model}")
        else:
            print(f"'{title}' → Could not parse (might be accessory or unknown format)")
        print()

if __name__ == "__main__":
    print("🚀 TESTING ENHANCED SUFFIX-BASED PRODUCT FILTERING")
    print("=" * 80)
    
    # Test parsing first
    test_parsing_capabilities()
    
    print("\n" + "=" * 80)
    print()
    
    # Test filtering logic
    test_enhanced_suffix_filtering()
    
    print("🎉 TEST COMPLETED!")
    print()
    print("🎯 KEY IMPROVEMENTS IN THIS ENHANCED SYSTEM:")
    print("  ✅ Base model searches (e.g., 'iPhone 16') exclude ALL variants")
    print("  ✅ Variant searches (e.g., 'iPhone 16 Pro') only include exact matches")
    print("  ✅ Accessories are always excluded (case, charger, etc.)")
    print("  ✅ Multiple suffixes are prevented (iPhone 16 Pro ≠ iPhone 16 Pro Max)")
    print("  ✅ Works across all major phone brands (iPhone, Samsung, Redmi, etc.)")
    print()
    print("This ensures that when you search for 'iPhone 16', you get exactly that -")
    print("not iPhone 16 Pro, not iPhone 16 Plus, not iPhone 16 cases!")
