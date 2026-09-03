#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 7: Verse in den Idgham-Lektionen, die nicht zur Lektion passen.

Der Generator zählte in Lektion 15–21 nur die Idgham-Art der jeweiligen
Lektion. Bei elf Aufgaben stimmt die hinterlegte Zahl deshalb nicht mit dem
Text überein — mal steckt in einem Ablenker mit Antwort 0 doch ein Idgham,
mal fehlt in der Zahl eines aus einer späteren Lektion.

Auf Wunsch des Kursautors wird nicht die Zahl angehoben, sondern der Vers
getauscht: gleiche Länge und Wortzahl, und darin nur Idgham aus der laufenden
oder einer bereits behandelten Lektion. Der Schüler muss also nichts zählen,
was er noch nicht gelernt hat, und die hinterlegte Zahl stimmt.

Dazu Aufgabe 1220, die zwei Idgham zählte, wo nur eines steht: das ٱلنَّعِيمِ
am Ende ist das Lām des Artikels, keine Aufgabe dieser Lektion.

ACHTUNG: Die Tonaufnahmen (audio/<id>.wav) gehören noch zum alten Vers und
müssen für die getauschten Aufgaben neu eingesprochen werden.

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
REPORT = Path("docs/idgham-verse-getauscht.md")

AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

# Aufgabe -> neue Stelle. Der alte Vers steht im Bericht.
REPLACE = {
    # Ablenker mit Antwort 0, in denen doch ein Idgham steckte
    974:  (23, 49),    # وَلَقَدْ ءَاتَيْنَا … — Dāl sākin vor Hamza, kein Idgham
    975:  (15, 13),    # … وَقَدْ خَلَتْ سُنَّةُ … — Dāl und Tāʾ sākin ohne Partner
    982:  (23, 105),   # أَلَمْ تَكُنْ … تُتْلَىٰ … — Tāʾ sākin, kein Idgham
    983:  (10, 96),    # … حَقَّتْ عَلَيْهِمْ … — Tāʾ sākin vor ʿAin
    1175: (7, 15),     # قَالَ إِنَّكَ مِنَ ٱلْمُنظَرِينَ — Nūn sākin vor Ẓāʾ (Ichfāʾ)
    # Zählaufgaben, in deren Vers ein Idgham einer späteren Lektion steckte
    964:  (37, 56),    # كِدتَّ — Dāl in Tāʾ (Lektion 16)
    965:  (26, 22),    # عَبَّدتَّ — Dāl in Tāʾ. Antwort 2 → 1: im ganzen Koran gibt
                       # es keinen Vers mit zwei solchen Stellen und sonst nichts
    972:  (19, 33),    # وُلِدتُّ — Dāl in Tāʾ
    1173: (78, 30),    # فَلَن نَّزِيدَكُمْ — Nūn in Nūn (Lektion 19)
    1292: (74, 9),     # يَوْمَئِذٍ يَوْمٌ — Tanwīn in Yāʾ (Lektion 21)
    1308: (81, 28),    # أَن يَسْتَقِيمَ — Nūn in Yāʾ
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

        n = str(nr.count(text, x["rule"]))
        want = [o["id"] for o in x["options"] if o["text"] == n]
        if not want:
            raise SystemExit(f"FEHLER: {n} steht bei {i} nicht zur Auswahl.")
        had = "+".join(o["text"] for o in x["options"] if o["id"] in x["answer"])
        rows.append((i, x["lesson"], f"{x['sura']}:{x['verse']}", x["subject"]["text"],
                     f"{ref[0]}:{ref[1]}", text, had, n))
        x["sura"], x["verse"] = ref
        x["subject"]["text"] = text
        pat = nr.pattern(text, x["rule"])
        x.pop("pattern", None)
        if pat:
            items = list(x.items())
            x.clear()
            for k, v in items:
                x[k] = v
                if k == "verse":
                    x["pattern"] = pat
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

    L = ["# Getauschte Verse in den Idgham-Lektionen", "",
         "Der Generator zählte nur die Idgham-Art der jeweiligen Lektion. Statt die",
         "Zahl anzuheben — der Schüler müsste sonst etwas mitzählen, das erst später",
         "drankommt — wurde der Vers getauscht: gleiche Länge und Wortzahl, und darin",
         "nur Idgham aus der laufenden oder einer bereits behandelten Lektion.", "",
         "**Die Tonaufnahmen dieser Aufgaben gehören noch zum alten Vers.**", "",
         "| ID | Lektion | Antwort | alt | neu |", "|---|---|---|---|---|"]
    for i, les, oref, otext, nref, ntext, had, n in rows:
        ans = n if had == n else f"{had} → {n}"
        L.append(f"| {i} | {les} | {ans} | {oref} — {otext} | {nref} — {ntext} |")
        print(f"  {i:>5} L{les:<3} {oref} → {nref}   Antwort {ans}")
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
