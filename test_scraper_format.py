#!/usr/bin/env python3
"""
Test script to verify scraper data format matches dashboard expectations
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.json_manager import JSONDataManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_realistic_scraper_data():
    """Create test data that matches the scraper's output format."""
    return [
        {
            'id': 'mp_1234567890',
            'title': 'iPhone 16 Pro Max 256GB - Perfect condition',
            'price': {
                'raw_value': '15000 kr',
                'currency': 'SEK',
                'amount': '15000',
                'note': 'Extracted from: 15000 kr'
            },
            'location': {
                'city': 'Stockholm',
                'distance': '5 km',
                'raw_location': 'Stockholm 5 km'
            },
            'marketplace_url': 'https://facebook.com/marketplace/item/1234567890',
            'images': [
                {
                    'url': 'https://scontent.fbcdn.net/test_image.jpg',
                    'type': 'thumbnail',
                    'size': 'unknown'
                }
            ],
            'seller': {
                'info': 'Not extracted',
                'profile': None
            },
            'product_details': {
                'model': 'iPhone 16 Pro Max',
                'storage': 'Unknown',
                'condition': 'Unknown',
                'color': 'Unknown'
            },
            'extraction_method': 'automated_scraper',
            'data_quality': 'medium',
            'full_url': 'https://facebook.com/marketplace/item/1234567890',
            'added_at': datetime.now().isoformat(),
            'source': 'facebook_marketplace_scraper'
        },
        {
            'id': 'mp_9876543210',
            'title': 'iPhone 16 128GB Blue - Like new',
            'price': {
                'raw_value': '12500 kr',
                'currency': 'SEK', 
                'amount': '12500',
                'note': 'Extracted from: 12500 kr'
            },
            'location': {
                'city': 'Stockholm',
                'distance': '8 km',
                'raw_location': 'Stockholm 8 km'
            },
            'marketplace_url': 'https://facebook.com/marketplace/item/9876543210',
            'images': [
                {
                    'url': 'https://scontent.fbcdn.net/test_image2.jpg',
                    'type': 'thumbnail',
                    'size': 'unknown'
                }
            ],
            'seller': {
                'info': 'Not extracted',
                'profile': None
            },
            'product_details': {
                'model': 'iPhone 16',
                'storage': 'Unknown',
                'condition': 'Unknown',
                'color': 'Unknown'
            },
            'extraction_method': 'automated_scraper',
            'data_quality': 'medium',
            'full_url': 'https://facebook.com/marketplace/item/9876543210',
            'added_at': datetime.now().isoformat(),
            'source': 'facebook_marketplace_scraper'
        }
    ]

def test_dashboard_compatibility():
    """Test that scraper format data works with dashboard."""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Testing Scraper Data Format Compatibility ===")
    
    # Create realistic test data
    test_listings = create_realistic_scraper_data()
    logger.info(f"Created {len(test_listings)} realistic test listings")
    
    # Test with JSON manager
    json_manager = JSONDataManager()
    
    # Add the test data
    stats = json_manager.add_products_batch(test_listings)
    logger.info(f"Added to JSON: {stats}")
    
    # Fetch recent products (like dashboard does)
    recent_products = json_manager.get_recent_products(5)
    logger.info(f"Recent products count: {len(recent_products)}")
    
    # Test dashboard format conversion (like web app does)
    from web.app import create_app
    from config.settings import Settings
    
    settings = Settings()
    app = create_app(settings)
    
    with app.test_client() as client:
        response = client.get('/api/listings?limit=5')
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                listings = data.get('data', [])
                logger.info(f"Dashboard API returned {len(listings)} listings")
                
                # Check the format of dashboard listings
                if listings:
                    sample = listings[0]
                    logger.info("Dashboard format sample listing:")
                    logger.info(f"  Title: {sample.get('title')}")
                    logger.info(f"  Price Display: {sample.get('price_display')}")
                    logger.info(f"  Location: {sample.get('seller_location')}")
                    logger.info(f"  Category: {sample.get('category')}")
                    logger.info(f"  Created At: {sample.get('created_at')}")
                    
                    # Check if all expected fields are present
                    expected_fields = ['title', 'price_display', 'seller_location', 'category', 'created_at']
                    missing_fields = [field for field in expected_fields if field not in sample]
                    if missing_fields:
                        logger.error(f"Missing fields in dashboard format: {missing_fields}")
                    else:
                        logger.info("✓ All expected dashboard fields are present")
                        
                return True
    
    logger.error("Failed to test dashboard compatibility")
    return False

def main():
    """Main test function."""
    logger = logging.getLogger(__name__)
    
    try:
        success = test_dashboard_compatibility()
        if success:
            logger.info("✓ Scraper data format is compatible with dashboard")
        else:
            logger.error("✗ Compatibility issues found")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
