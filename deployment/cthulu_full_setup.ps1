<#
.SYNOPSIS
    Cthulu Complete VM Setup - One Script Does Everything
.DESCRIPTION
    Downloads and installs all dependencies, MT5, Python, Git, VS Code Server,
    and Cthulu trading system. Run this script as Administrator on a fresh Windows VM.
.NOTES
    Version: 5.1.0 APEX
    Run: Right-click -> Run with PowerShell (as Administrator)
#>

param(
    [string]$CthulRepoUrl = "https://github.com/amuzetnoM/cthulu.git",
    [string]$InstallPath = "C:\Cthulu",
    [string]$MT5Account = "",
    [string]$MT5Password = "",
    [string]$MT5Server = ""
)

# ============================================================================
# CONFIGURATION
# ============================================================================
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$PYTHON_VERSION = "3.11.7"
$PYTHON_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
$MT5_URL = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
$VSCODE_SERVER_URL = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64"

$LogFile = "$env:TEMP\cthulu_setup_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $(switch($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } "SUCCESS" { "Green" } default { "White" } })
    Add-Content -Path $LogFile -Value $logMessage
}

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Download-File {
    param([string]$Url, [string]$OutFile)
    Write-Log "Downloading: $Url"
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
        Write-Log "Downloaded: $OutFile" "SUCCESS"
    } catch {
        Write-Log "Failed to download $Url : $_" "ERROR"
        throw
    }
}

function Install-Silently {
    param([string]$Installer, [string]$Args, [string]$Name)
    Write-Log "Installing $Name..."
    $process = Start-Process -FilePath $Installer -ArgumentList $Args -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
        Write-Log "$Name installed successfully" "SUCCESS"
    } else {
        Write-Log "$Name installation failed with exit code: $($process.ExitCode)" "WARN"
    }
}

# ============================================================================
# BANNER
# ============================================================================
Clear-Host
Write-Host @"

    _________   __  .__          .__         
    \_   ___ \_/  |_|  |__  __ __|  |  __ __ 
    /    \  \/\   __\  |  \|  |  \  | |  |  \
    \     \____|  | |   Y  \  |  /  |_|  |  /
     \______  /|__| |___|  /____/|____/____/ 
            \/           \/                  
    
    APEX v5.1.0 - Complete VM Setup
    ================================
    
"@ -ForegroundColor Cyan

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================
Write-Log "Starting Cthulu Complete Setup"
Write-Log "Log file: $LogFile"

if (-not (Test-Admin)) {
    Write-Log "This script requires Administrator privileges. Please run as Administrator." "ERROR"
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Create directories
$DownloadDir = "$env:TEMP\cthulu_setup"
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null

Write-Log "Installation path: $InstallPath"
Write-Log "Download cache: $DownloadDir"

# ============================================================================
# STEP 1: INSTALL PYTHON
# ============================================================================
Write-Host "`n[1/6] Installing Python $PYTHON_VERSION..." -ForegroundColor Yellow

$pythonInstaller = "$DownloadDir\python_installer.exe"
$pythonInstalled = $false

# Check if Python already installed
try {
    $pyVersion = & python --version 2>&1
    if ($pyVersion -match "Python 3\.(10|11|12)") {
        Write-Log "Python already installed: $pyVersion" "SUCCESS"
        $pythonInstalled = $true
    }
} catch {}

if (-not $pythonInstalled) {
    Download-File -Url $PYTHON_URL -OutFile $pythonInstaller
    Install-Silently -Installer $pythonInstaller -Args "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_tcltk=1" -Name "Python"
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# ============================================================================
# STEP 2: INSTALL GIT
# ============================================================================
Write-Host "`n[2/6] Installing Git..." -ForegroundColor Yellow

$gitInstaller = "$DownloadDir\git_installer.exe"
$gitInstalled = $false

try {
    $gitVersion = & git --version 2>&1
    if ($gitVersion -match "git version") {
        Write-Log "Git already installed: $gitVersion" "SUCCESS"
        $gitInstalled = $true
    }
} catch {}

if (-not $gitInstalled) {
    Download-File -Url $GIT_URL -OutFile $gitInstaller
    Install-Silently -Installer $gitInstaller -Args "/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS=icons,ext\reg\shellhere,assoc,assoc_sh" -Name "Git"
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# ============================================================================
# STEP 3: INSTALL METATRADER 5
# ============================================================================
Write-Host "`n[3/6] Installing MetaTrader 5..." -ForegroundColor Yellow

$mt5Installer = "$DownloadDir\mt5setup.exe"
$mt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"

if (Test-Path $mt5Path) {
    Write-Log "MetaTrader 5 already installed" "SUCCESS"
} else {
    Download-File -Url $MT5_URL -OutFile $mt5Installer
    Write-Log "Running MT5 installer (follow the wizard if it appears)..."
    Start-Process -FilePath $mt5Installer -ArgumentList "/auto" -Wait
    Write-Log "MT5 installation initiated" "SUCCESS"
}

# ============================================================================
# STEP 4: CLONE CTHULU REPOSITORY
# ============================================================================
Write-Host "`n[4/6] Setting up Cthulu Repository..." -ForegroundColor Yellow

$cthulPath = "$InstallPath\cthulu"

if (Test-Path "$cthulPath\.git") {
    Write-Log "Cthulu repo exists, pulling latest..."
    Push-Location $cthulPath
    & git pull origin main 2>&1 | Out-Null
    Pop-Location
    Write-Log "Repository updated" "SUCCESS"
} else {
    Write-Log "Cloning Cthulu repository..."
    & git clone $CthulRepoUrl $cthulPath 2>&1
    Write-Log "Repository cloned" "SUCCESS"
}

# ============================================================================
# STEP 5: INSTALL PYTHON DEPENDENCIES
# ============================================================================
Write-Host "`n[5/6] Installing Python Dependencies..." -ForegroundColor Yellow

Push-Location $cthulPath

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Log "Creating virtual environment..."
    & python -m venv venv
}

# Activate and install
Write-Log "Installing requirements..."
& .\venv\Scripts\python.exe -m pip install --upgrade pip 2>&1 | Out-Null
& .\venv\Scripts\pip.exe install -r requirements.txt 2>&1

Write-Log "Dependencies installed" "SUCCESS"
Pop-Location

# ============================================================================
# STEP 6: CONFIGURE CTHULU
# ============================================================================
Write-Host "`n[6/6] Configuring Cthulu..." -ForegroundColor Yellow

$configPath = "$cthulPath\config.json"
$exampleConfig = "$cthulPath\config.example.json"

if (-not (Test-Path $configPath)) {
    if (Test-Path $exampleConfig) {
        Copy-Item $exampleConfig $configPath
        Write-Log "Created config.json from example"
    }
}

# Create desktop shortcuts
$WshShell = New-Object -ComObject WScript.Shell

# Wizard shortcut
$shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Cthulu Wizard.lnk")
$shortcut.TargetPath = "$cthulPath\venv\Scripts\python.exe"
$shortcut.Arguments = "__main__.py --wizard"
$shortcut.WorkingDirectory = $cthulPath
$shortcut.IconLocation = "$cthulPath\assets\icon.ico,0"
$shortcut.Description = "Cthulu Trading System - APEX v5.1"
$shortcut.Save()

# Sentinel shortcut
$shortcut2 = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Cthulu Sentinel.lnk")
$shortcut2.TargetPath = "powershell.exe"
$shortcut2.Arguments = "-ExecutionPolicy Bypass -File `"C:\workspace\sentinel\sentinel_gui.py`""
$shortcut2.WorkingDirectory = "C:\workspace\sentinel"
$shortcut2.Description = "Cthulu Sentinel - Crash Recovery"
$shortcut2.Save()

Write-Log "Desktop shortcuts created" "SUCCESS"

# ============================================================================
# SETUP VS CODE SERVER (Optional - for remote development)
# ============================================================================
Write-Host "`n[Bonus] Setting up VS Code Server..." -ForegroundColor Yellow

$codeServerDir = "$InstallPath\code-server"
New-Item -ItemType Directory -Force -Path $codeServerDir | Out-Null

# Create code-server setup script
$codeServerScript = @'
# VS Code Server Setup
# Run: code tunnel --accept-server-license-terms
# This enables remote VS Code connections

Write-Host "To enable VS Code remote access:"
Write-Host "1. Open VS Code on this machine"
Write-Host "2. Install 'Remote - Tunnels' extension"
Write-Host "3. Run: code tunnel --accept-server-license-terms"
Write-Host "4. Follow authentication prompts"
Write-Host ""
Write-Host "Or use GitHub Codespaces for cloud-based development"
'@
Set-Content -Path "$codeServerDir\setup_tunnel.ps1" -Value $codeServerScript

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Host @"

============================================================================
                    CTHULU SETUP COMPLETE!
============================================================================

"@ -ForegroundColor Green

Write-Host "Installation Summary:" -ForegroundColor Cyan
Write-Host "  - Python:      Installed & configured"
Write-Host "  - Git:         Installed & configured"
Write-Host "  - MetaTrader5: Installed (configure account manually)"
Write-Host "  - Cthulu:      $cthulPath"
Write-Host "  - Virtual Env: $cthulPath\venv"
Write-Host ""
Write-Host "Desktop Shortcuts Created:" -ForegroundColor Cyan
Write-Host "  - Cthulu Wizard (double-click to start)"
Write-Host "  - Cthulu Sentinel (crash recovery)"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open MetaTrader 5 and login to your broker account"
Write-Host "  2. Enable 'Algo Trading' in MT5 (Tools > Options > Expert Advisors)"
Write-Host "  3. Double-click 'Cthulu Wizard' on desktop to configure and start"
Write-Host ""
Write-Host "Log file: $LogFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
