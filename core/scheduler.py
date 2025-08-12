"""
Scheduler Manager for Facebook Marketplace Automation

Handles automated scheduling of scraping tasks using APScheduler.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from core.scraper import FacebookMarketplaceScraper
from core.json_manager import JSONDataManager


class SchedulerManager:
    """Manages automated scheduling of marketplace scraping tasks."""
    
    def __init__(self, settings):
        """Initialize scheduler with configuration."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.json_manager = JSONDataManager()
        
        # Scheduler configuration
        self.scheduler_config = settings.get_scheduler_config()
        
        # Initialize scheduler
        self.scheduler = None
        self.is_running_flag = False
        
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Configure and initialize the APScheduler."""
        try:
            # Configure executors
            executors = {
                'default': ThreadPoolExecutor(max_workers=1),  # Single thread to avoid conflicts
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 1,  # Only one instance of job at a time
                'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
            }
            
            # Initialize background scheduler with memory job store
            self.scheduler = BackgroundScheduler(
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            self.logger.info("Scheduler initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup scheduler: {e}")
            # Fallback to simple background scheduler
            self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start the scheduler with configured scraping intervals."""
        try:
            if self.is_running():
                self.logger.warning("Scheduler is already running")
                return True
            
            # Add the scraping job
            interval_minutes = self.scheduler_config['interval_minutes']
            
            self.scheduler.add_job(
                func=self._run_scraping_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='marketplace_scraping',
                name='Facebook Marketplace Scraping',
                replace_existing=True,
                next_run_time=datetime.now() + timedelta(seconds=30)  # Start in 30 seconds
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running_flag = True
            
            self.logger.info(f"Scheduler started with {interval_minutes} minute intervals")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler."""
        try:
            if self.scheduler and self.is_running():
                self.scheduler.shutdown(wait=True)
                self.is_running_flag = False
                self.logger.info("Scheduler stopped successfully")
                return True
            else:
                self.logger.warning("Scheduler is not running")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        try:
            if self.scheduler:
                return self.scheduler.running
            return False
        except:
            return self.is_running_flag
    
    def get_next_run(self) -> Optional[str]:
        """Get the next scheduled run time."""
        try:
            if self.scheduler and self.is_running():
                jobs = self.scheduler.get_jobs()
                if jobs:
                    next_run = jobs[0].next_run_time
                    if next_run:
                        return next_run.strftime('%Y-%m-%d %H:%M:%S UTC')
            return None
        except Exception as e:
            self.logger.error(f"Failed to get next run time: {e}")
            return None
    
    def get_job_status(self) -> dict:
        """Get current job status and statistics."""
        try:
            status = {
                'scheduler_running': self.is_running(),
                'next_run': self.get_next_run(),
                'jobs_count': 0,
                'last_execution': None,
                'execution_count': 0
            }
            
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                status['jobs_count'] = len(jobs)
                
                # Get job execution info from JSON data
                try:
                    stats = self.json_manager.get_system_stats()
                    status['last_execution'] = stats.get('last_scrape', 'Never')
                except:
                    pass
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get job status: {e}")
            return {'error': str(e)}
    
    def _run_scraping_job(self):
        """Execute the scraping job - called by scheduler."""
        job_start_time = datetime.now()
        self.logger.info(f"Starting scheduled scraping job at {job_start_time}")
        
        try:
            # Create scraper instance
            scraper = FacebookMarketplaceScraper(self.settings)
            
            # Run the scraping
            results = scraper.scrape_marketplace()
            
            # Log results
            job_end_time = datetime.now()
            duration = (job_end_time - job_start_time).total_seconds()
            
            self.logger.info(
                f"Scheduled scraping completed in {duration:.1f} seconds. "
                f"Found {len(results)} listings"
            )
            
            return len(results)
            
        except Exception as e:
            self.logger.error(f"Scheduled scraping job failed: {e}")
            return 0
    
    def run_manual_scraping(self) -> dict:
        """Run scraping manually (outside of schedule)."""
        try:
            self.logger.info("Starting manual scraping job")
            
            start_time = datetime.now()
            scraper = FacebookMarketplaceScraper(self.settings)
            results = scraper.scrape_marketplace()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'listings_found': len(results),
                'duration_seconds': round(duration, 1),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            self.logger.info(f"Manual scraping completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Manual scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'listings_found': 0,
                'duration_seconds': 0
            }
    
    def run_custom_scraping(self, search_query: str) -> dict:
        """Run custom scraping with user-provided search query."""
        try:
            self.logger.info(f"Starting custom scraping job for: {search_query}")
            
            start_time = datetime.now()
            scraper = FacebookMarketplaceScraper(self.settings)
            results = scraper.scrape_marketplace_custom(search_query)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            # Check actual listings in JSON file for accurate count
            actual_count = len(results)
            
            # Always check JSON file to get the most accurate count
            try:
                data = self.json_manager.load_data()
                # Count products from the current scraping session
                current_timestamp = datetime.now().strftime('%Y-%m-%d')
                matching_products = [
                    p for p in data.get('products', [])
                    if search_query.lower() in p.get('title', '').lower()
                    and p.get('added_at', '').startswith(current_timestamp)
                ]
                
                # Use JSON count if it's higher than returned count (more accurate)
                if len(matching_products) > actual_count:
                    self.logger.info(f"JSON verification: Found {len(matching_products)} matching products vs {actual_count} returned from scraper")
                    actual_count = len(matching_products)
                    
                    # Log sample products for verification
                    for i, product in enumerate(matching_products[:3]):
                        self.logger.info(f"Sample product {i+1}: {product.get('title', 'NO TITLE')[:50]}...")
                        
            except Exception as e:
                self.logger.warning(f"Could not verify saved product count: {e}")
            
            result = {
                'success': True,
                'listings_found': actual_count,
                'duration_seconds': round(duration, 1),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'search_query': search_query
            }
            
            self.logger.info(f"Custom scraping completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Custom scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'listings_found': 0,
                'duration_seconds': 0,
                'search_query': search_query
            }
    
    def update_schedule(self, new_interval_minutes: int):
        """Update the scraping schedule interval."""
        try:
            if self.is_running():
                # Remove existing job
                self.scheduler.remove_job('marketplace_scraping')
                
                # Add new job with updated interval
                self.scheduler.add_job(
                    func=self._run_scraping_job,
                    trigger=IntervalTrigger(minutes=new_interval_minutes),
                    id='marketplace_scraping',
                    name='Facebook Marketplace Scraping',
                    replace_existing=True,
                    next_run_time=datetime.now() + timedelta(minutes=new_interval_minutes)
                )
                
                self.logger.info(f"Schedule updated to {new_interval_minutes} minute intervals")
                return True
            else:
                self.logger.warning("Cannot update schedule - scheduler is not running")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update schedule: {e}")
            return False
    
    def pause_job(self):
        """Pause the scraping job."""
        try:
            if self.scheduler and self.is_running():
                self.scheduler.pause_job('marketplace_scraping')
                self.logger.info("Scraping job paused")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause job: {e}")
            return False
    
    def resume_job(self):
        """Resume the scraping job."""
        try:
            if self.scheduler and self.is_running():
                self.scheduler.resume_job('marketplace_scraping')
                self.logger.info("Scraping job resumed")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume job: {e}")
            return False
    
    def keep_alive(self):
        """Keep the scheduler running - for CLI usage."""
        try:
            while self.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Scheduler interrupted by user")
            self.stop()
    
    def get_schedule_info(self) -> dict:
        """Get detailed schedule information."""
        try:
            info = {
                'scheduler_status': 'running' if self.is_running() else 'stopped',
                'interval_minutes': self.scheduler_config['interval_minutes'],
                'next_run': self.get_next_run(),
                'jobs': []
            }
            
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    job_info = {
                        'id': job.id,
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    }
                    info['jobs'].append(job_info)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get schedule info: {e}")
            return {'error': str(e)}
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if self.is_running():
                self.stop()
        except:
            pass
