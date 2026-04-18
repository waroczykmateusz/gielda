import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

app = Flask(__name__)


def _buduj_prompt(gpw, usa, korelacje):
    def opis_spolki(s, waluta):
        zysk_proc = s.get('zysk_proc', 0)
        sygnaly = [sg['typ'] for sg in s.get('sygnaly', [])]
        syg_txt = ','.join(sygnaly) if sygnaly else '-'
        return (
            f"{s['symbol']}: P&L {'+' if zysk_proc >= 0 else ''}{zysk_proc}% "
            f"RSI_d={s.get('rsi_d','?')} RSI_w={s.get('rsi_w','?')} "
            f"syg=[{syg_txt}]"
        )

    gpw_pod = gpw.get('podsumowanie', {})
    usa_pod = usa.get('podsumowanie', {})
    gpw_txt = ' | '.join(opis_spolki(s, 'zł') for s in gpw.get('spolki', [])) or 'brak'
    usa_txt = ' | '.join(opis_spolki(s, '$') for s in usa.get('spolki', [])) or 'brak'

    wysokie = korelacje.get('wysokie_pary', []) if korelacje and not korelacje.get('error') else []
    korel_txt = ', '.join(f"{p['symbol1']}↔{p['symbol2']}:{p['korelacja']}" for p in wysokie) or 'brak'

    return f"""Jesteś polskim doradcą inwestycyjnym. Przeanalizuj portfel i daj KONKRETNE rekomendacje.

GPW: wartość={gpw_pod.get('wartosc','?')}zł zwrot={gpw_pod.get('zwrot','?')}%
{gpw_txt}

USA: wartość={usa_pod.get('wartosc','?')}$ zwrot={usa_pod.get('zwrot','?')}%
{usa_txt}

Wysokie korelacje (ryzyko): {korel_txt}

Napisz po polsku 3 sekcje:
**OCENA PORTFELA**: 2 zdania o kondycji
**REKOMENDACJE**: 3-4 punkty (co dokupić/sprzedać/zmienić)
**PRIORYTET**: jedna najważniejsza akcja

Konkretnie, bez wstępu."""


@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    try:
        import anthropic

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'Brak ANTHROPIC_API_KEY'}), 500

        body = request.get_json(force=True, silent=True) or {}
        gpw = body.get('gpw', {})
        usa = body.get('usa', {})
        korelacje = body.get('korelacje', {})

        prompt = _buduj_prompt(gpw, usa, korelacje)

        client = anthropic.Anthropic(api_key=api_key, timeout=9.0)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=500,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return jsonify({'rekomendacja': msg.content[0].text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
