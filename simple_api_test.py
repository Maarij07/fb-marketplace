#!/usr/bin/env python3
"""
Simple API test script that directly tests the Flask app components
"""

import os
import sys
import json
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from web.app import create_app
from core.json_manager import JSONDataManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_json_manager():
    """Test the JSON manager directly."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing JSON Manager ===")
    
    json_manager = JSONDataManager()
    
    # Test recent products
    recent_products = json_manager.get_recent_products(5)
    logger.info(f"Recent products: {len(recent_products)}")
    
    for i, product in enumerate(recent_products):
        logger.info(f"Product {i+1}: '{product.get('title', 'No title')}' - Price: {product.get('price', {}).get('amount', 'N/A')}")
    
    # Test system stats
    stats = json_manager.get_system_stats()
    logger.info(f"System stats: {stats}")
    
    return recent_products

def test_flask_app():
    """Test the Flask app directly."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing Flask App Components ===")
    
    settings = Settings()
    app = create_app(settings)
    
    with app.test_client() as client:
        # Test stats endpoint
        logger.info("Testing /api/stats")
        response = client.get('/api/stats')
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"Stats response: {data}")
        
        # Test listings endpoint
        logger.info("Testing /api/listings")
        response = client.get('/api/listings')
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                listings = data.get('data', [])
                logger.info(f"Found {len(listings)} listings")
                if listings:
                    sample = listings[0]
                    logger.info(f"Sample listing: {sample.get('title', 'No title')} - {sample.get('price_display', 'No price')}")
                    logger.info(f"Sample keys: {list(sample.keys())}")
            else:
                logger.error(f"API error: {data.get('error')}")

def main():
    """Main test function."""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Direct API Component Testing ===")
    
    try:
        # Test JSON manager directly
        products = test_json_manager()
        
        print("\n")
        
        # Test Flask app
        test_flask_app()
        
        logger.info("=== Testing completed ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
