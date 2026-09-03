#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 6: Antwortmöglichkeit „kommt nicht vor".

Aufgaben, die nach dem Vokal, der Stelle oder dem auslösenden Buchstaben
fragen, setzten bisher voraus, dass die Regel überhaupt vorkommt. Wo sie das
nicht tut (1611 يَمْشُونَ بِهَآ, 1643 هُمْ يُوقِنُونَ — beides Izhār, kein Ichfāʾ),
gab es keine richtige Antwort. Alle Aufgaben dieser Fragetypen bekommen darum
eine zusätzliche Option; sonst wäre sie dort, wo sie zutrifft, ein Verräter.

Dazu die Anzeige: OPT_DE übersetzt den Schlüssel, und die neue Option steht
über die volle Breite unter den übrigen, damit das Raster der Vokalzeichen
dreispaltig bleibt.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")

QTYPES = ("vowel_before_letter", "vowel_on_letter", "vowels_before_letter",
          "vowels_on_letter", "position_in_word", "which_letter")
NONE = "none"

# 1611 zeigte nur يَمْشُونَ. Mit dem folgenden Wort steht das Bāʾ im Blick, ohne
# dass ein Ichfāʾ entsteht — das Mīm davor gehört zu يَمْشُونَ und trägt Sukūn
# vor Schīn (Izhār), das Nūn am Wortende trägt Fatha. Wortlaut nach 7:195.
NEW_TEXT = {1611: "يَمْشُونَ بِهَآ"}
ANSWER_NONE = (1611, 1643, 1377)

# Vor der einheitlichen Option gab es dafür schon Behelfslösungen mit eigener
# Beschriftung („Keine", bei 1377 sogar Ja/Nein). Die weichen der neuen Option.
AD_HOC = ("Keine", "Ja", "Nein")
# 1377 fragt „Welcher Buchstabe löst das Ichfāʾ aus?" zu مِنْ عَمَلِ und hatte
# statt Buchstaben ein Ja/Nein zur Auswahl. Die vier Kehllaute sind hier die
# lehrreiche Wahl: keiner von ihnen löst ein Ichfāʾ aus.
NEW_OPTIONS = {1377: ["ع", "غ", "ح", "خ"]}

EDITS = [
    ("Beschriftung der neuen Option",
     'const OPT_DE = {yes:"Ja",no:"Nein",start:"Anfang",mid:"Mitte",end:"Ende"};',
     'const OPT_DE = {yes:"Ja",no:"Nein",start:"Anfang",mid:"Mitte",end:"Ende",\n'
     '                none:"kommt nicht vor"};'),
    ("Spaltenzahl ohne die neue Option",
     '  const texts = x.options.map(o => o.text);',
     '  /* „kommt nicht vor" steht über die volle Breite und bestimmt das\n'
     '     Raster der übrigen Antworten nicht mit. */\n'
     '  const texts = x.options.filter(o => o.text !== "none").map(o => o.text);'),
    ("Spaltenzahl aus den übrigen Antworten",
     "(allShort ? Math.min(4, x.options.length) :",
     "(allShort ? Math.min(4, texts.length) :"),
    ("volle Breite für die neue Option",
     '    const row = el("div", "opt" + (correct.has(o.id) ? " correct" : ""));',
     '    const row = el("div", "opt" + (o.text === "none" ? " wide" : "")\n'
     '                              + (correct.has(o.id) ? " correct" : ""));'),
    ("Stil der neuen Option",
     ".opts.cols3,.opts.cols4{grid-template-columns:repeat(2,minmax",
     ".opt.wide{grid-column:1/-1}\n  .opts.cols3,.opts.cols4{grid-template-columns:repeat(2,minmax"),
]
WIDE_CSS = (".opt.wide{grid-column:1/-1}\n", ".opt{")


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out = src

    if 'none:"kommt nicht vor"' in out:
        print("Anzeige war schon angepasst.")
    else:
        for label, needle, rep in EDITS:
            if out.count(needle) != 1:
                raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden.")
            out = out.replace(needle, rep, 1)
            print("  ✓", label)
        css, anchor = WIDE_CSS
        if out.count(anchor) < 1:
            raise SystemExit("FEHLER: Anker für den Stil nicht gefunden.")
        out = out.replace(anchor, css + anchor, 1)
        print("  ✓ Grundstil der neuen Option")

    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    added, answered, merged = 0, [], []
    for x in data:
        touched = False
        if x["id"] in NEW_OPTIONS and [o["text"] for o in x["options"]][:-1] != NEW_OPTIONS[x["id"]]:
            x["options"] = [{"id": k + 1, "text": t} for k, t in enumerate(NEW_OPTIONS[x["id"]])]
            x["answer"] = []
            merged.append(x["id"])
            touched = True
        if x["question_type"] in QTYPES and not any(o["text"] == NONE for o in x["options"]):
            x["options"].append({"id": max((o["id"] for o in x["options"]), default=0) + 1, "text": NONE})
            added += 1
            touched = True
        if x["question_type"] in QTYPES and any(o["text"] in AD_HOC for o in x["options"]):
            none_id = next(o["id"] for o in x["options"] if o["text"] == NONE)
            drop = {o["id"] for o in x["options"] if o["text"] in AD_HOC}
            keep = [o for o in x["options"] if o["id"] not in drop]
            remap = {o["id"]: k + 1 for k, o in enumerate(keep)}
            x["answer"] = sorted({remap[a] if a in remap else remap[none_id] for a in x["answer"]})
            x["options"] = [{"id": remap[o["id"]], "text": o["text"]} for o in keep]
            merged.append(x["id"])
            touched = True
        if x["id"] in NEW_TEXT and x["subject"]["text"] != NEW_TEXT[x["id"]]:
            x["subject"]["text"] = NEW_TEXT[x["id"]]
            touched = True
        if x["id"] in ANSWER_NONE:
            want = [o["id"] for o in x["options"] if o["text"] == NONE]
            if x["answer"] != want:
                x["answer"] = want
                answered.append(x["id"])
                touched = True
    new_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if new_blob != blob:
        out = out.replace(blob, new_blob, 1)
    HTML.write_text(out, encoding="utf-8")
    print(f"\n{added} Aufgaben um „kommt nicht vor“ ergänzt.")
    if answered:
        print(f"als richtige Antwort gesetzt bei: {', '.join(map(str, answered))}")
    if merged:
        print(f"Behelfsoption ersetzt bei {len(merged)} Aufgaben: {', '.join(map(str, sorted(set(merged))))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
