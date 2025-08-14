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
    
    def __init__(self, settings, persistent_session=False):
        """Initialize scraper with configuration."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.json_manager = JSONDataManager()
        self.persistent_session = persistent_session
        self.is_logged_in_flag = False
        self.is_on_marketplace = False
        
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
            
            # Initialize driver - let Selenium manage ChromeDriver automatically
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            try:
                # Use webdriver-manager to automatically get the right ChromeDriver version
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                self.logger.warning(f"webdriver-manager failed: {e}, trying default Chrome setup")
                # Fallback to default Chrome setup if webdriver-manager fails
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
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Marketplace')]")),
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
            
            # Use the most reliable approach: find elements that contain marketplace item links
            self.logger.info("Looking for Facebook Marketplace product containers...")
            
            # First, try to find direct marketplace item links
            marketplace_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            self.logger.info(f"Found {len(marketplace_links)} marketplace item links")
            
            # Get the parent containers of these links (these are the actual product cards)
            listing_elements = []
            seen_elements = set()
            
            for link in marketplace_links:
                # Try different parent levels to find the product container
                current_element = link
                for level in range(5):  # Go up to 5 parent levels
                    try:
                        current_element = current_element.find_element(By.XPATH, "..")
                        element_id = id(current_element)
                        
                        # Check if this element looks like a product container
                        if (element_id not in seen_elements and 
                            current_element.text and 
                            len(current_element.text.strip()) > 10):
                            
                            seen_elements.add(element_id)
                            listing_elements.append(current_element)
                            break
                    except:
                        break
            
            self.logger.info(f"Extracted {len(listing_elements)} unique product containers from marketplace links")
            
            # If we didn't find enough, try alternative methods
            if len(listing_elements) < 3:
                self.logger.info("Trying alternative selector methods...")
                
                # Try finding elements with price information (Swedish kronor)
                price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'kr') or contains(text(), 'SEK')]")
                for elem in price_elements:
                    # Go up parent levels to find container
                    current = elem
                    for level in range(3):
                        try:
                            current = current.find_element(By.XPATH, "..")
                            element_id = id(current)
                            if (element_id not in seen_elements and 
                                current.text and 
                                len(current.text.strip()) > 20 and
                                ('kr' in current.text or 'SEK' in current.text)):
                                seen_elements.add(element_id)
                                listing_elements.append(current)
                                break
                        except:
                            break
                
                self.logger.info(f"Found {len(listing_elements)} total product containers")
            
            if not listing_elements:
                self.logger.warning("No listing elements found")
                
                # Debug: Save screenshot and page source for analysis
                try:
                    debug_dir = "debug_output"
                    import os
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    # Save screenshot
                    screenshot_path = f"{debug_dir}/no_elements_screenshot_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"Debug screenshot saved: {screenshot_path}")
                    
                    # Save page source
                    page_source_path = f"{debug_dir}/no_elements_page_source_{int(time.time())}.html"
                    with open(page_source_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    self.logger.info(f"Debug page source saved: {page_source_path}")
                    
                    # Log current URL and basic page info
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    self.logger.info(f"Debug info - URL: {current_url}, Title: {page_title}")
                    
                    # Try to find ANY elements on the page to see what's there
                    all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    self.logger.info(f"Page has {len(all_divs)} div elements and {len(all_links)} link elements")
                    
                    # Check for specific Facebook elements
                    fb_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid], [role], [aria-label]")
                    self.logger.info(f"Found {len(fb_elements)} Facebook-specific elements")
                    
                except Exception as debug_error:
                    self.logger.error(f"Debug info collection failed: {debug_error}")
                
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
            
            # Extract all text content from the element for debugging
            element_text = element.text.strip()
            if not element_text:
                return None
            
            # Try to extract title - look for the main heading/link text
            title = None
            title_selectors = [
                "a[role='link'] span",
                "h3", "h4", "h2",
                "span[dir='auto']",
                "[data-testid*='title']",
                "a span"
            ]
            
            # Try each selector and get the first meaningful text
            for selector in title_selectors:
                try:
                    elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        # Additional filtering to avoid prices and short text
                        if text and len(text) > 3 and not text.startswith('$') and not text.lower().startswith('sek') and 'kr' not in text.lower() and not text.replace(',','').isdigit():
                            title = text
                            break
                    if title:
                        break
                except:
                    continue
            
            # If no title found with selectors, try to extract from element text
            if not title:
                lines = element_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if len(line) > 3 and not line.startswith('$') and 'km' not in line.lower() and not line.isdigit() and not line.lower().startswith('sek'):
                        title = line
                        break
            
            if not title:
                self.logger.debug(f"No title found in element: {element_text[:100]}...")
                return None
            
            listing_data['title'] = title[:200]  # Limit title length
            
            # Extract price - look for currency symbols and numbers
            price_text = None
            price_patterns = [
                r'\$[\d,]+(?:\.\d{2})?',  # $1,234.56
                r'[\d,]+\s*kr',           # 1234 kr
                r'SEK\s*[\d,]+',          # SEK 1234
                r'[\d,]+\s*SEK',          # 1234 SEK
                r'AU\$[\d,]+',            # AU$1234
                r'USD\s*[\d,]+',          # USD 1234
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, element_text, re.IGNORECASE)
                if matches:
                    price_text = matches[0]
                    break
            
            # Parse price into structured format for JSON compatibility
            if price_text:
                # Extract numeric value
                price_numbers = re.findall(r'[\d,]+', price_text)
                if price_numbers:
                    try:
                        amount = int(price_numbers[0].replace(',', ''))
                        # Determine currency
                        if 'kr' in price_text.lower() or 'sek' in price_text.lower():
                            currency = 'SEK'
                        elif '$' in price_text:
                            currency = 'USD' if 'AU' not in price_text else 'AUD'
                        else:
                            currency = 'SEK'  # Default for Stockholm
                        
                        listing_data['price'] = {
                            'raw_value': price_text,
                            'currency': currency,
                            'amount': str(amount),
                            'note': f'Extracted from: {price_text}'
                        }
                    except ValueError:
                        listing_data['price'] = {'amount': '0', 'currency': 'SEK', 'raw_value': price_text}
                else:
                    listing_data['price'] = {'amount': '0', 'currency': 'SEK', 'raw_value': price_text}
            else:
                listing_data['price'] = {'amount': '0', 'currency': 'SEK', 'raw_value': 'Not found'}
            
            # Extract location - look for distance indicators
            location_text = None
            location_patterns = [
                r'([\w\s]+)\s+\d+\s*km',  # City 15 km
                r'\d+\s*km\s+from\s+([\w\s]+)',  # 15 km from City
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, element_text, re.IGNORECASE)
                if matches:
                    location_text = matches[0].strip()
                    break
            
            # If no specific location found, look for location-like text
            if not location_text:
                lines = element_text.split('\n')
                for line in lines:
                    if 'km' in line.lower():
                        location_text = line.strip()
                        break
            
            listing_data['location'] = {
                'city': location_text if location_text else 'Stockholm',
                'distance': 'Unknown',
                'raw_location': location_text if location_text else 'Not specified'
            }
            
            # Extract listing URL and ID
            try:
                link_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
                if not link_elements:
                    link_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='marketplace']")
                
                if link_elements:
                    href = link_elements[0].get_attribute('href')
                    listing_data['marketplace_url'] = href
                    
                    # Extract listing ID from URL
                    id_match = re.search(r'/marketplace/item/(\d+)', href)
                    if id_match:
                        listing_data['id'] = f"mp_{id_match.group(1)}"
                    else:
                        listing_data['id'] = f"mp_gen_{int(time.time())}_{index}"
                else:
                    listing_data['marketplace_url'] = ''
                    listing_data['id'] = f"mp_gen_{int(time.time())}_{index}"
            except Exception as e:
                listing_data['marketplace_url'] = ''
                listing_data['id'] = f"mp_gen_{int(time.time())}_{index}"
            
            # Extract image URLs
            image_urls = []
            try:
                img_elements = element.find_elements(By.CSS_SELECTOR, "img")
                for img in img_elements:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and ('scontent' in src or 'fbcdn' in src):
                        image_urls.append({
                            'url': src,
                            'type': 'thumbnail',
                            'size': 'unknown'
                        })
                        break  # Just take the first good image
            except:
                pass
            
            listing_data['images'] = image_urls
            
            # Add seller info (placeholder)
            listing_data['seller'] = {
                'info': 'Not extracted',
                'profile': None
            }
            
            # Add product details
            listing_data['product_details'] = {
                'model': self._extract_model(title),
                'storage': 'Unknown',
                'condition': 'Unknown',
                'color': 'Unknown'
            }
            
            # Add metadata with timestamp
            listing_data['extraction_method'] = 'automated_scraper'
            listing_data['data_quality'] = 'medium' if location_text and price_text else 'basic'
            listing_data['full_url'] = listing_data['marketplace_url']
            listing_data['added_at'] = datetime.now().isoformat()
            listing_data['source'] = 'facebook_marketplace_scraper'
            
            # Log successful extraction (handle Unicode properly)
            try:
                safe_title = title[:50].encode('ascii', 'replace').decode('ascii')
                self.logger.info(f"Successfully extracted listing: {safe_title}... Price: {listing_data['price']['amount']} {listing_data['price']['currency']} ID: {listing_data['id']}")
            except Exception:
                self.logger.info(f"Successfully extracted listing (title contains special chars) Price: {listing_data['price']['amount']} {listing_data['price']['currency']} ID: {listing_data['id']}")
            
            return listing_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract data from listing element {index}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _extract_model(self, title: str) -> str:
        """Extract product model from title."""
        title_lower = title.lower()
        if 'iphone' in title_lower:
            # Try to extract iPhone model
            iphone_patterns = [
                r'iphone\s*(\d+)\s*(pro\s*max|pro|plus|mini)?',
                r'iphone\s*(se|xr|xs|x)\s*(max)?'
            ]
            for pattern in iphone_patterns:
                match = re.search(pattern, title_lower)
                if match:
                    model = f"iPhone {match.group(1)}"
                    if match.group(2):
                        model += f" {match.group(2).title()}"
                    return model
            return 'iPhone'
        return 'Unknown'
    
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
    
    def _ensure_single_tab(self):
        """Ensure only one tab is open, close any extra tabs."""
        try:
            if not self.driver:
                return
            
            # Get all window handles
            all_windows = self.driver.window_handles
            
            if len(all_windows) > 1:
                self.logger.info(f"Found {len(all_windows)} tabs, closing extra tabs...")
                
                # Keep the first tab, close all others
                main_window = all_windows[0]
                
                for window in all_windows[1:]:
                    try:
                        self.driver.switch_to.window(window)
                        self.driver.close()
                        self.logger.debug(f"Closed extra tab: {window}")
                    except Exception as e:
                        self.logger.warning(f"Failed to close tab {window}: {e}")
                
                # Switch back to the main window
                self.driver.switch_to.window(main_window)
                self.logger.info(f"Now using single tab: {main_window}")
            
        except Exception as e:
            self.logger.warning(f"Failed to ensure single tab: {e}")
    
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
                    self.logger.info(f"Attempting to save {len(listings)} listings to JSON...")
                    stats = self.json_manager.add_products_batch(listings)
                    self.session_stats['new_listings'] = stats['added']
                    self.session_stats['duplicates_found'] = stats['duplicates']
                    self.session_stats['errors_count'] += stats['errors']
                    self.logger.info(f"JSON save stats: {stats['added']} added, {stats['duplicates']} duplicates, {stats['errors']} errors")
                else:
                    self.logger.warning("No listings extracted to save")
                
                all_listings.extend(listings)
                self.logger.info(f"Found {len(listings)} iPhone 16 listings, total so far: {len(all_listings)}")
                
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
    
    def scrape_marketplace_custom(self, search_query: str) -> List[Dict[str, Any]]:
        """Custom scraping method with user-provided search query."""
        all_listings = []
        
        try:
            # Setup WebDriver
            if not self.setup_driver():
                return []
            
            # Login to Facebook
            if not self.login_to_facebook():
                self.session_stats['error_details'].append("Login failed")
                return []
            
            # Navigate to Marketplace with custom search
            if not self.navigate_to_marketplace_custom(search_query):
                self.session_stats['error_details'].append("Failed to navigate to Marketplace")
                return []
            
            # Extract listings
            try:
                self.logger.info(f"Extracting {search_query} listings from current page...")
                listings = self.extract_listings()
                
                self.logger.info(f"Raw extraction returned {len(listings)} listings for '{search_query}'")
                
                # Save listings to JSON with duplicate prevention FIRST
                if listings:
                    self.logger.info(f"Attempting to save {len(listings)} {search_query} listings to JSON...")
                    stats = self.json_manager.add_products_batch(listings)
                    self.session_stats['new_listings'] = stats['added']
                    self.session_stats['duplicates_found'] = stats['duplicates'] 
                    self.session_stats['errors_count'] += stats['errors']
                    self.logger.info(f"JSON save stats: {stats['added']} added, {stats['duplicates']} duplicates, {stats['errors']} errors")
                    
                    # Add to return list
                    all_listings.extend(listings)
                    
                    # Log the actual titles found for debugging
                    for i, listing in enumerate(listings[:5]):
                        self.logger.info(f"Found listing {i+1}: {listing.get('title', 'NO TITLE')[:60]}...")
                    
                else:
                    self.logger.warning(f"No {search_query} listings extracted from page")
                    # Check if page loaded correctly by looking for any elements
                    try:
                        page_source_snippet = self.driver.page_source[:500] if self.driver else "No driver"
                        self.logger.debug(f"Page source snippet: {page_source_snippet}")
                        
                        # Check if we can find any products in general (not just matching search)
                        all_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-surface-wrapper='1'] > div > div")
                        self.logger.info(f"Total elements found on page: {len(all_elements)}")
                        
                        if all_elements:
                            self.logger.info(f"Sample element text: {all_elements[0].text[:200]}..." if all_elements[0].text else "Empty text")
                    except Exception as debug_error:
                        self.logger.error(f"Debug info extraction failed: {debug_error}")
                
                self.logger.info(f"Final count for '{search_query}': {len(all_listings)} listings will be returned")
                
            except Exception as e:
                self.logger.error(f"Failed to extract {search_query} listings: {e}")
                self.session_stats['errors_count'] += 1
                self.session_stats['error_details'].append(f"{search_query} extraction: {str(e)}")
            
            # Update session stats
            self.session_stats['end_time'] = datetime.now().isoformat()
            self.session_stats['status'] = 'completed'
            self.session_stats['search_keywords'] = search_query
            self.session_stats['search_location'] = 'Stockholm, Sweden'
            
            self.logger.info(f"Custom scraping completed. Total listings: {len(all_listings)}")
            
        except Exception as e:
            self.logger.error(f"Custom scraping failed: {e}")
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
    
    def navigate_to_marketplace_custom(self, search_query: str) -> bool:
        """Navigate to Facebook Marketplace with custom search query."""
        try:
            self.logger.info(f"Navigating to Facebook Marketplace with search: {search_query}")
            
            # First navigate to main marketplace
            marketplace_url = "https://www.facebook.com/marketplace"
            self.logger.info(f"Opening marketplace URL: {marketplace_url}")
            self.driver.get(marketplace_url)
            
            # Wait 1 second
            time.sleep(1)
            
            # Build search URL with custom query
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.facebook.com/marketplace/stockholm/search/?query={encoded_query}"
            
            self.logger.info(f"Navigating to custom search: {search_url}")
            self.driver.get(search_url)
            self._random_delay(3, 5)
            
            # Wait for marketplace to load
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-surface='marketplace']")),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Marketplace')]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label*='Marketplace']"))
                    )
                )
                self.logger.info(f"Successfully navigated to Marketplace with search: {search_query}")
                return True
            except TimeoutException:
                self.logger.error("Failed to load Marketplace page")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to Marketplace with custom search: {e}")
            return False
    
    def initialize_session(self) -> bool:
        """Initialize persistent session (login + navigate to marketplace)."""
        try:
            # Setup WebDriver if not already done
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            # Login if not already logged in
            if not self.is_logged_in_flag:
                if not self.login_to_facebook():
                    self.session_stats['error_details'].append("Login failed")
                    return False
                self.is_logged_in_flag = True
            
            # Navigate to marketplace if not already there
            if not self.is_on_marketplace:
                marketplace_url = "https://www.facebook.com/marketplace/stockholm"
                self.logger.info(f"Navigating to marketplace: {marketplace_url}")
                self.driver.get(marketplace_url)
                self._random_delay(2, 3)
                self.is_on_marketplace = True
            
            self.logger.info("Persistent session initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize persistent session: {e}")
            return False
    
    def quick_search(self, search_query: str) -> List[Dict[str, Any]]:
        """Enhanced quick search with continuous scrolling and deduplication."""
        try:
            self.logger.info(f"Starting enhanced search for: {search_query}")
            
            # Ensure session is initialized
            if not self.initialize_session():
                return []
            
            # Ensure we're using only one tab - close any extra tabs
            self._ensure_single_tab()
            
            # Build search URL and navigate directly in the current tab
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.facebook.com/marketplace/stockholm/search/?query={encoded_query}"
            
            self.logger.info(f"Navigating to search in current tab: {search_url}")
            self.driver.get(search_url)
            self._random_delay(3, 5)
            
            # Double-check we still have only one tab
            self._ensure_single_tab()
            
            # Wait for search results
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-surface-wrapper='1']"))
                    )
                )
            except TimeoutException:
                self.logger.warning("Search results may not have loaded properly")
            
            # Start continuous scraping with scrolling
            all_listings = self.continuous_scroll_and_scrape(search_query, max_cycles=10)
            
            return all_listings
            
        except Exception as e:
            self.logger.error(f"Quick search failed for '{search_query}': {e}")
            return []
    
    def continuous_scroll_and_scrape(self, search_query: str, max_cycles: int = 10) -> List[Dict[str, Any]]:
        """Continuously scroll and scrape products with deduplication."""
        all_listings = []
        seen_ids = set()
        cycle_count = 0
        no_new_products_count = 0
        
        self.logger.info(f"Starting continuous scraping for '{search_query}' with max {max_cycles} cycles")
        
        try:
            while cycle_count < max_cycles:
                cycle_count += 1
                self.logger.info(f"--- Scraping Cycle {cycle_count}/{max_cycles} ---")
                
                # Wait for products to load
                self._random_delay(2, 4)
                
                # Extract current listings from page
                current_listings = self.extract_listings()
                
                if not current_listings:
                    self.logger.warning(f"No listings found in cycle {cycle_count}")
                    no_new_products_count += 1
                    if no_new_products_count >= 3:
                        self.logger.warning("No new products found for 3 consecutive cycles, stopping")
                        break
                else:
                    # Reset counter if we found products
                    no_new_products_count = 0
                
                # Filter out duplicates based on ID
                new_listings = []
                for listing in current_listings:
                    listing_id = listing.get('id')
                    if listing_id and listing_id not in seen_ids:
                        # Additional check: skip obviously invalid listings
                        title = listing.get('title', '').lower()
                        if title and 'create new listing' not in title and len(title) > 3:
                            seen_ids.add(listing_id)
                            new_listings.append(listing)
                            self.logger.debug(f"New listing: {listing.get('title', 'NO TITLE')[:40]}...")
                
                if new_listings:
                    self.logger.info(f"Cycle {cycle_count}: Found {len(new_listings)} new unique listings")
                    all_listings.extend(new_listings)
                    
                    # Save to JSON immediately to prevent data loss
                    try:
                        stats = self.json_manager.add_products_batch(new_listings)
                        self.logger.info(f"Saved {stats['added']} listings, {stats['duplicates']} duplicates")
                    except Exception as save_error:
                        self.logger.error(f"Failed to save listings: {save_error}")
                else:
                    self.logger.info(f"Cycle {cycle_count}: No new unique listings found")
                
                # Scroll down to load more products
                if cycle_count < max_cycles:
                    self.logger.info(f"Scrolling down to load more products...")
                    
                    # Get current scroll position
                    current_height = self.driver.execute_script("return window.pageYOffset;")
                    
                    # Scroll down by 300-500 pixels (more controlled scrolling)
                    scroll_amount = random.randint(300, 500)
                    new_scroll_pos = current_height + scroll_amount
                    
                    self.driver.execute_script(f"window.scrollTo(0, {new_scroll_pos});")
                    self.logger.debug(f"Scrolled from {current_height} to {new_scroll_pos}")
                    
                    # Wait for new content to load
                    self._random_delay(3, 5)
                    
                    # Check if we've reached the bottom or no new content loaded
                    new_height = self.driver.execute_script("return document.body.scrollHeight;")
                    if new_scroll_pos >= new_height - 100:  # Near bottom with 100px buffer
                        self.logger.info("Reached near bottom of page")
                        break
                
                # Every 30 seconds cycle (approximate)
                if cycle_count % 3 == 0:  # Roughly every 3 cycles = ~30 seconds
                    self.logger.info(f"Completed {cycle_count} cycles, brief pause...")
                    self._random_delay(1, 2)
        
        except Exception as e:
            self.logger.error(f"Error during continuous scrolling: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
        
        self.logger.info(f"Continuous scraping completed: {len(all_listings)} unique listings found")
        
        # Log summary of found listings
        if all_listings:
            self.logger.info("Sample of scraped listings:")
            for i, listing in enumerate(all_listings[:5], 1):
                title = listing.get('title', 'NO TITLE')[:50]
                price = listing.get('price', {}).get('amount', 'N/A')
                currency = listing.get('price', {}).get('currency', '')
                try:
                    safe_title = title.encode('ascii', 'replace').decode('ascii')
                    self.logger.info(f"  {i}. {safe_title}... - {price} {currency}")
                except Exception:
                    self.logger.info(f"  {i}. [Title with special chars]... - {price} {currency}")
        
        return all_listings
    
    def close_session(self):
        """Close the persistent session and browser."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.logger.info("Closing persistent session")
                self.driver.quit()
                self.driver = None
                self.is_logged_in_flag = False
                self.is_on_marketplace = False
            except:
                pass
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if not self.persistent_session:
            # Only auto-close if not in persistent mode
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
