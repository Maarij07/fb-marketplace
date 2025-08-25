#!/usr/bin/env python3

import json
import sys
sys.path.insert(0, '.')
from core.json_manager import JSONDataManager

# Load data directly
manager = JSONDataManager()
data = manager.load_data()

print(f"Total products in JSON: {len(data['products'])}")
print()

# Check first 10 products
for i, product in enumerate(data['products'][:10], 1):
    title = product.get('title', 'NO TITLE')[:50]
    price = product.get('price', {})
    amount = price.get('amount', 'N/A')
    currency = price.get('currency', '')
    added_at = product.get('added_at', 'NO TIME')
    
    print(f"{i}. {title}... | {amount} {currency} | Added: {added_at}")

print()

# Test get_recent_products method specifically
recent = manager.get_recent_products(10)
print(f"Recent products returned by get_recent_products(): {len(recent)}")

for i, product in enumerate(recent[:5], 1):
    title = product.get('title', 'NO TITLE')[:50]
    price = product.get('price', {})
    amount = price.get('amount', 'N/A')
    currency = price.get('currency', '')
    
    print(f"  {i}. {title}... | {amount} {currency}")
