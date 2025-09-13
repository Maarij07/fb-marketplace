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
                    'plus', 'pro', 'max', 'mini', 'se', 'c', 's'
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
        # Global exclusion patterns - Enhanced with more accessory keywords
        self.global_exclusions = [
            'case', 'cover', 'screen protector', 'charger', 'cable', 'adapter',
            'battery', 'replacement', 'parts', 'repair', 'service', 'unlock',
            'sim', 'memory card', 'headphones', 'airpods', 'bluetooth', 'speaker',
            'holder', 'mount', 'stand', 'dock', 'wireless', 'power bank',
            'tempered glass', 'magsafe', 'charging', 'wallet', 'folio', 'glass',
            'shield', 'bumper', 'pouch', 'sleeve', 'skin', 'film', 'leather',
            'silicone', 'tpu', 'hard', 'soft', 'wallet', 'flip', 'holster'
        ]
        
        # Version/generation exclusion patterns (removed 'generation' since it's legitimate for iPads, etc.)
        self.version_exclusions = [
            'gen', 'version', 'ver', 'v2', 'v3', 'mk2', 'mk3', '2nd', '3rd'
        ]
        
        self.logger.info("Smart Product Filter initialized")
    
    def should_include_product(self, product_title: str, target_search: str) -> Tuple[bool, str]:
        """
        Determine if a product should be included based on enhanced suffix-based filtering rules.
        
        Enhanced Logic:
        1. HIGHEST PRIORITY: If search query is found EXACTLY in product title, ALWAYS include
        2. Second Priority: Apply smart phone filtering for recognized brands
        3. Third Priority: If smart filtering fails, use substring matching fallback
        4. Always Apply: Global exclusions (accessories like case, cover, etc.)
        
        Args:
            product_title: The title of the product found
            target_search: The original search query (e.g., "iPhone 16", "iPad 9th generation")
            
        Returns:
            Tuple[bool, str]: (should_include, exclusion_reason)
        """
        try:
            # HIGHEST PRIORITY: Direct substring match check (before any cleaning)
            # If the search query is found exactly in the product title, include it
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
                        return self._smart_model_matching(target_info, product_info)
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
        
        # Define comprehensive brand patterns for ALL major phone brands
        brand_patterns = {
            # iPhone patterns - Fixed to handle compound variants like 'Pro Max'
            'iphone': r'iphone\s*(\d+)(\s*(pro\s*max|pro\s*plus|pro|plus\s*max|plus|max|mini|se|c|s))?',
            
            # Samsung patterns - Fixed to handle common search variations
            'samsung': r'(?:samsung\s*(?:galaxy\s*)?s(\d+)|galaxy\s*s(\d+)|samsung\s*s(\d+))(\s*(ultra|plus|edge|fe|lite|neo))?|(?:samsung\s*)?galaxy\s*note\s*(\d+)(\s*(ultra|plus))?',
            
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
                        'variants': match.group(3) if match.group(3) else '',
                        'full_model': f"iPhone {match.group(1)}" + (f" {match.group(3)}" if match.group(3) else "")
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
    
    def _smart_model_matching(self, target_info: Dict[str, str], product_info: Dict[str, str]) -> Tuple[bool, str]:
        """
        Apply smart model matching rules based on search intent.
        
        ENHANCED SUFFIX-BASED LOGIC:
        - If you search "iPhone 16" → Only show iPhone 16 (exclude Pro, Plus, etc.)
        - If you search "iPhone 16 Pro" → Only show iPhone 16 Pro (exclude regular 16, Plus, Max)
        - If you search "Redmi Note 10" → Only show Redmi Note 10 (exclude Pro, other models)
        - Any search term + suffix should be excluded (iPhone 16 + case, iPhone 16 Pro + case)
        - Any search term with suffix shouldn't match additional suffixes (iPhone 16 Pro ≠ iPhone 16 Pro Max)
        
        Args:
            target_info: Parsed target search info
            product_info: Parsed product info
            
        Returns:
            Tuple[bool, str]: (should_include, reason)
        """
        # 1. Check if base model numbers match (this is mandatory)
        if target_info['model'] != product_info['model']:
            return False, f"Different model number: {product_info['model']} vs {target_info['model']}"
        
        # 2. Parse variants from both target and product
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
        
        # Case A: Target has NO variants (e.g., "iPhone 16", "Redmi Note 10")
        # → Should ONLY include products with NO variants
        # → Should EXCLUDE any products with variants (Pro, Plus, Max, etc.)
        if not target_variants:
            # Check if product has any known suffix that's not in the target
            for suffix in all_known_suffixes:
                if suffix in product_title_lower and suffix not in target_search_lower:
                    return False, f"Target is base model but product has suffix: '{suffix}'"
            
            # If product has variants parsed, exclude it
            if product_variants:
                return False, f"Target is base model but product has variants: {', '.join(product_variants)}"
            
            # Both target and product have no variants - PERFECT MATCH
            return True, "Exact base model match"
        
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
        """Check if title contains globally excluded terms."""
        title_lower = title.lower()
        
        # Check for accessory keywords with word boundary check for more precision
        for exclusion in self.global_exclusions:
            # Use word boundaries for more accurate matching
            if re.search(r'\b' + re.escape(exclusion) + r'\b', title_lower):
                return True
        
        # Check for version-specific exclusions
        for exclusion in self.version_exclusions:
            if exclusion in title_lower:
                return True
        
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
