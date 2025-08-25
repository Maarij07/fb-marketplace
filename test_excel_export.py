#!/usr/bin/env python3
"""
Test script to verify Excel export functionality
"""

import sys
import os
import logging

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.excel_manager import ExcelManager
from config.settings import Settings

def test_excel_export():
    """Test the Excel export functionality."""
    print("🧪 Testing Excel Export Functionality...")
    
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Test ExcelManager directly
        excel_manager = ExcelManager()
        
        print("📊 Creating Excel export...")
        filepath = excel_manager.export_all_products_to_excel()
        
        if filepath:
            print(f"✅ Excel file created successfully!")
            print(f"📁 File path: {filepath}")
            
            # Try to open the file
            print("🔓 Attempting to open Excel file...")
            opened = excel_manager.open_excel_file(filepath)
            
            if opened:
                print("✅ Excel file opened successfully!")
            else:
                print("⚠️ Excel file created but failed to open automatically")
                print(f"You can manually open: {filepath}")
            
            return True
        else:
            print("❌ Failed to create Excel file")
            return False
            
    except Exception as e:
        print(f"❌ Error during Excel export test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_api():
    """Test the Excel export through the web API."""
    print("\n🌐 Testing Web API Excel Export...")
    
    try:
        from web.app import create_app
        from config.settings import Settings
        
        settings = Settings()
        app = create_app(settings)
        
        with app.test_client() as client:
            print("📤 Sending POST request to /api/excel/export...")
            response = client.post('/api/excel/export')
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    print("✅ API Excel export successful!")
                    print(f"📝 Message: {data.get('message')}")
                    if 'filepath' in data:
                        print(f"📁 File path: {data.get('filepath')}")
                else:
                    print(f"❌ API returned error: {data.get('error')}")
                    return False
            else:
                print(f"❌ API request failed with status: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Facebook Marketplace Excel Export Test")
    print("=" * 50)
    
    # Test 1: Direct Excel manager
    success1 = test_excel_export()
    
    # Test 2: Web API
    success2 = test_web_api()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"   Direct Excel Manager: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Web API Excel Export: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Excel export is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        sys.exit(1)
