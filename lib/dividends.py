import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import yfinance as yf

from .storage import get_portfolio


def _fmt_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%d.%m.%Y')
    except Exception:
        return None


def _dywidenda_z_historii(ticker):
    try:
        rok_temu = datetime.now() - timedelta(days=365)
        divs = ticker.dividends
        if divs.empty:
            return None
        divs.index = divs.index.tz_localize(None) if divs.index.tz else divs.index
        ostatni_rok = divs[divs.index >= rok_temu]
        if ostatni_rok.empty:
            return None
        return round(float(ostatni_rok.sum()), 4)
    except Exception:
        return None


def pobierz_dywidendy_portfela():
    gpw = get_portfolio('gpw')
    usa = get_portfolio('usa')

    wyniki = []

    for market, portfel in [('gpw', gpw), ('usa', usa)]:
        for symbol, info in portfel.items():
            try:
                t = yf.Ticker(symbol)
                inf = t.info or {}

                dywidenda_na_akcje = inf.get('dividendRate') or None
                if dywidenda_na_akcje is None:
                    dywidenda_na_akcje = _dywidenda_z_historii(t)

                yield_proc = inf.get('dividendYield')
                if yield_proc:
                    yield_proc = round(yield_proc * 100, 2)

                ex_date = _fmt_date(inf.get('exDividendDate'))
                pay_date = _fmt_date(inf.get('payDate'))

                akcje = info['akcje']
                wyplata = round(dywidenda_na_akcje * akcje, 2) if dywidenda_na_akcje else None

                wyniki.append({
                    'symbol': symbol,
                    'nazwa': info['nazwa'],
                    'market': market,
                    'akcje': akcje,
                    'dywidenda_na_akcje': round(dywidenda_na_akcje, 4) if dywidenda_na_akcje else None,
                    'wyplata_laczna': wyplata,
                    'yield_proc': yield_proc,
                    'ex_date': ex_date,
                    'pay_date': pay_date,
                })
            except Exception as e:
                wyniki.append({
                    'symbol': symbol,
                    'nazwa': info['nazwa'],
                    'market': market,
                    'akcje': info['akcje'],
                    'dywidenda_na_akcje': None,
                    'wyplata_laczna': None,
                    'yield_proc': None,
                    'ex_date': None,
                    'pay_date': None,
                })

    lacznie_gpw = sum(
        w['wyplata_laczna'] for w in wyniki
        if w['market'] == 'gpw' and w['wyplata_laczna'] is not None
    )
    lacznie_usa = sum(
        w['wyplata_laczna'] for w in wyniki
        if w['market'] == 'usa' and w['wyplata_laczna'] is not None
    )

    return {
        'spolki': wyniki,
        'lacznie_gpw': round(lacznie_gpw, 2),
        'lacznie_usa': round(lacznie_usa, 2),
    }
