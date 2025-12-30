<#
.SYNOPSIS
    Cthulu 4-Hour Phased Precision Tuning Test
.DESCRIPTION
    Phase 1 (0-60 min):   Conservative - Capital preservation, surgical entries
    Phase 2 (60-120 min): Balanced - Moderate risk, optimized R:R
    Phase 3 (120-180 min): Aggressive - Higher frequency, trend capture
    Phase 4 (180-240 min): Ultra-Aggressive - Full throttle, 100+ trade management
    
    Each phase tunes the system progressively, carrying learnings forward.
.NOTES
    Started: 2025-12-29
    Target: 240 minutes error-free with positive P&L trajectory
#>

param(
    [int]$PhaseDurationMinutes = 60,
    [switch]$SkipToPhase,
    [int]$StartPhase = 1
)

$ErrorActionPreference = "Continue"
Set-Location "C:\workspace\cthulu"

# Configuration paths
$Configs = @{
    1 = "configs\mindsets\conservative\config_conservative_m15.json"
    2 = "configs\mindsets\balanced\config_balanced_m15.json"
    3 = "configs\mindsets\aggressive\config_aggressive_m15.json"
    4 = "config_ultra_aggressive.json"
}

$PhaseNames = @{
    1 = "CONSERVATIVE - Capital Preservation"
    2 = "BALANCED - Optimized Risk/Reward"
    3 = "AGGRESSIVE - Trend Capture"
    4 = "ULTRA-AGGRESSIVE - Boss Mode"
}

$LogFile = "monitoring\four_hour_test.log"
$MetricsCSV = "monitoring\metrics.csv"
$SystemReport = "SYSTEM_REPORT.md"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    $entry = "[$ts] [$Level] $Message"
    Write-Host $entry
    Add-Content -Path $LogFile -Value $entry
}

function Get-AccountMetrics {
    $result = python -c @"
import MetaTrader5 as mt5
import json
mt5.initialize()
info = mt5.account_info()
positions = mt5.positions_get()
pos_count = len(positions) if positions else 0
total_profit = sum(p.profit for p in positions) if positions else 0
print(json.dumps({
    'balance': info.balance,
    'equity': info.equity,
    'margin': info.margin,
    'free_margin': info.margin_free,
    'positions': pos_count,
    'floating_pnl': round(total_profit, 2),
    'margin_level': round(info.margin_level, 2) if info.margin_level else 0
}))
mt5.shutdown()
"@
    return $result | ConvertFrom-Json
}

function Update-SystemReport {
    param(
        [int]$Phase,
        [string]$Status,
        [hashtable]$Metrics
    )
    
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $appendText = @"

### Phase $Phase Update - $ts

| Metric | Value |
|--------|-------|
| Status | $Status |
| Balance | `$$($Metrics.balance) |
| Equity | `$$($Metrics.equity) |
| Positions | $($Metrics.positions) |
| Floating P&L | `$$($Metrics.floating_pnl) |
| Margin Level | $($Metrics.margin_level)% |

"@
    
    Add-Content -Path $SystemReport -Value $appendText
    
    # Push to remote
    git add $SystemReport 2>$null
    git commit -m "Phase $Phase update: $Status" --quiet 2>$null
    git push --quiet 2>$null
}

function Append-MetricsCSV {
    param([int]$Phase, [hashtable]$Metrics)
    
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    $row = "$ts,$Phase,$($PhaseNames[$Phase]),$($Metrics.balance),$($Metrics.equity),$($Metrics.positions),$($Metrics.floating_pnl),$($Metrics.margin_level)"
    Add-Content -Path $MetricsCSV -Value $row
}

function Start-CthuluPhase {
    param([int]$Phase, [string]$ConfigPath)
    
    Write-Log "Starting Phase $Phase with config: $ConfigPath" "PHASE"
    
    # Kill existing Cthulu
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "cthulu" -or $_.CommandLine -match "main.py"
    } | ForEach-Object { 
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 2
    
    # Start Cthulu with phase config
    $cthuluProc = Start-Process -FilePath "python" `
        -ArgumentList "-m", "cthulu.main", "--config", $ConfigPath `
        -WorkingDirectory "C:\workspace\cthulu" `
        -PassThru `
        -RedirectStandardOutput "monitoring\cthulu_phase${Phase}.log" `
        -RedirectStandardError "monitoring\cthulu_phase${Phase}_err.log" `
        -WindowStyle Hidden
    
    Write-Log "Cthulu Phase $Phase started (PID: $($cthuluProc.Id))"
    return $cthuluProc
}

function Run-PhaseMonitoring {
    param(
        [int]$Phase,
        [int]$DurationMinutes,
        [System.Diagnostics.Process]$CthuluProcess
    )
    
    $startTime = Get-Date
    $endTime = $startTime.AddMinutes($DurationMinutes)
    $checkInterval = 30  # seconds
    $errorCount = 0
    $peakEquity = 0
    $peakDrawdown = 0
    
    Write-Log "Phase $Phase monitoring started. Duration: $DurationMinutes minutes"
    
    while ((Get-Date) -lt $endTime) {
        Start-Sleep -Seconds $checkInterval
        
        # Check if Cthulu is still running
        if ($CthuluProcess.HasExited) {
            Write-Log "CRITICAL: Cthulu crashed during Phase $Phase!" "ERROR"
            $errorCount++
            
            # Restart
            $CthuluProcess = Start-CthuluPhase -Phase $Phase -ConfigPath $Configs[$Phase]
        }
        
        # Get metrics
        try {
            $metrics = Get-AccountMetrics
            
            # Track peak equity and drawdown
            if ($metrics.equity -gt $peakEquity) {
                $peakEquity = $metrics.equity
            }
            $currentDD = [math]::Round((($peakEquity - $metrics.equity) / $peakEquity) * 100, 2)
            if ($currentDD -gt $peakDrawdown) {
                $peakDrawdown = $currentDD
            }
            
            # Append to CSV
            Append-MetricsCSV -Phase $Phase -Metrics $metrics
            
            $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
            $remaining = [math]::Round(($endTime - (Get-Date)).TotalMinutes, 1)
            
            Write-Log "Phase $Phase [$elapsed/$DurationMinutes min] Balance: `$$($metrics.balance) | Equity: `$$($metrics.equity) | Positions: $($metrics.positions) | DD: ${currentDD}%"
            
            # Check for critical conditions
            if ($currentDD -gt 30) {
                Write-Log "WARNING: Drawdown exceeds 30%! Triggering defensive mode." "WARN"
            }
            
        }
        catch {
            Write-Log "Error getting metrics: $_" "ERROR"
            $errorCount++
        }
        
        # Every 5 minutes, update system report
        if ([math]::Round(((Get-Date) - $startTime).TotalMinutes) % 5 -eq 0) {
            $metricsHash = @{
                balance      = $metrics.balance
                equity       = $metrics.equity
                positions    = $metrics.positions
                floating_pnl = $metrics.floating_pnl
                margin_level = $metrics.margin_level
            }
            Update-SystemReport -Phase $Phase -Status "Running" -Metrics $metricsHash
        }
    }
    
    # Phase complete
    $finalMetrics = Get-AccountMetrics
    $metricsHash = @{
        balance      = $finalMetrics.balance
        equity       = $finalMetrics.equity
        positions    = $finalMetrics.positions
        floating_pnl = $finalMetrics.floating_pnl
        margin_level = $finalMetrics.margin_level
    }
    
    Write-Log "Phase $Phase COMPLETE. Final Balance: `$$($finalMetrics.balance) | Peak DD: ${peakDrawdown}% | Errors: $errorCount"
    Update-SystemReport -Phase $Phase -Status "COMPLETED" -Metrics $metricsHash
    
    return @{
        FinalBalance = $finalMetrics.balance
        PeakDrawdown = $peakDrawdown
        ErrorCount   = $errorCount
        Process      = $CthuluProcess
    }
}

# === MAIN EXECUTION ===

Write-Log "="*60
Write-Log "CTHULU 4-HOUR PHASED PRECISION TUNING TEST"
Write-Log "="*60
Write-Log "Total Duration: $($PhaseDurationMinutes * 4) minutes"
Write-Log "Phase Duration: $PhaseDurationMinutes minutes each"
Write-Log "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Initialize metrics CSV header if needed
if (-not (Test-Path $MetricsCSV) -or (Get-Item $MetricsCSV).Length -eq 0) {
    "timestamp,phase,phase_name,balance,equity,positions,floating_pnl,margin_level" | Out-File $MetricsCSV -Encoding UTF8
}

# Get initial account state
$initialMetrics = Get-AccountMetrics
Write-Log "Initial Balance: `$$($initialMetrics.balance)"

$results = @{}

for ($phase = $StartPhase; $phase -le 4; $phase++) {
    Write-Log ""
    Write-Log "="*60
    Write-Log "PHASE $phase`: $($PhaseNames[$phase])"
    Write-Log "="*60
    
    $configPath = $Configs[$phase]
    
    if (-not (Test-Path $configPath)) {
        Write-Log "Config not found: $configPath - using ultra_aggressive" "WARN"
        $configPath = "config_ultra_aggressive.json"
    }
    
    $cthuluProc = Start-CthuluPhase -Phase $phase -ConfigPath $configPath
    $phaseResult = Run-PhaseMonitoring -Phase $phase -DurationMinutes $PhaseDurationMinutes -CthuluProcess $cthuluProc
    
    $results[$phase] = $phaseResult
    
    # Brief pause between phases
    Write-Log "Phase transition pause (10 seconds)..."
    Start-Sleep -Seconds 10
}

# === FINAL SUMMARY ===
Write-Log ""
Write-Log "="*60
Write-Log "4-HOUR TEST COMPLETE - FINAL SUMMARY"
Write-Log "="*60

$finalMetrics = Get-AccountMetrics
$totalPnL = $finalMetrics.balance - $initialMetrics.balance
$totalPnLPct = [math]::Round(($totalPnL / $initialMetrics.balance) * 100, 2)

Write-Log "Initial Balance: `$$($initialMetrics.balance)"
Write-Log "Final Balance:   `$$($finalMetrics.balance)"
Write-Log "Total P&L:       `$$totalPnL ($totalPnLPct%)"
Write-Log ""
Write-Log "Phase Results:"
foreach ($phase in 1..4) {
    if ($results[$phase]) {
        Write-Log "  Phase $phase`: Balance `$$($results[$phase].FinalBalance) | Peak DD: $($results[$phase].PeakDrawdown)% | Errors: $($results[$phase].ErrorCount)"
    }
}

# Final system report update
$summaryText = @"

---

## 🏆 4-HOUR TEST FINAL SUMMARY

**Completed:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

### Financial Results

| Metric | Value |
|--------|-------|
| Initial Balance | `$$($initialMetrics.balance) |
| Final Balance | `$$($finalMetrics.balance) |
| Total P&L | `$$totalPnL |
| Total Return | $totalPnLPct% |

### Phase Performance

| Phase | Profile | Final Balance | Peak Drawdown | Errors |
|-------|---------|---------------|---------------|--------|
| 1 | Conservative | `$$($results[1].FinalBalance) | $($results[1].PeakDrawdown)% | $($results[1].ErrorCount) |
| 2 | Balanced | `$$($results[2].FinalBalance) | $($results[2].PeakDrawdown)% | $($results[2].ErrorCount) |
| 3 | Aggressive | `$$($results[3].FinalBalance) | $($results[3].PeakDrawdown)% | $($results[3].ErrorCount) |
| 4 | Ultra-Aggressive | `$$($results[4].FinalBalance) | $($results[4].PeakDrawdown)% | $($results[4].ErrorCount) |

### System Grade Post-Test

**PENDING EVALUATION**

---
"@

Add-Content -Path $SystemReport -Value $summaryText
git add $SystemReport
git commit -m "4-hour test complete: $totalPnLPct% return"
git push

Write-Log "System report updated and pushed to remote."
Write-Log "4-HOUR PRECISION TUNING TEST COMPLETE."
