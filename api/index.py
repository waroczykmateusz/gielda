import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from flask_cors import CORS

from lib.analysis import analizuj_spolke
from lib.prices import pobierz_dane_dzienne
from lib.sanitize import sanitize
from lib.storage import (
    apply_transaction, get_portfolio, set_alerts,
)

app = Flask(__name__)
CORS(app)


def _przelicz_portfel(portfel):
    spolki = []
    suma_wartosc = suma_zainwestowano = suma_zysk_dzis = 0
    for symbol, info in portfel.items():
        cena, zmiana = pobierz_dane_dzienne(symbol)
        if cena is None:
            cena, zmiana = 0.0, 0.0
        wartosc = round(cena * info["akcje"], 2)
        zainwestowano = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(wartosc - zainwestowano, 2)
        zysk_proc = round((zysk / zainwestowano) * 100, 2) if zainwestowano else 0
        cena_wczoraj = cena / (1 + zmiana / 100) if zmiana != -100 else 0
        zysk_dzis = round((cena - cena_wczoraj) * info["akcje"], 2)
        suma_wartosc += wartosc
        suma_zainwestowano += zainwestowano
        suma_zysk_dzis += zysk_dzis
        sygnaly, rsi_d, rsi_w, macd_w, macd_signal_w, macd_hist_w = analizuj_spolke(symbol)
        spolki.append({
            "symbol": symbol,
            "nazwa": info["nazwa"],
            "cena": cena,
            "zmiana_proc": zmiana,
            "akcje": info["akcje"],
            "srednia": info["srednia_cena"],
            "wartosc": wartosc,
            "zysk": zysk,
            "zysk_proc": zysk_proc,
            "zysk_dzis": zysk_dzis,
            "alert_up": info.get("alert_powyzej"),
            "alert_down": info.get("alert_ponizej"),
            "sygnaly": [{"typ": t, "opis": o, "kolor": k} for t, o, k in sygnaly],
            "rsi_d": rsi_d,
            "rsi_w": rsi_w,
            "macd_w": macd_w,
            "macd_signal_w": macd_signal_w,
            "macd_hist_w": macd_hist_w,
        })
    suma_zysk = round(suma_wartosc - suma_zainwestowano, 2)
    suma_zwrot = round((suma_zysk / suma_zainwestowano) * 100, 2) if suma_zainwestowano else 0
    return spolki, {
        "wartosc": round(suma_wartosc, 2),
        "zainwestowano": round(suma_zainwestowano, 2),
        "zysk": suma_zysk,
        "zwrot": suma_zwrot,
        "zysk_dzis": round(suma_zysk_dzis, 2),
    }


@app.route("/api/portfolio/<tab>")
def portfolio(tab):
    if tab not in ("gpw", "usa"):
        return jsonify({"error": "invalid tab"}), 400
    portfel = get_portfolio(tab)
    spolki, podsumowanie = _przelicz_portfel(portfel)
    return jsonify(sanitize({"spolki": spolki, "podsumowanie": podsumowanie}))


@app.route("/api/transaction", methods=["POST"])
def dodaj():
    data = request.json or {}
    tab = data.get("tab", "gpw")
    symbol = data["symbol"].strip().upper()
    nazwa = (data.get("nazwa") or "").strip() or symbol
    akcje = int(data["akcje"])
    cena = float(data["cena"])
    typ = data["typ"]
    apply_transaction(tab, symbol, nazwa, akcje, cena, typ)
    return jsonify({"ok": True})


@app.route("/api/alert", methods=["POST"])
def ustaw_alert():
    data = request.json or {}
    tab = data.get("tab", "gpw")
    symbol = data["symbol"].strip().upper()
    set_alerts(tab, symbol, data.get("alert_powyzej"), data.get("alert_ponizej"))
    return jsonify({"ok": True})


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
