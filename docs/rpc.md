---
title: RPC Interface
description: How to use the local RPC server to control Herald at runtime
---

# RPC Interface

Herald now includes a lightweight, local-only RPC server to allow programmatic control at runtime.

Overview
- The server binds to `127.0.0.1` and exposes a single POST endpoint: `/trade`.
- Authentication: Use `HERALD_API_TOKEN` (bearer token or `X-Api-Key` header). If the token is not set the server will still start but will run unauthenticated (still bound to localhost). For production, always set `HERALD_API_TOKEN`.

Quick start

1. Ensure Herald is running. The RPC server starts automatically.
2. Place a trade via curl (replace `TOKEN` and payload values):

```bash
curl -X POST \
  -H "Authorization: Bearer $HERALD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","side":"BUY","volume":0.01}' \
  http://127.0.0.1:8181/trade
```

Payload fields
- `symbol` (string): trading symbol
- `side` ("BUY" or "SELL")
- `volume` (numeric): lots
- `price` (optional): limit price
- `sl` (optional): stop loss
- `tp` (optional): take profit

Behavior
- The RPC server performs a risk check using the same `RiskManager` as the main system. If rejected, HTTP 403 is returned with reason.
- On success, the server will place the order via the same `ExecutionEngine` and return a structured JSON response describing the order status.

Security
- Recommended to only expose the server on loopback. If you must expose to a network set strong firewall rules and always set `HERALD_API_TOKEN`.

Extending
- The server is implemented in `herald/rpc/server.py`. It wires into Herald's runtime components (execution engine, risk manager, position manager, database) during startup.
