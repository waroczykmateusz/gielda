import os
from datetime import datetime

from .notify import wyslij_telegram
from .prices import pobierz_dane_dzienne
from .storage import get_portfolio


def _wskazniki_bulk(symbole):
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

            delta = c.diff()
            rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
            rsi = round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)

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

            sma50 = round(float(c.rolling(50).mean().iloc[-1]), 2) if len(c) >= 50 else None
            sma200 = round(float(c.rolling(200).mean().iloc[-1]), 2) if len(c) >= 200 else None

            zmiana = round(float((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100), 2) if len(c) >= 2 else 0.0

            wyniki[symbol] = {
                "rsi": rsi,
                "macd_hist": hist,
                "macd_cross": macd_cross,
                "sma50": sma50,
                "sma200": sma200,
                "zmiana": zmiana,
            }
    except Exception as e:
        print(f"Blad wskaznikow bulk: {e}")
    return wyniki


def _sekcja_dzienna(portfel, waluta, wskazniki):
    linie = []
    suma_dzienny_pl = 0.0

    for symbol, info in portfel.items():
        cena, zmiana_dzis = pobierz_dane_dzienne(symbol)
        if cena is None:
            continue
        wartosc = round(cena * info["akcje"], 2)
        dzienny_pl = round(wartosc * zmiana_dzis / 100, 2)
        suma_dzienny_pl += dzienny_pl
        emoji = "🟢" if zmiana_dzis >= 0 else "🔴"
        linie.append(
            f"{emoji} <b>{info['nazwa']}</b>: {zmiana_dzis:+.2f}% ({dzienny_pl:+.2f} {waluta})"
        )

    if linie:
        suma_emoji = "📈" if suma_dzienny_pl >= 0 else "📉"
        linie.append(f"\n{suma_emoji} <b>Łącznie dziś:</b> {suma_dzienny_pl:+.2f} {waluta}")

    return linie


def _rekomendacja_ai(portfel, waluta, wskazniki, rynek_label):
    def opis():
        linie = []
        for symbol, info in portfel.items():
            cena, zmiana = pobierz_dane_dzienne(symbol)
            if cena is None:
                continue
            wsk = wskazniki.get(symbol, {})
            rsi = wsk.get("rsi", "?")
            hist = wsk.get("macd_hist", "?")
            cross = f" MACD={wsk['macd_cross']}" if wsk.get("macd_cross") else ""
            sma50 = wsk.get("sma50", "?")
            sma200 = wsk.get("sma200", "?")
            zm = wsk.get("zmiana", zmiana or 0)
            w = round(cena * info["akcje"], 2)
            z = round(info["srednia_cena"] * info["akcje"], 2)
            proc = round((w - z) / z * 100, 2) if z else 0
            linie.append(
                f"{symbol}: cena={cena} akcje={info['akcje']} P&L={proc:+.1f}% "
                f"dziś={zm:+.1f}% RSI={rsi} MACDhist={hist}{cross} SMA50={sma50} SMA200={sma200}"
            )
        return "\n".join(linie) or "brak"

    prompt = f"""Jesteś polskim doradcą inwestycyjnym. Na podstawie danych z dzisiejszego zamknięcia sesji podaj KONKRETNE rekomendacje na jutro.

{rynek_label} ({waluta}):
{opis()}

Legenda: P&L=zysk od zakupu, dziś=zmiana sesji, RSI<30 wyprzedana/>70 wykupiona, MACDhist>0 trend wzrostowy, MACD=KUP/UWAGA crossover, SMA50/200=średnie kroczące

Napisz krótko po polsku (max 200 słów):
**OCENA DNIA**: 1-2 zdania co się działo w portfelu
**NA JUTRO**: 2-3 konkretne punkty (co dokupić/sprzedać/obserwować z uzasadnieniem)
**PRIORYTET**: jedna najważniejsza akcja

Bez wstępu, konkretnie."""

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
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

        synteza_prompt = f"""Poniżej znajdują się 3 niezależne analizy portfela inwestycyjnego.
Wyciągnij KONSENSUS — wnioski i rekomendacje które powtarzają się lub są zgodne.
Zignoruj sprzeczności i opinie pojawiające się tylko raz.

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
        return final.content[0].text.strip()
    except Exception as e:
        print(f"Blad rekomendacji AI: {e}")
        return None


def raport_gpw():
    if datetime.now().weekday() >= 5:
        return

    portfel = get_portfolio("gpw")
    if not portfel:
        return

    wskazniki = _wskazniki_bulk(list(portfel.keys()))

    linie = [f"📊 <b>GPW — {datetime.now().strftime('%d.%m.%Y')}</b>\n"]
    linie.extend(_sekcja_dzienna(portfel, "zł", wskazniki))
    wyslij_telegram("\n".join(linie))

    rekomen = _rekomendacja_ai(portfel, "zł", wskazniki, "GPW")
    if rekomen:
        wyslij_telegram(f"🤖 <b>Rekomendacja AI GPW — {datetime.now().strftime('%d.%m.%Y')}</b>\n\n{rekomen}")


def raport_usa():
    if datetime.now().weekday() >= 5:
        return

    portfel = get_portfolio("usa")
    if not portfel:
        return

    wskazniki = _wskazniki_bulk(list(portfel.keys()))

    linie = [f"📊 <b>USA — {datetime.now().strftime('%d.%m.%Y')}</b>\n"]
    linie.extend(_sekcja_dzienna(portfel, "$", wskazniki))
    wyslij_telegram("\n".join(linie))

    rekomen = _rekomendacja_ai(portfel, "$", wskazniki, "USA")
    if rekomen:
        wyslij_telegram(f"🤖 <b>Rekomendacja AI USA — {datetime.now().strftime('%d.%m.%Y')}</b>\n\n{rekomen}")
