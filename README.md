# Facebook Marketplace Automation

A comprehensive Python-based automation tool to monitor competitor activity on Facebook Marketplace. The system tracks product listings, detects price changes, and provides a web dashboard for data visualization and management.

## Features

### Core Functionality
- **Automated Login & Navigation**: Secure login to Facebook Marketplace via browser automation
- **iPhone 16 Focused Monitoring**: Specifically targets iPhone 16 listings in Stockholm marketplace
- **Competitor Listing Scraper**: Extract product details (title, price, seller info, etc.)
- **Price Change Tracking**: Detect and log changes in product prices
- **Data Retention**: Configurable 48-hour data retention policy
- **Scheduled Monitoring**: Automated scraping every 15 minutes
- **SQLite Database**: Local data storage with optimized schema

### Web Dashboard
- **Real-time Statistics**: Total listings, new entries, price changes
- **Interactive Charts**: Price distribution and category analysis (Plotly)
- **Data Tables**: Recent listings and price change history
- **Scheduler Control**: Start/stop automation from the web interface
- **Responsive Design**: Bootstrap-based UI with mobile support

### Modular Architecture
- **Configuration Management**: Environment-based settings
- **Database Layer**: SQLite with automatic schema management
- **Scraping Engine**: Selenium-based Facebook scraper
- **Scheduling System**: Background automation with job management
- **Web API**: RESTful endpoints for dashboard integration

## Project Structure

```
fbMarketplace/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
├── README.md              # This file
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── core/
│   ├── __init__.py
│   ├── database.py        # Database operations
│   ├── scraper.py         # Facebook Marketplace scraper
│   └── scheduler.py       # Background job scheduler
├── web/
│   ├── __init__.py
│   ├── app.py            # Flask web application
│   ├── templates/
│   │   └── dashboard.html # Dashboard HTML template
│   └── static/
│       └── css/
│           └── dashboard.css # Custom styles
├── data/                  # Database storage (auto-created)
└── logs/                  # Log files (auto-created)
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Chrome browser installed
- Valid Facebook account

### Setup

1. **Clone/Download the project**
   ```bash
   cd D:\temp\development\python\fbMarketplace
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env with your settings
   notepad .env
   ```

4. **Environment Variables**
   ```env
   # Required
   FACEBOOK_EMAIL=your_email@example.com
   FACEBOOK_PASSWORD=your_password
   
   # Optional (defaults provided)
   SEARCH_LOCATION=New York, NY
   SEARCH_KEYWORDS=electronics,furniture,cars
   SCRAPE_INTERVAL_MINUTES=15
   DATA_RETENTION_HOURS=48
   FLASK_PORT=5000
   ```

5. **Initialize database**
   ```bash
   python main.py init-db
   ```

## Usage

### Command Line Interface

```bash
# Run scraper once
python main.py scrape

# Start automated scheduler
python main.py schedule

# Launch web dashboard
python main.py dashboard

# Show system status
python main.py status

# Clean up old data
python main.py cleanup

# Verbose logging
python main.py scrape --verbose
```

### Web Dashboard

1. **Start the dashboard**
   ```bash
   python main.py dashboard
   ```

2. **Access the interface**
   ```
   http://localhost:5000
   ```

3. **Dashboard Features**
   - **Statistics Cards**: Overview of total listings, new entries, price changes
   - **Scheduler Control**: Start/stop automated monitoring
   - **Charts**: Price distribution histogram and category pie chart
   - **Data Tables**: Recent listings and price change history
   - **Manual Scraping**: Run scraper immediately from the interface

## Database Schema

### Tables
- **listings**: Product information and metadata
- **price_history**: Price change tracking
- **scraping_sessions**: Session logs and statistics

### Key Fields
- `listing_id`: Unique identifier from Facebook
- `title`: Product name/description
- `price`: Current price
- `seller_name`: Seller information
- `seller_location`: Geographic data
- `created_at`/`updated_at`: Timestamps
- `change_amount`: Price difference
- `change_percentage`: Percentage change

## Configuration Options

### Search Parameters
- `SEARCH_LOCATION`: Target geographic area
- `SEARCH_KEYWORDS`: Comma-separated product categories
- `PRICE_RANGE_MIN/MAX`: Price filtering

### Automation Settings
- `SCRAPE_INTERVAL_MINUTES`: How often to run scraper
- `DATA_RETENTION_HOURS`: How long to keep data

### Chrome Options
- Configurable browser settings for different environments
- User agent spoofing for better compatibility

## API Endpoints

### Dashboard API
- `GET /api/stats` - System statistics
- `GET /api/listings` - Recent listings with filtering
- `GET /api/price-changes` - Price change history
- `GET /api/price-chart` - Price distribution chart data
- `GET /api/category-chart` - Category distribution chart data

### Control API
- `POST /api/scheduler/start` - Start scheduler
- `POST /api/scheduler/stop` - Stop scheduler
- `POST /api/scrape/run` - Run scraper immediately

## Monitoring & Logging

### Log Files
- Application logs stored in `logs/marketplace_automation.log`
- Configurable log levels (INFO, DEBUG, ERROR)
- Automatic log rotation

### Error Handling
- Graceful handling of Facebook changes
- Session management and recovery
- Database transaction safety

## Security Considerations

### Credentials
- Environment-based credential storage
- No hardcoded passwords in source code
- Secure browser session management

### Rate Limiting
- Configurable scraping intervals
- Built-in delays between requests
- Respect for platform terms of service

## Scalability & Future Enhancements

### Current Architecture Supports
- Multiple search keywords
- Configurable data retention
- Modular component design
- RESTful API for integrations

### Potential Extensions
- Multi-platform support (beyond Facebook)
- Advanced analytics and reporting
- Email notifications for price changes
- Export functionality (CSV, JSON)
- Historical trend analysis
- Machine learning price predictions

## Troubleshooting

### Common Issues

1. **Facebook Login Issues**
   - Ensure credentials are correct in `.env`
   - Handle 2FA if enabled on account
   - Check for Facebook security restrictions

2. **Scraping Failures**
   - Facebook may have updated their HTML structure
   - Chrome driver may need updating
   - Network connectivity issues

3. **Database Errors**
   - Ensure write permissions in project directory
   - Check disk space availability
   - Validate SQLite installation

### Debug Mode
```bash
# Enable verbose logging
python main.py scrape --verbose

# Check system status
python main.py status
```

## License & Disclaimer

This tool is for educational and research purposes. Users are responsible for:
- Complying with Facebook's Terms of Service
- Respecting rate limits and platform policies
- Ensuring legal use in their jurisdiction
- Data privacy and security practices

## Support

For issues and questions:
1. Check the logs for error details
2. Verify configuration settings
3. Ensure all dependencies are installed
4. Review Facebook's current terms and policies
