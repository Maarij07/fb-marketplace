#!/usr/bin/env python3
"""
Temporary Enhanced Facebook Marketplace Scraper

This is a temporary version designed to gather more detailed data from:
1. Individual product pages (save full HTML)
2. Seller profile pages (extract real seller names and info)
3. Enhanced product details extraction

This script will be deleted after we improve the main scraper.
"""

import argparse
import logging
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from core.persistent_session import get_persistent_session
from config.settings import Settings


class EnhancedMarketplaceScraper:
    """Enhanced scraper for detailed product and seller data collection."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = get_persistent_session(settings)
        
        # Create directories for saving HTML
        self.html_dir = "temp_html_data"
        self.product_html_dir = os.path.join(self.html_dir, "products")
        self.seller_html_dir = os.path.join(self.html_dir, "sellers")
        
        for directory in [self.html_dir, self.product_html_dir, self.seller_html_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.enhanced_products = []
        
    def enhance_existing_products(self, input_file: str = "products.json") -> List[Dict]:
        """
        Enhance existing products with detailed data from individual pages.
        
        Args:
            input_file: Path to existing products JSON file
            
        Returns:
            List of enhanced product data
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
        
        # Enhance each product
        enhanced_count = 0
        for i, product in enumerate(products[:5]):  # Limit to first 5 for testing
            try:
                self.logger.info(f"Enhancing product {i+1}/{min(5, len(products))}: {product.get('title', 'Unknown')[:50]}...")
                
                enhanced_product = self.enhance_single_product(product)
                if enhanced_product:
                    self.enhanced_products.append(enhanced_product)
                    enhanced_count += 1
                
                # Add delay between products
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error enhancing product {i+1}: {e}")
                continue
        
        self.logger.info(f"Enhanced {enhanced_count} products successfully")
        return self.enhanced_products
    
    def enhance_single_product(self, product: Dict) -> Optional[Dict]:
        """
        Enhance a single product with detailed data.
        
        Args:
            product: Original product data
            
        Returns:
            Enhanced product data or None if failed
        """
        product_url = product.get('marketplace_url')
        if not product_url:
            self.logger.warning("Product has no marketplace URL")
            return None
        
        enhanced_product = product.copy()
        enhanced_product['enhancement_timestamp'] = datetime.now().isoformat()
        
        # Get product ID early for error handling
        product_id = product.get('id', 'unknown')
        
        try:
            # Start persistent session to get access to driver
            if not self.session.start_session():
                self.logger.error("Failed to start browser session")
                return None
            
            # Get driver from the session's scraper
            driver = self.session.scraper.driver
            if not driver:
                self.logger.error("Failed to get browser driver from session")
                return None
            
            # Visit product page and save HTML
            self.logger.info(f"Visiting product page: {product_url}")
            driver.get(product_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Additional wait for dynamic content
            
            # Save full product page HTML
            product_html_file = os.path.join(self.product_html_dir, f"{product_id}.html")
            with open(product_html_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            self.logger.info(f"Saved product HTML to {product_html_file}")
            
            # Extract enhanced product details
            enhanced_details = self.extract_enhanced_product_details(driver)
            if enhanced_details:
                enhanced_product.update(enhanced_details)
            
            # Extract and enhance seller information
            seller_data = self.extract_enhanced_seller_data(driver, product)
            if seller_data:
                enhanced_product['enhanced_seller'] = seller_data
            
            return enhanced_product
            
        except Exception as e:
            self.logger.error(f"Error enhancing product {product_id}: {e}")
            return product  # Return original if enhancement fails
    
    def extract_enhanced_product_details(self, driver) -> Dict:
        """Extract enhanced product details from the product page."""
        details = {}
        
        try:
            # Extract title
            title_selectors = [
                "[data-testid='fb-marketplace-listing-title']",
                "h1[dir='auto']",
                ".x1e56ztr.x1xmf6yo",
                ".x193iq5w.xeuugli.x13faqbe.x1vvkbs",
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        details['enhanced_title'] = title_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract price
            price_selectors = [
                "[data-testid='mf-listing-price']",
                ".x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1s688f.xzsf02u",
                ".x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.xl56j7k.x6s0dn4.xozqiw3.x1q0g3np.xi112ho.x17zwfj4.x585lrc.x1403ito.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.xn6708d.x1ye3gou.xtvsq51.x1r1pt67"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if price_elem and price_elem.text.strip():
                        details['enhanced_price_text'] = price_elem.text.strip()
                        # Try to extract structured price
                        price_match = re.search(r'([\d,]+)\s*([A-Z]+)', price_elem.text.strip())
                        if price_match:
                            details['enhanced_price'] = {
                                'amount': price_match.group(1).replace(',', ''),
                                'currency': price_match.group(2),
                                'raw': price_elem.text.strip()
                            }
                        break
                except NoSuchElementException:
                    continue
            
            # Extract description
            description_selectors = [
                "[data-testid='listing-description']",
                ".x1pha1pf.x78zum5.x2lwn1j.xeuugli.x1n2onr6.x1ja2u2z",
                ".xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs"
            ]
            
            for selector in description_selectors:
                try:
                    desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem and desc_elem.text.strip():
                        details['enhanced_description'] = desc_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract location
            location_selectors = [
                "[data-testid='listing-location']",
                ".x1i10hfl.x1qjc9v5.xjbqb8w.xjqpnuy.xa49m3k.xqeqjp1.x2hbi6w.x13fuv20.xu3j5b3.x1q0q8m5.x26u7qi.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.x78zum5.xdl72j9.x2lah0s.xe8uvvx.x2lwn1j.xeuugli.xggy1nq.x1t137rt.x1o1ewxj.x3x9cwd.x1e5q0jg.x13rtm0m.x3nfvp2.x1q0g3np.x87ps6o.x1lku1pv.x1a2a7pz.xzsf02u.x1rg5ohu"
            ]
            
            for selector in location_selectors:
                try:
                    loc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if loc_elem and loc_elem.text.strip():
                        details['enhanced_location'] = loc_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract condition
            try:
                condition_elems = driver.find_elements(By.XPATH, "//span[contains(text(), 'Condition')]/following-sibling::*")
                for elem in condition_elems:
                    if elem.text.strip():
                        details['enhanced_condition'] = elem.text.strip()
                        break
            except:
                pass
            
            self.logger.info(f"Extracted enhanced details: {len(details)} fields")
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting enhanced product details: {e}")
            return {}
    
    def extract_enhanced_seller_data(self, driver, product: Dict) -> Optional[Dict]:
        """Extract enhanced seller data by visiting seller profile."""
        
        seller_data = {
            'extraction_method': 'enhanced_scraper',
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        # Try to find seller profile link from existing deep_data
        seller_profile_url = None
        deep_data = product.get('deep_data', {})
        seller_details = deep_data.get('seller_details', {})
        
        if seller_details.get('button_href'):
            seller_profile_url = seller_details['button_href']
        else:
            # Try to find seller profile link on current page
            try:
                seller_link_selectors = [
                    "a[href*='/marketplace/profile/']",
                    "a[href*='facebook.com/profile.php']",
                    "[data-testid='seller-profile-link']"
                ]
                
                for selector in seller_link_selectors:
                    try:
                        link_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if link_elem:
                            seller_profile_url = link_elem.get_attribute('href')
                            break
                    except NoSuchElementException:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Could not find seller profile link: {e}")
        
        if not seller_profile_url:
            self.logger.warning("No seller profile URL found")
            return seller_data
        
        try:
            # Visit seller profile page
            self.logger.info(f"Visiting seller profile: {seller_profile_url}")
            driver.get(seller_profile_url)
            
            # Wait for profile page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Save seller profile HTML
            product_id = product.get('id', 'unknown')
            seller_html_file = os.path.join(self.seller_html_dir, f"{product_id}_seller.html")
            with open(seller_html_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            self.logger.info(f"Saved seller HTML to {seller_html_file}")
            
            # Extract seller name
            seller_name_selectors = [
                "h1[data-testid='user-name']",
                ".x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz h1",
                ".x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz",
                "h1.x1heor9g",
                ".x1i10hfl h1",
                "h1"
            ]
            
            seller_name = None
            for selector in seller_name_selectors:
                try:
                    name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if name_elem and name_elem.text.strip() and len(name_elem.text.strip()) < 100:
                        seller_name = name_elem.text.strip()
                        self.logger.info(f"Found seller name: {seller_name}")
                        break
                except NoSuchElementException:
                    continue
            
            if seller_name:
                seller_data['real_name'] = seller_name
            else:
                self.logger.warning("Could not extract seller name from profile page")
            
            # Extract additional seller info
            try:
                # Look for "Joined Facebook in" text
                join_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Joined Facebook')]")
                for elem in join_elements:
                    if elem.text.strip():
                        seller_data['facebook_join_info'] = elem.text.strip()
                        break
                
                # Look for seller rating or reviews
                rating_selectors = [
                    "[data-testid='seller-rating']",
                    ".x1i10hfl .x1fcty0u",
                    "*[class*='rating']"
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        if rating_elem and rating_elem.text.strip():
                            seller_data['rating_info'] = rating_elem.text.strip()
                            break
                    except NoSuchElementException:
                        continue
                
                # Extract location info from seller profile
                location_indicators = driver.find_elements(By.XPATH, "//*[contains(@class, 'location') or contains(@aria-label, 'location') or contains(text(), 'Lives in')]")
                for elem in location_indicators:
                    if elem.text.strip() and len(elem.text.strip()) < 200:
                        seller_data['profile_location'] = elem.text.strip()
                        break
                        
            except Exception as e:
                self.logger.warning(f"Error extracting additional seller info: {e}")
            
            seller_data['profile_url'] = seller_profile_url
            seller_data['profile_visited'] = True
            
            return seller_data
            
        except Exception as e:
            self.logger.error(f"Error extracting seller data from profile: {e}")
            seller_data['profile_url'] = seller_profile_url
            seller_data['profile_visited'] = False
            seller_data['error'] = str(e)
            return seller_data
    
    def save_enhanced_products(self, output_file: str = "enhanced_products.json"):
        """Save enhanced products to JSON file."""
        if not self.enhanced_products:
            self.logger.warning("No enhanced products to save")
            return
        
        output_data = {
            'enhancement_info': {
                'timestamp': datetime.now().isoformat(),
                'total_enhanced': len(self.enhanced_products),
                'method': 'enhanced_scraper_temp',
                'html_saved': True,
                'html_directory': self.html_dir
            },
            'enhanced_products': self.enhanced_products
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.enhanced_products)} enhanced products to {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving enhanced products: {e}")


def main():
    """Main entry point for temporary enhanced scraper."""
    parser = argparse.ArgumentParser(description="Temporary Enhanced Facebook Marketplace Scraper")
    parser.add_argument('--input', '-i', default='products.json', help='Input products JSON file')
    parser.add_argument('--output', '-o', default='enhanced_products.json', help='Output enhanced products JSON file')
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
        scraper = EnhancedMarketplaceScraper(settings)
        
        logger.info("🔧 Starting temporary enhanced scraping process...")
        logger.info(f"📁 Input file: {args.input}")
        logger.info(f"📁 Output file: {args.output}")
        logger.info(f"📁 HTML will be saved to: {scraper.html_dir}/")
        
        # Enhance existing products
        enhanced_products = scraper.enhance_existing_products(args.input)
        
        if enhanced_products:
            # Save enhanced products
            scraper.save_enhanced_products(args.output)
            
            logger.info("✅ Enhancement completed successfully!")
            logger.info(f"📊 Enhanced {len(enhanced_products)} products")
            logger.info(f"📂 HTML files saved to: {scraper.html_dir}/")
            logger.info("🗑️  Remember to delete this temporary scraper after analysis")
        else:
            logger.error("❌ No products were enhanced")
            
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
