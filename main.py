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

from core.json_manager import JSONDataManager
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
    
    # Create file handler with UTF-8 encoding
    file_handler = logging.FileHandler('logs/marketplace_automation.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Create console handler with UTF-8 encoding (or fallback gracefully)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Set up UTF-8 output for Windows console if possible
    if os.name == 'nt':  # Windows
        try:
            # Try to set console to UTF-8
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        except (AttributeError, OSError):
            # Fallback: keep original stdout but handle encoding errors gracefully
            pass
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[file_handler, console_handler]
    )
    
    return logging.getLogger(__name__)


def init_json_storage(logger):
    """Initialize the JSON data storage."""
    try:
        json_manager = JSONDataManager()
        json_manager.initialize_json_file()
        logger.info("JSON data storage initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize JSON storage: {e}")
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


def run_deep_scraper(logger, search_query: str = "iPhone 16", max_products: int = 5, verbose: bool = False):
    """Run the Facebook Marketplace deep scraper."""
    try:
        settings = Settings()
        scraper = FacebookMarketplaceScraper(settings)
        
        logger.info(f"Starting deep scraping for: {search_query}")
        results = scraper.deep_scrape_marketplace(search_query, max_products)
        
        if results:
            logger.info(f"Successfully deep scraped {len(results)} products")
            return True
        else:
            logger.warning("No products found in deep scraping")
            return False
            
    except Exception as e:
        logger.error(f"Deep scraping failed: {e}")
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
        json_manager = JSONDataManager()
        stats = json_manager.get_system_stats()
        
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
        json_manager = JSONDataManager()
        settings = Settings()
        
        retention_hours = int(settings.get('DATA_RETENTION_HOURS', 48))
        data = json_manager.load_data()
        deleted_count = json_manager.cleanup_old_data(data, retention_hours)
        if deleted_count > 0:
            json_manager.save_data(data)
        
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
            choices=['init-db', 'scrape', 'schedule', 'dashboard', 'status', 'cleanup', 'deep_scrape'],
            help='Command to execute'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--query', '-q',
            type=str,
            default='iPhone 16',
            help='Search query for deep scraping (default: iPhone 16)'
        )
        
        parser.add_argument(
            '--max-products', '-m',
            type=int,
            default=5,
            help='Maximum products to deep scrape (default: 5)'
        )
        
        args = parser.parse_args()
        
        # Setup logging
        logger = setup_logging(args.verbose)
        
        # Execute command
        success = False
        
        try:
            if args.command == 'init-db':
                success = init_json_storage(logger)
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
            elif args.command == 'deep_scrape':
                success = run_deep_scraper(logger, args.query, args.max_products, args.verbose)
            
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
