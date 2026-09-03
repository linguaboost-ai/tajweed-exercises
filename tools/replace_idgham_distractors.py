#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 7: Ablenker in den Idgham-Lektionen, in denen doch ein Idgham steckt.

In Lektion 15–21 gibt es Aufgaben mit der richtigen Antwort 0. In fünf davon
kommt aber sehr wohl ein Idgham vor — nur eines aus einer späteren Lektion,
weshalb der Generator es nicht mitzählte. Da der Kurs keine Idgham-Arten
unterscheidet, ist die Antwort 0 dort falsch.

Diese Aufgaben bekommen einen anderen Vers gleicher Länge und Wortzahl, in dem
gar kein Idgham vorkommt. Ausgewählt wurde jeweils ein Vers, der den
Auslösebuchstaben der Lektion sākin enthält, ohne dass ein Idgham entsteht —
der Ablenker bleibt also lehrreich.

Dazu Aufgabe 1220, die zwei Idgham zählte, wo nur eines steht: das ٱلنَّعِيمِ
am Ende ist das Lām des Artikels, keine Aufgabe dieser Lektion.

ACHTUNG: Die Tonaufnahmen (audio/<id>.wav) gehören noch zum alten Vers und
müssen für die fünf Aufgaben neu eingesprochen werden.

Idempotent.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nun_rules as nr                                            # noqa: E402
from quran_text import to_dataset                                 # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
CORPUS = Path(os.environ.get("QURAN_JSON", "/tmp/quran/package/dist/quran.json"))
REPORT = Path("docs/idgham-ablenker.md")

AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

# Aufgabe -> neue Stelle. Der alte Vers steht im Bericht.
REPLACE = {
    974:  (23, 49),    # وَلَقَدْ ءَاتَيْنَا ... — Dāl sākin vor Hamza, kein Idgham
    975:  (15, 13),    # ... وَقَدْ خَلَتْ سُنَّةُ ... — Dāl und Tāʾ sākin, kein Partner
    982:  (23, 105),   # أَلَمْ تَكُنْ ... تُتْلَىٰ ... — Tāʾ sākin, kein Idgham
    983:  (10, 96),    # ... حَقَّتْ عَلَيْهِمْ ... — Tāʾ sākin vor ʿAin
    1175: (7, 15),     # قَالَ إِنَّكَ مِنَ ٱلْمُنظَرِينَ — Nūn sākin vor Ẓāʾ (Ichfāʾ)
}
RECOUNT = (1220,)


def arabic_number(n):
    return "".join(AR_DIGITS[int(d)] for d in str(n))


def main() -> int:
    q = json.loads(CORPUS.read_text(encoding="utf-8"))
    corp = {(c["id"], v["id"]): v["text"] for c in q for v in c["verses"]}

    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    by_id = {x["id"]: x for x in data}
    used = {(x.get("sura"), x.get("verse")) for x in data if x.get("sura")}

    rows = []
    for i, ref in REPLACE.items():
        x = by_id[i]
        text = to_dataset(corp[ref]) + " " + arabic_number(ref[1])
        if x["subject"]["text"] == text:
            continue
        if ref in used and (x["sura"], x["verse"]) != ref:
            raise SystemExit(f"FEHLER: {ref[0]}:{ref[1]} kommt schon im Datensatz vor.")
        if nr.count(text, "idgham"):
            raise SystemExit(f"FEHLER: {ref[0]}:{ref[1]} enthält doch ein Idgham.")
        want = [o["id"] for o in x["options"] if o["text"] == "0"]
        rows.append((i, x["lesson"], f"{x['sura']}:{x['verse']}", x["subject"]["text"],
                     f"{ref[0]}:{ref[1]}", text))
        x["sura"], x["verse"] = ref
        x["subject"]["text"] = text
        x.pop("pattern", None)
        x["answer"] = want

    fixed = []
    for i in RECOUNT:
        x = by_id[i]
        want = str(nr.count(x["subject"]["text"], x["rule"]))
        ids = [o["id"] for o in x["options"] if o["text"] == want]
        if ids and ids != x["answer"]:
            had = "+".join(o["text"] for o in x["options"] if o["id"] in x["answer"])
            fixed.append((i, x["lesson"], had, want, x["subject"]["text"]))
            x["answer"] = ids
            pat = nr.pattern(x["subject"]["text"], x["rule"])
            if pat != x.get("pattern"):
                x["pattern"] = pat

    if not rows and not fixed:
        print("Nichts zu tun – bereits korrigiert.")
        return 0

    new_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, new_blob, 1), encoding="utf-8")

    L = ["# Idgham-Ablenker mit verstecktem Idgham", "",
         "Aufgaben in Lektion 15–21, deren richtige Antwort 0 lautet, in denen aber",
         "ein Idgham einer späteren Lektion steckt. Da der Kurs keine Idgham-Arten",
         "unterscheidet, wäre 0 dort falsch. Ersetzt durch einen Vers gleicher Länge",
         "und Wortzahl ganz ohne Idgham.", "",
         "**Die Tonaufnahmen dieser fünf Aufgaben gehören noch zum alten Vers.**", "",
         "| ID | Lektion | alt | neu |", "|---|---|---|---|"]
    for i, les, oref, otext, nref, ntext in rows:
        L.append(f"| {i} | {les} | {oref} — {otext} | {nref} — {ntext} |")
        print(f"  {i:>5} L{les:<3} {oref} → {nref}")
    if fixed:
        L += ["", "## Zahl berichtigt", "", "| ID | Lektion | vorher | jetzt | Vers |", "|---|---|---|---|---|"]
        for i, les, had, want, t in fixed:
            L.append(f"| {i} | {les} | {had} | {want} | {t} |")
            print(f"  {i:>5} L{les:<3} Antwort {had} → {want}")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nBericht: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
