#!/usr/bin/env python3
"""
Test script to verify the licensing system works correctly.
"""

import os
import sys
from datetime import date, timedelta
from license_generator import generate_license, create_license_file


def test_license_system():
    """Test the licensing system."""
    print("🧪 Testing License System")
    print("=" * 40)
    
    # Test 1: Future license should work
    print("\n1. Testing future license (should work)...")
    future_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
    create_license_file(future_date, "test_license_future.json")
    
    # Test 2: Past license should fail
    print("\n2. Testing expired license (should fail)...")
    past_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    create_license_file(past_date, "test_license_expired.json")
    
    # Test 3: Show trial status
    cutoff = date(2025, 9, 11)
    today = date.today()
    days_left = (cutoff - today).days
    
    print(f"\n📅 Current Trial Status:")
    print(f"   Today: {today}")
    print(f"   Trial ends: {cutoff}")
    print(f"   Days remaining: {days_left}")
    
    if days_left > 0:
        print("   ✅ Trial is active")
    else:
        print("   ❌ Trial has expired")
    
    print(f"\n📋 Test files created:")
    print(f"   • test_license_future.json (valid)")
    print(f"   • test_license_expired.json (expired)")
    
    print(f"\n🔧 To test with the EXE:")
    print(f"   1. Copy 'test_license_future.json' as 'license.json' in the dist folder")
    print(f"   2. Run the EXE - it should work even after Sept 11th")
    print(f"   3. Copy 'test_license_expired.json' as 'license.json' in the dist folder")
    print(f"   4. Run the EXE - it should fail if after Sept 11th")


if __name__ == "__main__":
    test_license_system()
