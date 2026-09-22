#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Die Rückmeldungen aus der Tonaufnahme.

Drei falsche Antwortschlüssel und vier Schreibfehler, die beim Einsprechen
aufgefallen sind.

Antwortschlüssel — „kommt nicht vor" stimmt dort nicht:

  931   هُمْ + مَتَاعُ           Mīm sākin trifft Mīm: Idghām. Richtig ist 2.
  1007  هُمْ + مَتَاعُ / مِنْ     zweimal dasselbe: richtig sind 2 und 3.
  1019  لَمْ + مَتَاعُ / مِنْ     ebenso: richtig sind 2 und 3.

Schreibfehler:

  173    وَلِلَٰذٰلِكَ → وَلِذَٰلِكَ. Ein Lām zu viel; 11:119 liest
         وَلِذَٰلِكَ خَلَقَهُمْ.
  292_2  مُضِيئَة → مُضِيئَةَ. Am Ende fehlte die Harakah, das Wort wurde
         mit Sukūn gelesen. Die drei Geschwisterwörter enden alle auf Fatḥa.
  1090   قُرَّةُ عَيْنٍ لَّي → قُرَّتُ عَيْنٍ لِّى. Das Lām braucht Kasra,
         nicht Fatḥa; 28:9 liest قُرَّتُ عَيْنٍ لِّي, also auch Tāʾ statt
         Tāʾ marbūṭa.
  1217   غَشَاوَةٌ → غِشَٰوَةٌ. Das Ghain braucht Kasra; 2:7 liest غِشَٰوَةٞ,
         mit hochgestelltem Alif statt vollem.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")

# id -> gewünschte Optionstexte der richtigen Antwort
ANTWORTEN = {
    931: ["مَتَاعُ"],
    1007: ["مَتَاعُ", "مِنْ"],
    1019: ["مَتَاعُ", "مِنْ"],
}

# id -> (Erkennungsstück im alten Text, neuer Text). Die neuen Texte stehen
# als Codepunkte da, damit sie beim Kopieren nicht still normalisiert werden.
TEXTE = {
    173: ("\u0644\u0650\u0644\u064e\u0670\u0630",      # وَلِلَٰذ…
          "\u0648\u064e\u0644\u0650\u0630\u064e\u0670\u0644\u0650\u0643\u064e"
          "\u0020\u062e\u064e\u0644\u064e\u0642\u064e\u0647\u064f\u0645\u0652"
          "\u0020\u06d7"),
    1090: ("\u0644\u0651\u064e\u064a",                   # …لَّي
           "\u0642\u064f\u0631\u0651\u064e\u062a\u064f\u0020\u0639\u064e\u064a"
           "\u0652\u0646\u064d\u0020\u0644\u0651\u0650\u0649"),
    1217: ("\u063a\u064e\u0634",                          # غَش…
           "\u063a\u0650\u0634\u064e\u0670\u0648\u064e\u0629\u064c"
           "\u0020\u0648\u064e\u0644\u064e\u0647\u064f\u0645\u0652"),
}
# (id, Item-Nummer) -> (Erkennungsstück, neuer Text)
ITEMS = {(292, 2): ("\u0626\u064e\u0629",                  # …ئَة ohne Harakah
                    "\u0645\u064f\u0636\u0650\u064a\u0626\u064e\u0629\u064e")}


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    nach_id = {x["id"]: x for x in data}
    getan = []

    for i, texte in ANTWORTEN.items():
        x = nach_id[i]
        neu = sorted(o["id"] for o in x["options"] if o["text"] in texte)
        if len(neu) != len(texte):
            raise SystemExit(f"{i}: Optionen {texte} nicht gefunden")
        if x["answer"] != neu:
            getan.append(f"{i}: Antwort {x['answer']} → {neu} ({' / '.join(texte)})")
            x["answer"] = neu

    for i, (merkmal, neu) in TEXTE.items():
        x = nach_id[i]
        alt = x["subject"]["text"]
        if alt == neu:
            continue
        if merkmal not in alt:
            raise SystemExit(f"{i}: {merkmal!r} steht nicht in {alt!r}")
        x["subject"]["text"] = neu
        getan.append(f"{i}: {alt} → {neu}")

    for (i, nr), (merkmal, neu) in ITEMS.items():
        o = next(o for o in nach_id[i]["items"] if o["id"] == nr)
        alt = o["text"]
        if alt == neu:
            continue
        if merkmal not in alt:
            raise SystemExit(f"{i}_{nr}: {merkmal!r} steht nicht in {alt!r}")
        o["text"] = neu
        getan.append(f"{i}_{nr}: {alt} → {neu}")

    if not getan:
        print("Nichts zu tun – die Korrekturen sind drin.")
        return 0
    neu_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, neu_blob, 1), encoding="utf-8")
    for z in getan:
        print("  " + z)
    print(f"{len(getan)} Korrekturen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
