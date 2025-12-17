# News & Calendar Ingest

Herald provides an opt-in News and Economic Calendar ingest pipeline.

How to enable
- Set `NEWS_INGEST_ENABLED=1` in env OR set `config['news']['enabled'] = true` in your config file.
- Ensure `ML` instrumentation is enabled (the ingest writes events to the ML collector).

Environment variables (examples)
- `NEWSAPI_KEY` (optional): API key for NewsAPI.org
- `FRED_API_KEY` (optional): API key for FRED (macroeconomic series)
- `ECON_CAL_API_KEY` (optional): API key for TradingEconomics or other calendar provider
- `NEWS_RSS_FEEDS` (recommended): comma-separated RSS feeds for non-API fallback
- `NEWS_USE_RSS` (true|false): prefer RSS when available
- `NEWS_CACHE_TTL` (seconds): how long to cache news/calendar responses (default 300)
- `NEWS_INGEST_INTERVAL` (seconds): polling interval for ingest (default 300)
- `NEWS_ALERT_WINDOW` (seconds): how long to pause trading after a high-impact event (default 600)

What it records
- `news_event`: headline, body, provider, ts, meta
- `calendar_event`: economic calendar event with normalized `meta.importance` (low|medium|high)
- `monitor.news_alert`: high-impact event alert emitted by TradeMonitor

Notes
- The ingest pipeline is non-blocking and writes to the ML collector; if ML is disabled, the ingest is skipped.
- TradeMonitor can pause trading when a high-impact calendar event is detected.
- Tests: `tests/unit/test_news_ingest.py` and gated `tests/integration/test_news_ingest_live.py`.
