"""
Flask Web Application for Facebook Marketplace Automation

Provides web dashboard for monitoring scraping results, controlling scheduler,
and viewing analytics.
"""

import json
import logging
import queue
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response

from core.json_manager import JSONDataManager
from core.scheduler import SchedulerManager
from core.persistent_session import get_persistent_session
from core.excel_manager import ExcelManager


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
    
    # Initialize components
    json_manager = JSONDataManager()
    scheduler_manager = SchedulerManager(settings)
    notification_manager = NotificationManager()
    excel_manager = ExcelManager()
    
    # Make notification manager accessible to other modules
    app.notification_manager = notification_manager
    
    logger = logging.getLogger(__name__)
    
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
    
    @app.route('/api/price-changes')
    def api_price_changes():
        """Get recent price changes (notifications)."""
        try:
            limit = int(request.args.get('limit', 50))
            
            # Since we don't have actual price tracking yet, show dummy notifications
            # In a real system, this would come from a price tracking database
            dummy_notifications = [
                {
                    'id': 1,
                    'title': 'iPhone 12 Pro Max 256GB',
                    'seller': 'Aslihan',
                    'old_price': 8500,
                    'new_price': 7800,
                    'change_amount': -700,
                    'change_percentage': -8.2,
                    'detected_at': '2025-08-24T05:30:00Z',
                    'location': 'Stockholm'
                },
                {
                    'id': 2,
                    'title': 'iPhone 16 Pro Black Titanium',
                    'seller': 'Marcus',
                    'old_price': 12000,
                    'new_price': 11500,
                    'change_amount': -500,
                    'change_percentage': -4.2,
                    'detected_at': '2025-08-24T04:15:00Z',
                    'location': 'Stockholm'
                },
                {
                    'id': 3,
                    'title': 'iPhone 15 Pro Max Natural Titanium',
                    'seller': 'Sara',
                    'old_price': 9500,
                    'new_price': 10200,
                    'change_amount': 700,
                    'change_percentage': 7.4,
                    'detected_at': '2025-08-24T03:45:00Z',
                    'location': 'Stockholm'
                }
            ]
            
            # Format data for frontend
            formatted_changes = []
            for change in dummy_notifications[:limit]:
                formatted_change = {
                    'id': change['id'],
                    'title': change['title'],
                    'seller': change['seller'],
                    'old_price': change['old_price'],
                    'new_price': change['new_price'],
                    'change_amount': change['change_amount'],
                    'change_percentage': change['change_percentage'],
                    'detected_at': change['detected_at'],
                    'location': change['location']
                }
                
                # Format price displays
                formatted_change['old_price_display'] = f"{change['old_price']} SEK"
                formatted_change['new_price_display'] = f"{change['new_price']} SEK"
                
                # Format change display
                sign = "+" if change['change_amount'] > 0 else ""
                formatted_change['change_display'] = f"{sign}{change['change_amount']} SEK"
                formatted_change['change_percent_display'] = f"{sign}{change['change_percentage']:.1f}%"
                
                # Format notification message
                action = "increased" if change['change_amount'] > 0 else "decreased"
                formatted_change['notification_message'] = f"{change['seller']} {action} {change['title'][:30]}... price by {abs(change['change_amount'])} SEK"
                
                formatted_changes.append(formatted_change)
            
            return jsonify({
                'success': True,
                'data': formatted_changes
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
            
            if not search_query:
                return jsonify({'success': False, 'message': 'Search query is required'})
            
            if interval_minutes not in [15, 30, 60]:
                return jsonify({'success': False, 'message': 'Invalid interval. Must be 15, 30, or 60 minutes'})
            
            # For now, we'll update the scheduler with the new configuration
            # In a more complex system, you might store multiple scheduler configs
            success = scheduler_manager.update_configuration({
                'search_query': search_query,
                'city': city,
                'interval_minutes': interval_minutes
            })
            
            if success:
                # Start the scheduler with new configuration
                scheduler_manager.start()
                return jsonify({
                    'success': True,
                    'message': f'Scheduler created and started successfully for "{search_query}"'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to create scheduler configuration'
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
    
    @app.route('/api/schedulers')
    def api_get_schedulers():
        """Get list of schedulers."""
        try:
            # For now, we'll simulate multiple schedulers using the current single scheduler
            # In a real implementation, you'd store multiple scheduler configurations
            status = scheduler_manager.get_job_status()
            schedulers = []
            
            # Only show scheduler if it has been explicitly configured with a search query
            config = scheduler_manager.scheduler_config
            search_query = config.get('search_query')
            
            # Only show if there's an actual search query set (not None or empty)
            if search_query and search_query.strip():
                is_running = status.get('scheduler_running', False)
                scheduler_data = {
                    'id': 1,
                    'search_query': search_query,
                    'city': config.get('city', 'Stockholm'),
                    'interval_minutes': config.get('interval_minutes', 30),
                    'is_running': is_running,
                    'created_at': datetime.now().isoformat(),
                    'next_run': status.get('next_run') if is_running else None
                }
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
            success = scheduler_manager.start()
            return jsonify({
                'success': success,
                'message': 'Scheduler started successfully' if success else 'Failed to start scheduler'
            })
        except Exception as e:
            logger.error(f"Failed to start scheduler {scheduler_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/<int:scheduler_id>/pause', methods=['POST'])
    def api_pause_scheduler(scheduler_id):
        """Pause a specific scheduler."""
        try:
            success = scheduler_manager.stop()
            return jsonify({
                'success': success,
                'message': 'Scheduler paused successfully' if success else 'Failed to pause scheduler'
            })
        except Exception as e:
            logger.error(f"Failed to pause scheduler {scheduler_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/scheduler/<int:scheduler_id>', methods=['DELETE'])
    def api_delete_scheduler(scheduler_id):
        """Delete a specific scheduler."""
        try:
            # Stop the scheduler first
            scheduler_manager.stop()
            
            # Clear the scheduler configuration
            scheduler_manager.scheduler_config = {
                'interval_minutes': 30,
                'search_query': None,
                'city': None
            }
            
            return jsonify({
                'success': True,
                'message': 'Scheduler deleted successfully'
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
        """Export data to Excel and open file."""
        try:
            # Create Excel export
            filepath = excel_manager.export_all_products_to_excel()
            
            if not filepath:
                return jsonify({
                    'success': False,
                    'error': 'No data available to export'
                })
            
            # Open the Excel file
            opened_successfully = excel_manager.open_excel_file(filepath)
            
            if opened_successfully:
                return jsonify({
                    'success': True,
                    'message': 'Excel file created and opened successfully!',
                    'filepath': filepath
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Excel file created successfully, but failed to open automatically',
                    'filepath': filepath
                })
                
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/excel/backup', methods=['POST'])
    def api_excel_backup():
        """Create Excel backup of recent data."""
        try:
            data = request.get_json() or {}
            hours = int(data.get('hours', 2))
            
            # Create backup
            filepath = excel_manager.create_backup_before_cleanup(hours)
            
            if not filepath:
                return jsonify({
                    'success': False,
                    'message': f'No data found in the last {hours} hours to backup'
                })
            
            # Open the Excel file
            opened_successfully = excel_manager.open_excel_file(filepath)
            
            if opened_successfully:
                return jsonify({
                    'success': True,
                    'message': f'Backup created for last {hours} hours and opened successfully!',
                    'filepath': filepath
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'Backup created for last {hours} hours, but failed to open automatically',
                    'filepath': filepath
                })
                
        except Exception as e:
            logger.error(f"Failed to create Excel backup: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
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
