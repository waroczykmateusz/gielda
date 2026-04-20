from datetime import datetime

from .analysis import analizuj_spolke, wykryj_konflikt, analizuj_konflikt_sygnalu
from .notify import wyslij_telegram_dlugi
from .storage import get_portfolio


def sprawdz_sygnaly(market=None):
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    if market:
        wszystkie = get_portfolio(market)
    else:
        wszystkie = {**get_portfolio("gpw"), **get_portfolio("usa")}

    wszystkie_sygnaly = []
    for symbol, info in wszystkie.items():
        sygnaly, _, _, _, _, _ = analizuj_spolke(symbol)
        if sygnaly:
            wszystkie_sygnaly.append((info["nazwa"], symbol, sygnaly, info["srednia_cena"]))

    if not wszystkie_sygnaly:
        return

    label = {"gpw": "GPW", "usa": "USA"}.get(market, "Portfel")
    linie = [f"📊 <b>Sygnaly {label} — {teraz.strftime('%d.%m.%Y %H:%M')}</b>\n"]
    for nazwa, symbol, sygnaly, srednia in wszystkie_sygnaly:
        linie.append(f"🔔 <b>{nazwa}</b>")
        for typ, opis, _ in sygnaly:
            emoji = "🟢" if "SILNY" in typ else "🟡" if "KUP" in typ else "🔴"
            linie.append(f"  {emoji} {typ} — {opis}")
        if wykryj_konflikt(sygnaly):
            analiza = analizuj_konflikt_sygnalu(nazwa, symbol, sygnaly, srednia)
            linie.append(f"  🤖 <i>{analiza}</i>")
        linie.append("")

    wyslij_telegram_dlugi("\n".join(linie))
