@echo off
REM Dual-pane monitor: Left=Cthulu trading logs, Right=Injection responses
REM Opens two PowerShell windows side-by-side

REM Start Cthulu log tail (left pane)
start "Cthulu Trading Logs" powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'CTHULU TRADING LOGS' -ForegroundColor Cyan; Write-Host '===================' -ForegroundColor Cyan; Get-Content 'C:\workspace\cthulu\logs\Cthulu.log' -Wait -Tail 100"

REM Start injection log tail (right pane)
start "Injection Monitor" powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'SIGNAL INJECTION MONITOR' -ForegroundColor Yellow; Write-Host '========================' -ForegroundColor Yellow; if (Test-Path 'C:\workspace\cthulu\logs\inject.log') { Get-Content 'C:\workspace\cthulu\logs\inject.log' -Wait -Tail 100 } else { Write-Host 'Waiting for inject.log to be created...'; while (-not (Test-Path 'C:\workspace\cthulu\logs\inject.log')) { Start-Sleep -Seconds 2 }; Get-Content 'C:\workspace\cthulu\logs\inject.log' -Wait -Tail 100 }"

echo Dual monitor started. Close windows manually when done.
