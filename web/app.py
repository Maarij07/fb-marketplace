"""
Flask Web Application for Facebook Marketplace Automation

Provides web dashboard for monitoring scraping results, controlling scheduler,
and viewing analytics.
"""

import json
import logging
import queue
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response

from core.json_manager import JSONDataManager
from core.scheduler import SchedulerManager
from core.persistent_session import get_persistent_session
from core.excel_manager import ExcelManager
from core.google_sheets_manager import GoogleSheetsManager
from core.price_monitor import PriceChangeMonitor
from core.notification_monitor import get_notification_monitor


def calculate_price_distribution(products):
    """Calculate price distribution for chart data."""
    distribution = {
        '0-4999 SEK': 0,
        '5000-7999 SEK': 0, 
        '8000-11999 SEK': 0,
        '12000+ SEK': 0
    }
    
    for product in products:
        price_info = product.get('price', {})
        if isinstance(price_info, dict) and price_info.get('amount'):
            try:
                amount = int(price_info.get('amount', 0))
                # Handle incomplete prices (single digits likely represent thousands)
                if amount < 100:  # Single or double digit
                    amount = amount * 1000
                
                if amount < 5000:
                    distribution['0-4999 SEK'] += 1
                elif amount < 8000:
                    distribution['5000-7999 SEK'] += 1
                elif amount < 12000:
                    distribution['8000-11999 SEK'] += 1
                else:
                    distribution['12000+ SEK'] += 1
            except (ValueError, TypeError):
                continue
    
    return list(distribution.items())


# Global notification system
class NotificationManager:
    """Manages real-time notifications via Server-Sent Events."""
    
    def __init__(self):
        self.clients = set()
        self.lock = threading.Lock()
    
    def add_client(self, client_queue):
        """Add a new SSE client."""
        with self.lock:
            self.clients.add(client_queue)
    
    def remove_client(self, client_queue):
        """Remove an SSE client."""
        with self.lock:
            self.clients.discard(client_queue)
    
    def broadcast_notification(self, message_type, data):
        """Send notification to all connected clients."""
        message = {
            'type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.lock:
            # Remove disconnected clients
            disconnected_clients = set()
            for client_queue in self.clients.copy():
                try:
                    client_queue.put(message, block=False)
                except:
                    disconnected_clients.add(client_queue)
            
            # Clean up disconnected clients
            for client in disconnected_clients:
                self.clients.discard(client)


def create_app(settings):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'marketplace-automation-secret-key'
    
    # Initialize logger first
    logger = logging.getLogger(__name__)
    
    # Initialize components
    json_manager = JSONDataManager()
    scheduler_manager = SchedulerManager(settings)
    notification_manager = NotificationManager()
    excel_manager = ExcelManager()
    google_sheets_manager = GoogleSheetsManager()
    
    # Initialize schedulers storage (max 3 schedulers)
    app.schedulers = []  # List to store multiple scheduler configurations
    app.max_schedulers = 3
    
    # Initialize price monitor with notification callback
    def price_notification_callback(notification_data):
        """Callback for price change notifications."""
        notification_manager.broadcast_notification(
            notification_data['type'], 
            notification_data['data']
        )
    
    price_monitor = PriceChangeMonitor(json_manager, price_notification_callback)
    
    # Initialize notification monitor with callback
    def browser_notification_callback(notification_data):
        """Callback for browser-based notifications."""
        notification_manager.broadcast_notification(
            notification_data['type'], 
            notification_data['data']
        )
    
    notification_monitor = get_notification_monitor(settings, browser_notification_callback)
    
    # Auto-start notification monitoring is disabled by default
    # Users can manually start it via the dashboard button
    logger.info("Browser notification monitoring is available - use dashboard to start manually")
    
    # Make managers accessible to other modules
    app.notification_manager = notification_manager
    app.notification_monitor = notification_monitor
    
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/api/stats')
    def api_stats():
        """Get system statistics."""
        try:
            stats = json_manager.get_system_stats()
            scheduler_status = scheduler_manager.get_job_status()
            
            return jsonify({
                'success': True,
                'data': {
                    **stats,
                    'scheduler': scheduler_status
                }
            })
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/listings')
    def api_listings():
        """Get recent listings."""
        try:
            limit = int(request.args.get('limit', 50))
            listings = json_manager.get_recent_products(limit)
            
            # Format data for frontend
            formatted_listings = []
            for listing in listings:
                formatted_listing = dict(listing)
                # Format price display for Swedish marketplace
                price_info = formatted_listing.get('price', {})
                if isinstance(price_info, dict) and price_info.get('amount'):
                    currency = price_info.get('currency', 'SEK')
                    amount = price_info.get('amount', '0')
                    # Handle incomplete prices (like "SEK6" -> "6000+ SEK")
                    if len(str(amount)) <= 2:
                        formatted_listing['price_display'] = f"{amount}000+ {currency}"
                    else:
                        formatted_listing['price_display'] = f"{amount} {currency}"
                else:
                    formatted_listing['price_display'] = "N/A"
                
                # Convert location format
                location_info = formatted_listing.get('location', {})
                if isinstance(location_info, dict):
                    city = location_info.get('city', 'Unknown')
                    formatted_listing['seller_location'] = city
                else:
                    formatted_listing['seller_location'] = 'Unknown'
                
                # Add seller name if missing
                if not formatted_listing.get('seller_name'):
                    seller_info = formatted_listing.get('seller', {}).get('info', 'Private Seller')
                    formatted_listing['seller_name'] = seller_info if seller_info != 'Not extracted' else 'Private Seller'
                
                # Add category field for dashboard display
                product_details = formatted_listing.get('product_details', {})
                model = product_details.get('model', '')
                if 'iphone' in model.lower():
                    formatted_listing['category'] = 'electronics'
                else:
                    formatted_listing['category'] = 'other'
                
                # Ensure created_at field exists for dashboard sorting
                if not formatted_listing.get('created_at'):
                    formatted_listing['created_at'] = formatted_listing.get('added_at', datetime.now().isoformat())
                
                formatted_listings.append(formatted_listing)
            
            return jsonify({
                'success': True,
                'data': formatted_listings
            })
        except Exception as e:
            logger.error(f"Failed to get listings: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/listing/<listing_id>')
    def api_listing_details(listing_id):
        """Get detailed information for a specific listing."""
        try:
            # Get the listing by ID
            listing = json_manager.get_product_by_id(listing_id)
            
            if not listing:
                return jsonify({
                    'success': False,
                    'error': 'Listing not found'
                }), 404
            
            # Format the listing data for the frontend
            formatted_listing = dict(listing)
            
            # Format price display
            price_info = formatted_listing.get('price', {})
            if isinstance(price_info, dict) and price_info.get('amount'):
                currency = price_info.get('currency', 'SEK')
                amount = price_info.get('amount', '0')
                if len(str(amount)) <= 2:
                    formatted_listing['price_display'] = f"{amount}000+ {currency}"
                else:
                    formatted_listing['price_display'] = f"{amount} {currency}"
            else:
                formatted_listing['price_display'] = "N/A"
            
            # Format location
            location_info = formatted_listing.get('location', {})
            if isinstance(location_info, dict):
                city = location_info.get('city', 'Unknown')
                formatted_listing['seller_location'] = city
            else:
                formatted_listing['seller_location'] = 'Unknown'
            
            # Format seller info
            if not formatted_listing.get('seller_name'):
                seller_info = formatted_listing.get('seller', {}).get('info', 'Private Seller')
                formatted_listing['seller_name'] = seller_info if seller_info != 'Not extracted' else 'Private Seller'
            
            # Format dates
            if not formatted_listing.get('created_at'):
                formatted_listing['created_at'] = formatted_listing.get('added_at', datetime.now().isoformat())
            
            # Format posted date if available
            posted_date = formatted_listing.get('posted_date', '')
            if posted_date:
                formatted_listing['posted_date_display'] = posted_date
            else:
                formatted_listing['posted_date_display'] = 'Unknown'
            
            # Add category
            product_details = formatted_listing.get('product_details', {})
            model = product_details.get('model', '')
            if 'iphone' in model.lower():
                formatted_listing['category'] = 'Electronics'
            else:
                formatted_listing['category'] = 'Other'
            
            # Extract and format images for the frontend
            images = []
            
            # First, try to get images from the main images array
            if formatted_listing.get('images') and isinstance(formatted_listing['images'], list):
                for img in formatted_listing['images']:
                    if isinstance(img, dict) and img.get('url'):
                        images.append(img['url'])
                    elif isinstance(img, str):
                        images.append(img)
            
            # Also try to get images from deep_data if available
            deep_data = formatted_listing.get('deep_data', {})
            if isinstance(deep_data, dict):
                # Check comprehensive_product images
                comp_product = deep_data.get('comprehensive_product', {})
                if comp_product.get('images') and isinstance(comp_product['images'], list):
                    for img in comp_product['images']:
                        if isinstance(img, dict) and img.get('url'):
                            url = img['url']
                            if url not in images:  # Avoid duplicates
                                images.append(url)
                        elif isinstance(img, str) and img not in images:
                            images.append(img)
            
            # Create deep_scraped_data JSON string for the frontend 
            # (the frontend expects this format for image parsing)
            if images:
                formatted_listing['deep_scraped_data'] = json.dumps({
                    'images': images,
                    'product_details': product_details
                })
            
            # Add description from multiple possible sources
            if not formatted_listing.get('description'):
                # Try to get description from deep_data
                if deep_data.get('comprehensive_product', {}).get('description'):
                    formatted_listing['description'] = deep_data['comprehensive_product']['description']
            
            # Add marketplace URL if available
            if not formatted_listing.get('url') and formatted_listing.get('marketplace_url'):
                formatted_listing['url'] = formatted_listing['marketplace_url']
            
            # Add updated_at field from FacebookTimeParser timing data
            timing_info = formatted_listing.get('timing', {})
            if isinstance(timing_info, dict) and timing_info.get('timestamp'):
                # Use the parsed timestamp from FacebookTimeParser
                formatted_listing['updated_at'] = timing_info['timestamp']
            elif deep_data.get('basic_info', {}).get('extraction_timestamp'):
                # Fallback to extraction timestamp from deep scrape data
                formatted_listing['updated_at'] = deep_data['basic_info']['extraction_timestamp']
            elif formatted_listing.get('created_at'):
                # Final fallback to created_at if available
                formatted_listing['updated_at'] = formatted_listing['created_at']
            else:
                # Last resort - current time
                formatted_listing['updated_at'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'data': formatted_listing
            })
            
        except Exception as e:
            logger.error(f"Failed to get listing details for {listing_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/price-changes')
    def api_price_changes():
        """Get recent price changes with dynamic keyword-based notifications."""
        try:
            limit = int(request.args.get('limit', 50))
            
            # Get price changes from our dynamic monitoring system
            price_changes = price_monitor.get_recent_price_changes(limit)
            
            return jsonify({
                'success': True,
                'data': price_changes
            })
        except Exception as e:
            logger.error(f"Failed to get price changes: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/price-chart')
    def api_price_chart():
        """Get price distribution data for charts."""
        try:
            # Simple price distribution from JSON data  
            products = json_manager.get_recent_products(1000)
            distribution = calculate_price_distribution(products)
            
            chart_data = {
                'labels': [item[0] for item in distribution],
                'data': [item[1] for item in distribution]
            }
            
            return jsonify({
                'success': True,
                'data': chart_data
            })
        except Exception as e:
            logger.error(f"Failed to get price chart data: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/category-chart')
    def api_category_chart():
        """Get category distribution data for charts."""
        try:
            # Get category distribution from database
            # This is a simple implementation - you could enhance it
            listings = json_manager.get_recent_products(1000)
            
            category_counts = {}
            for listing in listings:
                category = listing.get('product_details', {}).get('model', 'other')
                if 'iphone' in category.lower():
                    category = 'electronics'
                else:
                    category = 'other'
                category_counts[category] = category_counts.get(category, 0) + 1
            
            chart_data = {
                'labels': list(category_counts.keys()),
                'data': list(category_counts.values())
            }
            
            return jsonify({
                'success': True,
                'data': chart_data
            })
        except Exception as e:
            logger.error(f"Failed to get category chart data: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/start', methods=['POST'])
    def api_scheduler_start():
        """Start the scheduler."""
        try:
            success = scheduler_manager.start()
            return jsonify({
                'success': success,
                'message': 'Scheduler started successfully' if success else 'Failed to start scheduler'
            })
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/stop', methods=['POST'])
    def api_scheduler_stop():
        """Stop the scheduler."""
        try:
            success = scheduler_manager.stop()
            return jsonify({
                'success': success,
                'message': 'Scheduler stopped successfully' if success else 'Failed to stop scheduler'
            })
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/create', methods=['POST'])
    def api_scheduler_create():
        """Create a new scheduler configuration."""
        try:
            data = request.get_json()
            search_query = data.get('search_query', '').strip()
            city = data.get('city', '').strip() or None
            interval_minutes = data.get('interval_minutes', 30)
            
            # Sydney cities list - alphabetical order
            sydney_cities = [
                'Alexandria', 'Ashfield', 'Auburn', 'Balmain', 'Bankstown',
                'Blacktown', 'Bondi Beach', 'Bondi Junction', 'Burwood', 'Castle Hill',
                'Chatswood', 'Cronulla', 'Darlinghurst', 'Five Dock', 'Homebush',
                'Hornsby', 'Kirribilli', 'Leichhardt', 'Liverpool', 'Macquarie Park',
                'Manly', 'Maroubra', 'Mascot', 'Milsons Point', 'Miranda',
                'Neutral Bay', 'Newtown', 'North Sydney', 'Paddington', 'Parramatta',
                'Potts Point', 'Randwick', 'Rhodes', 'Ryde', 'Surry Hills',
                'Sydney CBD', 'Wetherill Park'
            ]
            
            if not search_query:
                return jsonify({'success': False, 'message': 'Search query is required'})
            
            if interval_minutes not in [15, 30, 60]:
                return jsonify({'success': False, 'message': 'Invalid interval. Must be 15, 30, or 60 minutes'})
            
            # Check if we've reached the maximum number of schedulers
            if len(app.schedulers) >= app.max_schedulers:
                return jsonify({
                    'success': False, 
                    'message': f'Limit reached! Maximum {app.max_schedulers} schedulers allowed.'
                })
            
            # Check for duplicate search queries
            for scheduler in app.schedulers:
                if scheduler['search_query'].lower() == search_query.lower():
                    return jsonify({
                        'success': False,
                        'message': f'A scheduler for "{search_query}" already exists.'
                    })
            
            # Create new scheduler configuration
            new_scheduler = {
                'id': len(app.schedulers) + 1,
                'search_query': search_query,
                'city': city or sydney_cities[0],
                'interval_minutes': interval_minutes,
                'is_running': True,
                'created_at': datetime.now().isoformat(),
                'sydney_cities': sydney_cities
            }
            
            # Add to schedulers list
            app.schedulers.append(new_scheduler)
            
            return jsonify({
                'success': True,
                'message': f'Scheduler created and started successfully for "{search_query}"',
                'scheduler': new_scheduler
            })
            
        except Exception as e:
            logger.error(f"Failed to create scheduler: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/status')
    def api_scheduler_status():
        """Get scheduler status."""
        try:
            status = scheduler_manager.get_job_status()
            return jsonify({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sydney-cities')
    def api_sydney_cities():
        """Get list of Sydney cities for scheduler configuration."""
        try:
            sydney_cities = [
                'Alexandria', 'Ashfield', 'Auburn', 'Balmain', 'Bankstown',
                'Blacktown', 'Bondi Beach', 'Bondi Junction', 'Burwood', 'Castle Hill',
                'Chatswood', 'Cronulla', 'Darlinghurst', 'Five Dock', 'Homebush',
                'Hornsby', 'Kirribilli', 'Leichhardt', 'Liverpool', 'Macquarie Park',
                'Manly', 'Maroubra', 'Mascot', 'Milsons Point', 'Miranda',
                'Neutral Bay', 'Newtown', 'North Sydney', 'Paddington', 'Parramatta',
                'Potts Point', 'Randwick', 'Rhodes', 'Ryde', 'Surry Hills',
                'Sydney CBD', 'Wetherill Park'
            ]
            
            return jsonify({
                'success': True,
                'data': sydney_cities
            })
        except Exception as e:
            logger.error(f"Failed to get Sydney cities: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/schedulers')
    def api_get_schedulers():
        """Get list of schedulers."""
        try:
            # Return the schedulers from our array
            schedulers = []
            
            for scheduler in app.schedulers:
                # Add next_run information for running schedulers
                scheduler_data = scheduler.copy()
                if scheduler_data['is_running']:
                    status = scheduler_manager.get_job_status()
                    scheduler_data['next_run'] = status.get('next_run')
                else:
                    scheduler_data['next_run'] = None
                
                schedulers.append(scheduler_data)
            
            return jsonify({
                'success': True,
                'data': schedulers
            })
        except Exception as e:
            logger.error(f"Failed to get schedulers: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/<int:scheduler_id>/start', methods=['POST'])
    def api_start_scheduler(scheduler_id):
        """Start a specific scheduler."""
        try:
            # Find the scheduler in our array
            scheduler_to_start = None
            for i, scheduler in enumerate(app.schedulers):
                if scheduler['id'] == scheduler_id:
                    scheduler_to_start = scheduler
                    app.schedulers[i]['is_running'] = True
                    break
            
            if not scheduler_to_start:
                return jsonify({
                    'success': False,
                    'message': 'Scheduler not found'
                })
            
            return jsonify({
                'success': True,
                'message': f'Scheduler for "{scheduler_to_start["search_query"]}" started successfully'
            })
        except Exception as e:
            logger.error(f"Failed to start scheduler {scheduler_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/<int:scheduler_id>/pause', methods=['POST'])
    def api_pause_scheduler(scheduler_id):
        """Pause a specific scheduler."""
        try:
            # Find the scheduler in our array
            scheduler_to_pause = None
            for i, scheduler in enumerate(app.schedulers):
                if scheduler['id'] == scheduler_id:
                    scheduler_to_pause = scheduler
                    app.schedulers[i]['is_running'] = False
                    break
            
            if not scheduler_to_pause:
                return jsonify({
                    'success': False,
                    'message': 'Scheduler not found'
                })
            
            return jsonify({
                'success': True,
                'message': f'Scheduler for "{scheduler_to_pause["search_query"]}" paused successfully'
            })
        except Exception as e:
            logger.error(f"Failed to pause scheduler {scheduler_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/<int:scheduler_id>', methods=['DELETE'])
    def api_delete_scheduler(scheduler_id):
        """Delete a specific scheduler."""
        try:
            # Find and remove the scheduler from our array
            scheduler_to_delete = None
            for i, scheduler in enumerate(app.schedulers):
                if scheduler['id'] == scheduler_id:
                    scheduler_to_delete = app.schedulers.pop(i)
                    break
            
            if not scheduler_to_delete:
                return jsonify({
                    'success': False,
                    'message': 'Scheduler not found'
                })
            
            return jsonify({
                'success': True,
                'message': f'Scheduler for "{scheduler_to_delete["search_query"]}" deleted successfully'
            })
        except Exception as e:
            logger.error(f"Failed to delete scheduler {scheduler_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    
    @app.route('/api/scrape/run', methods=['POST'])
    def api_run_scrape():
        """Run scraper manually."""
        try:
            result = scheduler_manager.run_manual_scraping()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to run manual scraping: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scrape/custom', methods=['POST'])
    def api_run_custom_scrape():
        """Run scraper with custom search query."""
        try:
            data = request.get_json()
            search_query = data.get('query', '').strip()
            
            if not search_query:
                return jsonify({'success': False, 'error': 'Search query is required'})
            
            # Pass the notification manager for real-time updates
            result = scheduler_manager.run_custom_scraping(search_query, notification_manager)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to run custom scraping: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/search')
    def api_search():
        """Search listings by keyword."""
        try:
            keyword = request.args.get('q', '')
            if not keyword:
                return jsonify({'success': False, 'error': 'No search keyword provided'})
            
            limit = int(request.args.get('limit', 100))
            listings = json_manager.search_products(keyword, limit)
            
            # Format data for frontend
            formatted_listings = []
            for listing in listings:
                formatted_listing = dict(listing)
                # Format price display for Swedish marketplace
                price_info = formatted_listing.get('price', {})
                if isinstance(price_info, dict) and price_info.get('amount'):
                    currency = price_info.get('currency', 'SEK')
                    amount = price_info.get('amount', '0')
                    if len(str(amount)) <= 2:
                        formatted_listing['price_display'] = f"{amount}000+ {currency}"
                    else:
                        formatted_listing['price_display'] = f"{amount} {currency}"
                else:
                    formatted_listing['price_display'] = "N/A"
                
                formatted_listings.append(formatted_listing)
            
            return jsonify({
                'success': True,
                'data': formatted_listings,
                'count': len(formatted_listings)
            })
        except Exception as e:
            logger.error(f"Failed to search listings: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/cleanup', methods=['POST'])
    def api_cleanup():
        """Clean up old data."""
        try:
            retention_hours = int(request.json.get('retention_hours', 48))
            # JSON version doesn't need cleanup - files are small
            deleted_count = 0
            
            return jsonify({
                'success': True,
                'message': f'Cleaned up {deleted_count} old records',
                'deleted_count': deleted_count
            })
        except Exception as e:
            logger.error(f"Failed to cleanup data: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/session/status')
    def api_session_status():
        """Get persistent browser session status."""
        try:
            persistent_session = get_persistent_session(settings)
            status = persistent_session.get_session_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/session/refresh', methods=['POST'])
    def api_session_refresh():
        """Refresh the persistent browser session."""
        try:
            persistent_session = get_persistent_session(settings)
            success = persistent_session.refresh_session()
            
            return jsonify({
                'success': success,
                'message': 'Session refreshed successfully' if success else 'Failed to refresh session'
            })
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/session/close', methods=['POST'])
    def api_session_close():
        """Close the persistent browser session."""
        try:
            persistent_session = get_persistent_session(settings)
            persistent_session.close_session()
            
            return jsonify({
                'success': True,
                'message': 'Session closed successfully'
            })
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/events')
    def sse_events():
        """Server-Sent Events endpoint for real-time notifications."""
        def event_generator():
            client_queue = queue.Queue()
            notification_manager.add_client(client_queue)
            
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'data': 'Connected to notification stream', 'timestamp': datetime.now().isoformat()})}\n\n"
                
                while True:
                    try:
                        # Wait for message with timeout
                        message = client_queue.get(timeout=30)
                        yield f"data: {json.dumps(message)}\n\n"
                    except queue.Empty:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'data': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
            except GeneratorExit:
                notification_manager.remove_client(client_queue)
            finally:
                notification_manager.remove_client(client_queue)
        
        return Response(event_generator(), mimetype='text/event-stream')
    
    @app.route('/api/excel/export', methods=['POST'])
    def api_excel_export():
        """Export data to Google Sheets and open spreadsheet."""
        try:
            # Your Google Sheets URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit?usp=sharing"
            worksheet_name = "Products"
            
            # Export to Google Sheets
            success = google_sheets_manager.export_all_products_to_sheets(sheet_url, worksheet_name)
            
            if success:
                # Open the Google Sheets in browser
                import webbrowser
                try:
                    webbrowser.open(sheet_url)
                    return jsonify({
                        'success': True,
                        'message': 'Data exported to Google Sheets and opened successfully!',
                        'sheet_url': sheet_url,
                        'action': 'google_sheets_export'
                    })
                except Exception as browser_error:
                    logger.warning(f"Failed to open browser: {browser_error}")
                    return jsonify({
                        'success': True,
                        'message': 'Data exported to Google Sheets successfully, but failed to open browser automatically.',
                        'sheet_url': sheet_url,
                        'action': 'google_sheets_export'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to export data to Google Sheets. Please check your credentials and permissions.',
                    'help': 'Make sure you have set up Google API credentials and shared the spreadsheet with your service account.'
                })
                
        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
            return jsonify({
                'success': False, 
                'error': f'Google Sheets export failed: {str(e)}',
                'help': 'Check the GOOGLE_SHEETS_SETUP.md file for setup instructions.'
            })
    
    @app.route('/api/excel/backup', methods=['POST'])
    def api_excel_backup():
        """Create Google Sheets backup of recent data."""
        try:
            data = request.get_json() or {}
            hours = int(data.get('hours', 2))
            
            # Your Google Sheets URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit?usp=sharing"
            
            # Create backup in Google Sheets with timestamped worksheet name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            worksheet_name = f"Backup_{hours}h_{timestamp}"
            
            success = google_sheets_manager.create_backup_in_sheets(sheet_url, hours, "Backup")
            
            if success:
                # Open the Google Sheets in browser
                import webbrowser
                try:
                    webbrowser.open(sheet_url)
                    return jsonify({
                        'success': True,
                        'message': f'Backup created for last {hours} hours in Google Sheets and opened successfully!',
                        'sheet_url': sheet_url,
                        'action': 'google_sheets_backup'
                    })
                except Exception as browser_error:
                    logger.warning(f"Failed to open browser: {browser_error}")
                    return jsonify({
                        'success': True,
                        'message': f'Backup created for last {hours} hours in Google Sheets successfully, but failed to open browser automatically.',
                        'sheet_url': sheet_url,
                        'action': 'google_sheets_backup'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': f'No data found in the last {hours} hours to backup, or Google Sheets export failed.'
                })
                
        except Exception as e:
            logger.error(f"Failed to create Google Sheets backup: {e}")
            return jsonify({
                'success': False, 
                'error': f'Google Sheets backup failed: {str(e)}',
                'help': 'Check the GOOGLE_SHEETS_SETUP.md file for setup instructions.'
            })
    
    @app.route('/api/excel/files')
    def api_excel_files():
        """Get list of available Excel backup files."""
        try:
            files = excel_manager.get_backup_files()
            return jsonify({
                'success': True,
                'data': files
            })
        except Exception as e:
            logger.error(f"Failed to get Excel files: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    # Google Sheets Export APIs
    @app.route('/api/sheets/export', methods=['POST'])
    def api_sheets_export():
        """Export all products to Google Sheets."""
        try:
            data = request.get_json() or {}
            sheet_url = data.get('sheet_url', '').strip()
            worksheet_name = data.get('worksheet_name', 'Products')
            
            if not sheet_url:
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets URL is required'
                })
            
            # Export to Google Sheets
            success = google_sheets_manager.export_all_products_to_sheets(sheet_url, worksheet_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully exported all products to Google Sheets worksheet "{worksheet_name}"!',
                    'sheet_url': sheet_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to export data to Google Sheets. Check credentials and permissions.'
                })
                
        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sheets/backup', methods=['POST'])
    def api_sheets_backup():
        """Create backup of recent data in Google Sheets."""
        try:
            data = request.get_json() or {}
            sheet_url = data.get('sheet_url', '').strip()
            hours = int(data.get('hours', 2))
            worksheet_name = data.get('worksheet_name', 'Backup')
            
            if not sheet_url:
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets URL is required'
                })
            
            # Create backup in Google Sheets
            success = google_sheets_manager.create_backup_in_sheets(sheet_url, hours, worksheet_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully created backup of last {hours} hours in Google Sheets!',
                    'sheet_url': sheet_url
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'No data found in the last {hours} hours to backup, or export failed.'
                })
                
        except Exception as e:
            logger.error(f"Failed to create Google Sheets backup: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sheets/analytics', methods=['POST'])
    def api_sheets_analytics():
        """Create analytics summary in Google Sheets."""
        try:
            data = request.get_json() or {}
            sheet_url = data.get('sheet_url', '').strip()
            worksheet_name = data.get('worksheet_name', 'Analytics')
            
            if not sheet_url:
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets URL is required'
                })
            
            # Create analytics sheet
            success = google_sheets_manager.create_analytics_sheet(sheet_url, worksheet_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully created analytics summary in Google Sheets worksheet "{worksheet_name}"!',
                    'sheet_url': sheet_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to create analytics sheet. Check credentials and permissions.'
                })
                
        except Exception as e:
            logger.error(f"Failed to create Google Sheets analytics: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sheets/append', methods=['POST'])
    def api_sheets_append():
        """Append current products to Google Sheets without removing existing data."""
        try:
            data = request.get_json() or {}
            sheet_url = data.get('sheet_url')
            
            if not sheet_url:
                return jsonify({
                    'success': False, 
                    'error': 'sheet_url is required'
                })
            
            worksheet_name = data.get('worksheet_name', 'Products')
            
            success = google_sheets_manager.append_products_to_sheets(sheet_url, worksheet_name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully appended products to {worksheet_name} worksheet'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to append products to Google Sheets'
                })
                
        except Exception as e:
            logger.error(f"Sheets append API error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sheets/info')
    def api_sheets_info():
        """Get information about connected Google Sheets."""
        try:
            data = request.get_json() or {}
            sheet_url = data.get('sheet_url', '').strip()
            
            if not sheet_url:
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets URL is required'
                })
            
            # Get sheet information
            sheet_info = google_sheets_manager.get_sheet_info(sheet_url)
            
            if sheet_info:
                return jsonify({
                    'success': True,
                    'data': sheet_info
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to get sheet information. Check URL and permissions.'
                })
                
        except Exception as e:
            logger.error(f"Failed to get Google Sheets info: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/sheets/test', methods=['GET'])
    def api_sheets_test():
        """Test Google Sheets API connection."""
        try:
            # Test connection
            connection_ok = google_sheets_manager.test_connection()
            
            if connection_ok:
                return jsonify({
                    'success': True,
                    'message': 'Google Sheets API connection is working!'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets API connection failed. Check credentials.'
                })
                
        except Exception as e:
            logger.error(f"Failed to test Google Sheets connection: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    # Browser Notification Monitoring APIs
    @app.route('/api/monitoring/status')
    def api_monitoring_status():
        """Get notification monitoring status."""
        try:
            status = notification_monitor.get_monitoring_status()
            return jsonify({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"Failed to get monitoring status: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/monitoring/start', methods=['POST'])
    def api_monitoring_start():
        """Start browser notification monitoring."""
        try:
            success = notification_monitor.start_monitoring()
            return jsonify({
                'success': success,
                'message': 'Browser monitoring started successfully' if success else 'Failed to start browser monitoring'
            })
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/monitoring/stop', methods=['POST'])
    def api_monitoring_stop():
        """Stop browser notification monitoring."""
        try:
            notification_monitor.stop_monitoring()
            return jsonify({
                'success': True,
                'message': 'Browser monitoring stopped successfully'
            })
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/monitoring/refresh', methods=['POST'])
    def api_monitoring_refresh():
        """Refresh the monitoring browser page."""
        try:
            notification_monitor.refresh_page()
            return jsonify({
                'success': True,
                'message': 'Browser page refreshed successfully'
            })
        except Exception as e:
            logger.error(f"Failed to refresh monitoring page: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    from config.settings import Settings
    
    settings = Settings()
    app = create_app(settings)
    
    flask_config = settings.get_flask_config()
    app.run(
        host=flask_config['host'],
        port=flask_config['port'],
        debug=flask_config['debug']
    )
