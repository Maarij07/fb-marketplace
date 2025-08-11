"""
Flask Web Application for Facebook Marketplace Automation

Provides web dashboard for monitoring scraping results, controlling scheduler,
and viewing analytics.
"""

import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

from core.json_manager import JSONDataManager
from core.scheduler import SchedulerManager


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


def create_app(settings):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'marketplace-automation-secret-key'
    
    # Initialize components
    json_manager = JSONDataManager()
    scheduler_manager = SchedulerManager(settings)
    
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
        """Get recent price changes."""
        try:
            limit = int(request.args.get('limit', 50))
            # Price changes not tracked in JSON version yet
            price_changes = []
            
            # Format data for frontend
            formatted_changes = []
            for change in price_changes:
                formatted_change = dict(change)
                # Convert prices from cents to dollars
                if formatted_change['old_price']:
                    formatted_change['old_price_display'] = f"${formatted_change['old_price'] / 100:.2f}"
                else:
                    formatted_change['old_price_display'] = "N/A"
                
                if formatted_change['new_price']:
                    formatted_change['new_price_display'] = f"${formatted_change['new_price'] / 100:.2f}"
                else:
                    formatted_change['new_price_display'] = "N/A"
                
                if formatted_change['change_amount']:
                    sign = "+" if formatted_change['change_amount'] > 0 else ""
                    formatted_change['change_display'] = f"{sign}${formatted_change['change_amount'] / 100:.2f}"
                else:
                    formatted_change['change_display'] = "N/A"
                
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
    
    @app.route('/api/scrape/run', methods=['POST'])
    def api_run_scrape():
        """Run scraper manually."""
        try:
            result = scheduler_manager.run_manual_scraping()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to run manual scraping: {e}")
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
