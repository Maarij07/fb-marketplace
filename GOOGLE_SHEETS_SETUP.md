# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets integration for the Facebook Marketplace automation tool.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. The Google Sheets document you want to use (you provided: https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit)

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note down your project ID

## Step 2: Enable APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

## Step 3: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `marketplace-sheets-service`
   - Description: `Service account for marketplace data export to Google Sheets`
4. Click "Create and Continue"
5. For roles, add:
   - **Editor** (or more specific roles if you prefer)
6. Click "Continue" and then "Done"

## Step 4: Generate Service Account Key

1. In the Credentials page, find your service account
2. Click on the service account name
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" format
6. Click "Create" - this will download a JSON file

## Step 5: Configure Credentials

1. Rename the downloaded JSON file to `google_sheets_credentials.json`
2. Move it to the `config/` folder in your project:
   ```
   fb-marketplace/config/google_sheets_credentials.json
   ```

## Step 6: Share Your Google Sheets

1. Open your Google Sheets document: https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit
2. Click the "Share" button (top-right)
3. Add the service account email (found in your credentials JSON file) as an Editor
   - The email looks like: `your-service-account@your-project-id.iam.gserviceaccount.com`
4. Make sure "Notify people" is unchecked
5. Click "Share"

## Step 7: Test the Integration

Once everything is set up, you can test the integration using the web interface or API endpoints.

## API Endpoints

The following new endpoints will be available:

- `POST /api/sheets/export` - Export all products to Google Sheets
- `POST /api/sheets/backup` - Create backup of recent data
- `POST /api/sheets/analytics` - Create analytics sheet
- `GET /api/sheets/info` - Get information about the connected sheet

## Usage Examples

### Export All Products
```bash
curl -X POST http://localhost:5000/api/sheets/export \
  -H "Content-Type: application/json" \
  -d '{"sheet_url": "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit"}'
```

### Create Backup
```bash
curl -X POST http://localhost:5000/api/sheets/backup \
  -H "Content-Type: application/json" \
  -d '{"sheet_url": "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit", "hours": 2}'
```

### Create Analytics
```bash
curl -X POST http://localhost:5000/api/sheets/analytics \
  -H "Content-Type: application/json" \
  -d '{"sheet_url": "https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit"}'
```

## What Gets Exported

The integration will create multiple worksheets in your Google Sheets:

### 1. Products Sheet
- Complete product data with all fields
- Product ID, Title, Price, Location, Images
- Seller information, Product details
- Timestamps and data quality indicators

### 2. Analytics Sheet
- Summary statistics
- Price distribution analysis
- Location breakdowns
- Top product models

### 3. Backup Sheets (when requested)
- Time-stamped backup sheets
- Contains recent products based on specified hours

## Formatting

- Headers are automatically formatted with blue background and white text
- Columns are auto-resized for better readability
- Analytics sheets have different color formatting

## Troubleshooting

### Common Issues:

1. **"Permission denied"** - Make sure you've shared the sheet with the service account email
2. **"Credentials not found"** - Check that the credentials JSON file is in the correct location
3. **"API not enabled"** - Ensure both Google Sheets API and Google Drive API are enabled
4. **"Invalid sheet URL"** - Make sure you're using the full shareable URL

### Debugging:

Check the application logs for detailed error messages. The Google Sheets manager includes comprehensive logging.

## Security Notes

- Keep your service account credentials secure
- Don't commit the credentials JSON file to version control
- The service account only has access to sheets you explicitly share with it
- Consider using more restrictive IAM roles in production

## Next Steps

Once set up, you can:
1. Set up scheduled exports to automatically update your sheets
2. Create custom analytics dashboards
3. Integrate with other Google Workspace tools
4. Set up automated reporting workflows
