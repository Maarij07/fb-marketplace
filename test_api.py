#!/usr/bin/env python3
"""
Test script to check web API endpoints
Tests the Flask web app endpoints to see what data is being returned.
"""

import os
import sys
import requests
import json
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_api_endpoint(url: str, endpoint: str):
    """Test a single API endpoint."""
    logger = logging.getLogger(__name__)
    full_url = f"{url}{endpoint}"
    
    try:
        logger.info(f"Testing endpoint: {full_url}")
        response = requests.get(full_url, timeout=10)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    result_data = data.get('data', [])
                    if isinstance(result_data, list):
                        logger.info(f"Success! Found {len(result_data)} items")
                        if result_data:
                            # Show sample data
                            first_item = result_data[0]
                            logger.info(f"Sample item keys: {list(first_item.keys())}")
                            logger.info(f"Sample title: {first_item.get('title', 'No title')}")
                            logger.info(f"Sample price: {first_item.get('price_display', 'No price')}")
                    else:
                        logger.info(f"Success! Data: {result_data}")
                else:
                    logger.error(f"API error: {data.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response")
                logger.info(f"Raw response: {response.text[:200]}")
        else:
            logger.error(f"HTTP error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection failed - is the Flask app running on {url}?")
    except Exception as e:
        logger.error(f"Request failed: {e}")

def main():
    """Main test function."""
    logger = logging.getLogger(__name__)
    
    # Test different possible URLs
    urls_to_test = [
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "http://127.0.0.1:8080", 
        "http://localhost:8080"
    ]
    
    endpoints_to_test = [
        "/api/stats",
        "/api/listings",
        "/api/listings?limit=10"
    ]
    
    logger.info("=== Testing Flask API Endpoints ===")
    
    # First, let's try to start the Flask app in the background
    import subprocess
    import time
    
    logger.info("Attempting to start Flask app...")
    try:
        # Try to start the Flask app
        flask_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's still running
        if flask_process.poll() is None:
            logger.info("Flask app appears to be running")
        else:
            logger.error("Flask app failed to start")
            stdout, stderr = flask_process.communicate()
            logger.error(f"Stdout: {stdout.decode()}")
            logger.error(f"Stderr: {stderr.decode()}")
            
    except Exception as e:
        logger.error(f"Failed to start Flask app: {e}")
        flask_process = None
    
    try:
        # Test the endpoints
        for url in urls_to_test:
            logger.info(f"\n--- Testing URL: {url} ---")
            for endpoint in endpoints_to_test:
                test_api_endpoint(url, endpoint)
                
    finally:
        # Clean up the Flask process
        if flask_process and flask_process.poll() is None:
            logger.info("Terminating Flask app")
            flask_process.terminate()
            time.sleep(1)
            if flask_process.poll() is None:
                flask_process.kill()

if __name__ == "__main__":
    main()
