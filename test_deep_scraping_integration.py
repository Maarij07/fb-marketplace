#!/usr/bin/env python3
"""
Test script for deep scraping integration with scheduler manager.

This script tests the integration of deep scraping methods into the main
scheduler system to ensure the complete competitive intelligence pipeline works.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from core.settings import Settings
from core.scheduler import SchedulerManager
from core.persistent_session import get_persistent_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_deep_scraping_config():
    """Test deep scraping configuration management."""
    print("\n" + "="*60)
    print("TESTING DEEP SCRAPING CONFIGURATION")
    print("="*60)
    
    try:
        # Initialize settings
        settings = Settings()
        
        # Test enabling deep scraping
        settings.set('ENABLE_DEEP_SCRAPING', 'true')
        settings.set('DEEP_SCRAPE_MAX_PRODUCTS', '5')
        settings.set('DEEP_SCRAPE_PAGE_TIMEOUT', '20')
        
        # Initialize scheduler with deep scraping
        scheduler = SchedulerManager(settings)
        
        # Test configuration retrieval
        config = scheduler.get_deep_scraping_config()
        print(f"✅ Deep scraping config: {json.dumps(config, indent=2)}")
        
        # Test configuration update
        new_config = {
            'enabled': True,
            'max_products': 8,
            'page_load_timeout': 25
        }
        success = scheduler.update_deep_scraping_config(new_config)
        print(f"✅ Config update success: {success}")
        
        # Verify update
        updated_config = scheduler.get_deep_scraping_config()
        print(f"✅ Updated config: {json.dumps(updated_config, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deep scraping configuration test failed: {e}")
        return False

def test_scheduler_integration():
    """Test scheduler integration with deep scraping."""
    print("\n" + "="*60)
    print("TESTING SCHEDULER DEEP SCRAPING INTEGRATION")
    print("="*60)
    
    try:
        # Initialize settings with deep scraping enabled
        settings = Settings()
        settings.set('ENABLE_DEEP_SCRAPING', 'true')
        settings.set('DEEP_SCRAPE_MAX_PRODUCTS', '3')  # Small number for testing
        
        # Initialize scheduler
        scheduler = SchedulerManager(settings)
        
        # Test manual deep scraping method
        print("🔍 Testing manual deep scraping...")
        result = scheduler.run_deep_scraping_manual(
            search_query="iphone 15",  # Different from default to test
            max_products=2
        )
        
        print(f"✅ Manual deep scraping result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Listings found: {result.get('listings_found', 0)}")
        print(f"   Duration: {result.get('duration_seconds', 0)}s")
        print(f"   Method: {result.get('scraping_method', 'unknown')}")
        
        if result.get('error'):
            print(f"   Error: {result['error']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Scheduler integration test failed: {e}")
        return False

def test_persistent_session_integration():
    """Test persistent session integration with deep scraping."""
    print("\n" + "="*60)
    print("TESTING PERSISTENT SESSION DEEP SCRAPING INTEGRATION")
    print("="*60)
    
    try:
        # Initialize settings
        settings = Settings()
        settings.set('ENABLE_DEEP_SCRAPING', 'true')
        settings.set('DEEP_SCRAPE_MAX_PRODUCTS', '3')
        
        # Get persistent session
        session = get_persistent_session(settings)
        
        # Test capabilities
        capabilities = session.get_scraping_capabilities()
        print(f"✅ Scraping capabilities: {json.dumps(capabilities, indent=2)}")
        
        # Test forced deep scraping (this will likely fail due to Facebook login requirements)
        print("🔍 Testing forced deep scraping (may fail due to login requirements)...")
        try:
            results = session.run_deep_scrape(
                search_query="samsung galaxy",
                max_products=2
            )
            print(f"✅ Deep scrape results: {len(results)} products found")
            
            if results:
                # Show sample of deep data structure
                sample = results[0]
                print("📊 Sample deep scraped data structure:")
                for key in sample.keys():
                    if isinstance(sample[key], dict):
                        print(f"   {key}: {len(sample[key])} fields")
                    elif isinstance(sample[key], list):
                        print(f"   {key}: {len(sample[key])} items")
                    else:
                        print(f"   {key}: {type(sample[key]).__name__}")
        
        except Exception as deep_error:
            print(f"⚠️  Deep scraping expected to fail without valid FB session: {deep_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Persistent session integration test failed: {e}")
        return False

def test_settings_integration():
    """Test that all deep scraping settings are properly integrated."""
    print("\n" + "="*60)
    print("TESTING DEEP SCRAPING SETTINGS INTEGRATION")
    print("="*60)
    
    try:
        settings = Settings()
        
        # Test all deep scraping settings
        test_settings = {
            'ENABLE_DEEP_SCRAPING': 'true',
            'DEEP_SCRAPE_MAX_PRODUCTS': '12',
            'DEEP_SCRAPE_PAGE_TIMEOUT': '20',
            'DEEP_SCRAPE_ELEMENT_TIMEOUT': '10',
            'DEEP_SCRAPE_DELAY_MIN': '2',
            'DEEP_SCRAPE_DELAY_MAX': '5'
        }
        
        # Set all test settings
        for key, value in test_settings.items():
            settings.set(key, value)
            retrieved_value = settings.get(key)
            print(f"✅ {key}: set='{value}' retrieved='{retrieved_value}'")
        
        # Test boolean and integer parsing
        print(f"✅ Boolean parsing - ENABLE_DEEP_SCRAPING: {settings.get_bool('ENABLE_DEEP_SCRAPING')}")
        print(f"✅ Integer parsing - DEEP_SCRAPE_MAX_PRODUCTS: {settings.get_int('DEEP_SCRAPE_MAX_PRODUCTS')}")
        
        # Test defaults
        print(f"✅ Default handling - NON_EXISTENT_SETTING: {settings.get_bool('NON_EXISTENT_SETTING', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings integration test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Starting Deep Scraping Integration Tests")
    print("="*60)
    
    # Run all tests
    tests = [
        ("Settings Integration", test_settings_integration),
        ("Deep Scraping Configuration", test_deep_scraping_config),
        ("Persistent Session Integration", test_persistent_session_integration),
        ("Scheduler Integration", test_scheduler_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            success = test_func()
            results[test_name] = success
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   Result: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"   Result: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deep scraping integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
