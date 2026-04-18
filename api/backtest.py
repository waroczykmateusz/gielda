import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

from lib.sanitize import sanitize
from lib.storage import get_portfolio

app = Flask(__name__)


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
            return {
                f"zysk_{s}t": round((ceny.iloc[i + s] - ceny.iloc[i]) / ceny.iloc[i] * 100, 1)
                if i + s < len(ceny) else None
                for s in steps
            }

        def trafny(z):
            return z["zysk_8t"] > 0 if z["zysk_8t"] is not None else None

        syg_rsi, syg_sma, syg_macd = [], [], []
        for i in range(14, len(ceny_w) - 13):
            if rsi_w.iloc[i] < 40 and rsi_w.iloc[i - 1] >= 40:
                z = zyski(ceny_w, i, [4, 8, 12])
                syg_rsi.append({
                    "data": h_w.index[i].strftime("%Y-%m-%d"),
                    "cena": round(float(ceny_w.iloc[i]), 2),
                    "rsi": round(float(rsi_w.iloc[i]), 1),
                    **z,
                    "trafny": trafny(z),
                })
        for i in range(35, len(ceny_w) - 13):
            if macd.iloc[i] > macd_signal.iloc[i] and macd.iloc[i - 1] <= macd_signal.iloc[i - 1]:
                z = zyski(ceny_w, i, [4, 8, 12])
                syg_macd.append({
                    "data": h_w.index[i].strftime("%Y-%m-%d"),
                    "cena": round(float(ceny_w.iloc[i]), 2),
                    "macd": round(float(macd.iloc[i]), 3),
                    "strefa": "dodatnia" if macd.iloc[i] > 0 else "ujemna",
                    **z,
                    "trafny": trafny(z),
                })
        for i in range(200, len(ceny_d) - 85):
            if sma50.iloc[i] > sma200.iloc[i] and sma50.iloc[i - 1] <= sma200.iloc[i - 1]:
                z = zyski(ceny_d, i, [20, 40, 60])
                syg_sma.append({
                    "data": h_d.index[i].strftime("%Y-%m-%d"),
                    "cena": round(float(ceny_d.iloc[i]), 2),
                    "zysk_4t": z["zysk_20t"],
                    "zysk_8t": z["zysk_40t"],
                    "zysk_12t": z["zysk_60t"],
                    "trafny": z["zysk_40t"] is not None and z["zysk_40t"] > 0,
                })

        def stats(s):
            if not s:
                return {"count": 0, "skutecznosc": 0, "avg_4t": 0, "avg_8t": 0, "avg_12t": 0}
            trafne = [x for x in s if x["trafny"]]
            return {
                "count": len(s),
                "skutecznosc": round(len(trafne) / len(s) * 100),
                "avg_4t": round(sum(x["zysk_4t"] for x in s if x["zysk_4t"] is not None) / len(s), 1),
                "avg_8t": round(sum(x["zysk_8t"] for x in s if x["zysk_8t"] is not None) / len(s), 1),
                "avg_12t": round(sum(x["zysk_12t"] for x in s if x["zysk_12t"] is not None) / len(s), 1),
            }

        return {
            "nazwa": nazwa,
            "symbol": symbol,
            "rsi": {"sygnaly": syg_rsi[-5:], "stats": stats(syg_rsi)},
            "macd": {"sygnaly": syg_macd[-5:], "stats": stats(syg_macd)},
            "sma": {"sygnaly": syg_sma[-5:], "stats": stats(syg_sma)},
        }
    except Exception as e:
        print(f"Backtest error {symbol}: {e}")
        return {"symbol": symbol, "nazwa": nazwa, "error": str(e)}


@app.route("/api/backtest")
def backtest():
    symbol = (request.args.get("symbol") or "").strip().upper()
    market = (request.args.get("market") or "").strip().lower()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    nazwa = symbol
    if market in ("gpw", "usa"):
        portfel = get_portfolio(market)
        if symbol in portfel:
            nazwa = portfel[symbol]["nazwa"]

    wynik = _backtest_spolki(symbol, nazwa)
    if wynik is None:
        return jsonify({"error": "insufficient data", "symbol": symbol, "nazwa": nazwa}), 200
    return jsonify(sanitize(wynik))
