"""
Browser-Based Notification Monitoring Service for Facebook Marketplace

Automatically opens Chrome, logs into Facebook, and monitors for notifications
that indicate price changes, new listings, and other marketplace activity.
"""

import time
import threading
import logging
import random
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class NotificationMonitor:
    """
    Browser-based notification monitoring service.
    
    Opens a persistent Chrome window, logs into Facebook, and continuously
    monitors for marketplace notifications and price changes.
    """
    
    def __init__(self, settings, notification_callback: Optional[Callable] = None):
        """Initialize the notification monitor."""
        self.settings = settings
        self.notification_callback = notification_callback
        self.logger = logging.getLogger(__name__)
        
        # Browser and monitoring state
        self.driver = None
        self.monitoring_active = False
        self.monitor_thread = None
        self.stop_monitoring = False
        
        # Configuration
        self.config = {
            'check_interval': 30,  # Check every 30 seconds
            'notification_selectors': [
                # Facebook notification selectors
                '[aria-label*="Notifications"]',
                '[data-testid="notification"]',
                '.notification-item',
                # Marketplace-specific selectors
                '[aria-label*="Marketplace"]',
                '.marketplace-notification',
                # Price change indicators
                '[data-testid*="price"]',
                '.price-change',
                '.discount-badge'
            ],
            'price_change_keywords': [
                'price reduced', 'price dropped', 'now', 'sale', 'discount',
                'lower price', 'markdown', 'clearance', 'deal'
            ]
        }
        
        self.logger.info("Notification Monitor initialized")
    
    def start_monitoring(self) -> bool:
        """
        Start the browser-based notification monitoring.
        
        Returns:
            bool: True if monitoring started successfully, False otherwise
        """
        try:
            if self.monitoring_active:
                self.logger.info("Notification monitoring already active")
                return True
            
            self.logger.info("🔔 Starting browser-based notification monitoring...")
            
            # Initialize Chrome browser
            if not self._setup_browser():
                return False
            
            # Login to Facebook
            if not self._login_to_facebook():
                self._cleanup_browser()
                return False
            
            # Navigate to Notifications
            if not self._navigate_to_notifications():
                self._cleanup_browser() 
                return False
            
            # Start monitoring thread
            self._start_monitoring_thread()
            
            self.monitoring_active = True
            self.logger.info("✅ Notification monitoring started successfully!")
            
            # Send initial notification
            if self.notification_callback:
                self.notification_callback({
                    'type': 'monitoring_started',
                    'data': {
                        'message': 'Browser notification monitoring is now active',
                        'timestamp': datetime.now().isoformat(),
                        'url': self.driver.current_url if self.driver else None
                    }
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start notification monitoring: {e}")
            self._cleanup_browser()
            return False
    
    def stop_monitoring(self):
        """Stop the notification monitoring."""
        try:
            self.logger.info("🛑 Stopping notification monitoring...")
            
            self.stop_monitoring = True
            self.monitoring_active = False
            
            # Wait for monitoring thread to stop
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            # Cleanup browser
            self._cleanup_browser()
            
            self.logger.info("✅ Notification monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping notification monitoring: {e}")
    
    def _setup_browser(self) -> bool:
        """Setup Chrome browser for monitoring."""
        try:
            self.logger.info("🌐 Setting up Chrome browser...")
            
            chrome_options = Options()
            
            # Browser configuration for monitoring
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Enable notifications
            prefs = {
                "profile.default_content_setting_values.notifications": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome browser setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser: {e}")
            return False
    
    def _human_type(self, element, text: str):
        """Type text character by character with human-like delays."""
        for char in text:
            element.send_keys(char)
            # Random delay between 50-150ms with occasional longer pauses
            base_delay = random.uniform(0.05, 0.15)
            if random.random() < 0.1:  # 10% chance of longer pause
                base_delay += random.uniform(0.2, 0.5)
            time.sleep(base_delay)
    
    def _login_to_facebook(self) -> bool:
        """Login to Facebook."""
        try:
            self.logger.info("🔐 Logging into Facebook...")
            
            # Navigate to Facebook main page (same as scraper to get consistent layout)
            self.driver.get('https://www.facebook.com')
            time.sleep(3)
            
            # Get credentials from settings (supports both env vars and config.json)
            fb_email = self.settings.get('FACEBOOK_EMAIL')
            fb_password = self.settings.get('FACEBOOK_PASSWORD')
            
            self.logger.info(f"Email found: {'Yes' if fb_email else 'No'}")
            self.logger.info(f"Password found: {'Yes' if fb_password else 'No'}")
            
            if not fb_email or not fb_password:
                self.logger.error("Facebook credentials not found in settings. Please check FACEBOOK_EMAIL and FACEBOOK_PASSWORD in your .env file")
                return False
            
            # Fill login form with human-like typing
            wait = WebDriverWait(self.driver, 10)
            
            # Email field
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            # Add small delay before typing
            time.sleep(random.uniform(0.5, 1.2))
            self._human_type(email_field, fb_email)
            
            # Password field
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            # Add small delay before typing password
            time.sleep(random.uniform(0.3, 0.8))
            self._human_type(password_field, fb_password)
            
            # Random pause before clicking login
            time.sleep(random.uniform(0.5, 1.5))
            
            # Login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if 'facebook.com' in current_url and 'login' not in current_url:
                self.logger.info("✅ Facebook login successful")
                return True
            else:
                self.logger.error(f"Login failed - redirected to: {current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Facebook login failed: {e}")
            return False
    
    def _navigate_to_notifications(self) -> bool:
        """Navigate to Facebook Notifications page."""
        try:
            self.logger.info("🔔 Navigating to Facebook Notifications...")
            
            # Navigate to notifications page
            notifications_url = 'https://www.facebook.com/notifications'
            self.driver.get(notifications_url)
            time.sleep(5)
            
            # Wait for notifications page to load
            wait = WebDriverWait(self.driver, 15)
            
            try:
                # Look for notifications-specific elements
                notification_indicators = [
                    "//h1[contains(text(), 'Notifications')]",
                    "//span[contains(text(), 'All notifications')]",
                    "[aria-label*='Notifications']",
                    "[role='main']",
                    "//div[contains(@aria-label, 'notification')]"
                ]
                
                for indicator in notification_indicators:
                    try:
                        if indicator.startswith('//'):
                            element = wait.until(EC.presence_of_element_located((By.XPATH, indicator)))
                        else:
                            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, indicator)))
                        
                        if element:
                            self.logger.info("✅ Successfully navigated to Notifications")
                            return True
                    except TimeoutException:
                        continue
                
                # If we get here, none of the indicators were found
                self.logger.warning("Notification elements not found, but continuing...")
                return True  # Continue anyway as the page might have loaded
                
            except Exception as e:
                self.logger.warning(f"Could not verify notifications navigation: {e}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to notifications: {e}")
            return False
    
    def _start_monitoring_thread(self):
        """Start the monitoring thread."""
        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        self.logger.info("🔍 Starting notification monitoring loop...")
        
        check_count = 0
        
        while not self.stop_monitoring and self.monitoring_active:
            try:
                check_count += 1
                
                # Perform monitoring checks
                self._check_for_notifications()
                self._check_for_price_changes()
                
                # Log periodic status
                if check_count % 10 == 0:  # Every 10 checks
                    self.logger.info(f"📊 Monitoring active - Check #{check_count}")
                
                # Wait for next check
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait a bit before continuing
    
    def _check_for_notifications(self):
        """Check for new Facebook notifications."""
        try:
            if not self.driver:
                return
            
            # Look for notification indicators
            for selector in self.config['notification_selectors']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        # Check if this is a new notification
                        if self._is_new_notification(element):
                            notification_text = element.text.strip()
                            
                            # Check if it's marketplace-related
                            if self._is_marketplace_notification(notification_text):
                                self._process_marketplace_notification(notification_text)
                                
                except Exception as e:
                    continue  # Try next selector
                    
        except Exception as e:
            self.logger.error(f"Error checking notifications: {e}")
    
    def _check_for_price_changes(self):
        """Check for price change indicators on the current page."""
        try:
            if not self.driver:
                return
            
            # Look for price change keywords in page text
            page_text = self.driver.page_source.lower()
            
            for keyword in self.config['price_change_keywords']:
                if keyword in page_text:
                    # Found potential price change
                    self._process_price_change_indicator(keyword)
                    break  # Only process one per check to avoid spam
                    
        except Exception as e:
            self.logger.error(f"Error checking price changes: {e}")
    
    def _is_new_notification(self, element) -> bool:
        """Check if a notification element represents a new notification."""
        try:
            # Simple heuristic: check for unread indicators
            element_html = element.get_attribute('outerHTML')
            
            unread_indicators = [
                'unread', 'new', 'badge', 'dot', 
                'notification-new', 'unseen'
            ]
            
            for indicator in unread_indicators:
                if indicator in element_html.lower():
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _is_marketplace_notification(self, text: str) -> bool:
        """Check if notification is marketplace-related."""
        marketplace_keywords = [
            'marketplace', 'listing', 'item', 'buyer', 'seller',
            'price', 'sold', 'available', 'interested'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in marketplace_keywords)
    
    def _process_marketplace_notification(self, notification_text: str):
        """Process a marketplace-related notification."""
        try:
            self.logger.info(f"📢 Marketplace notification detected: {notification_text[:100]}...")
            
            if self.notification_callback:
                self.notification_callback({
                    'type': 'marketplace_notification',
                    'data': {
                        'message': f'New marketplace activity: {notification_text[:200]}',
                        'full_text': notification_text,
                        'detected_at': datetime.now().isoformat(),
                        'source': 'browser_monitor'
                    }
                })
                
        except Exception as e:
            self.logger.error(f"Error processing marketplace notification: {e}")
    
    def _process_price_change_indicator(self, keyword: str):
        """Process a detected price change indicator."""
        try:
            self.logger.info(f"💰 Price change indicator detected: {keyword}")
            
            if self.notification_callback:
                self.notification_callback({
                    'type': 'price_change_detected',
                    'data': {
                        'message': f'Price change detected: {keyword}',
                        'keyword': keyword,
                        'detected_at': datetime.now().isoformat(),
                        'change_type': 'decrease' if keyword in ['reduced', 'dropped', 'lower', 'sale'] else 'change',
                        'source': 'browser_monitor'
                    }
                })
                
        except Exception as e:
            self.logger.error(f"Error processing price change indicator: {e}")
    
    def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("🧹 Browser cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up browser: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_monitoring': self.monitoring_active,
            'monitoring_active': self.monitoring_active,
            'browser_active': self.driver is not None,
            'current_url': self.driver.current_url if self.driver else None,
            'last_check': datetime.now().isoformat()
        }
    
    def is_monitoring_active(self) -> bool:
        """Check if monitoring is currently active."""
        return self.monitoring_active and self.driver is not None
    
    def refresh_page(self):
        """Refresh the current page to check for new content."""
        try:
            if self.driver:
                self.driver.refresh()
                time.sleep(3)
                self.logger.info("🔄 Page refreshed for monitoring")
        except Exception as e:
            self.logger.error(f"Error refreshing page: {e}")


# Global instance
_notification_monitor = None

def get_notification_monitor(settings, notification_callback=None):
    """Get or create the global notification monitor instance."""
    global _notification_monitor
    
    if _notification_monitor is None:
        _notification_monitor = NotificationMonitor(settings, notification_callback)
    
    return _notification_monitor
