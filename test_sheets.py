#!/usr/bin/env python3
"""
Quick test script to verify Google Sheets integration is working
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.google_sheets_manager import GoogleSheetsManager
    
    print("Testing Google Sheets integration...")
    
    # Initialize the manager
    sheets_manager = GoogleSheetsManager()
    
    # Test connection
    print("Testing connection...")
    if sheets_manager.client:
        print("✅ Google Sheets client initialized successfully!")
        
        # Test getting sheet info
        sheet_url = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit"
        print(f"Testing access to your spreadsheet...")
        
        sheet_info = sheets_manager.get_sheet_info(sheet_url)
        if sheet_info:
            print("✅ Successfully connected to your spreadsheet!")
            print(f"   - Title: {sheet_info.get('title', 'Unknown')}")
            print(f"   - Worksheets: {', '.join(sheet_info.get('worksheets', []))}")
            print(f"   - Total worksheets: {sheet_info.get('worksheet_count', 0)}")
            
            # Test exporting sample data
            print("\nTesting data export...")
            success = sheets_manager.export_all_products_to_sheets(sheet_url)
            if success:
                print("✅ Successfully exported data to Google Sheets!")
            else:
                print("❌ Failed to export data - but connection works")
        else:
            print("❌ Could not access spreadsheet - check sharing permissions")
    else:
        print("❌ Failed to initialize Google Sheets client")
        print("   Check your credentials file at: config/google_sheets_credentials.json")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Try: pip install gspread google-auth")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")
