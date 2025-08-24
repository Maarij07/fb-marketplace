"""
Additional Deep Scraping Methods
This file contains the remaining deep scraping methods that will be integrated into the main scraper.
"""

import time
import re
import logging
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException


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
