from datetime import datetime

from .alerts_state import was_sent, mark_sent, cleanup_expired
from .notify import wyslij_telegram
from .prices import pobierz_cene
from .storage import get_portfolio


def _waluta(market):
    return "zl" if market == "gpw" else "$"


def _sprawdz_alerty_dla(spolki, market):
    teraz = datetime.now().strftime("%H:%M")
    waluta = _waluta(market)
    rynek_label = "GPW" if market == "gpw" else "USA"

    for symbol, info in spolki.items():
        alert_powyzej = info.get("alert_powyzej")
        alert_ponizej = info.get("alert_ponizej")
        if not alert_powyzej and not alert_ponizej:
            continue
        cena = pobierz_cene(symbol)
        if cena is None:
            continue

        if alert_powyzej and cena >= alert_powyzej:
            klucz = f"{market}:{symbol}_powyzej"
            if not was_sent(klucz):
                wyslij_telegram(
                    f"🚀 <b>{info['nazwa']}</b> [{rynek_label}]\n"
                    f"Cena wzrosla do <b>{cena} {waluta}</b>\n"
                    f"(prog: {alert_powyzej} {waluta})\n"
                    f"⏰ {teraz}"
                )
                mark_sent(klucz, cena)

        if alert_ponizej and cena <= alert_ponizej:
            klucz = f"{market}:{symbol}_ponizej"
            if not was_sent(klucz):
                wyslij_telegram(
                    f"📉 <b>{info['nazwa']}</b> [{rynek_label}]\n"
                    f"Cena spadla do <b>{cena} {waluta}</b>\n"
                    f"(prog: {alert_ponizej} {waluta})\n"
                    f"⏰ {teraz}"
                )
                mark_sent(klucz, cena)


def sprawdz_alerty(market=None):
    cleanup_expired()
    if market in (None, "gpw"):
        _sprawdz_alerty_dla(get_portfolio("gpw"), "gpw")
    if market in (None, "usa"):
        _sprawdz_alerty_dla(get_portfolio("usa"), "usa")
