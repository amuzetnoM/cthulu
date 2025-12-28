---
title: Risk Management
description: Risk management configuration and stop-loss strategies for Cthulu trading system
tags: [risk-management, stop-loss, position-sizing]
slug: /docs/risk-management
sidebar_position: 9
---

![version-badge](https://img.shields.io/badge/version-5.0.1-blue)


## Overview

This document describes the lightweight risk-management knobs added to Cthulu and how the system adapts stop-loss placement to account size.

Key configuration entries (in `config_schema.py` under `risk`):

- `emergency_stop_loss_pct` (float): default emergency stop used when adopting external trades (percent, e.g. `8.0`).
- `sl_balance_thresholds` (mapping): relative SL thresholds mapped to balance buckets. Example:

```json
"sl_balance_thresholds": {
  "tiny": 0.01,
  "small": 0.02,
  "medium": 0.05,
  "large": 0.25
}
```

- `sl_balance_breakpoints` (list): numeric breakpoints that map to the thresholds. Example: `[1000.0, 5000.0, 20000.0]`.

Behavior summary:

- When placing a new order (or when applying SL during adoption), Cthulu calls `position.risk_manager.suggest_sl_adjustment(...)` with the account balance and proposed SL.
- If the proposed SL is wider than a computed relative threshold, the `risk_manager` returns an `adjusted_sl` nearer to market and suggests target timeframes and a trading mindset (`scalping`, `short-term`, `swing`).
- The `ExecutionEngine` and `PositionManager` will apply the adjusted SL automatically and attach the suggestion to order/position metadata.

Operational guidance:

- For small accounts (<= 1k), thresholds are tight so Cthulu will favor scalping timeframes (`M1`, `M5`, `M15`) and small SLs.
- For larger accounts, thresholds are looser and Cthulu will permit wider SLs and swing-style timeframes.

Future improvements:

- Symbol-specific pip scaling and lot-size-aware distance calculations.
- Volatility-based dynamic thresholds using recent ATR.




