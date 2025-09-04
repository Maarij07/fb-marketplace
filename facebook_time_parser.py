"""
Facebook Marketplace Time Parser

This module provides functionality to parse Facebook's natural language timing expressions
and convert them to approximate minute values for data processing and analysis.

The mapping covers common Facebook timing expressions found in marketplace listings,
including abbreviated forms like "3h", "1w", "23h" as well as full text expressions
like "just listed", "moments ago", "yesterday", etc.
"""

import re
from typing import Optional, Dict, List, Union


class FacebookTimeParser:
    """Parser for Facebook Marketplace timing expressions."""
    
    # Comprehensive mapping of Facebook time expressions to approximate minutes
    TIME_MAPPINGS = [
        # Exact match expressions (most common)
        {"text": "just listed", "minutes": 5},
        {"text": "moments ago", "minutes": 1},
        {"text": "a few seconds ago", "minutes": 0.1},
        {"text": "few seconds ago", "minutes": 0.1},
        {"text": "a few minutes ago", "minutes": 3},
        {"text": "few minutes ago", "minutes": 3},
        {"text": "1 minute ago", "minutes": 1},
        {"text": "minute ago", "minutes": 1},
        {"text": "about a minute ago", "minutes": 1},
        {"text": "about 5 minutes ago", "minutes": 5},
        {"text": "about 10 minutes ago", "minutes": 10},
        {"text": "about 15 minutes ago", "minutes": 15},
        {"text": "a quarter of an hour ago", "minutes": 15},
        {"text": "30 minutes ago", "minutes": 30},
        {"text": "about 30 minutes ago", "minutes": 30},
        {"text": "an hour ago", "minutes": 60},
        {"text": "about an hour ago", "minutes": 60},
        {"text": "1 hour ago", "minutes": 60},
        {"text": "2 hours ago", "minutes": 120},
        {"text": "3 hours ago", "minutes": 180},
        {"text": "today", "minutes": 720},  # 12 hours approx.
        {"text": "yesterday", "minutes": 1440},  # 24 hours
        {"text": "1 day ago", "minutes": 1440},
        {"text": "a week ago", "minutes": 10080},  # 7 days
        {"text": "1 week ago", "minutes": 10080},
        {"text": "a month ago", "minutes": 43200},  # 30 days
        {"text": "1 month ago", "minutes": 43200},
        {"text": "a year ago", "minutes": 525600},  # 365 days
        {"text": "1 year ago", "minutes": 525600},
        # Default fallbacks
        {"text": "minutes ago", "minutes": 5},  # default if no number
        {"text": "hours ago", "minutes": 120},  # default if no number
        {"text": "days ago", "minutes": 2880},  # default 2 days
        {"text": "weeks ago", "minutes": 20160},  # 14 days default
        {"text": "months ago", "minutes": 86400},  # 60 days default
        {"text": "years ago", "minutes": 1051200},  # 2 years default
    ]
    
    # Regex patterns for parsing abbreviated forms like "3h", "1w", "23h"
    REGEX_PATTERNS = [
        # Minutes: "5m", "15m", "30m"
        (r'(\d+)m\b', 1),
        # Hours: "1h", "3h", "23h"
        (r'(\d+)h\b', 60),
        # Days: "1d", "2d", "7d"
        (r'(\d+)d\b', 1440),
        # Weeks: "1w", "2w"
        (r'(\d+)w\b', 10080),
        # Months: "1mo", "2mo" (some systems use "mo" to distinguish from minutes)
        (r'(\d+)mo\b', 43200),
        # Years: "1y", "2y"
        (r'(\d+)y\b', 525600),
        # Extended patterns with spaces
        (r'(\d+)\s+minutes?\s+ago', 1),
        (r'(\d+)\s+hours?\s+ago', 60),
        (r'(\d+)\s+days?\s+ago', 1440),
        (r'(\d+)\s+weeks?\s+ago', 10080),
        (r'(\d+)\s+months?\s+ago', 43200),
        (r'(\d+)\s+years?\s+ago', 525600),
    ]
    
    def __init__(self):
        """Initialize the parser with compiled regex patterns."""
        self.compiled_patterns = [(re.compile(pattern, re.IGNORECASE), multiplier) 
                                 for pattern, multiplier in self.REGEX_PATTERNS]
    
    def parse_time_expression(self, text: str) -> Optional[float]:
        """
        Parse a Facebook time expression and return approximate minutes.
        
        Args:
            text (str): The timing expression to parse
            
        Returns:
            Optional[float]: Number of minutes, or None if cannot be parsed
        """
        if not text or not isinstance(text, str):
            return None
        
        # Clean the input
        cleaned_text = text.strip().lower()
        
        # First try exact matches
        for mapping in self.TIME_MAPPINGS:
            if mapping["text"].lower() == cleaned_text:
                return float(mapping["minutes"])
        
        # Try regex patterns for abbreviated forms
        for pattern, multiplier in self.compiled_patterns:
            match = pattern.search(cleaned_text)
            if match:
                try:
                    number = int(match.group(1))
                    return float(number * multiplier)
                except (ValueError, IndexError):
                    continue
        
        # Try partial matches for common phrases
        for mapping in self.TIME_MAPPINGS:
            if mapping["text"].lower() in cleaned_text:
                return float(mapping["minutes"])
        
        return None
    
    def parse_multiple_expressions(self, expressions: List[str]) -> Dict[str, Optional[float]]:
        """
        Parse multiple time expressions at once.
        
        Args:
            expressions (List[str]): List of timing expressions
            
        Returns:
            Dict[str, Optional[float]]: Dictionary mapping expressions to minutes
        """
        return {expr: self.parse_time_expression(expr) for expr in expressions}
    
    def get_supported_expressions(self) -> List[str]:
        """
        Get list of all supported exact match expressions.
        
        Returns:
            List[str]: List of supported expressions
        """
        return [mapping["text"] for mapping in self.TIME_MAPPINGS]


def extract_time_from_html(html_content: str) -> List[str]:
    """
    Extract potential timing expressions from Facebook HTML content.
    
    This function looks for common patterns where timing information appears
    in Facebook Marketplace HTML.
    
    Args:
        html_content (str): HTML content to search
        
    Returns:
        List[str]: List of found timing expressions
    """
    # Common patterns for Facebook timing in HTML
    timing_patterns = [
        # Pattern: <span>3h</span>, <span>1w</span>
        r'<span[^>]*>([0-9]+[mhdwy])</span>',
        # Pattern: <abbr aria-label="X hours ago"><span>3h</span></abbr>
        r'<abbr[^>]*aria-label="[^"]*ago"[^>]*><span[^>]*>([^<]+)</span></abbr>',
        # Pattern: aria-label="X minutes ago" or similar
        r'aria-label="([^"]*(?:ago|listed))"',
        # Pattern: Plain text timing expressions
        r'\b(\d+\s*(?:minutes?|hours?|days?|weeks?|months?|years?)\s+ago)\b',
        r'\b(just listed|moments ago|yesterday|today)\b',
    ]
    
    found_expressions = []
    
    for pattern in timing_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        found_expressions.extend(matches)
    
    # Remove duplicates while preserving order
    unique_expressions = []
    seen = set()
    for expr in found_expressions:
        if expr.lower() not in seen:
            unique_expressions.append(expr)
            seen.add(expr.lower())
    
    return unique_expressions


# Example usage and testing
if __name__ == "__main__":
    parser = FacebookTimeParser()
    
    # Test various expressions
    test_expressions = [
        "just listed",
        "3h",
        "1w", 
        "23h",
        "moments ago",
        "2 hours ago",
        "yesterday",
        "1 day ago",
        "about an hour ago",
        "5m",
        "30 minutes ago"
    ]
    
    print("Facebook Time Parser - Test Results")
    print("=" * 40)
    
    for expr in test_expressions:
        minutes = parser.parse_time_expression(expr)
        if minutes is not None:
            hours = minutes / 60
            days = minutes / 1440
            print(f"'{expr}' -> {minutes} minutes ({hours:.2f} hours, {days:.2f} days)")
        else:
            print(f"'{expr}' -> Unable to parse")
    
    print("\nSupported exact expressions:")
    print("-" * 30)
    for expr in parser.get_supported_expressions()[:10]:  # Show first 10
        print(f"- {expr}")
    print("... and more")
