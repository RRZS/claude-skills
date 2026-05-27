# weather-polymarket-bot

A safe **paper-trading** scanner for Polymarket weather markets.

This bot discovers active U.S. city weather markets on Polymarket, pulls the
official NOAA / NWS forecast for the relevant city and date, computes an
implied edge, and logs simulated entries to CSV. **It does not place real
trades in v1.** There is no private key, no signing, no order submission.

Supported cities in v1: **New York** and **Chicago**.

---

## Quick start

```bash
git clone <this repo>
cd weather-polymarket-bot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env to set NWS_USER_AGENT (NOAA requires a contact identifier).
# Everything else has safe defaults.

python -m weather_polymarket_bot           # single scan
python -m weather_polymarket_bot --loop    # rescan every POLL_INTERVAL_SEC seconds
```

A successful run prints clean console alerts and appends rows to
`logs/paper_trades.csv`.

---

## What it does, step by step

1. **Discover markets.** Pulls active markets from the public Polymarket
   Gamma API (`gamma-api.polymarket.com`). No auth.
2. **Filter for weather.** Keeps only markets whose question mentions a
   supported city and a temperature.
3. **Parse.** Extracts `(city, target_date, temperature_bracket,
   token_id, outcome_label, market_close_time)` from each market /
   outcome pair. Ambiguous markets are dropped.
4. **Forecast.** Calls NOAA / NWS `api.weather.gov` for the city's daily
   high on `target_date`.
5. **Price.** Calls Polymarket's public CLOB endpoints (`clob.polymarket.com`)
   for midpoint / book on each token. Wide-spread books are dropped.
6. **Signal.** Computes a Gaussian-bracket probability from the forecast
   and compares to the market YES price. Signals when `edge >=
   MIN_EDGE`.
7. **Risk-check.** Caps position size, daily signal count, and rejects
   markets with unclear resolution sources.
8. **Paper trade.** Appends a row to `logs/paper_trades.csv` and prints
   a console alert. No funds are moved.

---

## Project layout

```
weather-polymarket-bot/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── src/
│   └── weather_polymarket_bot/
│       ├── __init__.py
│       ├── __main__.py            # CLI entry point
│       ├── config.py              # env-driven settings
│       ├── models.py              # dataclasses: WeatherMarket, Signal, ...
│       ├── scanner.py             # orchestration loop
│       ├── polymarket/
│       │   ├── gamma_client.py    # discover active markets
│       │   └── clob_client.py     # public price / book endpoints
│       ├── weather/
│       │   └── nws_client.py      # NOAA NWS forecast
│       ├── parsing/
│       │   └── market_parser.py   # question -> structured WeatherMarket
│       ├── signals/
│       │   └── signal_engine.py   # forecast + price -> edge
│       ├── trading/
│       │   └── paper_trader.py    # CSV logging only, no real trades
│       ├── risk/
│       │   └── risk_controls.py   # position cap, daily cap, sanity checks
│       └── notifications/
│           └── console.py         # clean stdout formatting
├── tests/
│   ├── test_market_parser.py
│   ├── test_signal_engine.py
│   └── test_risk_controls.py
└── logs/                          # paper_trades.csv lands here
```

---

## Configuration

All config is read from environment variables. See `.env.example` for the
full list. The important ones:

| Variable                  | Default                          | Meaning |
|---------------------------|----------------------------------|---------|
| `NWS_USER_AGENT`          | `weather-polymarket-bot (contact@example.com)` | **NOAA requires this.** Put a real contact. |
| `CITIES`                  | `new_york,chicago`               | Which cities to scan. |
| `MIN_EDGE`                | `0.05`                           | Minimum edge (true_prob - market_price) to fire a signal. |
| `MAX_SPREAD`              | `0.05`                           | Reject books whose (ask - bid) exceeds this. |
| `MAX_POSITION_USD`        | `25.0`                           | Simulated cap per signal. |
| `MAX_DAILY_SIGNALS`       | `20`                             | Per-day cap. |
| `FORECAST_TEMP_STDDEV_F`  | `2.5`                            | Gaussian σ for forecast-error model. |
| `POLL_INTERVAL_SEC`       | `300`                            | Sleep between scans in `--loop` mode. |
| `PAPER_TRADES_CSV`        | `logs/paper_trades.csv`          | Output file. |
| `LOG_LEVEL`               | `INFO`                           | Standard logging level. |

---

## CSV schema

`logs/paper_trades.csv` columns:

```
timestamp_utc, market_id, token_id, city, target_date, bracket_low_f,
bracket_high_f, bracket_kind, outcome_label, forecast_high_f, market_yes_price,
true_probability, edge, position_usd, market_close_time, resolution_source
```

`bracket_kind` is one of `range`, `at_or_below`, `at_or_above`.

---

## Running tests

```bash
pip install -r requirements.txt
pytest -v
```

Tests cover market parsing (titles → structured brackets) and signal logic
(forecast + price → edge). They do not hit any network.

---

## Parser-coverage diagnostic

Before relying on the parser, verify it actually matches today's
Polymarket weather markets. The bundled diagnostic hits ONLY the public
Gamma endpoint and reports how many active markets survive each filter:

```bash
PYTHONPATH=src python scripts/parser_coverage.py
PYTHONPATH=src python scripts/parser_coverage.py --json drops.json   # full dump
```

It prints per-stage counts, examples of markets the parser handled, and
examples of markets that mention a supported city + temperature but
didn't fully parse (with a list of reasons). If you see a dominant
failure pattern, extend the regexes in `parsing/market_parser.py` and
re-run.

---

## Safety guarantees in v1

- No private key is ever read.
- No HTTP POST is made to any signing or order endpoint.
- The only outbound calls are GETs to `gamma-api.polymarket.com`,
  `clob.polymarket.com`, and `api.weather.gov`.
- Every "trade" is a CSV row.

---

## TODO — future versions

**Do not implement these in v1.**

- **v2: Live trading via authenticated CLOB.** Wire in `py-clob-client-v2`,
  load `POLY_PRIVATE_KEY` from env, sign EIP-712 orders, submit to the
  CLOB `/order` endpoint, track fills via WebSocket. Gate behind an
  explicit `--live` flag and require a second confirmation.
- **v2: Telegram notifications.** Add a `notifications/telegram.py`
  module using a bot token + chat ID; mirror the console alerts.
- **v2: Historical forecast-error calibration.** Replace the fixed σ in
  `signals/signal_engine.py` with a per-horizon empirical distribution
  built from a NOAA forecast archive.
- **v2: Position management.** Track open positions, mark-to-market,
  exit signals, P&L attribution. v1 only logs entries.
- **v2: Multi-city expansion.** Add Boston, LA, Miami, etc. by extending
  `weather/nws_client.py::CITY_COORDS` and the parser's city alias map.
- **v2: WebSocket order book.** Replace polled `/book` calls with the
  CLOB WSS feed for lower latency.

---

## API notes — these may shift, read carefully

- **Polymarket Gamma API response shape varies.** `outcomes`,
  `outcomePrices`, and `clobTokenIds` are sometimes returned as JSON
  strings and sometimes as native arrays. `gamma_client.py` normalizes
  both forms.
- **Polymarket market questions are free text.** The parser handles the
  most common patterns (`NYC high temperature on March 15`, `between X
  and Y °F`, `X °F or below`) but unusual phrasings are intentionally
  dropped instead of being guessed at.
- **NWS `api.weather.gov` requires a `User-Agent` header.** Requests
  without one are rejected. Forecast periods cover ~7 days; markets
  resolving further out have no forecast and are skipped.

---

## License

MIT.
