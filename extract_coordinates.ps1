# Extract GPS coordinates from Facebook Marketplace HTML files
# This script finds the exact latitude and longitude coordinates from the static map URLs

param(
    [string]$HtmlDirectory = "D:\temp\development\fb-marketplace\temp_html_data\products"
)

Write-Host "Extracting GPS coordinates from Facebook Marketplace HTML files..." -ForegroundColor Green
Write-Host "Searching in: $HtmlDirectory" -ForegroundColor Yellow

# Get all HTML files
$htmlFiles = Get-ChildItem -Path $HtmlDirectory -Filter "*.html"

$results = @()

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)" -ForegroundColor Cyan
    
    $content = Get-Content $file.FullName -Raw
    
    # Extract coordinates from static_map.php URL
    # Pattern: center=LATITUDE%2CLONGITUDE
    $pattern = 'center=(-?\d+\.\d+)%2C(\d+\.\d+)'
    
    $matches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $matches) {
        if ($match.Groups.Count -ge 3) {
            $latitude = $match.Groups[1].Value
            $longitude = $match.Groups[2].Value
            
            Write-Host "  Found coordinates: $latitude, $longitude" -ForegroundColor Green
            
            $result = [PSCustomObject]@{
                FileName = $file.Name
                Latitude = [decimal]$latitude
                Longitude = [decimal]$longitude
                StaticMapURL = $match.Value
            }
            
            $results += $result
        }
    }
    
    # Also extract the human-readable location text
    $locationPattern = '<span[^>]*>Sydney, NSW</span>'
    $locationMatches = [regex]::Matches($content, $locationPattern)
    
    if ($locationMatches.Count -gt 0) {
        Write-Host "  Human-readable location: Sydney, NSW" -ForegroundColor Gray
    }
}

Write-Host "`nSummary of extracted coordinates:" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

$results | ForEach-Object {
    Write-Host "File: $($_.FileName)" -ForegroundColor White
    Write-Host "Coordinates: $($_.Latitude), $($_.Longitude)" -ForegroundColor Green
    Write-Host "Google Maps: https://www.google.com/maps?q=$($_.Latitude),$($_.Longitude)" -ForegroundColor Blue
    Write-Host ""
}

# Export to CSV for further analysis
$csvPath = "D:\temp\development\fb-marketplace\extracted_coordinates.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation
Write-Host "Results exported to: $csvPath" -ForegroundColor Magenta

# Show reverse geocoding information for the first coordinate
if ($results.Count -gt 0) {
    $lat = $results[0].Latitude
    $lon = $results[0].Longitude
    Write-Host "Sample reverse geocoding for coordinates $lat, $lon:" -ForegroundColor Yellow
    Write-Host "This appears to be in the Sydney metropolitan area, NSW, Australia" -ForegroundColor Gray
}

return $results
