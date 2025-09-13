#!/usr/bin/env python3
"""
License Generator for Facebook Marketplace Automation
Use this script to generate valid license files for clients after payment.
"""

import json
import hmac
import hashlib
import os
from datetime import datetime, date


def generate_license(expiry_date: str, secret: str = None) -> dict:
    """Generate a valid license with expiry date.
    
    Args:
        expiry_date: Date in YYYY-MM-DD format (e.g., "2026-01-01")
        secret: License secret (defaults to environment LIC_SECRET or fallback)
    
    Returns:
        Dictionary with license data
    """
    if not secret:
        secret = os.environ.get('LIC_SECRET', 'CHANGE_ME_SECRET')
    
    # Validate date format
    try:
        datetime.strptime(expiry_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Expiry date must be in YYYY-MM-DD format")
    
    # Generate HMAC signature
    license_key = hmac.new(
        secret.encode('utf-8'), 
        expiry_date.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    return {
        "expiry": expiry_date,
        "license_key": license_key
    }


def create_license_file(expiry_date: str, output_path: str = "license.json", secret: str = None):
    """Create a license.json file with the specified expiry date.
    
    Args:
        expiry_date: Date in YYYY-MM-DD format
        output_path: Path where to save the license file
        secret: License secret
    """
    license_data = generate_license(expiry_date, secret)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(license_data, f, indent=2)
    
    print(f"✅ License created: {output_path}")
    print(f"📅 Expires: {expiry_date}")
    print(f"🔑 Key: {license_data['license_key'][:16]}...")


def main():
    """Interactive license generator."""
    print("🔑 License Generator for Facebook Marketplace Automation")
    print("=" * 60)
    
    # Get expiry date
    while True:
        expiry_input = input("\nEnter license expiry date (YYYY-MM-DD): ").strip()
        if not expiry_input:
            print("❌ Please enter a date")
            continue
        
        try:
            exp_date = datetime.strptime(expiry_input, '%Y-%m-%d').date()
            if exp_date <= date.today():
                print("❌ Expiry date must be in the future")
                continue
            break
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2026-01-01)")
            continue
    
    # Get output path
    output = input("\nOutput file (press Enter for 'license.json'): ").strip()
    if not output:
        output = "license.json"
    
    # Use custom secret if available
    secret = os.environ.get('LIC_SECRET')
    if not secret:
        print("⚠️  Using default secret. Set LIC_SECRET environment variable for production.")
        secret = 'CHANGE_ME_SECRET'
    
    try:
        create_license_file(expiry_input, output, secret)
        print(f"\n✅ License file created successfully!")
        print(f"📋 Send '{output}' to your client")
        print("🔧 They should place it in the same folder as the EXE")
        
    except Exception as e:
        print(f"❌ Error creating license: {e}")


if __name__ == "__main__":
    main()
