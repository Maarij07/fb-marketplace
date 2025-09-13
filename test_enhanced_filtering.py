#!/usr/bin/env python3
"""
Test script for enhanced smart product filtering with comprehensive blacklist and whitelist.

This script tests the filtering system to ensure:
1. Accessories and covers are properly blacklisted
2. Exact iPhone models are whitelisted (no variants)
3. Color names and valid phone terms are whitelisted
"""

from core.product_filter import SmartProductFilter

def test_enhanced_filtering():
    """Test the enhanced filtering with real-world examples."""
    
    # Initialize the filter
    filter_engine = SmartProductFilter()
    
    # Test cases: (product_title, search_query, expected_result, description)
    test_cases = [
        # ✅ SHOULD BE INCLUDED - Exact iPhone matches
        ("iPhone 15 128GB Black Unlocked", "iPhone 15", True, "Exact iPhone 15 with color and storage"),
        ("iPhone 16 256GB Space Gray", "iPhone 16", True, "Exact iPhone 16 with valid color"),
        ("iPhone 13 64GB Blue Mint Condition", "iPhone 13", True, "Exact iPhone 13 with condition"),
        ("Apple iPhone 14 512GB Gold Factory Unlocked", "iPhone 14", True, "Exact iPhone 14 with brand prefix"),
        ("iPhone 12 Pro", "iPhone 12 Pro", True, "Exact iPhone 12 Pro match"),
        
        # ❌ SHOULD BE EXCLUDED - Accessories and covers
        ("iPhone 15 Case Black Silicone", "iPhone 15", False, "iPhone case - should be blacklisted"),
        ("iPhone 16 Screen Protector Tempered Glass", "iPhone 16", False, "Screen protector - should be blacklisted"),
        ("iPhone 14 Charger Lightning Cable", "iPhone 14", False, "Charger cable - should be blacklisted"),
        ("iPhone 13 Cover Leather Wallet", "iPhone 13", False, "Leather cover - should be blacklisted"),
        ("iPhone 12 Bumper Case Clear", "iPhone 12", False, "Bumper case - should be blacklisted"),
        ("iPhone 15 Airpods Pro", "iPhone 15", False, "Airpods - should be blacklisted"),
        ("iPhone 16 Stand Desk Mount", "iPhone 16", False, "Phone stand - should be blacklisted"),
        ("iPhone 14 Battery Replacement Kit", "iPhone 14", False, "Battery replacement - should be blacklisted"),
        
        # ❌ SHOULD BE EXCLUDED - Wrong variants
        ("iPhone 15 Pro", "iPhone 15", False, "iPhone 15 Pro when searching for iPhone 15"),
        ("iPhone 16 Plus", "iPhone 16", False, "iPhone 16 Plus when searching for iPhone 16"),
        ("iPhone 14 Pro Max", "iPhone 14", False, "iPhone 14 Pro Max when searching for iPhone 14"),
        ("iPhone 13 Mini", "iPhone 13", False, "iPhone 13 Mini when searching for iPhone 13"),
        
        # ❌ SHOULD BE EXCLUDED - Different models
        ("iPhone 14", "iPhone 15", False, "Different iPhone model"),
        ("iPhone 16", "iPhone 15", False, "Different iPhone model (newer)"),
        
        # ✅ SHOULD BE INCLUDED - Edge cases with valid phone terms
        ("iPhone 15 128GB Black New in Box", "iPhone 15", True, "Valid phone with 'box' (not 'box only')"),
        ("iPhone 16 256GB Unlocked GSM", "iPhone 16", True, "Valid phone with network terms"),
        ("iPhone 14 64GB Refurbished Like New", "iPhone 14", True, "Valid phone with condition terms"),
        
        # ❌ SHOULD BE EXCLUDED - Clear accessories with phone names
        ("iPhone 15 Case Bundle with Screen Protector", "iPhone 15", False, "Bundle of accessories"),
        ("iPhone 16 Charging Kit Wireless Pad", "iPhone 16", False, "Charging accessories kit"),
        ("iPhone 14 Repair Service Broken Screen", "iPhone 14", False, "Repair service - should be blacklisted"),
    ]
    
    print("🧪 Testing Enhanced Smart Product Filtering")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, (title, search_query, expected, description) in enumerate(test_cases, 1):
        try:
            should_include, reason = filter_engine.should_include_product(title, search_query)
            
            # Check if result matches expectation
            if should_include == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
            
            print(f"{status} Test {i:2d}: {description}")
            print(f"    Title: '{title}'")
            print(f"    Search: '{search_query}'")
            print(f"    Expected: {'INCLUDE' if expected else 'EXCLUDE'}, Got: {'INCLUDE' if should_include else 'EXCLUDE'}")
            print(f"    Reason: {reason}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR Test {i:2d}: {description}")
            print(f"    Exception: {e}")
            print()
            failed += 1
    
    print("=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced filtering is working correctly.")
    else:
        print(f"⚠️  {failed} tests failed. Please review the filtering logic.")
    
    return failed == 0


def test_specific_cases():
    """Test specific edge cases that were problematic."""
    
    filter_engine = SmartProductFilter()
    
    print("\n🔍 Testing Specific Edge Cases")
    print("=" * 40)
    
    edge_cases = [
        ("iPhone 13 128GB Space Gray", "iPhone 13", "Should INCLUDE - exact match with color"),
        ("iPhone 13 Pro 128GB Space Gray", "iPhone 13", "Should EXCLUDE - has Pro variant"),
        ("iPhone 13 Case Space Gray", "iPhone 13", "Should EXCLUDE - is a case"),
        ("Space Gray iPhone 13 128GB", "iPhone 13", "Should INCLUDE - different word order"),
    ]
    
    for title, search_query, expected_behavior in edge_cases:
        should_include, reason = filter_engine.should_include_product(title, search_query)
        result_text = "INCLUDE" if should_include else "EXCLUDE"
        
        print(f"Title: '{title}'")
        print(f"Search: '{search_query}'")
        print(f"Result: {result_text}")
        print(f"Reason: {reason}")
        print(f"Expected: {expected_behavior}")
        print("-" * 40)


if __name__ == "__main__":
    # Run main tests
    success = test_enhanced_filtering()
    
    # Run edge case tests
    test_specific_cases()
    
    print(f"\n{'🎉 SUCCESS' if success else '❌ SOME TESTS FAILED'}: Enhanced filtering test complete!")
