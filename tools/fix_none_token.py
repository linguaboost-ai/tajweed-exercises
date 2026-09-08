#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
„Keine" und „keines von beiden" sind deutscher Text und haben im Datensatz
nichts verloren — die Formatregel lässt neben dem Arabischen nur feste Marken
zu (yes/no, start/mid/end, Zahlen, „-", „none"). Beide werden deshalb zur Marke
„none"; die Seite beschriftet sie je nach Aufgabe („keines der Wörter" bei der
Wortauswahl, „keines von beiden" bei der Muʿānaqa, sonst „kommt nicht vor").

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    n = 0
    for x in data:
        for o in x.get("options") or []:
            if o.get("text") in ("Keine", "keines von beiden"):
                o["text"] = "none"
                n += 1
    if not n:
        print("Nichts zu tun.")
        return 0
    neu = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, neu, 1), encoding="utf-8")
    print(f"{n} Optionen von „Keine“ auf „none“ umgestellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
