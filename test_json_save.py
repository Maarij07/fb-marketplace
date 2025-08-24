#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime
from core.json_manager import JSONDataManager

def test_json_save():
    """Test JSON save functionality to diagnose the issue."""
    print("=== JSON Save Test ===")
    print()
    
    json_manager = JSONDataManager()
    
    # Check current data
    print("Current data in products.json:")
    products_before = json_manager.get_recent_products(5)
    print(f"Products count before: {len(products_before)}")
    
    if products_before:
        print("Sample product titles:")
        for i, p in enumerate(products_before[:3]):
            title = p.get('title', 'NO TITLE')
            print(f"  {i+1}. {title}")
    print()
    
    # Create test product data
    test_products = [
        {
            "id": f"test_product_1_{int(time.time())}",
            "title": "Test iPhone 16 Pro - Manual Test",
            "price": {
                "amount": "8000",
                "currency": "SEK",
                "raw_value": "8 000 kr"
            },
            "location": {
                "city": "Stockholm",
                "distance": "5 km",
                "raw_location": "Stockholm, 5 km"
            },
            "marketplace_url": f"https://facebook.com/marketplace/item/test{int(time.time())}",
            "images": [],
            "seller": {
                "info": "Test Seller",
                "profile": None
            },
            "product_details": {
                "model": "iPhone 16 Pro",
                "storage": "256GB",
                "condition": "New",
                "color": "Black"
            },
            "extraction_method": "test_script",
            "data_quality": "high",
            "source": "test_save_function"
        },
        {
            "id": f"test_product_2_{int(time.time())}",
            "title": "Test Samsung Galaxy S24 - Manual Test",
            "price": {
                "amount": "6000",
                "currency": "SEK",
                "raw_value": "6 000 kr"
            },
            "location": {
                "city": "Stockholm",
                "distance": "3 km",
                "raw_location": "Stockholm, 3 km"
            },
            "marketplace_url": f"https://facebook.com/marketplace/item/test{int(time.time())+1}",
            "images": [],
            "seller": {
                "info": "Test Seller 2",
                "profile": None
            },
            "product_details": {
                "model": "Samsung Galaxy S24",
                "storage": "128GB",
                "condition": "Used",
                "color": "White"
            },
            "extraction_method": "test_script",
            "data_quality": "high",
            "source": "test_save_function"
        }
    ]
    
    # Test saving
    print(f"Attempting to save {len(test_products)} test products...")
    try:
        stats = json_manager.add_products_batch(test_products)
        print(f"Save result: {stats}")
    except Exception as e:
        print(f"ERROR during save: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Wait a moment for file system to update
    time.sleep(1)
    
    # Check data after save
    print("\nChecking data after save:")
    products_after = json_manager.get_recent_products(10)
    print(f"Products count after: {len(products_after)}")
    
    # Look for our test products
    test_products_found = [p for p in products_after if 'Manual Test' in p.get('title', '')]
    print(f"Test products found: {len(test_products_found)}")
    
    if test_products_found:
        print("Our test products:")
        for i, p in enumerate(test_products_found):
            title = p.get('title', 'NO TITLE')
            added_at = p.get('added_at', 'Unknown')
            print(f"  {i+1}. {title} (Added: {added_at})")
    else:
        print("ERROR: Test products not found in recent listings!")
        
        # Debug: Check if they were saved to the file at all
        print("\nDebugging - checking raw file content...")
        try:
            with open(json_manager.json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Manual Test' in content:
                    print("Test products ARE in the file!")
                else:
                    print("Test products NOT found in file content")
                    
                # Check file size
                file_size = len(content)
                print(f"File size: {file_size} characters")
                
        except Exception as e:
            print(f"Error reading file: {e}")
    
    # Check file permissions
    print(f"\nFile permissions check:")
    file_path = json_manager.json_path
    print(f"File path: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(f"File readable: {os.access(file_path, os.R_OK)}")
    print(f"File writable: {os.access(file_path, os.W_OK)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_json_save()
