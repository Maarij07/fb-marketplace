#!/usr/bin/env python3

from core.json_manager import JSONDataManager

def check_current_data():
    """Check current data in products.json."""
    jm = JSONDataManager()
    print(f"JSON path: {jm.json_path}")
    
    # Get recent products
    products = jm.get_recent_products(50)
    print(f"Total products count: {len(products)}")
    
    if products:
        print("\nFirst 10 products:")
        for i, p in enumerate(products[:10]):
            title = p.get("title", "NO TITLE")
            added_at = p.get("added_at", "Unknown")
            source = p.get("source", "Unknown")
            print(f"{i+1}. {title} (Added: {added_at[:19]}, Source: {source})")
        
        # Check for different sources
        sources = {}
        for p in products:
            source = p.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\nProducts by source: {sources}")
    else:
        print("No products found!")

if __name__ == "__main__":
    check_current_data()
