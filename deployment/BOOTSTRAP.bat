:: ============================================================================
:: CTHULU APEX v5.1 - BOOTSTRAP INSTALLER
:: ============================================================================
:: COPY THIS ENTIRE FILE, PASTE INTO NOTEPAD ON THE VM, SAVE AS install.bat
:: THEN RIGHT-CLICK -> RUN AS ADMINISTRATOR
:: ============================================================================
@echo off
setlocal enabledelayedexpansion
color 0A

echo.
echo  _________   __  .__          .__         
echo  \_   ___ \_/  ^|_^|  ^|__  __ __^|  ^|  __ __ 
echo  /    \  \/\   __\  ^|  \^|  ^|  \  ^| ^|  ^|  \
echo  \     \____^|  ^| ^|   Y  \  ^|  /  ^|_^|  ^|  /
echo   \______  /^|__^| ^|___^|  /____/^|____/____/ 
echo          \/           \/                  
echo.
echo           APEX v5.1 BOOTSTRAP
echo  ========================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo [1/6] Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

echo [2/6] Installing Python 3.10...
call choco install python310 -y

echo [3/6] Installing Git...
call choco install git -y

echo [4/6] Refreshing environment...
call refreshenv

echo [5/6] Creating workspace...
if not exist C:\workspace mkdir C:\workspace
cd /d C:\workspace

echo [6/6] Cloning Cthulu...
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu

echo.
echo Setting up Python environment...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo ========================================
echo  BASIC INSTALLATION COMPLETE!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Install MetaTrader 5 manually from:
echo    https://www.metatrader5.com/en/download
echo.
echo 2. Edit your config:
echo    notepad C:\workspace\cthulu\config.json
echo.
echo 3. Run Cthulu:
echo    cd C:\workspace\cthulu
echo    venv\Scripts\activate
echo    python __main__.py --wizard
echo.
echo ========================================
pause
