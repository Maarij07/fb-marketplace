"""
JSON-based Data Manager for Facebook Marketplace Automation

Handles JSON file operations, data persistence, and duplicate prevention.
Replaces database operations with JSON storage.
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class JSONDataManager:
    """Manages JSON-based data operations for marketplace data."""
    
    def __init__(self, json_path: Optional[str] = None):
        """Initialize JSON data manager with file path."""
        from config.settings import Settings
        
        self.settings = Settings()
        self.json_path = json_path or './products.json'
        
        # Ensure data directory exists
        json_dir = os.path.dirname(os.path.abspath(self.json_path))
        os.makedirs(json_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize JSON file if it doesn't exist
        self.initialize_json_file()
    
    def initialize_json_file(self):
        """Create JSON file with default structure if it doesn't exist."""
        if not os.path.exists(self.json_path):
            default_data = {
                "extraction_info": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Facebook Marketplace Stockholm",
                    "search_query": "iPhone 16",
                    "total_products_found": 0,
                    "extraction_method": "automated_scraper"
                },
                "summary": {
                    "products_with_complete_data": 0,
                    "products_with_images": 0,
                    "products_with_links": 0,
                    "products_with_locations": 0,
                    "products_with_prices": 0,
                    "unique_locations": []
                },
                "products": [],
                "scraping_sessions": [],
                "extraction_notes": {
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "Facebook Marketplace",
                    "deduplication": "Based on listing ID and title similarity"
                }
            }
            
            self.save_data(default_data)
            self.logger.info("Initialized new products.json file")
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load JSON data: {e}")
            self.initialize_json_file()
            return self.load_data()
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to JSON file."""
        try:
            # Update extraction info timestamp
            data["extraction_info"]["timestamp"] = datetime.now().strftime("%Y-%m-%d")
            data["extraction_notes"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save JSON data: {e}")
            return False
    
    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """Add a single product with duplicate checking."""
        data = self.load_data()
        
        # Check for duplicates
        if self.is_duplicate(product_data, data["products"]):
            self.logger.debug(f"Duplicate product skipped: {product_data.get('title', 'Unknown')}")
            return False
        
        # Add unique ID if not present
        if not product_data.get('id'):
            product_data['id'] = self.generate_product_id(product_data)
        
        # Add timestamp
        product_data['added_at'] = datetime.now().isoformat()
        product_data['source'] = 'facebook_marketplace_scraper'
        
        # Add to products list
        data["products"].append(product_data)
        
        # Update summary
        self.update_summary(data)
        
        # Save updated data
        success = self.save_data(data)
        if success:
            self.logger.info(f"Added new product: {product_data.get('title', 'Unknown')}")
        
        return success
    
    def add_products_batch(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Add multiple products with duplicate checking."""
        data = self.load_data()
        stats = {
            'added': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        for product_data in products:
            try:
                # Check for duplicates
                if self.is_duplicate(product_data, data["products"]):
                    stats['duplicates'] += 1
                    continue
                
                # Add unique ID if not present
                if not product_data.get('id'):
                    product_data['id'] = self.generate_product_id(product_data)
                
                # Add metadata
                product_data['added_at'] = datetime.now().isoformat()
                product_data['source'] = 'facebook_marketplace_scraper'
                
                # Add to products list
                data["products"].append(product_data)
                stats['added'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process product: {e}")
                stats['errors'] += 1
                continue
        
        # Update summary
        self.update_summary(data)
        
        # Save updated data
        if self.save_data(data):
            self.logger.info(f"Batch operation completed: {stats['added']} added, {stats['duplicates']} duplicates, {stats['errors']} errors")
        
        return stats
    
    def is_duplicate(self, new_product: Dict[str, Any], existing_products: List[Dict[str, Any]]) -> bool:
        """Check if a product is a duplicate based on ID and title similarity."""
        new_id = new_product.get('id')
        new_title = new_product.get('title', '').lower().strip()
        new_url = new_product.get('marketplace_url', '').strip()
        
        for existing in existing_products:
            existing_id = existing.get('id')
            existing_title = existing.get('title', '').lower().strip()
            existing_url = existing.get('marketplace_url', '').strip()
            
            # Check exact ID match
            if new_id and existing_id and new_id == existing_id:
                return True
            
            # Check exact URL match
            if new_url and existing_url and new_url == existing_url:
                return True
            
            # Check title similarity (exact match after normalization)
            if new_title and existing_title:
                # Remove common variations and check similarity
                clean_new = self.normalize_title(new_title)
                clean_existing = self.normalize_title(existing_title)
                
                if clean_new == clean_existing:
                    return True
                
                # Check if titles are very similar (90%+ match)
                similarity = self.calculate_similarity(clean_new, clean_existing)
                if similarity > 0.9:
                    return True
        
        return False
    
    def normalize_title(self, title: str) -> str:
        """Normalize product title for comparison."""
        import re
        
        title = title.lower().strip()
        
        # Remove common variations
        title = re.sub(r'\s+', ' ', title)  # Multiple spaces to single
        title = re.sub(r'[^\w\s]', '', title)  # Remove special characters
        title = re.sub(r'\b(new|used|like new|excellent|good condition)\b', '', title)
        title = re.sub(r'\b(in|i|från|from)\s+\w+\b', '', title)  # Remove location indicators
        title = title.strip()
        
        return title
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Simple similarity based on common words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def generate_product_id(self, product_data: Dict[str, Any]) -> str:
        """Generate unique product ID."""
        # Try to extract from URL first
        url = product_data.get('marketplace_url', '')
        if '/marketplace/item/' in url:
            import re
            match = re.search(r'/marketplace/item/(\d+)', url)
            if match:
                return f"mp_{match.group(1)}"
        
        # Generate based on title and timestamp
        title = product_data.get('title', 'unknown')
        timestamp = str(int(datetime.now().timestamp()))
        
        # Create hash-like ID
        import hashlib
        hash_input = f"{title}_{timestamp}".encode('utf-8')
        hash_digest = hashlib.md5(hash_input).hexdigest()[:8]
        
        return f"mp_gen_{hash_digest}"
    
    def update_summary(self, data: Dict[str, Any]):
        """Update summary statistics."""
        products = data["products"]
        
        summary = {
            "products_with_complete_data": 0,
            "products_with_images": 0,
            "products_with_links": 0,
            "products_with_locations": 0,
            "products_with_prices": 0,
            "unique_locations": []
        }
        
        locations = set()
        
        for product in products:
            # Complete data (has title, price, and either image or URL)
            if (product.get('title') and 
                product.get('price', {}).get('amount') and
                (product.get('images') or product.get('marketplace_url'))):
                summary["products_with_complete_data"] += 1
            
            # Has images
            if product.get('images') and len(product.get('images', [])) > 0:
                summary["products_with_images"] += 1
            
            # Has links
            if product.get('marketplace_url'):
                summary["products_with_links"] += 1
            
            # Has location
            location = product.get('location', {}).get('city', '').strip()
            if location and location.lower() not in ['unknown', 'x', '']:
                summary["products_with_locations"] += 1
                locations.add(location)
            
            # Has price
            if product.get('price', {}).get('amount'):
                summary["products_with_prices"] += 1
        
        summary["unique_locations"] = sorted(list(locations))
        data["summary"] = summary
        data["extraction_info"]["total_products_found"] = len(products)
    
    def get_recent_products(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent products for dashboard display."""
        data = self.load_data()
        products = data.get("products", [])
        
        # Sort by added_at timestamp (most recent first)
        sorted_products = sorted(
            products,
            key=lambda x: x.get('added_at', '1970-01-01T00:00:00'),
            reverse=True
        )
        
        return sorted_products[:limit]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for dashboard."""
        data = self.load_data()
        
        total_products = len(data.get("products", []))
        
        # Count today's products
        today = datetime.now().strftime("%Y-%m-%d")
        today_products = len([
            p for p in data.get("products", [])
            if p.get('added_at', '').startswith(today)
        ])
        
        # Get last scraping session
        sessions = data.get("scraping_sessions", [])
        last_scrape = "Never"
        if sessions:
            last_session = max(sessions, key=lambda x: x.get('start_time', ''))
            last_scrape = last_session.get('start_time', 'Never')
        
        # File size
        try:
            file_size = os.path.getsize(self.json_path)
            file_size_str = f"{file_size / 1024:.1f} KB"
        except OSError:
            file_size_str = "Unknown"
        
        return {
            'total_listings': total_products,
            'listings_today': today_products,
            'price_changes': 0,  # Not tracked in JSON version
            'last_scrape': last_scrape,
            'db_size': file_size_str
        }
    
    def save_scraping_session(self, session_data: Dict[str, Any]) -> bool:
        """Save scraping session information."""
        try:
            data = self.load_data()
            
            # Initialize sessions list if not present
            if "scraping_sessions" not in data:
                data["scraping_sessions"] = []
            
            # Add session with timestamp
            session_data['saved_at'] = datetime.now().isoformat()
            data["scraping_sessions"].append(session_data)
            
            # Keep only last 50 sessions
            data["scraping_sessions"] = data["scraping_sessions"][-50:]
            
            return self.save_data(data)
            
        except Exception as e:
            self.logger.error(f"Failed to save scraping session: {e}")
            return False
    
    def search_products(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search products by keyword."""
        data = self.load_data()
        products = data.get("products", [])
        
        keyword_lower = keyword.lower().strip()
        matches = []
        
        for product in products:
            title = product.get('title', '').lower()
            description = product.get('description', '').lower()
            
            if keyword_lower in title or keyword_lower in description:
                matches.append(product)
        
        return matches[:limit]
