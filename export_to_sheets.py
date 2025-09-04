#!/usr/bin/env python3
"""
Export current marketplace data to Google Sheets
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.google_sheets_manager import GoogleSheetsManager

def main():
    print("🚀 Starting data export to Google Sheets...")
    
    # Your Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit"
    
    # Initialize Google Sheets manager
    sheets_manager = GoogleSheetsManager()
    
    if not sheets_manager.client:
        print("❌ Failed to initialize Google Sheets client")
        return False
    
    print("✅ Google Sheets client initialized")
    
    # Export all products to the main "Products" sheet
    print("📊 Exporting products data...")
    success = sheets_manager.export_all_products_to_sheets(sheet_url, "Products")
    
    if success:
        print("✅ Successfully exported products to 'Products' worksheet!")
    else:
        print("❌ Failed to export products")
        return False
    
    # Create analytics sheet
    print("📈 Creating analytics sheet...")
    analytics_success = sheets_manager.create_analytics_sheet(sheet_url, "Analytics")
    
    if analytics_success:
        print("✅ Successfully created 'Analytics' worksheet!")
    else:
        print("⚠️ Analytics sheet creation failed, but products were exported")
    
    # Create a backup of recent data (last 24 hours)
    print("💾 Creating backup sheet...")
    backup_success = sheets_manager.create_backup_in_sheets(sheet_url, 24, "Recent_Backup")
    
    if backup_success:
        print("✅ Successfully created backup worksheet!")
    else:
        print("⚠️ Backup creation failed, but main export was successful")
    
    print(f"\n🎉 Data export completed!")
    print(f"📋 Check your Google Sheet: {sheet_url}")
    print(f"📝 You should see:")
    print(f"   - Products worksheet with all {28} products")
    print(f"   - Analytics worksheet with summary stats")
    print(f"   - Recent_Backup worksheet (if created)")
    
    return True

if __name__ == "__main__":
    main()
