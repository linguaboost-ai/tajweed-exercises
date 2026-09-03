#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 8: Fragestellung bei den Madd-Aufgaben (Lektion 29–34).

Der Kurs behandelt den natürlichen Langvokal (Fatḥa + Alif und seine
Geschwister) nicht als eigenes Thema — den kennen die Schüler aus dem normalen
Lesen. Streng genommen ist قَالَ ein Madd ṭabīʿī; im Kurs zählt es nicht als
Madd. Die Frage „Enthält dieses Wort ein Madd?" widersprach deshalb der
hinterlegten Antwort „nein".

Gefragt wird jetzt nach dem, was der Kurs tatsächlich unterrichtet: der
Dehnung über die zwei Einheiten hinaus. Die Antwortschlüssel bleiben, wie sie
sind — sie waren schon nach dieser Lesart gesetzt (bei den 160 Ja/Nein-Aufgaben
steht „ja" genau dann, wenn ein Muster hinterlegt ist).

Betroffen sind alle 257 Aufgaben mit rule = "madd"; die Formulierung entsteht
zur Anzeigezeit, im Datensatz ändert sich nichts.

Idempotent.
"""
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")

HELPER = '''/* Beim Madd fragt der Kurs nicht nach dem natürlichen Langvokal — der gehört
   zum normalen Lesen —, sondern nach der Dehnung darüber hinaus. */
function maddQuestion(x){
  const woerter = (((x.subject && x.subject.text) || "").trim().split(/\\s+/) || []).length;
  switch (x.question_type){
    case "has_rule":
      return woerter > 1
        ? "Enthalten diese W\\u00f6rter eine Dehnung, die l\\u00e4nger als zwei Einheiten ist?"
        : "Enth\\u00e4lt dieses Wort eine Dehnung, die l\\u00e4nger als zwei Einheiten ist?";
    case "count_rule":
      return "Wie oft kommt eine Dehnung vor, die l\\u00e4nger als zwei Einheiten ist?";
    case "match_rule":
      return "Welche W\\u00f6rter enthalten eine Dehnung, die l\\u00e4nger als zwei Einheiten ist?";
    case "mark_rule_in_verse":
      return "Markiere jede Stelle im Vers, an der l\\u00e4nger als zwei Einheiten gedehnt wird.";
    default:
      return null;
  }
}
'''

ANCHOR = '''/* ---------- Fragetext ---------- */
function questionText(x){'''

CALL_OLD = '''  const withPat = base => p ? `${base} <span style="color:var(--ink-2);font-weight:400">(</span>${patternHTML(p)}<span style="color:var(--ink-2);font-weight:400">)</span>` : base;
  switch (x.question_type){'''

CALL_NEW = '''  const withPat = base => p ? `${base} <span style="color:var(--ink-2);font-weight:400">(</span>${patternHTML(p)}<span style="color:var(--ink-2);font-weight:400">)</span>` : base;
  if (x.rule === "madd"){
    const q = maddQuestion(x);
    if (q) return withPat(q);
  }
  switch (x.question_type){'''


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    if "function maddQuestion" in src:
        print("Bereits korrigiert – nichts zu tun.")
        return 0
    out = src
    for label, needle, rep in (
        ("Hilfsfunktion maddQuestion()", ANCHOR, "/* ---------- Fragetext ---------- */\n" + HELPER + "function questionText(x){"),
        ("Aufruf in questionText()", CALL_OLD, CALL_NEW),
    ):
        if out.count(needle) != 1:
            print(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden (erwartet 1×).")
            return 1
        out = out.replace(needle, rep, 1)
        print("  ✓", label)
    HTML.write_text(out, encoding="utf-8")
    n = len(re.findall(r'"rule":"madd"', src))
    print(f"\nGeschrieben: {HTML} · betrifft {n} Aufgaben (Lektion 29–34)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
