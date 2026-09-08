#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 14: kein Halt-Zeichen aus einer späteren Lektion.

Seit der Schlüssel alle Zeichen des Verses nennt, verlangten 19 Aufgaben ein
Zeichen, das erst später unterrichtet wird — in Lektion 35 etwa das صلى aus
Lektion 36. Diese Aufgaben bekommen einen anderen Vers: gleiche Länge und
Wortzahl, das Zeichen der Lektion darin, und sonst nur Zeichen aus bereits
behandelten Lektionen.

  Lektion 35 (ج)    -> Vers mit ۚ, ohne ۖ ۗ ۙ ۘ ۜ ۛ
  Lektion 36 (صلى)  -> Vers mit ۖ, ۚ erlaubt
  Lektion 37 (قلى)  -> Vers mit ۗ, ۚ und ۖ erlaubt

Dazu die acht Qalqala-Aufgaben, deren Muster im Titel eine „1" zeigte, obwohl
keine Fundstelle vorliegt: dort steht jetzt „0".

ACHTUNG: Die Tonaufnahmen der 19 Aufgaben gehören zum alten Vers.

Idempotent.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from quran_text import to_dataset                                 # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
CORPUS = Path(os.environ.get("QURAN_JSON", "/tmp/quran/package/dist/quran.json"))
REPORT = Path("docs/waqf-lektionsreihenfolge.md")

LEK = {"ۚ": 35, "ۖ": 36, "ۗ": 37, "ۙ": 38, "ۘ": 39, "ۜ": 39, "ۛ": 40}
NAME = {"ۖ": "صلى", "ۗ": "قلى", "ۘ": "م", "ۙ": "لا", "ۚ": "ج", "ۛ": "∴", "ۜ": "س"}
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
MUSTER_NULL = (583, 591, 599, 607, 615, 623, 631, 639)


def arabic_number(n):
    return "".join(AR_DIGITS[int(d)] for d in str(n))


def signs(text):
    return [c for c in dict.fromkeys(text) if c in LEK]


def set_pattern(x, pat):
    items = [(k, v) for k, v in x.items() if k != "pattern"]
    x.clear()
    for k, v in items:
        x[k] = v
        if k == "verse" and pat:
            x["pattern"] = pat


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    offen = [x for x in data
             if x["rule"] == "waqf" and x["question_type"] == "identify_waqf_sign"
             and [o["text"] for o in x["options"]][:2] == ["ج", "صلى"]
             and any(LEK[c] > x["lesson"] for c in signs(x["subject"]["text"]))]
    muster = [x for x in data if x["id"] in MUSTER_NULL and x.get("pattern") == "1"]
    if not offen and not muster:
        print("Nichts zu tun – bereits korrigiert.")
        return 0

    q = json.loads(CORPUS.read_text(encoding="utf-8"))
    belegt = {(x.get("sura"), x.get("verse")) for x in data if x.get("sura")}
    pool = []
    for c in q:
        for v in c["verses"]:
            if (c["id"], v["id"]) in belegt:
                continue
            t = to_dataset(v["text"])
            if any(ch in t for ch in "ۢۥ۩"):
                continue
            pool.append((c["id"], v["id"], t, signs(t)))

    rows = []
    for x in sorted(offen, key=lambda x: x["id"]):
        eigen = next(c for c, l in LEK.items() if l == x["lesson"] and c in "ۚۖۗ")
        alt = x["subject"]["text"]
        w, n = len(alt.split()), len(alt)
        passend = [p for p in pool
                   if eigen in p[3] and all(LEK[s] <= x["lesson"] for s in p[3])]
        if not passend:
            raise SystemExit(f"FEHLER: kein Vers für Aufgabe {x['id']}.")
        # Möglichst viele bereits gelernte Zeichen (der Kursautor wollte mehr als
        # eine richtige Antwort), dann gleiche Zahl eigener Zeichen, dann Länge
        passend.sort(key=lambda p: (-len(p[3]), abs(p[2].count(eigen) - alt.count(eigen)),
                                    abs(len(p[2].split()) - w) + abs(len(p[2]) - n) / 12))
        ref = passend[0]
        pool.remove(ref)
        text = ref[2] + " " + arabic_number(ref[1])
        da = signs(text)
        rows.append((x["id"], x["lesson"], f"{x['sura']}:{x['verse']}",
                     "".join(NAME[c] for c in signs(alt)),
                     f"{ref[0]}:{ref[1]}", " + ".join(NAME[c] for c in da), text))
        x["sura"], x["verse"] = ref[0], ref[1]
        x["subject"]["text"] = text
        set_pattern(x, ":".join(da))
        x["answer"] = sorted(o["id"] for o in x["options"] if o["text"] in {NAME[c] for c in da})

    for x in muster:
        set_pattern(x, "0")

    HTML.write_text(src.replace(blob, json.dumps(data, ensure_ascii=False,
                                                 separators=(",", ":")), 1), encoding="utf-8")

    L = ["# Halt-Zeichen: keine späteren Lektionen im Vers", "",
         "Der Schlüssel nennt alle Zeichen, die im Vers stehen. Damit verlangten",
         "19 Aufgaben ein Zeichen, das erst später unterrichtet wird. Sie haben einen",
         "anderen Vers bekommen — gleiche Länge und Wortzahl, das Zeichen der Lektion",
         "darin, sonst nur Zeichen aus behandelten Lektionen.", "",
         "**Die Tonaufnahmen dieser Aufgaben gehören zum alten Vers.**", "",
         "| ID | Lektion | alt | Zeichen alt | neu | Zeichen neu |", "|---|---|---|---|---|---|"]
    for i, les, oref, ozn, nref, nzn, _ in rows:
        L.append(f"| {i} | {les} | {oref} | {ozn} | {nref} | {nzn} |")
        print(f"  {i:>5} L{les}  {oref} ({ozn}) → {nref} ({nzn})")
    if muster:
        L += ["", "## Muster im Titel", "",
              f"{len(muster)} Qalqala-Aufgaben zeigten die Ziffer 1, obwohl keine",
              "Fundstelle vorliegt; jetzt steht dort 0: "
              + ", ".join(str(x["id"]) for x in muster), ""]
        print(f"\n  {len(muster)} Muster „1“ → „0“")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nBericht: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
