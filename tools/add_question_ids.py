#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schreibt jeder Aufgabe ihre „question_id" ins Feld — den Schlüssel der
Formulierung in questions.json.

question_type allein genügt nicht: „has_rule" wird beim Madd anders formuliert
als sonst und bei einem Wortpaar anders als bei einem einzelnen Wort. Welche
Aufgabe welche Formulierung bekommt, entscheidet tools/questions.py an einer
einzigen Stelle; hier wird das Ergebnis in den Datensatz geschrieben, damit
die Seite es nicht erneut herleiten muss.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from questions import frage_id                                  # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    for x in data:
        neu = frage_id(x)
        felder = [(k, v) for k, v in x.items() if k != "question_id"]
        x.clear()
        for k, v in felder:
            x[k] = v
            if k == "question_type":
                x["question_id"] = neu

    neu_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if neu_blob == blob:
        print("Nichts zu tun – die Fragestellungen sind eingetragen.")
        return 0
    HTML.write_text(src.replace(blob, neu_blob, 1), encoding="utf-8")
    anzahl = len({x["question_id"] for x in data})
    print(f"{len(data)} Aufgaben, {anzahl} verschiedene Fragestellungen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
