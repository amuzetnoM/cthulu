@echo off
REM Cthulu VM Bootstrap - Run this in the Windows VM
REM Copy this entire script to the VM and run it

echo.
echo ========================================
echo    CTHULU VM BOOTSTRAP - APEX v5.1.0
echo ========================================
echo.

REM Create workspace
if not exist "C:\workspace" mkdir C:\workspace
cd C:\workspace

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Please install Python 3.10+ first.
    echo     Download from: https://www.python.org/downloads/
    echo     IMPORTANT: Check "Add Python to PATH" during install!
    pause
    exit /b 1
)

REM Check for Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [!] Git not found. Please install Git first.
    echo     Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/4] Cloning Cthulu repository...
if exist "C:\workspace\cthulu" (
    cd cthulu
    git pull origin main
) else (
    git clone https://github.com/amuzetnoM/cthulu.git
    cd cthulu
)

echo [2/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Cloning Sentinel...
cd C:\workspace
if exist "C:\workspace\sentinel" (
    cd sentinel
    git pull origin main
) else (
    git clone https://github.com/amuzetnoM/sentinel.git 2>nul || (
        echo Creating local sentinel...
        mkdir sentinel
    )
)

echo [4/4] Setting up configuration...
cd C:\workspace\cthulu
if not exist "config.json" (
    if exist "config.example.json" (
        copy config.example.json config.json
        echo Created config.json - EDIT THIS FILE before trading!
    )
)

echo.
echo ========================================
echo    BOOTSTRAP COMPLETE!
echo ========================================
echo.
echo NEXT STEPS:
echo   1. Install MetaTrader 5 from metatrader5.com
echo   2. Log into your broker account in MT5
echo   3. Enable "Allow Algo Trading" in MT5
echo   4. Edit C:\workspace\cthulu\config.json
echo   5. Run: python __main__.py --wizard
echo.
pause
