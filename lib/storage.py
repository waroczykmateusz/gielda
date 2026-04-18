from decimal import Decimal
from .db import connect


def _row_to_dict(row):
    symbol, nazwa, akcje, srednia, alert_up, alert_down = row
    return {
        "nazwa": nazwa,
        "akcje": float(akcje),
        "srednia_cena": float(srednia),
        "alert_powyzej": float(alert_up) if alert_up is not None else None,
        "alert_ponizej": float(alert_down) if alert_down is not None else None,
    }


def get_portfolio(market):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT symbol, nazwa, akcje, srednia_cena, alert_powyzej, alert_ponizej "
            "FROM positions WHERE market = %s ORDER BY symbol",
            (market,),
        )
        return {row[0]: _row_to_dict(row) for row in cur.fetchall()}


def upsert_position(market, symbol, nazwa, akcje, srednia_cena, alert_powyzej=None, alert_ponizej=None):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO positions (market, symbol, nazwa, akcje, srednia_cena, alert_powyzej, alert_ponizej)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (market, symbol) DO UPDATE SET
                nazwa = EXCLUDED.nazwa,
                akcje = EXCLUDED.akcje,
                srednia_cena = EXCLUDED.srednia_cena,
                alert_powyzej = COALESCE(EXCLUDED.alert_powyzej, positions.alert_powyzej),
                alert_ponizej = COALESCE(EXCLUDED.alert_ponizej, positions.alert_ponizej)
            """,
            (market, symbol, nazwa, Decimal(str(akcje)), Decimal(str(srednia_cena)),
             Decimal(str(alert_powyzej)) if alert_powyzej is not None else None,
             Decimal(str(alert_ponizej)) if alert_ponizej is not None else None),
        )


def delete_position(market, symbol):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM positions WHERE market = %s AND symbol = %s", (market, symbol))


def set_alerts(market, symbol, alert_powyzej, alert_ponizej):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE positions SET alert_powyzej = %s, alert_ponizej = %s "
            "WHERE market = %s AND symbol = %s",
            (
                Decimal(str(alert_powyzej)) if alert_powyzej is not None else None,
                Decimal(str(alert_ponizej)) if alert_ponizej is not None else None,
                market,
                symbol,
            ),
        )


def apply_transaction(market, symbol, nazwa, akcje_delta, cena, typ):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT akcje, srednia_cena FROM positions WHERE market = %s AND symbol = %s",
            (market, symbol),
        )
        row = cur.fetchone()
        akcje_delta = Decimal(str(akcje_delta))
        cena = Decimal(str(cena))

        if row is None:
            if typ != "kup":
                return
            cur.execute(
                "INSERT INTO positions (market, symbol, nazwa, akcje, srednia_cena) "
                "VALUES (%s, %s, %s, %s, %s)",
                (market, symbol, nazwa or symbol, akcje_delta, cena),
            )
            return

        stare_akcje, stara_srednia = row
        if typ == "kup":
            nowa_akcje = stare_akcje + akcje_delta
            nowa_srednia = ((stare_akcje * stara_srednia) + (akcje_delta * cena)) / nowa_akcje
            cur.execute(
                "UPDATE positions SET akcje = %s, srednia_cena = %s "
                "WHERE market = %s AND symbol = %s",
                (nowa_akcje, round(nowa_srednia, 2), market, symbol),
            )
        else:
            pozostale = stare_akcje - akcje_delta
            if pozostale <= 0:
                cur.execute(
                    "DELETE FROM positions WHERE market = %s AND symbol = %s",
                    (market, symbol),
                )
            else:
                cur.execute(
                    "UPDATE positions SET akcje = %s WHERE market = %s AND symbol = %s",
                    (pozostale, market, symbol),
                )
