import os
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from .notify import wyslij_telegram
from .storage import get_portfolio


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


def dzienna_analiza():
    if datetime.now().weekday() >= 5:
        return

    gpw = get_portfolio("gpw")
    usa = get_portfolio("usa")
    wszystkie = {**gpw, **usa}

    wyslij_telegram(
        f"📰 <b>Poranne newsy — {datetime.now().strftime('%d.%m.%Y')}</b>\n"
        f"Pobieram newsy dla {len(wszystkie)} spolek..."
    )

    for symbol, info in wszystkie.items():
        nazwa = info["nazwa"]
        newsy = pobierz_newsy(nazwa, symbol)
        wiadomosc = f"📰 <b>{nazwa}</b> ({symbol})\n{newsy}"
        wyslij_telegram(wiadomosc)
        time.sleep(1)

    wyslij_telegram("✅ <b>Newsy pobrane.</b>")
