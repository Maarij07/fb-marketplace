"""
Script to test the Facebook time parser on actual HTML files.
This will read HTML files and extract timing expressions.
"""

import os
from facebook_time_parser import FacebookTimeParser, extract_time_from_html

def test_html_files():
    """Test the parser on HTML files in the working_html_data/products directory."""
    parser = FacebookTimeParser()
    
    # Look for HTML files in the products directory
    products_dir = os.path.join('working_html_data', 'products')
    if not os.path.exists(products_dir):
        print(f"Directory {products_dir} not found")
        return
        
    html_files = [f for f in os.listdir(products_dir) if f.endswith('.html')]
    html_file_paths = [os.path.join(products_dir, f) for f in html_files]
    
    if not html_files:
        print("No HTML files found in current directory")
        return
    
    print(f"Found {len(html_files)} HTML files")
    print("=" * 50)
    
    total_expressions = []
    
    for i, html_file in enumerate(html_files[:3]):  # Test first 3 files
        html_file_path = html_file_paths[i]
        print(f"\nAnalyzing: {html_file}")
        print("-" * 30)
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract timing expressions
            expressions = extract_time_from_html(html_content)
            
            if expressions:
                print(f"Found {len(expressions)} timing expressions:")
                for expr in expressions:
                    minutes = parser.parse_time_expression(expr)
                    if minutes is not None:
                        hours = minutes / 60
                        print(f"  '{expr}' -> {minutes} minutes ({hours:.1f} hours)")
                        total_expressions.append(expr)
                    else:
                        print(f"  '{expr}' -> Unable to parse")
            else:
                print("No timing expressions found")
                
        except Exception as e:
            print(f"Error reading {html_file}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    if total_expressions:
        unique_expressions = list(set(total_expressions))
        print(f"Total unique expressions found: {len(unique_expressions)}")
        print("All unique expressions:")
        for expr in sorted(unique_expressions):
            minutes = parser.parse_time_expression(expr)
            if minutes is not None:
                print(f"  '{expr}' -> {minutes} minutes")
    else:
        print("No timing expressions found in any files")

if __name__ == "__main__":
    test_html_files()
