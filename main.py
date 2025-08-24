#!/usr/bin/env python3
"""
Facebook Marketplace Automation - Main Entry Point

A comprehensive tool for monitoring competitor activity on Facebook Marketplace.
Supports automated scraping, price tracking, and web dashboard.
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import DatabaseManager
from core.scraper import FacebookMarketplaceScraper
from core.scheduler import SchedulerManager
from web.app import create_app
from config.settings import Settings


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/marketplace_automation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def init_database(logger):
    """Initialize the database with required tables."""
    try:
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def run_scraper(logger, verbose: bool = False):
    """Run the Facebook Marketplace scraper once."""
    try:
        settings = Settings()
        scraper = FacebookMarketplaceScraper(settings)
        
        logger.info("Starting Facebook Marketplace scraper...")
        results = scraper.scrape_marketplace()
        
        if results:
            logger.info(f"Successfully scraped {len(results)} listings")
            return True
        else:
            logger.warning("No listings found")
            return False
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        return False


def start_scheduler(logger):
    """Start the automated scheduler for regular scraping."""
    try:
        settings = Settings()
        scheduler = SchedulerManager(settings)
        
        logger.info("Starting automated scheduler...")
        scheduler.start()
        
        print("Scheduler started successfully!")
        print("Press Ctrl+C to stop...")
        
        try:
            scheduler.keep_alive()
        except KeyboardInterrupt:
            print("\nShutting down scheduler...")
            scheduler.stop()
            logger.info("Scheduler stopped")
        
        return True
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return False


def start_dashboard(logger):
    """Start the web dashboard."""
    try:
        settings = Settings()
        app = create_app(settings)
        
        host = settings.get('FLASK_HOST', '127.0.0.1')
        port = int(settings.get('FLASK_PORT', 5000))
        debug = settings.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Starting web dashboard at http://{host}:{port}")
        print(f"Dashboard available at: http://{host}:{port}")
        
        app.run(host=host, port=port, debug=debug)
        return True
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        return False


def show_status(logger):
    """Show system status and statistics."""
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_system_stats()
        
        print("\n=== Facebook Marketplace Automation Status ===")
        print(f"Total listings: {stats.get('total_listings', 0)}")
        print(f"Listings today: {stats.get('listings_today', 0)}")
        print(f"Price changes: {stats.get('price_changes', 0)}")
        print(f"Last scrape: {stats.get('last_scrape', 'Never')}")
        print(f"Database size: {stats.get('db_size', 'Unknown')}")
        
        # Check scheduler status
        try:
            scheduler = SchedulerManager(Settings())
            if scheduler.is_running():
                print(f"Scheduler: Running (next run: {scheduler.get_next_run()})")
            else:
                print("Scheduler: Stopped")
        except:
            print("Scheduler: Status unknown")
        
        print("=" * 50)
        return True
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return False


def cleanup_data(logger):
    """Clean up old data based on retention policy."""
    try:
        db_manager = DatabaseManager()
        settings = Settings()
        
        retention_hours = int(settings.get('DATA_RETENTION_HOURS', 48))
        deleted_count = db_manager.cleanup_old_data(retention_hours)
        
        logger.info(f"Cleaned up {deleted_count} old records")
        print(f"Successfully cleaned up {deleted_count} old records")
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup data: {e}")
        return False


def main():
    """Main entry point with command-line interface."""
    logger = None
    
    try:
        parser = argparse.ArgumentParser(
            description='Facebook Marketplace Automation Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py init-db              # Initialize database
  python main.py scrape               # Run scraper once
  python main.py scrape --verbose     # Run with debug logging
  python main.py schedule             # Start automated scheduler
  python main.py dashboard            # Launch web dashboard
  python main.py status               # Show system status
  python main.py cleanup              # Clean up old data
            """
        )
        
        parser.add_argument(
            'command',
            choices=['init-db', 'scrape', 'schedule', 'dashboard', 'status', 'cleanup'],
            help='Command to execute'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        args = parser.parse_args()
        
        # Setup logging
        logger = setup_logging(args.verbose)
        
        # Execute command
        success = False
        
        try:
            if args.command == 'init-db':
                success = init_database(logger)
            elif args.command == 'scrape':
                success = run_scraper(logger, args.verbose)
            elif args.command == 'schedule':
                success = start_scheduler(logger)
            elif args.command == 'dashboard':
                success = start_dashboard(logger)
            elif args.command == 'status':
                success = show_status(logger)
            elif args.command == 'cleanup':
                success = cleanup_data(logger)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            success = True
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error: {e}")
                if args.verbose:
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                print(f"Error: {e}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to start dashboard: {e}")
        else:
            print(f"Failed to start dashboard: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
