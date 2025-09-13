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
        """Load data from JSON file with retry mechanism for concurrent access."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        if attempt == max_retries - 1:
                            self.logger.warning("JSON file is empty, initializing...")
                            self.initialize_json_file()
                            return self.load_data()
                        else:
                            import time
                            time.sleep(0.1)  # Brief delay for concurrent access
                            continue
                    data = json.loads(content)
                return data
            except (FileNotFoundError, json.JSONDecodeError) as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to load JSON data after {max_retries} attempts: {e}")
                    self.initialize_json_file()
                    return self.load_data()
                else:
                    self.logger.debug(f"JSON load attempt {attempt + 1} failed, retrying: {e}")
                    import time
                    time.sleep(0.1)
                    continue
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to JSON file with atomic write and retry mechanism."""
        import tempfile
        import shutil
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Update extraction info timestamp
                data["extraction_info"]["timestamp"] = datetime.now().strftime("%Y-%m-%d")
                data["extraction_notes"]["last_updated"] = datetime.now().isoformat()
                
                # Atomic write using temporary file
                temp_path = None
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                               dir=os.path.dirname(self.json_path), 
                                               delete=False, encoding='utf-8') as temp_file:
                    temp_path = temp_file.name
                    json.dump(data, temp_file, indent=2, ensure_ascii=False)
                    temp_file.flush()  # Ensure data is written to disk
                    os.fsync(temp_file.fileno())  # Force write to disk
                
                # Move temp file to final location (atomic operation)
                shutil.move(temp_path, self.json_path)
                return True
                
            except Exception as e:
                # Clean up temp file if it exists
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
                
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to save JSON data after {max_retries} attempts: {e}")
                    return False
                else:
                    self.logger.debug(f"JSON save attempt {attempt + 1} failed, retrying: {e}")
                    import time
                    time.sleep(0.1)
                    continue
    
    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """Add a single product with duplicate checking."""
        data = self.load_data()
        
        # Validate title first
        title = product_data.get('title', '').strip()
        if not self._is_valid_title(title):
            self.logger.warning(f"Skipping product with invalid title: '{title}'")
            return False
        
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
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if a title is valid for a product listing."""
        if not title or len(title.strip()) <= 3:
            return False
        
        title = title.strip()
        
        # Invalid titles to filter out
        import re
        invalid_patterns = [
            r'^SEK\d+',  # SEK followed by numbers
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
        
        # Valid titles should contain meaningful text (at least one letter)
        if not any(c.isalpha() for c in title):
            return False
        
        return True
    
    def add_product_hot_reload(self, product_data: Dict[str, Any]) -> bool:
        """🔥 HOT RELOAD: Add product immediately without extensive validation for real-time updates."""
        data = self.load_data()
        
        # Minimal title validation - just check it exists and isn't empty
        title = product_data.get('title', '').strip()
        if not title or len(title) < 2:
            self.logger.warning(f"Hot reload: Skipping product with empty/too short title: '{title}'")
            return False
        
        # Relaxed duplicate checking - only check exact ID matches
        new_id = product_data.get('id')
        if new_id:
            for existing in data["products"]:
                if existing.get('id') == new_id:
                    self.logger.debug(f"Hot reload: Duplicate ID found, skipping: {new_id}")
                    return False
        
        # Add unique ID if not present
        if not product_data.get('id'):
            product_data['id'] = self.generate_product_id(product_data)
        
        # Add hot reload metadata
        current_time = datetime.now().isoformat()
        product_data['added_at'] = current_time
        product_data['created_at'] = current_time
        product_data['source'] = 'facebook_marketplace_scraper'
        product_data['hot_reload'] = True
        product_data['hot_reload_timestamp'] = current_time
        
        # Add to products list (at the beginning for immediate visibility)
        data["products"].insert(0, product_data)
        
        # Update summary
        self.update_summary(data)
        
        # Save immediately without cleanup
        success = self.save_data(data)
        if success:
            self.logger.info(f"🔥 Hot reload: Added product immediately: {product_data.get('title', 'Unknown')[:50]}...")
        else:
            self.logger.error(f"🔥 Hot reload: Failed to save product: {product_data.get('title', 'Unknown')[:50]}...")
        
        return success
    
    def add_products_batch(self, products: List[Dict[str, Any]], skip_cleanup: bool = False) -> Dict[str, int]:
        """Add multiple products with duplicate checking."""
        data = self.load_data()
        
        # Cleanup old data before adding new products (skip for hot reload)
        if not skip_cleanup:
            self.cleanup_old_data(data)
        
        stats = {
            'added': 0,
            'duplicates': 0,
            'errors': 0,
            'invalid_titles': 0
        }
        
        for product_data in products:
            try:
                # Validate title first
                title = product_data.get('title', '').strip()
                if not self._is_valid_title(title):
                    self.logger.warning(f"Skipping product with invalid title: '{title}'")
                    stats['invalid_titles'] += 1
                    continue
                
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
        new_title = (new_product.get('title') or '').lower().strip()
        new_url = (new_product.get('marketplace_url') or '').strip()
        
        for existing in existing_products:
            existing_id = existing.get('id')
            existing_title = (existing.get('title') or '').lower().strip()
            existing_url = (existing.get('marketplace_url') or '').strip()
            
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
        
        # DO NOT modify existing data - just return it
        # The posted_date and created_at fields should be preserved as-is
        
        # Sort by created_at or added_at timestamp (most recent first)
        sorted_products = sorted(
            products,
            key=lambda x: x.get('created_at', x.get('added_at', '1970-01-01T00:00:00')),
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
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by its ID."""
        data = self.load_data()
        products = data.get("products", [])
        
        for product in products:
            if product.get('id') == product_id:
                return product
        
        return None
    
    def cleanup_old_data(self, data: Dict[str, Any], retention_hours: int = 48) -> int:
        """Remove products older than retention period."""
        try:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            products = data.get("products", [])
            sessions = data.get("scraping_sessions", [])
            
            # Filter out old products
            original_count = len(products)
            data["products"] = [
                product for product in products
                if self._is_product_recent(product, cutoff_time)
            ]
            removed_products = original_count - len(data["products"])
            
            # Filter out old sessions
            original_sessions = len(sessions)
            data["scraping_sessions"] = [
                session for session in sessions
                if self._is_session_recent(session, cutoff_time)
            ]
            removed_sessions = original_sessions - len(data["scraping_sessions"])
            
            total_removed = removed_products + removed_sessions
            
            if total_removed > 0:
                self.logger.info(f"Cleaned up {removed_products} old products and {removed_sessions} old sessions")
                # Update summary after cleanup
                self.update_summary(data)
            
            return total_removed
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def safe_cleanup_unwanted_variants(self, search_query: str, max_age_minutes: int = 60) -> Dict[str, int]:
        """🔥 SAFETY NET: Remove unwanted variants from current scraping session only.
        
        Args:
            search_query: Current search query (e.g., "iPhone 14", "iPhone 14 Plus")
            max_age_minutes: Only clean products added in the last N minutes (default: 60 min)
            
        Returns:
            Dict with cleanup statistics
        """
        try:
            from datetime import datetime, timedelta
            from core.product_filter import SmartProductFilter
            
            data = self.load_data()
            products = data.get("products", [])
            
            if not products:
                return {'removed': 0, 'kept': len(products), 'error': None}
            
            # Calculate cutoff time for current session safety
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            
            # Initialize product filter
            product_filter = SmartProductFilter()
            
            # Separate recent products (current session) from old products (keep unchanged)
            recent_products = []
            old_products = []
            
            for product in products:
                if self._is_product_from_current_session(product, cutoff_time):
                    recent_products.append(product)
                else:
                    old_products.append(product)
            
            self.logger.info(f"🛡️ Variant cleanup: Found {len(recent_products)} recent products and {len(old_products)} older products")
            
            if not recent_products:
                self.logger.info(f"🛡️ No recent products to check for variants")
                return {'removed': 0, 'kept': len(products), 'error': None, 'recent_products': 0}
            
            # Apply smart filtering ONLY to recent products
            self.logger.info(f"🛡️ Applying variant cleanup to recent products for search: '{search_query}'")
            
            filtered_recent, excluded_recent = product_filter.filter_product_list(recent_products, search_query)
            
            # Count what was removed
            removed_count = len(excluded_recent)
            kept_recent = len(filtered_recent)
            
            # Log cleanup results
            if excluded_recent:
                filter_stats = product_filter.get_filter_statistics(excluded_recent)
                self.logger.info(f"🛡️ Variant cleanup results: {kept_recent} recent products kept, {removed_count} removed")
                self.logger.info(f"🛡️ Removal reasons: {filter_stats}")
                
                # Log some examples of removed products
                self.logger.info(f"🛡️ Sample removed products:")
                for i, removed in enumerate(excluded_recent[:3]):
                    title = removed.get('title', 'Unknown')[:60]
                    reason = removed.get('exclusion_reason', 'Unknown reason')
                    self.logger.info(f"  {i+1}. {title}... - Reason: {reason}")
            else:
                self.logger.info(f"🛡️ No unwanted variants found in recent products")
            
            # Combine old products (unchanged) + filtered recent products
            data["products"] = old_products + filtered_recent
            
            # Update summary and save
            self.update_summary(data)
            
            if removed_count > 0:
                success = self.save_data(data)
                if success:
                    self.logger.info(f"🛡️ Successfully cleaned up {removed_count} unwanted variants from recent session")
                else:
                    self.logger.error(f"🛡️ Failed to save after variant cleanup")
                    return {'removed': 0, 'kept': len(products), 'error': 'Failed to save after cleanup'}
            
            return {
                'removed': removed_count,
                'kept': len(data["products"]),
                'recent_products': len(recent_products),
                'old_products_preserved': len(old_products),
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"🛡️ Variant cleanup failed: {e}")
            return {'removed': 0, 'kept': len(data.get("products", [])), 'error': str(e)}
    
    def _is_product_from_current_session(self, product: Dict[str, Any], cutoff_time: datetime) -> bool:
        """Check if product is from current scraping session (within time window)."""
        try:
            # Check multiple timestamp fields
            timestamp_fields = ['added_at', 'hot_reload_timestamp', 'created_at']
            
            for field in timestamp_fields:
                timestamp_str = product.get(field, '')
                if timestamp_str:
                    try:
                        # Parse ISO format timestamp
                        if 'T' in timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            # Remove timezone info for comparison if present
                            if timestamp.tzinfo is not None:
                                timestamp = timestamp.replace(tzinfo=None)
                            
                            # If this product is newer than cutoff, it's from current session
                            if timestamp >= cutoff_time:
                                return True
                    except (ValueError, TypeError):
                        continue
            
            # If we can't parse any timestamps or all are too old, treat as old product
            return False
            
        except Exception as e:
            # If any error, treat as old product to be safe
            return False
    
    def _is_product_recent(self, product: Dict[str, Any], cutoff_time: datetime) -> bool:
        """Check if product is recent enough to keep."""
        try:
            added_at_str = product.get('added_at', '')
            if not added_at_str:
                # If no timestamp, keep the product (could be legacy data)
                return True
            
            # Parse the timestamp
            if 'T' in added_at_str:
                # ISO format
                added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
            else:
                # Simple date format
                added_at = datetime.strptime(added_at_str, '%Y-%m-%d')
            
            # Remove timezone info for comparison if present
            if added_at.tzinfo is not None:
                added_at = added_at.replace(tzinfo=None)
            
            return added_at >= cutoff_time
            
        except Exception as e:
            self.logger.debug(f"Could not parse timestamp for product {product.get('id', 'unknown')}: {e}")
            # If we can't parse the timestamp, keep the product to be safe
            return True
    
    def _is_session_recent(self, session: Dict[str, Any], cutoff_time: datetime) -> bool:
        """Check if scraping session is recent enough to keep."""
        try:
            start_time_str = session.get('start_time', '')
            if not start_time_str:
                return True
            
            # Parse the timestamp
            if 'T' in start_time_str:
                # ISO format
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            else:
                # Simple date format
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d')
            
            # Remove timezone info for comparison if present
            if start_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=None)
            
            return start_time >= cutoff_time
            
        except Exception as e:
            self.logger.debug(f"Could not parse timestamp for session: {e}")
            # If we can't parse the timestamp, keep the session to be safe
            return True
