#!/usr/bin/env python3
"""
Test script for Google Sheets integration
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.google_sheets_manager import GoogleSheetsManager

def test_sheet_id_extraction():
    """Test URL to Sheet ID extraction."""
    print("Testing Google Sheets URL parsing...")
    
    manager = GoogleSheetsManager()
    
    # Test with your provided URL
    test_url = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit?usp=sharing"
    sheet_id = manager.extract_sheet_id_from_url(test_url)
    
    print(f"URL: {test_url}")
    print(f"Extracted Sheet ID: {sheet_id}")
    
    expected_id = "1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI"
    
    if sheet_id == expected_id:
        print("✅ Sheet ID extraction: PASSED")
        return True
    else:
        print(f"❌ Sheet ID extraction: FAILED - Expected: {expected_id}, Got: {sheet_id}")
        return False

def test_manager_initialization():
    """Test GoogleSheetsManager initialization."""
    print("\nTesting GoogleSheetsManager initialization...")
    
    try:
        manager = GoogleSheetsManager()
        print("✅ Manager initialization: PASSED")
        
        # Test without credentials (expected to warn but not crash)
        if manager.client is None:
            print("⚠️  No credentials found (expected) - Google Sheets client is None")
        else:
            print("✅ Google Sheets client initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ Manager initialization: FAILED - {e}")
        return False

def test_data_preparation():
    """Test data preparation for Google Sheets format."""
    print("\nTesting data preparation...")
    
    try:
        manager = GoogleSheetsManager()
        
        # Sample product data (similar to your project's structure)
        sample_products = [
            {
                "id": "test_123",
                "title": "iPhone 11 64GB",
                "price": {
                    "amount": "1500",
                    "currency": "KR",
                    "raw_value": "1500 kr"
                },
                "location": {
                    "city": "Stockholm",
                    "distance": "10km"
                },
                "marketplace_url": "https://example.com/item/123",
                "seller_name": "Test Seller",
                "seller": {
                    "info": "Private Seller"
                },
                "product_details": {
                    "model": "iPhone 11",
                    "storage": "64 GB",
                    "condition": "good",
                    "color": "Black"
                },
                "images": [
                    {"url": "https://example.com/image1.jpg"},
                    {"url": "https://example.com/image2.jpg"}
                ],
                "added_at": "2025-08-27T11:42:43Z",
                "created_at": "2025-08-27T11:42:43Z",
                "source": "facebook_marketplace_scraper",
                "data_quality": "comprehensive",
                "extraction_method": "deep_scraper"
            }
        ]
        
        sheet_data = manager._prepare_products_data(sample_products)
        
        print(f"✅ Data preparation: PASSED")
        print(f"   Headers: {len(sheet_data[0])} columns")
        print(f"   Data rows: {len(sheet_data) - 1}")
        print(f"   Sample headers: {sheet_data[0][:5]}...")
        print(f"   Sample data: {sheet_data[1][:5]}...")
        
        return True
    except Exception as e:
        print(f"❌ Data preparation: FAILED - {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Google Sheets Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_sheet_id_extraction,
        test_manager_initialization,
        test_data_preparation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Google Sheets integration is ready.")
        print("\nNext steps:")
        print("1. Follow GOOGLE_SHEETS_SETUP.md to set up API credentials")
        print("2. Share your spreadsheet with the service account")
        print("3. Test the API endpoints or use the web interface")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
