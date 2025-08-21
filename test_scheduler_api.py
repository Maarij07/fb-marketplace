#!/usr/bin/env python3
"""
Test script for multi-scheduler API endpoints
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_scheduler_api():
    """Test the scheduler API endpoints"""
    
    print("Testing multi-scheduler API endpoints...")
    
    try:
        # Test 1: Get current schedulers
        print("\n1. Getting current schedulers...")
        response = requests.get(f"{BASE_URL}/api/schedulers")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: Found {len(data['data'])} schedulers")
            for scheduler in data['data']:
                print(f"   - Scheduler {scheduler['id']}: {scheduler['search_query']} ({scheduler['city']}) - {'Running' if scheduler['is_running'] else 'Stopped'}")
        else:
            print(f"   Failed: {response.status_code}")
        
        # Test 2: Create a new scheduler
        print("\n2. Creating a new scheduler...")
        new_scheduler = {
            "search_query": "macbook pro",
            "city": "Stockholm", 
            "interval_minutes": 30
        }
        response = requests.post(f"{BASE_URL}/api/scheduler/create", json=new_scheduler)
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data['message']}")
        else:
            print(f"   Failed: {response.status_code}")
        
        # Test 3: Get schedulers again to see the new one
        print("\n3. Getting schedulers after creation...")
        response = requests.get(f"{BASE_URL}/api/schedulers")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: Found {len(data['data'])} schedulers")
            for scheduler in data['data']:
                print(f"   - Scheduler {scheduler['id']}: {scheduler['search_query']} ({scheduler['city']}) - {'Running' if scheduler['is_running'] else 'Stopped'}")
        
        # Test 4: Pause a scheduler
        if data['data']:
            scheduler_id = data['data'][0]['id']
            print(f"\n4. Pausing scheduler {scheduler_id}...")
            response = requests.post(f"{BASE_URL}/api/scheduler/{scheduler_id}/pause")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result['message']}")
            else:
                print(f"   Failed: {response.status_code}")
        
        # Test 5: Start a scheduler
        if data['data']:
            scheduler_id = data['data'][0]['id']
            print(f"\n5. Starting scheduler {scheduler_id}...")
            response = requests.post(f"{BASE_URL}/api/scheduler/{scheduler_id}/start")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result['message']}")
            else:
                print(f"   Failed: {response.status_code}")
        
        # Test 6: Delete a scheduler
        if data['data']:
            scheduler_id = data['data'][0]['id']
            print(f"\n6. Deleting scheduler {scheduler_id}...")
            response = requests.delete(f"{BASE_URL}/api/scheduler/{scheduler_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result['message']}")
            else:
                print(f"   Failed: {response.status_code}")
        
        print("\nAPI test completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to dashboard. Make sure it's running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scheduler_api()
