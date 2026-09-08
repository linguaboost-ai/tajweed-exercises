#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vokal-Aufgaben beim Tafkhīm geradeziehen.

„Welcher Vokal steht auf dem Tafkhīm-Buchstaben?" ist nur dann eine Frage mit
einer Antwort, wenn das Wort genau einen Tafkhīm-Buchstaben hat. In elf
Aufgaben stehen zwei — dort nennt der Schlüssel nur einen Vokal (42, 74, 122,
138, 546) oder er nennt beide, während Fragetyp und multiple weiter von einem
einzigen ausgehen (290, 298, 314, 410, 418, 506). Bei 214 steht im Schlüssel
ein Sukūn, das auf keinem der Buchstaben sitzt.

Der Vokalsatz wird aus den Buchstaben der bis dahin unterrichteten Lektionen
hergeleitet (Lektion 1 ق, 2 ط, 3 خ, 4 غ, 5 ض, 6 ظ, 7 ص, 8 ر, 9 das Lām in
„Allāh"); Tanwīn zählt als sein Grundvokal, weil die Optionen nur die vier
Harakat anbieten. Geändert wird nur, wo der Schlüssel davon abweicht; der
Fragetyp bleibt stehen, außer die Antwort nennt jetzt mehrere Vokale — dann
wird aus der Einzahl die Mehrzahl und multiple true. Ein bereits gesetztes
multiple bleibt stehen.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import add_spots as A                                            # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")


def vokale(x):
    t = x["subject"]["text"]
    sp = A.tafkheem_spots(t, "regel", x["lesson"] >= 9, A.TAF_LEKTION.get(x["lesson"]))
    aus = set()
    for a, b in sp:
        for c in t[a:b]:
            if c in A.VOKAL and c != A.SHADDA:
                aus.add(A.TANWIN.get(c, c))
    return aus


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    geaendert, muster = [], []
    for x in data:
        if x["rule"] != "tafkheem" or x["task_type"] != "select":
            continue
        if x["question_type"] not in ("vowel_on_letter", "vowels_on_letter"):
            continue
        soll = vokale(x)
        nach_id = {o["text"]: o["id"] for o in x["options"]}
        if not soll:
            neu = [nach_id["none"]] if "none" in nach_id else []
        else:
            if not soll <= set(nach_id):
                continue
            neu = sorted(nach_id[v] for v in soll)
        if set(neu) == set(x["answer"]):
            neu = x["answer"]          # Reihenfolge unangetastet lassen
        # Der Fragetyp bleibt, wie er ist; nur wo mehrere Vokale zu nennen sind,
        # muss aus der Einzahl die Mehrzahl werden.
        qt = "vowels_on_letter" if len(neu) > 1 else x["question_type"]
        mul = True if len(neu) > 1 else x.get("multiple", False)
        if x["answer"] == neu and x["question_type"] == qt and x.get("multiple") == mul:
            continue
        geaendert.append((x["id"], x["answer"], neu, x["question_type"], qt))
        x["answer"] = neu
        x["question_type"] = qt
        x["multiple"] = mul

    # Das Muster im Titel nennt dieselben Stellen wie der Schlüssel. Wo es
    # einen Buchstaben unterschlägt (42) oder einen falschen Vokal nennt
    # (74, 370), wird es aus den Buchstaben neu gesetzt. Muster, die ein
    # ganzes Wort nennen — „ٱللَّهُ" in Lektion 9 —, bleiben unberührt.
    for x in data:
        if x["rule"] != "tafkheem" or x["task_type"] != "select":
            continue
        t = x["subject"]["text"]
        teile = [t[a:b] for a, b in
                 A.tafkheem_spots(t, "regel", x["lesson"] >= 9,
                                  A.TAF_LEKTION.get(x["lesson"]))]
        alt = [q for q in (x.get("pattern") or "").split(":") if q]
        if teile and all(len(q) <= 3 for q in alt) and sorted(alt) != sorted(teile):
            muster.append((x["id"], x.get("pattern"), ":".join(teile)))
            x["pattern"] = ":".join(teile)

    if not geaendert and not muster:
        print("Nichts zu tun.")
        return 0
    neu_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(src.replace(blob, neu_blob, 1), encoding="utf-8")
    for i, alt, neu, aq, nq in geaendert:
        print(f"{i}: {alt} -> {neu}   {aq} -> {nq}")
    for i, alt, neu in muster:
        print(f"{i}: Muster {alt} -> {neu}")
    print(f"{len(geaendert)} Antworten, {len(muster)} Muster geändert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
