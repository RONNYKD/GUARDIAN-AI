# Test script for Gemini Analyzer
# Sets all required environment variables and runs the test

Write-Host "🔧 Setting up environment..." -ForegroundColor Cyan

# Set environment variables
$env:GCP_PROJECT_ID = "lovable-clone-e08db"
$env:GOOGLE_APPLICATION_CREDENTIALS = "d:\SENTINEL (for the google accelerator hackerthon)\lovable-clone-e08db-56b9ffba4711.json"

Write-Host "✅ GCP_PROJECT_ID: $env:GCP_PROJECT_ID" -ForegroundColor Green
Write-Host "✅ GOOGLE_APPLICATION_CREDENTIALS: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Green

# Verify credentials file exists
if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
    Write-Host "✅ Service account JSON file found" -ForegroundColor Green
} else {
    Write-Host "❌ Service account JSON file NOT found at: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Red
    exit 1
}

Write-Host "`n🚀 Running Gemini Analyzer test..." -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor DarkGray

# Run the test
python gemini_analyzer.py

Write-Host "`n================================================" -ForegroundColor DarkGray

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Test completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
}
