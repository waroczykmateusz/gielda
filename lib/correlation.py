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

    # Pobierz wszystkie symbole jednym requestem — dużo szybsze niż pętla
    try:
        raw = yf.download(
            symbole,
            period='1y',
            interval='1d',
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        return {'error': f'Błąd pobierania danych: {e}'}

    # yf.download zwraca MultiIndex gdy >1 symbol
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw['Close']
    else:
        close = raw[['Close']]
        close.columns = symbole[:1]

    # Usuń symbole z za małą ilością danych
    dostepne = [s for s in symbole if s in close.columns and close[s].notna().sum() >= 30]

    if len(dostepne) < 2:
        return {'error': 'Nie udało się pobrać danych dla wystarczającej liczby spółek'}

    returns = close[dostepne].pct_change().dropna(how='all')
    corr = returns.corr()

    macierz = []
    for s1 in dostepne:
        wiersz = []
        for s2 in dostepne:
            try:
                val = round(float(corr.loc[s1, s2]), 3)
            except Exception:
                val = None
            wiersz.append(val)
        macierz.append(wiersz)

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
