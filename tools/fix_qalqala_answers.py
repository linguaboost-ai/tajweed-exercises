#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 2: unvollständige Antwortschlüssel bei den Qalqala-Vokalaufgaben.

Gefragt ist „Welche Vokale stehen VOR den Qalqala-Buchstaben?". Enthält ein Vers
mehrere Qalqala-Stellen, war nur der Vokal der ersten Stelle als richtig
markiert; die Stelle am Versende (Qalqala beim Anhalten) fiel unter den Tisch.
In zwei Aufgaben war zusätzlich der Vokal markiert, den der Qalqala-Buchstabe
selbst trägt — beim Anhalten wird der aber gar nicht gesprochen.

Der Sollwert wird aus dem Verstext hergeleitet, nicht aus dem Muster im Titel:
  * Qalqala-Stelle = Buchstabe aus ق ط ب ج د mit Sukun, dazu der Endbuchstabe
    des letzten Wortes (Qalqala beim Waqf).
  * Vokal davor = Haraka des vorangehenden Buchstabens; ein Langvokal zählt als
    sein kurzes Pendant (ـَا→Fatha, ـُو→Damma, ـِي→Kasra).
  * Hamzat Wasl ٱ übernimmt den Auslaut des Vorworts; am Satzanfang trägt der
    Artikel ٱل Fatha, der Imperativ Kasra bzw. Damma vor Damma im 3. Radikal.

Die Herleitung stimmt bei 107 der 118 Aufgaben mit dem hinterlegten Schlüssel
überein; nur die 11 Abweichungen unten werden geändert. Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
REPORT = Path("docs/qalqala-korrektur.md")

QALQ = set("قطبجد")
HAR = "ًٌٍَُِّْٰٓٔۡ۟۠ـٕ"
SUK, SUPALEF = "ْ", "ٰ"
FA, DA, KA = "َ", "ُ", "ِ"
TANWIN = {"ً": FA, "ٌ": DA, "ٍ": KA}
NAME = {FA: "Fatha", DA: "Damma", KA: "Kasra"}
WAQF = "ۖۗۘۙۚۛۜ۝۞۩ۭ"
DIGITS = "٠١٢٣٤٥٦٧٨٩"


def words(text):
    t = "".join(c for c in text if c not in WAQF and c not in DIGITS)
    return [w for w in t.split() if any(ch not in HAR for ch in w)]


def marks(w, i):
    j, out = i + 1, ""
    while j < len(w) and w[j] in HAR:
        out += w[j]
        j += 1
    return out


def haraka_of(w, i):
    m = marks(w, i)
    for h in (FA, DA, KA):
        if h in m:
            return h
    for t, b in TANWIN.items():
        if t in m:
            return b
    return None


def letters(w):
    return [i for i, c in enumerate(w) if c not in HAR]


def wasl_vowel(w, prev_word):
    if prev_word:
        for i in reversed(letters(prev_word)):
            h = haraka_of(prev_word, i)
            if h:
                return h, f"Auslaut von {prev_word}"
            if prev_word[i] in "اويى":
                return {"ا": FA, "و": DA, "ي": KA, "ى": KA}[prev_word[i]], f"Auslaut von {prev_word}"
        return FA, f"Auslaut von {prev_word}"
    li = letters(w)
    if len(li) > 2 and w[li[1]] == "ل":
        return FA, "Artikel ٱل"
    if len(li) > 3 and haraka_of(w, li[3]) == DA:
        return DA, "Hamzat Wasl vor Damma"
    return KA, "Hamzat Wasl"


def preceding_vowel(w, i, prev_word):
    j = i - 1
    while j >= 0:
        c = w[j]
        if c in HAR:
            if c == SUPALEF:
                return FA, "hochgestelltes Alif (langes a)"
            j -= 1
            continue
        h = haraka_of(w, j)
        if c == "ٱ" and j == letters(w)[0]:
            return wasl_vowel(w, prev_word)
        if c in "اآ":
            if h:
                return h, f"{c} mit {NAME[h]}"
            if j == letters(w)[0]:
                return KA, "Alif am Wortanfang (i)"
            return FA, "langes a"
        if c in "ويى":
            if h:
                return h, f"{c} mit {NAME[h]}"
            return {"و": DA, "ي": KA, "ى": KA}[c], "langer Vokal " + c
        if h:
            return h, f"{c} mit {NAME[h]}"
        if SUK in marks(w, j):
            j -= 1
            continue
        j -= 1
    return (wasl_vowel(w, prev_word) if prev_word else (None, "?"))


def occurrences(text):
    ws = words(text)
    out = []
    for wi, w in enumerate(ws):
        li = letters(w)
        for k in li:
            if w[k] not in QALQ:
                continue
            final = (k == li[-1]) and wi == len(ws) - 1
            if SUK in marks(w, k) or final:
                v, why = preceding_vowel(w, k, ws[wi - 1] if wi else None)
                out.append({"wort": w, "letter": w[k], "vokal": NAME.get(v, "?"),
                            "art": "Sukun" if SUK in marks(w, k) else "Versende",
                            "grund": why})
    return out


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\[.*?\]);\n", src, re.S)
    data = json.loads(m.group(1))

    changes, out = [], src
    for x in data:
        if x["rule"] != "qalqala" or x["question_type"] not in (
            "vowels_before_letter", "vowel_before_letter"
        ):
            continue
        by_text = {o["text"].strip(): o["id"] for o in x["options"]}
        vowel_id = {NAME[h]: by_text[h] for h in (FA, DA, KA) if h in by_text}
        occ = occurrences(x["subject"]["text"])
        want_ids = []
        for o in occ:
            i = vowel_id.get(o["vokal"])
            if i and i not in want_ids:
                want_ids.append(i)
        if not want_ids or set(want_ids) == set(x["answer"]):
            continue

        old = json.dumps(x["answer"], separators=(",", ":"))
        new = json.dumps(want_ids, separators=(",", ":"))
        # Objekt der Aufgabe punktgenau ersetzen, Rest der Datei bleibt unberührt
        start = out.find('{"id":%d,"rule":"qalqala"' % x["id"])
        if start < 0:
            print(f"FEHLER: Aufgabe {x['id']} nicht gefunden."); return 1
        depth, end = 0, start
        for k in range(start, len(out)):
            if out[k] == "{": depth += 1
            elif out[k] == "}":
                depth -= 1
                if depth == 0:
                    end = k + 1
                    break
        obj = out[start:end]
        if obj.count('"answer":' + old) != 1:
            print(f"FEHLER: Antwortfeld von {x['id']} nicht eindeutig."); return 1
        out = out[:start] + obj.replace('"answer":' + old, '"answer":' + new) + out[end:]
        changes.append((x, occ, old, new, vowel_id))

    if not changes:
        print("Nichts zu tun – alle Antwortschlüssel stimmen mit dem Verstext überein.")
        return 0

    HTML.write_text(out, encoding="utf-8")

    inv = lambda vid, x: next(NAME[h] for h in (FA, DA, KA)
                              if next(o for o in x["options"] if o["id"] == vid)["text"].strip() == h)
    lines = ["# Qalqala: korrigierte Antwortschlüssel", "",
             "Gefragt ist der Vokal **vor** dem Qalqala-Buchstaben. Bei Versen mit mehreren",
             "Qalqala-Stellen war nur die erste Stelle im Schlüssel; die Stelle am Versende",
             "(Qalqala beim Anhalten) fehlte. Hergeleitet aus dem Verstext, nicht aus dem",
             "Muster im Aufgabentitel — das Muster zeigt die Fundstellen, nicht die Antwort.", ""]
    print(f"{'ID':>5} {'Lek':>3}  {'vorher':<20} {'nachher':<20}")
    for x, occ, old, new, vid in changes:
        before = "+".join(inv(i, x) for i in json.loads(old))
        after = "+".join(inv(i, x) for i in json.loads(new))
        print(f"{x['id']:>5} {x['lesson']:>3}  {before:<20} {after:<20}")
        lines += [f"## Aufgabe {x['id']} (Lektion {x['lesson']}, Muster `{x.get('pattern')}`)", "",
                  f"> {x['subject']['text']}", "",
                  f"* vorher markiert: **{before}** — jetzt: **{after}**", "", "| Fundstelle | Art | Vokal davor | Begründung |", "|---|---|---|---|"]
        for o in occ:
            lines.append(f"| {o['wort']} | {o['art']} | {o['vokal']} | {o['grund']} |")
        lines.append("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{len(changes)} Aufgaben geändert · Bericht: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
