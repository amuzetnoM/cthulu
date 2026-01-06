@echo off
REM Cthulu Backtesting UI - Quick Start Script
REM Activates integration and starts backend

echo ================================================================================
echo CTHULU BACKTESTING UI - QUICK START
echo ================================================================================
echo.

echo Step 1: Activating UI Integration...
python scripts\activate_ui_integration.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to activate integration
    pause
    exit /b 1
)

echo.
echo Step 2: Starting Backend Server...
echo.
echo Backend will start on http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
echo Opening UI in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start backend in background
start "Cthulu Backend" python backtesting\ui_server.py

REM Wait a moment for server to start
timeout /t 2 /nobreak >nul

REM Open UI in default browser
start backtesting\ui\index.html

echo.
echo ================================================================================
echo UI opened in browser!
echo Backend running in separate window
echo.
echo Look for the green "Backend Connected" indicator in the top-right
echo.
echo To stop:
echo   - Close this window
echo   - Close the "Cthulu Backend" window
echo ================================================================================
echo.

pause
