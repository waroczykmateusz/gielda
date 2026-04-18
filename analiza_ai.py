import anthropic
import requests
import schedule
import time
import json
import os
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ANTHROPIC_API_KEY
from core import wczytaj_portfel, get_base_dir

# Szukaj portfel_usa.json w kilku miejscach
for _sciezka in [
    os.path.join(get_base_dir(), "portfel_usa.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "portfel_usa.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfel_usa.json"),
]:
    if os.path.exists(_sciezka):
        PLIK_USA = _sciezka
        break
else:
    PLIK_USA = os.path.join(get_base_dir(), "portfel_usa.json")
def wczytaj_portfel_usa():
    if os.path.exists(PLIK_USA):
        with open(PLIK_USA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def wyslij_telegram(wiadomosc):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    dane = {"chat_id": TELEGRAM_CHAT_ID, "text": wiadomosc, "parse_mode": "HTML"}
    try:
        requests.post(url, data=dane, timeout=10)
    except Exception as e:
        print(f"Blad Telegram: {e}")

def pobierz_newsy(nazwa, symbol):
    try:
        # Usun sufiks gieldowy dla wyszukiwania
        nazwa_szukana = nazwa.replace(" SA", "").replace(" S.A.", "").strip()
        url = f"https://news.google.com/rss/search?q={nazwa_szukana}+akcje&hl=pl&gl=PL&ceid=PL:pl"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        # Parsuj RSS
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:3]

        if not items:
            return "Brak najnowszych newsow."

        teksty = []
        for item in items:
            title = item.find("title")
            if title is not None:
                teksty.append(f"- {title.text}")
        return "\n".join(teksty) if teksty else "Brak newsow."
    except Exception as e:
        return f"Nie udalo sie pobrac newsow: {e}"

def analizuj_ai(nazwa, symbol, srednia_cena, akcje, newsy):
    try:
        from core import pobierz_dane_dzienne
        cena_aktualna, zmiana_dzis = pobierz_dane_dzienne(symbol)
        if cena_aktualna is None:
            cena_aktualna = "nieznana"
            zmiana_dzis = 0

        zysk = None
        zysk_proc = None
        if isinstance(cena_aktualna, float):
            zysk = round((cena_aktualna - srednia_cena) * akcje, 2)
            zysk_proc = round((cena_aktualna - srednia_cena) / srednia_cena * 100, 2)

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""Jestes doswiadczonym analitykiem gieldowym. Przeanalizuj krotko spolke {nazwa} (symbol: {symbol}).

Dane inwestora:
- Liczba akcji: {akcje}
- Srednia cena zakupu: {srednia_cena} 
- Aktualna cena rynkowa: {cena_aktualna}
- Zmiana dzisiaj: {zmiana_dzis}%
- Aktualny zysk/strata: {zysk} ({zysk_proc}%)

Najnowsze newsy o spolce:
{newsy}

Napisz krotka analize (max 3 zdania) zawierajaca:
1. Ogolna ocena sytuacji spolki na podstawie newsow i aktualnej ceny
2. Krotkoterminowa rekomendacja (trzymaj/dokup/sprzedaj) BIORAC POD UWAGE ze inwestor jest na {zysk_proc}% zysku/stracie
3. Jeden kluczowy czynnik ryzyka lub szansa

Odpowiedz po polsku, zwiezle i konkretnie."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Blad analizy AI: {e}"

def dzienna_analiza():
    if datetime.now().weekday() >= 5:
        print("Weekend - pomijam analize AI.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M')}] Uruchamiam analize AI...")

    gpw = wczytaj_portfel()
    usa = wczytaj_portfel_usa()
    wszystkie = {**gpw, **usa}

    wyslij_telegram(f"🤖 <b>Poranna analiza AI — {datetime.now().strftime('%d.%m.%Y')}</b>\nAnalizuje {len(wszystkie)} spolek...")

    for symbol, info in wszystkie.items():
        nazwa = info["nazwa"]
        print(f"  Analizuje: {nazwa}...")

        newsy = pobierz_newsy(nazwa, symbol)
        analiza = analizuj_ai(nazwa, symbol, info["srednia_cena"], info["akcje"], newsy)

        wiadomosc = (
            f"📈 <b>{nazwa}</b> ({symbol})\n\n"
            f"<i>Newsy:</i>\n{newsy}\n\n"
            f"<b>Analiza AI:</b>\n{analiza}"
        )
        if len(wiadomosc) <= 4000:
            wyslij_telegram(wiadomosc)
        else:
            wyslij_telegram(f"📈 <b>{nazwa}</b> ({symbol})\n\n<i>Newsy:</i>\n{newsy}")
            time.sleep(1)
            wyslij_telegram(f"<b>Analiza AI — {nazwa}:</b>\n{analiza}")
        time.sleep(2)

    wyslij_telegram("✅ <b>Analiza AI zakonczona.</b>")
    print("  Analiza zakonczona.")

if __name__ == "__main__":
    dzienna_analiza()
    schedule.every().day.at("08:00").do(dzienna_analiza)
    print("\nSkrypt analizy AI dziala. Ctrl+C zeby zatrzymac.\n")
    while True:
        schedule.run_pending()
        time.sleep(60)