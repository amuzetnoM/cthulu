@echo off
title Cthulu APEX v5.1 - Complete Setup
color 0A

echo.
echo     _________   __  .__          .__         
echo     \_   ___ \_/  ^|_^|  ^|__  __ __^|  ^|  __ __ 
echo     /    \  \/\   __\  ^|  \^|  ^|  \  ^| ^|  ^|  \
echo     \     \____^|  ^| ^|   Y  \  ^|  /  ^|_^|  ^|  /
echo      \______  /^|__^| ^|___^|  /____/^|____/____/ 
echo             \/           \/                  
echo.
echo     APEX v5.1.0 - One-Click Setup
echo     ==============================
echo.

echo Launching PowerShell setup script...
echo This will install Python, Git, MT5, and Cthulu automatically.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0cthulu_full_setup.ps1"

pause
