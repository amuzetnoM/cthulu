param(
    [int]$DurationMinutes = 120,
    [string]$MindsetConfig = "config_ultra_aggressive.json",
    [string]$CthuluDir = "C:\workspace\cthulu",
    [string]$PythonExe = "python",
    [string]$InjectionMode = "realistic",  # realistic, burst, indicator
    [string]$Intensity = "medium",         # low, medium, high (for realistic mode)
    [int]$BurstCount = 200,
    [int]$BurstRate = 10
)

Write-Host "============================================="
Write-Host "  CTHULU STRESS TEST - ENHANCED VERSION"
Write-Host "============================================="
Write-Host "Duration: $DurationMinutes minutes"
Write-Host "Injection Mode: $InjectionMode"
Write-Host "Intensity: $Intensity"
Write-Host "Mindset: $MindsetConfig"
Write-Host "============================================="

# Save current config
$cfg = Join-Path $CthuluDir "config.json"
$backup = Join-Path $CthuluDir "config.json.bak"
Copy-Item $cfg $backup -Force

# Replace with ultra-aggressive
Copy-Item (Join-Path $CthuluDir $MindsetConfig) $cfg -Force

# Restart Cthulu
function Stop-Cthulu() {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match '\-m\s+cthulu') }
    foreach ($p in $procs) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch { } }
}

Stop-Cthulu
Start-Sleep -Seconds 2

# Start Cthulu
$proc = Start-Process -FilePath $PythonExe -ArgumentList "-m cthulu --config config.json --mindset ultra_aggressive --skip-setup" -WorkingDirectory $CthuluDir -PassThru
$cthuluPid = $proc.Id
Write-Host "Started Cthulu (PID $cthuluPid) with mindset $MindsetConfig (RPC enabled)"
Start-Sleep -Seconds 6

# Verify Cthulu started and RPC is up
$maxRetries = 10
$rpcReady = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8278/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $rpcReady = $true
            Write-Host "RPC server is ready!"
            break
        }
    }
    catch {
        Write-Host "Waiting for RPC server... (attempt $($i + 1)/$maxRetries)"
        Start-Sleep -Seconds 3
    }
}

if (-not $rpcReady) {
    Write-Host "WARNING: RPC server may not be ready. Continuing anyway..."
}

# Kick off collector if not running
if (-not (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'collect_metrics.ps1') })) {
    Start-Process -FilePath pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File monitoring\collect_metrics.ps1 -IntervalSeconds 10 -DurationMinutes $DurationMinutes" -WorkingDirectory $CthuluDir -PassThru | Out-Null
    Write-Host "Started metrics collector"
}

# Run injection based on mode
Write-Host ""
Write-Host "Starting signal injection in '$InjectionMode' mode..."

switch ($InjectionMode) {
    "realistic" {
        # Realistic market simulation - spreads signals over the duration with varying market conditions
        $injectorArgs = "monitoring\inject_signals.py --mode realistic --duration $DurationMinutes --intensity $Intensity --symbol BTCUSD#"
        Write-Host "Realistic mode: Simulating changing market conditions over $DurationMinutes minutes"
    }
    "burst" {
        # Traditional burst mode - rapid fire signals
        $injectorArgs = "monitoring\inject_signals.py --mode burst --count $BurstCount --rate $BurstRate --symbol BTCUSD#"
        Write-Host "Burst mode: Injecting $BurstCount signals at $BurstRate/sec"
    }
    "indicator" {
        # Run through all indicator types
        $indicators = @("rsi_oversold", "rsi_overbought", "rsi_divergence", "macd_crossover_bull", "macd_crossover_bear", "bollinger_squeeze", "ema_crossover", "adx_strong_trend", "supertrend_flip", "momentum_breakout")
        Write-Host "Indicator mode: Testing all indicator signal types"
        
        foreach ($indicator in $indicators) {
            Write-Host "  Testing indicator: $indicator"
            Start-Process -FilePath $PythonExe -ArgumentList "monitoring\inject_signals.py --mode indicator --indicator $indicator --count 10 --symbol BTCUSD#" -WorkingDirectory $CthuluDir -Wait -NoNewWindow
            Start-Sleep -Seconds 5
        }
        
        # After indicator tests, continue with realistic mode for remaining time
        $remainingMinutes = $DurationMinutes - 15  # Assume indicator tests take ~15 min
        if ($remainingMinutes -gt 0) {
            $injectorArgs = "monitoring\inject_signals.py --mode realistic --duration $remainingMinutes --intensity $Intensity --symbol BTCUSD#"
        }
        else {
            $injectorArgs = $null
        }
    }
    default {
        $injectorArgs = "monitoring\inject_signals.py --mode realistic --duration $DurationMinutes --intensity $Intensity --symbol BTCUSD#"
    }
}

if ($injectorArgs) {
    Start-Process -FilePath $PythonExe -ArgumentList $injectorArgs -WorkingDirectory $CthuluDir -NoNewWindow -PassThru | Out-Null
}

Write-Host ""
Write-Host "============================================="
Write-Host "Stress test running for $DurationMinutes minutes..."
Write-Host "Cthulu PID: $cthuluPid"
Write-Host ""
Write-Host "Monitor live output:"
Write-Host "  - Cthulu logs: Get-Content logs\cthulu.log -Wait"
Write-Host "  - Injection logs: Get-Content logs\inject.log -Wait"
Write-Host "  - Dual monitor: run monitoring\dual_monitor.bat"
Write-Host "============================================="

# Wait for duration
Start-Sleep -Seconds ($DurationMinutes * 60)

# Restore config and restart
Write-Host ""
Write-Host "Stress test complete! Restoring configuration..."
Copy-Item $backup $cfg -Force
Stop-Cthulu
Start-Sleep -Seconds 2
Start-Process -FilePath $PythonExe -ArgumentList "-m cthulu --config config.json --skip-setup" -WorkingDirectory $CthuluDir -PassThru | Out-Null

Write-Host "============================================="
Write-Host "STRESS TEST FINISHED"
Write-Host "Config restored and system restarted"
Write-Host ""
Write-Host "Artifacts:"
Write-Host "  - Metrics: monitoring/metrics.csv"
Write-Host "  - Reports: SYSTEM_REPORT.md, monitoring/monitoring_report.md"
Write-Host "  - Logs: logs/cthulu.log, logs/inject.log"
Write-Host "============================================="