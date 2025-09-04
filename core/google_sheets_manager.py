"""
Google Sheets Manager for Facebook Marketplace Automation

Handles Google Sheets export functionality for marketplace data.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import gspread
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
import re

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    """Manages Google Sheets export and update operations."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets Manager.
        
        Args:
            credentials_path: Path to Google service account credentials JSON file
        """
        self.credentials_path = credentials_path or './config/google_sheets_credentials.json'
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client with authentication."""
        try:
            if os.path.exists(self.credentials_path):
                # Use service account credentials
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, 
                    scopes=scope
                )
                self.client = gspread.authorize(credentials)
                logger.info("Google Sheets client initialized with service account")
            else:
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            self.client = None
    
    def extract_sheet_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract Google Sheets ID from a shareable URL.
        
        Args:
            url: Google Sheets URL
            
        Returns:
            Sheet ID if found, None otherwise
        """
        try:
            # Pattern to match Google Sheets URLs
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"Error extracting sheet ID from URL: {e}")
            return None
    
    def export_all_products_to_sheets(self, sheet_url: str, worksheet_name: str = "Products") -> bool:
        """
        Export all current products to Google Sheets.
        
        Args:
            sheet_url: Google Sheets URL or ID
            worksheet_name: Name of the worksheet to create/update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found to export")
                return False
            
            all_products = products.get('products', [])
            if not all_products:
                logger.warning("No products in the data")
                return False
            
            # Extract sheet ID from URL if needed
            sheet_id = self.extract_sheet_id_from_url(sheet_url)
            if not sheet_id:
                # Assume it's already an ID
                sheet_id = sheet_url
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Create or get the worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                # Clear existing data
                worksheet.clear()
            except gspread.WorksheetNotFound:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=len(all_products) + 10, cols=30)
            
            # Prepare data for Google Sheets
            sheet_data = self._prepare_products_data(all_products)
            
            # Update the worksheet with data
            worksheet.update('A1', sheet_data)
            
            # Apply formatting
            self._apply_basic_formatting(worksheet, len(sheet_data))
            
            logger.info(f"Successfully exported {len(all_products)} products to Google Sheets")
            return True
            
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {e}")
            return False
    
    def append_products_to_sheets(self, sheet_url: str, worksheet_name: str = "Products") -> bool:
        """
        Append all current products to Google Sheets without removing existing data.
        Perfect for daily automated exports.
        
        Args:
            sheet_url: Google Sheets URL or ID
            worksheet_name: Name of the worksheet to append to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found to append")
                return False
            
            all_products = products.get('products', [])
            if not all_products:
                logger.warning("No products in the data")
                return False
            
            # Extract sheet ID from URL if needed
            sheet_id = self.extract_sheet_id_from_url(sheet_url)
            if not sheet_id:
                sheet_id = sheet_url
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Create or get the worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                # Create new worksheet with headers
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=30)
                # Add headers first
                headers = [
                    'ID', 'Title', 'Price_Amount', 'Price_Currency', 'Price_Raw',
                    'City', 'Distance', 'Marketplace_URL', 'Seller_Name', 'Seller_Info',
                    'Model', 'Storage', 'Condition', 'Color', 'Added_At', 'Created_At',
                    'Source', 'Data_Quality', 'Extraction_Method', 
                    'Image_URL_1', 'Image_URL_2', 'Image_URL_3', 'Export_Timestamp'
                ]
                worksheet.update('A1', [headers])
                self._apply_basic_formatting(worksheet, 1)
            
            # Find the next empty row
            try:
                # Get all values to find the last row with data
                all_values = worksheet.get_all_values()
                next_row = len([row for row in all_values if any(cell.strip() for cell in row)]) + 1
            except:
                # If there's an error, assume we start from row 2 (after headers)
                next_row = 2
            
            # Prepare data for Google Sheets (without headers since we're appending)
            sheet_data = self._prepare_products_data_for_append(all_products)
            
            if not sheet_data:
                logger.warning("No data prepared for append")
                return False
            
            # Ensure worksheet has enough rows
            required_rows = next_row + len(sheet_data)
            current_rows = worksheet.row_count
            if required_rows > current_rows:
                worksheet.add_rows(required_rows - current_rows + 10)  # Add some extra
            
            # Append the data starting from the next empty row
            range_name = f'A{next_row}'
            worksheet.update(range_name, sheet_data)
            
            logger.info(f"Successfully appended {len(all_products)} products to Google Sheets at row {next_row}")
            return True
            
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending to Google Sheets: {e}")
            return False
    
    def create_backup_in_sheets(self, sheet_url: str, hours_to_backup: int = 2, worksheet_name: str = "Backup") -> bool:
        """
        Create backup of recent products in Google Sheets.
        
        Args:
            sheet_url: Google Sheets URL or ID
            hours_to_backup: Number of hours of data to backup
            worksheet_name: Name of the backup worksheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found to backup")
                return False
            
            # Filter products from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours_to_backup)
            recent_products = []
            
            for product in products.get('products', []):
                try:
                    added_at = datetime.fromisoformat(product.get('added_at', '').replace('Z', '+00:00'))
                    if added_at >= cutoff_time:
                        recent_products.append(product)
                except (ValueError, TypeError):
                    recent_products.append(product)
            
            if not recent_products:
                logger.info(f"No products found in the last {hours_to_backup} hours")
                return False
            
            # Extract sheet ID from URL if needed
            sheet_id = self.extract_sheet_id_from_url(sheet_url)
            if not sheet_id:
                sheet_id = sheet_url
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Create backup worksheet with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_sheet_name = f"{worksheet_name}_{timestamp}"
            
            try:
                worksheet = spreadsheet.add_worksheet(
                    title=backup_sheet_name, 
                    rows=len(recent_products) + 10, 
                    cols=30
                )
            except Exception as e:
                logger.error(f"Failed to create backup worksheet: {e}")
                return False
            
            # Prepare and update data
            sheet_data = self._prepare_products_data(recent_products)
            worksheet.update('A1', sheet_data)
            
            # Apply formatting
            self._apply_basic_formatting(worksheet, len(sheet_data))
            
            logger.info(f"Created backup in Google Sheets: {backup_sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup in Google Sheets: {e}")
            return False
    
    def create_analytics_sheet(self, sheet_url: str, worksheet_name: str = "Analytics") -> bool:
        """
        Create analytics summary in Google Sheets.
        
        Args:
            sheet_url: Google Sheets URL or ID
            worksheet_name: Name of the analytics worksheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found for analytics")
                return False
            
            all_products = products.get('products', [])
            if not all_products:
                return False
            
            # Extract sheet ID
            sheet_id = self.extract_sheet_id_from_url(sheet_url)
            if not sheet_id:
                sheet_id = sheet_url
            
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Create or get analytics worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=50, cols=10)
            
            # Create analytics data
            analytics_data = self._create_analytics_data(all_products)
            
            # Update worksheet
            worksheet.update('A1', analytics_data)
            
            # Format analytics sheet
            self._format_analytics_sheet(worksheet, len(analytics_data))
            
            logger.info("Created analytics sheet in Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error creating analytics sheet: {e}")
            return False
    
    def _load_products_json(self) -> Dict[str, Any]:
        """Load products from JSON file."""
        try:
            json_path = './products.json'
            if not os.path.exists(json_path):
                logger.warning("products.json not found")
                return {}
                
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading products.json: {e}")
            return {}
    
    def _prepare_products_data(self, products: List[Dict[str, Any]]) -> List[List[str]]:
        """Prepare product data for Google Sheets format."""
        try:
            # Header row
            headers = [
                'ID', 'Title', 'Price_Amount', 'Price_Currency', 'Price_Raw',
                'City', 'Distance', 'Marketplace_URL', 'Seller_Name', 'Seller_Info',
                'Model', 'Storage', 'Condition', 'Color', 'Added_At', 'Created_At',
                'Source', 'Data_Quality', 'Extraction_Method', 
                'Image_URL_1', 'Image_URL_2', 'Image_URL_3'
            ]
            
            sheet_data = [headers]
            
            for product in products:
                row = [
                    str(product.get('id', 'N/A')),
                    str(product.get('title', 'N/A')),
                    str(product.get('price', {}).get('amount', 'N/A')),
                    str(product.get('price', {}).get('currency', 'N/A')),
                    str(product.get('price', {}).get('raw_value', 'N/A')),
                    str(product.get('location', {}).get('city', 'N/A')),
                    str(product.get('location', {}).get('distance', 'N/A')),
                    str(product.get('marketplace_url', 'N/A')),
                    str(product.get('seller_name', 'N/A')),
                    str(product.get('seller', {}).get('info', 'N/A')),
                    str(product.get('product_details', {}).get('model', 'N/A')),
                    str(product.get('product_details', {}).get('storage', 'N/A')),
                    str(product.get('product_details', {}).get('condition', 'N/A')),
                    str(product.get('product_details', {}).get('color', 'N/A')),
                    str(product.get('added_at', 'N/A')),
                    str(product.get('created_at', 'N/A')),
                    str(product.get('source', 'N/A')),
                    str(product.get('data_quality', 'N/A')),
                    str(product.get('extraction_method', 'N/A'))
                ]
                
                # Add image URLs (first 3)
                images = product.get('images', [])
                for i in range(3):
                    if i < len(images):
                        image = images[i]
                        if isinstance(image, dict):
                            row.append(str(image.get('url', 'N/A')))
                        elif isinstance(image, str):
                            row.append(str(image))
                        else:
                            row.append('N/A')
                    else:
                        row.append('N/A')
                
                sheet_data.append(row)
            
            return sheet_data
            
        except Exception as e:
            logger.error(f"Error preparing products data: {e}")
            return [['Error preparing data']]
    
    def _prepare_products_data_for_append(self, products: List[Dict[str, Any]]) -> List[List[str]]:
        """Prepare product data for appending to Google Sheets (no headers, with timestamp)."""
        try:
            sheet_data = []
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for product in products:
                row = [
                    str(product.get('id', 'N/A')),
                    str(product.get('title', 'N/A')),
                    str(product.get('price', {}).get('amount', 'N/A')),
                    str(product.get('price', {}).get('currency', 'N/A')),
                    str(product.get('price', {}).get('raw_value', 'N/A')),
                    str(product.get('location', {}).get('city', 'N/A')),
                    str(product.get('location', {}).get('distance', 'N/A')),
                    str(product.get('marketplace_url', 'N/A')),
                    str(product.get('seller_name', 'N/A')),
                    str(product.get('seller', {}).get('info', 'N/A')),
                    str(product.get('product_details', {}).get('model', 'N/A')),
                    str(product.get('product_details', {}).get('storage', 'N/A')),
                    str(product.get('product_details', {}).get('condition', 'N/A')),
                    str(product.get('product_details', {}).get('color', 'N/A')),
                    str(product.get('added_at', 'N/A')),
                    str(product.get('created_at', 'N/A')),
                    str(product.get('source', 'N/A')),
                    str(product.get('data_quality', 'N/A')),
                    str(product.get('extraction_method', 'N/A'))
                ]
                
                # Add image URLs (first 3)
                images = product.get('images', [])
                for i in range(3):
                    if i < len(images):
                        image = images[i]
                        if isinstance(image, dict):
                            row.append(str(image.get('url', 'N/A')))
                        elif isinstance(image, str):
                            row.append(str(image))
                        else:
                            row.append('N/A')
                    else:
                        row.append('N/A')
                
                # Add export timestamp
                row.append(current_timestamp)
                
                sheet_data.append(row)
            
            return sheet_data
            
        except Exception as e:
            logger.error(f"Error preparing products data for append: {e}")
            return []
    
    def _create_analytics_data(self, products: List[Dict[str, Any]]) -> List[List[str]]:
        """Create analytics summary data."""
        try:
            total_products = len(products)
            cities = set()
            price_ranges = {
                '0-5000 SEK': 0,
                '5000-10000 SEK': 0,
                '10000-15000 SEK': 0,
                '15000+ SEK': 0
            }
            models = {}
            
            for product in products:
                # Cities
                city = product.get('location', {}).get('city', 'Unknown')
                cities.add(city)
                
                # Price ranges
                try:
                    price = int(product.get('price', {}).get('amount', 0))
                    if price < 5000:
                        price_ranges['0-5000 SEK'] += 1
                    elif price < 10000:
                        price_ranges['5000-10000 SEK'] += 1
                    elif price < 15000:
                        price_ranges['10000-15000 SEK'] += 1
                    else:
                        price_ranges['15000+ SEK'] += 1
                except (ValueError, TypeError):
                    pass
                
                # Models
                model = product.get('product_details', {}).get('model', 'Unknown')
                models[model] = models.get(model, 0) + 1
            
            # Create analytics data
            analytics_data = [
                ['Metric', 'Value'],
                ['Total Products', str(total_products)],
                ['Unique Cities', str(len(cities))],
                ['Cities List', ', '.join(cities)],
                ['Generation Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ['', ''],  # Empty row
                ['Price Distribution', ''],
            ]
            
            # Add price ranges
            for price_range, count in price_ranges.items():
                analytics_data.append([f'Products {price_range}', str(count)])
            
            analytics_data.append(['', ''])  # Empty row
            analytics_data.append(['Top Models', ''])
            
            # Add top models
            top_models = sorted(models.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (model, count) in enumerate(top_models, 1):
                analytics_data.append([f'Top Model #{i}', f'{model} ({count})'])
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error creating analytics data: {e}")
            return [['Error creating analytics']]
    
    def _apply_basic_formatting(self, worksheet, data_rows: int):
        """Apply basic formatting to the worksheet."""
        try:
            # Format header row
            worksheet.format('A1:V1', {
                'backgroundColor': {
                    'red': 0.2,
                    'green': 0.6,
                    'blue': 0.9
                },
                'textFormat': {
                    'foregroundColor': {
                        'red': 1.0,
                        'green': 1.0,
                        'blue': 1.0
                    },
                    'bold': True
                }
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(worksheet.row_values(1)))
            
        except Exception as e:
            logger.error(f"Error applying formatting: {e}")
    
    def _format_analytics_sheet(self, worksheet, data_rows: int):
        """Apply formatting to analytics sheet."""
        try:
            # Format header
            worksheet.format('A1:B1', {
                'backgroundColor': {
                    'red': 0.9,
                    'green': 0.6,
                    'blue': 0.2
                },
                'textFormat': {
                    'bold': True
                }
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 2)
            
        except Exception as e:
            logger.error(f"Error formatting analytics sheet: {e}")
    
    def test_connection(self) -> bool:
        """Test Google Sheets API connection."""
        try:
            if not self.client:
                return False
            
            # Try to list spreadsheets (this requires Drive API access)
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False
    
    def get_sheet_info(self, sheet_url: str) -> Optional[Dict[str, Any]]:
        """Get information about a Google Sheets document."""
        try:
            if not self.client:
                return None
            
            sheet_id = self.extract_sheet_id_from_url(sheet_url)
            if not sheet_id:
                sheet_id = sheet_url
            
            spreadsheet = self.client.open_by_key(sheet_id)
            
            worksheets = [ws.title for ws in spreadsheet.worksheets()]
            
            return {
                'title': spreadsheet.title,
                'id': spreadsheet.id,
                'url': spreadsheet.url,
                'worksheets': worksheets,
                'worksheet_count': len(worksheets)
            }
            
        except Exception as e:
            logger.error(f"Error getting sheet info: {e}")
            return None
