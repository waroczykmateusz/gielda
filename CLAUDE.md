# Mój Portfel GPW — Claude Context

## Project Overview

Aplikacja webowa (deploy: Vercel) do trackowania portfela na GPW i giełdach USA.
Pokazuje ceny, RSI/MACD/SMA, sygnały i backtesty. Codzienne joby (cron) wysyłają
analizę AI newsów i raport portfela na Telegram.

**Architektura webowa, nie desktop.** Wcześniej istniała wersja desktop (Tkinter +
nieskończona pętla) — została całkowicie usunięta.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Vercel Serverless Functions (Python 3 via `@vercel/python`) |
| API framework | Flask 3.x (jeden Flask app per plik w `api/`) |
| DB | Vercel Postgres (psycopg 3) |
| Market data | yfinance |
| Notifications | requests → Telegram Bot API |
| AI analysis | Anthropic Claude API (`claude-sonnet-4-6`) |
| Scheduler | Vercel Cron Jobs (zdefiniowane w `vercel.json`) |

---

## Struktura projektu

```
gielda/
├── frontend/                  # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js             # fetch wrapper, base = '/api'
│   │   ├── main.jsx, index.css
│   │   └── components/
│   │       ├── PortfolioTab.jsx, StockCard.jsx, SummaryBox.jsx
│   │       ├── TransactionForm.jsx, AlertForm.jsx
│   │       └── BacktestPage.jsx       # per-symbol button trigger
│   ├── package.json, vite.config.js
│   └── index.html
├── api/                       # Vercel Python functions
│   ├── index.py               # Flask: /api/portfolio/<tab>, /api/transaction, /api/alert, /api/health
│   ├── backtest.py            # Flask: GET /api/backtest?symbol=X&market=Y
│   └── cron/
│       ├── morning.py         # GET /api/cron/morning  (08:00 PL)
│       └── evening.py         # GET /api/cron/evening  (17:00 PL)
├── lib/                       # Shared utils (zastępuje stary core.py)
│   ├── db.py                  # psycopg connection context manager
│   ├── storage.py             # CRUD positions w Postgres
│   ├── alerts_state.py        # sent_alerts (TTL dedup)
│   ├── prices.py              # yfinance: pobierz_cene, pobierz_dane_dzienne
│   ├── analysis.py            # analizuj_spolke, wykryj_konflikt (RSI vs MACD), analizuj_konflikt_sygnalu
│   ├── ai.py                  # dzienna_analiza (newsy + Claude)
│   ├── notify.py              # wyslij_telegram (secrets z os.environ)
│   ├── alerts.py              # sprawdz_alerty (price thresholds → Telegram)
│   ├── signals.py             # sprawdz_sygnaly (RSI/MACD/SMA → Telegram)
│   ├── report.py              # dzienny_raport (podsumowanie portfela)
│   └── sanitize.py            # numpy → JSON-safe values
├── migrations/
│   └── 001_init.sql           # schemat Postgres (positions, sent_alerts)
├── scripts/
│   └── import_portfolios.py   # jednorazowy import JSON → DB
├── vercel.json                # crons + rewrites + buildCommand
├── requirements.txt           # Python deps
└── .env.example               # template env vars
```

---

## REST API

| Method | Route | Source | Notes |
|---|---|---|---|
| GET | `/api/portfolio/<tab>` | [api/index.py](api/index.py) | tab: `gpw` / `usa` |
| POST | `/api/transaction` | [api/index.py](api/index.py) | `{tab, symbol, nazwa, akcje, cena, typ}` |
| POST | `/api/alert` | [api/index.py](api/index.py) | `{tab, symbol, alert_powyzej, alert_ponizej}` |
| GET | `/api/backtest?symbol=X&market=Y` | [api/backtest.py](api/backtest.py) | per-symbol (limit 10s) |
| GET | `/api/cron/morning` | [api/cron/morning.py](api/cron/morning.py) | wymaga `Authorization: Bearer ${CRON_SECRET}` |
| GET | `/api/cron/evening` | [api/cron/evening.py](api/cron/evening.py) | jw. |
| GET | `/api/health` | [api/index.py](api/index.py) | smoke test |

---

## Cron schedule (vercel.json)

| Cron | UTC | Czas PL (CEST/CET) | Akcje |
|---|---|---|---|
| morning | `0 6 * * 1-5` | 08:00 / 07:00 | `lib.ai.dzienna_analiza()` |
| evening | `0 15 * * 1-5` | 17:00 / 16:00 | `signals.sprawdz_sygnaly()` + `alerts.sprawdz_alerty()` + `report.dzienny_raport()` |

Vercel Hobby pozwala na max 2 cron joby z częstotliwością 1x dziennie. Bardziej granularny harmonogram = Vercel Pro lub zewnętrzny cron.

---

## Database schema

```sql
positions (market, symbol, nazwa, akcje, srednia_cena, alert_powyzej, alert_ponizej)  PK (market, symbol)
sent_alerts (alert_key, price, sent_at, expires_at)  PK (alert_key)
```

Patrz [migrations/001_init.sql](migrations/001_init.sql).

---

## Environment variables (Vercel Project Settings)

```
POSTGRES_URL       # auto-injected przez Vercel Postgres
TELEGRAM_TOKEN
TELEGRAM_CHAT_ID
ANTHROPIC_API_KEY
CRON_SECRET        # Vercel auto-generuje dla cron jobs
```

Lokalnie: `vercel env pull .env.local`.

---

## Run & deploy

### Lokalnie (development)
```bash
# Frontend dev (proxy /api → vercel dev)
cd frontend && npm install && npm run dev

# Backend serverless lokalnie (osobny terminal)
vercel dev
```

### Deploy
```bash
git push  # Vercel auto-deploy z brancha podpiętego do projektu
```

### Migracja danych (jednorazowo, lokalnie)
```bash
vercel env pull .env.local
psql $POSTGRES_URL -f migrations/001_init.sql
python scripts/import_portfolios.py .data-backup/portfel.json .data-backup/portfel_usa.json
```

---

## Testing crons lokalnie
```bash
curl http://localhost:3000/api/cron/morning -H "Authorization: Bearer $CRON_SECRET"
curl http://localhost:3000/api/cron/evening -H "Authorization: Bearer $CRON_SECRET"
```

> **Brak test suite — tylko manualne testy.**
