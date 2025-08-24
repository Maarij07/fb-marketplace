# Deep Scraping Integration Documentation

## Overview

This document describes the comprehensive integration of deep scraping functionality into the Facebook Marketplace automation system. The deep scraping feature provides advanced competitive intelligence capabilities by extracting detailed product, seller, and marketplace metadata.

## Architecture

### Core Components

1. **FacebookMarketplaceScraper** (`core/scraper.py`)
   - Main scraper class with integrated deep scraping methods
   - Handles both standard and deep scraping modes
   - Includes comprehensive data extraction, seller analysis, and product details

2. **SchedulerManager** (`core/scheduler.py`)
   - Updated to support deep scraping scheduling
   - New methods for deep scraping job management
   - Configuration management for deep scraping parameters

3. **PersistentBrowserSession** (`core/persistent_session.py`)
   - Enhanced with deep scraping support
   - Maintains browser sessions for efficient deep scraping
   - Automatic mode detection based on settings

## Features

### Deep Scraping Capabilities

- **Comprehensive Product Details**
  - Model identification (iPhone variants, storage, color)
  - Condition assessment (new, like new, used, etc.)
  - Battery health extraction
  - Complete image collection
  - Full product descriptions

- **Advanced Seller Analysis**
  - Seller profile information extraction
  - Response time and rate analysis
  - Member since date detection
  - Verification badge identification
  - Listing count statistics

- **Marketplace Metadata**
  - Facebook listing ID extraction
  - View count tracking
  - Sold status monitoring
  - Shipping availability detection
  - Posting time analysis
  - Urgency indicator detection

### Configuration Settings

```env
# Deep Scraping Configuration
ENABLE_DEEP_SCRAPING=true
DEEP_SCRAPE_MAX_PRODUCTS=10
DEEP_SCRAPE_PAGE_TIMEOUT=15
DEEP_SCRAPE_ELEMENT_TIMEOUT=8
DEEP_SCRAPE_DELAY_MIN=3
DEEP_SCRAPE_DELAY_MAX=7
```

## Usage Examples

### 1. Scheduler-Based Deep Scraping

```python
from core.settings import Settings
from core.scheduler import SchedulerManager

# Initialize with deep scraping enabled
settings = Settings()
settings.set('ENABLE_DEEP_SCRAPING', 'true')
settings.set('DEEP_SCRAPE_MAX_PRODUCTS', '15')

scheduler = SchedulerManager(settings)

# Manual deep scraping
result = scheduler.run_deep_scraping_manual(
    search_query="iphone 16 pro",
    max_products=10
)

print(f"Found {result['listings_found']} comprehensive listings")
```

### 2. Persistent Session Deep Scraping

```python
from core.persistent_session import get_persistent_session

session = get_persistent_session(settings)

# Force deep scraping regardless of settings
results = session.run_deep_scrape(
    search_query="samsung galaxy s24",
    max_products=8
)

for product in results:
    print(f"Product: {product['basic_info']['title']}")
    print(f"Seller: {product['seller_details'].get('seller_name', 'Unknown')}")
    print(f"Condition: {product['product_comprehensive'].get('condition', 'Unknown')}")
```

### 3. Configuration Management

```python
# Get current deep scraping configuration
config = scheduler.get_deep_scraping_config()

# Update configuration
new_config = {
    'enabled': True,
    'max_products': 20,
    'page_load_timeout': 25
}
scheduler.update_deep_scraping_config(new_config)
```

## Data Structure

### Deep Scraped Product Format

```json
{
  "basic_info": {
    "title": "iPhone 16 Pro 256GB",
    "url": "https://facebook.com/marketplace/item/123456789",
    "extraction_timestamp": "2024-01-20T10:30:00",
    "price": {
      "amount": "15000",
      "currency": "SEK",
      "raw_price_text": "15 000 kr"
    },
    "location": {
      "city": "Stockholm",
      "distance": "5km",
      "raw_location": "Stockholm 5 km"
    }
  },
  "seller_details": {
    "button_found": true,
    "seller_name": "John Doe",
    "profile_url": "https://facebook.com/profile/johndoe",
    "ratings": ["4.8 stars"],
    "response_info": "Responds in 30 minutes",
    "join_date": "Member since January 2020"
  },
  "product_comprehensive": {
    "model_name": "iPhone 16 Pro",
    "storage": "256 GB",
    "color": "Titanium",
    "condition": "like_new",
    "battery_health": "98%",
    "images": [
      {
        "url": "https://scontent.fbcdn.net/...",
        "alt_text": "iPhone front view",
        "type": "product_image"
      }
    ],
    "description": "Selling my iPhone 16 Pro in excellent condition..."
  },
  "marketplace_metadata": {
    "fb_listing_id": "123456789",
    "view_count": 47,
    "is_sold": false,
    "shipping_available": true,
    "timing": {
      "posted_time": "3 hours ago",
      "urgency_indicators": ["quick sale"]
    }
  }
}
```

## API Integration

### Scheduler Manager New Methods

- `_run_deep_scraping_job()` - Execute deep scraping for scheduled jobs
- `_run_custom_deep_scraping(search_query, notification_manager)` - Custom deep scraping
- `run_deep_scraping_manual(search_query, max_products)` - Manual deep scraping
- `get_deep_scraping_config()` - Get current configuration
- `update_deep_scraping_config(config)` - Update configuration

### Persistent Session New Methods

- `run_deep_scrape(search_query, max_products, notification_manager)` - Force deep scraping
- `get_scraping_capabilities()` - Get available scraping methods

## Performance Considerations

### Timing and Delays

- **Inter-product delay**: 3-7 seconds (configurable)
- **Click delay**: 1-3 seconds (randomized)
- **Page load timeout**: 15 seconds (configurable)
- **Element wait timeout**: 8 seconds (configurable)

### Resource Management

- **Memory usage**: ~200MB additional for deep scraping
- **Browser sessions**: Automatically managed persistent sessions
- **Output files**: Individual product reports + session summaries
- **JSON storage**: Converted to standard format for dashboard compatibility

## Error Handling

### Graceful Degradation

- Falls back to standard scraping if deep scraping fails
- Continues processing if individual product extraction fails
- Logs detailed error information for debugging
- Maintains session stability across multiple products

### Common Error Scenarios

1. **Facebook UI Changes**: Robust selector fallbacks
2. **Network Timeouts**: Configurable timeout handling
3. **Element Not Found**: Multiple selector strategies
4. **Session Expiry**: Automatic session refresh

## Output and Storage

### File Outputs

- `deep_scrape_output/deep_product_N_timestamp.json` - Individual product reports
- `deep_scrape_output/deep_scrape_session_timestamp.json` - Complete session data
- Standard JSON database integration for dashboard compatibility

### Notification System

Real-time notifications for:
- Deep scrape started/completed
- Product processing progress
- Error notifications
- Session status updates

## Testing

Run the integration tests:

```bash
python test_deep_scraping_integration.py
```

Test coverage includes:
- Configuration management
- Scheduler integration
- Persistent session integration
- Settings validation
- Error handling scenarios

## Future Enhancements

### Planned Features

1. **AI-Powered Analysis**
   - Automated price trend detection
   - Seller reliability scoring
   - Product condition assessment

2. **Advanced Filtering**
   - Condition-based filtering
   - Seller rating thresholds
   - Custom extraction rules

3. **Export Formats**
   - CSV export for analysis
   - Excel reports with charts
   - API webhooks for external systems

4. **Monitoring Dashboard**
   - Real-time scraping progress
   - Deep data visualization
   - Competitive analysis charts

## Support and Troubleshooting

### Common Issues

1. **Deep scraping not enabled**: Check `ENABLE_DEEP_SCRAPING` setting
2. **Slow performance**: Adjust delay settings in configuration
3. **Memory issues**: Reduce `DEEP_SCRAPE_MAX_PRODUCTS` value
4. **Facebook blocks**: Increase delays and randomization

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('core.scraper').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor deep scraping statistics:

```python
stats = scraper.deep_scrape_stats
print(f"Success rate: {stats['products_successful']}/{stats['products_attempted']}")
print(f"Seller details extracted: {stats['seller_details_extracted']}")
```

## Contributing

When contributing to deep scraping functionality:

1. Follow the existing pattern for selector fallbacks
2. Add comprehensive error handling
3. Include timing delays to avoid detection
4. Update tests for new features
5. Document new configuration options

---

*This integration provides a comprehensive competitive intelligence platform for Facebook Marketplace automation with advanced data extraction capabilities.*
