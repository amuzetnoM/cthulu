# Phase 2 - Balanced Mode Stress Test
# Duration: 60 minutes
# Mindset: balanced (M15 timeframe)

param(
    [int]$DurationMinutes = 60
)

$ErrorActionPreference = "Continue"
$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CTHULU PHASE 2 - BALANCED MODE TEST" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Start Time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "Target End: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "Duration: $DurationMinutes minutes"
Write-Host ""

# Check MT5
$mt5 = Get-Process -Name terminal64 -ErrorAction SilentlyContinue
if (-not $mt5) {
    Write-Host "[ERROR] MT5 is not running. Please start MT5 first." -ForegroundColor Red
    Write-Host "Looking for MT5 in common locations..."
    
    $mt5Paths = @(
        "$env:ProgramFiles\MetaTrader 5\terminal64.exe",
        "${env:ProgramFiles(x86)}\MetaTrader 5\terminal64.exe",
        "$env:LOCALAPPDATA\Programs\MetaTrader 5\terminal64.exe"
    )
    
    foreach ($path in $mt5Paths) {
        if (Test-Path $path) {
            Write-Host "Found MT5 at: $path" -ForegroundColor Yellow
            Write-Host "Starting MT5..."
            Start-Process $path
            Start-Sleep -Seconds 10
            break
        }
    }
    
    $mt5 = Get-Process -Name terminal64 -ErrorAction SilentlyContinue
    if (-not $mt5) {
        Write-Host "[FATAL] Could not start MT5. Please start manually." -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] MT5 running (PID: $($mt5.Id))" -ForegroundColor Green

# Copy balanced config to main config
$balancedConfig = "C:\workspace\cthulu\configs\mindsets\balanced\config_balanced_m15.json"
$mainConfig = "C:\workspace\cthulu\config.json"

if (Test-Path $balancedConfig) {
    Write-Host "Applying balanced mindset configuration..."
    Copy-Item $balancedConfig $mainConfig -Force
    Write-Host "[OK] Balanced config applied" -ForegroundColor Green
} else {
    Write-Host "[WARN] Balanced config not found, using current config" -ForegroundColor Yellow
}

# Start Cthulu
Write-Host ""
Write-Host "Starting Cthulu in balanced mode..." -ForegroundColor Yellow
Set-Location "C:\workspace\cthulu"

# Start in background
$cthuluProcess = Start-Process -FilePath "python" -ArgumentList "-m cthulu --config config.json --skip-setup" -PassThru -NoNewWindow
Write-Host "[OK] Cthulu started (PID: $($cthuluProcess.Id))" -ForegroundColor Green

# Record start
$startRecord = @{
    phase = 2
    mindset = "balanced"
    start_time = $startTime.ToString("o")
    cthulu_pid = $cthuluProcess.Id
    mt5_pid = $mt5.Id
    duration_target = $DurationMinutes
}
$startRecord | ConvertTo-Json | Out-File "C:\workspace\cthulu\monitoring\phase2_session.json"

Write-Host ""
Write-Host "Phase 2 started successfully!" -ForegroundColor Green
Write-Host "Monitor logs: Get-Content C:\workspace\cthulu\logs\cthulu.log -Tail 50 -Wait"
Write-Host "Cthulu PID: $($cthuluProcess.Id)"
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (Cthulu will continue running)"
Write-Host ""

# Monitor loop
$loopCount = 0
while ((Get-Date) -lt $endTime) {
    $loopCount++
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    $remaining = [math]::Round(($endTime - (Get-Date)).TotalMinutes, 1)
    
    # Check if Cthulu is still running
    $cthuluProc = Get-Process -Id $cthuluProcess.Id -ErrorAction SilentlyContinue
    if (-not $cthuluProc) {
        Write-Host "[ERROR] Cthulu process died! Restarting..." -ForegroundColor Red
        $cthuluProcess = Start-Process -FilePath "python" -ArgumentList "-m cthulu --config config.json --skip-setup" -PassThru -NoNewWindow
        Write-Host "[OK] Restarted (New PID: $($cthuluProcess.Id))" -ForegroundColor Yellow
    }
    
    # Status update every minute
    if ($loopCount % 6 -eq 0) {
        Write-Host "[$($elapsed)m / $($DurationMinutes)m] Phase 2 running... $($remaining)m remaining" -ForegroundColor Cyan
    }
    
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  PHASE 2 COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Duration: $DurationMinutes minutes"
Write-Host "End Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
