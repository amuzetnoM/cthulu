Herald ML/RI Pipeline

Purpose: A lightweight, fast, and reliable ML pipeline for Herald.

High-level layout:

- data/raw: raw event logs (JSONL/Parquet) produced by instrumentation
- data/processed: cleaned datasets and labeled examples for training
- features: feature engineering scripts
- training: training scripts and model evaluation
- serving: model serving and signal notifier (Discord)
- monitoring: drift detectors, model health monitors
- utils: helpers, schema definitions

MVP approach (short):
1. Instrumentation to capture order, execution, and market snapshots.
2. Offline experiments (simple tree model like LightGBM/XGBoost) predicting short-term probability of positive returns for 1-5 bar horizons.
3. Shadow / advisory mode: model outputs are recorded and sent to Discord (via webhook) as "signals" in advisory mode only.
4. If approval and performance: advisory -> gated advisory filters -> advisory+small position sizing -> production.

Design principles: simple, explainable, versioned, and auditable. Keep processing fast and robust; favor lightweight models initially.
