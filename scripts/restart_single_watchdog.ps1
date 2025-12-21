# Kill any existing watchdog instances and start a single detached watchdog
$existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*run_herald_watchdog.ps1*' }
if ($existing) {
    $pids = $existing | Select-Object -ExpandProperty ProcessId
    Write-Output "Killing existing watchdog PIDs: $($pids -join ', ')"
    foreach ($id in $pids) {
        try { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 200 } catch {}
    }
}
# Start a single detached watchdog
$script = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) 'run_herald_watchdog.ps1'
Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-WindowStyle','Hidden','-File',$script -PassThru | ForEach-Object { Write-Output "Started watchdog PID: $($_.Id)" }
