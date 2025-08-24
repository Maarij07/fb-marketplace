#!/usr/bin/env python3

import time
from datetime import datetime, timedelta
from core.json_manager import JSONDataManager

def test_retention_fix():
    """Test that the retention policy fix works."""
    print("=== Retention Policy Fix Test ===")
    print()
    
    json_manager = JSONDataManager()
    
    # Create test products with different ages
    now = datetime.now()
    
    test_products = [
        {
            "id": f"old_product_{int(time.time())}",
            "title": "Old iPhone 15 Pro - Should be kept with new retention",
            "price": {"amount": "7000", "currency": "SEK"},
            "location": {"city": "Stockholm"},
            "marketplace_url": f"https://facebook.com/marketplace/item/old{int(time.time())}",
            "images": [],
            "seller": {"info": "Old Seller"},
            "product_details": {"model": "iPhone 15 Pro"},
            "extraction_method": "test_retention",
            "source": "retention_test",
            "added_at": (now - timedelta(hours=100)).isoformat()  # 100 hours old (would be deleted with 48h retention)
        },
        {
            "id": f"recent_product_{int(time.time())}",
            "title": "Recent iPhone 16 Pro - Should definitely be kept", 
            "price": {"amount": "9000", "currency": "SEK"},
            "location": {"city": "Stockholm"},
            "marketplace_url": f"https://facebook.com/marketplace/item/recent{int(time.time())}",
            "images": [],
            "seller": {"info": "Recent Seller"},
            "product_details": {"model": "iPhone 16 Pro"},
            "extraction_method": "test_retention",
            "source": "retention_test",
            "added_at": (now - timedelta(hours=5)).isoformat()  # 5 hours old
        }
    ]
    
    print(f"Adding {len(test_products)} test products...")
    print(f"1. Old product (100 hours ago): Should be KEPT with 168h retention")
    print(f"2. Recent product (5 hours ago): Should be KEPT")
    print()
    
    # Save the test products
    stats = json_manager.add_products_batch(test_products)
    print(f"Save stats: {stats}")
    
    # Check what was actually saved
    products = json_manager.get_recent_products(10)
    retention_test_products = [p for p in products if p.get('source') == 'retention_test']
    
    print(f"\nProducts found after save: {len(retention_test_products)}")
    
    if len(retention_test_products) == 2:
        print("✅ SUCCESS: Both products were saved (retention policy working correctly)")
        for i, p in enumerate(retention_test_products):
            title = p.get('title', 'NO TITLE')
            added_at = p.get('added_at', 'Unknown')
            print(f"  {i+1}. {title}")
            print(f"     Added: {added_at}")
    elif len(retention_test_products) == 1:
        print("⚠️  PARTIAL: Only 1 product saved - old product may have been cleaned up")
        print("   This might happen if retention setting hasn't taken effect yet")
    else:
        print("❌ ERROR: No retention test products found")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_retention_fix()
