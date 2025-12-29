$logPath = 'C:\workspace\cthulu\logs\Cthulu.log'
if (-not (Test-Path $logPath)) {
    Write-Output "Log not found: $logPath"
    pause
    exit 1
}

Write-Output "Tailing Cthulu.log (press Ctrl+C to stop)"
Get-Content -Path $logPath -Wait -Tail 200
