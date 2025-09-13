#!/usr/bin/env python3
"""
Facebook Marketplace Automation - EXE Launcher
Production-ready launcher with comprehensive error handling and logging.
"""

import sys
import os
import logging
import traceback
import webbrowser
import time
import threading
from pathlib import Path
import json
from datetime import datetime, date
import hmac
import hashlib

def setup_exe_environment():
    """Setup the environment for EXE execution."""
    try:
        # Determine if we're running from EXE or script
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller EXE
            application_path = sys._MEIPASS
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Running from script
            application_path = os.path.dirname(os.path.abspath(__file__))
            exe_dir = application_path
        
        # Set working directory to EXE location
        os.chdir(exe_dir)
        
        # Add application path to Python path
        if application_path not in sys.path:
            sys.path.insert(0, application_path)
        
        # Create necessary directories
        directories = ['logs', 'data', 'exports', 'temp']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        return exe_dir, application_path
        
    except Exception as e:
        print(f"❌ Failed to setup environment: {e}")
        return None, None

def setup_logging():
    """Setup comprehensive logging for the EXE."""
    try:
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Setup logging configuration
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('logs/facebook_marketplace.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("🚀 Facebook Marketplace Automation - Starting...")
        logger.info(f"📁 Working Directory: {os.getcwd()}")
        logger.info(f"🐍 Python Version: {sys.version}")
        
        return logger
        
    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        return None

def check_dependencies(logger):
    """Check if all required dependencies are available."""
    try:
        logger.info("🔍 Checking dependencies...")
        
        # Critical dependencies
        dependencies = [
            ('flask', 'Flask web framework'),
            ('selenium', 'Web automation'),
            ('requests', 'HTTP requests'),
            ('apscheduler', 'Task scheduling'),
            ('pandas', 'Data processing'),
            ('openpyxl', 'Excel export'),
        ]
        
        missing_deps = []
        for dep_name, description in dependencies:
            try:
                __import__(dep_name)
                logger.info(f"✅ {dep_name} - {description}")
            except ImportError:
                missing_deps.append((dep_name, description))
                logger.error(f"❌ {dep_name} - {description} - MISSING")
        
        if missing_deps:
            logger.error(f"❌ Missing {len(missing_deps)} critical dependencies")
            return False
        
        logger.info("✅ All dependencies available")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dependency check failed: {e}")
        return False

def check_chrome_driver(logger):
    """Check Chrome WebDriver availability with improved error handling."""
    try:
        import signal
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import subprocess
        
        logger.info("🌐 Checking Chrome WebDriver...")
        
        # Set a timeout for the entire operation
        def timeout_handler(signum, frame):
            raise TimeoutError("Chrome WebDriver check timed out")
        
        # Only set signal on non-Windows or if available
        timeout_set = False
        if hasattr(signal, 'SIGALRM'):
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(15)  # 15 second timeout
                timeout_set = True
            except:
                pass
        
        try:
            # Try to setup Chrome driver with timeout
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--remote-debugging-port=9222')
            
            # Try to get ChromeDriver path with shorter timeout
            try:
                driver_path = ChromeDriverManager().install()
                logger.info(f"✅ ChromeDriver available: {driver_path}")
            except Exception as e:
                logger.warning(f"⚠️  ChromeDriver manager failed: {e}")
                # Try to use system Chrome driver
                driver_path = None
            
            # Create Chrome service with timeout
            service = None
            if driver_path:
                service = Service(driver_path)
            
            # Quick test with very short timeout
            try:
                if service:
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    driver = webdriver.Chrome(options=chrome_options)
                
                # Quick test - just get title with timeout
                driver.set_page_load_timeout(3)
                driver.get("data:text/html,<html><head><title>Test</title></head><body>Test</body></html>")
                title = driver.title
                driver.quit()
                
                if "Test" in title:
                    logger.info("✅ Chrome WebDriver test successful")
                    return True
                else:
                    logger.warning("⚠️  Chrome WebDriver test inconclusive")
                    return False
                    
            except Exception as e:
                logger.warning(f"⚠️  Chrome WebDriver test failed: {e}")
                try:
                    driver.quit()
                except:
                    pass
                return False
                
        finally:
            # Cancel timeout if it was set
            if timeout_set:
                try:
                    signal.alarm(0)
                except:
                    pass
        
    except TimeoutError:
        logger.warning("⚠️  Chrome WebDriver check timed out - skipping")
        return False
    except Exception as e:
        logger.warning(f"⚠️  Chrome WebDriver check failed: {e}")
        logger.info("🔧 Chrome WebDriver will be available when needed for scraping")
        return False

def initialize_application(logger):
    """Initialize the main application components."""
    try:
        logger.info("🔧 Initializing application components...")
        
        # Import core modules
        from config.settings import Settings
        from core.json_manager import JSONDataManager
        from core.scheduler import SchedulerManager
        from web.app import create_app
        
        # Initialize settings
        settings = Settings()
        logger.info("✅ Settings loaded")
        
        # Initialize JSON data storage
        json_manager = JSONDataManager()
        json_manager.initialize_json_file()
        logger.info("✅ Data storage initialized")
        
        # Create Flask app
        app = create_app(settings)
        logger.info("✅ Web application created")
        
        return app, settings
        
    except Exception as e:
        logger.error(f"❌ Application initialization failed: {e}")
        logger.error(traceback.format_exc())
        return None, None

def start_web_dashboard(app, settings, logger):
    """Start the web dashboard in a separate thread."""
    try:
        host = settings.get('FLASK_HOST', '127.0.0.1')
        port = int(settings.get('FLASK_PORT', 5000))
        
        logger.info(f"🌐 Starting web dashboard at http://{host}:{port}")
        
        def run_flask():
            app.run(host=host, port=port, debug=False, use_reloader=False)
        
        # Start Flask in separate thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Wait a moment for Flask to start
        time.sleep(3)
        
        # Try to open browser
        dashboard_url = f"http://{host}:{port}"
        try:
            webbrowser.open(dashboard_url)
            logger.info(f"🌐 Browser opened: {dashboard_url}")
        except Exception as e:
            logger.warning(f"⚠️  Could not open browser: {e}")
            logger.info(f"📱 Please manually open: {dashboard_url}")
        
        return flask_thread
        
    except Exception as e:
        logger.error(f"❌ Failed to start web dashboard: {e}")
        return None

def _read_license_file(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def _verify_license(payload: dict, secret: str) -> bool:
    try:
        # Expected fields: {"expiry": "YYYY-MM-DD", "license_key": "<hex>"}
        expiry_str = payload.get('expiry')
        provided_key = (payload.get('license_key') or '').strip().lower()
        if not expiry_str or not provided_key:
            return False
        # Build HMAC over expiry string only (simple, offline)
        expected = hmac.new(secret.encode('utf-8'), expiry_str.encode('utf-8'), hashlib.sha256).hexdigest()
        # Check date not expired and signature matches
        exp_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        if date.today() > exp_date:
            return False
        return hmac.compare_digest(provided_key, expected)
    except Exception:
        return False

def check_license_or_trial(logger):
    """Block execution on and after 2025-09-11 unless a valid license is present.
    
    License options (in the same folder as the EXE):
      - license.json with fields: {"expiry": "YYYY-MM-DD", "license_key": "<hex>"}
        where license_key = HMAC_SHA256(secret, expiry)
      - or set environment variable LICENSE_BYPASS=1 for internal testing only.
    """
    CUTOFF = date(2025, 9, 11)  # Block starting this date (inclusive)

    # Internal testing bypass (do not share with clients)
    if os.environ.get('LICENSE_BYPASS') == '1':
        logger.info('🔓 License bypass active (internal testing)')
        return True

    today = date.today()
    if today >= CUTOFF:
        # Look for a license file to allow post-trial operation
        lic_path = os.path.join(os.getcwd(), 'license.json')
        payload = _read_license_file(lic_path)

        # IMPORTANT: Replace this secret before building a production EXE
        LIC_SECRET = os.environ.get('LIC_SECRET', 'CHANGE_ME_SECRET')

        if payload and _verify_license(payload, LIC_SECRET):
            logger.info('✅ Valid license found. Continuing execution.')
            return True
        else:
            logger.error('⛔ Trial period has ended. No valid license was found.')
            print("\n⛔ Trial expired on 2025-09-11. Please contact the vendor for a license.")
            print("Place a license.json file next to the EXE to continue after the trial.")
            input("Press Enter to exit...")
            sys.exit(2)

    # Before cutoff date, allow running as trial
    days_left = (CUTOFF - today).days
    logger.info(f"🕒 Trial mode active. Days remaining: {days_left}")
    return True

def main():
    """Main launcher function."""
    print("🚀 Facebook Marketplace Automation")
    print("=" * 50)
    
    # Setup environment
    exe_dir, app_path = setup_exe_environment()
    if not exe_dir:
        input("❌ Environment setup failed. Press Enter to exit...")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging()
    if not logger:
        input("❌ Logging setup failed. Press Enter to exit...")
        sys.exit(1)

    # Licensing/trial check early to avoid heavy initialization before gating
    check_license_or_trial(logger)
    
    try:
        # Check dependencies
        if not check_dependencies(logger):
            logger.error("❌ Critical dependencies missing")
            input("❌ Dependency check failed. Press Enter to exit...")
            sys.exit(1)
        
        # Check Chrome driver (optional - won't fail if issues)
        logger.info("🔍 Performing optional Chrome WebDriver check...")
        check_chrome_driver(logger)
        
        # Initialize application
        app, settings = initialize_application(logger)
        if not app:
            logger.error("❌ Application initialization failed")
            input("❌ Application startup failed. Press Enter to exit...")
            sys.exit(1)
        
        # Start web dashboard
        flask_thread = start_web_dashboard(app, settings, logger)
        if not flask_thread:
            logger.error("❌ Web dashboard startup failed")
            input("❌ Web dashboard failed to start. Press Enter to exit...")
            sys.exit(1)
        
        # Success message
        host = settings.get('FLASK_HOST', '127.0.0.1')
        port = int(settings.get('FLASK_PORT', 5000))
        dashboard_url = f"http://{host}:{port}"
        
        print("\n" + "=" * 50)
        print("✅ FACEBOOK MARKETPLACE AUTOMATION STARTED!")
        print("=" * 50)
        print(f"🌐 Dashboard URL: {dashboard_url}")
        print("📱 The dashboard should open automatically in your browser")
        print("🔧 Check the dashboard for all features:")
        print("   • Custom Search & Scrape")
        print("   • Automated Schedulers")
        print("   • Browser Monitoring")
        print("   • Price Tracking")
        print("   • Excel Export")
        print("=" * 50)
        print("💡 Press Ctrl+C to stop the application")
        print("=" * 50)
        
        logger.info("🎉 Application started successfully!")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Application shutdown requested")
            print("\n🛑 Shutting down Facebook Marketplace Automation...")
            print("✅ Application stopped successfully!")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Fatal error: {e}")
        print("📋 Check logs/facebook_marketplace.log for details")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
