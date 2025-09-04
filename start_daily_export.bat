@echo off
echo =====================================
echo    Facebook Marketplace Automation  
echo    Daily Google Sheets Export        
echo =====================================
echo.
echo Starting daily export scheduler...
echo - Exports data every 24 hours
echo - Appends without removing existing data
echo - No deduplication (as requested)
echo.
echo Google Sheet: https://docs.google.com/spreadsheets/d/1plNlmsrbvE0fRYLrfBqt6rawPYiXwsJrhyqJa6-5BpI/edit
echo.
echo Press Ctrl+C to stop the scheduler
echo.
python daily_sheets_exporter.py
pause
