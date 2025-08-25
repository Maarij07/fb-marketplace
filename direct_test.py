#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

try:
    from web.app import create_app
    from config.settings import Settings
    print("✓ Imports successful")

    settings = Settings()
    app = create_app(settings)
    print("✓ Flask app created successfully")

    # Test within app context
    with app.app_context():
        with app.test_client() as client:
            print("\n=== Testing /api/stats ===")
            stats_response = client.get('/api/stats')
            print(f"Status: {stats_response.status_code}")
            
            if stats_response.status_code == 200:
                stats_data = stats_response.get_json()
                print(f"Response: {stats_data}")
                print(f"Success: {stats_data.get('success', False)}")
                if stats_data.get('success'):
                    data = stats_data.get('data', {})
                    print(f"Total listings: {data.get('total_listings', 'N/A')}")
                else:
                    print(f"Error: {stats_data.get('error', 'Unknown error')}")
            else:
                print(f"Error response: {stats_response.get_data(as_text=True)}")
            
            print("\n=== Testing /api/listings ===")
            listings_response = client.get('/api/listings?limit=5')
            print(f"Status: {listings_response.status_code}")
            
            if listings_response.status_code == 200:
                listings_data = listings_response.get_json()
                print(f"Success: {listings_data.get('success', False)}")
                if listings_data.get('success'):
                    listings = listings_data.get('data', [])
                    print(f"Number of listings returned: {len(listings)}")
                    for i, listing in enumerate(listings[:3], 1):
                        title = listing.get('title', 'NO TITLE')[:50]
                        price_display = listing.get('price_display', 'N/A')
                        print(f"  {i}. {title}... | {price_display}")
                else:
                    print(f"Error: {listings_data.get('error', 'Unknown error')}")
            else:
                print(f"Error response: {listings_response.get_data(as_text=True)}")

except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    print(traceback.format_exc())
