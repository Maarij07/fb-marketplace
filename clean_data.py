#!/usr/bin/env python3
"""
Data cleanup script for Facebook Marketplace JSON

Removes entries with invalid titles that contain only price information
and other non-product-related text.
"""

import json
import re
from datetime import datetime


def is_valid_title(title):
    """Check if a title is a valid product title."""
    if not title or len(title.strip()) <= 3:
        return False
    
    title = title.strip()
    
    # Invalid titles to filter out
    invalid_patterns = [
        r'^SEK\d+',  # SEK followed by numbers (like "SEK6,500")
        r'^\$\d+',   # Dollar sign followed by numbers
        r'^\d+\s*kr',  # Numbers followed by "kr"
        r'^Create new listing$',  # Facebook UI text
        r'^Loading',  # Loading states
        r'^\d+$',     # Pure numbers
        r'^[\d,]+$',  # Numbers with commas only
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, title, re.IGNORECASE):
            return False
    
    # Additional checks
    if title.lower().startswith('sek') and any(c.isdigit() for c in title):
        return False
    
    if title.replace(',', '').replace('.', '').isdigit():
        return False
    
    # Valid titles should contain meaningful text
    # At least one letter
    if not any(c.isalpha() for c in title):
        return False
    
    return True


def clean_products_json():
    """Clean the products JSON file."""
    file_path = "products.json"
    
    try:
        # Read current data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        original_count = len(products)
        
        print(f"Original product count: {original_count}")
        
        # Filter out products with invalid titles
        valid_products = []
        removed_count = 0
        
        for product in products:
            title = product.get('title', '')
            if is_valid_title(title):
                valid_products.append(product)
            else:
                removed_count += 1
                print(f"Removing invalid title: '{title[:50]}...'")
        
        # Update the data
        data['products'] = valid_products
        data['extraction_info']['total_products_found'] = len(valid_products)
        data['extraction_info']['timestamp'] = datetime.now().strftime('%Y-%m-%d')
        data['extraction_info']['last_cleaned'] = datetime.now().isoformat()
        
        # Recalculate summary
        data['summary']['products_with_complete_data'] = len([
            p for p in valid_products 
            if p.get('title') and p.get('price', {}).get('amount') and p.get('location', {}).get('city')
        ])
        data['summary']['products_with_images'] = len([
            p for p in valid_products if p.get('images')
        ])
        data['summary']['products_with_links'] = len([
            p for p in valid_products if p.get('marketplace_url')
        ])
        data['summary']['products_with_locations'] = len([
            p for p in valid_products if p.get('location', {}).get('city', 'Unknown') != 'Unknown'
        ])
        data['summary']['products_with_prices'] = len([
            p for p in valid_products if p.get('price', {}).get('amount', '0') != '0'
        ])
        
        # Update unique locations
        locations = set()
        for product in valid_products:
            city = product.get('location', {}).get('city', 'Unknown')
            if city and city != 'Unknown':
                locations.add(city)
        data['summary']['unique_locations'] = sorted(list(locations))
        
        # Save cleaned data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCleaning completed!")
        print(f"Removed {removed_count} invalid entries")
        print(f"Kept {len(valid_products)} valid products")
        print(f"New total: {len(valid_products)} products")
        
        return True
        
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return False


if __name__ == "__main__":
    print("Starting Facebook Marketplace data cleanup...")
    success = clean_products_json()
    if success:
        print("✅ Data cleanup completed successfully!")
    else:
        print("❌ Data cleanup failed!")
