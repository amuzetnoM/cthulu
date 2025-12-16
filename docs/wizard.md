# Herald Setup Wizard

This document describes the interactive setup wizard and the optional NLP-driven wizard (`--wizard-ai`).

## Quick start

Run the wizard:

```powershell
python -m herald --wizard
```

Run the NLP-driven wizard (lightweight, local):

```powershell
python -m herald --wizard-ai
```

The NLP wizard accepts a single-line natural-language intent, for example:

- "Aggressive GOLD#m M15 H1, 2% risk, $100 max loss"
- "Conservative EURUSD 1m, 0.5% position size, max loss $50"

After parsing, the wizard will propose a configuration which you can accept, edit, and save as a per-mindset profile.

## Optional advanced NLP

Herald can optionally use local NLP models (spaCy) for better entity extraction when available. This integration is entirely optional and disabled by default. When `spaCy` is installed and you choose to enable advanced parsing at the prompt, the wizard will attempt to use a local spaCy pipeline to extract entities (symbols, money amounts, percents, timeframes).

To enable advanced parsing, install spaCy and a small model:

```powershell
python -m pip install spacy
python -m spacy download en_core_web_sm
```

If advanced parsing is not available or fails, the wizard automatically falls back to a conservative rule-based parser that is deterministic and privacy-preserving (no network calls).

## Saving profiles

After accepting a proposed configuration, you can save it as a per-mindset profile (`configs/mindsets/<mindset>/config_<mindset>_<timeframe>.json`). The wizard can optionally start these profiles immediately (dry-run supported).

## Implementation notes for developers

- The rule-based parser is implemented in `config/wizard.py::parse_natural_language_intent` and is intentionally conservative (no remote calls).
- The optional advanced parser lives at `config/wizard.py::advanced_intent_parser` and attempts to use `spaCy` if available.
- Unit tests for the parser can be added under `herald/tests/` (a quick test runner is included at `herald/tests/test_wizard_nlp.py`).

## Examples

- `Aggressive GOLD#m M15 H1, 2% risk, $100 max loss` -> `symbol: XAUUSD#M`, `timeframes: [TIMEFRAME_M15, TIMEFRAME_H1]`, `position_size_pct: 2.0`, `max_daily_loss: 100`

- `Balanced BTCUSD 5m, 1%` -> `symbol: BTCUSD`, `timeframes: [TIMEFRAME_M5]`, `position_size_pct: 1.0`

If you want, I can add more examples and unit tests next.
