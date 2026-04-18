import os
from datetime import datetime

from .notify import wyslij_telegram
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


def dzienny_raport():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    linie = [f"📊 <b>Podsumowanie {teraz.strftime('%d.%m.%Y')}</b>\n"]
    linie.append("🇵🇱 <b>GPW</b>")
    linie.extend(_sekcja(get_portfolio("gpw"), "zl"))
    linie.append("\n🇺🇸 <b>USA</b>")
    linie.extend(_sekcja(get_portfolio("usa"), "$"))
    wyslij_telegram("\n".join(linie))


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


def rekomendacja_dzienna():
    if datetime.now().weekday() >= 5:
        return

    gpw = get_portfolio("gpw")
    usa = get_portfolio("usa")
    wszystkie_symbole = list(gpw.keys()) + list(usa.keys())

    wskazniki = _wskazniki_bulk(wszystkie_symbole)

    def opis(portfel, waluta):
        linie = []
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
            linie.append(
                f"{symbol}: cena={cena} P&L={proc:+.1f}% "
                f"dziś={zmiana:+.1f}% RSI={rsi} MACDhist={hist}{cross}"
            )
        return "\n".join(linie) or "brak"

    prompt = f"""Jesteś polskim doradcą inwestycyjnym. Na podstawie danych z dzisiejszego zamknięcia sesji podaj KONKRETNE rekomendacje na jutro.

GPW ({waluta_gpw}):
{opis(gpw, 'zł')}

USA ($):
{opis(usa, '$')}

Legenda: P&L=zysk od zakupu, dziś=zmiana sesji, RSI<30 wyprzedana/>70 wykupiona, MACDhist>0 trend wzrostowy, MACD=KUP/UWAGA crossover

Napisz krótko po polsku (max 200 słów):
**OCENA DNIA**: 1-2 zdania co się działo w portfelu
**NA JUTRO**: 2-3 konkretne punkty (co dokupić/sprzedać/obserwować z uzasadnieniem)
**PRIORYTET**: jedna najważniejsza akcja

Bez wstępu, konkretnie.""".replace("{waluta_gpw}", "zł")

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        tekst = msg.content[0].text.strip()
        wyslij_telegram(f"🤖 <b>Rekomendacja AI — {datetime.now().strftime('%d.%m.%Y')}</b>\n\n{tekst}")
    except Exception as e:
        print(f"Blad rekomendacji AI: {e}")
