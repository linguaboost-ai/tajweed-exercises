#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 3: Versnummer am Ende eines vollständigen Verses.

Aufgaben vom Typ „Vers" zeigen den Verstext ohne die Nummer, die im Mushaf am
Versende in der verzierten Kartusche steht. Dieses Skript hängt sie an —
als indische Ziffern hinter einem Leerzeichen. Das Ornament (U+06DD) setzt
die Anzeige zur Laufzeit (siehe ayahHTML(), Korrektur 1); im Datensatz stehen
deshalb nur die Ziffern, so wie es dort schon vorher üblich war (أَحَدٌ ١).

Eine Nummer bekommt nur, wer den *ganzen* Vers zeigt. Grundlage ist ein
Abgleich mit dem Korantext, nicht die Referenz im Datensatz:

  * ganzer Vers        -> Nummer anhängen
  * ganzer Vers, aber der Datensatz weicht orthographisch ab
    (z. B. ٱالسَّمَٰوَٰتِ statt ٱلسَّمَٰوَٰتِ)                -> Nummer anhängen, Abweichung berichten
  * Basmala + ganzer Vers                              -> Nummer anhängen
  * Referenz zeigt auf den falschen Vers               -> Referenz korrigieren, Nummer des
                                                          tatsächlichen Verses anhängen
  * nur ein Ausschnitt des Verses                      -> keine Nummer

Zusätzlich wird markVerse() versnummernfähig gemacht: bei „Vers markieren"
lief der Text bisher an ayahHTML() vorbei, die Nummer bliebe eine nackte Ziffer.

Vergleichstext: quran-json 3.1.2 (Tanzil/Uthmani).
    npm pack quran-json@3.1.2 && tar xzf quran-json-3.1.2.tgz -C /tmp/quran
Pfad über $QURAN_JSON oder Argument 2 änderbar.

Idempotent: ein zweiter Lauf findet nichts mehr zu tun.
"""
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
CORPUS = Path(sys.argv[2] if len(sys.argv) > 2
              else os.environ.get("QURAN_JSON", "/tmp/quran/package/dist/quran.json"))
REPORT = Path("docs/versnummern.md")

AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
TAIL = re.compile(r"[٠-٩۰-۹]+$")
BASMALA = "بسم الله الرحمن الرحيم"

# Für den Textvergleich unerheblich: Vokalzeichen, Waqf-Zeichen, Ziffern,
# Tatweel; dazu Schreibvarianten, die je nach Vorlage anders kodiert sind.
DROP = (set(range(0x0610, 0x061B)) | set(range(0x064B, 0x0660))
        | set(range(0x06D6, 0x06ED + 1)) | set(range(0x0660, 0x066A))
        | {0x0670, 0x0640, 0x0653, 0x0654, 0x0655, 0x0621, 0x06DD, 0x06DE})
MAP = {"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"}


def skel(t):
    t = unicodedata.normalize("NFC", t or "")
    t = "".join(MAP.get(c, c) for c in t if ord(c) not in DROP)
    return re.sub(r"\s+", "", t)


def arabic_number(n):
    return "".join(AR_DIGITS[int(d)] for d in str(n))


def strip_basmala(text):
    """Basmala als Vorspann vor dem ersten Vers einer Sure abtrennen."""
    b = skel(BASMALA)
    if skel(text).startswith(b) and skel(text) != b:
        # im Originaltext dieselbe Stelle suchen: nach dem 4. Wort
        parts = text.split()
        for k in range(1, len(parts)):
            if skel(" ".join(parts[:k])) == b:
                return " ".join(parts[k:]), True
    return text, False


def decide(x, corp, nverses):
    """(art, versnummer, hinweis) für eine Aufgabe mit Sura/Vers-Angabe."""
    text, basmala = strip_basmala(x["subject"]["text"])
    a = skel(text)
    ref = corp.get((x["sura"], x["verse"]))
    note = "Basmala vorangestellt" if basmala else ""
    if ref is None:
        return "unbekannte Referenz", None, f"Sure {x['sura']} hat keinen Vers {x['verse']}"
    b = skel(ref)
    if a == b:
        return "ganzer Vers", x["verse"], note
    if a and a in b:
        return "Ausschnitt", None, f"{len(a)*100//len(b)} % des Verses"
    # gleicher Vers, aber der Datensatz schreibt ihn anders
    if SequenceMatcher(None, a, b).ratio() >= 0.95:
        return "ganzer Vers", x["verse"], (note + "; " if note else "") + "Schreibweise weicht ab: " + deviation(a, b)
    # Referenz zeigt woanders hin: den Vers suchen, der wirklich dasteht
    for v in range(1, nverses[x["sura"]] + 1):
        if skel(corp[(x["sura"], v)]) == a:
            return "falsche Referenz", v, f"Text ist Sure {x['sura']}:{v}, angegeben war {x['sura']}:{x['verse']}"
    return "passt nicht", None, "im Korantext nicht gefunden"


def deviation(a, b):
    out = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b).get_opcodes():
        if tag != "equal":
            out.append(f"„{a[max(0,i1-3):i2+3]}“ statt „{b[max(0,j1-3):j2+3]}“")
    return ", ".join(out[:3])


JS_OLD = """function ayahHTML(text){
  const s = String(text == null ? "" : text);
  const m = s.match(AYAH_TAIL);
  if (!m) return esc(s);
  const stem = s.slice(0, m.index).replace(/[\\s\\u00A0]+$/, "");
  return esc(stem) + ' <span class="ayah">\\u06DD' + esc(m[0]) + '</span>';
}"""

JS_NEW = """function ayahSplit(text){
  const s = String(text == null ? "" : text);
  const m = s.match(AYAH_TAIL);
  if (!m) return [s, ""];
  const stem = s.slice(0, m.index).replace(/[\\s\\u00A0]+$/, "");
  return [stem, ' <span class="ayah">\\u06DD' + esc(m[0]) + '</span>'];
}
function ayahHTML(text){
  const [stem, mark] = ayahSplit(text);
  return esc(stem) + mark;
}"""

MARK_OLD = """function markVerse(text, spans){
  if (!spans || !spans.length) return esc(text);"""

MARK_NEW = """function markVerse(text, spans){
  /* Die Versnummer am Ende gehört nicht zum markierbaren Text. */
  const parts = ayahSplit(text), ayah = parts[1];
  text = parts[0];
  if (!spans || !spans.length) return esc(text) + ayah;"""

MARK_TAIL_OLD = '  return out + esc(text.slice(cur));\n}'
MARK_TAIL_NEW = '  return out + esc(text.slice(cur)) + ayah;\n}'

# Die Kopfzeile „Vers / Wort" zählt Wörter. Die Versnummer ist keins — ohne
# diese Zeile bekämen 118 kurze Verse plötzlich das Vers-Layout.
CAP_OLD = '(subj && subj.trim().split(/\\s+/).length > 3)'
CAP_NEW = '(subj && ayahSplit(subj)[0].trim().split(/\\s+/).length > 3)'


def patch_js(out):
    edits = [("ayahSplit() abtrennen", JS_OLD, JS_NEW),
             ("markVerse(): Versnummer aussparen", MARK_OLD, MARK_NEW),
             ("markVerse(): Versnummer anhängen", MARK_TAIL_OLD, MARK_TAIL_NEW),
             ("Wortzählung ohne Versnummer", CAP_OLD, CAP_NEW)]
    if "ayahSplit(" in out:
        return out, ["Anzeigecode war schon angepasst"]
    notes = []
    for label, old, new in edits:
        if out.count(old) != 1:
            raise SystemExit(f"FEHLER: Anker „{label}“ {out.count(old)}× gefunden (erwartet 1×).")
        out = out.replace(old, new, 1)
        notes.append(label)
    return out, notes


def object_span(src, start):
    depth = 0
    for k in range(start, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return start, k + 1
    raise SystemExit("FEHLER: Objektende nicht gefunden.")


def main() -> int:
    q = json.loads(CORPUS.read_text(encoding="utf-8"))
    corp = {(c["id"], v["id"]): v["text"] for c in q for v in c["verses"]}
    nverses = {c["id"]: c["total_verses"] for c in q}

    src = HTML.read_text(encoding="utf-8")
    out, notes = patch_js(src)
    data = json.loads(re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1))

    rows, skipped, changed = [], [], 0
    for x in data:
        if not x.get("sura"):
            continue
        kind, num, note = decide(x, corp, nverses)
        rows.append((x, kind, num, note))
        if num is None:
            skipped.append((x, kind, note))
            continue
        if TAIL.search(x["subject"]["text"].rstrip()):
            continue                     # trägt die Nummer schon

        old_text = x["subject"]["text"]
        new_text = old_text.rstrip() + " " + arabic_number(num)
        s, e = object_span(out, out.index('{"id":%d,' % x["id"]))
        obj = out[s:e]
        enc_old, enc_new = json.dumps(old_text, ensure_ascii=False), json.dumps(new_text, ensure_ascii=False)
        if obj.count('"text":' + enc_old) != 1:
            raise SystemExit(f"FEHLER: Verstext von {x['id']} nicht eindeutig.")
        obj = obj.replace('"text":' + enc_old, '"text":' + enc_new, 1)
        if num != x["verse"]:
            if obj.count('"verse":%d,' % x["verse"]) != 1:
                raise SystemExit(f"FEHLER: Versangabe von {x['id']} nicht eindeutig.")
            obj = obj.replace('"verse":%d,' % x["verse"], '"verse":%d,' % num, 1)
        out = out[:s] + obj + out[e:]
        changed += 1

    HTML.write_text(out, encoding="utf-8")
    write_report(rows, skipped)

    for n in notes:
        print("  ✓", n)
    print(f"\n{changed} Aufgaben mit Versnummer versehen.")
    kinds = {}
    for _, k, _, _ in rows:
        kinds[k] = kinds.get(k, 0) + 1
    for k, v in sorted(kinds.items(), key=lambda t: -t[1]):
        print(f"  {v:>5}  {k}")
    print(f"Bericht: {REPORT}")
    return 0


def write_report(rows, skipped):
    L = ["# Versnummern am Versende", "",
         "Eine Nummer bekommt nur, wer den ganzen Vers zeigt — hinter einem Leerzeichen,",
         "als indische Ziffern; das Ornament (U+06DD) setzt die Anzeige.", "",
         "| Fall | Aufgaben |", "|---|---|"]
    kinds = {}
    for _, k, _, _ in rows:
        kinds[k] = kinds.get(k, 0) + 1
    for k, v in sorted(kinds.items(), key=lambda t: -t[1]):
        L.append(f"| {k} | {v} |")
    L += ["", "## Ohne Nummer: nur ein Ausschnitt des Verses", "",
          "Ein Ausschnitt endet nicht am Versende — eine Nummer dahinter wäre falsch.", "",
          "| ID | Stelle | Anteil | Text |", "|---|---|---|---|"]
    for x, k, note in skipped:
        if k == "Ausschnitt":
            L.append(f"| {x['id']} | {x['sura']}:{x['verse']} | {note} | {x['subject']['text']} |")
    rest = [t for t in skipped if t[1] != "Ausschnitt"]
    if rest:
        L += ["", "## Ohne Nummer: Text im Korantext nicht wiedergefunden", "",
              "Diese Aufgaben brauchen eine inhaltliche Prüfung — bis dahin bekommen sie",
              "keine Nummer, weil unklar ist, welcher Vers gemeint ist.", "",
              "| ID | Stelle | Text |", "|---|---|---|"]
        for x, k, note in rest:
            L.append(f"| {x['id']} | {x['sura']}:{x['verse']} | {x['subject']['text']} |")
    L += ["", "## Angepasste Schreibweisen und Referenzen", "",
          "| ID | Stelle | Nummer | Anmerkung |", "|---|---|---|---|"]
    for x, k, num, note in rows:
        if num is not None and note:
            L.append(f"| {x['id']} | {x['sura']}:{x['verse']} | {arabic_number(num)} | {note} |")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
