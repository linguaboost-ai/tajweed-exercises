#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 11: Nachbesserungen bei den Halt-Zeichen.

  * Markiert wird wieder nur das Wort selbst (فِرْعَوْنَ statt آلَ فِرْعَوْنَ).
    Dass bei einem doppelt vorkommenden Wort die richtige Stelle getroffen
    wird, erledigt jetzt die Anzeige: markVerse() bekommt das Halt-Zeichen der
    Aufgabe und wählt das Vorkommen, hinter dem es steht.
  * Das Muster im Titel nennt jetzt alle Zeichen, die im Vers vorkommen — es
    soll zum Antwortschlüssel passen. Bei Muʿānaqa bleibt es bei ۛ, weil die
    Frage daran hängt.
  * Lektion 39 fasst Mīm und Sakta zusammen: an beiden Stellen wird angehalten,
    beim Mīm mit Atem, bei der Sakta ohne. Die Frage lautet deshalb jetzt
    „An welchen Stellen darf man nicht ohne Anhalten weiterlesen?"
  * 2286 zeigte وَيَبْصُۜطُ — dort ist das kleine Sīn die Lesehilfe ص/س, kein
    Halt. Die fünf echten Sakta-Stellen des Hafs sind schon vergeben (2273,
    2274, 2278, 2283, 2285), deshalb bekommt die Aufgabe einen Vers mit
    Mīm-Zeichen: 3:181.

ACHTUNG: Die Tonaufnahme 2286.wav gehört noch zum alten Vers.

Idempotent.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from quran_text import to_dataset                                 # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "browser/index.html")
CORPUS = Path(os.environ.get("QURAN_JSON", "/tmp/quran/package/dist/quran.json"))

SIGNS = "ۖۗۘۙۚۛۜ"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PLAIN = {2152: ("آلَ فِرْعَوْنَ", "فِرْعَوْنَ"),
         2158: ("يُؤْمِنُ بِهِۦ", "بِهِۦ")}
# Der zu markierende Ausdruck wird aus dem Vers geholt: das Wort vor dem ۘ.
NEW_VERSE = {2286: (3, 181)}

MARKVERSE_OLD = """function markVerse(text, spans){
  /* Die Versnummer am Ende gehört nicht zum markierbaren Text. */
  const parts = ayahSplit(text), ayah = parts[1];
  text = parts[0];
  if (!spans || !spans.length) return esc(text) + ayah;
  const need = new Map();
  spans.forEach(s => need.set(s, (need.get(s) || 0) + 1));
  const ranges = [];
  for (const [needle, times] of need){
    let from = 0;
    for (let i = 0; i < times; i++){
      const at = text.indexOf(needle, from);
      if (at === -1) break;
      ranges.push([at, at + needle.length]);
      from = at + needle.length;
    }
  }"""

MARKVERSE_NEW = """/* Steht hinter dieser Stelle das gesuchte Halt-Zeichen? Andere Halt-Zeichen
   dürfen dazwischenstehen (مَّرْقَدِنَا ۜ ۗ). */
function beforeSign(text, at, sign){
  for (let i = at; i < text.length; i++){
    const c = text[i];
    if (c === sign) return true;
    if (!/\\s/.test(c) && !/[\\u06D6-\\u06DC]/.test(c)) return false;
  }
  return false;
}
function markVerse(text, spans, sign){
  /* Die Versnummer am Ende gehört nicht zum markierbaren Text. */
  const parts = ayahSplit(text), ayah = parts[1];
  text = parts[0];
  if (!spans || !spans.length) return esc(text) + ayah;
  const need = new Map();
  spans.forEach(s => need.set(s, (need.get(s) || 0) + 1));
  const ranges = [];
  for (const [needle, times] of need){
    const alle = [];
    let from = 0, at;
    while ((at = text.indexOf(needle, from)) !== -1){
      alle.push(at);
      from = at + needle.length;
    }
    /* Kommt das Wort mehrfach vor, zählt die Stelle mit dem gesuchten
       Zeichen — sonst würde das erste Vorkommen markiert. */
    let treffer = alle;
    if (sign){
      const passend = alle.filter(a => beforeSign(text, a + needle.length, sign));
      if (passend.length) treffer = passend;
    }
    for (let i = 0; i < times && i < treffer.length; i++)
      ranges.push([treffer[i], treffer[i] + needle.length]);
  }"""

EDITS = [
    ("markVerse() achtet auf das Halt-Zeichen", MARKVERSE_OLD, MARKVERSE_NEW),
    ("Halt-Zeichen an markVerse() übergeben",
     'p.innerHTML = x.task_type === "mark_verse" ? markVerse(subj, x.answer) : ayahHTML(subj);',
     'p.innerHTML = x.task_type === "mark_verse"\n'
     '      ? markVerse(subj, x.answer, /^[\\u06D6-\\u06DC]$/.test(x.pattern || "") ? x.pattern : null)\n'
     '      : ayahHTML(subj);'),
    ("Frage in Lektion 39",
     'case "mark_waqf_mandatory":       return `Markiere jedes Wort vor einem notwendigen Halt ${patternHTML(p)}.`;',
     'case "mark_waqf_mandatory":       return `An welchen Stellen darf man nicht ohne Anhalten weiterlesen? ${patternHTML(p)}`;'),
]


def arabic_number(n):
    return "".join(AR_DIGITS[int(d)] for d in str(n))


def word_before(text, sign):
    """Das Wort, hinter dem das Zeichen steht."""
    at = text.find(sign)
    if at < 0:
        return None
    davor = text[:at].split()
    return davor[-1] if davor else None


def set_pattern(x, pat):
    items = [(k, v) for k, v in x.items() if k != "pattern"]
    x.clear()
    for k, v in items:
        x[k] = v
        if k == "verse" and pat:
            x["pattern"] = pat


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out = src
    for label, needle, rep in EDITS:
        if rep in out:
            continue
        if out.count(needle) != 1:
            raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(needle)}× gefunden.")
        out = out.replace(needle, rep, 1)
        print("  ✓", label)

    q = json.loads(CORPUS.read_text(encoding="utf-8"))
    corp = {(c["id"], v["id"]): v["text"] for c in q for v in c["verses"]}

    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    notes = []
    muster = 0
    for x in data:
        if x["rule"] != "waqf":
            continue
        i = x["id"]
        if i in PLAIN and PLAIN[i][0] in x["answer"]:
            alt, neu = PLAIN[i]
            x["answer"] = [neu if s == alt else s for s in x["answer"]]
            notes.append(f"{i}: Markierung wieder auf „{neu}“")
        if i in NEW_VERSE:
            ref = NEW_VERSE[i]
            text = to_dataset(corp[ref]) + " " + arabic_number(ref[1])
            if x["subject"]["text"] != text:
                span = word_before(text, "ۘ")
                if not span or text.count(span) != 1:
                    raise SystemExit(f"FEHLER: Vers {ref} passt nicht zu {i}.")
                notes.append(f"{i}: Vers getauscht ({x['sura']}:{x['verse']} → {ref[0]}:{ref[1]})")
                x["sura"], x["verse"] = ref
                x["subject"]["text"] = text
                x["answer"] = [span]
                set_pattern(x, "ۘ")
        if (x["question_type"] == "identify_waqf_sign"
                and [o["text"] for o in x["options"]][:2] == ["ج", "صلى"]):
            t = x["subject"]["text"]
            da = []
            for c in t:
                if c in SIGNS and c not in da:
                    da.append(c)
            pat = ":".join(da)
            if pat and pat != x.get("pattern"):
                set_pattern(x, pat)
                muster += 1

    new_blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if new_blob == blob and out == src:
        print("Nichts zu tun – bereits korrigiert.")
        return 0
    HTML.write_text(out.replace(blob, new_blob, 1) if new_blob != blob else out, encoding="utf-8")
    for n in notes:
        print("  ✓", n)
    print(f"\n{muster} Muster im Titel an den Antwortschlüssel angeglichen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
