#!/usr/bin/env python3
"""
Debug script to test JSON data saving functionality
Tests the JSON manager without needing to run the full scraper.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_listing(index: int):
    """Create a test listing for debugging."""
    return {
        'id': f'mp_test_{index}',
        'title': f'Test iPhone {16 + index} Pro - Debug Listing {index}',
        'price': {
            'amount': str(10000 + (index * 1000)),
            'currency': 'SEK',
            'raw_value': f'{10 + index}000 kr'
        },
        'location': {
            'city': 'Stockholm',
            'distance': f'{5 + index} km',
            'raw_location': f'Stockholm {5 + index} km'
        },
        'marketplace_url': f'https://facebook.com/marketplace/item/{123456 + index}',
        'images': [
            {
                'url': f'https://scontent.test/test_image_{index}.jpg',
                'type': 'thumbnail',
                'size': 'unknown'
            }
        ],
        'seller': {
            'info': f'Test Seller {index}',
            'profile': None
        },
        'product_details': {
            'model': f'iPhone {16 + index}',
            'storage': '128GB',
            'condition': 'Like new',
            'color': 'Black'
        },
        'extraction_method': 'debug_test',
        'data_quality': 'high',
        'full_url': f'https://facebook.com/marketplace/item/{123456 + index}',
        'added_at': datetime.now().isoformat(),
        'source': 'debug_test_script'
    }

def main():
    """Main debug function."""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Starting JSON Manager Debug Test ===")
    
    try:
        # Initialize JSON manager
        json_manager = JSONDataManager()
        logger.info(f"JSON Manager initialized with path: {json_manager.json_path}")
        
        # Check if JSON file exists
        if os.path.exists(json_manager.json_path):
            logger.info(f"JSON file exists: {json_manager.json_path}")
            try:
                with open(json_manager.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Current products in JSON: {len(data.get('products', []))}")
            except Exception as e:
                logger.error(f"Failed to read existing JSON: {e}")
        else:
            logger.info("JSON file does not exist yet")
        
        # Create test listings
        test_listings = []
        for i in range(3):
            listing = create_test_listing(i)
            test_listings.append(listing)
            logger.info(f"Created test listing {i}: {listing['title']}")
        
        # Test single product addition
        logger.info("\n--- Testing single product addition ---")
        single_result = json_manager.add_product(test_listings[0])
        logger.info(f"Single product add result: {single_result}")
        
        # Test batch addition
        logger.info("\n--- Testing batch product addition ---")
        batch_result = json_manager.add_products_batch(test_listings[1:])
        logger.info(f"Batch add result: {batch_result}")
        
        # Check final state
        logger.info("\n--- Checking final state ---")
        recent_products = json_manager.get_recent_products(10)
        logger.info(f"Recent products count: {len(recent_products)}")
        
        for i, product in enumerate(recent_products[:3]):
            logger.info(f"Product {i+1}: {product.get('title', 'No title')} - {product.get('id', 'No ID')}")
        
        # Get system stats
        stats = json_manager.get_system_stats()
        logger.info(f"System stats: {stats}")
        
        # Test search functionality
        logger.info("\n--- Testing search functionality ---")
        search_results = json_manager.search_products("iPhone", 5)
        logger.info(f"Search results for 'iPhone': {len(search_results)} found")
        
        logger.info("=== Debug test completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
