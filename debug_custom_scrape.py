#!/usr/bin/env python3
"""
Debug script to test seller detail extraction from product pages
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import Settings


class SellerDetailExtractor:
    """Extracts detailed seller information from Facebook Marketplace product pages."""
    
    def __init__(self, settings):
        """Initialize the seller detail extractor."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        self.credentials = settings.get_facebook_credentials()
        
        # Create output directory for HTML files
        self.output_dir = "seller_debug_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup detailed logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{self.output_dir}/seller_extraction.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with optimized settings."""
        try:
            chrome_options = Options()
            
            # Use visible browser for debugging
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Anti-detection measures
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional anti-detection
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, 10)
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def login_to_facebook(self):
        """Login to Facebook using provided credentials."""
        try:
            self.logger.info("Starting Facebook login...")
            
            # Navigate to Facebook login page
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Find and fill email field
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.credentials['email'])
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(self.credentials['password'])
            
            # Submit login form
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            time.sleep(5)
            
            # Check for successful login
            if self._is_logged_in():
                self.logger.info("Successfully logged in to Facebook")
                return True
            else:
                self.logger.error("Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def _is_logged_in(self):
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
    
    def navigate_to_marketplace_search(self, search_query="iphone 16"):
        """Navigate to marketplace with search query."""
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.facebook.com/marketplace/stockholm/search/?query={encoded_query}"
            
            self.logger.info(f"Navigating to search: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)
            
            # Wait for marketplace to load
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-surface='marketplace']"))
                    )
                )
                self.logger.info("Successfully navigated to Marketplace search")
                return True
            except TimeoutException:
                self.logger.warning("Marketplace may not have loaded properly")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to marketplace: {e}")
            return False
    
    def find_product_cards(self):
        """Find all product cards on the current page."""
        try:
            self.logger.info("Looking for product cards...")
            
            # Wait for content to load
            time.sleep(3)
            
            # Find marketplace item links
            marketplace_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            self.logger.info(f"Found {len(marketplace_links)} marketplace item links")
            
            # Extract URLs and create clickable elements info
            product_cards = []
            for i, link in enumerate(marketplace_links[:5]):  # Limit to first 5 for debugging
                try:
                    url = link.get_attribute('href')
                    if url and '/marketplace/item/' in url:
                        # Try to get product title from link or parent
                        title = ""
                        try:
                            # Look for text in the link or its parent
                            link_text = link.text.strip()
                            if link_text and len(link_text) > 5:
                                title = link_text
                            else:
                                # Look in parent elements
                                parent = link
                                for level in range(3):
                                    parent = parent.find_element(By.XPATH, "..")
                                    parent_text = parent.text.strip()
                                    if parent_text and len(parent_text) > 10:
                                        # Extract first meaningful line as title
                                        lines = parent_text.split('\n')
                                        for line in lines:
                                            line = line.strip()
                                            if len(line) > 5 and not line.startswith('SEK') and not line.replace(',','').isdigit():
                                                title = line
                                                break
                                        break
                        except:
                            title = f"Product {i+1}"
                        
                        product_cards.append({
                            'index': i,
                            'title': title or f"Product {i+1}",
                            'url': url,
                            'element': link
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process link {i}: {e}")
                    continue
            
            self.logger.info(f"Prepared {len(product_cards)} product cards for detail extraction")
            return product_cards
            
        except Exception as e:
            self.logger.error(f"Failed to find product cards: {e}")
            return []
    
    def extract_seller_details(self, product_url, product_title, index):
        """Extract detailed seller information from product page."""
        try:
            self.logger.info(f"Extracting seller details for: {product_title}")
            
            # Navigate to product page
            self.driver.get(product_url)
            time.sleep(4)
            
            # Save initial page source
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            initial_filename = f"product_page_initial_{index}_{timestamp}.html"
            initial_filepath = os.path.join(self.output_dir, initial_filename)
            
            with open(initial_filepath, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            self.logger.info(f"Initial page source saved to: {initial_filepath}")
            
            # Extract detailed information
            extracted_data = {
                'product_url': product_url,
                'product_title': product_title,
                'extraction_timestamp': datetime.now().isoformat(),
                'page_title': self.driver.title,
                'current_url': self.driver.current_url,
                'seller_info': {},
                'seller_details_info': {},  # New section for "See details" data
                'product_details': {},
                'contact_info': {},
                'location_details': {},
                'timing_info': {},
                'additional_images': [],
                'description': "",
                'raw_text_sections': [],
                'page_sources': {
                    'initial_page': initial_filename
                }
            }
            
            # Extract basic seller information first
            self._extract_seller_info(extracted_data)
            
            # Try to click "See details" button and extract additional seller info
            see_details_data = self._click_see_details_and_extract(extracted_data, index, timestamp)
            extracted_data['seller_details_info'] = see_details_data
            
            # Extract comprehensive product information
            self._extract_comprehensive_product_details(extracted_data)
            
            # Extract timing and posting information
            self._extract_timing_info(extracted_data)
            
            # Extract contact and location details
            self._extract_contact_location(extracted_data)
            
            # Extract additional images
            self._extract_product_images(extracted_data)
            
            # Extract product description
            self._extract_product_description(extracted_data)
            
            # Extract marketplace-specific metadata
            self._extract_marketplace_metadata(extracted_data)
            
            # Save extracted data as JSON
            json_filename = f"extracted_data_{index}_{timestamp}.json"
            json_filepath = os.path.join(self.output_dir, json_filename)
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Extracted data saved to: {json_filepath}")
            
            # Create formatted HTML report
            self._create_html_report(extracted_data, index, timestamp)
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract seller details: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _extract_seller_info(self, data):
        """Extract seller-specific information."""
        try:
            # Common selectors for seller information
            seller_selectors = [
                "[data-testid*='seller']",
                "[data-testid*='profile']",
                "a[href*='/profile/']",
                "a[href*='/people/']",
                "[role='link'][href*='/profile/']",
                "div[data-surface-wrapper] a[role='link']"
            ]
            
            seller_info = {}
            
            for selector in seller_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        href = element.get_attribute('href') or ''
                        
                        if text and '/profile/' in href:
                            seller_info[f'seller_from_{selector}'] = {
                                'text': text,
                                'profile_url': href
                            }
                            break
                except:
                    continue
            
            # Look for rating/reviews information
            rating_selectors = [
                "*[aria-label*='star']",
                "*[aria-label*='rating']",
                "*[data-testid*='rating']",
                "span:contains('★')",
                "span:contains('⭐')"
            ]
            
            for selector in rating_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and ('★' in text or '⭐' in text or 'star' in text.lower()):
                            seller_info['rating_info'] = text
                            break
                except:
                    continue
            
            # Look for join date or member since information
            member_selectors = [
                "*:contains('Member since')",
                "*:contains('Joined')",
                "*:contains('member')",
                "span[dir='auto']"
            ]
            
            page_text = self.driver.page_source.lower()
            if 'member since' in page_text or 'joined' in page_text:
                # Extract the relevant text
                import re
                member_matches = re.findall(r'(member since|joined)[^<]*\d{4}', page_text, re.IGNORECASE)
                if member_matches:
                    seller_info['member_since'] = member_matches[0]
            
            data['seller_info'] = seller_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract seller info: {e}")
            data['seller_info'] = {'error': str(e)}
    
    def _click_see_details_and_extract(self, data, index, timestamp):
        """Click on 'See details' button and extract seller details from popup/page."""
        try:
            self.logger.info("Looking for 'See details' button...")
            
            # Various selectors to find the "See details" button
            see_details_selectors = [
                "a:contains('See details')",
                "a:contains('View profile')",
                "a:contains('See seller')",
                "a:contains('Seller information')",
                "a[href*='/profile/']:contains('See')",
                "span:contains('See details')",
                "div[role='button']:contains('See details')",
                "div[role='button']:contains('View profile')",
                "div[data-testid*='profile']",
                "div[role='link'][tabindex='0']:contains('View profile')"
            ]
            
            # Try to find and click the button
            see_details_button = None
            for selector in see_details_selectors:
                try:
                    # Use JavaScript-friendly selectors as fallback
                    if ':contains(' in selector:
                        text_part = selector.split(':contains(')[1].strip(')').strip('\'"')
                        base_selector = selector.split(':contains(')[0]
                        
                        # Find elements using base selector and filter by text
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
            
            # Alternative method: look for any links with profile in the href
            if not see_details_button:
                try:
                    profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/profile/']")
                    if profile_links:
                        self.logger.info(f"Found profile link as alternative to 'See details' button")
                        see_details_button = profile_links[0]
                except Exception as e:
                    self.logger.debug(f"Profile link fallback failed: {e}")
            
            # If button found, click it and extract data
            if see_details_button:
                # Save button properties before clicking
                button_text = see_details_button.text.strip()
                button_href = see_details_button.get_attribute('href')
                button_classes = see_details_button.get_attribute('class')
                
                seller_details_info = {
                    'button_found': True,
                    'button_text': button_text,
                    'button_href': button_href,
                    'button_classes': button_classes
                }
                
                self.logger.info(f"Clicking 'See details' button: {button_text}")
                
                # Try clicking the button
                try:
                    # First try direct click
                    see_details_button.click()
                    time.sleep(3)
                    
                    # Save page after click
                    details_filename = f"seller_details_page_{index}_{timestamp}.html"
                    details_filepath = os.path.join(self.output_dir, details_filename)
                    
                    with open(details_filepath, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    
                    self.logger.info(f"Seller details page saved to: {details_filepath}")
                    seller_details_info['details_page_filename'] = details_filename
                    
                    # Extract information from details page
                    seller_details_info.update(self._extract_from_details_page())
                    
                    # Check if we navigated to a new page and need to go back
                    if self.driver.current_url != data['current_url']:
                        self.logger.info("Navigated to new page, going back to product page")
                        self.driver.back()
                        time.sleep(2)
                        
                except ElementNotInteractableException:
                    # Try JavaScript click as fallback
                    self.logger.info("Direct click failed, trying JavaScript click")
                    try:
                        self.driver.execute_script("arguments[0].click();", see_details_button)
                        time.sleep(3)
                        
                        # Save page after JS click
                        details_filename = f"seller_details_js_click_{index}_{timestamp}.html"
                        details_filepath = os.path.join(self.output_dir, details_filename)
                        
                        with open(details_filepath, 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        
                        self.logger.info(f"Seller details page (JS click) saved to: {details_filepath}")
                        seller_details_info['details_page_filename'] = details_filename
                        
                        # Extract information from details page
                        seller_details_info.update(self._extract_from_details_page())
                        
                        # Check if we navigated to a new page and need to go back
                        if self.driver.current_url != data['current_url']:
                            self.logger.info("Navigated to new page, going back to product page")
                            self.driver.back()
                            time.sleep(2)
                            
                    except Exception as js_click_error:
                        self.logger.error(f"JavaScript click failed: {js_click_error}")
                        seller_details_info['click_error'] = str(js_click_error)
                
                except Exception as click_error:
                    self.logger.error(f"Failed to click 'See details' button: {click_error}")
                    seller_details_info['click_error'] = str(click_error)
                
                return seller_details_info
                
            else:
                self.logger.warning("'See details' button not found")
                return {'button_found': False, 'error': "Button not found"}
                
        except Exception as e:
            self.logger.error(f"Error in _click_see_details_and_extract: {e}")
            return {'button_found': False, 'error': str(e)}
    
    def _extract_from_details_page(self):
        """Extract seller details from the seller details page/popup."""
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
            response_time_text = None
            response_patterns = [
                r'responds\s+in\s+[\w\s]+',
                r'response\s+time\s*:?\s*[\w\s]+',
                r'response\s+rate\s*:?\s*[\d.]+%'
            ]
            
            page_text = self.driver.page_source.lower()
            for pattern in response_patterns:
                import re
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    response_time_text = matches[0]
                    break
            
            if response_time_text:
                details_data['response_info'] = response_time_text
            
            # Look for member since information
            join_date_text = None
            date_patterns = [
                r'member\s+since\s+[\w\s]+\d{4}',
                r'joined\s+[\w\s]+\d{4}',
                r'on\s+facebook\s+since\s+[\w\s]+\d{4}'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    join_date_text = matches[0]
                    break
            
            if join_date_text:
                details_data['join_date'] = join_date_text
            
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
            
            # Look for listings count or other metrics
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
            
            # Extract any other profiles or links
            profile_links = []
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/profile/'], a[href*='/people/']")
            for link in link_elements:
                href = link.get_attribute('href')
                text = link.text.strip()
                if href and text:
                    profile_links.append({'url': href, 'text': text})
            
            if profile_links:
                details_data['profile_links'] = profile_links
            
            return details_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract from details page: {e}")
            return {'extraction_error': str(e)}
    
    def _extract_comprehensive_product_details(self, data):
        """Extract comprehensive product details including all important aspects."""
        # First run the basic product details extraction
        self._extract_product_details(data)
        
        try:
            product_details = data.get('product_details', {})
            
            # Extract model and series information
            title = data.get('product_title', '').lower()
            page_text = ' '.join(data.get('raw_text_sections', [])).lower()
            
            # iPhone model detection (more comprehensive)
            iphone_model_patterns = [
                r'iphone\s*(\d+)\s*(pro\s*max|pro|plus|mini)?',
                r'iphone\s*(\d+)\s*(\d+)?\s*(gb|tb)'
            ]
            
            import re
            for pattern in iphone_model_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    model_parts = [part for part in matches[0] if part]
                    model_name = 'iPhone ' + ' '.join(model_parts)
                    product_details['model_name'] = model_name.strip()
                    break
            
            # Extract price more precisely
            price_patterns = [
                r'(\d[\d,\s]*[\d])\s*(kr|sek)',  # Price with currency after
                r'(kr|sek)\s*(\d[\d,\s]*[\d])',  # Currency before price
                r'(\d[\d,\s]*[\d])\s*:-'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    if 'kr' in matches[0] or 'sek' in matches[0]:
                        # Handle different price formats
                        price_parts = [part.strip() for part in matches[0] if part.strip()]
                        numeric_part = next((part for part in price_parts if any(c.isdigit() for c in part)), '')
                        currency_part = next((part for part in price_parts if part.lower() in ['kr', 'sek']), 'SEK')
                        
                        if numeric_part:
                            clean_number = numeric_part.replace(' ', '').replace(',', '')
                            product_details['price_exact'] = {
                                'amount': clean_number,
                                'currency': currency_part.upper(),
                                'raw_text': f"{' '.join(price_parts)}"
                            }
                            break
            
            # Extract condition in more detail
            condition_phrases = {
                'new_in_box': ['new in box', 'sealed', 'unopened', 'new in packaging', 'brand new'],
                'like_new': ['like new', 'mint condition', 'as new', 'pristine'],
                'good': ['good condition', 'well maintained', 'lightly used'],
                'fair': ['fair condition', 'used', 'visible wear'],
                'poor': ['poor condition', 'heavily used', 'damaged']
            }
            
            for condition_type, phrases in condition_phrases.items():
                if any(phrase in page_text for phrase in phrases):
                    product_details['condition_detailed'] = condition_type
                    break
            
            # Extract additional specifications
            spec_patterns = {
                'storage': r'(\d+)\s*(gb|tb)',
                'color': r'colou?r\s*:?\s*([\w\s]+)',
                'battery_health': r'battery\s*(health|life)\s*:?\s*(\d+)%',
                'warranty': r'warranty\s*:?\s*([\w\s]+)'  
            }
            
            for spec_name, pattern in spec_patterns.items():
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    if spec_name == 'storage' and matches[0][0].isdigit():
                        product_details[spec_name] = f"{matches[0][0]} {matches[0][1].upper()}"
                    elif spec_name == 'battery_health' and len(matches[0]) > 1:
                        product_details[spec_name] = f"{matches[0][1]}%"
                    else:
                        product_details[spec_name] = matches[0].strip() if isinstance(matches[0], str) else matches[0][0].strip()
            
            # Update the data
            data['product_details'] = product_details
            
        except Exception as e:
            self.logger.error(f"Failed to extract comprehensive product details: {e}")
    
    def _extract_timing_info(self, data):
        """Extract timing information such as when item was posted."""
        try:
            timing_info = {}
            
            # Look for posting time information
            time_patterns = [
                r'posted\s+([\w\s]+ago)',
                r'listed\s+([\w\s]+ago)',
                r'(\d+)\s+(minutes|hours|days|weeks|months)\s+ago',
                r'posted\s+on\s+([\w\s]+\d{1,2},\s*\d{4})',
                r'published\s+on\s+([\w\s]+\d{1,2})',
                r'added\s+([\w\s]+ago)'
            ]
            
            page_text = ' '.join(data.get('raw_text_sections', [])).lower()
            
            import re
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    # Extract the time information
                    time_text = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
                    timing_info['posted_time'] = time_text.strip()
                    
                    # Try to parse the time to create an approximate timestamp
                    try:
                        from datetime import datetime, timedelta
                        
                        now = datetime.now()
                        time_text_lower = time_text.lower()
                        
                        if 'minute' in time_text_lower:
                            minutes = int(re.search(r'(\d+)', time_text_lower).group(1))
                            estimated_time = now - timedelta(minutes=minutes)
                        elif 'hour' in time_text_lower:
                            hours = int(re.search(r'(\d+)', time_text_lower).group(1))
                            estimated_time = now - timedelta(hours=hours)
                        elif 'day' in time_text_lower:
                            days = int(re.search(r'(\d+)', time_text_lower).group(1))
                            estimated_time = now - timedelta(days=days)
                        elif 'week' in time_text_lower:
                            weeks = int(re.search(r'(\d+)', time_text_lower).group(1))
                            estimated_time = now - timedelta(days=weeks*7)
                        elif 'month' in time_text_lower:
                            months = int(re.search(r'(\d+)', time_text_lower).group(1))
                            estimated_time = now - timedelta(days=months*30)
                        else:
                            estimated_time = None
                        
                        if estimated_time:
                            timing_info['estimated_timestamp'] = estimated_time.isoformat()
                    except Exception as time_parse_error:
                        self.logger.debug(f"Failed to parse time: {time_parse_error}")
                    
                    break
            
            # Look for time sensitive phrases
            urgency_phrases = ['urgent', 'quick sale', 'today only', 'immediate pickup', 'last chance']
            for phrase in urgency_phrases:
                if phrase in page_text:
                    if 'urgency_indicators' not in timing_info:
                        timing_info['urgency_indicators'] = []
                    timing_info['urgency_indicators'].append(phrase)
            
            # Set the timing info in the data
            data['timing_info'] = timing_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract timing info: {e}")
            data['timing_info'] = {'error': str(e)}
    
    def _extract_marketplace_metadata(self, data):
        """Extract Facebook Marketplace specific metadata."""
        try:
            metadata = {}
            
            # Extract listing ID from URL
            url = data.get('current_url', '')
            import re
            id_match = re.search(r'/item/(\d+)', url)
            if id_match:
                metadata['fb_listing_id'] = id_match.group(1)
            
            # Look for view count information
            page_text = ' '.join(data.get('raw_text_sections', [])).lower()
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
            
            # Look for category information
            category_patterns = [
                r'category\s*:?\s*([\w\s&]+)',
                r'listed\s+in\s+([\w\s&]+)'
            ]
            
            for pattern in category_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    metadata['category'] = matches[0].strip()
                    break
            
            # Check if it's marked as sold
            sold_indicators = ['sold', 'no longer available', 'not available']
            if any(indicator in page_text for indicator in sold_indicators):
                metadata['is_sold'] = True
            
            # Check if it's available for shipping
            shipping_indicators = ['ships to', 'shipping available', 'can ship']
            if any(indicator in page_text for indicator in shipping_indicators):
                metadata['shipping_available'] = True
            
            # Set the metadata in the data
            data['marketplace_metadata'] = metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract marketplace metadata: {e}")
            data['marketplace_metadata'] = {'error': str(e)}
    
    def _extract_product_details(self, data):
        """Extract detailed product information."""
        try:
            # Look for detailed product specs
            detail_selectors = [
                "[data-testid*='description']",
                "[data-testid*='details']",
                "div[role='main'] div",
                "span[dir='auto']"
            ]
            
            product_details = {}
            all_text_elements = []
            
            # Collect all meaningful text from the page
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, "span, div, p")
            for element in text_elements:
                text = element.text.strip()
                if text and len(text) > 3 and len(text) < 200:
                    all_text_elements.append(text)
            
            # Look for specific product attributes
            page_text = ' '.join(all_text_elements).lower()
            
            # Storage information
            import re
            storage_matches = re.findall(r'(\d+)\s*(gb|tb)', page_text, re.IGNORECASE)
            if storage_matches:
                product_details['storage'] = f"{storage_matches[0][0]} {storage_matches[0][1].upper()}"
            
            # Color information
            colors = ['black', 'white', 'blue', 'red', 'green', 'purple', 'pink', 'gold', 'silver', 'titanium']
            for color in colors:
                if color in page_text:
                    product_details['color'] = color.title()
                    break
            
            # Condition information
            conditions = ['new', 'used', 'refurbished', 'excellent', 'good', 'fair', 'begagnad', 'ny', 'oanvänd']
            for condition in conditions:
                if condition in page_text:
                    product_details['condition'] = condition.title()
                    break
            
            # Price information (more detailed)
            price_matches = re.findall(r'(sek|kr)\s*([\d,]+)', page_text, re.IGNORECASE)
            if price_matches:
                product_details['price_detailed'] = f"{price_matches[0][1]} {price_matches[0][0].upper()}"
            
            data['product_details'] = product_details
            data['raw_text_sections'] = all_text_elements[:50]  # First 50 text elements
            
        except Exception as e:
            self.logger.error(f"Failed to extract product details: {e}")
            data['product_details'] = {'error': str(e)}
    
    def _extract_contact_location(self, data):
        """Extract contact and location information."""
        try:
            contact_info = {}
            location_details = {}
            
            # Look for location information
            location_selectors = [
                "*:contains('Stockholm')",
                "*:contains('km')",
                "[data-testid*='location']",
                "span[dir='auto']"
            ]
            
            page_source = self.driver.page_source
            
            # Extract location using regex patterns
            import re
            location_patterns = [
                r'([\w\s]+)\s+(\d+)\s*km',  # City 15 km
                r'(\d+)\s*km\s+from\s+([\w\s]+)',  # 15 km from City
                r'Stockholm[^<]*',  # Any Stockholm reference
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    location_details[f'pattern_{pattern[:20]}'] = matches[:3]  # First 3 matches
            
            # Look for contact buttons or messaging options
            contact_selectors = [
                "button:contains('Message')",
                "button:contains('Contact')",
                "a:contains('Message')",
                "[aria-label*='Message']",
                "[aria-label*='Contact']"
            ]
            
            for selector in contact_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        contact_info[f'contact_option_{selector[:20]}'] = len(elements)
                except:
                    continue
            
            data['contact_info'] = contact_info
            data['location_details'] = location_details
            
        except Exception as e:
            self.logger.error(f"Failed to extract contact/location: {e}")
            data['contact_info'] = {'error': str(e)}
            data['location_details'] = {'error': str(e)}
    
    def _extract_product_images(self, data):
        """Extract additional product images."""
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
                        'type': 'product_detail'
                    })
            
            data['additional_images'] = images[:10]  # Limit to 10 images
            
        except Exception as e:
            self.logger.error(f"Failed to extract images: {e}")
            data['additional_images'] = []
    
    def _extract_product_description(self, data):
        """Extract product description text."""
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
                        if text and len(text) > 20 and len(text) < 1000:
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
            
            data['description'] = '\n\n'.join(unique_descriptions[:5])  # Top 5 unique descriptions
            
        except Exception as e:
            self.logger.error(f"Failed to extract description: {e}")
            data['description'] = f"Error: {str(e)}"
    
    def _create_html_report(self, extracted_data, index, timestamp):
        """Create a formatted HTML report of extracted data."""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Seller Details Report - Product {index}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; background: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .section {{ margin-bottom: 25px; padding: 20px; border: 1px solid #e1e5e9; border-radius: 12px; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .section h3 {{ color: #495057; border-bottom: 3px solid #dee2e6; padding-bottom: 12px; margin-bottom: 15px; font-size: 1.3em; }}
        .data-grid {{ display: grid; grid-template-columns: 200px 1fr; gap: 12px; margin-bottom: 15px; }}
        .label {{ font-weight: 600; color: #6c757d; }}
        .value {{ color: #212529; }}
        .json-block {{ background: #f8f9fa; padding: 18px; border-radius: 8px; font-family: 'Consolas', 'Monaco', monospace; white-space: pre-wrap; border-left: 4px solid #007bff; font-size: 0.9em; }}
        .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .image-item {{ text-align: center; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; background: #f8f9fa; }}
        .image-item img {{ max-width: 100%; height: auto; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .highlight {{ background: #fff3cd; padding: 10px; border-radius: 6px; border-left: 4px solid #ffc107; margin: 10px 0; }}
        .success {{ background: #d1edff; padding: 10px; border-radius: 6px; border-left: 4px solid #0d6efd; }}
        .error {{ background: #f8d7da; padding: 10px; border-radius: 6px; border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Comprehensive Facebook Marketplace Analysis</h1>
        <div class="data-grid" style="color: white;">
            <div class="label" style="color: #e9ecef;">Product:</div>
            <div class="value" style="color: white;">{extracted_data.get('product_title', 'N/A')}</div>
            <div class="label" style="color: #e9ecef;">URL:</div>
            <div class="value" style="color: white;"><a href="{extracted_data.get('product_url', '#')}" target="_blank" style="color: #b3d9ff;">{extracted_data.get('product_url', 'N/A')}</a></div>
            <div class="label" style="color: #e9ecef;">Extracted:</div>
            <div class="value" style="color: white;">{extracted_data.get('extraction_timestamp', 'N/A')}</div>
            <div class="label" style="color: #e9ecef;">Page Title:</div>
            <div class="value" style="color: white;">{extracted_data.get('page_title', 'N/A')}</div>
        </div>
    </div>
    
    <div class="section">
        <h3>🧑‍💼 Basic Seller Information</h3>
        <div class="json-block">{json.dumps(extracted_data.get('seller_info', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>🔍 Detailed Seller Information (from "See Details" button)</h3>
        <div class="highlight">
            <strong>🎯 This section shows data extracted after clicking the "See details" button</strong>
        </div>
        <div class="json-block">{json.dumps(extracted_data.get('seller_details_info', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>📱 Comprehensive Product Details</h3>
        <div class="json-block">{json.dumps(extracted_data.get('product_details', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>⏰ Timing & Posting Information</h3>
        <div class="success">
            <strong>📅 When was this item posted? Any urgency indicators?</strong>
        </div>
        <div class="json-block">{json.dumps(extracted_data.get('timing_info', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>📞 Contact & Location Details</h3>
        <div class="data-grid">
            <div class="label">Contact Options:</div>
            <div class="value">Available messaging/contact methods</div>
        </div>
        <div class="json-block">Contact Info:
{json.dumps(extracted_data.get('contact_info', {}), indent=2)}

Location Details:
{json.dumps(extracted_data.get('location_details', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>🏪 Marketplace Metadata</h3>
        <div class="highlight">
            <strong>📊 Facebook-specific information: listing ID, views, category, status</strong>
        </div>
        <div class="json-block">{json.dumps(extracted_data.get('marketplace_metadata', {}), indent=2)}</div>
    </div>
    
    <div class="section">
        <h3>📝 Product Description</h3>
        <div class="value" style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">{extracted_data.get('description', 'No description found')}</div>
    </div>
    
    <div class="section">
        <h3>🖼️ Product Images ({len(extracted_data.get('additional_images', []))} found)</h3>
        <div class="image-grid">
            {' '.join([f'<div class="image-item"><img src="{img["url"]}" alt="{img.get("alt_text", "Product image")}"><br><small style="color: #6c757d;">{img.get("alt_text", "No alt text")}</small></div>' for img in extracted_data.get('additional_images', [])[:8]])}
        </div>
    </div>
    
    <div class="section">
        <h3>📄 Raw Page Sources</h3>
        <div class="data-grid">
            <div class="label">Initial Page:</div>
            <div class="value">{extracted_data.get('page_sources', {}).get('initial_page', 'Not saved')}</div>
            <div class="label">Details Page:</div>
            <div class="value">{extracted_data.get('seller_details_info', {}).get('details_page_filename', 'Not clicked/found')}</div>
        </div>
    </div>
    
    <div class="section">
        <h3>📋 Raw Text Elements Sample (First 30)</h3>
        <div class="json-block">{json.dumps(extracted_data.get('raw_text_sections', [])[:30], indent=2)}</div>
    </div>
    
    <div class="section" style="background: #e7f3ff; border-color: #0d6efd;">
        <h3>💡 Analysis Summary</h3>
        <div class="data-grid">
            <div class="label">Seller Profile Found:</div>
            <div class="value">{'✅ Yes' if extracted_data.get('seller_info') and not extracted_data.get('seller_info', {}).get('error') else '❌ No'}</div>
            <div class="label">Details Button Clicked:</div>
            <div class="value">{'✅ Yes' if extracted_data.get('seller_details_info', {}).get('button_found') else '❌ No'}</div>
            <div class="label">Timing Info Extracted:</div>
            <div class="value">{'✅ Yes' if extracted_data.get('timing_info') and not extracted_data.get('timing_info', {}).get('error') else '❌ No'}</div>
            <div class="label">Contact Options Found:</div>
            <div class="value">{'✅ Yes' if extracted_data.get('contact_info') and not extracted_data.get('contact_info', {}).get('error') else '❌ No'}</div>
            <div class="label">Additional Images:</div>
            <div class="value">{len(extracted_data.get('additional_images', []))} images found</div>
            <div class="label">Description Length:</div>
            <div class="value">{len(extracted_data.get('description', ''))} characters</div>
        </div>
    </div>
</body>
</html>
            """
            
            report_filename = f"seller_report_{index}_{timestamp}.html"
            report_filepath = os.path.join(self.output_dir, report_filename)
            
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report created: {report_filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to create HTML report: {e}")
    
    def run_seller_extraction_debug(self, search_query="iphone 16", max_products=3):
        """Main method to run seller detail extraction debugging."""
        try:
            print(f"\n🔍 Starting seller detail extraction for: {search_query}")
            print(f"📁 Output directory: {self.output_dir}")
            
            # Setup WebDriver
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False
            
            # Login to Facebook
            if not self.login_to_facebook():
                print("❌ Failed to login to Facebook")
                return False
            
            # Navigate to marketplace search
            if not self.navigate_to_marketplace_search(search_query):
                print("❌ Failed to navigate to marketplace")
                return False
            
            # Find product cards
            product_cards = self.find_product_cards()
            if not product_cards:
                print("❌ No product cards found")
                return False
            
            print(f"\n📦 Found {len(product_cards)} product cards")
            
            # Extract details from each product
            extracted_products = []
            for i, card in enumerate(product_cards[:max_products]):
                print(f"\n🔍 Processing product {i+1}/{min(len(product_cards), max_products)}: {card['title'][:50]}...")
                
                extracted_data = self.extract_seller_details(
                    card['url'], 
                    card['title'], 
                    i+1
                )
                
                if extracted_data:
                    extracted_products.append(extracted_data)
                    print(f"✅ Successfully extracted data for product {i+1}")
                else:
                    print(f"❌ Failed to extract data for product {i+1}")
                
                # Delay between products to avoid being blocked
                if i < len(product_cards) - 1:
                    time.sleep(3)
            
            # Create summary report
            self._create_summary_report(extracted_products, search_query)
            
            print(f"\n✅ Extraction completed! Check the '{self.output_dir}' directory for:")
            print(f"   📄 HTML page sources: product_page_*.html")
            print(f"   📊 Extracted data: extracted_data_*.json")
            print(f"   📋 Formatted reports: seller_report_*.html")
            print(f"   📈 Summary report: extraction_summary.html")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Seller extraction debug failed: {e}")
            print(f"❌ Error: {e}")
            return False
        
        finally:
            # Close browser
            if self.driver:
                print("\n🔄 Closing browser...")
                try:
                    time.sleep(2)  # Give user time to see results
                    self.driver.quit()
                except:
                    pass
    
    def _create_summary_report(self, extracted_products, search_query):
        """Create a summary report of all extracted data."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            summary_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seller Extraction Summary - {search_query}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .product-card {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; }}
        .product-title {{ color: #2c5aa0; font-size: 1.2em; font-weight: bold; margin-bottom: 15px; }}
        .data-section {{ margin-bottom: 15px; }}
        .section-title {{ font-weight: bold; color: #555; font-size: 1.1em; margin-bottom: 8px; }}
        .json-data {{ background: #f0f0f0; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; font-size: 0.9em; }}
        .summary-stats {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Seller Extraction Summary Report</h1>
        <p><strong>Search Query:</strong> {search_query}</p>
        <p><strong>Extraction Date:</strong> {timestamp}</p>
        <p><strong>Products Processed:</strong> {len(extracted_products)}</p>
    </div>
    
    <div class="summary-stats">
        <h3>📈 Extraction Statistics</h3>
        <p><strong>Total Products:</strong> {len(extracted_products)}</p>
        <p><strong>Products with Seller Info:</strong> {sum(1 for p in extracted_products if p.get('seller_info') and not p.get('seller_info', {}).get('error'))}</p>
        <p><strong>Products with Contact Info:</strong> {sum(1 for p in extracted_products if p.get('contact_info') and not p.get('contact_info', {}).get('error'))}</p>
        <p><strong>Products with Descriptions:</strong> {sum(1 for p in extracted_products if p.get('description') and len(p.get('description', '')) > 10)}</p>
        <p><strong>Products with Additional Images:</strong> {sum(1 for p in extracted_products if p.get('additional_images') and len(p.get('additional_images', [])) > 0)}</p>
    </div>
            """
            
            # Add individual product details
            for i, product in enumerate(extracted_products):
                summary_html += f"""
    <div class="product-card">
        <div class="product-title">Product {i+1}: {product.get('product_title', 'Unknown')[:80]}...</div>
        
        <div class="data-section">
            <div class="section-title">🔗 Basic Info</div>
            <div class="json-data">URL: {product.get('product_url', 'N/A')}
Page Title: {product.get('page_title', 'N/A')}
Current URL: {product.get('current_url', 'N/A')}</div>
        </div>
        
        <div class="data-section">
            <div class="section-title">🧑‍💼 Seller Information</div>
            <div class="json-data">{json.dumps(product.get('seller_info', {}), indent=2)}</div>
        </div>
        
        <div class="data-section">
            <div class="section-title">📱 Product Details</div>
            <div class="json-data">{json.dumps(product.get('product_details', {}), indent=2)}</div>
        </div>
        
        <div class="data-section">
            <div class="section-title">📞 Contact & Location</div>
            <div class="json-data">Contact: {json.dumps(product.get('contact_info', {}), indent=2)}

Location: {json.dumps(product.get('location_details', {}), indent=2)}</div>
        </div>
        
        <div class="data-section">
            <div class="section-title">📝 Description</div>
            <div class="json-data">{product.get('description', 'No description found')[:500]}{'...' if len(product.get('description', '')) > 500 else ''}</div>
        </div>
        
        <div class="data-section">
            <div class="section-title">🖼️ Images Found ({len(product.get('additional_images', []))})</div>
            <div class="json-data">{json.dumps([img.get('url', '')[:100] + '...' for img in product.get('additional_images', [])[:3]], indent=2)}</div>
        </div>
    </div>
                """
            
            summary_html += """
</body>
</html>
            """
            
            summary_filepath = os.path.join(self.output_dir, f"extraction_summary_{timestamp}.html")
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write(summary_html)
            
            self.logger.info(f"Summary report created: {summary_filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to create summary report: {e}")


def debug_seller_extraction():
    """Debug seller detail extraction from product pages."""
    print("🚀 Starting Facebook Marketplace Seller Detail Extraction Debug")
    print("=" * 70)
    
    # Initialize components
    settings = Settings()
    extractor = SellerDetailExtractor(settings)
    
    # Run the extraction debug
    success = extractor.run_seller_extraction_debug(
        search_query="samsung galaxy s22",
        max_products=1  # Extract details from first product only for testing
    )
    
    return success


if __name__ == "__main__":
    success = debug_seller_extraction()
    print(f"\n{'🎉' if success else '💥'} Seller extraction debug {'completed successfully!' if success else 'failed!'}")
    
    if success:
        print("\n📂 Check the 'seller_debug_output' directory for:")
        print("   • HTML page sources (product_page_*.html)")
        print("   • Extracted JSON data (extracted_data_*.json)")
        print("   • Formatted reports (seller_report_*.html)")
        print("   • Summary report (extraction_summary_*.html)")
        print("\n💡 Open the HTML files in your browser to analyze the extracted data!")
