# Start local backend and optionally the Electron native UI (Windows PowerShell)
# Usage: .\start_local.ps1 [-StartElectron]
param([switch]$StartElectron)

Write-Host "Starting local backend (uvicorn)..."
$env:PYTHONPATH = "$PSScriptRoot\.."
Start-Process -NoNewWindow -FilePath python -ArgumentList 'services\api\main.py' -WindowStyle Hidden
Start-Sleep -Seconds 2

if ($StartElectron) {
    Write-Host "Starting Electron native UI..."
    Push-Location apps\native
    if (-not (Test-Path node_modules)) {
        Write-Host "Installing node deps (electron) - this may take a moment..."
        npm install
    }
    Start-Process -NoNewWindow -FilePath npm -ArgumentList 'run','start'
    Pop-Location
}

Write-Host "Local services started. Backend: http://127.0.0.1:8000"
Write-Host "Open apps/web/index.html in Chrome or run Electron to view native UI."
