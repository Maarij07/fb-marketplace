"""
Database Manager for Facebook Marketplace Automation

Handles SQLite database operations, schema management, and data persistence.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database operations for marketplace data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with path from settings."""
        from config.settings import Settings
        
        self.settings = Settings()
        self.db_path = db_path or self.settings.get('DATABASE_PATH', './data/marketplace.db')
        
        # Ensure database directory exists
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize database on first use
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Listings table - stores marketplace listing information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    price INTEGER,  -- Store price in cents to avoid float issues
                    currency TEXT DEFAULT 'USD',
                    seller_name TEXT,
                    seller_id TEXT,
                    seller_location TEXT,
                    listing_url TEXT,
                    image_url TEXT,
                    description TEXT,
                    category TEXT,
                    condition_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Price history table - tracks price changes over time
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    old_price INTEGER,
                    new_price INTEGER,
                    change_amount INTEGER,
                    change_percentage REAL,
                    change_type TEXT,  -- 'increase', 'decrease', 'new'
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings (listing_id)
                )
            """)
            
            # Scraping sessions table - tracks scraping runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT,  -- 'running', 'completed', 'failed'
                    listings_found INTEGER DEFAULT 0,
                    new_listings INTEGER DEFAULT 0,
                    updated_listings INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    search_keywords TEXT,
                    search_location TEXT,
                    error_details TEXT
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_id ON listings(listing_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_updated ON listings(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON scraping_sessions(start_time)")
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def save_listing(self, listing_data: Dict[str, Any]) -> bool:
        """Save or update a marketplace listing."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if listing already exists
                cursor.execute("SELECT price FROM listings WHERE listing_id = ?", 
                              (listing_data['listing_id'],))
                existing = cursor.fetchone()
                
                current_time = datetime.now().isoformat()
                
                if existing:
                    # Update existing listing
                    old_price = existing['price']
                    new_price = listing_data.get('price', 0)
                    
                    cursor.execute("""
                        UPDATE listings SET
                            title = ?, price = ?, seller_name = ?, seller_location = ?,
                            listing_url = ?, image_url = ?, description = ?,
                            category = ?, condition_text = ?, updated_at = ?, last_seen = ?
                        WHERE listing_id = ?
                    """, (
                        listing_data.get('title', ''),
                        new_price,
                        listing_data.get('seller_name', ''),
                        listing_data.get('seller_location', ''),
                        listing_data.get('listing_url', ''),
                        listing_data.get('image_url', ''),
                        listing_data.get('description', ''),
                        listing_data.get('category', ''),
                        listing_data.get('condition_text', ''),
                        current_time,
                        current_time,
                        listing_data['listing_id']
                    ))
                    
                    # Track price changes
                    if old_price != new_price and old_price is not None:
                        self._record_price_change(cursor, listing_data['listing_id'], 
                                                old_price, new_price)
                
                else:
                    # Insert new listing
                    cursor.execute("""
                        INSERT INTO listings (
                            listing_id, title, price, currency, seller_name, seller_id,
                            seller_location, listing_url, image_url, description,
                            category, condition_text, created_at, updated_at, last_seen
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        listing_data['listing_id'],
                        listing_data.get('title', ''),
                        listing_data.get('price', 0),
                        listing_data.get('currency', 'USD'),
                        listing_data.get('seller_name', ''),
                        listing_data.get('seller_id', ''),
                        listing_data.get('seller_location', ''),
                        listing_data.get('listing_url', ''),
                        listing_data.get('image_url', ''),
                        listing_data.get('description', ''),
                        listing_data.get('category', ''),
                        listing_data.get('condition_text', ''),
                        current_time,
                        current_time,
                        current_time
                    ))
                    
                    # Record as new listing
                    price = listing_data.get('price', 0)
                    if price:
                        self._record_price_change(cursor, listing_data['listing_id'], 
                                                None, price, 'new')
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save listing {listing_data.get('listing_id', 'unknown')}: {e}")
            return False
    
    def _record_price_change(self, cursor, listing_id: str, old_price: Optional[int], 
                           new_price: int, change_type: str = None):
        """Record a price change in the price history table."""
        if old_price is None:
            change_amount = 0
            change_percentage = 0.0
            change_type = change_type or 'new'
        else:
            change_amount = new_price - old_price
            change_percentage = (change_amount / old_price * 100) if old_price > 0 else 0.0
            
            if change_type is None:
                change_type = 'increase' if change_amount > 0 else 'decrease'
        
        cursor.execute("""
            INSERT INTO price_history (
                listing_id, old_price, new_price, change_amount, 
                change_percentage, change_type
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (listing_id, old_price, new_price, change_amount, change_percentage, change_type))
    
    def save_scraping_session(self, session_data: Dict[str, Any]) -> str:
        """Save scraping session information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                session_id = session_data.get('session_id', f"session_{datetime.now().isoformat()}")
                
                # Convert error_details list to string if needed
                error_details = session_data.get('error_details', [])
                if isinstance(error_details, list):
                    error_details = ', '.join(str(e) for e in error_details)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO scraping_sessions (
                        session_id, start_time, end_time, status, listings_found,
                        new_listings, updated_listings, errors_count,
                        search_keywords, search_location, error_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session_data.get('start_time', datetime.now().isoformat()),
                    session_data.get('end_time'),
                    session_data.get('status', 'running'),
                    session_data.get('listings_found', 0),
                    session_data.get('new_listings', 0),
                    session_data.get('updated_listings', 0),
                    session_data.get('errors_count', 0),
                    session_data.get('search_keywords', ''),
                    session_data.get('search_location', ''),
                    error_details
                ))
                
                conn.commit()
                return session_id
                
        except Exception as e:
            self.logger.error(f"Failed to save scraping session: {e}")
            return ""
    
    def get_recent_listings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent listings with price information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        listing_id, title, price, currency, seller_name, seller_location,
                        listing_url, image_url, category, condition_text,
                        created_at, updated_at, last_seen
                    FROM listings 
                    WHERE is_active = 1
                    ORDER BY updated_at DESC 
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get recent listings: {e}")
            return []
    
    def get_price_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent price changes."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        ph.listing_id, l.title, ph.old_price, ph.new_price,
                        ph.change_amount, ph.change_percentage, ph.change_type,
                        ph.detected_at, l.seller_name, l.listing_url
                    FROM price_history ph
                    JOIN listings l ON ph.listing_id = l.listing_id
                    WHERE ph.change_type != 'new'
                    ORDER BY ph.detected_at DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get price changes: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for dashboard."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total listings
                cursor.execute("SELECT COUNT(*) as count FROM listings WHERE is_active = 1")
                stats['total_listings'] = cursor.fetchone()['count']
                
                # Listings added today
                today = datetime.now().date()
                cursor.execute("""
                    SELECT COUNT(*) as count FROM listings 
                    WHERE DATE(created_at) = ? AND is_active = 1
                """, (today,))
                stats['listings_today'] = cursor.fetchone()['count']
                
                # Price changes
                cursor.execute("SELECT COUNT(*) as count FROM price_history WHERE change_type != 'new'")
                stats['price_changes'] = cursor.fetchone()['count']
                
                # Last successful scrape
                cursor.execute("""
                    SELECT start_time FROM scraping_sessions 
                    WHERE status = 'completed'
                    ORDER BY start_time DESC LIMIT 1
                """)
                last_scrape = cursor.fetchone()
                stats['last_scrape'] = last_scrape['start_time'] if last_scrape else 'Never'
                
                # Database size
                try:
                    db_size = os.path.getsize(self.db_path)
                    stats['db_size'] = f"{db_size / 1024:.1f} KB"
                except OSError:
                    stats['db_size'] = 'Unknown'
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def cleanup_old_data(self, retention_hours: int = 48) -> int:
        """Remove old data based on retention policy."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Mark old listings as inactive instead of deleting
                cursor.execute("""
                    UPDATE listings SET is_active = 0 
                    WHERE last_seen < ? AND is_active = 1
                """, (cutoff_time.isoformat(),))
                
                deactivated_listings = cursor.rowcount
                
                # Remove old scraping sessions
                cursor.execute("""
                    DELETE FROM scraping_sessions 
                    WHERE start_time < ?
                """, (cutoff_time.isoformat(),))
                
                deleted_sessions = cursor.rowcount
                
                # Remove old price history for inactive listings
                cursor.execute("""
                    DELETE FROM price_history 
                    WHERE listing_id IN (
                        SELECT listing_id FROM listings WHERE is_active = 0
                    ) AND detected_at < ?
                """, (cutoff_time.isoformat(),))
                
                deleted_price_history = cursor.rowcount
                
                conn.commit()
                
                total_cleaned = deactivated_listings + deleted_sessions + deleted_price_history
                self.logger.info(f"Cleanup completed: {total_cleaned} records processed")
                
                return total_cleaned
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def get_listings_by_keyword(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search listings by keyword."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                search_term = f"%{keyword}%"
                cursor.execute("""
                    SELECT * FROM listings 
                    WHERE (title LIKE ? OR description LIKE ?) 
                    AND is_active = 1
                    ORDER BY updated_at DESC 
                    LIMIT ?
                """, (search_term, search_term, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to search listings: {e}")
            return []
    
    def get_price_distribution(self) -> List[Tuple[int, int]]:
        """Get price distribution for charts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN price < 100 THEN '0-99'
                            WHEN price < 500 THEN '100-499'
                            WHEN price < 1000 THEN '500-999'
                            WHEN price < 2000 THEN '1000-1999'
                            ELSE '2000+'
                        END as price_range,
                        COUNT(*) as count
                    FROM listings 
                    WHERE is_active = 1 AND price > 0
                    GROUP BY price_range
                    ORDER BY 
                        CASE price_range
                            WHEN '0-99' THEN 1
                            WHEN '100-499' THEN 2
                            WHEN '500-999' THEN 3
                            WHEN '1000-1999' THEN 4
                            ELSE 5
                        END
                """)
                
                return [(row['price_range'], row['count']) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get price distribution: {e}")
            return []
