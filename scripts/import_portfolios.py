"""
Jednorazowy import portfeli z plików JSON do Vercel Postgres.

Użycie (lokalnie):
  1. `vercel env pull .env.local` — pobiera POSTGRES_URL z Vercel
  2. `set POSTGRES_URL=... ` (Windows) lub `export POSTGRES_URL=...` (Linux/Mac)
  3. `python scripts/import_portfolios.py portfel.json portfel_usa.json`

Argument 1 → plik GPW (rynek 'gpw'), argument 2 → plik USA (rynek 'usa').
Pomija pliki które nie istnieją.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.storage import upsert_position


def import_file(path, market):
    if not os.path.exists(path):
        print(f"  [SKIP] {path} — nie istnieje")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  [{market.upper()}] {path}: {len(data)} spółek")
    for symbol, info in data.items():
        upsert_position(
            market=market,
            symbol=symbol,
            nazwa=info["nazwa"],
            akcje=info["akcje"],
            srednia_cena=info["srednia_cena"],
            alert_powyzej=info.get("alert_powyzej"),
            alert_ponizej=info.get("alert_ponizej"),
        )
        print(f"    + {symbol} ({info['nazwa']})")


def main():
    args = sys.argv[1:]
    if not args:
        args = ["portfel.json", "portfel_usa.json"]
    if len(args) >= 1:
        import_file(args[0], "gpw")
    if len(args) >= 2:
        import_file(args[1], "usa")
    print("Done.")


if __name__ == "__main__":
    main()
