import os
from .prices import pobierz_dane_dzienne

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def analizuj_spolke(symbol):
    sygnaly = []
    rsi_d = 0
    rsi_w = 0
    macd_w = 0
    macd_signal_w = 0
    macd_hist_w = 0
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        h_d = t.history(period="1y", interval="1d")
        if len(h_d) >= 50:
            ceny_d = h_d["Close"]
            delta = ceny_d.diff()
            rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
            rsi_d = round(float((100 - (100 / (1 + rs))).iloc[-1]), 1)

        h_w = t.history(period="2y", interval="1wk")
        if len(h_w) >= 35:
            ceny_w = h_w["Close"]
            cena = float(ceny_w.iloc[-1])

            delta_w = ceny_w.diff()
            rs_w = delta_w.clip(lower=0).rolling(14).mean() / (-delta_w.clip(upper=0)).rolling(14).mean()
            rsi_w = round(float((100 - (100 / (1 + rs_w))).iloc[-1]), 1)

            if rsi_w < 30:
                sygnaly.append(("SILNY KUP", f"RSI tygodniowy={rsi_w} - mocno wyprzedana", "#26c281"))
            elif rsi_w < 40:
                sygnaly.append(("KUP", f"RSI tygodniowy={rsi_w} - wyprzedana", "#26c281"))
            elif rsi_w > 70:
                sygnaly.append(("UWAGA", f"RSI tygodniowy={rsi_w} - wykupiona", "#e74c3c"))

            ema12 = ceny_w.ewm(span=12, adjust=False).mean()
            ema26 = ceny_w.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal

            macd_w = round(float(macd.iloc[-1]), 3)
            macd_signal_w = round(float(macd_signal.iloc[-1]), 3)
            macd_hist_w = round(float(macd_hist.iloc[-1]), 3)

            if macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]:
                if macd.iloc[-1] < 0:
                    sygnaly.append(("KUP", "MACD tyg. przecial sygnal od dolu (strefa ujemna)", "#f39c12"))
                else:
                    sygnaly.append(("SILNY KUP", "MACD tyg. przecial sygnal od dolu (strefa dodatnia)", "#26c281"))
            elif macd.iloc[-1] < macd_signal.iloc[-1] and macd.iloc[-2] >= macd_signal.iloc[-2]:
                sygnaly.append(("UWAGA", "MACD tyg. spadl ponizej sygnalu", "#e74c3c"))

            if len(h_d) >= 200:
                ceny_d = h_d["Close"]
                sma20 = ceny_d.rolling(20).mean().iloc[-1]
                sma50 = ceny_d.rolling(50).mean()
                sma200 = ceny_d.rolling(200).mean()

                odch = round((cena - sma20) / sma20 * 100, 1)
                if odch < -5:
                    sygnaly.append(("KUP", f"{abs(odch)}% ponizej SMA20", "#f39c12"))

                if sma50.iloc[-1] > sma200.iloc[-1] and sma50.iloc[-5] <= sma200.iloc[-5]:
                    sygnaly.append(("SILNY KUP", "Zloty krzyz SMA50/SMA200", "#26c281"))

                sma20_s = ceny_d.rolling(20).mean()
                if sma20_s.iloc[-1] > sma50.iloc[-1] and sma20_s.iloc[-5] <= sma50.iloc[-5]:
                    sygnaly.append(("KUP", "Srebrny krzyz SMA20/SMA50", "#f39c12"))

            if len(ceny_w) >= 2:
                zmiana_tyg = round((ceny_w.iloc[-1] - ceny_w.iloc[-2]) / ceny_w.iloc[-2] * 100, 1)
                if zmiana_tyg < -8:
                    sygnaly.append(("KUP", f"Spadek {abs(zmiana_tyg)}% w tym tygodniu", "#f39c12"))

            if len(ceny_w) >= 4:
                zmiana_mies = round((ceny_w.iloc[-1] - ceny_w.iloc[-4]) / ceny_w.iloc[-4] * 100, 1)
                if zmiana_mies < -15:
                    sygnaly.append(("KUP", f"Spadek {abs(zmiana_mies)}% w miesiacu", "#f39c12"))

    except Exception as e:
        print(f"Blad analizy {symbol}: {e}")

    return sygnaly, rsi_d, rsi_w, macd_w, macd_signal_w, macd_hist_w


def wykryj_konflikt(sygnaly):
    typy_bycze = {"KUP", "SILNY KUP"}
    typy_niedzwiedzie = {"UWAGA", "SPRZEDAJ", "SILNA SPRZEDAZ"}
    rsi_bycze = any(typ in typy_bycze and "RSI" in opis for typ, opis, _ in sygnaly)
    rsi_niedzwiedzie = any(typ in typy_niedzwiedzie and "RSI" in opis for typ, opis, _ in sygnaly)
    macd_bycze = any(typ in typy_bycze and "MACD" in opis for typ, opis, _ in sygnaly)
    macd_niedzwiedzie = any(typ in typy_niedzwiedzie and "MACD" in opis for typ, opis, _ in sygnaly)
    rsi_vs_macd = (rsi_bycze and macd_niedzwiedzie) or (rsi_niedzwiedzie and macd_bycze)
    ogolny = any(typ in typy_bycze for typ, _, _ in sygnaly) and any(typ in typy_niedzwiedzie for typ, _, _ in sygnaly)
    return rsi_vs_macd or ogolny


def _grupuj_sygnaly(sygnaly):
    grupy = {"RSI": [], "MACD": [], "SMA": [], "inne": []}
    for typ, opis, _ in sygnaly:
        if "RSI" in opis:
            grupy["RSI"].append(f"{typ}: {opis}")
        elif "MACD" in opis:
            grupy["MACD"].append(f"{typ}: {opis}")
        elif any(k in opis for k in ("SMA", "krzyz", "Zloty", "Srebrny")):
            grupy["SMA"].append(f"{typ}: {opis}")
        else:
            grupy["inne"].append(f"{typ}: {opis}")
    return {k: v for k, v in grupy.items() if v}


def analizuj_konflikt_sygnalu(nazwa, symbol, sygnaly, srednia_cena):
    try:
        import anthropic
        cena, _ = pobierz_dane_dzienne(symbol)
        zysk_proc = round((cena - srednia_cena) / srednia_cena * 100, 1) if cena else None
        grupy = _grupuj_sygnaly(sygnaly)
        opis_sygnalow = "\n".join(
            f"[{wskaznik}]\n" + "\n".join(f"  - {s}" for s in lista)
            for wskaznik, lista in grupy.items()
        )

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": f"""Jestes analitykiem technicznym. Spolka {nazwa} ({symbol}) ma sprzeczne sygnaly tygodniowe pogrupowane wedlug wskaznika:

{opis_sygnalow}

Inwestor kupil po {srednia_cena}, teraz cena {cena} ({'+' if zysk_proc and zysk_proc >= 0 else ''}{zysk_proc}%).

Rozstrzygnij w max 2 zdaniach: ktory wskaznik (RSI/MACD/SMA) jest w tej sytuacji wiarygodniejszy i co robic (trzymaj/dokup/sprzedaj czesc). Konkretnie, bez wstepu."""}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Blad AI: {e}"
