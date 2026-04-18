import os
import sys
import json
import requests
import yfinance as yf
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ANTHROPIC_API_KEY

# ─────────────────────────────────────────────
# SCIEZKA DO PORTFELA — dziala i jako .py i .exe
# ─────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

PLIK_PORTFELA = os.path.join(get_base_dir(), "portfel.json")

PORTFEL_DOMYSLNY = {
    "ASB.WA": {
        "nazwa": "ASBIS Enterprises",
        "akcje": 62,
        "srednia_cena": 30.81,
        "alert_powyzej": 65.0,
        "alert_ponizej": 45.0,
    },
    "CRI.WA": {
        "nazwa": "Creotech Instruments",
        "akcje": 3,
        "srednia_cena": 685.67,
        "alert_powyzej": 750.0,
        "alert_ponizej": 600.0,
    },
}

# ─────────────────────────────────────────────
# PORTFEL
# ─────────────────────────────────────────────
def wczytaj_portfel():
    if os.path.exists(PLIK_PORTFELA):
        with open(PLIK_PORTFELA, "r", encoding="utf-8") as f:
            return json.load(f)
    zapisz_portfel(PORTFEL_DOMYSLNY)
    return PORTFEL_DOMYSLNY

def zapisz_portfel(portfel):
    with open(PLIK_PORTFELA, "w", encoding="utf-8") as f:
        json.dump(portfel, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def wyslij_telegram(wiadomosc):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    dane = {"chat_id": TELEGRAM_CHAT_ID, "text": wiadomosc, "parse_mode": "HTML"}
    try:
        requests.post(url, data=dane, timeout=10)
        print(f"Telegram OK ({len(wiadomosc)} znakow)")
    except Exception as e:
        print(f"Blad Telegram: {e}")

# ─────────────────────────────────────────────
# DANE GIELDOWE
# ─────────────────────────────────────────────
def pobierz_cene(symbol):
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="1d", interval="1m")
        if h.empty:
            return None
        return round(h["Close"].iloc[-1], 2)
    except:
        return None

def pobierz_dane_dzienne(symbol):
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="5d", interval="1d")
        if len(h) < 2:
            return None, None
        cena = round(h["Close"].iloc[-1], 2)
        poprzednia = round(h["Close"].iloc[-2], 2)
        zmiana = round((cena - poprzednia) / poprzednia * 100, 2)
        return cena, zmiana
    except:
        return None, None

# ─────────────────────────────────────────────
# SYGNALY
# ─────────────────────────────────────────────
def analizuj_spolke(symbol):
    sygnaly = []
    rsi_d = 0
    rsi_w = 0
    macd_w = 0
    macd_signal_w = 0
    macd_hist_w = 0
    try:
        import yfinance as yf

        # ── DZIENNY (szum, info dodatkowa) ──
        t = yf.Ticker(symbol)
        h_d = t.history(period="1y", interval="1d")
        if len(h_d) >= 50:
            ceny_d = h_d["Close"]
            delta = ceny_d.diff()
            rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
            rsi_d = round((100 - (100 / (1 + rs))).iloc[-1], 1)

        # ── TYGODNIOWY (glowny sygnal) ──
        h_w = t.history(period="2y", interval="1wk")
        if len(h_w) >= 35:
            ceny_w = h_w["Close"]
            cena = ceny_w.iloc[-1]

            # RSI tygodniowy
            delta_w = ceny_w.diff()
            rs_w = delta_w.clip(lower=0).rolling(14).mean() / (-delta_w.clip(upper=0)).rolling(14).mean()
            rsi_w = round((100 - (100 / (1 + rs_w))).iloc[-1], 1)

            if rsi_w < 30:
                sygnaly.append(("SILNY KUP", f"RSI tygodniowy={rsi_w} - mocno wyprzedana", "#26c281"))
            elif rsi_w < 40:
                sygnaly.append(("KUP", f"RSI tygodniowy={rsi_w} - wyprzedana", "#26c281"))
            elif rsi_w > 70:
                sygnaly.append(("UWAGA", f"RSI tygodniowy={rsi_w} - wykupiona", "#e74c3c"))

            # MACD tygodniowy
            ema12 = ceny_w.ewm(span=12, adjust=False).mean()
            ema26 = ceny_w.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal

            macd_w = round(macd.iloc[-1], 3)
            macd_signal_w = round(macd_signal.iloc[-1], 3)
            macd_hist_w = round(macd_hist.iloc[-1], 3)

            # MACD crossover — przeciecie od dolu (kupno)
            if macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]:
                if macd.iloc[-1] < 0:
                    sygnaly.append(("KUP", "MACD tyg. przecial sygnal od dolu (strefa ujemna)", "#f39c12"))
                else:
                    sygnaly.append(("SILNY KUP", "MACD tyg. przecial sygnal od dolu (strefa dodatnia)", "#26c281"))
            # MACD crossover — przeciecie od gory (ostrzezenie)
            elif macd.iloc[-1] < macd_signal.iloc[-1] and macd.iloc[-2] >= macd_signal.iloc[-2]:
                sygnaly.append(("UWAGA", "MACD tyg. spadl ponizej sygnalu", "#e74c3c"))

            # SMA na danych dziennych
            if len(h_d) >= 200:
                ceny_d = h_d["Close"]
                sma20 = ceny_d.rolling(20).mean().iloc[-1]
                sma50 = ceny_d.rolling(50).mean()
                sma200 = ceny_d.rolling(200).mean()

                odch = round((cena - sma20) / sma20 * 100, 1)
                if odch < -5:
                    sygnaly.append(("KUP", f"{abs(odch)}% ponizej SMA20", "#f39c12"))

                if sma50.iloc[-1] > sma200.iloc[-1] and sma50.iloc[-5] <= sma200.iloc[-5]:
                    sygnaly.append(("SILNY KUP", "Zloty krzyz SMA50/SMA200", "#26c281"))

                sma20_s = ceny_d.rolling(20).mean()
                if sma20_s.iloc[-1] > sma50.iloc[-1] and sma20_s.iloc[-5] <= sma50.iloc[-5]:
                    sygnaly.append(("KUP", "Srebrny krzyz SMA20/SMA50", "#f39c12"))

            # Spadek tygodniowy > 8%
            if len(ceny_w) >= 2:
                zmiana_tyg = round((ceny_w.iloc[-1] - ceny_w.iloc[-2]) / ceny_w.iloc[-2] * 100, 1)
                if zmiana_tyg < -8:
                    sygnaly.append(("KUP", f"Spadek {abs(zmiana_tyg)}% w tym tygodniu", "#f39c12"))

            # Spadek miesieczny > 15%
            if len(ceny_w) >= 4:
                zmiana_mies = round((ceny_w.iloc[-1] - ceny_w.iloc[-4]) / ceny_w.iloc[-4] * 100, 1)
                if zmiana_mies < -15:
                    sygnaly.append(("KUP", f"Spadek {abs(zmiana_mies)}% w miesiacu", "#f39c12"))

    except Exception as e:
        print(f"Blad analizy {symbol}: {e}")

    return sygnaly, rsi_d, rsi_w, macd_w, macd_signal_w, macd_hist_w

def wykryj_konflikt(sygnaly):
    typy_bycze = {"KUP", "SILNY KUP"}
    typy_niedzwiedzie = {"UWAGA", "SPRZEDAJ", "SILNA SPRZEDAZ"}
    ma_bycze = any(typ in typy_bycze for typ, _, _ in sygnaly)
    ma_niedzwiedzie = any(typ in typy_niedzwiedzie for typ, _, _ in sygnaly)
    return ma_bycze and ma_niedzwiedzie

def analizuj_konflikt_sygnalu(nazwa, symbol, sygnaly, srednia_cena):
    try:
        import anthropic
        cena, _ = pobierz_dane_dzienne(symbol)
        zysk_proc = round((cena - srednia_cena) / srednia_cena * 100, 1) if cena else None
        opis_sygnalow = "\n".join(f"- {typ}: {opis}" for typ, opis, _ in sygnaly)

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": f"""Jestes analitykiem technicznym. Spolka {nazwa} ({symbol}) ma sprzeczne sygnaly tygodniowe:

{opis_sygnalow}

Inwestor kupil po {srednia_cena}, teraz cena {cena} ({'+' if zysk_proc and zysk_proc >= 0 else ''}{zysk_proc}%).

Rozstrzygnij w max 2 zdaniach: ktory sygnal jest wazniejszy i co robic (trzymaj/dokup/sprzedaj czesc). Konkretnie, bez wstepu."""}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Blad AI: {e}"

def czy_gielda_otwarta():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return False
    if teraz.hour < 9 or teraz.hour >= 17:
        return False
    return True