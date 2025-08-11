#!/usr/bin/env python3
"""
Facebook Login Demo - Simple Version

This script will:
1. Read username/password from config.json
2. Open Chrome browser (visible)
3. Go to Facebook login page
4. Automatically type username and password
5. Login to Facebook
6. Navigate to Marketplace
"""

import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

def setup_chrome_driver():
    """Setup Chrome driver with visible browser - more human-like"""
    chrome_options = Options()
    
    # Make browser visible and normal-sized
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--start-maximized')
    
    # Enhanced anti-detection measures
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # More realistic user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'--user-agent={user_agent}')
    
    # Try different driver approaches
    try:
        # First try with webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"⚠️  Webdriver-manager failed: {e}")
        try:
            # Fallback to system PATH ChromeDriver
            print("🔄 Trying system PATH ChromeDriver...")
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            print(f"❌ System ChromeDriver also failed: {e2}")
            raise Exception("Could not initialize ChromeDriver. Please ensure Chrome and ChromeDriver are properly installed.")
    
    # Remove automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Set timeouts
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(30)
    
    return driver

def type_like_human(element, text):
    """Type text with more human-like delays and behavior"""
    element.clear()
    time.sleep(0.5)  # Pause before typing
    
    for i, char in enumerate(text):
        element.send_keys(char)
        # Variable delay between characters (more human-like)
        if i % 3 == 0:  # Occasional longer pause
            time.sleep(0.2)
        else:
            time.sleep(0.08)  # Normal typing speed

def main():
    """Main function"""
    print("🎭 FACEBOOK LOGIN DEMO")
    print("=" * 50)
    
    driver = None
    
    try:
        # Load configuration
        print("📋 Loading configuration from config.json...")
        config = load_config()
        
        email = config['facebook_credentials']['email']
        password = config['facebook_credentials']['password']
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {'*' * len(password)}")
        print()
        
        # Setup Chrome driver
        print("🌐 Opening Chrome browser...")
        driver = setup_chrome_driver()
        print("✅ Chrome browser opened successfully!")
        
        # Navigate to Facebook
        print("🚀 Navigating to Facebook.com...")
        driver.get("https://www.facebook.com")
        time.sleep(3)
        print("✅ Facebook page loaded!")
        
        # Find and fill email field
        print("📧 Locating email field...")
        wait = WebDriverWait(driver, 10)
        email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
        
        print("⌨️  Typing email address...")
        type_like_human(email_field, email)
        print("✅ Email entered!")
        
        # Find and fill password field
        print("🔑 Locating password field...")
        password_field = driver.find_element(By.ID, "pass")
        
        print("⌨️  Typing password...")
        type_like_human(password_field, password)
        print("✅ Password entered!")
        
        # Click login button
        print("🔐 Clicking login button...")
        login_button = driver.find_element(By.NAME, "login")
        login_button.click()
        
        print("⏳ Waiting for login to complete...")
        print("⏰ Please wait 7 seconds for Facebook to process login...")
        for i in range(7, 0, -1):
            print(f"\r⏳ Waiting {i} seconds...", end="")
            time.sleep(1)
        print("\n")
        
        # Check if login was successful
        current_url = driver.current_url.lower()
        print(f"🔍 Current URL after login: {driver.current_url}")
        
        if "login" in current_url or "checkpoint" in current_url:
            print("❌ Login requires additional verification (2FA/Security Check)")
            print("🚨 Waiting 10 more seconds for manual verification...")
            time.sleep(10)  # Give time for manual verification
            print("⏳ Continuing anyway...")
        else:
            print("✅ Login appears successful!")
        
        # MODAL DETECTION SECTION - Wait for user to identify modal classes
        print("\n🔍 MODAL DETECTION MODE")
        print("=" * 50)
        print("👀 Please look at the browser now and check if there are any modals/popups.")
        print("📝 If you see any modal/popup, please note down their close button classes.")
        print("⏰ The browser will stay open for 30 seconds for you to inspect...")
        print("🚨 Press Ctrl+C if you want to stop and provide the modal classes.")
        
        # Wait 30 seconds for manual inspection
        for i in range(30, 0, -1):
            print(f"\r⏳ Waiting {i} seconds for modal inspection...", end="")
            time.sleep(1)
        print("\n")
        
        # Additional wait before marketplace navigation
        print("⏰ Continuing to marketplace navigation...")
        
        # Navigate to Marketplace
        print("🏪 Navigating to Facebook Marketplace...")
        driver.get("https://www.facebook.com/marketplace")
        time.sleep(1)
        print("✅ Marketplace loaded!")
        
        # Navigate to iPhone 16 search in Stockholm
        print("📱 Navigating to iPhone 16 search in Stockholm...")
        search_url = "https://www.facebook.com/marketplace/stockholm/search/?query=iphone%2016"
        driver.get(search_url)
        time.sleep(3)
        print("✅ iPhone 16 search page loaded!")
        print(f"🔗 Current URL: {driver.current_url}")
        
        # Scroll to load more products
        print("📜 Scrolling to load all products...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while scroll_count < 10:  # Limit scrolls to prevent infinite loop
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new products to load
            print(f"⏳ Scroll {scroll_count + 1}/10 - Waiting for new content...")
            time.sleep(3)
            
            # Calculate new scroll height and compare with last height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("✅ Reached end of page or no more products to load")
                break
            last_height = new_height
            scroll_count += 1
        
        print(f"🏁 Finished scrolling after {scroll_count + 1} attempts")
        
        # Wait a bit more to ensure all content is loaded
        print("⏰ Waiting 5 seconds for final content to load...")
        time.sleep(5)
        
        print("💾 Capturing page source...")
        page_source = driver.page_source
        
        # Save source code to file with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"marketplace_source_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        print(f"✅ Source code saved to: {filename}")
        print(f"📊 Source code length: {len(page_source):,} characters")
        print("🚪 Closing browser and starting analysis...")
        
    except KeyboardInterrupt:
        print("\n⏸️  Demo interrupted by user")
        print("🌐 Browser will remain open until you close it manually")
        input("Press Enter to close browser...")
    
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        input("Press Enter to close browser...")
    
    finally:
        if driver:
            try:
                driver.quit()
                print("🧹 Browser closed!")
            except:
                pass

if __name__ == "__main__":
    print("\n🎭 FACEBOOK LOGIN DEMO - AUTOMATIC MODE")
    print("📋 Using Chrome browser and credentials from config.json")
    print("🚀 Starting in 2 seconds...")
    time.sleep(2)
    
    main()
    
    print("\n👋 Demo completed!")
