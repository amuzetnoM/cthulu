# ============================================================================
# CTHULU APEX v5.1 - ONE-CLICK FULL INSTALLATION SCRIPT
# ============================================================================
# INSTRUCTIONS:
# 1. Open the GCP Windows VM via http://34.171.231.16:8006
# 2. Open PowerShell as Administrator
# 3. Copy this ENTIRE script and paste it into PowerShell
# 4. Press Enter and wait for completion (~15-20 minutes)
# ============================================================================

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Banner
Write-Host @"

_________   __  .__          .__         
\_   ___ \_/  |_|  |__  __ __|  |  __ __ 
/    \  \/\   __\  |  \|  |  \  | |  |  \
\     \____|  | |   Y  \  |  /  |_|  |  /
 \______  /|__| |___|  /____/|____/____/ 
        \/           \/                  

        APEX v5.1 - GCP Auto-Installer
        ================================

"@ -ForegroundColor Cyan

$LogFile = "C:\cthulu_install.log"
function Log { param($msg) $ts = Get-Date -Format "HH:mm:ss"; "$ts - $msg" | Tee-Object -Append $LogFile; Write-Host "[$ts] $msg" -ForegroundColor Green }

Log "Starting Cthulu APEX installation..."

# ============================================================================
# STEP 1: Create directories
# ============================================================================
Log "Creating directories..."
$dirs = @("C:\workspace", "C:\tools", "C:\temp_install")
foreach ($d in $dirs) { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }

# ============================================================================
# STEP 2: Install Chocolatey (Package Manager)
# ============================================================================
Log "Installing Chocolatey package manager..."
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Log "Chocolatey installed successfully"
}
else {
    Log "Chocolatey already installed"
}

# Refresh environment
Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1 -ErrorAction SilentlyContinue
refreshenv 2>$null

# ============================================================================
# STEP 3: Install Python 3.10
# ============================================================================
Log "Installing Python 3.10..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    choco install python310 -y --force
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Log "Python installed"
}
else {
    $pyVer = python --version 2>&1
    Log "Python already installed: $pyVer"
}

# ============================================================================
# STEP 4: Install Git
# ============================================================================
Log "Installing Git..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    choco install git -y --force
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Log "Git installed"
}
else {
    Log "Git already installed"
}

# ============================================================================
# STEP 5: Install VS Code
# ============================================================================
Log "Installing VS Code..."
if (-not (Test-Path "C:\Program Files\Microsoft VS Code\Code.exe")) {
    choco install vscode -y --force
    Log "VS Code installed"
}
else {
    Log "VS Code already installed"
}

# Refresh PATH again
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# ============================================================================
# STEP 6: Download MetaTrader 5
# ============================================================================
Log "Downloading MetaTrader 5..."
$mt5Installer = "C:\temp_install\mt5setup.exe"
$mt5Url = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

if (-not (Test-Path "C:\Program Files\MetaTrader 5\terminal64.exe")) {
    try {
        Invoke-WebRequest -Uri $mt5Url -OutFile $mt5Installer -UseBasicParsing
        Log "MT5 downloaded, starting installation..."
        Start-Process -FilePath $mt5Installer -ArgumentList "/auto" -Wait
        Log "MT5 installation initiated (may require manual completion)"
    }
    catch {
        Log "MT5 auto-download failed. Please download manually from: $mt5Url"
    }
}
else {
    Log "MetaTrader 5 already installed"
}

# ============================================================================
# STEP 7: Clone Cthulu Repository
# ============================================================================
Log "Cloning Cthulu repository..."
$cthuluPath = "C:\workspace\cthulu"

if (Test-Path $cthuluPath) {
    Log "Cthulu directory exists, pulling latest..."
    Set-Location $cthuluPath
    git pull origin main 2>&1 | Out-Null
}
else {
    git clone https://github.com/amuzetnoM/cthulu.git $cthuluPath
    Log "Cthulu cloned successfully"
}

# ============================================================================
# STEP 8: Setup Python Virtual Environment
# ============================================================================
Log "Setting up Python virtual environment..."
Set-Location $cthuluPath

if (-not (Test-Path "$cthuluPath\venv")) {
    python -m venv venv
    Log "Virtual environment created"
}

# Activate and install dependencies
& "$cthuluPath\venv\Scripts\Activate.ps1"
Log "Installing Python dependencies (this may take a few minutes)..."
pip install --upgrade pip 2>&1 | Out-Null
pip install -r requirements.txt 2>&1 | Out-Null
Log "Dependencies installed"

# ============================================================================
# STEP 9: Create Default Configuration
# ============================================================================
Log "Setting up configuration..."
$configPath = "$cthuluPath\config.json"

if (-not (Test-Path $configPath)) {
    if (Test-Path "$cthuluPath\config.example.json") {
        Copy-Item "$cthuluPath\config.example.json" $configPath
        Log "Config created from example"
    }
    else {
        # Create minimal config
        @"
{
    "mt5": {
        "login": 0,
        "password": "",
        "server": ""
    },
    "trading": {
        "symbol": "BTCUSD#",
        "mindset": "dynamic",
        "timeframe": "M5",
        "lot_size": 0.01,
        "max_positions": 3
    },
    "risk": {
        "max_daily_loss_pct": 5.0,
        "max_drawdown_pct": 10.0
    }
}
"@ | Out-File -FilePath $configPath -Encoding UTF8
        Log "Default config created - EDIT BEFORE RUNNING"
    }
}

# ============================================================================
# STEP 10: Create Desktop Shortcuts
# ============================================================================
Log "Creating desktop shortcuts..."
$desktop = [Environment]::GetFolderPath("Desktop")

# Cthulu Wizard shortcut
$wizardShortcut = @"
@echo off
cd /d C:\workspace\cthulu
call venv\Scripts\activate.bat
python __main__.py --wizard
pause
"@
$wizardShortcut | Out-File -FilePath "$desktop\Cthulu Wizard.bat" -Encoding ASCII

# Cthulu Direct Launch shortcut
$directShortcut = @"
@echo off
cd /d C:\workspace\cthulu
call venv\Scripts\activate.bat
python __main__.py --config config.json
pause
"@
$directShortcut | Out-File -FilePath "$desktop\Cthulu Launch.bat" -Encoding ASCII

# Sentinel shortcut
$sentinelShortcut = @"
@echo off
cd /d C:\workspace\sentinel
call ..\cthulu\venv\Scripts\activate.bat
python sentinel_gui.py
"@
if (Test-Path "C:\workspace\sentinel") {
    $sentinelShortcut | Out-File -FilePath "$desktop\Sentinel Monitor.bat" -Encoding ASCII
}

Log "Desktop shortcuts created"

# ============================================================================
# STEP 11: Verify Installation
# ============================================================================
Log ""
Log "============================================"
Log "       INSTALLATION VERIFICATION"
Log "============================================"

$checks = @(
    @{Name = "Python"; Check = { python --version 2>&1 } },
    @{Name = "Git"; Check = { git --version 2>&1 } },
    @{Name = "Cthulu"; Check = { if (Test-Path "C:\workspace\cthulu\__main__.py") { "Found" }else { "NOT FOUND" } } },
    @{Name = "Venv"; Check = { if (Test-Path "C:\workspace\cthulu\venv") { "Created" }else { "NOT FOUND" } } },
    @{Name = "Config"; Check = { if (Test-Path "C:\workspace\cthulu\config.json") { "Present" }else { "NOT FOUND" } } },
    @{Name = "MT5"; Check = { if (Test-Path "C:\Program Files\MetaTrader 5\terminal64.exe") { "Installed" }else { "NOT FOUND - Install manually" } } }
)

foreach ($c in $checks) {
    $result = & $c.Check
    Write-Host "  $($c.Name): $result" -ForegroundColor $(if ($result -match "NOT") { Red }else { Green })
}

# ============================================================================
# COMPLETION
# ============================================================================
Log ""
Log "============================================"
Log "       INSTALLATION COMPLETE!"  
Log "============================================"
Write-Host @"

NEXT STEPS:
-----------
1. If MT5 didn't auto-install, download from:
   https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

2. Login to your MT5 account and ENABLE ALGO TRADING:
   Tools -> Options -> Expert Advisors -> Allow algorithmic trading

3. Edit your trading configuration:
   notepad C:\workspace\cthulu\config.json

4. Launch Cthulu:
   - Double-click 'Cthulu Wizard.bat' on Desktop, OR
   - Double-click 'Cthulu Launch.bat' for direct start

5. For monitoring, launch 'Sentinel Monitor.bat'

Log saved to: $LogFile

"@ -ForegroundColor Yellow

# Open config for editing
Write-Host "Opening config.json for editing..." -ForegroundColor Cyan
Start-Process notepad -ArgumentList "C:\workspace\cthulu\config.json"

Log "Script completed at $(Get-Date)"
