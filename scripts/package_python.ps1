# Create a portable Python venv bundle for offline distribution (Windows PowerShell)
param()
$Root = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $Root 'dist\py-bundle'
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
New-Item -ItemType Directory -Path $DistDir | Out-Null
python -m venv "$DistDir\venv"
& "$DistDir\venv\Scripts\pip.exe" install --upgrade pip
if (Test-Path (Join-Path $Root 'services\api\requirements.txt')) {
    & "$DistDir\venv\Scripts\pip.exe" install -r "$Root\services\api\requirements.txt"
}
# copy files
Copy-Item -Path "$Root\*" -Destination "$DistDir\app" -Recurse -Force -Exclude @('*.pyc','__pycache__')
# create launcher
$launcher = @'
@echo off
set DIR=%~dp0
call "%DIR%venv\Scripts\activate.bat"
python "%DIR%app\services\api\main.py"
'@
Set-Content -Path (Join-Path $DistDir 'run.bat') -Value $launcher -Encoding ASCII
# zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
$now = Get-Date -Format yyyyMMddHHmmss
$zip = Join-Path (Join-Path $Root 'dist') "py-bundle-$now.zip"
[System.IO.Compression.ZipFile]::CreateFromDirectory($DistDir, $zip)
Write-Host "Created $zip"