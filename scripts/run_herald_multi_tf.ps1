param(
    [string]$Mindset = "aggressive",
    [string]$Symbol = "EURUSD",
    [string[]]$Timeframes = @("TIMEFRAME_H1", "TIMEFRAME_M15"),
    [switch]$DryRun
)

# Helper to start Herald for multiple timeframes using configs stored under configs/mindsets/<mindset>/
$python = "python"

foreach ($tf in $Timeframes) {
    # Normalize suffix: accept either TIMEFRAME_H1 or h1/m15 etc.
    $suffix = $tf
    if ($suffix -like 'TIMEFRAME_*') { $suffix = $suffix -replace '^TIMEFRAME_','' }
    $suffix = $suffix.ToLower()

    $cfgPath = Join-Path -Path (Resolve-Path -Path "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)\..\configs\mindsets\$Mindset") -ChildPath "config_$Mindset_$suffix.json" -ErrorAction SilentlyContinue
    if (-not $cfgPath -or -not (Test-Path $cfgPath)) {
        Write-Warn "Config not found for timeframe '$tf' (expected $cfgPath). Skipping."
        continue
    }

    $argList = @('-m', 'herald', '--config', "$cfgPath", '--mindset', $Mindset, '--skip-setup')
    if ($DryRun) { $argList += '--dry-run' }

    Write-Host "Starting Herald for $Symbol on $tf using $cfgPath"
    Start-Process -FilePath $python -ArgumentList $argList -NoNewWindow -PassThru | Out-Null
}

Write-Host "Started $(($Timeframes).Count) Herald process(es)."
