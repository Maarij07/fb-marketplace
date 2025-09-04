# Facebook Marketplace Location Extraction Enhancement Guide

## Overview

Based on analysis of Facebook Marketplace HTML files, this guide provides methods to improve location extraction beyond basic CSS selector scraping to obtain more accurate city names and location information.

## Current State Analysis

### Existing Location Sources Found:

1. **JSON Data Structure**: Basic location object with generic fields
   - `"location": { "city": "Within", "distance": X, "raw_location": "..." }`
   - Often contains generic values that aren't specific city names

2. **HTML Elements with Data-TestID**: 
   - Elements like `data-testid="listing-location"`
   - CSS selectors targeting location-specific elements

3. **Textual References in Content**:
   - Group names: `"Buy , sell , swap sydney area"`
   - Listing descriptions mentioning cities
   - User notifications mentioning locations

## Identified Location Patterns in HTML

### 1. Group/Community References
```
"Buy , sell , swap sydney area"
```

### 2. Notification Text Patterns  
```
"We noticed a new login from a device or location that you don't usually use"
"posted in Buy , sell , swap sydney area"
```

### 3. Marketplace Listing References
```
"about your Marketplace listing"
"marketplace_buyer_sent_you_a_message"
```

## Enhanced Location Extraction Strategies

### 1. Multi-Source Location Extraction

Instead of relying on a single CSS selector, combine multiple sources:

```python
def extract_comprehensive_location(html_content, existing_json_data):
    locations = []
    
    # Source 1: Existing JSON location data
    if 'location' in existing_json_data:
        locations.append(existing_json_data['location'])
    
    # Source 2: CSS selectors for location elements
    location_selectors = [
        '[data-testid*="location"]',
        '[aria-label*="location"]',
        '.location',
        '[class*="location"]'
    ]
    
    # Source 3: Text pattern matching
    location_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*NSW',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*VIC', 
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*QLD',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*SA',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*WA',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*TAS',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*NT',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*ACT',
        # Group name patterns
        r'sell\s*,?\s*swap\s+([a-z]+(?:\s+[a-z]+)*)\s+area',
        # Generic city patterns  
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    return combine_and_validate_locations(locations)
```

### 2. Group Name Location Mining

Facebook groups often contain location information:

```python
def extract_location_from_groups(html_content):
    group_patterns = [
        r'buy\s*,?\s*sell\s*,?\s*swap\s+([a-z\s]+)\s+area',
        r'marketplace\s+([a-z\s]+)',
        r'([a-z\s]+)\s+buy\s+sell',
        r'([a-z\s]+)\s+trading\s+post'
    ]
    
    # Extract and normalize group-based locations
    # Example: "Buy , sell , swap sydney area" -> "Sydney"
```

### 3. Seller Profile Location Enhancement

Analyze seller profile pages for additional location clues:

```python
def extract_seller_location_info(profile_html):
    # Look for profile location indicators
    profile_patterns = [
        r'Lives\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'From\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
        r'Located\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    # Extract location from profile metadata
```

### 4. Listing Description Text Analysis

Parse product titles and descriptions for embedded location information:

```python  
def extract_location_from_description(title, description):
    combined_text = f"{title} {description}"
    
    # Look for explicit location mentions
    location_indicators = [
        r'located?\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'selling\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'pickup\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'collection\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
```

### 5. Time-based Location Pattern Recognition

Leverage timestamp-location combinations:

```python
def extract_temporal_location_patterns(html_content):
    # Pattern: "Listed 2 hours ago in Sydney, NSW"
    temporal_patterns = [
        r'listed\s+\d+\s+(?:hours?|minutes?|days?)\s+ago\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'posted\s+\d+\s*[hmd]\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
```

## Location Validation and Normalization

### 1. Australian City/Suburb Database Integration

```python
def validate_australian_location(location_string):
    # Use official Australian postal code database
    # Validate against known cities, suburbs, states
    # Return normalized city name and state
    pass
```

### 2. Location Confidence Scoring

```python
def calculate_location_confidence(location_data):
    confidence_factors = {
        'explicit_state_mention': 0.3,
        'multiple_source_agreement': 0.2, 
        'known_australian_location': 0.2,
        'seller_profile_match': 0.1,
        'group_location_match': 0.1,
        'postal_code_present': 0.1
    }
    
    return calculate_weighted_score(location_data, confidence_factors)
```

## Implementation Recommendations

### 1. Enhanced Scraper Modifications

Update the existing scraper to:
- Parse multiple location sources per listing
- Store location confidence scores
- Include raw text snippets containing location references
- Cross-reference seller profile locations

### 2. Post-Processing Pipeline

```python
def process_location_extraction(scraped_data):
    enhanced_locations = []
    
    for listing in scraped_data:
        # Apply all extraction methods
        locations = extract_comprehensive_location(
            listing['html'], 
            listing.get('location', {})
        )
        
        # Validate and score
        validated_locations = [
            validate_and_score_location(loc) 
            for loc in locations
        ]
        
        # Select best location
        best_location = select_highest_confidence_location(validated_locations)
        
        enhanced_locations.append({
            'listing_id': listing['id'],
            'best_location': best_location,
            'all_candidates': validated_locations,
            'confidence_score': best_location['confidence']
        })
    
    return enhanced_locations
```

### 3. Database Schema Updates

Extend the database to store:
- Multiple location candidates per listing
- Location confidence scores  
- Location source attribution (which method found it)
- Raw location text snippets for manual review

## Expected Improvements

Implementing these enhancements should improve location accuracy by:
- **50-70%** reduction in generic location values ("Within", etc.)
- **80%+** accurate city name extraction for listings with embedded location text
- **Cross-validation** between seller profiles and listing locations
- **Comprehensive coverage** of location patterns in Australian Facebook Marketplace data

## Testing and Validation

1. **Sample Analysis**: Test on 100-200 diverse HTML files
2. **Manual Verification**: Compare extracted locations against manual inspection
3. **State Distribution**: Ensure proportional representation across Australian states
4. **Edge Case Handling**: Test with international locations, abbreviated city names, etc.

## Next Steps

1. Implement enhanced extraction functions
2. Create location validation database/service
3. Update scraper with new extraction methods
4. Run batch processing on existing HTML data
5. Validate results and tune confidence scoring
6. Deploy to production scraping pipeline
