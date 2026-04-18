from flask import Flask, render_template_string, request, redirect
from datetime import datetime
from core import (
    wczytaj_portfel, zapisz_portfel, pobierz_dane_dzienne,
    analizuj_spolke, get_base_dir
)
import json
import os

app = Flask(__name__)

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

HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="60">
    <title>Moj Portfel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f1117; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding: 30px; }
        h1 { font-size: 24px; margin-bottom: 6px; color: #fff; }
        .subtitle { color: #666; font-size: 13px; margin-bottom: 20px; }
        .tabs { display: flex; gap: 4px; margin-bottom: 30px; }
        .tab { padding: 10px 28px; border-radius: 8px 8px 0 0; font-size: 14px; font-weight: bold; cursor: pointer; border: 1px solid #2a2d3a; border-bottom: none; background: #13151f; color: #666; text-decoration: none; }
        .tab.active { background: #1a1d27; color: #fff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .karty { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 40px; }
        .karta { background: #1a1d27; border-radius: 12px; padding: 24px; min-width: 280px; flex: 1; border: 1px solid #2a2d3a; }
        .karta h2 { font-size: 16px; color: #aaa; margin-bottom: 4px; }
        .karta .symbol { font-size: 12px; color: #555; margin-bottom: 16px; }
        .cena { font-size: 36px; font-weight: bold; margin-bottom: 4px; }
        .zmiana { font-size: 14px; margin-bottom: 20px; }
        .plus { color: #26c281; }
        .minus { color: #e74c3c; }
        .row { display: flex; justify-content: space-between; font-size: 13px; padding: 6px 0; border-bottom: 1px solid #2a2d3a; }
        .row:last-child { border-bottom: none; }
        .label { color: #777; }
        .val { font-weight: 600; }
        .alerty { margin-top: 16px; font-size: 12px; }
        .alert-tag { display: inline-block; padding: 3px 8px; border-radius: 4px; margin: 2px; }
        .alert-up { background: #1a3a2a; color: #26c281; }
        .alert-down { background: #3a1a1a; color: #e74c3c; }
        .podsumowanie { background: #1a1d27; border-radius: 12px; padding: 24px; border: 1px solid #2a2d3a; margin-bottom: 30px; }
        .podsumowanie h2 { font-size: 16px; color: #aaa; margin-bottom: 16px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; }
        .box { background: #13151f; border-radius: 8px; padding: 16px; }
        .box .l { font-size: 12px; color: #666; margin-bottom: 6px; }
        .box .v { font-size: 20px; font-weight: bold; }
        .formularz { background: #1a1d27; border-radius: 12px; padding: 24px; border: 1px solid #2a2d3a; margin-bottom: 30px; }
        .formularz h2 { font-size: 16px; color: #aaa; margin-bottom: 16px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; align-items: end; }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-group label { font-size: 12px; color: #666; }
        .form-group input, .form-group select { background: #13151f; border: 1px solid #2a2d3a; border-radius: 6px; padding: 8px 12px; color: #e0e0e0; font-size: 14px; }
        .btn { background: #26c281; color: #000; border: none; border-radius: 6px; padding: 9px 20px; font-size: 14px; font-weight: bold; cursor: pointer; }
        .btn-alert { background: #f39c12; color: #000; border: none; border-radius: 6px; padding: 9px 20px; font-size: 14px; font-weight: bold; cursor: pointer; }
        .footer { color: #444; font-size: 12px; margin-top: 20px; }
        .msg { padding: 10px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
        .msg-ok { background: #1a3a2a; color: #26c281; }
        .usa-badge { background: #1a2a3a; color: #4a9eff; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-left: 6px; }
    </style>
</head>
<body>
    <h1>Moj Portfel</h1>
    <p class="subtitle">Odswiezenie co 60 sekund - {{ czas }}</p>

    {% if komunikat %}
    <div class="msg msg-ok">{{ komunikat }}</div>
    {% endif %}

    <div class="tabs">
        <a href="/?tab=gpw" class="tab {% if tab == 'gpw' %}active{% endif %}">GPW</a>
        <a href="/?tab=usa" class="tab {% if tab == 'usa' %}active{% endif %}">USA</a>
        <a href="/backtest" class="tab">Backtest</a>
    </div>

    <div class="tab-content {% if tab == 'gpw' %}active{% endif %}">
        <div class="podsumowanie">
            <h2>Podsumowanie portfela GPW</h2>
            <div class="grid">
                <div class="box"><div class="l">Wartosc portfela</div><div class="v">{{ portfel_gpw.wartosc }} zl</div></div>
                <div class="box"><div class="l">Zainwestowano</div><div class="v">{{ portfel_gpw.zainwestowano }} zl</div></div>
                <div class="box"><div class="l">Zysk / Strata</div><div class="v {{ portfel_gpw.klasa }}">{{ portfel_gpw.zysk }} zl</div></div>
                <div class="box"><div class="l">Zwrot</div><div class="v {{ portfel_gpw.klasa }}">{{ portfel_gpw.zwrot }}%</div></div>
            </div>
        </div>
        <div class="karty">
            {% for s in spolki_gpw %}
            <div class="karta">
                <h2>{{ s.nazwa }}</h2>
                <div class="symbol">{{ s.symbol }}</div>
                <div class="cena">{{ s.cena }} zl</div>
                <div class="zmiana {{ s.klasa_zmiany }}">{{ s.zmiana_proc }}% dzis</div>
                <div class="row"><span class="label">Liczba akcji</span><span class="val">{{ s.akcje }}</span></div>
                <div class="row"><span class="label">Sr. cena zakupu</span><span class="val">{{ s.srednia }} zl</span></div>
                <div class="row"><span class="label">Wartosc pozycji</span><span class="val">{{ s.wartosc }} zl</span></div>
                <div class="row"><span class="label">Zysk / Strata</span><span class="val {{ s.klasa_zysku }}">{{ s.zysk }} zl ({{ s.zysk_proc }}%)</span></div>
                <div class="alerty">
                    {% if s.alert_up %}<span class="alert-tag alert-up">alert powyzej: {{ s.alert_up }} zl</span>
                    {% else %}<span class="alert-tag" style="background:#1a1d27;color:#444;">brak alertu powyzej</span>{% endif %}
                    {% if s.alert_down %}<span class="alert-tag alert-down">alert ponizej: {{ s.alert_down }} zl</span>
                    {% else %}<span class="alert-tag" style="background:#1a1d27;color:#444;">brak alertu ponizej</span>{% endif %}
                </div>
                {% if s.sygnaly %}
                <div style="margin-top:10px;">
                    {% for typ, opis, kolor in s.sygnaly %}
                    <div style="background:#13151f;border-radius:6px;padding:6px 10px;margin:4px 0;font-size:12px;border-left:3px solid {{ kolor }};">
                        <span style="color:{{ kolor }};font-weight:bold;">{{ typ }}</span>
                        <span style="color:#aaa;"> — {{ opis }}</span>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                <div style="margin-top:8px;display:flex;gap:8px;font-size:11px;flex-wrap:wrap;">
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">RSI D: {{ s.rsi_d }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#aaa;font-weight:bold;">RSI W: {{ s.rsi_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">MACD: {{ s.macd_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">Syg: {{ s.macd_signal_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:{% if s.macd_hist_w > 0 %}#26c281{% else %}#e74c3c{% endif %};font-weight:bold;">Hist: {% if s.macd_hist_w > 0 %}+{% endif %}{{ s.macd_hist_w }} {% if s.macd_hist_w > 0 %}▲{% else %}▼{% endif %}</span>
</div>
            </div>
            {% endfor %}
        </div>
        <div class="formularz">
            <h2>Dodaj transakcje GPW</h2>
            <form method="POST" action="/dodaj?tab=gpw">
                <div class="form-grid">
                    <div class="form-group"><label>Typ</label>
                        <select name="typ"><option value="kup">Kup</option><option value="sprzedaj">Sprzedaj</option></select></div>
                    <div class="form-group"><label>Symbol (np. PKN.WA)</label>
                        <input type="text" name="symbol" placeholder="ASB.WA" required></div>
                    <div class="form-group"><label>Nazwa spolki</label>
                        <input type="text" name="nazwa" placeholder="ASBIS Enterprises"></div>
                    <div class="form-group"><label>Liczba akcji</label>
                        <input type="number" name="akcje" min="1" required></div>
                    <div class="form-group"><label>Cena zakupu (zl)</label>
                        <input type="number" name="cena" step="0.01" min="0.01" required></div>
                    <div class="form-group"><button type="submit" class="btn">Zapisz</button></div>
                </div>
            </form>
        </div>
        <div class="formularz">
            <h2>Ustaw alert cenowy GPW</h2>
            <form method="POST" action="/ustaw_alert?tab=gpw">
                <div class="form-grid">
                    <div class="form-group"><label>Spolka</label>
                        <select name="symbol">{% for s in spolki_gpw %}<option value="{{ s.symbol }}">{{ s.nazwa }}</option>{% endfor %}</select></div>
                    <div class="form-group"><label>Alert powyzej (zl)</label>
                        <input type="number" name="alert_powyzej" step="0.01" min="0" placeholder="np. 200.00"></div>
                    <div class="form-group"><label>Alert ponizej (zl)</label>
                        <input type="number" name="alert_ponizej" step="0.01" min="0" placeholder="np. 150.00"></div>
                    <div class="form-group"><button type="submit" class="btn-alert">Zapisz alert</button></div>
                </div>
            </form>
        </div>
        <p class="footer">GPW: pon-pt 9:00-17:05</p>
    </div>

    <div class="tab-content {% if tab == 'usa' %}active{% endif %}">
        <div class="podsumowanie">
            <h2>Podsumowanie portfela USA <span class="usa-badge">USD</span></h2>
            <div class="grid">
                <div class="box"><div class="l">Wartosc portfela</div><div class="v">{{ portfel_usa.wartosc }} $</div></div>
                <div class="box"><div class="l">Zainwestowano</div><div class="v">{{ portfel_usa.zainwestowano }} $</div></div>
                <div class="box"><div class="l">Zysk / Strata</div><div class="v {{ portfel_usa.klasa }}">{{ portfel_usa.zysk }} $</div></div>
                <div class="box"><div class="l">Zwrot</div><div class="v {{ portfel_usa.klasa }}">{{ portfel_usa.zwrot }}%</div></div>
            </div>
        </div>
        <div class="karty">
            {% for s in spolki_usa %}
            <div class="karta">
                <h2>{{ s.nazwa }} <span class="usa-badge">US</span></h2>
                <div class="symbol">{{ s.symbol }}</div>
                <div class="cena">{{ s.cena }} $</div>
                <div class="zmiana {{ s.klasa_zmiany }}">{{ s.zmiana_proc }}% dzis</div>
                <div class="row"><span class="label">Liczba akcji</span><span class="val">{{ s.akcje }}</span></div>
                <div class="row"><span class="label">Sr. cena zakupu</span><span class="val">{{ s.srednia }} $</span></div>
                <div class="row"><span class="label">Wartosc pozycji</span><span class="val">{{ s.wartosc }} $</span></div>
                <div class="row"><span class="label">Zysk / Strata</span><span class="val {{ s.klasa_zysku }}">{{ s.zysk }} $ ({{ s.zysk_proc }}%)</span></div>
                <div class="alerty">
                    {% if s.alert_up %}<span class="alert-tag alert-up">alert powyzej: {{ s.alert_up }} $</span>
                    {% else %}<span class="alert-tag" style="background:#1a1d27;color:#444;">brak alertu powyzej</span>{% endif %}
                    {% if s.alert_down %}<span class="alert-tag alert-down">alert ponizej: {{ s.alert_down }} $</span>
                    {% else %}<span class="alert-tag" style="background:#1a1d27;color:#444;">brak alertu ponizej</span>{% endif %}
                </div>
                {% if s.sygnaly %}
                <div style="margin-top:10px;">
                    {% for typ, opis, kolor in s.sygnaly %}
                    <div style="background:#13151f;border-radius:6px;padding:6px 10px;margin:4px 0;font-size:12px;border-left:3px solid {{ kolor }};">
                        <span style="color:{{ kolor }};font-weight:bold;">{{ typ }}</span>
                        <span style="color:#aaa;"> — {{ opis }}</span>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                <div style="margin-top:8px;display:flex;gap:8px;font-size:11px;flex-wrap:wrap;">
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">RSI D: {{ s.rsi_d }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#aaa;font-weight:bold;">RSI W: {{ s.rsi_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">MACD: {{ s.macd_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:#666;">Syg: {{ s.macd_signal_w }}</span>
    <span style="background:#13151f;padding:3px 8px;border-radius:4px;color:{% if s.macd_hist_w > 0 %}#26c281{% else %}#e74c3c{% endif %};font-weight:bold;">Hist: {% if s.macd_hist_w > 0 %}+{% endif %}{{ s.macd_hist_w }} {% if s.macd_hist_w > 0 %}▲{% else %}▼{% endif %}</span>
</div>
            </div>
            {% endfor %}
        </div>
        <div class="formularz">
            <h2>Dodaj transakcje USA</h2>
            <form method="POST" action="/dodaj?tab=usa">
                <div class="form-grid">
                    <div class="form-group"><label>Typ</label>
                        <select name="typ"><option value="kup">Kup</option><option value="sprzedaj">Sprzedaj</option></select></div>
                    <div class="form-group"><label>Symbol (np. AAPL)</label>
                        <input type="text" name="symbol" placeholder="RKLB" required></div>
                    <div class="form-group"><label>Nazwa spolki</label>
                        <input type="text" name="nazwa" placeholder="Rocket Lab"></div>
                    <div class="form-group"><label>Liczba akcji</label>
                        <input type="number" name="akcje" min="1" required></div>
                    <div class="form-group"><label>Cena zakupu ($)</label>
                        <input type="number" name="cena" step="0.01" min="0.01" required></div>
                    <div class="form-group"><button type="submit" class="btn">Zapisz</button></div>
                </div>
            </form>
        </div>
        <div class="formularz">
            <h2>Ustaw alert cenowy USA</h2>
            <form method="POST" action="/ustaw_alert?tab=usa">
                <div class="form-grid">
                    <div class="form-group"><label>Spolka</label>
                        <select name="symbol">{% for s in spolki_usa %}<option value="{{ s.symbol }}">{{ s.nazwa }}</option>{% endfor %}</select></div>
                    <div class="form-group"><label>Alert powyzej ($)</label>
                        <input type="number" name="alert_powyzej" step="0.01" min="0" placeholder="np. 100.00"></div>
                    <div class="form-group"><label>Alert ponizej ($)</label>
                        <input type="number" name="alert_ponizej" step="0.01" min="0" placeholder="np. 50.00"></div>
                    <div class="form-group"><button type="submit" class="btn-alert">Zapisz alert</button></div>
                </div>
            </form>
        </div>
        <p class="footer">NYSE/NASDAQ: pon-pt 15:30-22:00 CET</p>
    </div>

</body>
</html>
"""

def przelicz_portfel(portfel):
    spolki = []
    suma_wartosc = 0
    suma_zainwestowano = 0
    for symbol, info in portfel.items():
        cena, zmiana = pobierz_dane_dzienne(symbol)
        if cena is None:
            cena = 0.0
            zmiana = 0.0
        wartosc = round(cena * info["akcje"], 2)
        zainwestowano = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(wartosc - zainwestowano, 2)
        zysk_proc = round((zysk / zainwestowano) * 100, 2) if zainwestowano else 0
        suma_wartosc += wartosc
        suma_zainwestowano += zainwestowano
        sygnaly_spolki, rsi_d, rsi_w, macd_w, macd_signal_w, macd_hist_w = analizuj_spolke(symbol)
        spolki.append({
            "symbol": symbol, "nazwa": info["nazwa"],
            "cena": cena, "zmiana_proc": zmiana,
            "klasa_zmiany": "plus" if zmiana >= 0 else "minus",
            "akcje": info["akcje"], "srednia": info["srednia_cena"],
            "wartosc": wartosc, "zysk": zysk, "zysk_proc": zysk_proc,
            "klasa_zysku": "plus" if zysk >= 0 else "minus",
            "alert_up": info.get("alert_powyzej"),
            "alert_down": info.get("alert_ponizej"),
            "sygnaly": sygnaly_spolki,
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
        "zysk": suma_zysk, "zwrot": suma_zwrot,
        "klasa": "plus" if suma_zysk >= 0 else "minus",
    }

@app.route("/")
def index():
    tab = request.args.get("tab", "gpw")
    komunikat = request.args.get("msg", "")
    czas = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    spolki_gpw, portfel_gpw = przelicz_portfel(wczytaj_portfel())
    spolki_usa, portfel_usa = przelicz_portfel(wczytaj_portfel_usa())
    return render_template_string(HTML,
        tab=tab, czas=czas, komunikat=komunikat,
        spolki_gpw=spolki_gpw, portfel_gpw=portfel_gpw,
        spolki_usa=spolki_usa, portfel_usa=portfel_usa,
    )

@app.route("/dodaj", methods=["POST"])
def dodaj():
    tab = request.args.get("tab", "gpw")
    symbol = request.form["symbol"].strip().upper()
    nazwa = request.form["nazwa"].strip() or symbol
    nowe_akcje = int(request.form["akcje"])
    nowa_cena = float(request.form["cena"])
    typ = request.form["typ"]
    portfel = wczytaj_portfel() if tab == "gpw" else wczytaj_portfel_usa()
    if symbol in portfel:
        stare_akcje = portfel[symbol]["akcje"]
        stara_srednia = portfel[symbol]["srednia_cena"]
        if typ == "kup":
            nowa_srednia = round((stare_akcje * stara_srednia + nowe_akcje * nowa_cena) / (stare_akcje + nowe_akcje), 2)
            portfel[symbol]["akcje"] = stare_akcje + nowe_akcje
            portfel[symbol]["srednia_cena"] = nowa_srednia
        else:
            pozostale = stare_akcje - nowe_akcje
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
    return redirect(f"/?tab={tab}&msg=Transakcja zapisana!")

@app.route("/ustaw_alert", methods=["POST"])
def ustaw_alert():
    tab = request.args.get("tab", "gpw")
    symbol = request.form["symbol"].strip().upper()
    alert_powyzej = request.form["alert_powyzej"].strip()
    alert_ponizej = request.form["alert_ponizej"].strip()
    portfel = wczytaj_portfel() if tab == "gpw" else wczytaj_portfel_usa()
    if symbol in portfel:
        portfel[symbol]["alert_powyzej"] = float(alert_powyzej) if alert_powyzej else None
        portfel[symbol]["alert_ponizej"] = float(alert_ponizej) if alert_ponizej else None
        nazwa = portfel[symbol]["nazwa"]
        if tab == "gpw":
            zapisz_portfel(portfel)
        else:
            zapisz_portfel_usa(portfel)
    else:
        nazwa = symbol
    return redirect(f"/?tab={tab}&msg=Alert zapisany dla {nazwa}!")

def backtest_spolki(symbol, nazwa):
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)

        # Dane tygodniowe — 3 lata zeby miec wystarczajaco duzo sygnalow
        h_w = t.history(period="3y", interval="1wk")
        if len(h_w) < 30:
            return None

        ceny_w = h_w["Close"]

        # RSI tygodniowy
        delta_w = ceny_w.diff()
        rs_w = delta_w.clip(lower=0).rolling(14).mean() / (-delta_w.clip(upper=0)).rolling(14).mean()
        rsi_w = 100 - (100 / (1 + rs_w))

        # SMA na danych dziennych
        h_d = t.history(period="3y", interval="1d")
        ceny_d = h_d["Close"]
        sma50_d = ceny_d.rolling(50).mean()
        sma200_d = ceny_d.rolling(200).mean()

        # MACD tygodniowy
        ema12 = ceny_w.ewm(span=12, adjust=False).mean()
        ema26 = ceny_w.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        sygnaly_rsi = []
        sygnaly_sma = []
        sygnaly_macd = []

        # RSI tygodniowy — szukamy przekroczenia progu < 40
        for i in range(14, len(ceny_w) - 13):
            c = ceny_w.iloc[i]
            d = h_w.index[i]

            # Sygnal: RSI spada ponizej 40 (wchodzi w strefe wyprzedania)
            if rsi_w.iloc[i] < 40 and rsi_w.iloc[i-1] >= 40:
                # Mierzymy wynik po 4, 8 i 12 tygodniach
                zysk_4t = round((ceny_w.iloc[i+4] - c) / c * 100, 1) if i+4 < len(ceny_w) else None
                zysk_8t = round((ceny_w.iloc[i+8] - c) / c * 100, 1) if i+8 < len(ceny_w) else None
                zysk_12t = round((ceny_w.iloc[i+12] - c) / c * 100, 1) if i+12 < len(ceny_w) else None
                sygnaly_rsi.append({
                    "data": d.strftime("%Y-%m-%d"),
                    "cena": round(c, 2),
                    "rsi": round(rsi_w.iloc[i], 1),
                    "zysk_4t": zysk_4t,
                    "zysk_8t": zysk_8t,
                    "zysk_12t": zysk_12t,
                    "trafny": zysk_8t > 0 if zysk_8t is not None else None
                })

        # Zloty krzyz SMA50/SMA200 dzienny
        for i in range(200, len(ceny_d) - 85):
            c = ceny_d.iloc[i]
            d = h_d.index[i]
            if (sma50_d.iloc[i] > sma200_d.iloc[i] and
                sma50_d.iloc[i-1] <= sma200_d.iloc[i-1]):
                # Mierzymy wynik po 4, 8 i 12 tygodniach (20, 40, 60 dni)
                zysk_4t = round((ceny_d.iloc[i+20] - c) / c * 100, 1) if i+20 < len(ceny_d) else None
                zysk_8t = round((ceny_d.iloc[i+40] - c) / c * 100, 1) if i+40 < len(ceny_d) else None
                zysk_12t = round((ceny_d.iloc[i+60] - c) / c * 100, 1) if i+60 < len(ceny_d) else None
                sygnaly_sma.append({
                    "data": d.strftime("%Y-%m-%d"),
                    "cena": round(c, 2),
                    "zysk_4t": zysk_4t,
                    "zysk_8t": zysk_8t,
                    "zysk_12t": zysk_12t,
                    "trafny": zysk_8t > 0 if zysk_8t is not None else None
                })

        # MACD tygodniowy — szukamy bullish crossover (MACD przecina sygnal od dolu)
        for i in range(35, len(ceny_w) - 13):
            c = ceny_w.iloc[i]
            d = h_w.index[i]
            if macd.iloc[i] > macd_signal.iloc[i] and macd.iloc[i-1] <= macd_signal.iloc[i-1]:
                strefa = "dodatnia" if macd.iloc[i] > 0 else "ujemna"
                zysk_4t = round((ceny_w.iloc[i+4] - c) / c * 100, 1) if i+4 < len(ceny_w) else None
                zysk_8t = round((ceny_w.iloc[i+8] - c) / c * 100, 1) if i+8 < len(ceny_w) else None
                zysk_12t = round((ceny_w.iloc[i+12] - c) / c * 100, 1) if i+12 < len(ceny_w) else None
                sygnaly_macd.append({
                    "data": d.strftime("%Y-%m-%d"),
                    "cena": round(c, 2),
                    "macd": round(macd.iloc[i], 3),
                    "strefa": strefa,
                    "zysk_4t": zysk_4t,
                    "zysk_8t": zysk_8t,
                    "zysk_12t": zysk_12t,
                    "trafny": zysk_8t > 0 if zysk_8t is not None else None
                })

        def statystyki(sygnaly):
            if not sygnaly:
                return {"count": 0, "skutecznosc": 0, "avg_4t": 0, "avg_8t": 0, "avg_12t": 0}
            trafne = [s for s in sygnaly if s["trafny"]]
            avg_4t = round(sum(s["zysk_4t"] for s in sygnaly if s["zysk_4t"] is not None) / len(sygnaly), 1)
            avg_8t = round(sum(s["zysk_8t"] for s in sygnaly if s["zysk_8t"] is not None) / len(sygnaly), 1)
            avg_12t = round(sum(s["zysk_12t"] for s in sygnaly if s["zysk_12t"] is not None) / len(sygnaly), 1)
            return {
                "count": len(sygnaly),
                "skutecznosc": round(len(trafne) / len(sygnaly) * 100),
                "avg_4t": avg_4t,
                "avg_8t": avg_8t,
                "avg_12t": avg_12t,
            }

        return {
            "nazwa": nazwa,
            "symbol": symbol,
            "rsi": {"sygnaly": sygnaly_rsi[-5:], "stats": statystyki(sygnaly_rsi)},
            "sma": {"sygnaly": sygnaly_sma[-5:], "stats": statystyki(sygnaly_sma)},
            "macd": {"sygnaly": sygnaly_macd[-5:], "stats": statystyki(sygnaly_macd)},
        }
    except Exception as e:
        print(f"Blad backtestingu {symbol}: {e}")
        return None

HTML_BACKTEST = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Backtest — Moj Portfel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f1117; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding: 30px; }
        h1 { font-size: 24px; margin-bottom: 6px; color: #fff; }
        .subtitle { color: #666; font-size: 13px; margin-bottom: 20px; }
        .nav { margin-bottom: 30px; }
        .nav a { color: #26c281; text-decoration: none; font-size: 14px; margin-right: 20px; }
        .nav a:hover { text-decoration: underline; }
        .spolka { background: #1a1d27; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #2a2d3a; }
        .spolka h2 { font-size: 18px; color: #fff; margin-bottom: 20px; }
        .sekcja { margin-bottom: 20px; }
        .sekcja h3 { font-size: 14px; color: #aaa; margin-bottom: 12px; border-bottom: 1px solid #2a2d3a; padding-bottom: 6px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
        .stat { background: #13151f; border-radius: 8px; padding: 12px; text-align: center; }
        .stat .l { font-size: 11px; color: #666; margin-bottom: 4px; }
        .stat .v { font-size: 18px; font-weight: bold; }
        .plus { color: #26c281; }
        .minus { color: #e74c3c; }
        .neutral { color: #f39c12; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; padding: 8px 10px; color: #666; border-bottom: 1px solid #2a2d3a; font-weight: normal; }
        td { padding: 8px 10px; border-bottom: 1px solid #1a1d27; }
        .tag-trafny { background: #1a3a2a; color: #26c281; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
        .tag-chybiony { background: #3a1a1a; color: #e74c3c; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
        .brak { color: #444; font-style: italic; font-size: 13px; }
        .info { background: #1a2a1a; border: 1px solid #2a3a2a; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 13px; color: #888; }
        .loading { text-align: center; padding: 60px; color: #444; font-size: 16px; }
    </style>
</head>
<body>
    <h1>Backtest strategii</h1>
    <p class="subtitle">Analiza skutecznosci sygnalow RSI tygodniowego i Zlotego Krzyza — ostatnie 3 lata</p>

    <div class="nav">
        <a href="/?tab=gpw">← Wróc do dashboardu</a>
    </div>

    <div class="info">
        RSI tygodniowy &lt; 40: sygnal gdy RSI spada ponizej 40 na interwale tygodniowym — bardziej wiarygodny dla inwestora dlugoterminowego.
        Wyniki mierzone po 4, 8 i 12 tygodniach. Skutecznosc = % sygnalow gdzie cena wzrosla po 8 tygodniach.
    </div>

    {% if ladowanie %}
    <div class="loading">⏳ Trwa obliczanie... To moze zajac 2-3 minuty.</div>
    {% else %}
    {% for wynik in wyniki %}
    {% if wynik %}
    <div class="spolka">
        <h2>{{ wynik.nazwa }} <span style="color:#555;font-size:14px;">{{ wynik.symbol }}</span></h2>

        <div class="sekcja">
            <h3>RSI tygodniowy &lt; 40 (sygnal wyprzedania — dlugoterminowy)</h3>
            {% if wynik.rsi.stats.count > 0 %}
            <div class="stats">
                <div class="stat"><div class="l">Liczba sygnalow</div><div class="v neutral">{{ wynik.rsi.stats.count }}</div></div>
                <div class="stat"><div class="l">Skutecznosc</div><div class="v {% if wynik.rsi.stats.skutecznosc >= 60 %}plus{% elif wynik.rsi.stats.skutecznosc >= 40 %}neutral{% else %}minus{% endif %}">{{ wynik.rsi.stats.skutecznosc }}%</div></div>
                <div class="stat"><div class="l">Avg po 4 tyg.</div><div class="v {% if wynik.rsi.stats.avg_4t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.rsi.stats.avg_4t }}%</div></div>
                <div class="stat"><div class="l">Avg po 8 tyg.</div><div class="v {% if wynik.rsi.stats.avg_8t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.rsi.stats.avg_8t }}%</div></div>
                <div class="stat"><div class="l">Avg po 12 tyg.</div><div class="v {% if wynik.rsi.stats.avg_12t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.rsi.stats.avg_12t }}%</div></div>
            </div>
            <table>
                <tr><th>Data sygnalu</th><th>Cena</th><th>RSI tyg.</th><th>+4 tyg.</th><th>+8 tyg.</th><th>+12 tyg.</th><th>Wynik</th></tr>
                {% for s in wynik.rsi.sygnaly %}
                <tr>
                    <td>{{ s.data }}</td>
                    <td>{{ s.cena }}</td>
                    <td style="color:#f39c12;">{{ s.rsi }}</td>
                    <td class="{% if s.zysk_4t and s.zysk_4t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_4t }}%</td>
                    <td class="{% if s.zysk_8t and s.zysk_8t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_8t }}%</td>
                    <td class="{% if s.zysk_12t and s.zysk_12t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_12t }}%</td>
                    <td>{% if s.trafny %}<span class="tag-trafny">TRAFNY</span>{% else %}<span class="tag-chybiony">CHYBIONY</span>{% endif %}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p class="brak">Brak sygnalow RSI tygodniowego &lt; 40 w ostatnich 3 latach dla tej spolki.</p>
            {% endif %}
        </div>

        <div class="sekcja">
            <h3>Zloty krzyz SMA50/SMA200</h3>
            {% if wynik.sma.stats.count > 0 %}
            <div class="stats">
                <div class="stat"><div class="l">Liczba sygnalow</div><div class="v neutral">{{ wynik.sma.stats.count }}</div></div>
                <div class="stat"><div class="l">Skutecznosc</div><div class="v {% if wynik.sma.stats.skutecznosc >= 60 %}plus{% elif wynik.sma.stats.skutecznosc >= 40 %}neutral{% else %}minus{% endif %}">{{ wynik.sma.stats.skutecznosc }}%</div></div>
                <div class="stat"><div class="l">Avg po 4 tyg.</div><div class="v {% if wynik.sma.stats.avg_4t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.sma.stats.avg_4t }}%</div></div>
                <div class="stat"><div class="l">Avg po 8 tyg.</div><div class="v {% if wynik.sma.stats.avg_8t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.sma.stats.avg_8t }}%</div></div>
                <div class="stat"><div class="l">Avg po 12 tyg.</div><div class="v {% if wynik.sma.stats.avg_12t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.sma.stats.avg_12t }}%</div></div>
            </div>
            <table>
                <tr><th>Data sygnalu</th><th>Cena</th><th>+4 tyg.</th><th>+8 tyg.</th><th>+12 tyg.</th><th>Wynik</th></tr>
                {% for s in wynik.sma.sygnaly %}
                <tr>
                    <td>{{ s.data }}</td>
                    <td>{{ s.cena }}</td>
                    <td class="{% if s.zysk_4t and s.zysk_4t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_4t }}%</td>
                    <td class="{% if s.zysk_8t and s.zysk_8t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_8t }}%</td>
                    <td class="{% if s.zysk_12t and s.zysk_12t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_12t }}%</td>
                    <td>{% if s.trafny %}<span class="tag-trafny">TRAFNY</span>{% else %}<span class="tag-chybiony">CHYBIONY</span>{% endif %}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p class="brak">Brak sygnalow Zlotego Krzyza w ostatnich 3 latach dla tej spolki.</p>
            {% endif %}
        </div>

        <div class="sekcja">
            <h3>MACD tygodniowy — bullish crossover (MACD przecina sygnal od dolu)</h3>
            {% if wynik.macd.stats.count > 0 %}
            <div class="stats">
                <div class="stat"><div class="l">Liczba sygnalow</div><div class="v neutral">{{ wynik.macd.stats.count }}</div></div>
                <div class="stat"><div class="l">Skutecznosc</div><div class="v {% if wynik.macd.stats.skutecznosc >= 60 %}plus{% elif wynik.macd.stats.skutecznosc >= 40 %}neutral{% else %}minus{% endif %}">{{ wynik.macd.stats.skutecznosc }}%</div></div>
                <div class="stat"><div class="l">Avg po 4 tyg.</div><div class="v {% if wynik.macd.stats.avg_4t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.macd.stats.avg_4t }}%</div></div>
                <div class="stat"><div class="l">Avg po 8 tyg.</div><div class="v {% if wynik.macd.stats.avg_8t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.macd.stats.avg_8t }}%</div></div>
                <div class="stat"><div class="l">Avg po 12 tyg.</div><div class="v {% if wynik.macd.stats.avg_12t > 0 %}plus{% else %}minus{% endif %}">{{ wynik.macd.stats.avg_12t }}%</div></div>
            </div>
            <table>
                <tr><th>Data sygnalu</th><th>Cena</th><th>MACD</th><th>Strefa</th><th>+4 tyg.</th><th>+8 tyg.</th><th>+12 tyg.</th><th>Wynik</th></tr>
                {% for s in wynik.macd.sygnaly %}
                <tr>
                    <td>{{ s.data }}</td>
                    <td>{{ s.cena }}</td>
                    <td style="color:#4a9eff;">{{ s.macd }}</td>
                    <td style="color:{% if s.strefa == 'dodatnia' %}#26c281{% else %}#f39c12{% endif %};">{{ s.strefa }}</td>
                    <td class="{% if s.zysk_4t and s.zysk_4t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_4t }}%</td>
                    <td class="{% if s.zysk_8t and s.zysk_8t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_8t }}%</td>
                    <td class="{% if s.zysk_12t and s.zysk_12t > 0 %}plus{% else %}minus{% endif %}">{{ s.zysk_12t }}%</td>
                    <td>{% if s.trafny %}<span class="tag-trafny">TRAFNY</span>{% else %}<span class="tag-chybiony">CHYBIONY</span>{% endif %}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p class="brak">Brak sygnalow MACD tygodniowego w ostatnich 3 latach dla tej spolki.</p>
            {% endif %}
        </div>
    </div>
    {% endif %}
    {% endfor %}
    {% endif %}

</body>
</html>
"""

@app.route("/backtest")
def backtest():
    gpw = wczytaj_portfel()
    usa = wczytaj_portfel_usa()
    wszystkie = {**gpw, **usa}
    wyniki = []
    for symbol, info in wszystkie.items():
        wynik = backtest_spolki(symbol, info["nazwa"])
        wyniki.append(wynik)
    return render_template_string(HTML_BACKTEST, wyniki=wyniki, ladowanie=False)

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    app.run(debug=False)