import os
from datetime import datetime

from .notify import wyslij_telegram, wyslij_telegram_dlugi
from .prices import pobierz_cene
from .storage import get_portfolio


def _sekcja(portfel, waluta):
    linie = []
    suma_w = suma_z = 0
    for symbol, info in portfel.items():
        cena = pobierz_cene(symbol)
        if cena is None:
            continue
        w = round(cena * info["akcje"], 2)
        z = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(w - z, 2)
        proc = round((zysk / z) * 100, 2) if z else 0
        emoji = "🟢" if zysk >= 0 else "🔴"
        linie.append(
            f"{emoji} <b>{info['nazwa']}</b>: {cena} {waluta} "
            f"({zysk:+.2f} {waluta} / {proc:+.1f}%)"
        )
        suma_w += w
        suma_z += z
    suma_zysk = round(suma_w - suma_z, 2)
    suma_zwrot = round((suma_zysk / suma_z) * 100, 2) if suma_z else 0
    emoji_t = "🟢" if suma_zysk >= 0 else "🔴"
    linie.append(
        f"\n{emoji_t} <b>Lacznie:</b> {round(suma_w, 2)} {waluta} "
        f"({suma_zysk:+.2f} {waluta} / {suma_zwrot:+.1f}%)"
    )
    return linie


def dzienny_raport(market=None):
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    if market == "gpw":
        linie = [f"🇵🇱 <b>Zamknięcie GPW — {teraz.strftime('%d.%m.%Y')}</b>\n"]
        linie.extend(_sekcja(get_portfolio("gpw"), "zł"))
    elif market == "usa":
        linie = [f"🇺🇸 <b>Zamknięcie USA — {teraz.strftime('%d.%m.%Y')}</b>\n"]
        linie.extend(_sekcja(get_portfolio("usa"), "$"))
    else:
        linie = [f"📊 <b>Podsumowanie {teraz.strftime('%d.%m.%Y')}</b>\n"]
        linie.append("🇵🇱 <b>GPW</b>")
        linie.extend(_sekcja(get_portfolio("gpw"), "zł"))
        linie.append("\n🇺🇸 <b>USA</b>")
        linie.extend(_sekcja(get_portfolio("usa"), "$"))
    wyslij_telegram_dlugi("\n".join(linie))


def _wskazniki_bulk(symbole):
    """Pobiera RSI, MACD i zmianę dzienną dla listy symboli jednym requestem."""
    import yfinance as yf
    import pandas as pd

    wyniki = {}
    try:
        raw = yf.download(symbole, period="6mo", interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw[["Close"]]
            close.columns = symbole[:1]

        for symbol in symbole:
            if symbol not in close.columns:
                continue
            c = close[symbol].dropna()
            if len(c) < 30:
                continue

            # RSI 14
            delta = c.diff()
            rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
            rsi = round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)

            # MACD
            ema12 = c.ewm(span=12, adjust=False).mean()
            ema26 = c.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            sig = macd.ewm(span=9, adjust=False).mean()
            hist = round(float((macd - sig).iloc[-1]), 3)
            macd_cross = ""
            if len(macd) >= 2:
                if macd.iloc[-1] > sig.iloc[-1] and macd.iloc[-2] <= sig.iloc[-2]:
                    macd_cross = "KUP"
                elif macd.iloc[-1] < sig.iloc[-1] and macd.iloc[-2] >= sig.iloc[-2]:
                    macd_cross = "UWAGA"

            # zmiana dzienna %
            zmiana = round(float((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100), 2) if len(c) >= 2 else 0.0

            wyniki[symbol] = {"rsi": rsi, "macd_hist": hist, "macd_cross": macd_cross, "zmiana": zmiana}
    except Exception as e:
        print(f"Blad wskaznikow bulk: {e}")
    return wyniki


def rekomendacja_dzienna(market):
    if datetime.now().weekday() >= 5:
        return

    portfel = get_portfolio(market)
    waluta = "zł" if market == "gpw" else "$"
    rynek_label = "GPW" if market == "gpw" else "USA"
    wskazniki = _wskazniki_bulk(list(portfel.keys()))

    linie_opisu = []
    for symbol, info in portfel.items():
        cena = pobierz_cene(symbol)
        if cena is None:
            continue
        z = round(info["srednia_cena"] * info["akcje"], 2)
        w = round(cena * info["akcje"], 2)
        proc = round((w - z) / z * 100, 2) if z else 0
        wsk = wskazniki.get(symbol, {})
        rsi = wsk.get("rsi", "?")
        hist = wsk.get("macd_hist", "?")
        cross = f" MACD={wsk['macd_cross']}" if wsk.get("macd_cross") else ""
        zmiana = wsk.get("zmiana", 0)
        linie_opisu.append(
            f"{symbol}: cena={cena} P&L={proc:+.1f}% "
            f"dziś={zmiana:+.1f}% RSI={rsi} MACDhist={hist}{cross}"
        )
    opis_portfela = "\n".join(linie_opisu) or "brak danych"

    prompt = f"""Jesteś polskim doradcą inwestycyjnym. Na podstawie danych z zamknięcia sesji {rynek_label} podaj KONKRETNE rekomendacje na jutro.

{rynek_label} ({waluta}):
{opis_portfela}

Legenda: P&L=zysk od zakupu, dziś=zmiana sesji, RSI<30 wyprzedana/>70 wykupiona, MACDhist>0 trend wzrostowy, MACD=KUP/UWAGA crossover

Napisz krótko po polsku (max 200 słów):
**OCENA DNIA**: 1-2 zdania co się działo w portfelu
**NA JUTRO**: 2-3 konkretne punkty (co dokupić/sprzedać/obserwować z uzasadnieniem)
**PRIORYTET**: jedna najważniejsza akcja

Bez wstępu, konkretnie."""

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return
        client = anthropic.Anthropic(api_key=api_key)

        analizy = []
        for _ in range(3):
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )
            analizy.append(msg.content[0].text.strip())

        synteza_prompt = f"""Poniżej znajdują się 3 niezależne analizy portfela {rynek_label} wygenerowane przez AI.
Wyciągnij KONSENSUS — wnioski i rekomendacje które się powtarzają. Zignoruj sprzeczności pojawiające się tylko raz.

=== ANALIZA 1 ===
{analizy[0]}

=== ANALIZA 2 ===
{analizy[1]}

=== ANALIZA 3 ===
{analizy[2]}

Napisz FINALNĄ rekomendację po polsku (max 200 słów):
**OCENA DNIA**: najczęściej powtarzająca się ocena
**NA JUTRO**: tylko punkty z co najmniej 2 analiz
**PRIORYTET**: jedna akcja zgodna z większością

Konkretnie, bez wstępu."""

        final = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0,
            messages=[{"role": "user", "content": synteza_prompt}],
        )
        tekst = final.content[0].text.strip()
        flag = "🇵🇱" if market == "gpw" else "🇺🇸"
        wyslij_telegram(f"{flag} <b>Rekomendacja AI {rynek_label} — {datetime.now().strftime('%d.%m.%Y')}</b>\n\n{tekst}")
    except Exception as e:
        print(f"Blad rekomendacji AI {market}: {e}")
