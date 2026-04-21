import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS

from lib.analysis import analizuj_spolke, _grupuj_sygnaly
from lib.prices import pobierz_dane_dzienne
from lib.ai import pobierz_newsy
from lib.storage import get_portfolio

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


@app.route("/api/recommend")
def recommend():
    symbol = (request.args.get("symbol") or "").strip().upper()
    market = (request.args.get("market") or "gpw").strip().lower()

    if not symbol:
        def err():
            yield f"data: {json.dumps({'error': 'missing symbol'})}\n\n"
        return Response(stream_with_context(err()), mimetype="text/event-stream")

    def generate():
        try:
            import anthropic

            cena, zmiana = pobierz_dane_dzienne(symbol)
            if cena is None:
                cena, zmiana = 0.0, 0.0

            sygnaly, rsi_d, rsi_w, macd_w, macd_signal_w, macd_hist_w = analizuj_spolke(symbol)

            portfel = get_portfolio(market)
            pozycja = portfel.get(symbol)
            nazwa = pozycja["nazwa"] if pozycja else symbol

            newsy = pobierz_newsy(nazwa, symbol)

            if pozycja and pozycja["akcje"] > 0:
                akcje = pozycja["akcje"]
                srednia = pozycja["srednia_cena"]
                wartosc = round(cena * akcje, 2)
                zainwestowano = round(srednia * akcje, 2)
                zysk = round(wartosc - zainwestowano, 2)
                zysk_proc = round(zysk / zainwestowano * 100, 1) if zainwestowano else 0
                sign = "+" if zysk_proc >= 0 else ""
                pozycja_txt = (
                    f"{akcje} akcji | śr. cena zakupu: {srednia} | bieżąca: {cena} "
                    f"({'+' if zmiana >= 0 else ''}{zmiana}% dziś) | "
                    f"wartość: {wartosc} | zysk/strata: {zysk} ({sign}{zysk_proc}%)"
                )
            else:
                pozycja_txt = f"Brak pozycji w portfelu. Bieżąca cena: {cena} ({'+' if zmiana >= 0 else ''}{zmiana}% dziś)."

            if sygnaly:
                grupy = _grupuj_sygnaly(sygnaly)
                sygnaly_txt = "\n".join(
                    f"[{wskaznik}]\n" + "\n".join(f"  - {s}" for s in lista)
                    for wskaznik, lista in grupy.items()
                )
            else:
                sygnaly_txt = "Brak aktywnych sygnałów technicznych."

            hist_sign = "+" if macd_hist_w > 0 else ""
            wskazniki_txt = (
                f"RSI dzienny: {rsi_d} | RSI tygodniowy: {rsi_w} | "
                f"MACD: {macd_w} | Sygnał MACD: {macd_signal_w} | "
                f"Histogram: {hist_sign}{macd_hist_w}"
            )

            prompt = f"""Jesteś doświadczonym analitykiem giełdowym. Przeanalizuj spółkę {nazwa} ({symbol}) i udziel konkretnej rekomendacji.

POZYCJA INWESTORA:
{pozycja_txt}

WSKAŹNIKI TECHNICZNE:
{wskazniki_txt}

SYGNAŁY TECHNICZNE:
{sygnaly_txt}

OSTATNIE NEWSY:
{newsy}

Odpowiedz w trzech częściach:
1. **Sytuacja techniczna** — krótka ocena wskaźników i sygnałów (2 zdania)
2. **Newsy** — czy sentyment jest pozytywny, neutralny czy negatywny (1 zdanie)
3. **Rekomendacja** — TRZYMAJ / DOKUP / REDUKUJ / SPRZEDAJ z konkretnym uzasadnieniem uwzględniającym aktualną pozycję inwestora (2-3 zdania)

Pisz po polsku, konkretnie i bez zbędnego wstępu."""

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=450,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
