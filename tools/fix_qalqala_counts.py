#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 4: Qalqala am Vers- bzw. Wortende in den Zähl- und Ja/Nein-Aufgaben.

Qalqala tritt an zwei Stellen auf:
  * Sukūn mitten im Wort  (Qalqala ṣughrā)  — ق ط ب ج د mit Sukun
  * beim Anhalten am Ende (Qalqala kubrā)   — der Endbuchstabe verliert seinen
    Vokal, dadurch entsteht dort ebenfalls Qalqala

Der Datensatz kennt beide Fälle — z. B. zählt Aufgabe 789 (وَقِيلَ مَنْ ۜ رَاقٍ)
die Stelle am Versende richtig mit. An drei Stellen fehlt sie bzw. eine
Sukūn-Stelle aber. Dieses Skript prüft alle Qalqala-Aufgaben mit Zähl- oder
Ja/Nein-Frage gegen die aus dem Text hergeleiteten Fundstellen und ändert nur
die Aufgaben, bei denen beides nicht zusammenpasst.

Die Herleitung der Fundstellen kommt aus tools/fix_qalqala_answers.py
(Korrektur 2) und wird hier unverändert weiterverwendet.

Nicht angetastet werden:
  * Muster-Aufgaben (position_in_word, match_pattern). Dort benennt das Muster
    im Titel die gemeinte Stelle — 883 تُطْرَدُ mit Muster ◌ُطْ fragt nach dem
    ط in der Wortmitte, nicht nach dem د am Ende.
  * die Vokalaufgaben, die Korrektur 2 bereits abgeglichen hat.

Idempotent.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
REPORT = Path("docs/qalqala-versende.md")

_spec = importlib.util.spec_from_file_location(
    "fq", Path(__file__).with_name("fix_qalqala_answers.py"))
_argv, sys.argv = sys.argv, ["fix_qalqala_answers.py", "/dev/null"]
fq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fq)
sys.argv = _argv


def expected(x, occ):
    """Erwartete Antwort-IDs aus den Fundstellen."""
    if x["question_type"] == "count_rule":
        want = str(len(occ))
    else:                                     # has_rule
        want = "yes" if occ else "no"
    return [o["id"] for o in x["options"] if o["text"] == want], want


def object_span(src, start):
    depth = 0
    for k in range(start, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return start, k + 1
    raise SystemExit("FEHLER: Objektende nicht gefunden.")


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1))

    out, changes, checked = src, [], 0
    for x in data:
        if x["rule"] != "qalqala" or x["question_type"] not in ("count_rule", "has_rule"):
            continue
        checked += 1
        occ = fq.occurrences(x["subject"]["text"])
        want_ids, want = expected(x, occ)
        if not want_ids or set(want_ids) == set(x["answer"]):
            continue

        old = json.dumps(x["answer"], separators=(",", ":"))
        new = json.dumps(want_ids, separators=(",", ":"))
        s, e = object_span(out, out.index('{"id":%d,"rule":"qalqala"' % x["id"]))
        obj = out[s:e]
        if obj.count('"answer":' + old) != 1:
            raise SystemExit(f"FEHLER: Antwortfeld von {x['id']} nicht eindeutig.")
        out = out[:s] + obj.replace('"answer":' + old, '"answer":' + new, 1) + out[e:]
        before = "+".join(o["text"] for o in x["options"] if o["id"] in x["answer"])
        changes.append((x, occ, before, want))

    print(f"{checked} Zähl- und Ja/Nein-Aufgaben geprüft.")
    if not changes:
        print("Nichts zu tun – alle Antworten passen zu den Fundstellen im Text.")
        return 0

    HTML.write_text(out, encoding="utf-8")
    write_report(changes)
    for x, occ, before, want in changes:
        print(f"  {x['id']:>5} L{x['lesson']}  {before} → {want}   {x['subject']['text'][:50]}")
    print(f"\n{len(changes)} Aufgaben geändert · Bericht: {REPORT}")
    return 0


def write_report(changes):
    L = ["# Qalqala: fehlende Fundstellen in Zähl- und Ja/Nein-Aufgaben", "",
         "Qalqala entsteht am Sukūn im Wortinneren (ṣughrā) und beim Anhalten am",
         "Ende (kubrā) — dort verliert der Endbuchstabe seinen Vokal. Beide Fälle",
         "zählen. Geprüft wurden alle Qalqala-Aufgaben mit Zähl- oder Ja/Nein-Frage;",
         "geändert wurden nur die folgenden.", ""]
    for x, occ, before, want in changes:
        L += [f"## Aufgabe {x['id']} (Lektion {x['lesson']}, {x['question_type']})", "",
              f"> {x['subject']['text']}", "",
              f"* bisher: **{before}** — jetzt: **{want}**", "",
              "| Fundstelle | Buchstabe | Art | Begründung |", "|---|---|---|---|"]
        for o in occ:
            art = "Sukūn im Wort" if o["art"] == "Sukun" else "Ende – beim Anhalten"
            L.append(f"| {o['wort']} | {o['letter']} | {art} | {o['grund']} |")
        L.append("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
