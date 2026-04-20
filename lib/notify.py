import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

_LIMIT = 4000


def wyslij_telegram(wiadomosc):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram secrets missing — skipping send")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    dane = {"chat_id": TELEGRAM_CHAT_ID, "text": wiadomosc, "parse_mode": "HTML"}
    try:
        requests.post(url, data=dane, timeout=10)
    except Exception as e:
        print(f"Blad Telegram: {e}")


def wyslij_telegram_dlugi(wiadomosc):
    if len(wiadomosc) <= _LIMIT:
        wyslij_telegram(wiadomosc)
        return
    czesc = ""
    for linia in wiadomosc.split("\n"):
        if len(czesc) + len(linia) + 1 > _LIMIT:
            if czesc:
                wyslij_telegram(czesc.strip())
                time.sleep(0.5)
            czesc = linia
        else:
            czesc += ("\n" if czesc else "") + linia
    if czesc:
        wyslij_telegram(czesc.strip())
