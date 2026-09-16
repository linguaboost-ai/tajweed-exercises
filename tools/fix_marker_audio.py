#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nimmt den Marken-Optionen ihre Tondatei.

37 Optionen tragen einen Dateinamen, obwohl es an ihnen nichts zu sprechen
gibt: ihr Text ist die feste Marke „none" („kommt nicht vor"), die die Seite
selbst beschriftet — kein arabisches Wort. Der Name stammt daher, dass der
Generator jede Option der Reihe nach durchnummeriert hat.

Aufgefallen ist das beim Abgleich mit der Aufnahmeliste des Studios: dort
fehlten genau diese 37 Dateien, weil das Aufnahmewerkzeug die Marken richtig
überspringt.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")
MARKEN = {"none", "-", "yes", "no", "start", "mid", "end"}


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    weg = []
    for x in data:
        for o in (x.get("options") or []) + (x.get("items") or []):
            if o.get("audio") and o.get("text") in MARKEN:
                weg.append((x["id"], x["lesson"], o["text"], o.pop("audio")))

    if not weg:
        print("Nichts zu tun – keine Marke trägt eine Tondatei.")
        return 0
    neu = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, neu, 1), encoding="utf-8")
    for i, lek, text, datei in weg:
        print(f"  Aufgabe {i:>4} · Lektion {lek:>2} · „{text}“ · {datei}")
    print(f"{len(weg)} Tondateien gestrichen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
