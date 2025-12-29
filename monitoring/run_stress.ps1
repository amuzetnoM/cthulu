param(
    [int]$DurationMinutes = 60,
    [string]$MindsetConfig = "config_ultra_aggressive.json",
    [string]$CthuluDir = "C:\workspace\cthulu",
    [string]$PythonExe = "python",
    [int]$BurstCount = 200,
    [int]$BurstRate = 10
)

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
$proc = Start-Process -FilePath $PythonExe -ArgumentList "-m cthulu --config config.json --enable-rpc --rpc-port 8278" -WorkingDirectory $CthuluDir -PassThru
Write-Host "Started Cthulu (PID $($proc.Id)) with mindset $MindsetConfig (RPC enabled)"
Start-Sleep -Seconds 6

# Kick off collector and monitor if not running
if (-not (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'collect_metrics.ps1') })) {
    Start-Process -FilePath pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File monitoring\collect_metrics.ps1 -IntervalSeconds 10 -DurationMinutes $DurationMinutes" -WorkingDirectory $CthuluDir -PassThru | Out-Null
}
if (-not (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'monitor_cthulu.ps1') })) {
    Start-Process -FilePath pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File scripts\monitor_cthulu.ps1 -RequiredSteadyMinutes 60 -MaxTotalMinutes ($DurationMinutes + 30) -PythonExe python" -WorkingDirectory $CthuluDir -PassThru | Out-Null
}

# Run burst injector
Start-Process -FilePath $PythonExe -ArgumentList "monitoring\inject_signals.py --mode burst --count $BurstCount --rate $BurstRate --symbol BTCUSD#" -WorkingDirectory $CthuluDir -NoNewWindow -PassThru | Out-Null

Write-Host "Stress test started; running for $DurationMinutes minutes..."
Start-Sleep -Seconds ($DurationMinutes * 60)

# Restore config and restart
Copy-Item $backup $cfg -Force
Stop-Cthulu
Start-Sleep -Seconds 2
Start-Process -FilePath $PythonExe -ArgumentList "-m cthulu --config config.json --enable-rpc --rpc-port 8278" -WorkingDirectory $CthuluDir -PassThru | Out-Null
Write-Host "Stress test finished; config restored and system restarted (RPC enabled). Artifacts: monitoring/metrics.csv and SYSTEM_REPORT.md"