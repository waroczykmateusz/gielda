from datetime import datetime

from .notify import wyslij_telegram
from .prices import pobierz_cene
from .storage import get_portfolio


def _sekcja(portfel, waluta):
    linie = []
    suma_w = suma_z = 0
    for symbol, info in portfel.items():
        cena = pobierz_cene(symbol)
        if cena is None:
            continue
        w = round(cena * info["akcje"], 2)
        z = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(w - z, 2)
        proc = round((zysk / z) * 100, 2) if z else 0
        emoji = "🟢" if zysk >= 0 else "🔴"
        linie.append(
            f"{emoji} <b>{info['nazwa']}</b>: {cena} {waluta} "
            f"({zysk:+.2f} {waluta} / {proc:+.1f}%)"
        )
        suma_w += w
        suma_z += z
    suma_zysk = round(suma_w - suma_z, 2)
    suma_zwrot = round((suma_zysk / suma_z) * 100, 2) if suma_z else 0
    emoji_t = "🟢" if suma_zysk >= 0 else "🔴"
    linie.append(
        f"\n{emoji_t} <b>Lacznie:</b> {round(suma_w, 2)} {waluta} "
        f"({suma_zysk:+.2f} {waluta} / {suma_zwrot:+.1f}%)"
    )
    return linie


def dzienny_raport():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    linie = [f"📊 <b>Podsumowanie {teraz.strftime('%d.%m.%Y')}</b>\n"]
    linie.append("🇵🇱 <b>GPW</b>")
    linie.extend(_sekcja(get_portfolio("gpw"), "zl"))
    linie.append("\n🇺🇸 <b>USA</b>")
    linie.extend(_sekcja(get_portfolio("usa"), "$"))
    wyslij_telegram("\n".join(linie))
