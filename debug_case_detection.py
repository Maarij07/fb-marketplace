#!/usr/bin/env python3
"""
Debug script to check why "case" and "screen protector" detection is failing.
"""

import re
from core.product_filter import SmartProductFilter

def debug_case_detection():
    """Debug the case detection logic."""
    
    filter_engine = SmartProductFilter()
    
    # Test cases that are failing
    failing_cases = [
        "iPhone 15 Case Black Silicone",
        "iPhone 16 Screen Protector Tempered Glass",
        "iPhone 13 Case Space Gray"
    ]
    
    print("🔍 Debugging Case Detection Logic")
    print("=" * 50)
    
    for test_case in failing_cases:
        print(f"\nTesting: '{test_case}'")
        
        title_lower = test_case.lower()
        print(f"Lowercase: '{title_lower}'")
        
        # Check individual blacklist terms
        blacklisted_terms = []
        for accessory_term in filter_engine.accessories_blacklist:
            # Use word boundaries for multi-word terms, simple substring for single words
            if ' ' in accessory_term:
                # Multi-word terms: use exact phrase matching
                if accessory_term in title_lower:
                    blacklisted_terms.append(accessory_term)
                    print(f"✅ Found multi-word term: '{accessory_term}'")
            else:
                # Single words: use word boundary for precision (but not too strict)
                if re.search(r'\b' + re.escape(accessory_term) + r'\b', title_lower):
                    blacklisted_terms.append(accessory_term)
                    print(f"✅ Found single word term: '{accessory_term}'")
        
        print(f"Blacklisted terms found: {blacklisted_terms}")
        
        # Check accessory patterns
        accessory_patterns = [
            r'\bcase\b',                    # iPhone 15 Case
            r'\bscreen\s+protector\b',      # Screen Protector
            r'\btempered\s+glass\b',        # Tempered Glass
        ]
        
        pattern_matches = []
        for pattern in accessory_patterns:
            if re.search(pattern, title_lower):
                match = re.search(pattern, title_lower)
                pattern_matches.append(match.group().strip())
                print(f"✅ Pattern matched: '{pattern}' -> '{match.group()}'")
        
        print(f"Pattern matches: {pattern_matches}")
        
        # Test the actual exclusion function
        contains_exclusions = filter_engine._contains_global_exclusions(test_case)
        print(f"Contains exclusions: {contains_exclusions}")
        
        # Test the full filtering logic
        should_include, reason = filter_engine.should_include_product(test_case, "iPhone 15")
        print(f"Should include: {should_include}, Reason: {reason}")
        
        print("-" * 50)


def test_regex_patterns():
    """Test specific regex patterns."""
    print("\n🧪 Testing Regex Patterns")
    print("=" * 30)
    
    test_strings = [
        "iPhone 15 Case Black Silicone",
        "iPhone 16 Screen Protector Tempered Glass",
        "iPhone Case for 15",
        "Screen Protector iPhone 16",
        "Tempered Glass iPhone",
        "iPhone 15 case silicone",  # lowercase
    ]
    
    patterns = [
        (r'\bcase\b', "Case pattern"),
        (r'\bscreen\s+protector\b', "Screen protector pattern"),
        (r'\btempered\s+glass\b', "Tempered glass pattern"),
    ]
    
    for test_string in test_strings:
        print(f"\nTesting: '{test_string}'")
        test_lower = test_string.lower()
        
        for pattern, description in patterns:
            match = re.search(pattern, test_lower, re.IGNORECASE)
            if match:
                print(f"  ✅ {description} matched: '{match.group()}'")
            else:
                print(f"  ❌ {description} NO MATCH")


if __name__ == "__main__":
    debug_case_detection()
    test_regex_patterns()
