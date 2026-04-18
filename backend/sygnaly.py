import schedule
import time
import json
import os
from datetime import datetime
from core import wczytaj_portfel, analizuj_spolke, wyslij_telegram, get_base_dir, wykryj_konflikt, analizuj_konflikt_sygnalu

PLIK_USA = os.path.join(get_base_dir(), "portfel_usa.json")

def wczytaj_portfel_usa():
    if os.path.exists(PLIK_USA):
        with open(PLIK_USA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def sprawdz_sygnaly():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    print(f"\n[{teraz.strftime('%H:%M')}] Analizuje sygnaly...")
    wszystkie = {**wczytaj_portfel(), **wczytaj_portfel_usa()}
    wszystkie_sygnaly = []

    for symbol, info in wszystkie.items():
        sygnaly, _, rsi_w, _, _, _ = analizuj_spolke(symbol)
        if sygnaly:
            print(f"  {info['nazwa']}: {len(sygnaly)} sygnalow (RSI_W={rsi_w})")
            wszystkie_sygnaly.append((info["nazwa"], symbol, sygnaly, info["srednia_cena"]))
        else:
            print(f"  {info['nazwa']}: brak sygnalow (RSI_W={rsi_w})")

    if wszystkie_sygnaly:
        linie = [f"📊 <b>Sygnaly {teraz.strftime('%d.%m.%Y %H:%M')}</b>\n"]
        for nazwa, symbol, sygnaly, srednia in wszystkie_sygnaly:
            linie.append(f"🔔 <b>{nazwa}</b> ({symbol})")
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

sprawdz_sygnaly()
schedule.every().day.at("09:30").do(sprawdz_sygnaly)
schedule.every().day.at("13:00").do(sprawdz_sygnaly)

print(f"\nSkrypt sygnalow dziala. Ctrl+C zeby zatrzymac.\n")
while True:
    schedule.run_pending()
    time.sleep(60)
