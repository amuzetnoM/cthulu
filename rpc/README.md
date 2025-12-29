# Cthulu RPC Server

Lightweight HTTP-based RPC server for programmatic control of Cthulu at runtime.

## Quick Start

```powershell
# Place a BUY order
$body = '{"symbol":"BTCUSD#","side":"BUY","volume":0.01}'
Invoke-RestMethod -Uri "http://127.0.0.1:8278/trade" -Method POST -Body $body -ContentType "application/json"
```

## Configuration

Enable in `config.json`:

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

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/trade` | Submit a trade order |
| GET | `/provenance` | Query order audit trail |

## Full Documentation

See [docs/development_log/rpc.md](../docs/development_log/rpc.md) for complete API reference.

## Security

- Server binds to localhost only (127.0.0.1)
- Optional bearer token authentication via `CTHULU_API_TOKEN`
- All trades go through RiskEvaluator before execution
