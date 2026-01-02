# Cthulu VM Setup Script
# Run this INSIDE the Windows VM via PowerShell

# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CTHULU VM SETUP - APEX v5.1.0" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create working directory
$CTHULU_DIR = "C:\cthulu"
$TEMP_DIR = "C:\temp_setup"

New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null

# Step 1: Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {
    Write-Host "  Downloading Python 3.11..." -ForegroundColor Gray
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$TEMP_DIR\python_installer.exe"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    
    Write-Host "  Installing Python..." -ForegroundColor Gray
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  Python installed!" -ForegroundColor Green
} else {
    Write-Host "  Python already installed: $(python --version)" -ForegroundColor Green
}

# Step 2: Check Git
Write-Host "[2/5] Checking Git..." -ForegroundColor Yellow
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "  Downloading Git..." -ForegroundColor Gray
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$TEMP_DIR\git_installer.exe"
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller
    
    Write-Host "  Installing Git..." -ForegroundColor Gray
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  Git installed!" -ForegroundColor Green
} else {
    Write-Host "  Git already installed: $(git --version)" -ForegroundColor Green
}

# Step 3: Clone/Update Cthulu
Write-Host "[3/5] Setting up Cthulu..." -ForegroundColor Yellow
if (Test-Path $CTHULU_DIR) {
    Write-Host "  Updating existing repository..." -ForegroundColor Gray
    Set-Location $CTHULU_DIR
    git pull origin main
} else {
    Write-Host "  Cloning repository..." -ForegroundColor Gray
    git clone https://github.com/amuzetnoM/cthulu.git $CTHULU_DIR
    Set-Location $CTHULU_DIR
}
Write-Host "  Cthulu ready at $CTHULU_DIR" -ForegroundColor Green

# Step 4: Install Python dependencies
Write-Host "[4/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "  Dependencies installed!" -ForegroundColor Green

# Step 5: Setup config
Write-Host "[5/5] Configuring Cthulu..." -ForegroundColor Yellow
if (-not (Test-Path "$CTHULU_DIR\config.json")) {
    if (Test-Path "$CTHULU_DIR\config.example.json") {
        Copy-Item "$CTHULU_DIR\config.example.json" "$CTHULU_DIR\config.json"
        Write-Host "  Created config.json from example" -ForegroundColor Green
        Write-Host "  IMPORTANT: Edit config.json with your settings!" -ForegroundColor Red
    }
} else {
    Write-Host "  config.json already exists" -ForegroundColor Green
}

# Cleanup
Remove-Item -Path $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Install MetaTrader 5 manually (requires GUI)"
Write-Host "2. Login to your broker account in MT5"
Write-Host "3. Enable 'Allow Algo Trading' in MT5"
Write-Host "4. Edit C:\cthulu\config.json"
Write-Host "5. Run: python C:\cthulu\__main__.py --wizard"
Write-Host ""
