#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 10: Halt-Zeichen (Lektion 35–40).

Drei Sachen aus der Durchsicht des Lehrers:

  * „Welches Waqf-Zeichen steht in diesem Vers?" ist eine Mehrfachauswahl, im
    Schlüssel stand aber nur das Zeichen der jeweiligen Lektion — obwohl in den
    Versen mehrere stehen. Der Schlüssel führt jetzt alle auf, die vorkommen.
  * Muʿānaqa (Lektion 40): angehalten werden darf an einer der beiden Stellen,
    also sind beide Wörter richtig. Bisher galt mal das eine, mal das andere,
    sechsmal sogar „keines von beiden". Beide Wörter sind jetzt richtig, und
    die Frage sagt ausdrücklich, dass nur an einer der Stellen angehalten wird.
  * Zwei Markieraufgaben trafen das falsche Vorkommen: das Wort steht zweimal
    im Vers, markiert wurde das erste — bei 2152 das فِرْعَوْنَ mit dem Zeichen
    „Halt verboten", bei 2158 das بِهِۦ mit „besser weiterlesen". Die Spanne
    nennt jetzt auch das Wort davor und trifft damit die richtige Stelle.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")

# Zeichen -> Beschriftung der Antwortmöglichkeit
SIGN = {"ۖ": "صلى", "ۗ": "قلى", "ۘ": "م", "ۙ": "لا", "ۚ": "ج", "ۛ": "∴", "ۜ": "س"}
MUANAQA = "ۛ"
SPAN = {2152: ("فِرْعَوْنَ", "آلَ فِرْعَوْنَ"),
        2158: ("بِهِۦ", "يُؤْمِنُ بِهِۦ")}

EDIT = ("Muʿānaqa-Frage",
        "        ? `Muʿānaqa <span class=\"pat ar\">◌ۛ</span> — an welchem der beiden Wörter darf angehalten werden?`",
        "        ? `Muʿānaqa <span class=\"pat ar\">◌ۛ</span> — an welchem der beiden Wörter darf angehalten werden?"
        " <span style=\"color:var(--ink-3);font-weight:400\">(nur an einer der beiden Stellen, nicht an beiden)</span>`")


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out = src
    label, needle, rep = EDIT
    if rep in out:
        print("Fragetext war schon angepasst.")
    elif out.count(needle) == 1:
        out = out.replace(needle, rep, 1)
        print("  ✓", label)
    else:
        raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden.")

    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    zeichen = muan = spannen = 0
    for x in data:
        if x["rule"] != "waqf":
            continue
        t = (x.get("subject") or {}).get("text") or ""
        if x["question_type"] == "identify_waqf_sign":
            texte = [o["text"] for o in x["options"]]
            if texte[:2] == ["ج", "صلى"]:
                da = {SIGN[c] for c in t if c in SIGN}
                want = sorted(o["id"] for o in x["options"] if o["text"] in da)
                if want and want != sorted(x["answer"]):
                    x["answer"] = want
                    zeichen += 1
            elif x.get("pattern") == MUANAQA:
                # beide Wörter sind richtig, „keines von beiden" bleibt Ablenker
                want = [o["id"] for o in x["options"] if o["text"] != "keines von beiden"]
                if want != x["answer"]:
                    x["answer"] = want
                    muan += 1
        elif x["id"] in SPAN:
            alt, neu = SPAN[x["id"]]
            if alt in x["answer"]:
                if t.count(neu) != 1:
                    raise SystemExit(f"FEHLER: „{neu}“ ist in {x['id']} nicht eindeutig.")
                x["answer"] = [neu if s == alt else s for s in x["answer"]]
                spannen += 1

    new_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if new_blob == blob and out == src:
        print("Nichts zu tun – bereits korrigiert.")
        return 0
    HTML.write_text(out.replace(blob, new_blob, 1) if new_blob != blob else out, encoding="utf-8")
    print(f"\n{zeichen} Aufgaben „Welches Waqf-Zeichen …“ vervollständigt")
    print(f"{muan} Muʿānaqa-Aufgaben: beide Wörter richtig")
    print(f"{spannen} Markierungen auf die richtige Stelle gesetzt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
