# Cthulu — File-by-file Critical Analysis (high-level)

> Summary: I reviewed `OVERVIEW.md`, `_dev` docs and the repo structure. The `OVERVIEW.md` mermaid diagrams align with `_dev` review and changelog (v5.1.0 APEX). No `system_map.*` was found in `cthulu` so I created `cthulu/_dev/system_map.html` with a mermaid flowchart. Below are per-directory notes — actionable and critical where appropriate.

---

## Top-level summary
- Version/tag: **v5.1.0 APEX** — consistent across `OVERVIEW.md`, `_dev` reports and changelog.
- Docs: Extensive documentation across `docs/`, `monitoring/`, `observability/`, `_dev/` and `OVERVIEW.md`.
- Missing: No dedicated `system_map` or `system_mapping` file under `cthulu/` (added `cthulu/_dev/system_map.html`).

---

## Per-directory notes

- `core/`
  - Purpose: Startup, initialization, shared runtime components.
  - Good: Centralized bootstrap and loop code; `OVERVIEW.md` references `bootstrap.py` and `trading_loop.py`.
  - Risk: Ensure robust graceful shutdown + restart tests (shutdown edge cases).

- `cognition/` (AI/ML)
  - Purpose: Regime classifier, predictor, exit oracle and other ML helpers.
  - Good: Clear separation; docs reference cognition engine.
  - Concern: Unit tests for ML determinism and data pipelines should be emphasized (data drift tests, deterministic seeding).

- `strategy/`
  - Purpose: Strategy implementations (SMA, EMA, momentum, scalping, mean-rev).
  - Good: Well-documented; StrategySelector exists for dynamic selection.
  - Action: Add more integration tests simulating strategy switching under regime changes.

- `indicators/`
  - Purpose: Indicator calculations (RSI, MACD, ATR...)
  - Good: IndicatorRequirementResolver noted in docs; avoids duplicated computation.
  - Concern: Profiling for high-throughput: ensure single-pass computation for many symbols.

- `risk/`
  - Purpose: Risk evaluation, drawdown protection, adaptive sizing.
  - Note: OVERVIEW notes unification planned (Phase 6) — risk manager currently split (`risk/manager.py` and `position/risk_manager.py`).
  - Action: Prioritize unified interface and more comprehensive unit tests for risk limits and emergency stops.

- `position/`
  - Purpose: Position lifecycle, manager, tracker, adoption (external trades support).
  - Good: Clear lifecycle separation.
  - Concern: Concurrency and DB consistency tests when positions are updated rapidly (race conditions).

- `exit/`
  - Purpose: Exit strategies (trailing, profit target, time-based, confluence).
  - Good: Priority-based exit system described in docs.
  - Action: Add property-based tests covering exit conflicts (ensuring highest priority wins and no double-closes).

- `execution/` and `connector/`
  - Purpose: ExecutionEngine, MT5 connector.
  - Critical: MT5 connectivity is an external dependency — add robust retry & circuit-breaker tests, and a clear dry-run mode verification.

- `persistence/` and DB files
  - Purpose: Database storage (SQLite WAL), training logs.
  - Concern: Banking on SQLite for production; document migration path to a more scalable DB and ensure WAL tuning is included in ops docs.

- `observability/` & `monitoring/`
  - Purpose: Metrics, Prometheus, dashboard.
  - Good: Complete guides exist; dashboards and metrics present.
  - Action: Add SLO/alerting runbook and announce which metrics are critical for circuit breakers.

- `tests/`
  - Purpose: Unit and integration tests.
  - Observation: Test coverage is present but add more integration tests for real-world scenarios (regime shifts, connectivity outages, rapid fills).

- `docs/` & `_dev/`
  - Purpose: Central documentation and internal notes (release notes, system reviews).
  - Good: `_dev` contains a comprehensive system report and reviews. `OVERVIEW.md` mermaid diagrams were recently added and align with `_dev`.

---

## Critical issues / risks (priority)
1. Risk manager split (Phase 6 unification): **Medium-High** — unify interface to avoid divergent risk decisions.
2. Execution/Connector flakiness under MT5 network issues: **High** — add circuit breakers and deterministic tests for failures.
3. DB concurrency/race conditions in Position Manager: **Medium** — add integration tests and locks/transactions.
4. ML reproducibility & data validation for ML-driven signals: **Medium** — add data-contract tests and deterministic seeding.

---

## Quick recommendations
- Add `docs/architecture/` with a small set of diagrams (C4 container + sequence for order flow) — `system_map.html` is a good starting point. ✅ (file added)
- Add an integration test harness that can run key workflows (signal → risk → exec) in a simulated MT5/DB environment.
- Consolidate risk-related modules earlier rather than later; add comprehensive unit tests for emergency stops and daily loss breakers.

---

If you want, I can:
- Expand this into a precise, file-by-file table listing the important files (every file) with a one-line verdict, or
- Create an additional C4-style diagram and a sequence diagram for the order flow (signal → risk → exec).

Next steps: I will commit these new tracked artifacts and prepare a short PR description. Want me to commit now? (I can also push and open a draft PR.)