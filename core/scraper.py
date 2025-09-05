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
from facebook_time_parser import FacebookTimeParser
from core.product_filter import SmartProductFilter


class FacebookMarketplaceScraper:
    """Main scraper class for Facebook Marketplace automation with deep scraping capabilities.
    
    This class now integrates deep scraping functionality by default for comprehensive
    competitive intelligence gathering.
    """
    
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
        
        # Deep scraping configuration - Optimized for speed
        self.deep_scrape_config = {
            'max_products_per_session': self.settings.get_int('DEEP_SCRAPE_MAX_PRODUCTS', 10),
            'page_load_timeout': 10,
            'element_wait_timeout': 5,
            'inter_product_delay': (0.2, 0.5),  # Much faster between products
            'click_delay': (0.1, 0.3),          # Much faster after clicks
            'scroll_delay': (0.5, 1),           # Faster scrolling
            'enable_deep_scraping': self.settings.get_bool('ENABLE_DEEP_SCRAPING', True)
        }
        
        # Track deep scraping progress
        self.deep_scrape_stats = {
            'products_attempted': 0,
            'products_successful': 0,
            'seller_details_extracted': 0,
            'see_details_clicked': 0,
            'errors': []
        }
        
        # Enhanced extraction settings
        self.enhanced_extraction = {
            'enabled': True,
            'extract_real_prices': True,
            'extract_real_seller_names': True,
            'visit_seller_profiles': True,
            'save_enhanced_data': True
        }
        
        # Create output directory for detailed reports
        import os
        self.output_dir = "deep_scrape_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Facebook Time Parser for timing extraction
        self.time_parser = FacebookTimeParser()
        
        # Initialize Smart Product Filter for accurate model matching
        self.product_filter = SmartProductFilter()
        self.enable_smart_filtering = self.settings.get_bool('ENABLE_SMART_FILTERING', True)
    
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
            
            # Store search query for smart filtering
            self._current_search_query = "iPhone 16"
            
            # First navigate to main marketplace
            marketplace_url = "https://www.facebook.com/marketplace"
            self.logger.info(f"Opening marketplace URL: {marketplace_url}")
            self.driver.get(marketplace_url)
            
            # Wait 1 second as requested
            time.sleep(1)
            
            # Then navigate to iPhone 16 search in Sydney (using correct syntax)
            search_url = "https://www.facebook.com/marketplace/sydney/search/?query=iphone%2016"
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
            raw_listings = []
            for i, element in enumerate(listing_elements[:self.search_config['max_listings']]):
                try:
                    listing_data = self._extract_listing_data(element, i)
                    if listing_data:
                        raw_listings.append(listing_data)
                        self.session_stats['listings_found'] += 1
                    
                    # Add delay between extractions
                    if i % 5 == 0:  # Every 5 items
                        self._random_delay(1, 2)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract listing {i}: {e}")
                    self.session_stats['errors_count'] += 1
                    continue
            
            # 🔥 SMART FILTERING: Apply intelligent product filtering to exclude variants
            if self.enable_smart_filtering and raw_listings:
                search_query = getattr(self, '_current_search_query', 'iPhone 16')  # Default or stored query
                
                self.logger.info(f"🧠 Applying smart product filtering for search: '{search_query}'")
                self.logger.info(f"Found {len(raw_listings)} raw products before filtering")
                
                try:
                    # Filter products using smart filtering
                    filtered_listings, excluded_listings = self.product_filter.filter_product_list(raw_listings, search_query)
                    
                    # Log filtering results
                    if excluded_listings:
                        filter_stats = self.product_filter.get_filter_statistics(excluded_listings)
                        self.logger.info(f"📊 Smart filtering results: {len(filtered_listings)} included, {len(excluded_listings)} excluded")
                        self.logger.info(f"📊 Exclusion reasons: {filter_stats}")
                        
                        # Log some examples of excluded products
                        self.logger.info("📋 Sample excluded products:")
                        for i, excluded in enumerate(excluded_listings[:3]):
                            title = excluded.get('title', 'Unknown')[:50]
                            reason = excluded.get('exclusion_reason', 'Unknown reason')
                            self.logger.info(f"  {i+1}. {title}... - Reason: {reason}")
                    
                    # Use filtered listings for further processing
                    listings = filtered_listings
                    
                    # Update session stats
                    self.session_stats['raw_listings_found'] = len(raw_listings)
                    self.session_stats['filtered_listings_included'] = len(filtered_listings)
                    self.session_stats['filtered_listings_excluded'] = len(excluded_listings)
                    
                except Exception as filter_error:
                    self.logger.error(f"Smart filtering failed: {filter_error}")
                    self.logger.info("Falling back to unfiltered results")
                    listings = raw_listings
            else:
                # No filtering applied
                if not self.enable_smart_filtering:
                    self.logger.info("Smart filtering is disabled, using all extracted products")
                listings = raw_listings
            
            # 🔥 HOT RELOAD FEATURE: Save and notify for final filtered products
            for i, listing_data in enumerate(listings):
                try:
                    # Save product immediately for standard scraping
                    self._save_product_immediately_standard(listing_data, i + 1)
                    
                    # Send real-time notification for standard scraping
                    self._send_standard_product_notification(listing_data, i + 1, len(listings))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to save/notify for listing {i+1}: {e}")
            
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
            
            # Extract timing information from listing element using FacebookTimeParser
            timing_info = self._extract_timing_from_element(element)
            listing_data['timing'] = timing_info
            
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
            
            # 🔥 ENHANCED EXTRACTION: If enabled, enhance this listing with real data
            if self.enhanced_extraction['enabled']:
                listing_data = self._enhance_listing_with_real_data(listing_data)
            
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
    
    def _send_scraping_notification(self, notification_type: str, data: dict):
        """Send real-time scraping notification via Flask app if available."""
        try:
            # Try to get notification manager from the global registry
            if hasattr(self, '_notification_manager') and self._notification_manager:
                self._notification_manager.broadcast_notification(notification_type, data)
                self.logger.debug(f"Sent notification: {notification_type} - {data.get('message', 'No message')}")
            else:
                # Try Flask current_app as fallback
                try:
                    from flask import current_app
                    if hasattr(current_app, 'notification_manager'):
                        current_app.notification_manager.broadcast_notification(notification_type, data)
                        self.logger.debug(f"Sent notification via Flask app: {notification_type} - {data.get('message', 'No message')}")
                    else:
                        self.logger.debug(f"No notification manager available for: {notification_type}")
                except:
                    self.logger.debug(f"Flask app not available, notification not sent: {notification_type}")
                
        except Exception as e:
            # Silently fail if Flask app is not available or in different context
            self.logger.debug(f"Could not send notification {notification_type}: {e}")
    
    def set_notification_manager(self, notification_manager):
        """Set notification manager for real-time updates."""
        self._notification_manager = notification_manager
    
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
    
    def search_marketplace_custom(self, search_query: str) -> List[Dict[str, Any]]:
        """Search marketplace with custom query and return results."""
        all_listings = []
        
        try:
            # Send start notification
            self._send_scraping_notification('scrape_started', {
                'search_query': search_query,
                'message': f'Started scraping for "{search_query}"'
            })
            
            # Setup WebDriver
            if not self.driver:
                if not self.setup_driver():
                    return []
            
            # Login to Facebook
            if not self.is_logged_in_flag:
                if not self.login_to_facebook():
                    self.session_stats['error_details'].append("Login failed")
                    self._send_scraping_notification('scrape_error', {
                        'error': 'Login failed',
                        'message': 'Failed to login to Facebook'
                    })
                    return []
                self.is_logged_in_flag = True
            
            # Navigate to Marketplace with custom search
            if not self.navigate_to_marketplace_custom(search_query):
                self.session_stats['error_details'].append("Failed to navigate to Marketplace")
                self._send_scraping_notification('scrape_error', {
                    'error': 'Navigation failed',
                    'message': 'Failed to navigate to Marketplace'
                })
                return []
            
            # Extract listings from search results
            try:
                self.logger.info(f"Extracting {search_query} listings from search results...")
                
                # Send progress notification
                self._send_scraping_notification('scrape_progress', {
                    'message': f'Extracting listings for "{search_query}"...',
                    'status': 'extracting'
                })
                
                listings = self.extract_listings()
                
                # Save listings to JSON with real-time updates
                if listings:
                    self.logger.info(f"Processing {len(listings)} listings for real-time updates...")
                    
                    # Process listings one by one for real-time updates
                    saved_count = 0
                    for i, listing in enumerate(listings):
                        try:
                            # Add individual product
                            if self.json_manager.add_product(listing):
                                saved_count += 1
                                
                                # Send real-time update notification
                                self._send_scraping_notification('product_found', {
                                    'product_title': listing.get('title', 'Unknown'),
                                    'product_price': listing.get('price', {}).get('amount', 'N/A'),
                                    'product_location': listing.get('location', {}).get('city', 'Unknown'),
                                    'current_count': saved_count,
                                    'total_processed': i + 1,
                                    'message': f'Found: {listing.get("title", "Unknown")[:40]}...',
                                    'search_query': search_query
                                })
                                
                                # Quick delay for UI updates
                                import time
                                time.sleep(0.1)
                        except Exception as e:
                            self.logger.warning(f"Failed to save individual listing: {e}")
                    
                    self.session_stats['new_listings'] = saved_count
                    self.logger.info(f"Saved {saved_count} new listings from {len(listings)} total")
                    
                    # Send completion notification
                    self._send_scraping_notification('scrape_completed', {
                        'search_query': search_query,
                        'total_found': len(listings),
                        'total_saved': saved_count,
                        'message': f'Completed! Found {saved_count} new listings for "{search_query}"'
                    })
                else:
                    self.logger.warning("No listings extracted")
                    self._send_scraping_notification('scrape_completed', {
                        'search_query': search_query,
                        'total_found': 0,
                        'total_saved': 0,
                        'message': f'No listings found for "{search_query}"'
                    })
                
                all_listings.extend(listings)
                self.logger.info(f"Found {len(listings)} listings for {search_query}")
                
            except Exception as e:
                self.logger.error(f"Failed to extract {search_query} listings: {e}")
                self.session_stats['errors_count'] += 1
                self.session_stats['error_details'].append(f"{search_query} extraction: {str(e)}")
                self._send_scraping_notification('scrape_error', {
                    'error': str(e),
                    'search_query': search_query,
                    'message': f'Error extracting listings: {str(e)}'
                })
            
            # Update session stats
            self.session_stats['end_time'] = datetime.now().isoformat()
            self.session_stats['status'] = 'completed'
            self.session_stats['search_keywords'] = search_query
            self.session_stats['search_location'] = 'Sydney, Australia'
            
            self.logger.info(f"Custom search scraping completed. Total listings: {len(all_listings)}")
            
        except Exception as e:
            self.logger.error(f"Custom search scraping failed: {e}")
            self.session_stats['status'] = 'failed'
            self.session_stats['error_details'].append(f"General error: {str(e)}")
            self.session_stats['end_time'] = datetime.now().isoformat()
            self._send_scraping_notification('scrape_error', {
                'error': str(e),
                'search_query': search_query,
                'message': f'Scraping failed: {str(e)}'
            })
        
        finally:
            # Save session data
            self.json_manager.save_scraping_session(self.session_stats)
            
            # Don't close driver here - let it persist for potential next use
            # if self.driver:
            #     try:
            #         self.driver.quit()
            #     except:
            #         pass
        
        return all_listings
    
    
    def navigate_to_marketplace_custom(self, search_query: str) -> bool:
        """Navigate to Facebook Marketplace with custom search query."""
        try:
            self.logger.info(f"Navigating to Facebook Marketplace with search: {search_query}")
            
            # Store search query for smart filtering
            self._current_search_query = search_query
            
            # First navigate to main marketplace
            marketplace_url = "https://www.facebook.com/marketplace"
            self.logger.info(f"Opening marketplace URL: {marketplace_url}")
            self.driver.get(marketplace_url)
            
            # Wait 1 second
            time.sleep(1)
            
            # Build search URL with custom query
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={encoded_query}"
            
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
                marketplace_url = "https://www.facebook.com/marketplace/sydney"
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
            search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={encoded_query}"
            
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
        
        # Send start notification
        self._send_scraping_notification('scraping_started', {
            'search_query': search_query,
            'max_cycles': max_cycles,
            'message': f'Started scraping for "{search_query}"'
        })
        
        try:
            while cycle_count < max_cycles:
                cycle_count += 1
                self.logger.info(f"--- Scraping Cycle {cycle_count}/{max_cycles} ---")
                
                # Send cycle start notification
                self._send_scraping_notification('cycle_started', {
                    'cycle': cycle_count,
                    'max_cycles': max_cycles,
                    'message': f'Starting cycle {cycle_count} of {max_cycles}'
                })
                
                # Wait for products to load
                self._random_delay(2, 4)
                
                # Extract current listings from page
                current_listings = self.extract_listings()
                
                if not current_listings:
                    self.logger.warning(f"No listings found in cycle {cycle_count}")
                    no_new_products_count += 1
                    
                    # Send no items found notification
                    self._send_scraping_notification('no_items_found', {
                        'cycle': cycle_count,
                        'message': f'No items found in cycle {cycle_count}'
                    })
                    
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
                    
                    # 🔥 HOT RELOAD FEATURE: Save each product immediately as it's found
                    for idx, listing in enumerate(new_listings):
                        try:
                            # Add hot reload metadata
                            listing['hot_reload_timestamp'] = datetime.now().isoformat()
                            listing['scraping_status'] = 'completed'
                            listing['scraping_method'] = 'continuous'
                            
                            # Save individual product immediately using hot reload
                            success = self.json_manager.add_product_hot_reload(listing)
                            if success:
                                self.logger.debug(f"🔥 Hot reload: Saved product {idx+1}/{len(new_listings)} successfully")
                            else:
                                self.logger.warning(f"🔥 Hot reload: Failed to save product {idx+1}/{len(new_listings)}")
                            
                            # Send individual product notification
                            self._send_scraping_notification('product_added', {
                                'cycle': cycle_count,
                                'product_index': idx + 1,
                                'total_in_cycle': len(new_listings),
                                'product_title': listing.get('title', 'Unknown')[:50],
                                'product_price': listing.get('price', {}).get('amount', '0'),
                                'product_currency': listing.get('price', {}).get('currency', 'SEK'),
                                'search_query': search_query,
                                'message': f'Added: {listing.get("title", "Unknown")[:40]}...'
                            })
                        except Exception as individual_save_error:
                            self.logger.error(f"Failed to save individual product: {individual_save_error}")
                    
                    # Send cycle summary notification
                    self._send_scraping_notification('items_found', {
                        'cycle': cycle_count,
                        'new_items': len(new_listings),
                        'total_items': len(all_listings),
                        'search_query': search_query,
                        'message': f'Cycle {cycle_count} complete: {len(new_listings)} new items added'
                    })
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
                    self._random_delay(1, 2)
                    
                    # Check if we've reached the bottom or no new content loaded
                    new_height = self.driver.execute_script("return document.body.scrollHeight;")
                    if new_scroll_pos >= new_height - 100:  # Near bottom with 100px buffer
                        self.logger.info("Reached near bottom of page")
                        break
                
                # No inter-cycle delays for maximum speed
        
        except Exception as e:
            self.logger.error(f"Error during continuous scrolling: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
        
        self.logger.info(f"Continuous scraping completed: {len(all_listings)} unique listings found")
        
        # Send completion notification
        self._send_scraping_notification('scraping_completed', {
            'search_query': search_query,
            'total_items': len(all_listings),
            'cycles_completed': cycle_count,
            'message': f'Scraping completed! Found {len(all_listings)} total items for "{search_query}"'
        })
        
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
    
    def deep_scrape_marketplace(self, search_query: str, max_products: int = None) -> List[Dict[str, Any]]:
        """
        Main method to perform deep scraping of marketplace products.
        
        Args:
            search_query: Product search term (e.g., "iphone 16", "samsung galaxy")
            max_products: Maximum number of products to deep scrape
        
        Returns:
            List of comprehensive product data with seller details
        """
        if not self.deep_scrape_config['enable_deep_scraping']:
            self.logger.info("Deep scraping is disabled, using standard scraping")
            return self.quick_search(search_query)
        
        if max_products is None:
            max_products = self.deep_scrape_config['max_products_per_session']
        
        try:
            self.logger.info(f"Starting deep scrape for: {search_query} (max {max_products} products)")
            
            # Send start notification
            self._send_scraping_notification('deep_scrape_started', {
                'search_query': search_query,
                'max_products': max_products,
                'message': f'Started deep scraping for "{search_query}"'
            })
            
            # Reset stats
            self.deep_scrape_stats = {
                'products_attempted': 0,
                'products_successful': 0,
                'seller_details_extracted': 0,
                'see_details_clicked': 0,
                'errors': []
            }
            
            # Setup WebDriver if needed
            if not self.driver:
                if not self.setup_driver():
                    return []
            
            # Login to Facebook if needed
            if not self.is_logged_in_flag:
                if not self.login_to_facebook():
                    self.session_stats['error_details'].append("Login failed")
                    return []
                self.is_logged_in_flag = True
            
            # Store current search query for navigation back
            self._current_search_query = search_query
            
            # Navigate to marketplace search
            if not self.navigate_to_marketplace_custom(search_query):
                self.session_stats['error_details'].append("Failed to navigate to Marketplace")
                return []
            
            # Find product cards from search results
            product_cards = self._find_product_cards_for_deep_scrape()
            if not product_cards:
                self.logger.warning("No product cards found for deep scraping")
                return []
            
            self.logger.info(f"Found {len(product_cards)} product cards, will deep scrape first {min(max_products, len(product_cards))}")
            
            # Perform deep extraction on each product
            deep_scraped_products = []
            cards_to_process = product_cards[:max_products]
            
            for i, card in enumerate(cards_to_process):
                try:
                    self.deep_scrape_stats['products_attempted'] += 1
                    
                    self.logger.info(f"Deep scraping product {i+1}/{len(cards_to_process)}: {card['title'][:50]}...")
                    
                    # Send progress notification
                    self._send_scraping_notification('deep_scrape_progress', {
                        'current_product': i + 1,
                        'total_products': len(cards_to_process),
                        'product_title': card['title'][:60],
                        'message': f'Scraping product {i+1}/{len(cards_to_process)}: {card["title"][:40]}...'
                    })
                    
                    # Extract comprehensive data from product page
                    deep_data = self._extract_deep_product_data(card, i + 1)
                    
                    if deep_data:
                        deep_scraped_products.append(deep_data)
                        self.deep_scrape_stats['products_successful'] += 1
                        self.logger.info(f"✅ Successfully deep scraped product {i+1}")
                        
                        # 🔥 HOT RELOAD FEATURE: Save product immediately to JSON
                        self._save_product_immediately(deep_data, i + 1)
                        
                        # Send real-time notification to dashboard
                        self._send_product_completion_notification(deep_data, i + 1, len(cards_to_process))
                        
                    else:
                        self.logger.warning(f"❌ Failed to deep scrape product {i+1}")
                        self.deep_scrape_stats['errors'].append(f"Product {i+1}: Failed to extract data")
                    
                    # Delay between products to avoid detection
                    if i < len(cards_to_process) - 1:
                        delay = random.uniform(*self.deep_scrape_config['inter_product_delay'])
                        self.logger.debug(f"Waiting {delay:.1f}s before next product...")
                        time.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error deep scraping product {i+1}: {e}")
                    self.deep_scrape_stats['errors'].append(f"Product {i+1}: {str(e)}")
                    continue
            
            # Save comprehensive results
            self._save_deep_scrape_results(deep_scraped_products, search_query)
            
            # Send completion notification
            self._send_scraping_notification('deep_scrape_completed', {
                'search_query': search_query,
                'total_products': len(deep_scraped_products),
                'successful': self.deep_scrape_stats['products_successful'],
                'attempted': self.deep_scrape_stats['products_attempted'],
                'seller_details': self.deep_scrape_stats['seller_details_extracted'],
                'message': f'Deep scraping completed! Successfully processed {self.deep_scrape_stats["products_successful"]}/{self.deep_scrape_stats["products_attempted"]} products'
            })
            
            self.logger.info(f"Deep scraping completed: {len(deep_scraped_products)} products with comprehensive data")
            return deep_scraped_products
            
        except Exception as e:
            self.logger.error(f"Deep scraping failed: {e}")
            self._send_scraping_notification('deep_scrape_error', {
                'error': str(e),
                'message': f'Deep scraping failed: {str(e)}'
            })
            return []
    
    def _find_product_cards_for_deep_scrape(self) -> List[Dict[str, Any]]:
        """Find and prepare product cards for deep scraping with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Finding product cards for deep scraping (attempt {attempt + 1}/{max_attempts})...")
                
                # Wait for content to load with longer delays for bad connections
                wait_time = 2 + attempt  # Progressively longer waits
                time.sleep(wait_time)
                
                # Verify we're on the right page first
                current_url = self.driver.current_url.lower()
                if 'marketplace' not in current_url or ('search' not in current_url and 'query=' not in current_url):
                    self.logger.warning(f"Not on marketplace search page (URL: {current_url}), attempting to navigate back...")
                    
                    # Try to get back to search results
                    search_query = getattr(self, '_current_search_query', 'iphone')
                    import urllib.parse
                    encoded_query = urllib.parse.quote(search_query)
                    search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={encoded_query}"
                    
                    self.logger.info(f"Navigating back to search: {search_url}")
                    self.driver.get(search_url)
                    time.sleep(3 + attempt)  # Extra time for page load
                
                # Find marketplace item links
                marketplace_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
                self.logger.info(f"Found {len(marketplace_links)} marketplace item links on attempt {attempt + 1}")
                
                # If we found some links, process them
                if marketplace_links:
                    product_cards = []
                    for i, link in enumerate(marketplace_links):
                        try:
                            url = link.get_attribute('href')
                            if not url or '/marketplace/item/' not in url:
                                continue
                            
                            # Verify link is still valid (element not stale)
                            try:
                                link.is_displayed()  # This will throw if element is stale
                            except:
                                self.logger.debug(f"Link {i} is stale, skipping")
                                continue
                            
                            # Try to get product title from link or parent
                            title = self._extract_title_from_link(link, i)
                            
                            product_cards.append({
                                'index': i,
                                'title': title,
                                'url': url,
                                'link_element': link
                            })
                            
                        except Exception as e:
                            self.logger.debug(f"Failed to process link {i}: {e}")
                            continue
                    
                    if product_cards:
                        self.logger.info(f"Successfully prepared {len(product_cards)} product cards for deep scraping")
                        return product_cards
                    else:
                        self.logger.warning(f"Found links but couldn't process any on attempt {attempt + 1}")
                else:
                    self.logger.warning(f"No marketplace links found on attempt {attempt + 1}")
                
                # If this isn't the last attempt, wait before retrying
                if attempt < max_attempts - 1:
                    self.logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error finding product cards on attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
        
        self.logger.error(f"Failed to find product cards after {max_attempts} attempts")
        return []
    
    def _extract_title_from_link(self, link, index: int) -> str:
        """Extract product title from link element or its parents."""
        try:
            # Try to get text from the link itself
            link_text = link.text.strip()
            if link_text and len(link_text) > 5:
                return link_text
            
            # Look in parent elements for title
            parent = link
            for level in range(3):
                try:
                    parent = parent.find_element(By.XPATH, "..")
                    parent_text = parent.text.strip()
                    if parent_text and len(parent_text) > 10:
                        # Extract first meaningful line as title
                        lines = parent_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if (len(line) > 5 and 
                                not line.startswith('SEK') and 
                                not line.startswith('$') and
                                not line.replace(',','').replace(' ','').isdigit()):
                                return line
                        break
                except:
                    break
            
            return f"Product {index+1}"
            
        except Exception as e:
            return f"Product {index+1}"
    
    def _extract_deep_product_data(self, card: Dict[str, Any], product_index: int) -> Optional[Dict[str, Any]]:
        """Extract comprehensive data from a product's detail page."""
        try:
            original_url = self.driver.current_url
            product_url = card['url']
            product_title = card['title']
            
            self.logger.info(f"Navigating to product page: {product_title[:50]}...")
            
            # Navigate to product detail page
            self.driver.get(product_url)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Initialize comprehensive data structure
            comprehensive_data = {
                'basic_info': {
                    'title': product_title,
                    'url': product_url,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'page_title': self.driver.title,
                    'current_url': self.driver.current_url
                },
                'seller_details': {},
                'seller_metrics': {},
                'product_comprehensive': {},
                'marketplace_metadata': {},
                'extraction_metadata': {
                    'method': 'deep_scraper',
                    'product_index': product_index,
                    'data_quality': 'comprehensive'
                }
            }
            
            # Extract basic product information first
            self._extract_basic_product_info(comprehensive_data)
            
            # Extract seller information
            self._extract_seller_information(comprehensive_data)
            
            # Try to click "See Details" button and get extended seller info
            seller_details = self._click_see_details_and_extract_seller(comprehensive_data, product_index)
            comprehensive_data['seller_details'] = seller_details
            
            # Extract comprehensive product details
            self._extract_comprehensive_product_details(comprehensive_data)
            
            # Extract marketplace metadata
            self._extract_marketplace_metadata(comprehensive_data)
            
            # Extract additional images
            self._extract_all_product_images(comprehensive_data)
            
            # Extract product description
            self._extract_full_product_description(comprehensive_data)
            
            # Extract timing and posting information
            self._extract_posting_timing_info(comprehensive_data)
            
            # Save individual product report
            self._save_individual_product_report(comprehensive_data, product_index)
            
            # Navigate back to search results for next product
            self.logger.info("Navigating back to search results...")
            max_back_attempts = 3
            back_successful = False
            
            for attempt in range(max_back_attempts):
                try:
                    # First attempt: browser back
                    if attempt == 0:
                        self.logger.info(f"Attempt {attempt + 1}: Using browser back()")
                        self.driver.back()
                        time.sleep(2)  # Longer wait for bad connections
                        
                    # Check if we're back on search results
                    current_url = self.driver.current_url.lower()
                    if ('marketplace' in current_url and 'search' in current_url) or 'query=' in current_url:
                        self.logger.info(f"Successfully navigated back on attempt {attempt + 1}")
                        back_successful = True
                        break
                    else:
                        # Not on search page, try to reconstruct search URL
                        search_query = getattr(self, '_current_search_query', 'iphone')
                        # Use URL encoding for search query
                        import urllib.parse
                        encoded_query = urllib.parse.quote(search_query)
                        search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={encoded_query}"
                        
                        self.logger.info(f"Attempt {attempt + 1}: Not on search page, navigating to: {search_url}")
                        self.driver.get(search_url)
                        time.sleep(3)  # Extra time for page load with bad internet
                        
                        # Verify we're on the right page now
                        if 'marketplace' in self.driver.current_url.lower():
                            back_successful = True
                            break
                        
                except Exception as nav_error:
                    self.logger.warning(f"Navigation attempt {attempt + 1} failed: {nav_error}")
                    if attempt < max_back_attempts - 1:
                        time.sleep(2)  # Wait before retrying
                        continue
                    else:
                        # Final attempt with fresh search page
                        try:
                            search_query = getattr(self, '_current_search_query', 'iphone')
                            import urllib.parse
                            encoded_query = urllib.parse.quote(search_query)
                            search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={encoded_query}"
                            
                            self.logger.error(f"All navigation attempts failed, final fallback to: {search_url}")
                            self.driver.get(search_url)
                            time.sleep(5)  # Long wait for final attempt
                            back_successful = True
                        except Exception as final_error:
                            self.logger.error(f"Final navigation fallback failed: {final_error}")
                            # Don't raise here, continue with what we have
                            break
            
            if not back_successful:
                self.logger.warning(f"Failed to navigate back after {max_back_attempts} attempts, but continuing...")
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract deep data for product {product_index}: {e}")
            
            # Try to navigate back to search results even on error
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.back()
                    time.sleep(0.5)
                    # If back doesn't work, try search URL
                    if 'marketplace' not in self.driver.current_url.lower():
                        search_query = getattr(self, '_current_search_query', 'iphone')
                        search_url = f"https://www.facebook.com/marketplace/sydney/search/?query={search_query.replace(' ', '%20')}"
                        self.driver.get(search_url)
                        time.sleep(1.0)
            except:
                pass
            
            return None
    
    def _extract_basic_product_info(self, data: Dict[str, Any]):
        """Extract basic product information from the page."""
        try:
            # Extract price information
            price_info = self._extract_detailed_price()
            data['basic_info']['price'] = price_info
            
            # Extract location information
            location_info = self._extract_detailed_location()
            data['basic_info']['location'] = location_info
            
            # Extract product ID from URL
            url = data['basic_info']['url']
            id_match = re.search(r'/marketplace/item/(\d+)', url)
            if id_match:
                data['basic_info']['product_id'] = id_match.group(1)
            
        except Exception as e:
            self.logger.error(f"Failed to extract basic product info: {e}")
    
    def _extract_detailed_price(self) -> Dict[str, Any]:
        """Extract detailed price information."""
        try:
            page_text = self.driver.page_source.lower()
            
            # Look for various price patterns
            price_patterns = [
                r'(\d[\d,\s]*[\d])\s*(kr|sek)',  # Price with currency after
                r'(kr|sek)\s*(\d[\d,\s]*[\d])',  # Currency before price
                r'(\d[\d,\s]*[\d])\s*:-'         # Swedish price format
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    match = matches[0]
                    if isinstance(match, tuple):
                        if 'kr' in match[0] or 'sek' in match[0]:
                            # Currency first format
                            currency = match[0].upper()
                            amount = match[1].replace(' ', '').replace(',', '')
                        else:
                            # Amount first format
                            amount = match[0].replace(' ', '').replace(',', '')
                            currency = match[1].upper() if len(match) > 1 else 'SEK'
                    else:
                        amount = match.replace(' ', '').replace(',', '').replace(':-', '')
                        currency = 'SEK'
                    
                    return {
                        'amount': amount,
                        'currency': currency,
                        'raw_price_text': f"{' '.join(match) if isinstance(match, tuple) else match}"
                    }
            
            return {'amount': '0', 'currency': 'SEK', 'raw_price_text': 'Not found'}
            
        except Exception as e:
            self.logger.error(f"Failed to extract price: {e}")
            return {'amount': '0', 'currency': 'SEK', 'error': str(e)}
    
    def _extract_detailed_location(self) -> Dict[str, Any]:
        """Extract detailed location information."""
        try:
            page_source = self.driver.page_source
            
            # Extract location using regex patterns
            location_patterns = [
                r'([A-Za-z\s]+)\s+(\d+)\s*km',  # City X km
                r'(\d+)\s*km\s+from\s+([A-Za-z\s]+)',  # X km from City
                r'Sydney[^<]*'  # Any Sydney reference
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        return {
                            'city': matches[0][0].strip(),
                            'distance': f"{matches[0][1]}km" if len(matches[0]) > 1 else 'Unknown',
                            'raw_location': ' '.join(matches[0])
                        }
                    else:
                        return {
                            'city': 'Sydney',
                            'distance': 'Unknown',
                            'raw_location': matches[0]
                        }
            
            return {'city': 'Sydney', 'distance': 'Unknown', 'raw_location': 'Not specified'}
            
        except Exception as e:
            self.logger.error(f"Failed to extract location: {e}")
            return {'city': 'Unknown', 'distance': 'Unknown', 'error': str(e)}
    
    def _extract_seller_information(self, data: Dict[str, Any]):
        """Extract basic seller information from the product page."""
        try:
            seller_info = {}
            
            # Look for seller profile links
            seller_selectors = [
                "a[href*='/profile/']",
                "a[href*='/people/']",
                "[data-testid*='seller']",
                "[data-testid*='profile']"
            ]
            
            for selector in seller_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        href = element.get_attribute('href') or ''
                        
                        if text and ('/profile/' in href or '/people/' in href):
                            seller_info['seller_name'] = text
                            seller_info['profile_url'] = href
                            break
                except:
                    continue
                
                if seller_info:
                    break
            
            data['seller_metrics']['basic_info'] = seller_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract seller info: {e}")
            data['seller_metrics']['basic_info'] = {'error': str(e)}
    
    def _click_see_details_and_extract_seller(self, data: Dict[str, Any], product_index: int) -> Dict[str, Any]:
        """Click 'See Details' button and extract detailed seller information."""
        try:
            self.logger.info("Looking for 'See Details' button...")
            
            # Various selectors to find the "See details" button
            see_details_selectors = [
                "a:contains('See details')",
                "a:contains('View profile')",
                "a:contains('See seller')",
                "span:contains('See details')",
                "div[role='button']:contains('See details')",
                "div[role='button']:contains('View profile')"
            ]
            
            see_details_button = None
            for selector in see_details_selectors:
                try:
                    if ':contains(' in selector:
                        text_part = selector.split(':contains(')[1].strip(')').strip('\'"')
                        base_selector = selector.split(':contains(')[0]
                        
                        potential_elements = self.driver.find_elements(By.CSS_SELECTOR, base_selector)
                        for element in potential_elements:
                            if text_part.lower() in element.text.lower():
                                see_details_button = element
                                break
                    else:
                        potential_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if potential_elements:
                            see_details_button = potential_elements[0]
                    
                    if see_details_button:
                        self.logger.info(f"Found 'See details' button with selector: {selector}")
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Try profile links as fallback
            if not see_details_button:
                try:
                    profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/profile/']")
                    if profile_links:
                        see_details_button = profile_links[0]
                        self.logger.info("Using profile link as 'See details' button")
                except:
                    pass
            
            seller_details_info = {
                'button_found': bool(see_details_button),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            if see_details_button:
                try:
                    button_text = see_details_button.text.strip()
                    button_href = see_details_button.get_attribute('href')
                    
                    seller_details_info.update({
                        'button_text': button_text,
                        'button_href': button_href
                    })
                    
                    self.logger.info(f"Clicking 'See details' button: {button_text}")
                    
                    # Click the button
                    try:
                        see_details_button.click()
                        time.sleep(random.uniform(0.5, 1.5))
                        
                        # Extract information from details page/popup
                        detailed_seller_data = self._extract_from_seller_details_page()
                        seller_details_info.update(detailed_seller_data)
                        
                        self.deep_scrape_stats['see_details_clicked'] += 1
                        self.deep_scrape_stats['seller_details_extracted'] += 1
                        
                        # Navigate back if we went to a new page
                        if self.driver.current_url != data['basic_info']['current_url']:
                            self.logger.info("Navigated to new page, going back...")
                            self.driver.back()
                            time.sleep(0.5)
                        
                    except ElementNotInteractableException:
                        # Try JavaScript click as fallback
                        self.logger.info("Direct click failed, trying JavaScript click")
                        try:
                            self.driver.execute_script("arguments[0].click();", see_details_button)
                            time.sleep(1.0)
                            
                            detailed_seller_data = self._extract_from_seller_details_page()
                            seller_details_info.update(detailed_seller_data)
                            
                            if self.driver.current_url != data['basic_info']['current_url']:
                                self.driver.back()
                                time.sleep(0.5)
                                
                        except Exception as js_error:
                            self.logger.error(f"JavaScript click failed: {js_error}")
                            seller_details_info['click_error'] = str(js_error)
                    
                except Exception as click_error:
                    self.logger.error(f"Failed to click 'See details': {click_error}")
                    seller_details_info['click_error'] = str(click_error)
            else:
                self.logger.warning("'See details' button not found")
                seller_details_info['error'] = "Button not found"
            
            return seller_details_info
            
        except Exception as e:
            self.logger.error(f"Error in _click_see_details_and_extract_seller: {e}")
            return {'button_found': False, 'error': str(e)}
    
    def _extract_from_seller_details_page(self) -> Dict[str, Any]:
        """Extract seller details from the details page/popup."""
        try:
            details_data = {}
            
            # Look for seller ratings
            rating_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='rating'], [aria-label*='star']")
            if rating_elements:
                ratings = []
                for elem in rating_elements:
                    label = elem.get_attribute('aria-label') or ''
                    if label:
                        ratings.append(label)
                details_data['ratings'] = ratings
            
            # Look for response time
            page_text = self.driver.page_source.lower()
            response_patterns = [
                r'responds\s+in\s+[\w\s]+',
                r'response\s+time\s*:?\s*[\w\s]+',
                r'response\s+rate\s*:?\s*[\d.]+%'
            ]
            
            for pattern in response_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    details_data['response_info'] = matches[0]
                    break
            
            # Look for member since information
            date_patterns = [
                r'member\s+since\s+[\w\s]+\d{4}',
                r'joined\s+[\w\s]+\d{4}',
                r'on\s+facebook\s+since\s+[\w\s]+\d{4}'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    details_data['join_date'] = matches[0]
                    break
            
            # Look for verification badges
            verification_selectors = [
                "[aria-label*='verified']",
                "[data-testid*='verification']",
                "[data-testid*='verified']"
            ]
            
            for selector in verification_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        details_data['verification_badge'] = {
                            'found': True,
                            'count': len(elements),
                            'labels': [elem.get_attribute('aria-label') for elem in elements if elem.get_attribute('aria-label')]
                        }
                        break
                except:
                    continue
            
            # Look for listings count
            count_patterns = [
                r'(\d+)\s+listings?',
                r'(\d+)\s+items?\s+for\s+sale',
                r'(\d+)\s+products?'
            ]
            
            for pattern in count_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches and matches[0].isdigit():
                    details_data['listings_count'] = int(matches[0])
                    break
            
            return details_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract from seller details page: {e}")
            return {'extraction_error': str(e)}
    
    def _extract_comprehensive_product_details(self, data: Dict[str, Any]):
        """Extract comprehensive product specifications and details."""
        try:
            product_details = {}
            
            # Get page text for analysis
            page_text = self.driver.page_source.lower()
            
            # Extract iPhone model information
            title = data['basic_info']['title'].lower()
            iphone_patterns = [
                r'iphone\s*(\d+)\s*(pro\s*max|pro|plus|mini)?',
                r'iphone\s*(se|xr|xs|x)\s*(max)?'
            ]
            
            for pattern in iphone_patterns:
                matches = re.findall(pattern, title + ' ' + page_text, re.IGNORECASE)
                if matches:
                    model_parts = [part for part in matches[0] if part]
                    model_name = 'iPhone ' + ' '.join(model_parts)
                    product_details['model_name'] = model_name.strip()
                    break
            
            # Extract storage information
            storage_matches = re.findall(r'(\d+)\s*(gb|tb)', page_text, re.IGNORECASE)
            if storage_matches:
                product_details['storage'] = f"{storage_matches[0][0]} {storage_matches[0][1].upper()}"
            
            # Extract color information
            colors = ['black', 'white', 'blue', 'red', 'green', 'purple', 'pink', 'gold', 'silver', 'titanium', 'space gray', 'midnight', 'starlight']
            for color in colors:
                if color in page_text or color in title:
                    product_details['color'] = color.title()
                    break
            
            # Extract condition information
            condition_phrases = {
                'new_in_box': ['new in box', 'sealed', 'unopened', 'brand new'],
                'like_new': ['like new', 'mint condition', 'as new'],
                'good': ['good condition', 'well maintained'],
                'fair': ['fair condition', 'used', 'visible wear'],
                'poor': ['poor condition', 'damaged']
            }
            
            for condition_type, phrases in condition_phrases.items():
                if any(phrase in page_text for phrase in phrases):
                    product_details['condition'] = condition_type
                    break
            
            # Extract battery health
            battery_matches = re.findall(r'battery\s*(?:health|life)?\s*:?\s*(\d+)%', page_text, re.IGNORECASE)
            if battery_matches:
                product_details['battery_health'] = f"{battery_matches[0]}%"
            
            data['product_comprehensive'] = product_details
            
        except Exception as e:
            self.logger.error(f"Failed to extract comprehensive product details: {e}")
            data['product_comprehensive'] = {'error': str(e)}
    
    def _extract_marketplace_metadata(self, data: Dict[str, Any]):
        """Extract Facebook Marketplace specific metadata."""
        try:
            metadata = {}
            
            # Get listing ID from URL
            url = data['basic_info']['url']
            id_match = re.search(r'/item/(\d+)', url)
            if id_match:
                metadata['fb_listing_id'] = id_match.group(1)
            
            # Look for view count
            page_text = self.driver.page_source.lower()
            view_patterns = [
                r'(\d+)\s+views?',
                r'viewed\s+(\d+)\s+times',
                r'(\d+)\s+people\s+saw\s+this'
            ]
            
            for pattern in view_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches and matches[0].isdigit():
                    metadata['view_count'] = int(matches[0])
                    break
            
            # Check for sold status
            sold_indicators = ['sold', 'no longer available', 'not available']
            if any(indicator in page_text for indicator in sold_indicators):
                metadata['is_sold'] = True
            else:
                metadata['is_sold'] = False
            
            # Check for shipping availability
            shipping_indicators = ['ships to', 'shipping available', 'can ship']
            if any(indicator in page_text for indicator in shipping_indicators):
                metadata['shipping_available'] = True
            
            data['marketplace_metadata'] = metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract marketplace metadata: {e}")
            data['marketplace_metadata'] = {'error': str(e)}
    
    def _extract_all_product_images(self, data: Dict[str, Any]):
        """Extract all product images from the page."""
        try:
            images = []
            
            # Find all images on the page
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
            
            for img in img_elements:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and ('scontent' in src or 'fbcdn' in src):
                    alt_text = img.get_attribute('alt') or ''
                    
                    images.append({
                        'url': src,
                        'alt_text': alt_text,
                        'type': 'product_image'
                    })
            
            data['product_comprehensive']['images'] = images[:15]  # Limit to 15 images
            
        except Exception as e:
            self.logger.error(f"Failed to extract images: {e}")
            data['product_comprehensive']['images'] = []
    
    def _extract_full_product_description(self, data: Dict[str, Any]):
        """Extract the complete product description."""
        try:
            # Look for description content
            description_selectors = [
                "[data-testid*='description']",
                "div[role='main'] p",
                "div[role='main'] span[dir='auto']",
                "div[role='main'] div"
            ]
            
            descriptions = []
            
            for selector in description_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and 20 <= len(text) <= 2000:  # Reasonable description length
                            descriptions.append(text)
                except:
                    continue
            
            # Remove duplicates while preserving order
            unique_descriptions = []
            seen = set()
            for desc in descriptions:
                if desc not in seen:
                    unique_descriptions.append(desc)
                    seen.add(desc)
            
            data['product_comprehensive']['description'] = '\n\n'.join(unique_descriptions[:3])
            
        except Exception as e:
            self.logger.error(f"Failed to extract description: {e}")
            data['product_comprehensive']['description'] = f"Error: {str(e)}"
    
    def _extract_posting_timing_info(self, data: Dict[str, Any]):
        """Extract when the item was posted and any urgency indicators using FacebookTimeParser."""
        try:
            timing_info = {}
            
            # Get page content for time extraction
            page_html = self.driver.page_source
            page_text = page_html.lower()
            
            # Extract timing expressions from HTML using FacebookTimeParser
            from facebook_time_parser import extract_time_from_html
            timing_expressions = extract_time_from_html(page_html)
            
            if timing_expressions:
                self.logger.debug(f"Found timing expressions: {timing_expressions}")
                
                # Parse the first (most relevant) timing expression
                primary_expression = timing_expressions[0]
                parsed_minutes = self.time_parser.parse_time_expression(primary_expression)
                
                if parsed_minutes is not None:
                    # Calculate timestamp from minutes ago
                    from datetime import datetime, timedelta
                    posting_time = datetime.now() - timedelta(minutes=parsed_minutes)
                    
                    timing_info.update({
                        'facebook_time_text': primary_expression,  # Original Facebook text like "just listed"
                        'parsed_minutes_ago': parsed_minutes,      # Converted to minutes
                        'calculated_timestamp': posting_time.isoformat(),  # When it was actually posted
                        'extraction_method': 'facebook_time_parser',
                        'all_expressions_found': timing_expressions[:5]  # Keep first 5 for debugging
                    })
                    
                    self.logger.info(f"✅ Parsed timing: '{primary_expression}' = {parsed_minutes} minutes ago (posted at {posting_time.strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    timing_info.update({
                        'facebook_time_text': primary_expression,
                        'parsed_minutes_ago': None,
                        'parse_error': 'Could not parse time expression',
                        'all_expressions_found': timing_expressions[:5]
                    })
            else:
                # Fallback to basic regex patterns if no expressions found
                self.logger.debug("No timing expressions found with HTML parser, trying basic patterns...")
                
                time_patterns = [
                    r'posted\s+([^<]*ago)',
                    r'listed\s+([^<]*ago)',
                    r'(\d+)\s+(minutes?|hours?|days?|weeks?|months?)\s+ago'
                ]
                
                for pattern in time_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        time_text = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
                        parsed_minutes = self.time_parser.parse_time_expression(time_text)
                        
                        if parsed_minutes is not None:
                            from datetime import datetime, timedelta
                            posting_time = datetime.now() - timedelta(minutes=parsed_minutes)
                            
                            timing_info.update({
                                'facebook_time_text': time_text.strip(),
                                'parsed_minutes_ago': parsed_minutes,
                                'calculated_timestamp': posting_time.isoformat(),
                                'extraction_method': 'regex_fallback'
                            })
                            
                            self.logger.info(f"✅ Regex fallback parsed: '{time_text}' = {parsed_minutes} minutes ago")
                            break
                        else:
                            timing_info.update({
                                'facebook_time_text': time_text.strip(),
                                'parsed_minutes_ago': None,
                                'extraction_method': 'regex_unparseable'
                            })
            
            # Look for urgency indicators
            urgency_phrases = ['urgent', 'quick sale', 'today only', 'must sell', 'moving sale']
            found_urgency = []
            for phrase in urgency_phrases:
                if phrase in page_text:
                    found_urgency.append(phrase)
            
            if found_urgency:
                timing_info['urgency_indicators'] = found_urgency
            
            data['marketplace_metadata']['timing'] = timing_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract timing info: {e}")
            data['marketplace_metadata']['timing'] = {'error': str(e)}
    
    def _save_individual_product_report(self, data: Dict[str, Any], product_index: int):
        """Save detailed report for individual product."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save JSON data
            json_filename = f"deep_product_{product_index}_{timestamp}.json"
            json_filepath = os.path.join(self.output_dir, json_filename)
            
            import json
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved individual report: {json_filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save individual report: {e}")
    
    def _save_deep_scrape_results(self, products: List[Dict[str, Any]], search_query: str):
        """Save comprehensive results from deep scraping session."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare summary data
            summary_data = {
                'search_query': search_query,
                'extraction_timestamp': datetime.now().isoformat(),
                'total_products': len(products),
                'extraction_stats': self.deep_scrape_stats,
                'products': products
            }
            
            # Save comprehensive JSON
            summary_filename = f"deep_scrape_session_{timestamp}.json"
            summary_filepath = os.path.join(self.output_dir, summary_filename)
            
            import json
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            # Also save to main JSON manager for dashboard
            if products:
                self.json_manager.add_products_batch([
                    self._convert_to_standard_format(product) for product in products
                ])
            
            self.logger.info(f"Deep scrape results saved: {summary_filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save deep scrape results: {e}")
    
    def _convert_to_standard_format(self, deep_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert deep scraped data to standard format for main system."""
        try:
            basic_info = deep_data.get('basic_info', {})
            seller_details = deep_data.get('seller_details', {})
            product_comp = deep_data.get('product_comprehensive', {})
            
            return {
                'id': f"deep_{basic_info.get('product_id', int(time.time()))}",
                'title': basic_info.get('title', 'Unknown'),
                'price': {
                    'amount': basic_info.get('price', {}).get('amount', '0'),
                    'currency': basic_info.get('price', {}).get('currency', 'SEK'),
                    'raw_value': basic_info.get('price', {}).get('raw_price_text', 'N/A')
                },
                'location': basic_info.get('location', {}),
                'marketplace_url': basic_info.get('url', ''),
                'seller': {
                    'info': seller_details.get('seller_name', 'Private Seller'),
                    'profile': seller_details.get('profile_url')
                },
                'product_details': {
                    'model': product_comp.get('model_name', 'Unknown'),
                    'storage': product_comp.get('storage', 'Unknown'),
                    'condition': product_comp.get('condition', 'Unknown'),
                    'color': product_comp.get('color', 'Unknown')
                },
                'images': product_comp.get('images', [])[:3],  # First 3 images
                'extraction_method': 'deep_scraper',
                'data_quality': 'comprehensive',
                'added_at': datetime.now().isoformat(),
                'source': 'deep_marketplace_scraper',
                
                # Additional deep data (preserved for advanced features)
                'deep_data': {
                    'seller_details': seller_details,
                    'marketplace_metadata': deep_data.get('marketplace_metadata', {}),
                    'comprehensive_product': product_comp
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to convert to standard format: {e}")
            return {}
    
    def _save_product_immediately(self, deep_data: Dict[str, Any], product_index: int):
        """🔥 HOT RELOAD: Save deep scraped product immediately to JSON for real-time dashboard updates."""
        try:
            # Convert to standard format
            standard_product = self._convert_to_standard_format(deep_data)
            
            if standard_product:
                # Add hot reload timestamp
                standard_product['hot_reload_timestamp'] = datetime.now().isoformat()
                standard_product['scraping_status'] = 'completed'
                standard_product['scraping_method'] = 'deep'
                
                # Save immediately using hot reload method
                success = self.json_manager.add_product_hot_reload(standard_product)
                if success:
                    self.logger.info(f"🔥 Hot reload: Saved deep product {product_index} successfully")
                else:
                    self.logger.warning(f"🔥 Hot reload: Failed to save deep product {product_index}")
                
        except Exception as e:
            self.logger.error(f"Hot reload save failed for product {product_index}: {e}")
    
    def _save_product_immediately_standard(self, listing_data: Dict[str, Any], product_index: int):
        """🔥 HOT RELOAD: Save standard scraped product immediately for real-time updates."""
        try:
            # Add hot reload metadata
            listing_data['hot_reload_timestamp'] = datetime.now().isoformat()
            listing_data['scraping_status'] = 'completed'
            listing_data['scraping_method'] = 'standard'
            
            # Save immediately using hot reload method
            success = self.json_manager.add_product_hot_reload(listing_data)
            if success:
                self.logger.debug(f"🔥 Hot reload: Standard product {product_index} saved successfully")
            else:
                self.logger.warning(f"🔥 Hot reload: Failed to save standard product {product_index}")
            
        except Exception as e:
            self.logger.error(f"Hot reload save failed for standard product {product_index}: {e}")
    
    def _send_product_completion_notification(self, deep_data: Dict[str, Any], product_index: int, total_products: int):
        """Send real-time notification when a deep scraped product is completed."""
        try:
            basic_info = deep_data.get('basic_info', {})
            title = basic_info.get('title', 'Unknown Product')
            price_info = basic_info.get('price', {})
            price_amount = price_info.get('amount', '0')
            price_currency = price_info.get('currency', 'SEK')
            
            # Get seller info if available
            seller_details = deep_data.get('seller_details', {})
            seller_name = seller_details.get('seller_name', 'Unknown Seller')
            
            self._send_scraping_notification('deep_product_completed', {
                'product_index': product_index,
                'total_products': total_products,
                'product_title': title[:50],
                'product_price': price_amount,
                'product_currency': price_currency,
                'seller_name': seller_name,
                'completion_timestamp': datetime.now().isoformat(),
                'progress_percentage': round((product_index / total_products) * 100, 1),
                'message': f'✅ Completed {product_index}/{total_products}: {title[:30]}... ({price_amount} {price_currency})'
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send product completion notification: {e}")
    
    def _send_standard_product_notification(self, listing_data: Dict[str, Any], product_index: int, total_products: int):
        """Send real-time notification when a standard scraped product is completed."""
        try:
            title = listing_data.get('title', 'Unknown Product')
            price_info = listing_data.get('price', {})
            price_amount = price_info.get('amount', '0')
            price_currency = price_info.get('currency', 'SEK')
            
            self._send_scraping_notification('standard_product_completed', {
                'product_index': product_index,
                'total_products': total_products,
                'product_title': title[:50],
                'product_price': price_amount,
                'product_currency': price_currency,
                'completion_timestamp': datetime.now().isoformat(),
                'progress_percentage': round((product_index / total_products) * 100, 1),
                'message': f'📦 Found {product_index}/{total_products}: {title[:30]}... ({price_amount} {price_currency})'
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send standard product notification: {e}")
    
    def _enhance_listing_with_real_data(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """🔥 ENHANCED EXTRACTION: Visit product page and extract real data."""
        try:
            if not self.enhanced_extraction['enabled']:
                return listing_data
            
            product_url = listing_data.get('marketplace_url')
            if not product_url:
                return listing_data
            
            original_url = self.driver.current_url
            product_id = listing_data.get('id', 'unknown')
            
            self.logger.info(f"🔥 Enhancing listing {product_id} with real data from product page")
            
            try:
                # Navigate to product page
                self.driver.get(product_url)
                time.sleep(2)
                
                # Extract real price
                if self.enhanced_extraction['extract_real_prices']:
                    real_price = self._extract_enhanced_price_from_page()
                    if real_price:
                        listing_data['enhanced_price'] = real_price
                        # Update main price with real data
                        listing_data['price'] = {
                            'amount': real_price.get('amount', listing_data['price']['amount']),
                            'currency': real_price.get('currency', listing_data['price']['currency']),
                            'raw_value': real_price.get('raw', listing_data['price']['raw_value'])
                        }
                
                # Extract real location
                real_location = self._extract_enhanced_location_from_page()
                if real_location:
                    listing_data['enhanced_location'] = real_location
                    # Update main location with real data
                    listing_data['location'] = real_location
                
                # Extract real seller information
                if self.enhanced_extraction['extract_real_seller_names']:
                    real_seller = self._extract_enhanced_seller_from_page(product_id)
                    if real_seller:
                        listing_data['enhanced_seller'] = real_seller
                        # Update main seller info
                        if real_seller.get('name'):
                            listing_data['seller'] = {
                                'info': real_seller['name'],
                                'profile': real_seller.get('profile_url', listing_data['seller'].get('profile'))
                            }
                            listing_data['seller_name'] = real_seller['name']
                
                # Extract enhanced product details
                enhanced_details = self._extract_enhanced_product_details_from_page()
                if enhanced_details:
                    listing_data['enhanced_details'] = enhanced_details
                    
                    # Update main product details
                    for key, value in enhanced_details.items():
                        if key in listing_data['product_details'] and value != 'Unknown':
                            listing_data['product_details'][key] = value
                
                # Mark as enhanced
                listing_data['enhancement_status'] = 'enhanced'
                listing_data['enhancement_timestamp'] = datetime.now().isoformat()
                
                # Navigate back
                self.driver.get(original_url)
                time.sleep(1)
                
                self.logger.info(f"✅ Successfully enhanced listing {product_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to enhance listing {product_id}: {e}")
                listing_data['enhancement_status'] = 'failed'
                listing_data['enhancement_error'] = str(e)
                
                # Try to navigate back even on error
                try:
                    self.driver.get(original_url)
                    time.sleep(1)
                except:
                    pass
            
            return listing_data
            
        except Exception as e:
            self.logger.error(f"Enhanced extraction failed: {e}")
            return listing_data
    
    def _extract_enhanced_price_from_page(self) -> Optional[Dict[str, Any]]:
        """Extract real price from product page."""
        try:
            # Multiple price selectors for different layouts
            price_selectors = [
                "[data-testid*='price']",
                ".x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1s688f",
                ".x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.xl56j7k"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if price_elem and price_elem.text.strip():
                        raw_price = price_elem.text.strip()
                        
                        # Parse the price
                        price_match = re.search(r'(AU\$|USD\$|\$)?\s*([0-9,]+)', raw_price)
                        if price_match:
                            return {
                                'currency_symbol': price_match.group(1) or '$',
                                'amount': price_match.group(2).replace(',', ''),
                                'currency': 'AUD' if 'AU' in raw_price else 'USD',
                                'raw': raw_price
                            }
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced price: {e}")
            return None
    
    def _extract_enhanced_location_from_page(self) -> Optional[Dict[str, Any]]:
        """Extract real location from product page."""
        try:
            location_selectors = [
                "[data-testid*='location']",
                ".x1i10hfl.x1qjc9v5.xjbqb8w.xjqpnuy",
                "*[class*='location']"
            ]
            
            for selector in location_selectors:
                try:
                    loc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if loc_elem and loc_elem.text.strip():
                        location_text = loc_elem.text.strip()
                        if len(location_text) < 100:  # Reasonable location length
                            return {
                                'city': location_text,
                                'distance': 'Unknown',
                                'raw_location': location_text
                            }
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced location: {e}")
            return None
    
    def _extract_enhanced_seller_from_page(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Extract real seller information by visiting seller profile."""
        try:
            if not self.enhanced_extraction['visit_seller_profiles']:
                return None
            
            seller_data = {
                'extraction_method': 'enhanced_scraper',
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # Look for seller profile links
            profile_link_selectors = [
                "a[href*='/marketplace/profile/']",
                "a[href*='facebook.com/profile.php']",
                "a[href*='/people/']"
            ]
            
            seller_profile_url = None
            for selector in profile_link_selectors:
                try:
                    link_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link_elem in link_elems:
                        href = link_elem.get_attribute('href')
                        if href and ('profile' in href or 'people' in href):
                            seller_profile_url = href
                            break
                    if seller_profile_url:
                        break
                except Exception:
                    continue
            
            if not seller_profile_url:
                return seller_data
            
            # Visit seller profile
            current_url = self.driver.current_url
            try:
                self.driver.get(seller_profile_url)
                time.sleep(2)
                
                # Extract seller name
                name_selectors = [
                    "h1[data-testid*='name']",
                    ".x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz h1",
                    "h1.x1heor9g",
                    "h1"
                ]
                
                for selector in name_selectors:
                    try:
                        name_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if name_elem and name_elem.text.strip():
                            name_text = name_elem.text.strip()
                            if len(name_text) < 100 and name_text.lower() not in ['facebook', 'marketplace']:
                                seller_data['name'] = name_text
                                break
                    except NoSuchElementException:
                        continue
                
                seller_data['profile_url'] = seller_profile_url
                seller_data['profile_visited'] = True
                
                # Navigate back
                self.driver.get(current_url)
                time.sleep(1)
                
                return seller_data
                
            except Exception as e:
                # Navigate back on error
                try:
                    self.driver.get(current_url)
                    time.sleep(1)
                except:
                    pass
                
                seller_data['error'] = str(e)
                seller_data['profile_visited'] = False
                return seller_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced seller info: {e}")
            return None
    
    def _extract_enhanced_product_details_from_page(self) -> Optional[Dict[str, Any]]:
        """Extract enhanced product details from current page."""
        try:
            details = {}
            page_text = self.driver.page_source.lower()
            
            # Extract storage information
            storage_matches = re.findall(r'(\d+)\s*(gb|tb)', page_text, re.IGNORECASE)
            if storage_matches:
                details['storage'] = f"{storage_matches[0][0]} {storage_matches[0][1].upper()}"
            
            # Extract color information
            colors = ['black', 'white', 'blue', 'red', 'green', 'purple', 'pink', 'gold', 'silver', 'titanium']
            for color in colors:
                if color in page_text:
                    details['color'] = color.title()
                    break
            
            # Extract condition
            condition_phrases = {
                'new_in_box': ['new in box', 'sealed', 'unopened', 'brand new'],
                'like_new': ['like new', 'mint condition', 'as new'],
                'good': ['good condition', 'well maintained'],
                'fair': ['fair condition', 'used', 'visible wear']
            }
            
            for condition_type, phrases in condition_phrases.items():
                if any(phrase in page_text for phrase in phrases):
                    details['condition'] = condition_type
                    break
            
            return details if details else None
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced product details: {e}")
            return None
    
    def _extract_timing_from_element(self, element) -> Dict[str, Any]:
        """Extract Facebook timing information from listing element using FacebookTimeParser."""
        try:
            timing_info = {}
            
            # Get element HTML and text for timing extraction
            element_html = element.get_attribute('outerHTML')
            element_text = element.text
            
            # First try to extract timing expressions from the element HTML
            from facebook_time_parser import extract_time_from_html
            timing_expressions = extract_time_from_html(element_html)
            
            if timing_expressions:
                self.logger.debug(f"Found timing expressions in element: {timing_expressions}")
                
                # Parse the first (most relevant) timing expression
                primary_expression = timing_expressions[0]
                parsed_minutes = self.time_parser.parse_time_expression(primary_expression)
                
                if parsed_minutes is not None:
                    # Calculate timestamp from minutes ago
                    from datetime import datetime, timedelta
                    posting_time = datetime.now() - timedelta(minutes=parsed_minutes)
                    
                    timing_info.update({
                        'facebook_time_text': primary_expression,  # Original Facebook text like "just listed"
                        'parsed_minutes_ago': parsed_minutes,      # Converted to minutes
                        'calculated_timestamp': posting_time.isoformat(),  # When it was actually posted
                        'extraction_method': 'facebook_time_parser_element',
                        'all_expressions_found': timing_expressions[:3]  # Keep first 3 for debugging
                    })
                    
                    self.logger.debug(f"⏰ Element timing: '{primary_expression}' = {parsed_minutes} minutes ago")
                else:
                    timing_info.update({
                        'facebook_time_text': primary_expression,
                        'parsed_minutes_ago': None,
                        'parse_error': 'Could not parse time expression',
                        'extraction_method': 'facebook_time_parser_element_failed',
                        'all_expressions_found': timing_expressions[:3]
                    })
            else:
                # Fallback: Look for timing patterns in element text
                element_text_lower = element_text.lower() if element_text else ''
                
                # Common timing patterns for listing cards
                time_patterns = [
                    r'(\d+)\s*(m|h|d|w)\b',  # 3h, 1w, 23h, 5m
                    r'(just\s+listed|moments\s+ago|yesterday|today)',  # Text expressions
                    r'(\d+)\s+(minutes?|hours?|days?|weeks?)\s+ago'
                ]
                
                for pattern in time_patterns:
                    matches = re.findall(pattern, element_text_lower, re.IGNORECASE)
                    if matches:
                        time_text = matches[0] if isinstance(matches[0], str) else ' '.join(str(x) for x in matches[0] if x)
                        parsed_minutes = self.time_parser.parse_time_expression(time_text)
                        
                        if parsed_minutes is not None:
                            from datetime import datetime, timedelta
                            posting_time = datetime.now() - timedelta(minutes=parsed_minutes)
                            
                            timing_info.update({
                                'facebook_time_text': time_text.strip(),
                                'parsed_minutes_ago': parsed_minutes,
                                'calculated_timestamp': posting_time.isoformat(),
                                'extraction_method': 'regex_element_text'
                            })
                            
                            self.logger.debug(f"⏰ Element regex: '{time_text}' = {parsed_minutes} minutes ago")
                            break
                        else:
                            timing_info.update({
                                'facebook_time_text': time_text.strip(),
                                'parsed_minutes_ago': None,
                                'extraction_method': 'regex_element_unparseable'
                            })
            
            # If no timing info found, set default values
            if not timing_info:
                timing_info = {
                    'facebook_time_text': None,
                    'parsed_minutes_ago': None,
                    'calculated_timestamp': None,
                    'extraction_method': 'none_found'
                }
            
            return timing_info
            
        except Exception as e:
            self.logger.debug(f"Failed to extract timing from element: {e}")
            return {
                'facebook_time_text': None,
                'parsed_minutes_ago': None,
                'calculated_timestamp': None,
                'extraction_method': 'error',
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if not self.persistent_session:
            # Only auto-close if not in persistent mode
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
