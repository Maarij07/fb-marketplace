"""
Test script to verify that the Smart Product Filter works correctly for Redmi Note 10
and excludes variants, accessories, and other models as expected.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.product_filter import SmartProductFilter

def test_multiple_search_scenarios():
    """Test filtering for different search scenarios - base model vs variants."""
    
    filter_engine = SmartProductFilter()
    
    # Test scenarios
    scenarios = [
        {
            'search': 'Redmi Note 10',
            'description': 'Base model search - should only include base model'
        },
        {
            'search': 'Redmi Note 10 Pro',
            'description': 'Variant search - should only include Pro variant'
        },
        {
            'search': 'iPhone 16',
            'description': 'iPhone base model - should exclude Pro/Plus/etc'
        },
        {
            'search': 'iPhone 16 Pro',
            'description': 'iPhone Pro variant - should only include Pro'
        }
    ]
    
    for scenario in scenarios:
        search_query = scenario['search']
        print(f"\n🔥 Testing: {search_query} ({scenario['description']})")
        print("=" * 80)
        
        test_scenario_filtering(filter_engine, search_query)

def test_scenario_filtering(filter_engine, search_query):
    
    # Dynamic test products based on search query
    if 'redmi note 10' in search_query.lower():
        test_products = [
            # Redmi Note 10 Base Model Products
            {"title": "Redmi Note 10 128GB Black"},
            {"title": "Xiaomi Redmi Note 10 Mint Condition"},
            {"title": "Redmi Note 10 64GB White Original Box"},
            {"title": "REDMI NOTE 10 USED BUT GOOD"},
            
            # Redmi Note 10 Pro Products
            {"title": "Redmi Note 10 Pro 128GB"},
            {"title": "Redmi Note 10 Pro Max 256GB"},
            {"title": "Redmi Note 10 Pro Excellent Condition"},
            
            # Other variants
            {"title": "Redmi Note 10 Plus Blue"},
            {"title": "Redmi Note 10S 128GB"},
            
            # Other models
            {"title": "Redmi Note 11 128GB"},
            {"title": "Redmi Note 9 64GB"},
            
            # Accessories
            {"title": "Redmi Note 10 Case Premium"},
            {"title": "Redmi Note 10 Screen Protector"},
        ]
    
    elif 'iphone 16' in search_query.lower():
        test_products = [
            # iPhone 16 Base Model Products
            {"title": "iPhone 16 128GB Pink"},
            {"title": "Apple iPhone 16 256GB Black"},
            {"title": "iPhone 16 512GB Blue Mint"},
            {"title": "IPHONE 16 SEALED NEW"},
            
            # iPhone 16 Pro Products  
            {"title": "iPhone 16 Pro 128GB Titanium"},
            {"title": "iPhone 16 Pro Max 256GB"},
            {"title": "Apple iPhone 16 Pro 1TB Desert Titanium"},
            
            # iPhone 16 Plus Products
            {"title": "iPhone 16 Plus 256GB Pink"},
            {"title": "Apple iPhone 16 Plus 512GB"},
            
            # Other iPhone models
            {"title": "iPhone 15 128GB"},
            {"title": "iPhone 17 Pro (future model)"},
            {"title": "iPhone 14 Pro Max"},
            
            # iPhone accessories
            {"title": "iPhone 16 Case MagSafe Compatible"},
            {"title": "iPhone 16 Screen Protector Tempered Glass"},
            {"title": "iPhone 16 Charger USB-C"},
            
            # Different brands
            {"title": "Samsung Galaxy S24"},
            {"title": "Google Pixel 8 Pro"},
        ]
    
    else:
        # Generic test products
        test_products = [
            {"title": "Test Product Base Model"},
            {"title": "Test Product Pro Variant"},
            {"title": "Test Product Case Accessory"},
        ]
    
    print(f"🔥 Testing Smart Product Filter for: '{search_query}'")
    print("=" * 80)
    
    included, excluded = filter_engine.filter_product_list(test_products, search_query)
    
    print(f"📊 RESULTS: {len(included)} included, {len(excluded)} excluded")
    print()
    
    print("✅ INCLUDED PRODUCTS:")
    for i, product in enumerate(included, 1):
        title = product['title']
        print(f"  {i}. {title}")
    print()
    
    print("❌ EXCLUDED PRODUCTS:")
    for i, product in enumerate(excluded, 1):
        title = product['title']
        reason = product.get('exclusion_reason', 'Unknown')
        print(f"  {i}. {title}")
        print(f"     → Reason: {reason}")
        print()
    
    # Get statistics
    if excluded:
        stats = filter_engine.get_filter_statistics(excluded)
        print("📈 EXCLUSION STATISTICS:")
        for reason, count in stats.items():
            print(f"  • {reason}: {count} products")
        print()
    
    # Verify expected results
    expected_included = 4  # Should include only exact "Redmi Note 10" matches
    actual_included = len(included)
    
    if actual_included == expected_included:
        print("🎉 SUCCESS: Filter worked correctly!")
        print(f"   Expected {expected_included} included, got {actual_included}")
    else:
        print("❌ FAILURE: Filter didn't work as expected!")
        print(f"   Expected {expected_included} included, got {actual_included}")
    
    return included, excluded

def test_parsing_examples():
    """Test parsing of various Redmi models."""
    
    filter_engine = SmartProductFilter()
    
    test_titles = [
        "Redmi Note 10",
        "Redmi Note 10 Pro",
        "Redmi Note 11", 
        "Redmi 9A",
        "Xiaomi Redmi Note 10",
        "Redmi Note 10 Case",
        "Samsung Galaxy Note 10",
        "iPhone 12 Pro Max"
    ]
    
    print("\n🔍 PARSING TESTS:")
    print("=" * 50)
    
    for title in test_titles:
        parsed = filter_engine._parse_phone_model(title.lower())
        if parsed:
            print(f"'{title}' → Brand: {parsed['brand']}, Model: {parsed['model']}, Variants: '{parsed['variants']}'")
        else:
            print(f"'{title}' → Could not parse")
    
    print()

if __name__ == "__main__":
    print("🧠 Smart Product Filter Test - Multiple Search Intent Scenarios")
    print("=" * 80)
    
    # Test parsing first
    test_parsing_examples()
    
    # Test multiple search scenarios to verify both base model and variant filtering
    test_multiple_search_scenarios()
    
    print("\n✅ Test completed!")
    print("\nThe filter should now work correctly for:")
    print("  ✅ Base model searches (e.g., 'iPhone 16', 'Redmi Note 10')")
    print("  ✅ Variant searches (e.g., 'iPhone 16 Pro', 'Redmi Note 10 Pro')")
    print("  ❌ EXCLUDE: Accessories, covers, cases, etc.")
    print("  ❌ EXCLUDE: Other model versions (e.g., Note 11 vs Note 10)")
