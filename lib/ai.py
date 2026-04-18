import os
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from .notify import wyslij_telegram
from .prices import pobierz_dane_dzienne
from .storage import get_portfolio

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def pobierz_newsy(nazwa, symbol):
    try:
        nazwa_szukana = nazwa.replace(" SA", "").replace(" S.A.", "").strip()
        url = f"https://news.google.com/rss/search?q={nazwa_szukana}+akcje&hl=pl&gl=PL&ceid=PL:pl"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
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
        import anthropic
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
        return

    gpw = get_portfolio("gpw")
    usa = get_portfolio("usa")
    wszystkie = {**gpw, **usa}

    wyslij_telegram(
        f"🤖 <b>Poranna analiza AI — {datetime.now().strftime('%d.%m.%Y')}</b>\n"
        f"Analizuje {len(wszystkie)} spolek..."
    )

    for symbol, info in wszystkie.items():
        nazwa = info["nazwa"]
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
        time.sleep(1)

    wyslij_telegram("✅ <b>Analiza AI zakonczona.</b>")
