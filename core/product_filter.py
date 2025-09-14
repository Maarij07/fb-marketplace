"""
Smart Product Filtering System for Facebook Marketplace Scraper

This module implements intelligent filtering to ensure that when searching for a specific phone model,
only exact matches are scraped and related variants (Plus, Pro, Series, etc.) are excluded.

Example: If searching for "iPhone 16", it should NOT scrape:
- iPhone 16 Plus
- iPhone 16 Pro
- iPhone 16 Pro Max
- iPhone 15 (older models)
- iPhone 17 (newer models if exist)
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import difflib


@dataclass
class ProductFilterRule:
    """Represents a filtering rule for product matching."""
    target_model: str
    exclude_variants: List[str]
    exclude_keywords: List[str]
    strict_match: bool = True


class SmartProductFilter:
    """
    Intelligent product filtering system to ensure exact model matching
    and exclude related but different variants.
    """
    
    def __init__(self):
        """Initialize the smart product filter."""
        self.logger = logging.getLogger(__name__)
        
        # Define comprehensive filtering rules for different phone brands
        self.phone_filter_rules = {
            # iPhone Rules
            'iphone': {
                'variants_to_exclude': [
                    'plus', 'pro', 'max', 'mini', 'se'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Samsung Rules  
            'samsung': {
                'variants_to_exclude': [
                    'plus', 'ultra', 'note', 'edge', 'active', 'fe', 'lite', 'neo'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Google Pixel Rules
            'pixel': {
                'variants_to_exclude': [
                    'xl', 'pro', 'a', 'lite'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # OnePlus Rules
            'oneplus': {
                'variants_to_exclude': [
                    't', 'pro', 'r', 'rt', 'ace'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Xiaomi/Redmi Rules
            'redmi': {
                'variants_to_exclude': [
                    'pro', 'plus', 'max', 'ultra', 'turbo', 'k', 's'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            'xiaomi': {
                'variants_to_exclude': [
                    'pro', 'plus', 'max', 'ultra', 'turbo', 't', 'lite', 'youth'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Huawei Rules
            'huawei': {
                'variants_to_exclude': [
                    'pro', 'plus', 'max', 'ultra', 'lite', 'youth', 'nova'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Oppo Rules
            'oppo': {
                'variants_to_exclude': [
                    'pro', 'plus', 'neo', 'lite', 'k', 'r', 'a'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Vivo Rules
            'vivo': {
                'variants_to_exclude': [
                    'pro', 'plus', 'max', 'neo', 'lite', 's', 't', 'y'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            },
            
            # Realme Rules
            'realme': {
                'variants_to_exclude': [
                    'pro', 'plus', 'max', 'ultra', 'neo', 'x', 'gt', 'c'
                ],
                'model_separators': [' ', '-', '_'],
                'strict_matching': True
            }
        }
        # COMPREHENSIVE BLACKLIST for phone accessories and covers
        self.accessories_blacklist = [
            # Phone Cases & Covers
            'case', 'cases', 'cover', 'covers', 'protection', 'protective',
            'shell', 'shells', 'sleeve', 'sleeves', 'pouch', 'pouches',
            'bumper', 'bumpers', 'holster', 'holsters', 'wallet', 'flip',
            'folio', 'leather', 'silicone', 'tpu', 'rubber', 'plastic',
            'hard case', 'soft case', 'clear case', 'transparent', 'shockproof',
            
            # Screen Protection
            'screen protector', 'screen guard', 'tempered glass', 'glass protector',
            'film', 'shield', 'privacy screen', '9h', 'anti-glare', 'matte',
            
            # Charging & Cables
            'charger', 'charging', 'cable', 'cables', 'adapter', 'adapters',
            'power bank', 'wireless charger', 'car charger', 'wall charger',
            'usb cable', 'lightning cable', 'type-c', 'usb-c', 'magsafe',
            'charging pad', 'charging station', 'charging dock',
            
            # Audio Accessories
            'headphones', 'earphones', 'airpods', 'earbuds', 'bluetooth',
            'speaker', 'speakers', 'audio', 'headset', 'wireless headphones',
            
            # Phone Stands & Mounts
            'stand', 'stands', 'holder', 'holders', 'mount', 'mounts',
            'car mount', 'desk stand', 'phone stand', 'tripod', 'ring holder',
            'pop socket', 'grip', 'kickstand',
            
            # Replacement Parts & Repair
            'battery', 'batteries', 'replacement', 'parts', 'repair',
            'service', 'fix', 'broken', 'cracked', 'damaged', 'spare parts',
            'lcd', 'display', 'screen replacement', 'back cover', 'housing',
            
            # Memory & Storage
            'memory card', 'sd card', 'micro sd', 'storage', 'flash drive',
            'sim card', 'sim tray', 'sim tool',
            
            # Other Accessories
            'lens', 'camera lens', 'ring light', 'selfie stick', 'stylus',
            'cleaning kit', 'wipe', 'cloth', 'kit', 'accessories pack',
            'bundle', 'combo', 'set', 'package deal', 'lot of',
            
            # Services & Software
            'unlock', 'unlocking', 'jailbreak', 'software', 'app', 'service',
            'contract', 'plan', 'carrier', 'network', 'sim free',
            
            # Box & Packaging (but NOT "new in box" or "sealed box")
            'empty box', 'box only', 'packaging', 'manual', 'instructions',
            
            # 🚫 MONITORS AND NON-PHONE ELECTRONICS (New Addition)
            'monitor', 'monitors', 'display', 'screen', 'lcd', 'led', 'oled',
            'curved monitor', 'gaming monitor', 'ultrawide', '4k monitor',
            'hd monitor', 'fhd', 'qhd', 'uhd', '24 inch', '27 inch', '32 inch',
            'tv', 'television', 'smart tv', 'projector', 'webcam', 'camera'
        ]
        
        # 🚫 MONITOR MODEL PATTERNS - Specific patterns to detect monitor models
        self.monitor_model_patterns = [
            r's\d+[a-z]\d+[a-z]+\d+[a-z]*',  # Samsung monitor pattern like S24C360EAE, S27AG50, etc.
            r'[a-z]\d+[a-z]\d+[a-z]?',       # Generic monitor patterns like C24F390, U28E590D
            r'\d+["\']?\s*(inch|in)\b',        # Size indicators like "24 inch", "27'", etc.
            r'\b(fhd|qhd|uhd|4k|1080p|1440p|2160p)\b',  # Resolution indicators
            r'\b(curved|gaming|ultrawide)\s*(monitor|display)\b',  # Monitor types
        ]
        
        # 🎨 COMPREHENSIVE COLOR DEFINITIONS - For color-specific filtering
        self.phone_colors = {
            # Basic Colors
            'black': ['black', 'jet black', 'matte black', 'space black'],
            'white': ['white', 'pearl white', 'ceramic white', 'cloud white'],
            'red': ['red', 'product red', 'cherry red', 'sunset red', 'coral red'],
            'blue': ['blue', 'pacific blue', 'sierra blue', 'sky blue', 'navy blue', 'midnight blue'],
            'green': ['green', 'alpine green', 'midnight green', 'pine green', 'forest green'],
            'purple': ['purple', 'deep purple', 'lavender', 'violet'],
            'pink': ['pink', 'rose pink', 'coral pink', 'blush pink'],
            'yellow': ['yellow', 'canary yellow', 'lemon yellow'],
            'orange': ['orange', 'sunset orange', 'coral orange'],
            
            # Metallic Colors
            'gold': ['gold', 'rose gold', 'champagne gold', 'bronze gold'],
            'silver': ['silver', 'platinum silver', 'mystic silver'],
            'gray': ['gray', 'grey', 'space gray', 'space grey', 'graphite', 'charcoal', 'slate'],
            'bronze': ['bronze', 'mystic bronze', 'copper bronze'],
            
            # Premium/Special Colors
            'titanium': ['titanium', 'natural titanium', 'blue titanium', 'white titanium', 'black titanium'],
            'phantom': ['phantom', 'phantom black', 'phantom silver', 'phantom white'],
            'midnight': ['midnight', 'midnight green', 'midnight blue'],
            'starlight': ['starlight', 'starlight gold'],
            'graphite': ['graphite', 'space gray'],
            
            # Samsung-specific colors
            'cream': ['cream', 'phantom cream'],
            'lavender': ['lavender', 'phantom lavender'],
            'mint': ['mint', 'mint green'],
            
            # Other brand colors
            'coral': ['coral', 'living coral'],
            'sage': ['sage', 'sage green'],
            'hazel': ['hazel', 'sorta sage']
        }
        
        # Flatten color variations for easy lookup
        self.all_color_variations = set()
        for color_family, variations in self.phone_colors.items():
            self.all_color_variations.update([v.lower() for v in variations])
        
        # WHITELIST: Allowed terms that should NOT be filtered out
        self.phone_whitelist = [
            # Valid phone conditions
            'new', 'used', 'refurbished', 'mint', 'excellent', 'good', 'fair',
            'sealed', 'unopened', 'new in box', 'mint condition', 'like new',
            
            # Valid phone colors (dynamically from color definitions)
            *self.all_color_variations,
            
            # Valid phone storage sizes
            '16gb', '32gb', '64gb', '128gb', '256gb', '512gb', '1tb', '2tb',
            'gb', 'tb', 'storage',
            
            # Valid phone networks
            'unlocked', 'factory unlocked', 'gsm', 'cdma', 'lte', '5g', '4g',
            
            # Valid descriptive terms
            'smartphone', 'mobile', 'phone', 'cellular', 'device'
        ]
        
        # Version/generation exclusion patterns (removed 'generation' since it's legitimate for iPads, etc.)
        self.version_exclusions = [
            'gen', 'version', 'ver', 'v2', 'v3', 'mk2', 'mk3', '2nd', '3rd'
        ]
        
        self.logger.info("Smart Product Filter initialized")
    
    def _extract_color_from_text(self, text: str) -> Optional[str]:
        """🎨 NEW: Extract color information from search query or product title."""
        text_lower = text.lower()
        
        # Look for colors in the text, prioritizing more specific colors first
        found_colors = []
        
        for color_family, variations in self.phone_colors.items():
            for variation in variations:
                if variation.lower() in text_lower:
                    # Use word boundaries to ensure we match whole color names
                    if re.search(r'\b' + re.escape(variation.lower()) + r'\b', text_lower):
                        found_colors.append((color_family, variation.lower()))
        
        if found_colors:
            # Return the most specific color found (longest variation name)
            most_specific = max(found_colors, key=lambda x: len(x[1]))
            return most_specific[0]  # Return the color family name
        
        return None
    
    def _get_color_variations(self, color_family: str) -> List[str]:
        """Get all variations of a color family."""
        return [v.lower() for v in self.phone_colors.get(color_family, [])]
    
    def _colors_match(self, target_color: str, product_color: str) -> bool:
        """🎨 Check if two colors match (considering color families and variations)."""
        if not target_color or not product_color:
            return True  # If no color specified, don't filter by color
        
        # If exact match
        if target_color == product_color:
            return True
        
        # Check if they belong to the same color family
        target_variations = self._get_color_variations(target_color)
        product_variations = self._get_color_variations(product_color)
        
        # Check if any variation of target color matches any variation of product color
        for target_var in target_variations:
            for product_var in product_variations:
                if target_var == product_var:
                    return True
        
        return False
    
    def should_include_product(self, product_title: str, target_search: str) -> Tuple[bool, str]:
        """
        Determine if a product should be included based on enhanced suffix-based filtering rules.
        
        Enhanced Logic:
        1. HIGHEST PRIORITY: Apply smart phone filtering for recognized brands (especially iPhones)
        2. Second Priority: If exact model filtering fails, use substring matching with extreme caution
        3. Always Apply: Global exclusions (accessories like case, cover, etc.)
        
        Args:
            product_title: The title of the product found
            target_search: The original search query (e.g., "iPhone 16", "iPad 9th generation")
            
        Returns:
            Tuple[bool, str]: (should_include, exclusion_reason)
        """
        try:
            # Check for common iPhone/branded model searches first for most accurate filtering
            if self._is_common_phone_model_search(target_search):
                # Skip substring matching and go straight to smart model matching for phones
                # This ensures "iPhone 13" doesn't match "iPhone 13 Pro"
                return self._apply_strict_model_matching(product_title, target_search)
            
            # For non-phone searches, check for exact substring match with caution
            if target_search.lower() in product_title.lower():
                # Still check for accessories even with exact match
                if self._contains_global_exclusions(product_title.lower()):
                    return False, "Contains accessory/non-phone keywords (despite exact match)"
                return True, f"Exact match: search query '{target_search}' found in product title"
            
            # Clean and normalize inputs for further processing
            title_clean = self._clean_title(product_title)
            search_clean = self._clean_title(target_search)
            
            # Check for global exclusions (accessories, etc.)
            if self._contains_global_exclusions(title_clean):
                return False, "Contains accessory/non-phone keywords"
            
            # Try to parse the target search to extract brand and model
            target_info = self._parse_phone_model(search_clean)
            
            # PRIORITY 2: Smart Phone Model Matching
            if target_info:
                # Parse the product title
                product_info = self._parse_phone_model(title_clean)
                if product_info:
                    # Check if it's the same brand
                    if target_info['brand'].lower() == product_info['brand'].lower():
                        # Apply smart model matching for recognized phone brands
                        return self._smart_model_matching(target_info, product_info, target_search, product_title)
                    else:
                        # Different phone brands - continue to fallback matching
                        pass
            
            # PRIORITY 3: Substring Matching Fallback
            # This handles cases like:
            # - "Apple iPad 9th generation 64GB Grey excellent condition"
            # - Non-phone products
            # - Products that couldn't be parsed by smart matching
            return self._substring_matching_fallback(title_clean, search_clean)
            
        except Exception as e:
            self.logger.error(f"Error in product filtering: {e}")
            # Final fallback to basic substring matching
            return self._substring_matching_fallback(product_title.lower(), target_search.lower())
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize product title."""
        if not title:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(title.strip().split())
        
        # Remove common marketplace noise
        noise_patterns = [
            r'\b(new|used|excellent|good|fair|condition|mint|sealed|unopened)\b',
            r'\b(with|without|includes|included)\b',
            r'\b(original|genuine|authentic|official)\b',
            r'\b(box|packaging|accessories)\b',
            r'\$\d+|€\d+|£\d+|\d+\s*kr|\d+\s*sek',  # Remove prices
            r'\b\d+gb|\b\d+tb|\b\d+mb',  # Remove storage when not relevant
        ]
        
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return ' '.join(cleaned.split())  # Remove extra spaces
    
    def _parse_phone_model(self, title: str) -> Optional[Dict[str, str]]:
        """
        Parse phone model information from title.
        
        Returns:
            Dict with 'brand', 'model', 'variants', 'full_model'
        """
        title_lower = title.lower()
        
        # Define comprehensive brand patterns for ALL major mobile devices
        brand_patterns = {
            # iPhone patterns - Fixed to handle compound variants like 'Pro Max' but not color names
            'iphone': r'iphone\s*(\d+)(?:\s+(pro\s*max|pro\s*plus|pro|plus\s*max|plus|max|mini|se))?',
            
            # 📱 IPAD PATTERNS - New Addition for iPad Support
            'ipad': r'(?:apple\s*)?ipad(?:\s+(air|pro|mini))?(?:\s*(\d+)(?:th|st|nd|rd)?(?:\s*generation|\s*gen)?)?',
            'ipad_numbered': r'ipad\s*(\d+)(?:th|st|nd|rd)?(?:\s*generation|\s*gen)?(?:\s+(air|pro|mini))?',
            
            # Samsung patterns - ENHANCED to detect and exclude monitor models
            'samsung': r'(?:samsung\s*(?:galaxy\s*)?s(\d+)(?![a-z]\d)|galaxy\s*s(\d+)(?![a-z]\d)|samsung\s*s(\d+)(?![a-z]\d))(\s*(ultra|plus|edge|fe|lite|neo))?|(?:samsung\s*)?galaxy\s*note\s*(\d+)(\s*(ultra|plus))?',
            
            # Google Pixel patterns
            'pixel': r'google\s*pixel\s*(\d+)(\s*(xl|pro|a))?|pixel\s*(\d+)(\s*(xl|pro|a))?',
            
            # OnePlus patterns
            'oneplus': r'oneplus\s*(\d+)(\s*(t|pro|r|rt|ace))?',
            
            # 🔥 REDMI PATTERNS - Fixed to handle compound variants like 'Pro Max'
            'redmi_note': r'redmi\s*note\s*(\d+)(\s*(pro\s*max|pro\s*plus|pro|plus\s*max|plus|max|ultra|turbo|s))?',
            'redmi': r'redmi\s*(\d+[a-z]?)(\s*(pro|plus|max|ultra|turbo|k|s))?',
            
            # 🔥 XIAOMI PATTERNS
            'xiaomi_mi': r'xiaomi\s*mi\s*(\d+)(\s*(pro|plus|max|ultra|turbo|t|lite|youth))?',
            'xiaomi': r'xiaomi\s*(\d+[a-z]?)(\s*(pro|plus|max|ultra|turbo|t|lite|youth))?',
            
            # 🔥 HUAWEI PATTERNS
            'huawei_p': r'huawei\s*p(\d+)(\s*(pro|plus|max|ultra|lite))?',
            'huawei_mate': r'huawei\s*mate\s*(\d+)(\s*(pro|plus|max|ultra|lite))?',
            'huawei_nova': r'huawei\s*nova\s*(\d+)(\s*(pro|plus|max|ultra|lite))?',
            
            # 🔥 OPPO PATTERNS
            'oppo_find': r'oppo\s*find\s*x?(\d+)(\s*(pro|plus|neo|lite))?',
            'oppo_reno': r'oppo\s*reno\s*(\d+)(\s*(pro|plus|neo|lite))?',
            'oppo_a': r'oppo\s*a(\d+)(\s*(pro|plus|neo|lite))?',
            
            # 🔥 VIVO PATTERNS
            'vivo_x': r'vivo\s*x(\d+)(\s*(pro|plus|max|neo|lite))?',
            'vivo_y': r'vivo\s*y(\d+)(\s*(pro|plus|max|neo|lite))?',
            'vivo_v': r'vivo\s*v(\d+)(\s*(pro|plus|max|neo|lite))?',
            
            # 🔥 REALME PATTERNS
            'realme': r'realme\s*(\d+)(\s*(pro|plus|max|ultra|neo|x|gt|c))?',
            
            # 🔥 HONOR PATTERNS
            'honor': r'honor\s*(\d+[a-z]?)(\s*(pro|plus|max|ultra|lite|x))?',
        }
        
        # Try to match each brand pattern
        for brand_key, pattern in brand_patterns.items():
            match = re.search(pattern, title_lower)
            if match:
                
                # iPhone parsing
                if brand_key == 'iphone':
                    return {
                        'brand': 'iPhone',
                        'model': match.group(1),
                        'variants': match.group(2) if match.group(2) else '',
                        'full_model': f"iPhone {match.group(1)}" + (f" {match.group(2)}" if match.group(2) else "")
                    }
                
                # 📱 iPad parsing - NEW: Handle iPad Air, Pro, Mini, and numbered generations
                elif brand_key.startswith('ipad'):
                    if brand_key == 'ipad':
                        # Pattern: "iPad Air 2" or "iPad Pro 12.9" or "iPad 9th generation"
                        variant = match.group(1)  # air, pro, mini
                        generation = match.group(2)  # number
                        
                        if variant and generation:
                            # "iPad Air 4", "iPad Pro 12"
                            model = f"{variant.title()} {generation}"
                        elif variant:
                            # "iPad Air" (no specific generation)
                            model = variant.title()
                        elif generation:
                            # "iPad 9th generation" (numbered iPad)
                            model = f"{generation}th generation"
                        else:
                            # Just "iPad"
                            model = "iPad"
                    
                    elif brand_key == 'ipad_numbered':
                        # Pattern: "iPad 9th generation" or "iPad 10th gen Air"
                        generation = match.group(1)  # number
                        variant = match.group(2)  # air, pro, mini
                        
                        if variant:
                            model = f"{generation}th generation {variant.title()}"
                        else:
                            model = f"{generation}th generation"
                    
                    return {
                        'brand': 'iPad',
                        'model': model,
                        'variants': '',  # iPads don't have sub-variants like phones
                        'full_model': f"iPad {model}" if model != 'iPad' else 'iPad'
                    }
                
                # Samsung parsing - Updated to handle new flexible regex pattern
                elif brand_key == 'samsung':
                    # Handle multiple capture groups from flexible pattern
                    # Groups: (s22_variant1, s22_variant2, s22_variant3, suffix, suffix_clean, note_model, note_suffix, note_suffix_clean)
                    base_model = match.group(1) or match.group(2) or match.group(3) or match.group(6)
                    variant = match.group(5) or match.group(8)  # Clean variant without leading space
                    
                    # Determine if it's Galaxy S or Galaxy Note
                    if match.group(6):  # Note model matched
                        model_type = "Galaxy Note"
                    else:
                        model_type = "Galaxy S"
                    
                    return {
                        'brand': 'Samsung',
                        'model': base_model,
                        'variants': variant if variant else '',
                        'full_model': f"{model_type} {base_model}" + (f" {variant}" if variant else "")
                    }
                
                # Google Pixel parsing
                elif brand_key == 'pixel':
                    base_model = match.group(1) if match.group(1) else match.group(4)
                    variant = match.group(2) if match.group(2) else match.group(5)
                    return {
                        'brand': 'Google Pixel',
                        'model': base_model,
                        'variants': variant if variant else '',
                        'full_model': f"Pixel {base_model}" + (f" {variant}" if variant else "")
                    }
                
                # OnePlus parsing
                elif brand_key == 'oneplus':
                    return {
                        'brand': 'OnePlus',
                        'model': match.group(1),
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"OnePlus {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
                
                # 🔥 REDMI NOTE parsing (e.g., "Redmi Note 10")
                elif brand_key == 'redmi_note':
                    return {
                        'brand': 'Redmi',
                        'model': f"Note {match.group(1)}",  # "Note 10"
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"Redmi Note {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
                
                # 🔥 REDMI parsing (e.g., "Redmi 9A")
                elif brand_key == 'redmi':
                    return {
                        'brand': 'Redmi',
                        'model': match.group(1),  # "9A"
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"Redmi {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
                
                # 🔥 XIAOMI parsing
                elif brand_key.startswith('xiaomi'):
                    model_prefix = "Mi " if 'mi' in brand_key else ""
                    return {
                        'brand': 'Xiaomi',
                        'model': f"{model_prefix}{match.group(1)}",
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"Xiaomi {model_prefix}{match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
                
                # 🔥 HUAWEI parsing
                elif brand_key.startswith('huawei'):
                    if 'p' in brand_key:
                        model_prefix = "P"
                    elif 'mate' in brand_key:
                        model_prefix = "Mate "
                    elif 'nova' in brand_key:
                        model_prefix = "Nova "
                    else:
                        model_prefix = ""
                    
                    return {
                        'brand': 'Huawei',
                        'model': f"{model_prefix}{match.group(1)}",
                        'variants': match.group(2) if len(match.groups()) > 1 and match.group(2) else '',
                        'full_model': f"Huawei {model_prefix}{match.group(1)}" + (f" {match.group(2) if len(match.groups()) > 1 and match.group(2) else ''}")
                    }
                
                # 🔥 OPPO parsing
                elif brand_key.startswith('oppo'):
                    if 'find' in brand_key:
                        model_prefix = "Find X" if 'x' in pattern else "Find "
                    elif 'reno' in brand_key:
                        model_prefix = "Reno "
                    elif 'a' in brand_key:
                        model_prefix = "A"
                    else:
                        model_prefix = ""
                    
                    return {
                        'brand': 'Oppo',
                        'model': f"{model_prefix}{match.group(1)}",
                        'variants': match.group(2) if len(match.groups()) > 1 and match.group(2) else '',
                        'full_model': f"Oppo {model_prefix}{match.group(1)}" + (f" {match.group(2) if len(match.groups()) > 1 and match.group(2) else ''}")
                    }
                
                # 🔥 VIVO parsing
                elif brand_key.startswith('vivo'):
                    model_prefix = brand_key.split('_')[1].upper() if '_' in brand_key else ""
                    return {
                        'brand': 'Vivo',
                        'model': f"{model_prefix}{match.group(1)}",
                        'variants': match.group(2) if len(match.groups()) > 1 and match.group(2) else '',
                        'full_model': f"Vivo {model_prefix}{match.group(1)}" + (f" {match.group(2) if len(match.groups()) > 1 and match.group(2) else ''}")
                    }
                
                # 🔥 REALME parsing
                elif brand_key == 'realme':
                    return {
                        'brand': 'Realme',
                        'model': match.group(1),
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"Realme {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
                
                # 🔥 HONOR parsing
                elif brand_key == 'honor':
                    return {
                        'brand': 'Honor',
                        'model': match.group(1),
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"Honor {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
                    }
        
        # If no specific pattern matched, try generic fallback
        return self._generic_phone_parsing(title_lower)
    
    def _generic_phone_parsing(self, title: str) -> Optional[Dict[str, str]]:
        """
        Generic fallback parsing for phone models that don't match specific patterns.
        
        This handles edge cases and unusual phone model naming conventions.
        """
        try:
            # Look for any brand + model pattern
            generic_patterns = [
                # Brand + number + optional variant
                r'(\w+)\s+(\d+[a-z]*)\s*(pro|plus|max|ultra|lite|mini|se|neo|turbo|k|s|t|r|x|gt|c|y|v|a)?',
                # Brand + word + number
                r'(\w+)\s+(note|mate|find|reno|nova|mi)\s+(\d+[a-z]*)\s*(pro|plus|max|ultra|lite)?'
            ]
            
            for pattern in generic_patterns:
                match = re.search(pattern, title.lower())
                if match:
                    brand = match.group(1).title()
                    
                    # Skip if it's clearly not a phone brand
                    non_phone_brands = ['new', 'used', 'mint', 'excellent', 'good', 'fair', 'with', 'without', 'original']
                    if brand.lower() in non_phone_brands:
                        continue
                    
                    if len(match.groups()) >= 4 and match.group(2):  # Brand + word + number pattern
                        model = f"{match.group(2).title()} {match.group(3)}"
                        variant = match.group(4) if len(match.groups()) >= 4 and match.group(4) else ''
                    else:  # Brand + number pattern
                        model = match.group(2)
                        variant = match.group(3) if len(match.groups()) >= 3 and match.group(3) else ''
                    
                    return {
                        'brand': brand,
                        'model': model,
                        'variants': variant if variant else '',
                        'full_model': f"{brand} {model}" + (f" {variant}" if variant else "")
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Generic parsing failed: {e}")
            return None
    
    def _is_common_phone_model_search(self, search_term: str) -> bool:
        """Check if search term is a common phone model search that requires strict filtering."""
        search_lower = search_term.lower()
        
        # Common phone brand patterns that need strict model matching
        phone_patterns = [
            r'iphone\s*\d+',     # iPhone 13, iPhone 16, etc.
            r'samsung\s*s\d+',   # Samsung S22, etc.
            r'galaxy\s*s\d+',    # Galaxy S22, etc.
            r'pixel\s*\d+',      # Pixel 6, etc.
            r'redmi\s*\d+',      # Redmi 9, etc.
            r'redmi\s*note\s*\d+' # Redmi Note 10, etc.
        ]
        
        for pattern in phone_patterns:
            if re.search(pattern, search_lower):
                return True
                
        return False
    
    def _apply_strict_model_matching(self, product_title: str, target_search: str) -> Tuple[bool, str]:
        """Apply strict model matching for phone models regardless of case."""
        # CRITICAL: Check for global exclusions FIRST before any model parsing
        # This ensures accessories are always excluded, even if they contain valid model names
        if self._contains_global_exclusions(product_title):
            return False, "Contains accessory/non-phone keywords"
        
        # Clean and normalize inputs for processing
        title_clean = self._clean_title(product_title)
        search_clean = self._clean_title(target_search)
        
        # Double-check exclusions on cleaned title as well
        if self._contains_global_exclusions(title_clean):
            return False, "Contains accessory/non-phone keywords (after cleaning)"
        
        # Parse the target search to extract brand and model
        target_info = self._parse_phone_model(search_clean)
        if not target_info:
            # Fallback to substring matching if we can't parse the model
            return self._substring_matching_fallback(title_clean, search_clean)
            
        # Parse the product title
        product_info = self._parse_phone_model(title_clean)
        if not product_info:
            # Skip this product if we can't parse its model information
            return False, "Unable to parse product model information"
            
        # Ensure same brand
        if target_info['brand'].lower() != product_info['brand'].lower():
            return False, f"Different brand: {product_info['brand']} vs {target_info['brand']}"
            
        # FINAL CHECK: Even if models match, triple-check for accessories 
        # (some accessories might have model names in them)
        if self._contains_global_exclusions(product_title.lower()):
            return False, "Contains accessory keywords (final check)"
            
        # Apply the enhanced smart model matching
        return self._smart_model_matching(target_info, product_info, target_search, product_title)
    
    def _smart_model_matching(self, target_info: Dict[str, str], product_info: Dict[str, str], 
                            target_search: str = "", product_title: str = "") -> Tuple[bool, str]:
        """
        Apply strict model matching rules based on search intent.
        
        ENHANCED STRICT MODEL MATCHING:
        - If you search "iPhone 16" → ONLY show iPhone 16 (EXCLUDE Pro, Plus, etc.)
        - If you search "iPhone 16 Pro" → ONLY show iPhone 16 Pro (EXCLUDE regular 16, Plus, Max)
        - If you search "iPhone 16 white" → ONLY show white iPhone 16 (EXCLUDE other colors)
        - If you search "Redmi Note 10" → ONLY show Redmi Note 10 (EXCLUDE Pro, other models)
        - Case insensitive matching ("iPhone" = "iphone" = "IPHONE")
        
        Args:
            target_info: Parsed target search info
            product_info: Parsed product info
            target_search: Original search query (for color extraction)
            product_title: Original product title (for color extraction)
            
        Returns:
            Tuple[bool, str]: (should_include, reason)
        """
        # 1. Check if base model numbers match (this is mandatory)
        if target_info['model'] != product_info['model']:
            return False, f"Different model number: {product_info['model']} vs {target_info['model']}"
        
        # 🎨 2. NEW: COLOR-SPECIFIC FILTERING - Check if colors match (if color specified)
        target_color = self._extract_color_from_text(target_search) if target_search else None
        product_color = self._extract_color_from_text(product_title) if product_title else None
        
        if target_color and product_color:
            if not self._colors_match(target_color, product_color):
                return False, f"Color mismatch: product is '{product_color}' but target wants '{target_color}'"
        elif target_color and not product_color:
            # User specified a color but product doesn't mention any color - exclude it
            return False, f"Target specifies color '{target_color}' but product color is not mentioned"
        # If target doesn't specify color but product does, that's fine - include it
        
        # 3. Parse variants from both target and product
        target_variants = set(target_info['variants'].lower().split()) if target_info['variants'] else set()
        product_variants = set(product_info['variants'].lower().split()) if product_info['variants'] else set()
        
        # 3. ENHANCED SUFFIX-BASED MATCHING LOGIC
        
        # Get all known suffixes/variants from all phone rules combined
        all_known_suffixes = set()
        for brand_rules in self.phone_filter_rules.values():
            all_known_suffixes.update(brand_rules.get('variants_to_exclude', []))
        
        # Add accessory suffixes
        accessory_suffixes = {'case', 'cover', 'screen', 'protector', 'charger', 'cable', 'adapter',
                             'battery', 'headphone', 'airpod', 'earpod', 'speaker', 'dock', 'stand'}
        all_known_suffixes.update(accessory_suffixes)
        
        # Check if product title contains any suffixes that aren't in the search term
        product_title_lower = product_info.get('full_model', '').lower()
        target_search_lower = target_info.get('full_model', '').lower()
        
        # STRICT FILTERING: Target has NO variants (e.g., "iPhone 16", "Redmi Note 10")
        # → Should ONLY include products with NO variants whatsoever
        # → Should EXCLUDE any products with variants (Pro, Plus, Max, etc.)
        if not target_variants:
            # Get phone-specific variant exclusions (more accurate than global list)
            brand_lower = target_info.get('brand', '').lower()
            phone_variants = set()
            
            # Get brand-specific variants to exclude
            for rule_brand, rules in self.phone_filter_rules.items():
                if rule_brand in brand_lower:
                    phone_variants.update(rules.get('variants_to_exclude', []))
                    break
            
            # If no brand-specific rules found, use common phone variants
            if not phone_variants:
                phone_variants = {'pro', 'plus', 'max', 'mini', 'ultra', 'lite', 'se'}
            
            # Check if product title contains phone variant words (as standalone words)
            product_title_words = set(word.strip() for word in product_title_lower.split())
            
            # Look for phone variant words that appear as standalone words
            for variant in phone_variants:
                if variant in product_title_words:
                    # Additional check: make sure it's not part of a color name or other context
                    # Skip single-letter variants that could be colors (like 's' in "Space Gray")
                    if len(variant) <= 1:
                        continue
                    return False, f"Target is base model but product has variant: '{variant}'"
            
            # If product has variants parsed by our regex, exclude it
            if product_variants:
                return False, f"Target is base model but product has parsed variants: {', '.join(product_variants)}"
            
            # Both target and product have no variants - PERFECT MATCH
            return True, "Exact base model match - no variants"
        
        # Case B: Target HAS variants (e.g., "iPhone 16 Pro", "Redmi Note 10 Pro")
        # → Should ONLY include products with EXACTLY the same variants
        # → Should EXCLUDE products with no variants or different variants
        else:
            if not product_variants:
                # Target has variants but product doesn't - EXCLUDE IT
                return False, f"Target has variants {', '.join(target_variants)} but product is base model"
            
            # Check for exact variant match
            if target_variants == product_variants:
                # Even with matching variants, check if product has any additional suffixes
                for suffix in all_known_suffixes:
                    # Only check suffixes that aren't part of the target variants
                    if suffix not in ' '.join(target_variants).lower():
                        if suffix in product_title_lower and suffix not in target_search_lower:
                            return False, f"Product has additional suffix: '{suffix}'"
                
                # Exact variant match without extra suffixes - PERFECT MATCH
                return True, f"Exact variant match: {', '.join(target_variants)}"
            else:
                # Different variants - EXCLUDE IT
                return False, f"Variant mismatch: product has {', '.join(product_variants)} but target wants {', '.join(target_variants)}"
        
        # This should never be reached, but just in case
        return False, "Unknown matching error"
    
    def _get_brand_rules(self, brand: str) -> Optional[Dict]:
        """Get filtering rules for a specific brand."""
        brand_lower = brand.lower()
        for rule_brand, rules in self.phone_filter_rules.items():
            if rule_brand in brand_lower:
                return rules
        return None
    
    def _contains_global_exclusions(self, title: str) -> bool:
        """Check if title contains globally excluded terms (accessories, etc.)."""
        title_lower = title.lower()
        
        # STEP 1: Check whitelist first - if title contains whitelist terms, be more lenient
        whitelist_found = []
        for whitelist_term in self.phone_whitelist:
            if whitelist_term in title_lower:
                whitelist_found.append(whitelist_term)
        
        # STEP 2: Check for monitor patterns (NEW - Prevents Samsung monitors from being matched)
        if self._is_monitor_product(title_lower):
            return True  # Exclude monitors
        
        # STEP 2.1: Check for comprehensive accessories blacklist
        blacklisted_terms = []
        for accessory_term in self.accessories_blacklist:
            # Use word boundaries for multi-word terms, simple substring for single words
            if ' ' in accessory_term:
                # Multi-word terms: use exact phrase matching
                if accessory_term in title_lower:
                    blacklisted_terms.append(accessory_term)
            else:
                # Single words: use word boundary for precision (but not too strict)
                if re.search(r'\b' + re.escape(accessory_term) + r'\b', title_lower):
                    blacklisted_terms.append(accessory_term)
        
        # STEP 2.5: Additional check for common accessory patterns that might be missed
        accessory_patterns = [
            r'\bcase\b',                    # iPhone 15 Case
            r'\bscreen\s+protector\b',      # Screen Protector
            r'\btempered\s+glass\b',        # Tempered Glass
            r'\bwireless\s+charger\b',     # Wireless Charger
            r'\bcar\s+charger\b',          # Car Charger
            r'\bmemory\s+card\b',          # Memory Card
            r'\bphone\s+holder\b',         # Phone Holder
        ]
        
        for pattern in accessory_patterns:
            if re.search(pattern, title_lower):
                match = re.search(pattern, title_lower)
                blacklisted_terms.append(match.group().strip())
        
        # STEP 3: Smart decision based on whitelist vs blacklist
        if blacklisted_terms:
            # CRITICAL: Always exclude obvious accessories, regardless of whitelist
            obvious_accessories = ['case', 'cases', 'cover', 'covers', 'screen protector', 'screen guard', 
                                 'tempered glass', 'charger', 'charging', 'cable', 'cables', 'adapter', 
                                 'headphones', 'airpods', 'speaker', 'stand', 'holder', 'mount', 'battery', 
                                 'replacement', 'repair', 'service', 'kit', 'bundle']
            
            # Check if any blacklisted terms are obvious accessories
            has_obvious_accessories = any(accessory in blacklisted_terms for accessory in obvious_accessories)
            
            if has_obvious_accessories:
                self.logger.debug(f"ALWAYS EXCLUDING - Contains obvious accessories: '{title[:50]}...', terms: {blacklisted_terms}")
                return True
            
            # For non-obvious blacklisted terms, check whitelist override
            if whitelist_found:
                # If we have significant whitelist presence, be more lenient for ambiguous terms
                strong_phone_indicators = ['iphone', 'samsung', 'galaxy', 'pixel', 'smartphone', 'mobile phone']
                has_strong_phone_indicators = any(indicator in title_lower for indicator in strong_phone_indicators)
                
                # Special handling for potentially valid combinations
                # Example: "iPhone 15 256gb unlocked" should NOT be excluded even if "unlocked" might be suspicious
                if has_strong_phone_indicators and len(whitelist_found) >= 2:
                    # Log the decision for debugging
                    self.logger.debug(f"Allowing title with ambiguous blacklisted terms due to strong phone indicators: '{title[:50]}...', blacklist: {blacklisted_terms}, whitelist: {whitelist_found}")
                    return False
                else:
                    self.logger.debug(f"Excluding title due to blacklisted terms: '{title[:50]}...', terms: {blacklisted_terms}")
                    return True
            else:
                # No whitelist terms found, definitely exclude
                self.logger.debug(f"Excluding title - blacklisted terms without phone indicators: '{title[:50]}...', terms: {blacklisted_terms}")
                return True
        
        # STEP 4: Check for version-specific exclusions (kept from original)
        for exclusion in self.version_exclusions:
            if exclusion in title_lower:
                return True
        
        return False
    
    def _is_monitor_product(self, title_lower: str) -> bool:
        """🚫 NEW: Check if product title indicates it's a monitor (not a phone)."""
        try:
            # Check for monitor model patterns (like Samsung S24C360EAE)
            for pattern in self.monitor_model_patterns:
                if re.search(pattern, title_lower):
                    self.logger.debug(f"MONITOR DETECTED: Pattern '{pattern}' matched in title: '{title_lower[:50]}...'")
                    return True
            
            # Check for explicit monitor keywords
            monitor_keywords = ['monitor', 'display', 'curved', 'gaming monitor', 'ultrawide', 
                              '24 inch', '27 inch', '32 inch', 'fhd', 'qhd', '4k monitor']
            
            for keyword in monitor_keywords:
                if keyword in title_lower:
                    self.logger.debug(f"MONITOR DETECTED: Keyword '{keyword}' found in title: '{title_lower[:50]}...'")
                    return True
            
            # Special case: Samsung model patterns that are monitors
            # Samsung monitors often follow the pattern: S + number + letters + numbers (e.g., S24C360EAE)
            samsung_monitor_pattern = r'samsung.*s\d+[a-z]\d+'
            if re.search(samsung_monitor_pattern, title_lower):
                self.logger.debug(f"SAMSUNG MONITOR DETECTED: Pattern '{samsung_monitor_pattern}' in title: '{title_lower[:50]}...'")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in monitor detection: {e}")
            return False
    
    def _substring_matching_fallback(self, title: str, target: str) -> Tuple[bool, str]:
        """
        Substring matching fallback with STRICT mode for deep/exact searches.
        
        LOGIC:
        - For long, detailed searches (7+ words): Use EXACT substring matching only
        - For medium searches (4-6 words): Use flexible word matching (80% threshold)
        - For short searches (1-3 words): Use very flexible matching
        
        This ensures that:
        - "Apple iPad 9th generation 64GB Grey excellent condition" requires EXACT match
        - "Cabramatta" type products are excluded from exact searches
        - Short searches remain flexible
        
        Args:
            title: Cleaned product title
            target: Cleaned target search query
            
        Returns:
            Tuple[bool, str]: (should_include, reason)
        """
        title_lower = title.lower()
        target_lower = target.lower()
        
        # METHOD 1: Always try exact substring match first
        if target_lower in title_lower:
            return True, f"Exact substring match: '{target}' found in title"
        
        # Count meaningful words in target to determine matching strategy
        # Remove common noise words first
        basic_noise = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'as', 'by'}
        target_word_count = len([w for w in target_lower.split() if w not in basic_noise])
        
        # STRICT MODE: For detailed searches (7+ meaningful words)
        # These are likely exact product searches and should match very precisely
        if target_word_count >= 7:
            # For very detailed searches, only allow exact substring matches
            # This prevents "Cabramatta" type products from matching detailed queries
            return False, f"Detailed search requires exact match - no substring match found (query has {target_word_count} words)"
        
        # FLEXIBLE MODE: For shorter searches, use enhanced matching
        # METHOD 2: Enhanced key-term matching for shorter searches
        target_normalized = self._normalize_for_matching(target_lower)
        title_normalized = self._normalize_for_matching(title_lower)
        
        target_words = set(target_normalized.split())
        title_words = set(title_normalized.split())
        
        # Enhanced noise word filtering for better matching
        noise_words = {
            # Condition words
            'new', 'used', 'excellent', 'good', 'fair', 'condition', 'mint', 'sealed', 
            'unopened', 'refurbished', 'barely', 'hardly', 'lightly',
            
            # Inclusion words
            'with', 'without', 'includes', 'included', 'comes', 'complete',
            
            # Quality words
            'original', 'genuine', 'authentic', 'official', 'brand', 'perfect',
            
            # Packaging words
            'box', 'packaging', 'accessories', 'manual', 'charger', 'cable',
            
            # Location/pickup words
            'pickup', 'delivery', 'collection', 'meet', 'location', 'area', 'cabramatta',
            
            # Generic words
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'as', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could',
            
            # Sale-related words
            'sale', 'sell', 'selling', 'price', 'cheap', 'bargain', 'deal', 'offer', 'obo',
            
            # Connectivity words
            'wifi', 'only', 'cellular', '4g', '5g'
        }
        
        # Remove noise words
        target_words = target_words - noise_words
        title_words = title_words - noise_words
        
        if not target_words:  # If no meaningful words left in target
            return False, "No meaningful words in search query after noise filtering"
        
        # METHOD 3: Core product identifier matching (for medium searches)
        if 4 <= target_word_count <= 6:
            target_core = self._extract_core_identifiers(target_normalized)
            title_core = self._extract_core_identifiers(title_normalized)
            
            core_matches = 0
            total_core = len(target_core) if target_core else 0
            
            if target_core and title_core:
                for key, target_value in target_core.items():
                    if key in title_core:
                        title_value = title_core[key]
                        if self._flexible_value_match(target_value, title_value, key):
                            core_matches += 1
            
            # Require higher core match ratio for medium searches
            if total_core > 0:
                core_ratio = core_matches / total_core
                if core_ratio >= 0.8:  # 80% of core identifiers must match
                    return True, f"Core identifier match: {core_matches}/{total_core} identifiers matched ({core_ratio:.1%})"
        
        # METHOD 4: Word-based matching with strict thresholds
        matching_words = target_words.intersection(title_words)
        match_ratio = len(matching_words) / len(target_words)
        
        # Stricter thresholds to prevent unwanted matches
        if len(target_words) <= 3:
            # Short queries: moderate flexibility (70%)
            threshold = 0.7
        elif len(target_words) <= 6:
            # Medium queries: high precision required (85%)
            threshold = 0.85
        else:
            # This shouldn't happen as we already handled 7+ words above
            threshold = 1.0  # Require perfect match
        
        if match_ratio >= threshold:
            return True, f"Word-based match: {len(matching_words)}/{len(target_words)} words matched ({match_ratio:.1%})"
        
        # METHOD 5: Fuzzy string similarity (only for very short queries)
        if len(target_words) <= 3:
            similarity = difflib.SequenceMatcher(None, title_lower, target_lower).ratio()
            
            if similarity >= 0.7:  # Higher threshold for similarity
                return True, f"Fuzzy similarity match: {similarity:.2f}"
            else:
                return False, f"No sufficient match found (word ratio: {match_ratio:.1%}, similarity: {similarity:.2f})"
        else:
            return False, f"No sufficient match found (word ratio: {match_ratio:.1%}, required: {threshold:.1%})"
    
    def _normalize_for_matching(self, text: str) -> str:
        """
        Normalize text for better matching by standardizing variations.
        
        Example:
        - "64GB" and "64g" both become "64gb"
        - "iPad" and "Ipad" both become "ipad"
        - "9th generation" and "9th-gen" both become "9th generation"
        """
        normalized = text.lower()
        
        # Storage normalization: 64g -> 64gb, 1t -> 1tb
        normalized = re.sub(r'(\d+)\s*g\b(?!b)', r'\1gb', normalized)
        normalized = re.sub(r'(\d+)\s*t\b(?!b)', r'\1tb', normalized)
        
        # Generation normalization: 9th-gen -> 9th generation
        normalized = re.sub(r'(\d+)\w*\s*-?\s*gen(?:eration)?', r'\1th generation', normalized)
        
        # Remove special characters for better word matching
        normalized = re.sub(r'[^a-zA-Z0-9\s]', ' ', normalized)
        
        # Normalize multiple spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _extract_core_identifiers(self, text: str) -> Dict[str, str]:
        """
        Extract core product identifiers for matching.
        
        Returns dict with keys like 'brand', 'product_type', 'generation', 'storage'
        """
        identifiers = {}
        
        # Brand patterns
        brand_patterns = {
            'apple': r'\bapple\b',
            'samsung': r'\bsamsung\b', 
            'google': r'\bgoogle\b',
            'microsoft': r'\bmicrosoft\b',
            'nintendo': r'\bnintendo\b'
        }
        
        for brand, pattern in brand_patterns.items():
            if re.search(pattern, text):
                identifiers['brand'] = brand
                break
        
        # Product type patterns
        product_patterns = {
            'ipad': r'\bipad\b',
            'iphone': r'\biphone\b',
            'macbook': r'\bmacbook\b',
            'galaxy': r'\bgalaxy\b',
            'pixel': r'\bpixel\b',
            'surface': r'\bsurface\b',
            'switch': r'\bswitch\b'
        }
        
        for product, pattern in product_patterns.items():
            if re.search(pattern, text):
                identifiers['product_type'] = product
                break
        
        # Generation/model patterns
        generation_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s+generation', text)
        if generation_match:
            identifiers['generation'] = f"{generation_match.group(1)}th generation"
        
        # Storage patterns
        storage_match = re.search(r'(\d+)\s*(gb|tb)', text)
        if storage_match:
            identifiers['storage'] = f"{storage_match.group(1)}{storage_match.group(2)}"
        
        # Model number patterns (iPhone 16, Galaxy S24, etc.)
        model_match = re.search(r'\b(\d+)\b(?!\s*(gb|tb|th|st|nd|rd))', text)
        if model_match:
            identifiers['model'] = model_match.group(1)
        
        return identifiers
    
    def _flexible_value_match(self, target_value: str, title_value: str, key: str) -> bool:
        """
        Flexible matching for specific identifier types.
        
        Args:
            target_value: Value from search query
            title_value: Value from product title
            key: Type of identifier (brand, storage, etc.)
        """
        # Exact match
        if target_value == title_value:
            return True
        
        # Storage flexible matching (64gb matches 64g)
        if key == 'storage':
            target_num = re.search(r'(\d+)', target_value)
            title_num = re.search(r'(\d+)', title_value)
            if target_num and title_num:
                return target_num.group(1) == title_num.group(1)
        
        # Generation flexible matching (9th generation matches 9th-gen)
        if key == 'generation':
            target_num = re.search(r'(\d+)', target_value)
            title_num = re.search(r'(\d+)', title_value)
            if target_num and title_num:
                return target_num.group(1) == title_num.group(1)
        
        # Model flexible matching
        if key == 'model':
            return target_value == title_value
        
        # Brand and product type should match exactly
        return target_value == title_value
    
    def _basic_string_matching(self, title: str, target: str) -> Tuple[bool, str]:
        """
        Legacy basic string matching method (kept for backward compatibility).
        """
        # Use fuzzy matching to determine similarity
        similarity = difflib.SequenceMatcher(None, title.lower(), target.lower()).ratio()
        
        if similarity >= 0.8:  # 80% similarity threshold
            return True, f"Basic string match (similarity: {similarity:.2f})"
        else:
            return False, f"Low similarity: {similarity:.2f}"
    
    def filter_product_list(self, products: List[Dict], target_search: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of products and return included/excluded lists.
        
        Args:
            products: List of product dictionaries
            target_search: Target search query
            
        Returns:
            Tuple[List[Dict], List[Dict]]: (included_products, excluded_products_with_reasons)
        """
        included = []
        excluded = []
        
        for product in products:
            title = product.get('title', '')
            should_include, reason = self.should_include_product(title, target_search)
            
            if should_include:
                included.append(product)
                self.logger.debug(f"✅ INCLUDED: {title[:50]}... - {reason}")
            else:
                excluded_product = product.copy()
                excluded_product['exclusion_reason'] = reason
                excluded.append(excluded_product)
                self.logger.debug(f"❌ EXCLUDED: {title[:50]}... - {reason}")
        
        self.logger.info(f"Product filtering results: {len(included)} included, {len(excluded)} excluded")
        return included, excluded
    
    def get_filter_statistics(self, excluded_products: List[Dict]) -> Dict[str, int]:
        """Get statistics about why products were excluded."""
        stats = {}
        for product in excluded_products:
            reason = product.get('exclusion_reason', 'Unknown')
            stats[reason] = stats.get(reason, 0) + 1
        return stats


# Convenience function for easy integration
def filter_products_smart(products: List[Dict], target_search: str) -> List[Dict]:
    """
    Convenience function to filter products using smart filtering.
    
    Args:
        products: List of product dictionaries with 'title' field
        target_search: Target search query (e.g., "iPhone 16")
        
    Returns:
        List[Dict]: Filtered products that match the target exactly
    """
    filter_engine = SmartProductFilter()
    included, excluded = filter_engine.filter_product_list(products, target_search)
    
    # Log summary
    if excluded:
        stats = filter_engine.get_filter_statistics(excluded)
        logging.getLogger(__name__).info(f"Filter stats: {stats}")
    
    return included
