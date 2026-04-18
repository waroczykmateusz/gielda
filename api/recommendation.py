import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
import anthropic

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')


def _buduj_prompt(gpw, usa, korelacje):
    def opis_spolki(s, waluta):
        sygnaly_txt = ', '.join(f"{sg['typ']}: {sg['opis']}" for sg in s.get('sygnaly', [])) or 'brak sygnałów'
        zysk_proc = s.get('zysk_proc', 0)
        znak = '+' if zysk_proc >= 0 else ''
        return (
            f"  - {s['nazwa']} ({s['symbol']}): "
            f"cena {s['cena']} {waluta}, "
            f"pozycja {s['wartosc']} {waluta}, "
            f"P&L {znak}{zysk_proc}%, "
            f"RSI_d={s.get('rsi_d', '?')} RSI_w={s.get('rsi_w', '?')}, "
            f"sygnały: [{sygnaly_txt}]"
        )

    gpw_spolki = gpw.get('spolki', [])
    usa_spolki = usa.get('spolki', [])
    gpw_pod = gpw.get('podsumowanie', {})
    usa_pod = usa.get('podsumowanie', {})

    gpw_txt = '\n'.join(opis_spolki(s, 'zł') for s in gpw_spolki) or '  (brak spółek)'
    usa_txt = '\n'.join(opis_spolki(s, '$') for s in usa_spolki) or '  (brak spółek)'

    wysokie = korelacje.get('wysokie_pary', []) if korelacje and not korelacje.get('error') else []
    korel_txt = '\n'.join(
        f"  - {p['nazwa1']} ↔ {p['nazwa2']}: korelacja {p['korelacja']}"
        for p in wysokie
    ) or '  Brak par z wysoką korelacją — portfel dobrze zdywersyfikowany'

    prompt = f"""Jesteś doświadczonym polskim doradcą inwestycyjnym. Przeanalizuj poniższy portfel prywatnego inwestora i podaj KONKRETNE rekomendacje.

=== PORTFEL GPW ===
Wartość: {gpw_pod.get('wartosc', '?')} zł | Zainwestowano: {gpw_pod.get('zainwestowano', '?')} zł | P&L: {gpw_pod.get('zysk', '?')} zł ({gpw_pod.get('zwrot', '?')}%)
{gpw_txt}

=== PORTFEL USA ===
Wartość: {usa_pod.get('wartosc', '?')} $ | Zainwestowano: {usa_pod.get('zainwestowano', '?')} $ | P&L: {usa_pod.get('zysk', '?')} $ ({usa_pod.get('zwrot', '?')}%)
{usa_txt}

=== KONCENTRACJA RYZYKA (korelacja ≥ 0.7) ===
{korel_txt}

Napisz zwięzłą analizę po polsku w 3 sekcjach:
1. **OCENA PORTFELA** (2-3 zdania): ogólna kondycja, główne mocne i słabe strony
2. **KONKRETNE REKOMENDACJE** (lista punktowana): co dokupić, co zredukować, jakie ryzyko ograniczyć — z uzasadnieniem
3. **NAJWAŻNIEJSZY PRIORYTET**: jedna rzecz do zrobienia w pierwszej kolejności

Bądź konkretny i bezpośredni. Nie powtarzaj danych wejściowych."""

    return prompt


@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    try:
        body = request.get_json()
        gpw = body.get('gpw', {})
        usa = body.get('usa', {})
        korelacje = body.get('korelacje', {})

        prompt = _buduj_prompt(gpw, usa, korelacje)

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=800,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return jsonify({'rekomendacja': msg.content[0].text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
