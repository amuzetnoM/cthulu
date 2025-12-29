# Cthulu RPC Server

Lightweight HTTP-based RPC server for programmatic control of Cthulu at runtime.

## Quick Start

```powershell
# Place a BUY order
$body = '{"symbol":"BTCUSD#","side":"BUY","volume":0.01}'
Invoke-RestMethod -Uri "http://127.0.0.1:8278/trade" -Method POST -Body $body -ContentType "application/json"

# Place a SELL order
$body = '{"symbol":"BTCUSD#","side":"SELL","volume":0.01}'
Invoke-RestMethod -Uri "http://127.0.0.1:8278/trade" -Method POST -Body $body -ContentType "application/json"

# Check health
Invoke-RestMethod -Uri "http://127.0.0.1:8278/health" -Method GET
```

## Configuration

Enable in `config.json` or any mindset config:

```json
{
  "rpc": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8278,
    "token": null
  }
}
```

**IMPORTANT:** RPC must be explicitly enabled. Default is `false`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/trade` | Submit a trade order |
| GET | `/provenance` | Query order audit trail |
| GET | `/health` | Server health check |
| GET | `/status` | Trading system status |

### Trade Request Format

```json
{
  "symbol": "BTCUSD#",
  "side": "BUY",
  "volume": 0.01,
  "confidence": 0.8,
  "sl_pips": 50,
  "tp_pips": 100
}
```

### Trade Response Format

```json
{
  "status": "OK",
  "ticket": 600315175,
  "price": 87588.60,
  "volume": 0.01,
  "signal_id": "rpc_manual_uuid123"
}
```

## Stress Testing via RPC

The monitoring directory includes scripts for RPC-based stress testing:

```powershell
# Run full stress test (120 minutes)
.\monitoring\run_stress.ps1 -DurationMinutes 120 -InjectionMode realistic

# Inject a single signal
python monitoring\inject_signals.py --symbol BTCUSD# --side BUY --volume 0.05 --count 1
```

## Integration Points

RPC integrates with:

1. **RiskEvaluator** - All trades checked before execution
2. **AdaptiveDrawdownManager** - Position sizing adjusted dynamically
3. **Provenance Tracking** - Full audit trail for each order
4. **Prometheus Metrics** - Trade counts exported

## Full Documentation

See [docs/development_log/rpc.md](../docs/development_log/rpc.md) for complete API reference.

## Security

- Server binds to localhost only (127.0.0.1) by default
- Optional bearer token authentication via `CTHULU_API_TOKEN` env var
- All trades go through RiskEvaluator before execution
- Duplicate order detection prevents accidental re-submissions

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "RPC down" in inject logs | Check RPC is enabled in config and Cthulu is running |
| "Connection refused" | Verify port 8278 is not blocked and server is listening |
| "Duplicate order" warning | Each request needs unique signal_id (auto-generated) |
| "Risk rejected" | Check spread limits and position limits in config |
