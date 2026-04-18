import os
from datetime import datetime

from .notify import wyslij_telegram
from .prices import pobierz_cene
from .storage import get_portfolio


def _sekcja(portfel, waluta):
    linie = []
    suma_w = suma_z = 0
    for symbol, info in portfel.items():
        cena = pobierz_cene(symbol)
        if cena is None:
            continue
        w = round(cena * info["akcje"], 2)
        z = round(info["srednia_cena"] * info["akcje"], 2)
        zysk = round(w - z, 2)
        proc = round((zysk / z) * 100, 2) if z else 0
        emoji = "🟢" if zysk >= 0 else "🔴"
        linie.append(
            f"{emoji} <b>{info['nazwa']}</b>: {cena} {waluta} "
            f"({zysk:+.2f} {waluta} / {proc:+.1f}%)"
        )
        suma_w += w
        suma_z += z
    suma_zysk = round(suma_w - suma_z, 2)
    suma_zwrot = round((suma_zysk / suma_z) * 100, 2) if suma_z else 0
    emoji_t = "🟢" if suma_zysk >= 0 else "🔴"
    linie.append(
        f"\n{emoji_t} <b>Lacznie:</b> {round(suma_w, 2)} {waluta} "
        f"({suma_zysk:+.2f} {waluta} / {suma_zwrot:+.1f}%)"
    )
    return linie


def dzienny_raport():
    teraz = datetime.now()
    if teraz.weekday() >= 5:
        return

    linie = [f"📊 <b>Podsumowanie {teraz.strftime('%d.%m.%Y')}</b>\n"]
    linie.append("🇵🇱 <b>GPW</b>")
    linie.extend(_sekcja(get_portfolio("gpw"), "zl"))
    linie.append("\n🇺🇸 <b>USA</b>")
    linie.extend(_sekcja(get_portfolio("usa"), "$"))
    wyslij_telegram("\n".join(linie))


def rekomendacja_dzienna():
    if datetime.now().weekday() >= 5:
        return

    gpw = get_portfolio("gpw")
    usa = get_portfolio("usa")

    def opis(portfel, waluta):
        linie = []
        for symbol, info in portfel.items():
            cena = pobierz_cene(symbol)
            if cena is None:
                continue
            z = round(info["srednia_cena"] * info["akcje"], 2)
            w = round(cena * info["akcje"], 2)
            proc = round((w - z) / z * 100, 2) if z else 0
            linie.append(f"{symbol}: cena={cena}{waluta} P&L={proc:+.1f}%")
        return " | ".join(linie) or "brak"

    prompt = f"""Jesteś polskim doradcą inwestycyjnym. Na podstawie danych z dzisiejszego zamknięcia sesji podaj KONKRETNE rekomendacje na jutro.

GPW (dzisiejsze zamknięcie): {opis(gpw, 'zł')}
USA (dzisiejsze zamknięcie): {opis(usa, '$')}

Napisz krótko po polsku (max 200 słów):
**OCENA DNIA**: 1-2 zdania co się działo
**NA JUTRO**: 2-3 konkretne punkty (co dokupić/sprzedać/obserwować)
**PRIORYTET**: jedna najważniejsza akcja

Bez wstępu, konkretnie."""

    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        tekst = msg.content[0].text.strip()
        wyslij_telegram(f"🤖 <b>Rekomendacja AI — {datetime.now().strftime('%d.%m.%Y')}</b>\n\n{tekst}")
    except Exception as e:
        print(f"Blad rekomendacji AI: {e}")
