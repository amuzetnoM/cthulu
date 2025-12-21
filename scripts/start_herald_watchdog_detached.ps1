# Starts the watchdog script in a detached PowerShell process
$script = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) 'run_herald_watchdog.ps1'
# Check for existing watchdog processes to avoid duplicates
$existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like "*run_herald_watchdog.ps1*" }
if ($existing) {
    $pids = ($existing | Select-Object -ExpandProperty ProcessId) -join ', '
    Write-Output "Watchdog already running (PIDs: $pids). Not starting another."
    exit 0
}

$p = Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile","-WindowStyle","Hidden","-File","$script" -PassThru
Write-Output "Started detached watchdog: PID $($p.Id)"