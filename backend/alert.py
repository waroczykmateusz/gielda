import sys
import os
import json
import schedule
import time
from datetime import datetime
from config import CZESTOTLIWOSC_MINUT
from core import (
    wczytaj_portfel, wyslij_telegram, pobierz_cene,
    analizuj_spolke, czy_gielda_otwarta, get_base_dir,
    wykryj_konflikt, analizuj_konflikt_sygnalu
)
from analiza_ai import dzienna_analiza

PLIK_USA = os.path.join(get_base_dir(), "portfel_usa.json")

def wczytaj_portfel_usa():
    if os.path.exists(PLIK_USA):
        with open(PLIK_USA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

wyslane_alerty = {}

def sprawdz_alerty_dla(spolki, rynek):
    teraz = datetime.now().strftime("%H:%M")
    for symbol, info in spolki.items():
        alert_powyzej = info.get("alert_powyzej")
        alert_ponizej = info.get("alert_ponizej")
        if not alert_powyzej and not alert_ponizej:
            continue
        cena = pobierz_cene(symbol)
        if cena is None:
            continue
        print(f"  [{rynek}] {info['nazwa']}: {cena}")
        waluta = "zl" if rynek == "GPW" else "$"

        if alert_powyzej and cena >= alert_powyzej:
            klucz = f"{symbol}_powyzej"
            if klucz not in wyslane_alerty:
                wyslij_telegram(
                    f"🚀 <b>{info['nazwa']}</b> [{rynek}]\n"
                    f"Cena wzrosla do <b>{cena} {waluta}</b>\n"
                    f"(prog: {alert_powyzej} {waluta})\n"
                    f"⏰ {teraz}"
                )
                wyslane_alerty[klucz] = cena
        else:
            wyslane_alerty.pop(f"{symbol}_powyzej", None)

        if alert_ponizej and cena <= alert_ponizej:
            klucz = f"{symbol}_ponizej"
            if klucz not in wyslane_alerty:
                wyslij_telegram(
                    f"📉 <b>{info['nazwa']}</b> [{rynek}]\n"
                    f"Cena spadla do <b>{cena} {waluta}</b>\n"
                    f"(prog: {alert_ponizej} {waluta})\n"
                    f"⏰ {teraz}"
                )
                wyslane_alerty[klucz] = cena
        else:
            wyslane_alerty.pop(f"{symbol}_ponizej", None)

def sprawdz_alerty():
    teraz = datetime.now()
    godzina = teraz.hour
    dzien = teraz.weekday()
    if dzien >= 5:
        print(f"[{teraz.strftime('%H:%M')}] Weekend - pomijam.")
        return

    print(f"\n[{teraz.strftime('%H:%M')}] Sprawdzam alerty...")

    # GPW: 9:00-17:05
    if 9 <= godzina < 17:
        sprawdz_alerty_dla(wczytaj_portfel(), "GPW")

    # USA: 15:30-22:00
    if godzina >= 15 and not (godzina == 15 and teraz.minute < 30):
        if godzina < 22:
            sprawdz_alerty_dla(wczytaj_portfel_usa(), "USA")

def sprawdz_sygnaly():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    print(f"\n[{teraz.strftime('%H:%M')}] Sprawdzam sygnaly...")
    wszystkie_sygnaly = []

    wszystkie = {**wczytaj_portfel(), **wczytaj_portfel_usa()}
    for symbol, info in wszystkie.items():
        sygnaly, _, _, _, _, _ = analizuj_spolke(symbol)
        if sygnaly:
            wszystkie_sygnaly.append((info["nazwa"], symbol, sygnaly, info["srednia_cena"]))

    if wszystkie_sygnaly:
        linie = [f"📊 <b>Sygnaly {teraz.strftime('%d.%m.%Y %H:%M')}</b>\n"]
        for nazwa, symbol, sygnaly, srednia in wszystkie_sygnaly:
            linie.append(f"🔔 <b>{nazwa}</b>")
            for typ, opis, _ in sygnaly:
                emoji = "🟢" if "SILNY" in typ else "🟡" if "KUP" in typ else "🔴"
                linie.append(f"  {emoji} {typ} — {opis}")
            if wykryj_konflikt(sygnaly):
                print(f"  Konflikt sygnalow dla {nazwa} — pytam AI...")
                analiza = analizuj_konflikt_sygnalu(nazwa, symbol, sygnaly, srednia)
                linie.append(f"  🤖 <i>{analiza}</i>")
            linie.append("")
        wyslij_telegram("\n".join(linie))
    else:
        print("  Brak sygnalow.")

def dzienny_raport():
    if datetime.now().weekday() >= 5:
        return

    def sekcja(portfel, waluta):
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
            linie.append(f"{emoji} <b>{info['nazwa']}</b>: {cena} {waluta} ({zysk:+.2f} {waluta} / {proc:+.1f}%)")
            suma_w += w
            suma_z += z
        suma_zysk = round(suma_w - suma_z, 2)
        suma_zwrot = round((suma_zysk / suma_z) * 100, 2) if suma_z else 0
        emoji_t = "🟢" if suma_zysk >= 0 else "🔴"
        linie.append(f"\n{emoji_t} <b>Lacznie:</b> {round(suma_w, 2)} {waluta} ({suma_zysk:+.2f} {waluta} / {suma_zwrot:+.1f}%)")
        return linie

    teraz = datetime.now()
    linie = [f"📊 <b>Podsumowanie {teraz.strftime('%d.%m.%Y')}</b>\n"]
    linie.append("🇵🇱 <b>GPW</b>")
    linie.extend(sekcja(wczytaj_portfel(), "zl"))
    linie.append("\n🇺🇸 <b>USA</b>")
    linie.extend(sekcja(wczytaj_portfel_usa(), "$"))
    wyslij_telegram("\n".join(linie))

if __name__ == "__main__":
    gpw = wczytaj_portfel()
    usa = wczytaj_portfel_usa()
    gpw_alerty = [f"• {v['nazwa']}" for v in gpw.values() if v.get("alert_powyzej") or v.get("alert_ponizej")]
    usa_alerty = [f"• {v['nazwa']}" for v in usa.values() if v.get("alert_powyzej") or v.get("alert_ponizej")]
    wyslij_telegram(
        "✅ <b>Monitor gieldowy uruchomiony!</b>\n"
        f"GPW: {len(gpw)} spolek | USA: {len(usa)} spolek\n"
        + ("GPW alerty:\n" + "\n".join(gpw_alerty) if gpw_alerty else "") +
        ("\nUSA alerty:\n" + "\n".join(usa_alerty) if usa_alerty else "")
    )

    sprawdz_alerty()
    schedule.every(CZESTOTLIWOSC_MINUT).minutes.do(sprawdz_alerty)
    schedule.every().day.at("08:00").do(dzienna_analiza)
    schedule.every().day.at("10:00").do(sprawdz_sygnaly)
    schedule.every().day.at("14:00").do(sprawdz_sygnaly)
    schedule.every().day.at("17:06").do(dzienny_raport)

    print(f"\nMonitor dziala. Sprawdzam co {CZESTOTLIWOSC_MINUT} minut.\n")
    while True:
        schedule.run_pending()
        time.sleep(30)