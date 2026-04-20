def _fresh_ticker(symbol):
    import yfinance as yf
    from requests import Session
    return yf.Ticker(symbol, session=Session())


def pobierz_cene(symbol):
    try:
        h = _fresh_ticker(symbol).history(period="1d", interval="1m")
        if h.empty:
            return None
        return round(float(h["Close"].iloc[-1]), 2)
    except Exception:
        return None


def pobierz_dane_dzienne(symbol):
    try:
        fi = _fresh_ticker(symbol).fast_info
        cena = round(float(fi.last_price), 2)
        poprzednia = round(float(fi.previous_close), 2)
        zmiana = round((cena - poprzednia) / poprzednia * 100, 2) if poprzednia else None
        return cena, zmiana
    except Exception:
        return None, None
