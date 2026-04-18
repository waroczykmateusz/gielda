import yfinance as yf
import pandas as pd


def dane_wykresu(symbol, period='6mo'):
    t = yf.Ticker(symbol)
    h = t.history(period=period, interval='1d')
    if h.empty or len(h) < 20:
        return None

    ceny = h['Close']

    sma20 = ceny.rolling(20).mean()
    sma50 = ceny.rolling(50).mean()
    sma200 = ceny.rolling(200).mean()

    delta = ceny.diff()
    rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + rs))

    ema12 = ceny.ewm(span=12, adjust=False).mean()
    ema26 = ceny.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_signal

    def _v(s, i):
        try:
            v = s.iloc[i]
            if pd.isna(v):
                return None
            return round(float(v), 3)
        except Exception:
            return None

    punkty = []
    for i, idx in enumerate(h.index):
        punkty.append({
            'date': idx.strftime('%Y-%m-%d'),
            'close': _v(ceny, i),
            'sma20': _v(sma20, i),
            'sma50': _v(sma50, i),
            'sma200': _v(sma200, i),
            'rsi': _v(rsi, i),
            'macd': _v(macd, i),
            'macd_signal': _v(macd_signal, i),
            'macd_hist': _v(macd_hist, i),
        })

    markery = []
    for i in range(1, len(h)):
        d = punkty[i]['date']
        cena = punkty[i]['close']
        rsi_val = punkty[i]['rsi']
        rsi_prev = punkty[i-1]['rsi']
        macd_val = punkty[i]['macd']
        macd_prev = punkty[i-1]['macd']
        sig_val = punkty[i]['macd_signal']
        sig_prev = punkty[i-1]['macd_signal']
        s50 = punkty[i]['sma50']
        s200 = punkty[i]['sma200']
        s50_prev = punkty[i-1]['sma50']
        s200_prev = punkty[i-1]['sma200']

        if rsi_val is not None and rsi_prev is not None:
            if rsi_prev >= 30 and rsi_val < 30:
                markery.append({'date': d, 'price': cena, 'typ': 'KUP', 'opis': f'RSI wyprzedana ({rsi_val})', 'kolor': '#26c281'})
            elif rsi_prev <= 70 and rsi_val > 70:
                markery.append({'date': d, 'price': cena, 'typ': 'UWAGA', 'opis': f'RSI wykupiona ({rsi_val})', 'kolor': '#e74c3c'})

        if macd_val is not None and macd_prev is not None and sig_val is not None and sig_prev is not None:
            if macd_prev <= sig_prev and macd_val > sig_val:
                markery.append({'date': d, 'price': cena, 'typ': 'KUP', 'opis': 'MACD przeciął sygnał od dołu', 'kolor': '#26c281'})
            elif macd_prev >= sig_prev and macd_val < sig_val:
                markery.append({'date': d, 'price': cena, 'typ': 'UWAGA', 'opis': 'MACD przeciął sygnał od góry', 'kolor': '#e74c3c'})

        if s50 is not None and s200 is not None and s50_prev is not None and s200_prev is not None:
            if s50_prev <= s200_prev and s50 > s200:
                markery.append({'date': d, 'price': cena, 'typ': 'SILNY KUP', 'opis': 'Złoty krzyż SMA50/SMA200', 'kolor': '#26c281'})
            elif s50_prev >= s200_prev and s50 < s200:
                markery.append({'date': d, 'price': cena, 'typ': 'UWAGA', 'opis': 'Krzyż śmierci SMA50/SMA200', 'kolor': '#e74c3c'})

    return {
        'symbol': symbol,
        'punkty': punkty,
        'markery': markery,
    }
