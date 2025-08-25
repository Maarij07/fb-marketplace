"""
Enhanced Facebook Marketplace Deep Scraper

Performs comprehensive scraping by visiting individual product detail pages
to extract seller information, product specifications, and metadata.
Based on debug_custom_scrape.py logic but integrated into the main system.
"""

import time
import re
import logging
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)

from core.scraper import FacebookMarketplaceScraper


class DeepMarketplaceScraper(FacebookMarketplaceScraper):
    """Enhanced scraper that performs deep extraction from individual product pages."""
    
    def __init__(self, settings, persistent_session=False):
        """Initialize deep scraper with enhanced capabilities."""
        super().__init__(settings, persistent_session)
        
        # Additional configuration for deep scraping
        self.deep_scrape_config = {
            'max_products_per_session': 10,
            'page_load_timeout': 15,
            'element_wait_timeout': 8,
            'inter_product_delay': (3, 7),  # Random delay between products
            'click_delay': (1, 3),          # Random delay after clicks
            'scroll_delay': (2, 4)          # Random delay after scrolling
        }
        
        # Track deep scraping progress
        self.deep_scrape_stats = {
            'products_attempted': 0,
            'products_successful': 0,
            'seller_details_extracted': 0,
            'see_details_clicked': 0,
            'errors': []
        }
        
        # Create output directory for detailed reports
        self.output_dir = "deep_scrape_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def deep_scrape_marketplace(self, search_query: str, max_products: int = 5) -> List[Dict[str, Any]]:
        """
        Main method to perform deep scraping of marketplace products.
        
        Args:
            search_query: Product search term (e.g., "iphone 16", "samsung galaxy")
            max_products: Maximum number of products to deep scrape
        
        Returns:
            List of comprehensive product data with seller details
        """
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
                        
                        # 🔥 HOT RELOAD: Save product immediately to JSON
                        self._save_product_immediately_deep(deep_data, i + 1)
                        
                        # Send real-time notification
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
        """Find and prepare product cards for deep scraping."""
        try:
            self.logger.info("Finding product cards for deep scraping...")
            
            # Wait for content to load
            time.sleep(3)
            
            # Find marketplace item links
            marketplace_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            self.logger.info(f"Found {len(marketplace_links)} marketplace item links")
            
            product_cards = []
            
            for i, link in enumerate(marketplace_links):
                try:
                    url = link.get_attribute('href')
                    if not url or '/marketplace/item/' not in url:
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
            
            self.logger.info(f"Prepared {len(product_cards)} product cards for deep scraping")
            return product_cards
            
        except Exception as e:
            self.logger.error(f"Failed to find product cards: {e}")
            return []
    
    def _save_product_immediately_deep(self, deep_data: Dict[str, Any], product_index: int):
        """🔥 HOT RELOAD: Save deep scraped product immediately to JSON for real-time dashboard updates."""
        try:
            # Convert to standard format
            standard_product = self._convert_to_standard_format(deep_data)
            
            if standard_product:
                # Add hot reload metadata
                standard_product['hot_reload'] = True
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
            self.logger.error(f"Hot reload save failed for deep product {product_index}: {e}")
    
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
    
    def _is_outside_search_result(self, link) -> bool:
        """Check if a product is from 'Results from outside your search' section."""
        try:
            # Look for indicators that this product is from outside search results
            # These products typically appear in sections labeled as such
            
            # Check parent elements for "outside" text indicators
            current_element = link
            for level in range(10):  # Check up to 10 parent levels
                try:
                    current_element = current_element.find_element(By.XPATH, "..")
                    element_text = current_element.text.lower()
                    
                    # Common phrases that indicate results from outside the search
                    outside_indicators = [
                        'results from outside your search',
                        'outside your search',
                        'suggested for you',
                        'sponsored',
                        'recommended',
                        'you might also like',
                        'similar items',
                        'related products'
                    ]
                    
                    # Check if any outside indicator is present
                    for indicator in outside_indicators:
                        if indicator in element_text:
                            self.logger.debug(f"Found outside search indicator: '{indicator}' in element text")
                            return True
                    
                    # Also check for specific CSS classes or attributes that might indicate sponsored/suggested content
                    class_name = current_element.get_attribute('class') or ''
                    data_attrs = ' '.join([current_element.get_attribute(attr) or '' for attr in ['data-testid', 'data-surface', 'aria-label']])
                    
                    combined_attrs = (class_name + ' ' + data_attrs).lower()
                    attr_indicators = ['sponsor', 'suggest', 'recommend', 'related', 'outside']
                    
                    for indicator in attr_indicators:
                        if indicator in combined_attrs:
                            self.logger.debug(f"Found outside search indicator: '{indicator}' in element attributes")
                            return True
                    
                except Exception as e:
                    # If we can't get parent element, break the loop
                    break
            
            # Additional check: look for section headers that might indicate this is an "outside search" section
            # Find all text elements on the page and check for section headers
            try:
                page_source = self.driver.page_source.lower()
                # Check if the page contains "Results from outside your search" section
                if 'results from outside your search' in page_source or 'outside your search' in page_source:
                    # If such section exists, we need to determine if this specific link is in that section
                    # This is a more complex check that would require analyzing the DOM structure
                    # For now, we'll use a heuristic approach
                    
                    # Get the link's position on the page
                    try:
                        link_location = link.location_once_scrolled_into_view
                        # If we can find section headers, we could compare positions
                        # This is a simplified approach - in practice you might need more sophisticated DOM analysis
                        
                        # For now, let's check if this link appears after any "outside search" text in the DOM
                        link_html = link.get_attribute('outerHTML')
                        page_before_link = page_source.split(link_html)[0] if link_html in page_source else page_source
                        
                        # Count occurrences of outside search indicators before this link
                        outside_count = sum(page_before_link.count(indicator) for indicator in [
                            'results from outside your search',
                            'outside your search',
                            'suggested for you'
                        ])
                        
                        if outside_count > 0:
                            self.logger.debug(f"Link appears after {outside_count} 'outside search' indicators")
                            # This is a heuristic - if outside search text appears before this link, it might be in that section
                            return True
                            
                    except Exception:
                        pass
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking outside search result: {e}")
            return False  # If we can't determine, assume it's a valid search result
    
    def _extract_deep_product_data(self, card: Dict[str, Any], product_index: int) -> Optional[Dict[str, Any]]:
        """Extract comprehensive data from a product's detail page."""
        try:
            original_url = self.driver.current_url
            product_url = card['url']
            product_title = card['title']
            
            self.logger.info(f"Navigating to product page: {product_title[:50]}...")
            
            # Navigate to product detail page
            self.driver.get(product_url)
            time.sleep(random.uniform(3, 5))
            
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
            self.driver.get(original_url)
            time.sleep(random.uniform(2, 4))
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract deep data for product {product_index}: {e}")
            
            # Try to navigate back to search results even on error
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.get(original_url)
                    time.sleep(2)
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
                        time.sleep(random.uniform(2, 4))
                        
                        # Extract information from details page/popup
                        detailed_seller_data = self._extract_from_seller_details_page()
                        seller_details_info.update(detailed_seller_data)
                        
                        self.deep_scrape_stats['see_details_clicked'] += 1
                        self.deep_scrape_stats['seller_details_extracted'] += 1
                        
                        # Navigate back if we went to a new page
                        if self.driver.current_url != data['basic_info']['current_url']:
                            self.logger.info("Navigated to new page, going back...")
                            self.driver.back()
                            time.sleep(2)
                        
                    except ElementNotInteractableException:
                        # Try JavaScript click as fallback
                        self.logger.info("Direct click failed, trying JavaScript click")
                        try:
                            self.driver.execute_script("arguments[0].click();", see_details_button)
                            time.sleep(3)
                            
                            detailed_seller_data = self._extract_from_seller_details_page()
                            seller_details_info.update(detailed_seller_data)
                            
                            if self.driver.current_url != data['basic_info']['current_url']:
                                self.driver.back()
                                time.sleep(2)
                                
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
        """Extract when the item was posted and any urgency indicators."""
        try:
            timing_info = {}
            
            # Look for posting time patterns
            page_text = self.driver.page_source.lower()
            time_patterns = [
                r'posted\s+([^<]*ago)',
                r'listed\s+([^<]*ago)',
                r'(\d+)\s+(minutes?|hours?|days?|weeks?|months?)\s+ago'
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    time_text = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
                    timing_info['posted_time'] = time_text.strip()
                    break
            
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
