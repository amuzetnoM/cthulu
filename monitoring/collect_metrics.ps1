param(
    [int]$IntervalSeconds = 10,
    [int]$DurationMinutes = 90,
    [string]$LogPath = "logs\cthulu.log",
    [string]$ReportPath = "SYSTEM_REPORT.md",
    [string]$CsvPath = "monitoring\metrics.csv"
)

$endTime = (Get-Date).AddMinutes($DurationMinutes)
if (-not (Test-Path (Split-Path $CsvPath -Parent))) { New-Item -ItemType Directory -Path (Split-Path $CsvPath -Parent) | Out-Null }
if (-not (Test-Path $CsvPath)) {
    "timestamp,pids,cpu_delta_s,mem_mb,errors_delta,errors_total,trades_delta,trades_total,restarts_total,log_bytes" | Out-File -FilePath $CsvPath -Encoding utf8
}

$lastErrorTotal = 0
$lastTradeTotal = 0
$lastLogBytes = 0
$lastCpuTimes = @{}

function Count-InLog([string]$pattern) {
    if (-not (Test-Path $LogPath)) { return 0 }
    try {
        (Select-String -Path $LogPath -Pattern $pattern -SimpleMatch -Quiet -List) | Out-Null
        # select-string -Quiet doesn't return count; use full search for counts
        return (Select-String -Path $LogPath -Pattern $pattern -SimpleMatch | Measure-Object).Count
    }
    catch {
        return 0
    }
}

function Count-Restarts() {
    if (-not (Test-Path $ReportPath)) { return 0 }
    try {
        return (Select-String -Path $ReportPath -Pattern "Restarted" | Measure-Object).Count
    }
    catch { return 0 }
}

while ((Get-Date) -lt $endTime) {
    $ts = (Get-Date).ToString("o")
    # find cthulu python process(es)
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match '\-m\s+cthulu') }
    $pids = $procs | ForEach-Object { $_.ProcessId } | Sort-Object | ForEach-Object { $_ } -join ";"

    $cpuDeltaTotal = 0.0
    $memTotalMb = 0
    foreach ($p in $procs) {
        try {
            $ps = Get-Process -Id $p.ProcessId -ErrorAction Stop
            $curCpu = [double]$ps.CPU
            if (-not $lastCpuTimes.ContainsKey($p.ProcessId)) { $lastCpuTimes[$($p.ProcessId)] = $curCpu }
            $deltaCpu = $curCpu - $lastCpuTimes[$($p.ProcessId)]
            $lastCpuTimes[$($p.ProcessId)] = $curCpu
            $cpuDeltaTotal += $deltaCpu
            $memTotalMb += [math]::Round($ps.WorkingSet64 / 1MB, 2)
        }
        catch {
            # process may have exited
        }
    }

    $errorsTotal = Count-InLog "ERROR"
    $errorsDelta = $errorsTotal - $lastErrorTotal
    $lastErrorTotal = $errorsTotal

    # trades identified by 'Order executed' or 'Placing MARKET order' messages in logs
    $tradePatterns = "Order executed", "Placing MARKET order", "Order filled"
    $tradeTotal = 0
    foreach ($pat in $tradePatterns) { $tradeTotal += Count-InLog $pat }
    $tradeDelta = $tradeTotal - $lastTradeTotal
    $lastTradeTotal = $tradeTotal

    $restartTotal = Count-Restarts

    $logBytes = 0
    if (Test-Path $LogPath) { $logBytes = (Get-Item $LogPath).Length }
    $logBytesDelta = $logBytes - $lastLogBytes
    $lastLogBytes = $logBytes

    # write CSV line
    $line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}" -f $ts, ($pids -replace ',', ';'), [math]::Round($cpuDeltaTotal, 3), $memTotalMb, $errorsDelta, $errorsTotal, $tradeDelta, $tradeTotal, $restartTotal, $logBytes
    Add-Content -Path $CsvPath -Value $line

    Start-Sleep -Seconds $IntervalSeconds
}

Write-Output "Metrics collection finished; csv at $CsvPath" | Out-File -FilePath monitoring\collector_done.log -Append -Encoding utf8
