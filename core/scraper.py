"""
Facebook Marketplace Scraper

Automated scraping of Facebook Marketplace listings using Selenium WebDriver.
Handles login, navigation, data extraction, and anti-detection measures.
"""

import time
import re
import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)

from core.json_manager import JSONDataManager


class FacebookMarketplaceScraper:
    """Main scraper class for Facebook Marketplace automation."""
    
    def __init__(self, settings):
        """Initialize scraper with configuration."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.json_manager = JSONDataManager()
        
        # Configuration
        self.credentials = settings.get_facebook_credentials()
        self.search_config = settings.get_search_config()
        self.chrome_config = settings.get_chrome_options()
        
        # WebDriver instance
        self.driver = None
        self.wait = None
        
        # Session tracking
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_stats = {
            'start_time': datetime.now().isoformat(),
            'listings_found': 0,
            'new_listings': 0,
            'updated_listings': 0,
            'errors_count': 0,
            'error_details': []
        }
    
    def setup_driver(self):
        """Initialize and configure Chrome WebDriver."""
        try:
            chrome_options = Options()
            
            # Basic Chrome options
            if self.chrome_config['headless']:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument(f'--window-size={self.chrome_config["window_size"]}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Anti-detection measures
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent to appear more like a real browser
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Additional anti-detection
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            # Set timeouts
            self.driver.implicitly_wait(self.chrome_config['element_timeout'])
            self.driver.set_page_load_timeout(self.chrome_config['page_load_timeout'])
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, self.chrome_config['element_timeout'])
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def login_to_facebook(self) -> bool:
        """Login to Facebook using provided credentials."""
        try:
            self.logger.info("Starting Facebook login...")
            
            # Navigate to Facebook login page
            self.driver.get("https://www.facebook.com")
            self._random_delay(2, 4)
            
            # Find and fill email field
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            self._type_like_human(email_field, self.credentials['email'])
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            self._type_like_human(password_field, self.credentials['password'])
            
            # Submit login form
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            self._random_delay(3, 6)
            
            # Check for successful login
            if self._is_logged_in():
                self.logger.info("Successfully logged in to Facebook")
                return True
            else:
                # Check for common login issues
                if "checkpoint" in self.driver.current_url.lower():
                    self.logger.error("Login blocked by Facebook security checkpoint")
                elif "login" in self.driver.current_url.lower():
                    self.logger.error("Login failed - incorrect credentials or blocked")
                else:
                    self.logger.error(f"Unknown login issue. Current URL: {self.driver.current_url}")
                return False
                
        except TimeoutException:
            self.logger.error("Timeout during login process")
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if successfully logged in to Facebook."""
        try:
            # Look for elements that indicate successful login
            indicators = [
                (By.CSS_SELECTOR, "[data-click='profile_icon']"),
                (By.CSS_SELECTOR, "[aria-label='Account']"),
                (By.CSS_SELECTOR, "[role='button'][aria-label*='Account']"),
                (By.XPATH, "//div[@data-click='profile_icon']")
            ]
            
            for locator in indicators:
                try:
                    self.driver.find_element(*locator)
                    return True
                except NoSuchElementException:
                    continue
            
            # Also check URL doesn't contain login-related paths
            url = self.driver.current_url.lower()
            login_indicators = ['login', 'checkpoint', 'recover']
            
            return not any(indicator in url for indicator in login_indicators)
            
        except Exception:
            return False
    
    def navigate_to_marketplace(self) -> bool:
        """Navigate to Facebook Marketplace with iPhone 16 search."""
        try:
            self.logger.info("Navigating to Facebook Marketplace...")
            
            # First navigate to main marketplace
            marketplace_url = "https://www.facebook.com/marketplace"
            self.logger.info(f"Opening marketplace URL: {marketplace_url}")
            self.driver.get(marketplace_url)
            
            # Wait 1 second as requested
            time.sleep(1)
            
            # Then navigate to iPhone 16 search in Stockholm (using correct syntax)
            search_url = "https://www.facebook.com/marketplace/stockholm/search/?query=iphone%2016"
            self.logger.info(f"Navigating to iPhone 16 search: {search_url}")
            self.driver.get(search_url)
            self._random_delay(3, 5)
            
            # Wait for marketplace to load
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-surface='marketplace']")),
                        EC.presence_of_element_located((By.TEXT, "Marketplace")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label*='Marketplace']"))
                    )
                )
                self.logger.info("Successfully navigated to Marketplace")
                return True
            except TimeoutException:
                self.logger.error("Failed to load Marketplace page")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to Marketplace: {e}")
            return False
    
    def search_marketplace(self, keyword: str) -> bool:
        """Search for items in marketplace."""
        try:
            self.logger.info(f"Searching for: {keyword}")
            
            # Find search box
            search_selectors = [
                "input[placeholder*='Search Marketplace']",
                "input[aria-label*='Search Marketplace']",
                "input[placeholder*='Search']",
                "[role='searchbox']"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                self.logger.error("Could not find search box")
                return False
            
            # Clear and enter search term
            search_box.clear()
            self._type_like_human(search_box, keyword)
            self._random_delay(1, 2)
            
            # Submit search (press Enter)
            search_box.send_keys("\n")
            self._random_delay(3, 5)
            
            # Wait for search results to load
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-surface-wrapper='1']"))
                )
                self.logger.info(f"Search results loaded for: {keyword}")
                return True
            except TimeoutException:
                self.logger.warning(f"Search results may not have loaded properly for: {keyword}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Failed to search for {keyword}: {e}")
            return False
    
    def extract_listings(self) -> List[Dict[str, Any]]:
        """Extract listing data from current page."""
        listings = []
        
        try:
            # Wait a bit for dynamic content to load
            self._random_delay(2, 4)
            
            # Find listing containers - try multiple selectors
            listing_selectors = [
                "[data-surface-wrapper='1'] > div > div",
                "[role='main'] [data-surface-wrapper='1'] > div",
                "div[data-surface-wrapper] > div > div",
                ".marketplace-card",
                "[data-testid*='marketplace-item']"
            ]
            
            listing_elements = []
            for selector in listing_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        listing_elements = elements
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not listing_elements:
                self.logger.warning("No listing elements found")
                return []
            
            # Extract data from each listing
            for i, element in enumerate(listing_elements[:self.search_config['max_listings']]):
                try:
                    listing_data = self._extract_listing_data(element, i)
                    if listing_data:
                        listings.append(listing_data)
                        self.session_stats['listings_found'] += 1
                    
                    # Add delay between extractions
                    if i % 5 == 0:  # Every 5 items
                        self._random_delay(1, 2)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract listing {i}: {e}")
                    self.session_stats['errors_count'] += 1
                    continue
            
            self.logger.info(f"Successfully extracted {len(listings)} listings")
            return listings
            
        except Exception as e:
            self.logger.error(f"Failed to extract listings: {e}")
            self.session_stats['errors_count'] += 1
            return []
    
    def _extract_listing_data(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing element."""
        try:
            listing_data = {}
            
            # Extract title
            title_selectors = [
                "span[dir='auto']",
                "h3 span",
                "[data-surface-wrapper] span",
                "a span[dir='auto']"
            ]
            
            title = self._find_text_by_selectors(element, title_selectors)
            if not title:
                return None  # Skip if no title found
            
            listing_data['title'] = title.strip()
            
            # Extract price
            price_selectors = [
                "span[dir='auto']:contains('$')",
                "span:contains('AU$')",
                "span:contains('AUD')",
                "[data-testid*='price']",
                "span[class*='price']"
            ]
            
            price_text = self._find_text_by_selectors(element, price_selectors)
            listing_data['price'] = self._parse_price(price_text)
            listing_data['currency'] = 'AUD'  # Default based on config
            
            # Extract seller location
            location_selectors = [
                "span:contains('km away')",
                "span[dir='auto']:contains('km')",
                "[data-testid*='location']"
            ]
            
            location = self._find_text_by_selectors(element, location_selectors)
            listing_data['seller_location'] = location.strip() if location else ""
            
            # Extract listing URL
            link_element = element.find_element(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            if link_element:
                href = link_element.get_attribute('href')
                listing_data['listing_url'] = href
                
                # Extract listing ID from URL
                match = re.search(r'/marketplace/item/(\d+)', href)
                if match:
                    listing_data['listing_id'] = match.group(1)
                else:
                    listing_data['listing_id'] = f"unknown_{index}_{int(time.time())}"
            else:
                listing_data['listing_id'] = f"unknown_{index}_{int(time.time())}"
                listing_data['listing_url'] = ""
            
            # Extract image URL
            img_selectors = [
                "img[src*='scontent']",
                "img[data-src*='scontent']",
                "img[alt]"
            ]
            
            img_element = self._find_element_by_selectors(element, img_selectors)
            if img_element:
                img_url = img_element.get_attribute('src') or img_element.get_attribute('data-src')
                listing_data['image_url'] = img_url
            else:
                listing_data['image_url'] = ""
            
            # Set default values for missing fields
            listing_data.setdefault('seller_name', '')
            listing_data.setdefault('seller_id', '')
            listing_data.setdefault('description', '')
            listing_data.setdefault('category', self._guess_category(title))
            listing_data.setdefault('condition_text', '')
            
            return listing_data
            
        except Exception as e:
            self.logger.debug(f"Failed to extract data from listing element: {e}")
            return None
    
    def _find_text_by_selectors(self, parent_element, selectors: List[str]) -> Optional[str]:
        """Try multiple CSS selectors to find text content."""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle pseudo-selector differently
                    text_content = selector.split(':contains(')[1].rstrip(')')
                    elements = parent_element.find_elements(By.CSS_SELECTOR, selector.split(':contains(')[0])
                    for elem in elements:
                        if text_content.strip("'\"") in elem.text:
                            return elem.text
                else:
                    element = parent_element.find_element(By.CSS_SELECTOR, selector)
                    if element and element.text:
                        return element.text
            except:
                continue
        return None
    
    def _find_element_by_selectors(self, parent_element, selectors: List[str]):
        """Try multiple CSS selectors to find an element."""
        for selector in selectors:
            try:
                element = parent_element.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        return None
    
    def _parse_price(self, price_text: str) -> int:
        """Parse price text and return price in cents."""
        if not price_text:
            return 0
        
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+(?:\.\d{2})?', price_text.replace(',', ''))
        if price_match:
            try:
                price_float = float(price_match.group().replace(',', ''))
                return int(price_float * 100)  # Convert to cents
            except ValueError:
                pass
        
        return 0
    
    def _guess_category(self, title: str) -> str:
        """Guess product category based on title."""
        title_lower = title.lower()
        
        categories = {
            'electronics': ['iphone', 'samsung', 'phone', 'laptop', 'computer', 'tablet', 'headphones'],
            'furniture': ['chair', 'table', 'sofa', 'bed', 'desk', 'cabinet', 'dresser'],
            'vehicles': ['car', 'truck', 'motorcycle', 'bike', 'vehicle', 'auto'],
            'clothing': ['shirt', 'dress', 'shoes', 'jacket', 'jeans', 'clothing'],
            'home_garden': ['tools', 'garden', 'kitchen', 'appliance', 'decor']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _type_like_human(self, element, text: str):
        """Type text with human-like delays."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _random_delay(self, min_seconds: float, max_seconds: float):
        """Add random delay to avoid detection."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scrape_marketplace(self) -> List[Dict[str, Any]]:
        """Main scraping method that orchestrates the entire process."""
        all_listings = []
        
        try:
            # Setup WebDriver
            if not self.setup_driver():
                return []
            
            # Login to Facebook
            if not self.login_to_facebook():
                self.session_stats['error_details'].append("Login failed")
                return []
            
            # Navigate to Marketplace (already with iPhone 16 search)
            if not self.navigate_to_marketplace():
                self.session_stats['error_details'].append("Failed to navigate to Marketplace")
                return []
            
            # Extract listings directly since we're already on iPhone 16 search page
            try:
                self.logger.info("Extracting iPhone 16 listings from current page...")
                listings = self.extract_listings()
                
                # Save listings to JSON with duplicate prevention
                if listings:
                    stats = self.json_manager.add_products_batch(listings)
                    self.session_stats['new_listings'] = stats['added']
                    self.session_stats['duplicates_found'] = stats['duplicates']
                    self.session_stats['errors_count'] += stats['errors']
                
                all_listings.extend(listings)
                self.logger.info(f"Found {len(listings)} iPhone 16 listings")
                
            except Exception as e:
                self.logger.error(f"Failed to extract iPhone 16 listings: {e}")
                self.session_stats['errors_count'] += 1
                self.session_stats['error_details'].append(f"iPhone 16 extraction: {str(e)}")
            
            # Update session stats
            self.session_stats['end_time'] = datetime.now().isoformat()
            self.session_stats['status'] = 'completed'
            self.session_stats['search_keywords'] = 'iPhone 16'
            self.session_stats['search_location'] = 'Stockholm, Sweden'
            
            self.logger.info(f"Scraping completed. Total listings: {len(all_listings)}")
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            self.session_stats['status'] = 'failed'
            self.session_stats['error_details'].append(f"General error: {str(e)}")
            self.session_stats['end_time'] = datetime.now().isoformat()
        
        finally:
            # Save session data
            self.json_manager.save_scraping_session(self.session_stats)
            
            # Close WebDriver
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return all_listings
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
