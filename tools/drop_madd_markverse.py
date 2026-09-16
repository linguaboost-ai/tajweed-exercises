#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entfernt Aufgabe 2131 — die einzige Markieraufgabe des ganzen Madd-Blocks.

Die Lektionen 29–33 bestehen aus Ja/Nein und Zählen, Lektion 34 aus Zählen;
dazwischen stand ein einziges „Markiere jede Stelle im Vers" auf الٓمٓ, einem
Vers aus einem Wort. Ein Einzelstück einer Aufgabenart, die in den übrigen 256
Madd-Aufgaben nirgends vorkommt — versehentlich dort gelandet.

Damit hat Lektion 34 sechzehn Aufgaben, und der Fragenkatalog kommt ohne
„mark_rule_in_verse.madd" aus. Der Text dazu bleibt in tools/questions.py
stehen: sollten später Markieraufgaben für das Madd dazukommen, greift er
wieder.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")
WEG = 2131


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    behalten = [x for x in data if x["id"] != WEG]
    if len(behalten) == len(data):
        print(f"Nichts zu tun – Aufgabe {WEG} ist nicht mehr im Datensatz.")
        return 0

    neu = json.dumps(behalten, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, neu, 1), encoding="utf-8")
    lek34 = sum(1 for x in behalten if x["lesson"] == 34)
    print(f"Aufgabe {WEG} entfernt. {len(behalten)} Aufgaben, "
          f"Lektion 34 hat jetzt {lek34}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
