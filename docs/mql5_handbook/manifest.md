# MQL5 Handbook — Manifest

Maintained: `docs/mql5_handbook/manifest.md`  
Source: https://www.mql5.com/en/articles/  
Date: 2025-12-07  
Author: (Automated import manifest)

---

## Overview
This manifest catalogs the candidate MQL5 articles to be saved into per-phase directories under `docs/mql5_handbook/` (one article per markdown file + assets). It’s organized by the project’s Phase map in `docs/development_log/build_plan.md` to ensure Phase 1–3 coverage. Per-phase manifests are:

- `phase1/manifest.md` — Phase 1 (foundation) articles
- `phase2/manifest.md` — Phase 2 (execution & indicators) articles
- `phase3/manifest.md` — Phase 3 (advanced analytics) articles

NOTE: Some articles are part of multi-part series. We'll record per-article author and publish date when fetching the article HTML for the final import. The manifest contains the Title, original URL, MQL5 article ID (where detected), and suggested tags & phase mapping.

---

## Table of Contents
1. Phase 1 / Phase 2 (Execution & Foundation)
2. Phase 3 — Price Action & Charting
3. Phase 3 — Advanced Chart Types
4. Phase 3 — Volume & Order Flow
5. Phase 3 — Statistical / Econometrics
6. Phase 3 — Session-based Trading
7. Phase 3 — Advanced Indicators & Integration
8. Machine Learning & Advanced Topics
9. Misc / Cross-cutting

---

## Phase 1 / Phase 2 (Execution & Foundation)
- Reimagining Classic Strategies (Part 19): Deep Dive Into Moving Average Crossovers — https://www.mql5.com/en/articles/20488  (article_id: 20488)  — tags: [strategy, moving-average, filtering]
- Implementing Practical Modules from Other Languages in MQL5 (Part 05): The Logging module from Python — https://www.mql5.com/en/articles/20458 (article_id: 20458) — tags: [integration, logging, python]
- Introduction to MQL5 (Part 27): Mastering API and WebRequest Function in MQL5 — https://www.mql5.com/en/articles/17774 (article_id: 17774) — tags: [integration, webrequest, API]
- Introduction to MQL5 (Part 29): Mastering API and WebRequest Function in MQL5 (III) — https://www.mql5.com/en/articles/20375 (article_id: 20375) — tags: [integration, webrequest]
- Introduction to MQL5 (Part 30): Mastering API and WebRequest Function in MQL5 (IV) — https://www.mql5.com/en/articles/20425 (article_id: 20425) — tags: [integration, webrequest]
- Building a Trading System (Part 5): Managing Gains Through Structured Trade Exits — https://www.mql5.com/en/articles/19693 (article_id: 19693) — tags: [exits, position-management]
- Risk Management (Part 1): Fundamentals for Building a Risk Management Class — https://www.mql5.com/en/articles/16820 (article_id: 16820) — tags: [risk, core]
- Risk Management (Part 2): Implementing Lot Calculation in a Graphical Interface — https://www.mql5.com/en/articles/16985 (article_id: 16985) — tags: [risk, GUI]
- Building a Professional Trading System with Heikin Ashi (Part 1 & Part 2) — https://www.mql5.com/en/articles/19260 (19260), https://www.mql5.com/en/articles/18810 (18810) — tags: [indicators, heikin-ashi]
- The MQL5 Standard Library Explorer (Part 4 & 5): Custom Signal Library / Multiple Signal Expert — https://www.mql5.com/en/articles/20266 (20266), https://www.mql5.com/en/articles/20289 (20289) — tags: [library, signals]
- MQL5 Trading Tools (Part 9–10): First run user setup wizard & strategy tracker — https://www.mql5.com/en/articles/19714 (19714), https://www.mql5.com/en/articles/20229 (20229) — tags: [tools, UI]
- MQL5 Wizard Techniques (Parts 81–85 series) — sample group: 19781, 19794, 19948, 19890 — tags: [wizard, patterns]
- Chart Sync: Chart Synchronization for Easier Technical Analysis — https://www.mql5.com/en/articles/18937 (18937) — tags: [charts, sync]

---

## Phase 3 — Price Action & Charting (Pattern detection, CHoCH, S/R, Heatmaps)
- Price Action Analysis (Parts 39–53) — grouped series: 19365, 19460, 19697, 19738, 19945, 19944, 20168, 20262, 20313, 20387, 20390 — tags: [price-action, pattern, CHoCH, S/R, heatmap]
  - Part 39: Automating BOS and CHoCH Detection — https://www.mql5.com/en/articles/19365 (19365)
  - Part 40: Market DNA Passport — https://www.mql5.com/en/articles/19460 (19460)
  - Part 42: Interactive Chart Testing — https://www.mql5.com/en/articles/19697 (19697)
  - Part 43: Candlestick Probability and Breakouts — https://www.mql5.com/en/articles/19738 (19738)
  - Part 46: Fibonacci Retracement EA — https://www.mql5.com/en/articles/19945 (19945)
  - Part 47: Tracking Forex Sessions and Breakouts — https://www.mql5.com/en/articles/19944 (19944)
  - Part 49: Integrating Trend, Momentum, Volatility — https://www.mql5.com/en/articles/20168 (20168)
  - Part 50: RVGI, CCI and SMA Confluence Engine — https://www.mql5.com/en/articles/20262 (20262)
  - Part 51: Pattern Discovery Chart Search — https://www.mql5.com/en/articles/20313 (20313)
  - Part 52: Master Market Structure with MTF Visual Analysis — https://www.mql5.com/en/articles/20387 (20387)
  - Part 53: Pattern Density Heatmap — https://www.mql5.com/en/articles/20390 (20390)
- From Novice to Expert: Revealing the Candlestick Shadows (Wicks) — https://www.mql5.com/en/articles/19919 (19919) — tags: [candlesticks, wicks]
- Mastering Quick Trades: Overcoming Execution Paralysis — https://www.mql5.com/en/articles/19576 (19576) — tags: [execution, psychology]
- Reimagining Classic Strategies (Part 18): Searching For Candlestick Patterns — https://www.mql5.com/en/articles/20223 (20223)
- Price Action: 5–0 Harmonic Pattern — https://www.mql5.com/en/articles/19856 (19856) — tags: [harmonic]

---

## Phase 3 — Advanced Chart Types
- Mastering Kagi Charts in MQL5 (Part I): Creating the Indicator — https://www.mql5.com/en/articles/20239 (20239) — tags: [kagi, charts]
- Renko, Point & Figure, and similar advanced chart discussions appear across indicator & price action series; see the categories for more details.

---

## Phase 3 — Volume Analysis & Order Flow
- Analytical Volume Profile Trading (AVPT): Liquidity Architecture — https://www.mql5.com/en/articles/20327 (20327) — tags: [volume, vpvr, AVPT]
- Candle Range Theory (CRT): Automating CRT — https://www.mql5.com/en/articles/20323 (20323) — tags: [range, accumulation, distribution]
- Order Blocks / Advanced ICT (Order Blocks Indicator): https://www.mql5.com/en/articles/16268 (16268) — tags: [order-blocks, ICT]
- Market Sentiment & Account Performance Matrix — https://www.mql5.com/en/articles/19422 (19422) — tags: [sentiment, metrics]
- Developing a Custom Account Performance Matrix — https://www.mql5.com/en/articles/19508 (19508) — tags: [performance, dashboard]

---

## Phase 3 — Statistical / Econometrics & Correlation
- Statistical Arbitrage Through Cointegrated Stocks (Part 8) — https://www.mql5.com/en/articles/20485 (20485) — tags: [arb, cointegration]
- Pseudo Pearson Correlation Approach — https://www.mql5.com/en/articles/20065 (20065) — tags: [correlation, indicators]
- Adaptive Linear Regression Channel Strategy — https://www.mql5.com/en/articles/20347 (20347) — tags: [statistical, regression]
- Statistical Mean Reversion with Confidence Intervals & Dashboard — https://www.mql5.com/en/articles/20167 (20167) — tags: [mean-reversion]

---

## Phase 3 — Session-Based Trading
- Session-Based Opening Range Breakout (ORB) — https://www.mql5.com/en/articles/20339 (20339) — tags: [session, ORB]
- Opening Range Breakout (Introduction part) — https://www.mql5.com/en/articles/19886 (19886) — tags: [ORB]
- Session-based volume & session overlap patterns: various articles across Trading pages.

---

## Phase 3 — Advanced Indicators & Integrations
- Intro indicator tutorial pages (RSI, MACD, Bollinger, Stochastic, ADX) are already implemented in the repository indicators; these MQL5 pages are reference points and implementation guides for each indicator.
- Currency pair strength indicator — https://www.mql5.com/en/articles/17303 (17303) — tags: [currency-strength]
- Triple Sine Mean Reversion Method — https://www.mql5.com/en/articles/20220 (20220) — tags: [TSO, mean-reversion]
- Butterfly Oscillator Method — https://www.mql5.com/en/articles/20113 (20113) — tags: [oscillator]
- Analytical & practical modules porting from Python — https://www.mql5.com/en/articles/19035 (19035) — tags: [port, time, date]

---

## Machine Learning & Advanced Topics (Phase 4 references)
- MetaTrader 5 Machine Learning Blueprint (Parts 4–6): Bootstrapping, Caching, Seq. Bootstrapping — https://www.mql5.com/en/articles/19850 (19850), https://www.mql5.com/en/articles/20059 (20059), https://www.mql5.com/en/articles/20302 (20302)
- Overcoming The Limitation of Machine Learning (Parts 7–8): Strategy selection & Nonparametric selection — https://www.mql5.com/en/articles/20256 (20256), https://www.mql5.com/en/articles/20317 (20317)
- Neural Networks Series (ResNeXt, Transformers etc.) — https://www.mql5.com/en/articles/17142 (17142), https://www.mql5.com/en/articles/17104 (17104), https://www.mql5.com/en/articles/17069 (17069)
- Other ML / model engineering articles and ONNX / Python integration described in various series: Integrating MQL5 with Data Processing Packages (Part 6) — https://www.mql5.com/en/articles/20235 (20235)

---

## Misc / Cross-cutting & Tools
- Automating Black-Scholes Greeks — https://www.mql5.com/en/articles/20287 (20287)
- Implementing Practical Modules from Other Languages in MQL5 (Parts 04 & 05): time/date/datetime and logging — https://www.mql5.com/en/articles/19035 (19035), https://www.mql5.com/en/articles/20458 (20458)
- Heikin-Ashi & similar indicator articles: https://www.mql5.com/en/articles/19260 (19260), https://www.mql5.com/en/articles/18810 (18810)
- Additional indicators in the indicators/ category on MQL5: see https://www.mql5.com/en/articles/indicators

---

## Next Steps / Suggested workflow
1. Review this manifest for additions/removals and approve the set for Phase 1–3 ingestion.
2. I will fetch each article, parse and capture: (title, author, publish_date, article_id, content HTML, images, code attachments), convert to Markdown, and store in `docs/mql5_handbook/articles/` and image/assets in `docs/mql5_handbook/assets/<article_id>/`.
3. For each article, I will add YAML front-matter with: title, author, original_url, article_id, published_date, tags, phase.
4. Create `docs/mql5_handbook/README.md` with an index and links to all saved articles.
5. Commit the manifest and all content into the repository on a dedicated branch and create a PR.

---

## Provenance & Attributions
- The articles come exclusively from https://www.mql5.com/en/articles/ and are being captured with explicit user permission to copy.
- All saved markdown articles will include a mandatory attribution header linking to the source URL and mention that content is copied verbatim where applicable.

---

*Manifest generated automatically on 2025-12-07 by import script. Once approved for content insertion, I will begin the fetch-and-save step.*
