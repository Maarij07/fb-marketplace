#!/usr/bin/env python3
"""
Daily Google Sheets Export Scheduler

Automatically exports marketplace data to Google Sheets every 24 hours.
Appends new data without removing existing data and without deduplication.
"""

import sys
import os
import time
import schedule
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.google_sheets_manager import GoogleSheetsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_sheets_export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration - Change this to your Google Sheet URL
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit"

def daily_export_job():
    """Daily job to append current products to Google Sheets."""
    try:
        logger.info("🚀 Starting daily Google Sheets export job...")
        
        # Initialize Google Sheets manager
        sheets_manager = GoogleSheetsManager()
        
        if not sheets_manager.client:
            logger.error("❌ Failed to initialize Google Sheets client")
            return False
        
        logger.info("✅ Google Sheets client initialized")
        
        # Append current products to the Products sheet
        logger.info("📊 Appending products data to Google Sheets...")
        success = sheets_manager.append_products_to_sheets(GOOGLE_SHEET_URL, "Products")
        
        if success:
            logger.info("✅ Successfully appended products to Google Sheets!")
            
            # Update analytics sheet as well
            logger.info("📈 Updating analytics sheet...")
            analytics_success = sheets_manager.create_analytics_sheet(GOOGLE_SHEET_URL, "Analytics")
            
            if analytics_success:
                logger.info("✅ Analytics sheet updated!")
            else:
                logger.warning("⚠️ Analytics sheet update failed")
            
            logger.info("🎉 Daily export completed successfully!")
            return True
        else:
            logger.error("❌ Failed to append products to Google Sheets")
            return False
            
    except Exception as e:
        logger.error(f"❌ Daily export job failed: {e}")
        return False

def run_scheduler():
    """Run the scheduler for daily exports."""
    logger.info("🕐 Starting daily Google Sheets export scheduler...")
    logger.info(f"📋 Target Google Sheet: {GOOGLE_SHEET_URL}")
    logger.info("⏰ Schedule: Every 24 hours")
    
    # Schedule the job to run every 24 hours
    schedule.every(24).hours.do(daily_export_job)
    
    # Run once immediately on startup
    logger.info("▶️ Running initial export...")
    daily_export_job()
    
    logger.info("✅ Scheduler started! Exports will run every 24 hours.")
    logger.info("Press Ctrl+C to stop the scheduler...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("⏹️ Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")

def run_manual_export():
    """Run a manual export immediately."""
    logger.info("🚀 Running manual Google Sheets export...")
    success = daily_export_job()
    if success:
        logger.info("✅ Manual export completed successfully!")
    else:
        logger.error("❌ Manual export failed!")
    return success

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # Run manual export
        run_manual_export()
    else:
        # Run scheduler
        run_scheduler()
