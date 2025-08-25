"""
Excel Manager for Facebook Marketplace Automation

Handles Excel export functionality and data backup before cleanup.
"""

import json
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import subprocess
import sys

logger = logging.getLogger(__name__)


class ExcelManager:
    """Manages Excel export and backup operations."""
    
    def __init__(self):
        """Initialize Excel Manager."""
        self.backup_dir = './data/excel_backups'
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup_before_cleanup(self, hours_to_backup: int = 2) -> str:
        """
        Create Excel backup of products that will be deleted during cleanup.
        
        Args:
            hours_to_backup: Number of hours of data to backup
            
        Returns:
            Path to the created Excel file
        """
        try:
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found to backup")
                return None
            
            # Filter products from last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours_to_backup)
            recent_products = []
            
            for product in products.get('products', []):
                try:
                    # Parse the added_at timestamp
                    added_at = datetime.fromisoformat(product.get('added_at', '').replace('Z', '+00:00'))
                    if added_at >= cutoff_time:
                        recent_products.append(product)
                except (ValueError, TypeError):
                    # If timestamp parsing fails, include the product to be safe
                    recent_products.append(product)
            
            if not recent_products:
                logger.info(f"No products found in the last {hours_to_backup} hours")
                return None
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_last_{hours_to_backup}h_{timestamp}.xlsx"
            filepath = os.path.join(self.backup_dir, filename)
            
            # Create Excel file
            self._create_excel_file(recent_products, filepath, f"Backup - Last {hours_to_backup} Hours")
            
            logger.info(f"Created backup Excel file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def export_all_products_to_excel(self) -> str:
        """
        Export all current products to Excel file.
        
        Returns:
            Path to the created Excel file
        """
        try:
            # Load current products
            products = self._load_products_json()
            if not products:
                logger.warning("No products found to export")
                return None
            
            all_products = products.get('products', [])
            if not all_products:
                logger.warning("No products in the data")
                return None
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"marketplace_data_export_{timestamp}.xlsx"
            filepath = os.path.join(self.backup_dir, filename)
            
            # Create Excel file
            self._create_excel_file(all_products, filepath, "All Products Export")
            
            logger.info(f"Created export Excel file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return None
    
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
    
    def _create_excel_file(self, products: List[Dict[str, Any]], filepath: str, sheet_name: str):
        """Create Excel file from products data."""
        try:
            # Prepare data for Excel
            excel_data = []
            
            for product in products:
                # Extract basic info
                row = {
                    'ID': product.get('id', 'N/A'),
                    'Title': product.get('title', 'N/A'),
                    'Price_Currency': product.get('price', {}).get('currency', 'N/A'),
                    'Price_Amount': product.get('price', {}).get('amount', 'N/A'),
                    'Price_Raw': product.get('price', {}).get('raw_value', 'N/A'),
                    'City': product.get('location', {}).get('city', 'N/A'),
                    'Distance': product.get('location', {}).get('distance', 'N/A'),
                    'Marketplace_URL': product.get('marketplace_url', 'N/A'),
                    'Seller_Name': product.get('seller_name', 'N/A'),
                    'Seller_Info': product.get('seller', {}).get('info', 'N/A'),
                    'Model': product.get('product_details', {}).get('model', 'N/A'),
                    'Storage': product.get('product_details', {}).get('storage', 'N/A'),
                    'Condition': product.get('product_details', {}).get('condition', 'N/A'),
                    'Color': product.get('product_details', {}).get('color', 'N/A'),
                    'Added_At': product.get('added_at', 'N/A'),
                    'Created_At': product.get('created_at', 'N/A'),
                    'Source': product.get('source', 'N/A'),
                    'Data_Quality': product.get('data_quality', 'N/A'),
                    'Extraction_Method': product.get('extraction_method', 'N/A')
                }
                
                # Add image URLs (first 3 images)
                images = product.get('images', [])
                for i in range(3):
                    if i < len(images):
                        # Handle both string URLs and dict image objects
                        image = images[i]
                        if isinstance(image, dict):
                            row[f'Image_URL_{i+1}'] = image.get('url', 'N/A')
                        elif isinstance(image, str):
                            row[f'Image_URL_{i+1}'] = image
                        else:
                            row[f'Image_URL_{i+1}'] = 'N/A'
                    else:
                        row[f'Image_URL_{i+1}'] = 'N/A'
                
                excel_data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(excel_data)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main products sheet
                df.to_excel(writer, sheet_name='Products', index=False)
                
                # Summary sheet
                summary_data = self._create_summary_sheet(products)
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Price analysis sheet
                price_analysis = self._create_price_analysis(products)
                price_df = pd.DataFrame(price_analysis)
                price_df.to_excel(writer, sheet_name='Price_Analysis', index=False)
            
            logger.info(f"Excel file created successfully: {filepath}")
            
        except Exception as e:
            logger.error(f"Error creating Excel file: {e}")
            raise
    
    def _create_summary_sheet(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create summary data for Excel."""
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
        
        summary = [
            {'Metric': 'Total Products', 'Value': total_products},
            {'Metric': 'Unique Cities', 'Value': len(cities)},
            {'Metric': 'Cities List', 'Value': ', '.join(cities)},
            {'Metric': 'Generation Date', 'Value': datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ]
        
        # Add price ranges
        for price_range, count in price_ranges.items():
            summary.append({'Metric': f'Products {price_range}', 'Value': count})
        
        # Add top models
        top_models = sorted(models.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (model, count) in enumerate(top_models, 1):
            summary.append({'Metric': f'Top Model #{i}', 'Value': f'{model} ({count})'})
        
        return summary
    
    def _create_price_analysis(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create price analysis data for Excel."""
        price_analysis = []
        
        for product in products:
            try:
                price = int(product.get('price', {}).get('amount', 0))
                if price > 0:
                    analysis_row = {
                        'Product_ID': product.get('id', 'N/A'),
                        'Title': product.get('title', 'N/A')[:50] + '...' if len(product.get('title', '')) > 50 else product.get('title', 'N/A'),
                        'Price': price,
                        'Currency': product.get('price', {}).get('currency', 'SEK'),
                        'City': product.get('location', {}).get('city', 'N/A'),
                        'Model': product.get('product_details', {}).get('model', 'N/A'),
                        'Added_Date': product.get('added_at', 'N/A')[:10] if product.get('added_at') else 'N/A'
                    }
                    price_analysis.append(analysis_row)
            except (ValueError, TypeError):
                pass
        
        # Sort by price descending
        price_analysis.sort(key=lambda x: x.get('Price', 0), reverse=True)
        
        return price_analysis
    
    def open_excel_file(self, filepath: str) -> bool:
        """
        Open Excel file in the default application.
        
        Args:
            filepath: Path to the Excel file
            
        Returns:
            True if successfully opened, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"Excel file not found: {filepath}")
                return False
            
            # Convert to absolute path
            abs_path = os.path.abspath(filepath)
            
            # Open file using system default application
            if sys.platform.startswith('win'):
                # Windows
                os.startfile(abs_path)
            elif sys.platform.startswith('darwin'):
                # macOS
                subprocess.run(['open', abs_path])
            else:
                # Linux
                subprocess.run(['xdg-open', abs_path])
            
            logger.info(f"Opened Excel file: {abs_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening Excel file: {e}")
            return False
    
    def get_backup_files(self) -> List[Dict[str, Any]]:
        """Get list of available backup files."""
        try:
            backup_files = []
            
            if not os.path.exists(self.backup_dir):
                return backup_files
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.xlsx'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(filepath)
                    
                    backup_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': file_stat.st_size,
                        'created': datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Sort by creation time, newest first
            backup_files.sort(key=lambda x: x['created'], reverse=True)
            
            return backup_files
            
        except Exception as e:
            logger.error(f"Error getting backup files: {e}")
            return []
