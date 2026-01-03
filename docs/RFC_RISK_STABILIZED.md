# RFC: Stabilized Risk Module (non-invasive toggle)

**Goal:** Provide a non-disruptive mechanism to route risk decisions through a stable, conservative implementation without refactoring the core trading loop. This allows fast rollbacks and a safe experimentation path.

## Problem
`risk/` and `position/` currently contain overlapping responsibilities (`risk/manager.py`, `position/risk_manager.py`). A large refactor to unify them is risky while the system is in active development/operation.

## Proposal
- Add a small wrapper module `risk/stabilized.py` implementing a conservative risk policy (strict limits, simplified checks) or delegating to `risk/manager` when toggled off.
- Add a configuration flag `risk.use_stabilized` in `config/*.json` (default: false). The main orchestrator loads this config during startup and binds `risk_manager` to either `risk.stabilized` or `risk.manager`.

### Implementation Sketch (non-invasive)
- `risk/stabilized.py` exposes the same public API as `risk.manager` (approve_trade, evaluate_position, etc.). Initially the implementation will delegate to `risk.manager` but enforce additional checks (e.g., lower max position size, stronger daily loss circuit).
- In `__main__` (or bootstrap) where risk manager is imported, replace:
  ```py
  from risk import manager as risk_manager
  ```
  with:
  ```py
  if config['risk'].get('use_stabilized'):
      from risk import stabilized as risk_manager
  else:
      from risk import manager as risk_manager
  ```
- Add a runtime toggle if config reload is supported (optional) with safe application only at cycle boundaries.

### Testing & Safety
- Provide unit tests that assert stabilized policy is stricter than default for given scenarios (no stubs in prod; run locally/in CI).
- On any toggle, log a clear audit event: `risk_toggle: stabilized_enabled=true|false` with timestamp and user/actor.

### Rollout & Rollback
- Add config option behind an environment or runtime flag; default set to `false`.
- Deploy stabilized to staging and run a smoke suite; after approval, flip flag in production (or via orchestrator UI) and monitor.

### Pros & Cons
- Pros: Allows quick activation of a conservative safety chain without refactor; can be used as a safe guard during unstable periods.
- Cons: May create divergence between stabilized and main policies over time — schedule periodic alignment or a single source of truth.

---

**Decision Needed:** Approve the RFC to add `risk/stabilized.py` and the `risk.use_stabilized` configuration toggle and we will implement the wrapper with logging and audit events.
