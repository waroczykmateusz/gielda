import yfinance as yf
import pandas as pd
from .storage import get_portfolio


def korelacja_portfela():
    gpw = get_portfolio('gpw')
    usa = get_portfolio('usa')
    wszystkie = {**gpw, **usa}

    symbole = list(wszystkie.keys())
    nazwy = {s: wszystkie[s]['nazwa'] for s in symbole}
    markety = {s: 'gpw' if s in gpw else 'usa' for s in symbole}

    if len(symbole) < 2:
        return {'error': 'Za mało spółek do analizy korelacji (minimum 2)'}

    returns = {}
    for symbol in symbole:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period='1y', interval='1d')
            if h.empty or len(h) < 30:
                continue
            r = h['Close'].pct_change().dropna()
            returns[symbol] = r
        except Exception:
            continue

    dostepne = list(returns.keys())
    if len(dostepne) < 2:
        return {'error': 'Nie udało się pobrać danych dla wystarczającej liczby spółek'}

    df = pd.DataFrame(returns).dropna()
    corr = df.corr()

    macierz = []
    for s1 in dostepne:
        wiersz = []
        for s2 in dostepne:
            val = round(float(corr.loc[s1, s2]), 3) if s1 in corr.index and s2 in corr.columns else None
            wiersz.append(val)
        macierz.append(wiersz)

    # grupy ryzyka: pary z korelacją > 0.7
    wysokie_pary = []
    for i, s1 in enumerate(dostepne):
        for j, s2 in enumerate(dostepne):
            if j <= i:
                continue
            val = macierz[i][j]
            if val is not None and val >= 0.7:
                wysokie_pary.append({
                    'symbol1': s1, 'nazwa1': nazwy.get(s1, s1),
                    'symbol2': s2, 'nazwa2': nazwy.get(s2, s2),
                    'korelacja': val,
                })

    wysokie_pary.sort(key=lambda x: x['korelacja'], reverse=True)

    return {
        'symbole': dostepne,
        'nazwy': {s: nazwy.get(s, s) for s in dostepne},
        'markety': {s: markety.get(s, '') for s in dostepne},
        'macierz': macierz,
        'wysokie_pary': wysokie_pary,
    }
