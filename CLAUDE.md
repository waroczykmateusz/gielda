# Mój Portfel GPW — Claude Context

## Project Overview

Personal portfolio tracker for the Polish stock exchange (GPW) and US markets.
Monitors stock prices, fires Telegram price alerts, detects RSI/SMA trading signals,
runs daily AI-powered analysis via Claude API, and serves a Flask web dashboard.

**Not a library or service** — single-user desktop tool packaged as Windows .exe files.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| Web UI | Flask 3.x + Jinja2 (inline templates in `dashboard.py`) |
| Desktop launcher | Tkinter (`app.py`) |
| Market data | yfinance |
| Notifications | python-telegram-bot + requests |
| AI analysis | Anthropic Claude API (`anthropic` SDK) |
| Scheduling | `schedule` library |
| Packaging | PyInstaller (→ `dist/alert.exe`, `dist/dashboard.exe`) |

---

## Key Files & Directories

```
gielda/
├── app.py            # Tkinter launcher — starts Flask subprocess, opens browser
├── dashboard.py      # Flask web server (routes, templates, backtest engine)
├── core.py           # Shared utilities: file I/O, price fetching, RSI, Telegram
├── alert.py          # Background alert monitor (runs every 15 min)
├── analiza_ai.py     # Daily AI analysis — fetches news, calls Claude API
├── sygnaly.py        # Trading signal detector (RSI/SMA), scheduled at 9:30 & 13:00
├── config.py         # API keys, stock symbols, alert thresholds — plaintext secrets
├── portfel.json      # GPW portfolio state (source of truth)
├── portfel_usa.json  # US portfolio state
├── alert.spec        # PyInstaller spec for alert.py
├── dashboard.spec    # PyInstaller spec for dashboard.py
└── dist/             # Compiled executables (alert.exe, dashboard.exe ~55 MB each)
```

**Key line references:**
- `core.py` shared utilities hub — see [core.py:1](core.py)
- Portfolio JSON schema — see [portfel.json:1](portfel.json)
- Flask routes — see [dashboard.py:1](dashboard.py)
- Market-hours guard — see [core.py](core.py) `czy_gielda_otwarta()`
- `get_base_dir()` path resolution (works for both .py and .exe) — [core.py](core.py)

---

## Build & Run Commands

### Run from source
```bash
python app.py          # Full launcher (Tkinter GUI + Flask on localhost:5000)
python dashboard.py    # Flask dashboard only
python alert.py        # Alert monitor only
python sygnaly.py      # Signal detector only
python analiza_ai.py   # AI analysis (one-shot)
```

### Package to .exe (Windows)
```bash
pyinstaller alert.spec
pyinstaller dashboard.spec
# Output: dist/alert.exe, dist/dashboard.exe
```

### Windows shortcut
```bat
start_dashboard.bat    # Calls python app.py
```

> **No test suite exists.** Manual testing only.

---

## Configuration

`config.py` holds all secrets and settings:
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` — Telegram bot credentials
- `ANTHROPIC_API_KEY` — Claude API key
- `SPOLKI` — dict of monitored symbols with price alert thresholds
- `CZESTOTLIWOSC_MINUT` — alert check interval (default: 15)

Portfolios are JSON files edited via the dashboard UI or directly:
- `portfel.json` — GPW stocks (symbol keys like `"CRI.WA"`)
- `portfel_usa.json` — US stocks (e.g., `"RKLB"`)

---

## Flask Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Portfolio dashboard (`?tab=gpw\|usa`) |
| GET | `/backtest` | Strategy backtesting |
| POST | `/dodaj` | Add transaction |
| POST | `/ustaw_alert` | Set price alert thresholds |

---

## Additional Documentation

| Topic | File |
|---|---|
| Architectural patterns & design decisions | [.claude/docs/architectural_patterns.md](.claude/docs/architectural_patterns.md) |
