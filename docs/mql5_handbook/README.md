# MQL5 Handbook — Index

This handbook stores MQL5 articles relevant to Herald’s development (Phases 1–3).  

Directory structure:

- `phase1/` — Foundation and execution-related articles (connectors, integration, logging, API, risk basics)
- `phase2/` — Autonomous execution, indicators, position management, exit strategies
- `phase3/` — Price action, volume profile, advanced charts, statistical analysis

## Phase Manifests
- Phase 1 Manifest: `phase1/manifest.md`
- Phase 2 Manifest: `phase2/manifest.md`
- Phase 3 Manifest: `phase3/manifest.md`

## How to convert/import articles (tooling expectations)
1. Each article must be saved as Markdown under `phaseN/articles/<article_id>-<slug>.md`.
2. All images and code samples will be stored under `phaseN/assets/<article_id>/`.
3. Each Markdown file should include front-matter with: title, original_url, article_id, published_date, phase. **Note: tags have been intentionally removed and are not generated; `author` is intentionally omitted**.
4. Use `docs/mql5_handbook/manifest.md` as the global index for the Handbook.

