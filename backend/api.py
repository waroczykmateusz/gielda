from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from core import (
    wczytaj_portfel, zapisz_portfel, pobierz_dane_dzienne,
    analizuj_spolke, get_base_dir
)
import json
import os

app = Flask(__name__)
CORS(app)

PLIK_USA = os.path.join(get_base_dir(), "portfel_usa.json")

PORTFEL_USA_DOMYSLNY = {
    "RKLB": {"nazwa": "Rocket Lab", "akcje": 3, "srednia_cena": 72.00, "alert_powyzej": None, "alert_ponizej": None},
    "LUNR": {"nazwa": "Intuitive Machines", "akcje": 40, "srednia_cena": 24.66, "alert_powyzej": None, "alert_ponizej": None},
    "PL": {"nazwa": "Planet Labs", "akcje": 20, "srednia_cena": 36.75, "alert_powyzej": None, "alert_ponizej": None},
    "RDW": {"nazwa": "Redwire", "akcje": 21, "srednia_cena": 10.38, "alert_powyzej": None, "alert_ponizej": None},
    "KTOS": {"nazwa": "Kratos Defense", "akcje": 3, "srednia_cena": 79.38, "alert_powyzej": None, "alert_ponizej": None},
    "ASTS": {"nazwa": "AST SpaceMobile", "akcje": 3, "srednia_cena": 100.50, "alert_powyzej": None, "alert_ponizej": None},
}

def wczytaj_portfel_usa():
    if os.path.exists(PLIK_USA):
        with open(PLIK_USA, "r", encoding="utf-8") as f:
            return json.load(f)
    zapisz_portfel_usa(PORTFEL_USA_DOMYSLNY)
    return PORTFEL_USA_DOMYSLNY

def zapisz_portfel_usa(portfel):
    with open(PLIK_USA, "w", encoding="utf-8") as f:
        json.dump(portfel, f, ensure_ascii=False, indent=2)

def przelicz_portfel(portfel):
    spolki = []
    suma_wartosc = suma_zainwestowano = 0
    for symbol, info in portfel.items():
        cena, zmiana = pobierz_dane_dzienne(symbol)
        if cena is None:
            cena, zmiana = 0.0, 0.0
        wartosc = round(cena * info["akcje"], 2)
        zainwestowano = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(wartosc - zainwestowano, 2)
        zysk_proc = round((zysk / zainwestowano) * 100, 2) if zainwestowano else 0
        suma_wartosc += wartosc
        suma_zainwestowano += zainwestowano
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
    }

@app.route("/api/portfolio/<tab>")
def portfolio(tab):
    portfel = wczytaj_portfel() if tab == "gpw" else wczytaj_portfel_usa()
    spolki, podsumowanie = przelicz_portfel(portfel)
    return jsonify({"spolki": spolki, "podsumowanie": podsumowanie})

@app.route("/api/transaction", methods=["POST"])
def dodaj():
    data = request.json
    tab = data.get("tab", "gpw")
    symbol = data["symbol"].strip().upper()
    nazwa = data.get("nazwa", "").strip() or symbol
    nowe_akcje = int(data["akcje"])
    nowa_cena = float(data["cena"])
    typ = data["typ"]
    portfel = wczytaj_portfel() if tab == "gpw" else wczytaj_portfel_usa()
    if symbol in portfel:
        stare = portfel[symbol]
        if typ == "kup":
            nowa_srednia = round((stare["akcje"] * stare["srednia_cena"] + nowe_akcje * nowa_cena) / (stare["akcje"] + nowe_akcje), 2)
            portfel[symbol]["akcje"] = stare["akcje"] + nowe_akcje
            portfel[symbol]["srednia_cena"] = nowa_srednia
        else:
            pozostale = stare["akcje"] - nowe_akcje
            if pozostale <= 0:
                del portfel[symbol]
            else:
                portfel[symbol]["akcje"] = pozostale
    else:
        portfel[symbol] = {"nazwa": nazwa, "akcje": nowe_akcje, "srednia_cena": nowa_cena, "alert_powyzej": None, "alert_ponizej": None}
    if tab == "gpw":
        zapisz_portfel(portfel)
    else:
        zapisz_portfel_usa(portfel)
    return jsonify({"ok": True})

@app.route("/api/alert", methods=["POST"])
def ustaw_alert():
    data = request.json
    tab = data.get("tab", "gpw")
    symbol = data["symbol"].strip().upper()
    portfel = wczytaj_portfel() if tab == "gpw" else wczytaj_portfel_usa()
    if symbol in portfel:
        portfel[symbol]["alert_powyzej"] = data.get("alert_powyzej")
        portfel[symbol]["alert_ponizej"] = data.get("alert_ponizej")
        if tab == "gpw":
            zapisz_portfel(portfel)
        else:
            zapisz_portfel_usa(portfel)
    return jsonify({"ok": True})

@app.route("/api/backtest")
def backtest():
    import yfinance as yf
    gpw = wczytaj_portfel()
    usa = wczytaj_portfel_usa()
    wyniki = []
    for symbol, info in {**gpw, **usa}.items():
        wyniki.append(_backtest_spolki(symbol, info["nazwa"]))
    return jsonify([w for w in wyniki if w])

def _backtest_spolki(symbol, nazwa):
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h_w = t.history(period="3y", interval="1wk")
        if len(h_w) < 35:
            return None
        ceny_w = h_w["Close"]

        delta_w = ceny_w.diff()
        rs_w = delta_w.clip(lower=0).rolling(14).mean() / (-delta_w.clip(upper=0)).rolling(14).mean()
        rsi_w = 100 - (100 / (1 + rs_w))

        ema12 = ceny_w.ewm(span=12, adjust=False).mean()
        ema26 = ceny_w.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        h_d = t.history(period="3y", interval="1d")
        ceny_d = h_d["Close"]
        sma50 = ceny_d.rolling(50).mean()
        sma200 = ceny_d.rolling(200).mean()

        def zyski(ceny, i, steps):
            return {f"zysk_{s}t": round((ceny.iloc[i+s] - ceny.iloc[i]) / ceny.iloc[i] * 100, 1) if i+s < len(ceny) else None for s in steps}

        def trafny(z): return z["zysk_8t"] > 0 if z["zysk_8t"] is not None else None

        syg_rsi, syg_sma, syg_macd = [], [], []
        for i in range(14, len(ceny_w) - 13):
            if rsi_w.iloc[i] < 40 and rsi_w.iloc[i-1] >= 40:
                z = zyski(ceny_w, i, [4, 8, 12])
                syg_rsi.append({"data": h_w.index[i].strftime("%Y-%m-%d"), "cena": round(ceny_w.iloc[i], 2), "rsi": round(rsi_w.iloc[i], 1), **z, "trafny": trafny(z)})
        for i in range(35, len(ceny_w) - 13):
            if macd.iloc[i] > macd_signal.iloc[i] and macd.iloc[i-1] <= macd_signal.iloc[i-1]:
                z = zyski(ceny_w, i, [4, 8, 12])
                syg_macd.append({"data": h_w.index[i].strftime("%Y-%m-%d"), "cena": round(ceny_w.iloc[i], 2), "macd": round(macd.iloc[i], 3), "strefa": "dodatnia" if macd.iloc[i] > 0 else "ujemna", **z, "trafny": trafny(z)})
        for i in range(200, len(ceny_d) - 85):
            if sma50.iloc[i] > sma200.iloc[i] and sma50.iloc[i-1] <= sma200.iloc[i-1]:
                z = zyski(ceny_d, i, [20, 40, 60])
                syg_sma.append({"data": h_d.index[i].strftime("%Y-%m-%d"), "cena": round(ceny_d.iloc[i], 2), "zysk_4t": z["zysk_20t"], "zysk_8t": z["zysk_40t"], "zysk_12t": z["zysk_60t"], "trafny": z["zysk_40t"] is not None and z["zysk_40t"] > 0})

        def stats(s):
            if not s: return {"count": 0, "skutecznosc": 0, "avg_4t": 0, "avg_8t": 0, "avg_12t": 0}
            trafne = [x for x in s if x["trafny"]]
            return {"count": len(s), "skutecznosc": round(len(trafne)/len(s)*100),
                    "avg_4t": round(sum(x["zysk_4t"] for x in s if x["zysk_4t"] is not None)/len(s), 1),
                    "avg_8t": round(sum(x["zysk_8t"] for x in s if x["zysk_8t"] is not None)/len(s), 1),
                    "avg_12t": round(sum(x["zysk_12t"] for x in s if x["zysk_12t"] is not None)/len(s), 1)}

        return {"nazwa": nazwa, "symbol": symbol,
                "rsi": {"sygnaly": syg_rsi[-5:], "stats": stats(syg_rsi)},
                "macd": {"sygnaly": syg_macd[-5:], "stats": stats(syg_macd)},
                "sma": {"sygnaly": syg_sma[-5:], "stats": stats(syg_sma)}}
    except Exception as e:
        print(f"Backtest error {symbol}: {e}")
        return None

if __name__ == "__main__":
    app.run(port=5000, debug=False)
