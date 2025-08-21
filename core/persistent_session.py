"""
Persistent Session Manager for Facebook Marketplace Automation

Maintains a single persistent browser session across multiple scraping operations
to improve UX and reduce login overhead.
"""

import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

from core.scraper import FacebookMarketplaceScraper


class PersistentBrowserSession:
    """
    Singleton-like class to manage persistent Facebook browser session.
    Maintains one browser instance across multiple scraping operations.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, settings=None):
        """Ensure singleton behavior."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, settings=None):
        """Initialize the persistent session manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.scraper = None
        self.session_active = False
        self.last_activity = None
        self.session_timeout = 1800  # 30 minutes timeout
        
        self._initialized = True
        self.logger.info("Persistent Browser Session Manager initialized")
    
    def start_session(self) -> bool:
        """
        Start or resume the persistent browser session.
        Returns True if session is ready, False if failed.
        """
        try:
            with self._lock:
                # Check if we need to create a new session
                if not self.session_active or not self._is_session_valid():
                    return self._create_new_session()
                else:
                    # Session exists and is valid
                    self.logger.info("Using existing persistent browser session")
                    self.last_activity = datetime.now()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to start persistent session: {e}")
            return False
    
    def _create_new_session(self) -> bool:
        """Create a new browser session and login to Facebook."""
        try:
            self.logger.info("Creating new persistent browser session...")
            
            # Clean up existing session if any
            self._cleanup_session()
            
            # Create new scraper with persistent session enabled
            self.scraper = FacebookMarketplaceScraper(
                self.settings, 
                persistent_session=True
            )
            
            # Initialize the session (setup driver, login, navigate to marketplace)
            if self.scraper.initialize_session():
                self.session_active = True
                self.last_activity = datetime.now()
                self.logger.info("Persistent browser session created and logged in successfully")
                return True
            else:
                self.logger.error("Failed to initialize persistent browser session")
                self._cleanup_session()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to create new persistent session: {e}")
            self._cleanup_session()
            return False
    
    def _is_session_valid(self) -> bool:
        """Check if the current session is still valid."""
        try:
            if not self.scraper or not self.scraper.driver:
                return False
            
            # Check if session has timed out
            if self.last_activity:
                time_since_last_activity = (datetime.now() - self.last_activity).total_seconds()
                if time_since_last_activity > self.session_timeout:
                    self.logger.info("Session timed out, will create new session")
                    return False
            
            # Check if browser is still responsive
            try:
                current_url = self.scraper.driver.current_url
                if not current_url:
                    return False
                    
                # Try to find a basic element to ensure page is loaded
                self.scraper.driver.find_element(By.TAG_NAME, "body")
                
                self.logger.debug("Session validation successful")
                return True
                
            except (WebDriverException, NoSuchElementException):
                self.logger.warning("Session validation failed - browser not responsive")
                return False
                
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return False
    
    def search_marketplace(self, search_query: str, notification_manager=None) -> list:
        """
        Perform a marketplace search using the persistent session.
        """
        try:
            if not self.start_session():
                self.logger.error("Could not establish persistent session for search")
                return []
            
            self.logger.info(f"Performing search for '{search_query}' using persistent session")
            
            # Set notification manager if provided
            if notification_manager and self.scraper:
                self.scraper.set_notification_manager(notification_manager)
            
            # Update activity timestamp
            self.last_activity = datetime.now()
            
            # Perform the search using existing session
            results = self.scraper.quick_search(search_query)
            
            self.logger.info(f"Search completed: found {len(results)} listings")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed in persistent session: {e}")
            # If search fails, mark session as invalid for next time
            self.session_active = False
            return []
    
    def run_default_scrape(self) -> list:
        """
        Run the default iPhone 16 scrape using persistent session.
        """
        try:
            if not self.start_session():
                self.logger.error("Could not establish persistent session for default scrape")
                return []
            
            self.logger.info("Running default scrape using persistent session")
            
            # Update activity timestamp
            self.last_activity = datetime.now()
            
            # Navigate to iPhone 16 search and scrape
            results = self.scraper.quick_search("iphone 16")
            
            self.logger.info(f"Default scrape completed: found {len(results)} listings")
            return results
            
        except Exception as e:
            self.logger.error(f"Default scrape failed in persistent session: {e}")
            # If scrape fails, mark session as invalid for next time
            self.session_active = False
            return []
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status information."""
        try:
            status = {
                'session_active': self.session_active,
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'browser_responsive': False,
                'current_url': None,
                'logged_in': False,
                'session_age_minutes': 0
            }
            
            if self.session_active and self.scraper and self.scraper.driver:
                try:
                    # Check browser responsiveness
                    status['current_url'] = self.scraper.driver.current_url
                    status['browser_responsive'] = True
                    
                    # Check login status
                    status['logged_in'] = self.scraper._is_logged_in()
                    
                    # Calculate session age
                    if self.last_activity:
                        age_seconds = (datetime.now() - self.last_activity).total_seconds()
                        status['session_age_minutes'] = round(age_seconds / 60, 1)
                        
                except Exception as e:
                    self.logger.debug(f"Error getting detailed session status: {e}")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get session status: {e}")
            return {'session_active': False, 'error': str(e)}
    
    def refresh_session(self) -> bool:
        """Force refresh the session by creating a new one."""
        self.logger.info("Manually refreshing persistent browser session")
        self.session_active = False
        return self.start_session()
    
    def _cleanup_session(self):
        """Clean up the current session."""
        try:
            if self.scraper:
                self.scraper.close_session()
                self.scraper = None
            
            self.session_active = False
            self.last_activity = None
            
        except Exception as e:
            self.logger.warning(f"Error during session cleanup: {e}")
    
    def close_session(self):
        """Explicitly close the persistent session."""
        self.logger.info("Closing persistent browser session")
        self._cleanup_session()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.close_session()
        except:
            pass


# Global instance for easy access
_persistent_session = None

def get_persistent_session(settings=None):
    """Get the global persistent session instance."""
    global _persistent_session
    if _persistent_session is None:
        _persistent_session = PersistentBrowserSession(settings)
    elif settings and not _persistent_session.settings:
        _persistent_session.settings = settings
    return _persistent_session
