param(
    [string]$PythonPath = "C:\Users\alish\AppData\Local\Programs\Python\Python312\python.exe",
    [string]$Config = "config.json",
    [string]$Symbol = "BTCUSD#m",
    [int]$MaxRestarts = 100,
    [int]$RestartDelaySeconds = 5,
    [string]$LogFile = "./herald_watchdog.log",
    [string]$PidFile = "./herald.pid",
    [string]$HeraldLogLevel = "INFO"
)

# Derive robust absolute paths based on the script location so the daemon
# is not sensitive to the process working directory used when launched.
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path $ScriptRoot -Parent
if ($LogFile -eq "./herald_watchdog.log") { $LogFile = Join-Path $RepoRoot 'herald_watchdog.log' }
if ($PidFile -eq "./herald.pid") { $PidFile = Join-Path $RepoRoot 'herald.pid' }

# Enforce single watchdog instance: if another watchdog is already running, exit gracefully
try {
    $me = $PID
    $otherWatchdogs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like "*run_herald_watchdog.ps1*" -and $_.ProcessId -ne $me }
    if ($otherWatchdogs) {
        $pids = ($otherWatchdogs | Select-Object -ExpandProperty ProcessId) -join ', '
        Write-Output "Another watchdog instance detected (PIDs: $pids). Exiting to avoid duplicates."
        exit 0
    }

    # Detect if running under VS Code integrated terminal (ancestor Code.exe)
    try {
        $parent = (Get-CimInstance Win32_Process -Filter "ProcessId=$me" | Select-Object -ExpandProperty ParentProcessId)
        $ancestor = $parent
        while ($ancestor) {
            $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ancestor" -ErrorAction SilentlyContinue
            if (-not $p) { break }
            if ($p.CommandLine -and $p.CommandLine -match 'Code.exe') {
                Write-Host "Detected VS Code ancestor process (PID $($p.ProcessId)); running the watchdog inside the VS Code integrated terminal may cause VS Code to send SIGINT to child processes and trigger shutdowns. Please run this script from a standalone PowerShell or install as a service. Exiting."
                exit 0
            }
            $ancestor = $p.ParentProcessId
        }
    } catch {
        # Non-fatal
    }
} catch {
    # Continue even if detection fails
}

function Log {
    param($m)
    $ts = (Get-Date).ToString('u')
    $line = "[$ts] $m"
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    # Use Write-Host to avoid emitting to the pipeline; prevents functions returning unintended output
    Write-Host $line
} 

function Kill-Other-HeraldProcesses {
    param(
        [int]$ExcludePid = $null
    )
    try {
        # Find python processes that look like Herald (match -m herald or scripts referencing herald)
        $candidates = Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and (
                ($_.CommandLine -match '\bpython\b' -and $_.CommandLine -match '\b-m\b.*\bherald\b') -or
                ($_.CommandLine -match '\bherald\\__main__\b') -or
                ($_.CommandLine -match '\bherald\b' -and $_.CommandLine -like '*\\herald*')
            )
        }
        foreach ($pr in $candidates) {
            if ($pr.ProcessId -ne $ExcludePid) {
                try {
                    Stop-Process -Id $pr.ProcessId -Force -ErrorAction SilentlyContinue
                    Log "Killed existing Herald process PID $($pr.ProcessId) (Cmd: $($pr.CommandLine))"
                } catch {
                    Log "Failed to kill PID $($pr.ProcessId): $_"
                }
            }
        }
    } catch {
        Log "Error scanning for existing Herald processes: $_"
    }
}

function Start-Herald {
    param()
    try {
        # Ensure no other Herald instances are running
        Kill-Other-HeraldProcesses

        # Prepare per-run log directory and files for capturing stdout/stderr to aid debugging
        $RunsDir = Join-Path $RepoRoot 'herald_runs'
        if (-not (Test-Path $RunsDir)) { New-Item -ItemType Directory -Path $RunsDir -Force | Out-Null }
        $ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
        $guid = [System.Guid]::NewGuid().ToString('N')
        $outFile = Join-Path $RunsDir "herald_${ts}_${guid}.log"
        $errFile = "$outFile.err"

        $args = "-m herald --config $Config --skip-setup --symbol `"$Symbol`" --no-prompt --log-level $HeraldLogLevel"
        # Launch the herald process with stdout/stderr redirected to separate files to avoid Start-Process error
        $p = Start-Process -FilePath $PythonPath -ArgumentList $args -WorkingDirectory $RepoRoot -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru

        # Give process a moment to settle
        Start-Sleep -Seconds 3

        # If the process exited quickly, capture exit code and short tails for investigation
        if ($p.HasExited) {
            $exit = $p.ExitCode
            $outTail = (Get-Content -Path $outFile -Tail 50 -ErrorAction SilentlyContinue) -join "`n"
            $errTail = (Get-Content -Path $errFile -Tail 50 -ErrorAction SilentlyContinue) -join "`n"
            Log "Herald process PID $($p.Id) exited immediately (ExitCode: $exit). Stdout tail:\n$outTail\nStderr tail:\n$errTail"
            return $null
        }

        # Validate we have a process and PID
        if (-not $p -or -not $p.Id) {
            Log "Start-Process did not return a valid process object; check logs: $outFile and $errFile"
            return $null
        }

        # Remove any other survivors (excluding this PID)
        Kill-Other-HeraldProcesses -ExcludePid $p.Id

        Log "Started Herald: PID $($p.Id) (WD: $RepoRoot) (Log: $outFile; Err: $errFile)"
        Set-Content -Path $PidFile -Value $p.Id -Encoding ascii
        Set-Content -Path (Join-Path $RepoRoot 'herald_last_run.log') -Value $outFile -Encoding ascii
        return $p.Id
    } catch {
        Log "Failed to start Herald: $_"
        return $null
    }
}

# Begin
Log "Watchdog started. Python: $PythonPath Config: $Config Symbol: $Symbol HeraldLogLevel: $HeraldLogLevel"
$restartCount = 0
$restartTimes = @()
$heraldPid = Start-Herald
if (-not $heraldPid) {
    Log "Initial start failed; exiting watchdog"
    exit 1
}

while ($true) {
    Start-Sleep -Seconds 5
    $proc = $null
    try { $proc = Get-Process -Id ([int]$heraldPid) -ErrorAction SilentlyContinue } catch { Log "Invalid herald PID detected ('$heraldPid'); treating as stopped"; $proc = $null }
    if ($proc) {
        # still running, continue
        continue
    } else {
        $now = Get-Date
        $restartTimes += $now
        # keep only restarts in the last 60 seconds
        $restartTimes = $restartTimes | Where-Object { $_ -gt $now.AddSeconds(-60) }
        $restartCount = $restartTimes.Count
        Log "Detected Herald stopped (PID $heraldPid). Restart attempt #$restartCount"

        if ($restartCount -ge 10) {
            Log "Too many restarts in a short window ($restartCount in last 60s). Aborting to avoid crash loop."
            break
        }

        if ($restartCount -gt $MaxRestarts) {
            Log "Max restarts ($MaxRestarts) reached; watchdog exiting"
            break
        }
        Start-Sleep -Seconds $RestartDelaySeconds
        $newpid = Start-Herald
        if ($newpid) { $heraldPid = $newpid } else { Log "Restart failed" }
    }
}

Log "Watchdog stopped"