#!/usr/bin/env python3
"""
Test script to reproduce and fix the timing parsing issue with "6 weeks ago".
"""

from facebook_time_parser import FacebookTimeParser

def test_timing_parser():
    """Test the timing parser with various expressions."""
    parser = FacebookTimeParser()
    
    # Test expressions that should work correctly
    test_cases = [
        ("6 weeks ago", 6 * 10080),  # Should be 60,480 minutes
        ("2 weeks ago", 2 * 10080),  # Should be 20,160 minutes  
        ("1 week ago", 1 * 10080),   # Should be 10,080 minutes
        ("weeks ago", 20160),        # Fallback should be 14 days (20,160 minutes)
        ("3h", 3 * 60),              # Should be 180 minutes
        ("1w", 1 * 10080),           # Should be 10,080 minutes
        ("just listed", 5),          # Should be 5 minutes
        ("5 days ago", 5 * 1440),    # Should be 7,200 minutes
    ]
    
    print("Testing Facebook Time Parser:")
    print("=" * 50)
    
    for text, expected_minutes in test_cases:
        result = parser.parse_time_expression(text)
        status = "✓ PASS" if result == expected_minutes else "✗ FAIL"
        print(f"{status} '{text}' -> {result} minutes (expected: {expected_minutes})")
        
        if result != expected_minutes:
            print(f"     Issue: Got {result}, expected {expected_minutes}")
            
            # Debug the issue
            print(f"     Debugging '{text}':")
            cleaned_text = text.strip().lower()
            
            # Check exact matches
            exact_match = None
            for mapping in parser.TIME_MAPPINGS:
                if mapping["text"].lower() == cleaned_text:
                    exact_match = mapping["minutes"]
                    break
            print(f"       Exact match: {exact_match}")
            
            # Check regex patterns
            regex_match = None
            for pattern, multiplier in parser.compiled_patterns:
                match = pattern.search(cleaned_text)
                if match:
                    try:
                        number = int(match.group(1))
                        regex_match = number * multiplier
                        print(f"       Regex match: {regex_match} (number={number}, multiplier={multiplier})")
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Check partial matches
            partial_match = None
            for mapping in parser.TIME_MAPPINGS:
                if mapping["text"].lower() in cleaned_text:
                    partial_match = mapping["minutes"]
                    print(f"       Partial match: {partial_match} (matched '{mapping['text']}')")
                    break
        
        print()

if __name__ == "__main__":
    test_timing_parser()
