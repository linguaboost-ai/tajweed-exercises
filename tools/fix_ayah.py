#!/usr/bin/env python3
"""
Korrektur 1: Versnummern am Wortende richtig setzen.

Im Datensatz stehen an manchen Aufgaben indische Ziffern direkt am Wortende,
z. B.  أَحَدٌ١  — sie werden dadurch wie eine normale Ziffer gesetzt.
Gemeint ist aber die Versnummer, die im Mushaf in einer verzierten Kartusche
steht. Unicode bildet das mit U+06DD (ARABIC END OF AYAH) ab: das Zeichen
direkt vor den Ziffern, die Schrift setzt die Ziffern dann in das Ornament.

Dieses Skript ist idempotent: mehrfach ausgeführt ändert es nichts mehr.
"""
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")

FONT_FACE = """
/* Ornament der Versnummer (U+06DD). Nur dieses eine Zeichen samt Ziffern
   kommt aus Amiri Quran, der restliche Text bleibt in der Hausschrift. */
@font-face{
  font-family:'AyahMark';
  src:url('fonts/amiri-quran-arabic-400-normal.woff2') format('woff2');
  font-weight:normal;font-style:normal;font-display:swap;
}
"""

AYAH_CSS = """
/* Versnummer: Kartusche mit der Ziffer darin, mit Luft zum Wort davor */
.ayah{
  font-family:'AyahMark','Hafs','Amiri Quran','Amiri',serif;
  white-space:nowrap;
  padding-inline-start:.12em;
}
"""

AYAH_JS = """
/* Indische Ziffern am Wortende sind Versnummern, keine Ziffern im Wort:
   U+06DD davor setzt sie in die verzierte Kartusche, davor ein Leerzeichen. */
const AYAH_TAIL = /[\\u0660-\\u0669\\u06F0-\\u06F9]+$/;
function ayahHTML(text){
  const s = String(text == null ? "" : text);
  const m = s.match(AYAH_TAIL);
  if (!m) return esc(s);
  const stem = s.slice(0, m.index).replace(/[\\s\\u00A0]+$/, "");
  return esc(stem) + ' <span class="ayah">\\u06DD' + esc(m[0]) + '</span>';
}
"""

# (Beschreibung, Suchtext, Ersatz)  – jeder Anker muss genau einmal vorkommen.
EDITS = [
    (
        "Schriftschnitt für das Ornament",
        ":root{\n  --ground:#F4F0EB;",
        FONT_FACE.strip() + "\n\n:root{\n  --ground:#F4F0EB;",
    ),
    (
        "CSS-Klasse .ayah",
        "*{box-sizing:border-box}",
        AYAH_CSS.strip() + "\n\n*{box-sizing:border-box}",
    ),
    (
        "Hilfsfunktion ayahHTML()",
        "function patternHTML(p){",
        AYAH_JS.strip() + "\nfunction patternHTML(p){",
    ),
    (
        "Detailansicht: Wort / Vers",
        'p.innerHTML = x.task_type === "mark_verse" ? markVerse(subj, x.answer) : esc(subj);',
        'p.innerHTML = x.task_type === "mark_verse" ? markVerse(subj, x.answer) : ayahHTML(subj);',
    ),
    (
        "Trefferliste links",
        "    tx.textContent = t || (TASK[x.task_type] || x.task_type);",
        "    if (t) tx.innerHTML = ayahHTML(t);\n"
        "    else tx.textContent = TASK[x.task_type] || x.task_type;",
    ),
    (
        "Antwortmöglichkeiten",
        "    tx.textContent = label || displayGlyph(raw);",
        "    if (label) tx.textContent = label;\n"
        "    else tx.innerHTML = ayahHTML(displayGlyph(raw));",
    ),
    (
        "Zuordnung: linke Seite",
        '    left.textContent = (it && it.text) || "?";',
        '    left.innerHTML = ayahHTML((it && it.text) || "?");',
    ),
    (
        "Zuordnung: rechte Seite",
        '    right.textContent = displayGlyph((op && op.text) || "?");',
        '    right.innerHTML = ayahHTML(displayGlyph((op && op.text) || "?"));',
    ),
]


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    if "ayahHTML(" in src:
        print("Bereits korrigiert – nichts zu tun.")
        return 0

    out = src
    for label, needle, replacement in EDITS:
        n = out.count(needle)
        if n != 1:
            print(f"FEHLER: Anker „{label}“ {n}× gefunden (erwartet: 1×).")
            return 1
        out = out.replace(needle, replacement, 1)
        print(f"  ✓ {label}")

    HTML.write_text(out, encoding="utf-8")

    tails = re.findall(r"[ء-ي][٠-٩]+", src)
    print(f"\nGeschrieben: {HTML}")
    print(f"Betroffene Stellen im Datensatz: {len(tails)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
