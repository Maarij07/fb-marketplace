# Facebook Marketplace Automation - Licensing System

## Overview

This application now includes a **non-destructive licensing system** that provides trial functionality with controlled access after the trial period.

## How It Works

### Trial Period
- **Trial ends:** September 11, 2025
- **Before this date:** Application runs normally in trial mode
- **On/after this date:** Application requires a valid license file to run

### Licensing Mechanism
The system uses HMAC-SHA256 cryptographic signatures to validate licenses:
- Licenses are stored in a `license.json` file next to the EXE
- Each license contains an expiry date and cryptographic signature
- Signatures prevent tampering and ensure authenticity

## For You (Developer)

### Generating Licenses
Use the `license_generator.py` script to create licenses for paying clients:

```bash
python license_generator.py
```

Or create programmatically:
```python
from license_generator import create_license_file
create_license_file("2026-12-31", "client_license.json")
```

### Important Security Notes
1. **Change the secret:** Before production, set environment variable `LIC_SECRET` to a secure random string
2. **Keep the secret safe:** Never share the secret with clients
3. **Test thoroughly:** Use `test_license.py` to verify the system works

### Internal Testing
For your own testing after Sept 11th, set environment variable:
```bash
set LICENSE_BYPASS=1
```

## For Clients

### Trial Usage
- Download and run the EXE normally
- No license file needed during trial period
- Application will show remaining trial days

### After Trial (Post Sept 11, 2025)
1. Purchase a license from you
2. Receive a `license.json` file
3. Place the file in the same folder as the EXE
4. Run the application normally

### License File Format
```json
{
  "expiry": "2026-12-31",
  "license_key": "a1b2c3d4e5f6..."
}
```

## Features

### Non-Destructive
- ✅ Does not delete files or damage systems
- ✅ Simply prevents application startup
- ✅ Clear error messages for expired trials

### Professional
- ✅ Cryptographically secure licensing
- ✅ Offline license validation
- ✅ Clear trial period communication
- ✅ Professional error handling

### Flexible
- ✅ Easy license generation for clients
- ✅ Customizable expiry dates
- ✅ Development bypass for testing
- ✅ No internet connection required

## File Structure
```
dist/
├── FacebookMarketplaceAutomation.exe
├── license.json                      # Client places this here
└── ... (other files)

Your development folder:
├── license_generator.py              # For creating client licenses
├── test_license.py                   # For testing the system
├── test_license_future.json          # Test file (valid license)
├── test_license_expired.json         # Test file (expired license)
└── LICENSE_SYSTEM_README.md          # This file
```

## Testing the System

1. **Test trial mode:**
   ```bash
   dist/FacebookMarketplaceAutomation.exe
   ```
   Should work normally and show remaining trial days.

2. **Test license after trial:**
   ```bash
   copy test_license_future.json dist/license.json
   dist/FacebookMarketplaceAutomation.exe
   ```
   Should work even after Sept 11th.

3. **Test expired license:**
   ```bash
   copy test_license_expired.json dist/license.json
   dist/FacebookMarketplaceAutomation.exe
   ```
   Should fail if after Sept 11th with clear error message.

## Client Instructions Template

Send this to clients:

---

**Facebook Marketplace Automation - Trial & Licensing**

**Trial Period:** This software includes a trial period until September 11, 2025.

**After Trial:** To continue using the software after the trial:
1. Purchase a license
2. Save the provided `license.json` file in the same folder as the EXE
3. Run the application normally

**Support:** Contact [your contact info] for licenses or technical support.

---

## Security Considerations

- License files are cryptographically signed and cannot be forged
- The system works offline (no internet required)
- Expired licenses are rejected automatically
- The secret key should be kept confidential and secure
