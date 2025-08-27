#!/usr/bin/env python3
"""
Working Enhanced Facebook Marketplace Scraper

This version fixes all the issues found during testing:
1. Proper session management with PersistentBrowserSession
2. Correct driver access pattern
3. Fixed variable scoping issues
4. Robust error handling
"""

import argparse
import logging
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from core.persistent_session import get_persistent_session
from config.settings import Settings


class WorkingEnhancedScraper:
    """Working enhanced scraper with proper session management."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = get_persistent_session(settings)
        
        # Create directories for saving HTML
        self.html_dir = "working_html_data"
        self.product_html_dir = os.path.join(self.html_dir, "products")
        self.seller_html_dir = os.path.join(self.html_dir, "sellers")
        
        for directory in [self.html_dir, self.product_html_dir, self.seller_html_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.enhanced_products = []
        self.driver = None
        
    def enhance_existing_products(self, input_file: str = "products.json", max_products: int = 3) -> List[Dict]:
        """
        Enhance existing products with detailed data from individual pages.
        """
        # Load existing products
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            products = data.get('products', [])
            self.logger.info(f"Loaded {len(products)} products from {input_file}")
        except FileNotFoundError:
            self.logger.error(f"File {input_file} not found")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from {input_file}: {e}")
            return []
        
        # Start browser session once for all products
        if not self._start_browser_session():
            self.logger.error("Failed to start browser session")
            return []
        
        try:
            # Enhance each product
            enhanced_count = 0
            for i, product in enumerate(products[:max_products]):
                try:
                    product_title = product.get('title', 'Unknown')[:50]
                    self.logger.info(f"Enhancing product {i+1}/{min(max_products, len(products))}: {product_title}...")
                    
                    enhanced_product = self._enhance_single_product(product)
                    if enhanced_product:
                        self.enhanced_products.append(enhanced_product)
                        enhanced_count += 1
                        self.logger.info(f"Successfully enhanced product {i+1}")
                    else:
                        self.logger.warning(f"Failed to enhance product {i+1}")
                    
                    # Add delay between products
                    time.sleep(3)
                    
                except Exception as e:
                    self.logger.error(f"Error enhancing product {i+1}: {e}")
                    continue
            
            self.logger.info(f"Enhanced {enhanced_count} out of {max_products} products successfully")
            return self.enhanced_products
            
        finally:
            # Clean up session
            self._cleanup_session()
    
    def _start_browser_session(self) -> bool:
        """Start the browser session and get driver reference."""
        try:
            self.logger.info("Starting browser session...")
            
            if not self.session.start_session():
                self.logger.error("Failed to start persistent session")
                return False
            
            if not self.session.scraper or not self.session.scraper.driver:
                self.logger.error("Session started but no driver available")
                return False
            
            self.driver = self.session.scraper.driver
            self.logger.info("Browser session started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting browser session: {e}")
            return False
    
    def _enhance_single_product(self, product: Dict) -> Optional[Dict]:
        """Enhance a single product with detailed data."""
        product_id = product.get('id', f'unknown_{int(time.time())}')
        product_url = product.get('marketplace_url')
        
        if not product_url:
            self.logger.warning(f"Product {product_id} has no marketplace URL")
            return product  # Return original if no URL
        
        if not self.driver:
            self.logger.error(f"No driver available for product {product_id}")
            return product
        
        # Start with copy of original product
        enhanced_product = product.copy()
        enhanced_product['enhancement_timestamp'] = datetime.now().isoformat()
        enhanced_product['enhancement_status'] = 'attempted'
        
        try:
            # Visit product page
            self.logger.info(f"Visiting product page: {product_url}")
            self.driver.get(product_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(4)  # Additional wait for dynamic content
            
            # Save product page HTML
            try:
                product_html_file = os.path.join(self.product_html_dir, f"{product_id}.html")
                with open(product_html_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"Saved product HTML: {product_html_file}")
                enhanced_product['saved_html_path'] = product_html_file
            except Exception as e:
                self.logger.warning(f"Failed to save HTML for {product_id}: {e}")
            
            # Extract enhanced product details
            enhanced_details = self._extract_product_details()
            if enhanced_details:
                enhanced_product['enhanced_details'] = enhanced_details
                self.logger.info(f"Extracted {len(enhanced_details)} enhanced fields")
            
            # Try to extract seller information
            seller_data = self._extract_seller_info(product_id)
            if seller_data:
                enhanced_product['enhanced_seller'] = seller_data
            
            enhanced_product['enhancement_status'] = 'success'
            return enhanced_product
            
        except Exception as e:
            self.logger.error(f"Error enhancing product {product_id}: {e}")
            enhanced_product['enhancement_status'] = 'failed'
            enhanced_product['enhancement_error'] = str(e)
            return enhanced_product
    
    def _extract_product_details(self) -> Dict:
        """Extract enhanced product details from current page."""
        details = {}
        
        try:
            # Extract title with multiple selectors
            title_selectors = [
                "h1[data-testid*='title']",
                "h1[dir='auto']",
                ".x1e56ztr.x1xmf6yo",
                ".x193iq5w.xeuugli.x13faqbe.x1vvkbs",
                "h1"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        details['title'] = title_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract price
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
                        details['price_text'] = raw_price
                        
                        # Parse price
                        price_match = re.search(r'(AU\$|USD\$|\$)?\s*([0-9,]+)', raw_price)
                        if price_match:
                            details['parsed_price'] = {
                                'currency_symbol': price_match.group(1) or '$',
                                'amount': price_match.group(2).replace(',', ''),
                                'raw': raw_price
                            }
                        break
                except NoSuchElementException:
                    continue
            
            # Extract description
            description_selectors = [
                "[data-testid*='description']",
                ".x1pha1pf.x78zum5.x2lwn1j.xeuugli",
                ".xdj266r.x11i5rnm.xat24cr.x1mh8g0r"
            ]
            
            for selector in description_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text.strip():
                        details['description'] = desc_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract location
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
                            details['location'] = location_text
                            break
                except NoSuchElementException:
                    continue
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting product details: {e}")
            return {}
    
    def _extract_seller_info(self, product_id: str) -> Optional[Dict]:
        """Extract seller information from current page and optionally visit profile."""
        seller_data = {
            'extraction_method': 'working_enhanced_scraper',
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        try:
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
                self.logger.warning(f"No seller profile URL found for product {product_id}")
                return seller_data
            
            # Visit seller profile
            self.logger.info(f"Visiting seller profile: {seller_profile_url}")
            self.driver.get(seller_profile_url)
            
            # Wait for profile page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Save seller profile HTML
            try:
                seller_html_file = os.path.join(self.seller_html_dir, f"{product_id}_seller.html")
                with open(seller_html_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"Saved seller HTML: {seller_html_file}")
                seller_data['saved_html_path'] = seller_html_file
            except Exception as e:
                self.logger.warning(f"Failed to save seller HTML: {e}")
            
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
                            self.logger.info(f"Found seller name: {name_text}")
                            break
                except NoSuchElementException:
                    continue
            
            # Look for additional info
            try:
                # Facebook join info
                join_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Joined Facebook')]")
                for elem in join_elements:
                    text = elem.text.strip()
                    if text:
                        seller_data['facebook_join_info'] = text
                        break
                
                # Location info
                location_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Lives in') or contains(text(), 'From')]")
                for elem in location_indicators:
                    text = elem.text.strip()
                    if text and len(text) < 200:
                        seller_data['location_info'] = text
                        break
                        
            except Exception as e:
                self.logger.debug(f"Error extracting additional seller info: {e}")
            
            seller_data['profile_url'] = seller_profile_url
            seller_data['profile_visited'] = True
            
            return seller_data
            
        except Exception as e:
            self.logger.error(f"Error extracting seller info: {e}")
            seller_data['error'] = str(e)
            seller_data['profile_visited'] = False
            return seller_data
    
    def save_enhanced_products(self, output_file: str = "working_enhanced_products.json"):
        """Save enhanced products to JSON file."""
        if not self.enhanced_products:
            self.logger.warning("No enhanced products to save")
            return
        
        output_data = {
            'enhancement_info': {
                'timestamp': datetime.now().isoformat(),
                'total_enhanced': len(self.enhanced_products),
                'successful_enhancements': sum(1 for p in self.enhanced_products if p.get('enhancement_status') == 'success'),
                'method': 'working_enhanced_scraper',
                'html_directory': self.html_dir
            },
            'enhanced_products': self.enhanced_products
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.enhanced_products)} enhanced products to {output_file}")
            
            # Print summary
            successful = output_data['enhancement_info']['successful_enhancements']
            total = len(self.enhanced_products)
            self.logger.info(f"Enhancement summary: {successful}/{total} successful")
            
        except Exception as e:
            self.logger.error(f"Error saving enhanced products: {e}")
    
    def _cleanup_session(self):
        """Clean up the browser session."""
        try:
            if self.session:
                self.session.close_session()
            self.driver = None
            self.logger.info("Browser session cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during session cleanup: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Working Enhanced Facebook Marketplace Scraper")
    parser.add_argument('--input', '-i', default='products.json', help='Input products JSON file')
    parser.add_argument('--output', '-o', default='working_enhanced_products.json', help='Output enhanced products JSON file')
    parser.add_argument('--max-products', '-m', type=int, default=3, help='Maximum products to enhance (default: 3)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize settings and scraper
        settings = Settings()
        scraper = WorkingEnhancedScraper(settings)
        
        logger.info("🚀 Starting working enhanced scraping process...")
        logger.info(f"📁 Input file: {args.input}")
        logger.info(f"📁 Output file: {args.output}")
        logger.info(f"📊 Max products: {args.max_products}")
        logger.info(f"📂 HTML will be saved to: {scraper.html_dir}/")
        
        # Enhance existing products
        enhanced_products = scraper.enhance_existing_products(args.input, args.max_products)
        
        if enhanced_products:
            # Save enhanced products
            scraper.save_enhanced_products(args.output)
            
            logger.info("✅ Enhancement process completed!")
            logger.info(f"📊 Enhanced {len(enhanced_products)} products")
            logger.info(f"📂 HTML files saved to: {scraper.html_dir}/")
        else:
            logger.error("❌ No products were enhanced")
            
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
