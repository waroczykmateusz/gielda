# Architectural Patterns

Patterns that appear consistently across multiple files in this project.

---

## 1. Functional Module Organization (No OOP)

All modules use top-level functions — no classes except the Flask `app` instance.
State is passed explicitly or stored in globals/JSON files.

Applies to: `core.py`, `alert.py`, `sygnaly.py`, `analiza_ai.py`

```
core.py       → wczytaj_portfel(), pobierz_cene(), analizuj_spolke(), wyslij_telegram()
alert.py      → sprawdz_alerty() called by scheduler
sygnaly.py    → sprawdz_sygnaly() called by scheduler
analiza_ai.py → analizuj_dzisiaj() called at startup or on schedule
```

**Implication:** There is no dependency injection. Functions directly import from `config.py`
and call `core.py` utilities. Adding new modules should follow this flat function style.

---

## 2. `core.py` as Shared Utility Hub

Every module imports from `core.py`. It is the single shared layer for:
- Portfolio read/write (`wczytaj_portfel`, `zapisz_portfel`)
- Price fetching (`pobierz_cene`, `pobierz_dane_dzienne`)
- Technical indicators (`analizuj_spolke` → RSI 14-period, SMA 20/50/200)
- Telegram dispatch (`wyslij_telegram`)
- Market-hours check (`czy_gielda_otwarta`)
- Path resolution (`get_base_dir` — handles both .py and .exe)

**Do not duplicate** any of these in other modules. Extend `core.py` for new shared logic.

---

## 3. File-Based State Persistence

No database. All persistent state lives in JSON files:
- `portfel.json` / `portfel_usa.json` — portfolio positions (dict keyed by ticker symbol)
- Written via `json.dump` directly (no atomic writes, no locking)

In-memory state (not persisted across restarts):
- `wyslane_alerty` dict in `alert.py` — tracks which alerts have been sent this session

**Implication:** Concurrent writes from multiple processes are unsafe. The dashboard and alert
monitor should not be writing to the same JSON file simultaneously.

---

## 4. Scheduled Background Jobs via `schedule`

`alert.py`, `sygnaly.py`, and `analiza_ai.py` each run their own `schedule` loop.
They are independent processes — no inter-process communication.

Typical pattern in each module:
```python
schedule.every(CZESTOTLIWOSC_MINUT).minutes.do(sprawdz_alerty)
while True:
    schedule.run_pending()
    time.sleep(30)
```

Scheduled times (all CET):
- **Alert monitor:** every 15 min during GPW (9:00–17:05) and US (15:30–22:00) hours
- **Signal detector:** 9:30 and 13:00 daily
- **AI analysis:** 8:00 daily
- **Daily report:** 17:06

---

## 5. Market-Hours Guard

`czy_gielda_otwarta()` in `core.py` returns `bool`. Callers skip analysis outside trading hours.

GPW: Mon–Fri 9:00–17:05 CET  
USA: Mon–Fri 15:30–22:00 CET  
Weekends: always skipped

All scheduled modules call this before doing any price-sensitive work.

---

## 6. Silent Failure Pattern

Errors are caught and suppressed with try/except, returning `None` or a default:

```python
try:
    cena = pobierz_cene(symbol)
except Exception:
    return None
```

No centralized logging exists — only `print()` to stdout. Failures are invisible when running
as a packaged `.exe` (no console window: `console=False` in `.spec` files).

**Implication:** When debugging issues, temporarily add `console=True` in the `.spec` file
or run the `.py` script directly to see output.

---

## 7. Inline Jinja2 Templates (No Template Files)

`dashboard.py` renders HTML as Python multi-line strings via `render_template_string()`.
There is no `templates/` directory.

All dashboard HTML, CSS, and JavaScript lives inside `dashboard.py`.
The dark-theme color palette (`#0f1117` bg, `#26c281` green, `#e74c3c` red, `#f39c12` orange)
is defined inline in those strings.

**Implication:** To change the UI, edit the string literals inside `dashboard.py`.

---

## 8. Portfolio Entry Schema

Both `portfel.json` and `portfel_usa.json` use the same structure:

```json
{
  "TICKER": {
    "nazwa": "Company Name",
    "akcje": 62,
    "srednia_cena": 30.81,
    "alert_powyzej": 65.0,
    "alert_ponizej": 45.0
  }
}
```

GPW tickers use `.WA` suffix (e.g., `"CRI.WA"`). US tickers are plain (e.g., `"RKLB"`).

---

## 9. Trading Signal Structure

`analizuj_spolke(symbol)` in `core.py` returns a list of tuples:

```python
(typ: str, opis: str, kolor: str)
# e.g.: ("SILNY KUP", "RSI tygodniowy=25 - mocno wyprzedana", "#26c281")
```

Signal types: `"SILNY KUP"`, `"KUP"`, `"UWAGA"`, `"SPRZEDAJ"`, `"SILNA SPRZEDAŻ"`  
Colors map to: green (`#26c281`), red (`#e74c3c`), orange (`#f39c12`)

This tuple list is consumed by both the dashboard renderer and the Telegram notifier.

---

## 10. Path Resolution for .exe Compatibility

`get_base_dir()` in `core.py` resolves the data directory for both `.py` and PyInstaller `.exe` modes:

```python
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
```

All file I/O (JSON reads/writes) must use `get_base_dir()` as the base path.
Never use relative paths or `__file__` directly in other modules.
