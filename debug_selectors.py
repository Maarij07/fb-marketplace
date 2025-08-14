#!/usr/bin/env python3
"""
Debug script to identify the correct selectors for Facebook Marketplace products
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config.settings import Settings

def setup_chrome_driver():
    """Setup Chrome driver for debugging"""
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'--user-agent={user_agent}')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"webdriver-manager failed: {e}, trying default Chrome setup")
        driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def debug_marketplace_elements():
    """Debug Facebook Marketplace element structure"""
    settings = Settings()
    credentials = settings.get_facebook_credentials()
    
    driver = setup_chrome_driver()
    
    try:
        print("🌐 Opening Facebook...")
        driver.get("https://www.facebook.com")
        time.sleep(3)
        
        # Login
        print("📧 Logging in...")
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys(credentials['email'])
        
        password_field = driver.find_element(By.ID, "pass")
        password_field.send_keys(credentials['password'])
        
        login_button = driver.find_element(By.NAME, "login")
        login_button.click()
        time.sleep(5)
        
        print("🏪 Navigating to iPhone 16 search...")
        search_url = "https://www.facebook.com/marketplace/stockholm/search/?query=iphone%2016"
        driver.get(search_url)
        time.sleep(5)
        
        print("\n=== DEBUGGING ELEMENT STRUCTURE ===")
        
        # Test different selectors and see what we get
        selectors_to_test = [
            # Basic containers
            "div[data-surface-wrapper='1'] > div > div",
            "div[data-surface-wrapper='1'] > div > div > div",
            "div[role='article']",
            "a[role='link'][tabindex='0']",
            "a[href*='/marketplace/item/']",
            
            # Currency/price based
            "div[aria-label*='kr']",
            "div[aria-label*='SEK']", 
            "*[aria-label*='kr']",
            "*[aria-label*='SEK']",
            
            # Generic marketplace
            "div[data-testid*='marketplace']",
            "[data-testid*='marketplace']",
            
            # More specific
            "[data-surface-wrapper] div",
            "[data-surface-wrapper] > div",
        ]
        
        print(f"Page URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        print()
        
        best_selector = None
        best_count = 0
        
        for selector in selectors_to_test:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                count = len(elements)
                print(f"'{selector}': {count} elements")
                
                if count > best_count and count < 100:  # Avoid overly broad selectors
                    best_selector = selector
                    best_count = count
                    
                # Show sample text from first few elements
                if count > 0 and count <= 20:
                    print("  Sample elements:")
                    for i, elem in enumerate(elements[:3]):
                        text = elem.text.strip()[:100] if elem.text else "(empty)"
                        print(f"    {i+1}: {text}...")
                print()
                
            except Exception as e:
                print(f"'{selector}': ERROR - {e}")
                print()
        
        if best_selector:
            print(f"🎯 BEST SELECTOR: '{best_selector}' ({best_count} elements)")
            print("\n=== ANALYZING BEST SELECTOR ELEMENTS ===")
            
            elements = driver.find_elements(By.CSS_SELECTOR, best_selector)
            for i, elem in enumerate(elements[:5]):
                print(f"\n--- Element {i+1} ---")
                text = elem.text.strip()
                print(f"Text content: {text[:200]}...")
                
                # Try to find links
                links = elem.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
                if links:
                    print(f"Marketplace links: {len(links)}")
                    print(f"First link: {links[0].get_attribute('href')}")
                
                # Try to find images
                images = elem.find_elements(By.CSS_SELECTOR, "img")
                if images:
                    print(f"Images: {len(images)}")
                
                # Check for price indicators
                if 'kr' in text.lower() or 'sek' in text.lower() or '$' in text:
                    print("✅ Contains price indicators")
                else:
                    print("❌ No price indicators found")
        
        print("\n=== MANUAL INSPECTION ===")
        print("🔍 Browser is now open for manual inspection.")
        print("📝 Look at the page and identify product containers manually.")
        print("⏰ Press Enter when ready to close...")
        input()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("🧹 Browser closed!")

if __name__ == "__main__":
    debug_marketplace_elements()
