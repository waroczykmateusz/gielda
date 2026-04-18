def pobierz_cene(symbol):
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h = t.history(period="1d", interval="1m")
        if h.empty:
            return None
        return round(float(h["Close"].iloc[-1]), 2)
    except Exception:
        return None


def pobierz_dane_dzienne(symbol):
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h = t.history(period="5d", interval="1d")
        if len(h) < 2:
            return None, None
        cena = round(float(h["Close"].iloc[-1]), 2)
        poprzednia = round(float(h["Close"].iloc[-2]), 2)
        zmiana = round((cena - poprzednia) / poprzednia * 100, 2)
        return cena, zmiana
    except Exception:
        return None, None
