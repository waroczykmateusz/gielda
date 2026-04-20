def _ticker(symbol):
    import yfinance as yf
    from requests import Session
    return yf.Ticker(symbol, session=Session())


def pobierz_cene(symbol):
    try:
        h = _ticker(symbol).history(period="1d", interval="1m")
        if h.empty:
            return None
        return round(float(h["Close"].iloc[-1]), 2)
    except Exception:
        return None


def pobierz_dane_dzienne(symbol):
    try:
        t = _ticker(symbol)
        h_intra = t.history(period="1d", interval="1m")
        h_daily = t.history(period="5d", interval="1d")
        if h_intra.empty and h_daily.empty:
            return None, None
        cena = round(float(h_intra["Close"].iloc[-1]), 2) if not h_intra.empty else round(float(h_daily["Close"].iloc[-1]), 2)
        if len(h_daily) >= 2:
            poprzednia = round(float(h_daily["Close"].iloc[-2]), 2)
            zmiana = round((cena - poprzednia) / poprzednia * 100, 2) if poprzednia else None
        else:
            zmiana = None
        return cena, zmiana
    except Exception:
        return None, None
