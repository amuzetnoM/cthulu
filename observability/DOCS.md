# Observability Documentation Index

Complete documentation for Cthulu's observability system.

## Core Documentation

### [README.md](./README.md)
Main observability system documentation covering:
- ComprehensiveMetricsCollector (173 metrics)
- Observability service (separate process)
- Integration with trading system
- Prometheus/Grafana setup (optional)
- Simplified CLI usage

### [OBSERVABILITY_GUIDE.md](./OBSERVABILITY_GUIDE.md)
Comprehensive guide for setup, testing, and analysis:
- Setting up monitoring infrastructure
- Running stress tests
- Analyzing metrics
- Troubleshooting

## Quick Start

**1. Start Observability Service (CSV only):**
```bash
python -m observability.service --csv
```

**2. Start with Prometheus (port 8181):**
```bash
python -m observability.service --csv --8181
```

**3. Integrate into Cthulu Bootstrap:**
```python
from observability.integration import start_observability_service

process = start_observability_service(enable_prometheus=False)
```

## Output Files

**Primary Output:**
- `observability/reporting/comprehensive_metrics.csv` - 173-field trading metrics (auto-created)

**Optional Outputs (if Prometheus enabled):**
- `prometheus/tmp/cthulu_metrics.prom` - Prometheus text format (auto-created)
- HTTP endpoint: `http://localhost:8181/metrics` (if port specified)

## Related Systems

**Monitoring Services** (separate from observability):
- [monitoring/README.md](../monitoring/README.md) - Indicator and system health monitoring
- `monitoring/indicator_metrics.csv` - Indicator/signal data with scoring
- `monitoring/system_health.csv` - System health metrics

## Architecture

```
Cthulu System
├─→ Observability Service (separate process)
│   └─→ observability/reporting/comprehensive_metrics.csv (173 trading metrics)
│
└─→ Monitoring Services (separate processes)
    ├─→ monitoring/indicator_metrics.csv (indicator/signal + scoring)
    └─→ monitoring/system_health.csv (system health)
```

## 3 Canonical CSV Files

1. **observability/reporting/comprehensive_metrics.csv** - Trading metrics (173 fields)
2. **monitoring/indicator_metrics.csv** - Indicator/signal data (78 fields) with confidence scoring
3. **monitoring/system_health.csv** - System health (80+ fields)

## Key Features

- **Direct Integration** - No legacy MetricsCollector dependency
- **Separate Process** - Non-blocking, independent PID and memory
- **CSV First** - Single source of truth, always enabled
- **Prometheus Optional** - Only enable if you need Grafana dashboards
- **Simplified CLI** - Easy-to-use flags (--csv, --8181, --prom)

## Links

- **Code:** `observability/` directory
- **Config:** `monitoring/prometheus.yml` (if using Grafana)
- **Dashboards:** `monitoring/grafana/dashboards/` (if using Grafana)
- **Schema:** `monitoring/COMPREHENSIVE_METRICS_SCHEMA.md` (173 metrics reference)

---

**For detailed usage, see [README.md](./README.md)**  
**For setup and testing, see [OBSERVABILITY_GUIDE.md](./OBSERVABILITY_GUIDE.md)**
