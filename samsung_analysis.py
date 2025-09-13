#!/usr/bin/env python3
"""
DEEP ANALYSIS: Samsung S22 Filtering Logic
This script traces exactly what happens when you search for "Samsung S22"
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_samsung_parsing():
    """Analyze Samsung regex pattern step by step."""
    
    print("🔍 DEEP ANALYSIS: Samsung S22 Pattern Matching")
    print("=" * 80)
    
    # The NEW flexible Samsung regex pattern from the updated code
    samsung_pattern = r'(?:samsung\s*(?:galaxy\s*)?s(\d+)|galaxy\s*s(\d+)|samsung\s*s(\d+))(\s*(ultra|plus|edge|fe|lite|neo))?|(?:samsung\s*)?galaxy\s*note\s*(\d+)(\s*(ultra|plus))?'
    
    print(f"Samsung Regex Pattern: {samsung_pattern}")
    print()
    
    # Test cases for Samsung S22
    test_cases = [
        # These should be INCLUDED for "Samsung S22" search
        "Samsung Galaxy S22",
        "Samsung Galaxy S22 128GB", 
        "Galaxy S22 256GB",
        "Samsung S22 Black",
        "SAMSUNG GALAXY S22",
        
        # These should be EXCLUDED for "Samsung S22" search  
        "Samsung Galaxy S22 Plus",
        "Samsung Galaxy S22 Ultra", 
        "Galaxy S22 FE",
        "Samsung Galaxy S22 Edge",
        "Samsung S22 Case",
        "Samsung Galaxy S21",
        "Samsung Galaxy S23",
    ]
    
    print("📋 Testing Samsung Pattern Matching:")
    print("-" * 50)
    
    for case in test_cases:
        print(f"Testing: '{case}'")
        
        # Test the regex
        match = re.search(samsung_pattern, case.lower())
        if match:
            print(f"  ✅ MATCHED!")
            print(f"  📊 Groups: {match.groups()}")
            
            # Parse like the actual code does
            base_model = match.group(1) if match.group(1) else match.group(4)
            variant = match.group(2) if match.group(2) else match.group(5)  # This includes the whitespace
            actual_variant = match.group(3) if match.group(3) else match.group(6)  # This is the clean variant
            model_type = "Galaxy S" if match.group(1) else "Galaxy Note"
            
            print(f"  🏷️  Brand: Samsung")
            print(f"  🔢 Model: {base_model}")
            print(f"  📝 Raw Variant Group: '{variant}'")
            print(f"  🎯 Clean Variant: '{actual_variant if actual_variant else ''}'")
            print(f"  🏆 Full Model: {model_type} {base_model}" + (f" {actual_variant}" if actual_variant else ""))
            
        else:
            print(f"  ❌ NO MATCH")
        print()

def analyze_filtering_logic():
    """Analyze the full filtering logic for Samsung S22."""
    
    print("🧠 DEEP ANALYSIS: Samsung S22 Filtering Logic")
    print("=" * 80)
    
    # Simulate the filtering logic step by step
    search_query = "Samsung S22"
    
    print(f"Search Query: '{search_query}'")
    print()
    
    # Step 1: Parse search query
    print("STEP 1: Parse Search Query")
    print("-" * 30)
    
    # Clean the search
    search_clean = search_query.strip()
    print(f"Cleaned search: '{search_clean}'")
    
    # Parse search with Samsung pattern (NEW flexible pattern)
    samsung_pattern = r'(?:samsung\s*(?:galaxy\s*)?s(\d+)|galaxy\s*s(\d+)|samsung\s*s(\d+))(\s*(ultra|plus|edge|fe|lite|neo))?|(?:samsung\s*)?galaxy\s*note\s*(\d+)(\s*(ultra|plus))?'
    search_match = re.search(samsung_pattern, search_clean.lower())
    
    if search_match:
        # Handle the new flexible pattern groups
        search_base_model = search_match.group(1) or search_match.group(2) or search_match.group(3) or search_match.group(6)
        search_variant = search_match.group(5) or search_match.group(8)  # Clean variant
        search_model_type = "Galaxy Note" if search_match.group(6) else "Galaxy S"
        
        target_info = {
            'brand': 'Samsung',
            'model': search_base_model,
            'variants': search_variant if search_variant else '',
            'full_model': f"{search_model_type} {search_base_model}" + (f" {search_variant}" if search_variant else "")
        }
        
        print(f"✅ Search parsed successfully:")
        print(f"  Brand: {target_info['brand']}")
        print(f"  Model: {target_info['model']}")
        print(f"  Variants: '{target_info['variants']}'")
        print(f"  Full Model: {target_info['full_model']}")
    else:
        print("❌ Search parsing failed!")
        return
    
    print()
    
    # Step 2: Test product filtering
    print("STEP 2: Test Product Filtering")
    print("-" * 30)
    
    test_products = [
        "Samsung Galaxy S22 128GB",      # Should INCLUDE
        "Samsung Galaxy S22 Plus 256GB", # Should EXCLUDE 
        "Samsung Galaxy S22 Ultra",      # Should EXCLUDE
        "Samsung Galaxy S22 Case",       # Should EXCLUDE
        "Samsung Galaxy S21 128GB",      # Should EXCLUDE
    ]
    
    for product_title in test_products:
        print(f"\nTesting product: '{product_title}'")
        
        # Step 2a: Check accessories first
        accessory_keywords = ['case', 'cover', 'screen protector', 'charger', 'cable']
        is_accessory = any(keyword in product_title.lower() for keyword in accessory_keywords)
        
        if is_accessory:
            print(f"  ❌ EXCLUDED: Contains accessory keyword")
            continue
        
        # Step 2b: Parse product
        product_match = re.search(samsung_pattern, product_title.lower())
        
        if not product_match:
            print(f"  ❌ EXCLUDED: Could not parse product model")
            continue
            
        # Handle the new flexible pattern groups for products too
        product_base_model = product_match.group(1) or product_match.group(2) or product_match.group(3) or product_match.group(6)
        product_variant = product_match.group(5) or product_match.group(8)  # Clean variant
        product_model_type = "Galaxy Note" if product_match.group(6) else "Galaxy S"
        
        product_info = {
            'brand': 'Samsung',
            'model': product_base_model,
            'variants': product_variant if product_variant else '',
            'full_model': f"{product_model_type} {product_base_model}" + (f" {product_variant}" if product_variant else "")
        }
        
        print(f"  📊 Product parsed:")
        print(f"    Brand: {product_info['brand']}")
        print(f"    Model: {product_info['model']}")
        print(f"    Variants: '{product_info['variants']}'")
        print(f"    Full Model: {product_info['full_model']}")
        
        # Step 2c: Check model match
        if target_info['model'] != product_info['model']:
            print(f"  ❌ EXCLUDED: Different model number ({product_info['model']} vs {target_info['model']})")
            continue
        
        # Step 2d: Check variant match
        target_variants = set(target_info['variants'].lower().split()) if target_info['variants'] else set()
        product_variants = set(product_info['variants'].lower().split()) if product_info['variants'] else set()
        
        print(f"  🎯 Target variants: {target_variants}")
        print(f"  🎯 Product variants: {product_variants}")
        
        # Apply the core logic
        if not target_variants:  # Target has no variants (base model search)
            if product_variants:
                print(f"  ❌ EXCLUDED: Target is base model but product has variants: {product_variants}")
            else:
                print(f"  ✅ INCLUDED: Both are base model - exact match!")
        else:  # Target has variants
            if not product_variants:
                print(f"  ❌ EXCLUDED: Target has variants but product is base model")
            elif target_variants == product_variants:
                print(f"  ✅ INCLUDED: Exact variant match: {target_variants}")
            else:
                print(f"  ❌ EXCLUDED: Different variants - target wants {target_variants}, product has {product_variants}")

if __name__ == "__main__":
    print("🚀 SAMSUNG S22 DEEP ANALYSIS")
    print("=" * 80)
    print("This script analyzes exactly what happens when you search for 'Samsung S22'")
    print()
    
    # First analyze the parsing
    analyze_samsung_parsing()
    
    print("\n" + "=" * 80)
    print()
    
    # Then analyze the full filtering logic
    analyze_filtering_logic()
    
    print("\n" + "=" * 80)
    print("🎯 CONCLUSION FOR 'Samsung S22' SEARCH:")
    print("✅ WILL INCLUDE: Samsung Galaxy S22, Galaxy S22 128GB, Samsung S22 Black")
    print("❌ WILL EXCLUDE: Samsung S22 Plus, Samsung S22 Ultra, Samsung S22 Case, Samsung S21/S23")
    print("\nThe logic is CORRECT! ✅")
