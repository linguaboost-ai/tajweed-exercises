#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 13: „Kommt nicht vor" als Antwort bei den Markieraufgaben.

30 Markieraufgaben haben nichts zu markieren, weil die gefragte Regel im Vers
gar nicht vorkommt. Das ist die richtige Antwort — die Seite zeigte dort aber
einen leeren Abschnitt und schob obendrein den Hinweisbalken „kein
Antwortschlüssel" davor, als wäre die Aufgabe kaputt.

Jetzt steht dort „Kommt nicht vor", und der Hinweisbalken bleibt weg: bei einer
Markieraufgabe ist die leere Liste ein Antwortschlüssel, keine Lücke. Für alle
anderen Aufgabentypen ändert sich am Hinweis nichts.

Nachgeprüft: in allen 30 Versen kommt die gefragte Regel tatsächlich nicht vor.

Idempotent.
"""
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")

EDITS = [
    ("Hinweisbalken nur, wo wirklich etwas fehlt",
     '  if (!x.answer || !x.answer.length) out.push("kein Antwortschlüssel");',
     '  /* Bei einer Markieraufgabe heißt die leere Liste „kommt nicht vor“ —\n'
     '     das ist eine Antwort, keine Lücke. */\n'
     '  if ((!x.answer || !x.answer.length) && x.task_type !== "mark_verse")\n'
     '    out.push("kein Antwortschlüssel");'),
    ("Antwort „Kommt nicht vor“",
     '''    const s = sectionEl("Zu markierende Stellen", n ? `${n} ${n === 1 ? "Stelle" : "Stellen"}` : "keine");
    if (n){
      const spans = el("div", "spans");
      x.answer.forEach(t => { const c = el("span", "span-chip ar"); c.textContent = t; spans.append(c); });
      s.append(spans);
    } else s.append(el("div", "empty", "—"));''',
     '''    const s = sectionEl("Zu markierende Stellen",
      n ? `${n} ${n === 1 ? "Stelle" : "Stellen"}` : "1 richtige Antwort");
    if (n){
      const spans = el("div", "spans");
      x.answer.forEach(t => { const c = el("span", "span-chip ar"); c.textContent = t; spans.append(c); });
      s.append(spans);
    } else {
      const row = el("div", "opt wide correct");
      row.append(el("div", "otx", "Kommt nicht vor"), el("span", "tick", "richtig"));
      const wrap = el("div", "opts cols1");
      wrap.append(row);
      s.append(wrap);
    }'''),
]


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out = src
    for label, needle, rep in EDITS:
        if rep in out:
            continue
        if out.count(needle) != 1:
            raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden (erwartet 1×).")
        out = out.replace(needle, rep, 1)
        print("  ✓", label)
    if out == src:
        print("Bereits korrigiert – nichts zu tun.")
        return 0
    HTML.write_text(out, encoding="utf-8")
    n = len(re.findall(r'"task_type":"mark_verse"[^{]*?"answer":\[\]', src))
    print(f"\nGeschrieben: {HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
