# Cthulu Complete Setup Script for Windows GCP VM
# Run this in PowerShell as Administrator

$ErrorActionPreference = "Continue"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CTHULU APEX v5.1 - GCP VM SETUP" -ForegroundColor Cyan  
Write-Host "==========================================" -ForegroundColor Cyan

# Create workspace
$workspace = "C:\workspace"
if (-not (Test-Path $workspace)) {
    New-Item -ItemType Directory -Path $workspace -Force | Out-Null
    Write-Host "[OK] Created $workspace" -ForegroundColor Green
}
Set-Location $workspace

# Install Chocolatey (package manager)
Write-Host "`n[1/5] Installing Chocolatey..." -ForegroundColor Yellow
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    Write-Host "[OK] Chocolatey installed" -ForegroundColor Green
} else {
    Write-Host "[OK] Chocolatey already installed" -ForegroundColor Green
}

# Install Python
Write-Host "`n[2/5] Installing Python 3.11..." -ForegroundColor Yellow
choco install python311 -y --no-progress
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
refreshenv
Write-Host "[OK] Python installed" -ForegroundColor Green

# Install Git
Write-Host "`n[3/5] Installing Git..." -ForegroundColor Yellow
choco install git -y --no-progress
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
refreshenv
Write-Host "[OK] Git installed" -ForegroundColor Green

# Install VS Code
Write-Host "`n[4/5] Installing VS Code..." -ForegroundColor Yellow
choco install vscode -y --no-progress
Write-Host "[OK] VS Code installed" -ForegroundColor Green

# Clone Cthulu
Write-Host "`n[5/5] Cloning Cthulu repository..." -ForegroundColor Yellow
if (Test-Path "$workspace\cthulu") {
    Write-Host "[INFO] Cthulu already exists, pulling latest..." -ForegroundColor Cyan
    Set-Location "$workspace\cthulu"
    git pull
} else {
    git clone https://github.com/amuzetnoM/cthulu.git "$workspace\cthulu"
}
Set-Location "$workspace\cthulu"
Write-Host "[OK] Cthulu cloned" -ForegroundColor Green

# Setup Python environment
Write-Host "`n[6/6] Setting up Python environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host "[OK] Python environment ready" -ForegroundColor Green

# Clone Sentinel
Write-Host "`n[7] Cloning Sentinel..." -ForegroundColor Yellow
if (-not (Test-Path "$workspace\sentinel")) {
    git clone https://github.com/amuzetnoM/cthulu.git "$workspace\sentinel-temp"
    Move-Item "$workspace\sentinel-temp\sentinel" "$workspace\sentinel" -Force
    Remove-Item "$workspace\sentinel-temp" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "[OK] Sentinel ready" -ForegroundColor Green

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host @"

NEXT STEPS:
1. Download and install MetaTrader 5 from your broker
2. Login to MT5 with your trading account
3. Enable Algo Trading in MT5 (Tools > Options > Expert Advisors)
4. Configure Cthulu:
   cd C:\workspace\cthulu
   .\venv\Scripts\Activate.ps1
   python __main__.py --wizard

Your Cthulu installation is at: C:\workspace\cthulu
Your Sentinel installation is at: C:\workspace\sentinel

"@ -ForegroundColor White
