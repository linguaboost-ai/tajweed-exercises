#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 9: Zuordnungsfragen „Welche Wörter enthalten ein …?"

Zwei Bauarten stecken hinter demselben Fragetyp:

  * mit Vorgabewort — gefragt ist, welches der Wörter darunter zusammen mit
    dem Vorgabewort die Regel ergibt (أَلَمْ + يَأْتِكُم …). Die alte Frage
    „Welche Wörter enthalten ein Ichfāʾ?" führte in die Irre: sie klingt, als
    solle man die Wörter für sich betrachten.
  * ohne Vorgabewort — dort sind die Wörter einzeln zu prüfen.

Die Frage unterscheidet jetzt beides. Dazu die inhaltlichen Korrekturen:

  1378  war unbrauchbar: eine einzige Antwortmöglichkeit, kein Schlüssel.
        Jetzt vier einzelne Wörter, zwei mit Ichfāʾ, zwei mit Izhār.
  1619  hatte يُمْسِكُ als Vorgabewort, obwohl die Wörter einzeln gemeint sind.
        Das Wort steht jetzt als vierte Antwortmöglichkeit, „Keine" als fünfte.
  1624  stellte أَلَمْ vor und bot يَأْتِكُم بَشِيرٌ an — darin steckt das Ichfāʾ
        schon, geprüft wurde also nicht die Verbindung. Jetzt steht بَشِيرٌ als
        Vorgabewort, أَلَمْ يَأْتِكُم als erste Antwort: erst zusammen ergibt
        sich das Ichfāʾ.
  984, 1577, 1587  ließen eine Antwort aus, deren Idgham-Art aus einer
        früheren Lektion stammt (قَالَتْ تَّعْبُدُ, أَن يَكُونَ, غَفُورٌ رَحِيمٌ).

Und schließlich: „Keine" stand bisher in genau den 37 Aufgaben zur Auswahl, in
denen es auch die richtige Antwort war — allein die Anwesenheit verriet sie.
Jetzt steht die Möglichkeit überall.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nun_rules as nr                                            # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
PROMPTLESS = "اختر"
NONE = "Keine"

OPTIONS = {
    # vier einzelne Wörter: zwei mit Ichfāʾ (ن vor ذ bzw. ز), zwei mit Izhār
    1378: ([("مُنذِرٌ", "1378_1.wav"), ("مِنْهُمْ", "1378_2.wav"),
            ("أَنزَلَ", "1378_3.wav"), ("وَٱنْحَرْ", "1378_4.wav")], [1, 3], "نذ:نز"),
    # يُمْسِكُ war Vorgabewort, gehört zu den Antwortmöglichkeiten
    1619: ([("يَعْلَمُونَ", "1619_1.wav"), ("يَمْشُونَ", "1619_2.wav"),
            ("يُوقِنُونَ", "1619_3.wav"), ("يُمْسِكُ", "1619_prompt.wav"),
            (NONE, "1619_4.wav")], [5], None),
    # Vorgabewort ist بَشِيرٌ; أَلَمْ يَأْتِكُم gehört als Ganzes in die erste
    # Antwort — erst die Verbindung يَأْتِكُم + بَشِيرٌ ergibt das Ichfāʾ.
    1624: ([("أَلَمْ يَأْتِكُم", "1624_1.wav"), ("يَعْلَمُونَ", "1624_2.wav"),
            ("يَمْشُونَ", "1624_3.wav"), ("يُمْسِكُ", "1624_4.wav"),
            (NONE, None)], [1], "م ب"),
}
ANSWERS = {984: [1, 2], 1577: [1, 3], 1587: [2]}
PROMPTLESS_NOW = (1619,)
# Aufgabe -> neues Vorgabewort
SUBJECT = {1624: ("بَشِيرٌ", "1624_prompt.wav")}

EDIT = (
    "Frage nach Bauart der Zuordnungsaufgabe",
    '    case "match_rule":            return withPat(`Welche Wörter enthalten ein ${R}?`);',
    '''    case "match_rule": {
      /* Mit Vorgabewort ist die Verbindung gemeint, ohne es das Wort für sich. */
      const vorgabe = (x.subject && x.subject.text) || "";
      return vorgabe && vorgabe !== "اختر"
        ? withPat(`Welche der folgenden Wörter bilden mit diesem ein ${R}?`)
        : withPat(`Markiere alle Wörter mit ${R}. <span style="color:var(--ink-3);font-weight:400">(Mehrfachauswahl möglich)</span>`);
    }''',
)


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out = src
    label, needle, rep = EDIT
    alt = "        ? withPat(`Mit welchen Wörtern wird ein ${R} gebildet?`)"
    neu = "        ? withPat(`Welche der folgenden Wörter bilden mit diesem ein ${R}?`)"
    if neu in out:
        print("Fragetext war schon angepasst.")
    elif alt in out:                      # ältere Fassung dieses Skripts
        out = out.replace(alt, neu, 1)
        print("  ✓ Fragetext nachgezogen")
    else:
        if out.count(needle) != 1:
            raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden.")
        out = out.replace(needle, rep, 1)
        print("  ✓", label)

    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    notes, added = [], 0
    for x in data:
        if x["question_type"] != "match_rule":
            continue
        i = x["id"]
        if i in OPTIONS:
            opts, ans, pat = OPTIONS[i]
            new = [{"id": k + 1, "text": t, **({"audio": a} if a else {"audio": None})}
                   for k, (t, a) in enumerate(opts)]
            ist = [(o["text"], o.get("audio")) for o in x["options"]]
            soll = [(o["text"], o["audio"]) for o in new]
            if ist[:len(soll)] != soll or ist[len(soll):] not in ([], [(NONE, None)]):
                x["options"], x["answer"] = new, ans
                if i in PROMPTLESS_NOW:
                    x["subject"] = {"text": PROMPTLESS, "audio": None}
                elif i in SUBJECT:
                    x["subject"] = {"text": SUBJECT[i][0], "audio": SUBJECT[i][1]}
                set_pattern(x, pat)
                notes.append(f"{i}: Antwortmöglichkeiten neu")
        elif i in ANSWERS and x["answer"] != ANSWERS[i]:
            was = "+".join(o["text"] for o in x["options"] if o["id"] in x["answer"])
            x["answer"] = ANSWERS[i]
            now = "+".join(o["text"] for o in x["options"] if o["id"] in x["answer"])
            notes.append(f"{i}: Antwort {was} → {now}")
        if not any(o["text"] == NONE for o in x["options"]):
            x["options"].append({"id": max(o["id"] for o in x["options"]) + 1,
                                 "text": NONE, "audio": None})
            added += 1

    new_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if new_blob == blob and out == src:
        print("Nichts zu tun – bereits korrigiert.")
        return 0
    HTML.write_text(out.replace(blob, new_blob, 1) if new_blob != blob else out,
                    encoding="utf-8")
    for n in notes:
        print("  ✓", n)
    print(f"\n„Keine“ in {added} weiteren Zuordnungsaufgaben ergänzt.")
    return 0


def set_pattern(x, pat):
    items = [(k, v) for k, v in x.items() if k != "pattern"]
    x.clear()
    for k, v in items:
        x[k] = v
        if k == "verse" and pat:
            x["pattern"] = pat


if __name__ == "__main__":
    raise SystemExit(main())
