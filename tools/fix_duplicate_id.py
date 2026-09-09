#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 12: doppelt vergebene Aufgabennummer 896.

Beim Zusammenführen der Quelldateien sind die Nummern an der Nahtstelle
kollidiert: Der Qalqala-Block läuft von 577 bis 896 (lückenlos bis auf 672),
der Idgham-Block beginnt ebenfalls bei 896. Zwei verschiedene Aufgaben tragen
dadurch dieselbe Nummer — und dieselbe Tonaufnahme 896.wav.

Die Nummer bleibt bei der Qalqala-Aufgabe, deren Block sie lückenlos erreicht.
Die Idgham-Aufgabe (يَجْعَل لَّكُمْ) bekommt eine neue, bisher unbenutzte Nummer.

ACHTUNG: Welche der beiden Aufgaben die vorhandene 896.wav zeigt, lässt sich
von hier aus nicht sehen. Gehört sie zur Idgham-Aufgabe, genügt es, die Datei
in die neue Nummer umzubenennen; sonst muss sie neu eingesprochen werden.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")
ALT, SRC, NEU = 896, "idgham", 2339


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    treffer = [x for x in data if x["id"] == ALT]
    if len(treffer) < 2:
        print(f"Nichts zu tun – Nummer {ALT} ist eindeutig.")
        return 0
    ziel = [x for x in treffer if x["src"] == SRC]
    if len(ziel) != 1:
        raise SystemExit(f"FEHLER: {len(ziel)} Aufgaben mit src={SRC} unter der Nummer {ALT}.")
    if NEU in {x["id"] for x in data}:
        raise SystemExit(f"FEHLER: Nummer {NEU} ist schon vergeben.")

    x = ziel[0]
    x["id"] = NEU
    if (x.get("subject") or {}).get("audio") == f"{ALT}.wav":
        x["subject"]["audio"] = f"{NEU}.wav"

    ids = [y["id"] for y in data]
    if len(ids) != len(set(ids)):
        raise SystemExit("FEHLER: es gibt weitere doppelte Nummern.")

    HTML.write_text(src.replace(blob, json.dumps(data, ensure_ascii=False,
                                                 separators=(",", ":")), 1), encoding="utf-8")
    print(f"  ✓ {SRC}-Aufgabe „{x['subject']['text']}“: {ALT} → {NEU}")
    print(f"  ✓ Tonaufnahme: {ALT}.wav → {NEU}.wav")
    print(f"\nAlle {len(ids)} Nummern sind jetzt eindeutig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
