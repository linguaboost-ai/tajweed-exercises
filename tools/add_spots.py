#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ergänzt jede Aufgabe um „spots": die genauen Stellen im Text, an denen die
Regel greift — damit ein Frontend die richtige Antwort im Wort bzw. im Vers
farbig zeigen kann.

    "spots": [ { "start": 3, "end": 5, "text": "ضِ" } ]

start/end sind Zeichenpositionen in dem Text, an dem „spots" hängt (halboffen,
wie String.slice). Der Datensatz enthält keine Zeichen außerhalb der BMP,
deshalb gilt Zeichen = Codepoint = UTF-16-Einheit, und es ist immer

    text.slice(start, end) === spot.text

„spots" hängt an subject (Stellen im Vorgabetext) und an einzelnen
options/items (Stellen in deren eigenem text) — bei Zuordnungs- und
Wortpaaraufgaben trägt die Option den Treffer, nicht der Vorgabetext.

Hergeleitet wird jede Angabe aus der Regel selbst, nicht aus dem Muster im
Titel (das ist an einigen Stellen ungenau). Anschließend wird sie gegen den
Antwortschlüssel geprüft:

    select_count      Zahl der Stellen == genannte Zahl
    yes_no            Stellen vorhanden <=> „ja"
    select_position   Lage der Stelle im Wort == start/mid/end
    select (Vokal)    Harakat auf den Stellen == Antwort
    mark_verse        markierte Wörter == Antwort

Nur was diese Probe besteht, wird geschrieben. Wo keine Probe möglich ist,
zählt die Regelherleitung. Wo die Probe fehlschlägt, bleibt „spots" weg —
lieber keine Angabe als eine falsche.

Idempotent.  Aufruf:  python3 tools/add_spots.py [index.html] [--dry]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nun_rules as nr                                            # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
DRY = "--dry" in sys.argv
HTML = Path(ARGS[0] if ARGS else "browser/index.html")

HAR = "ًٌٍَُِّْٰٓٔۡ۟۠ـٕٖٜٗ٘ٙٚٛٝٞۢۥۦ"
VOKAL = "ًٌٍَُِْ"
TANWIN = {"ً": "َ", "ٌ": "ُ", "ٍ": "ِ"}
WAQF = "ۖۗۘۙۚۛۜ"
ZIFFER = "٠١٢٣٤٥٦٧٨٩"
QALQ = set("قطبجد")
ISTI = set("خصضغطظق")
RA = "ر"
SUK = "ْ"
SHADDA = "ّ"
FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
DOTTED = "◌"


def ist_marke(c):
    return c in HAR


def marks_end(t, i):
    j = i + 1
    while j < len(t) and ist_marke(t[j]):
        j += 1
    return j


def basis_start(t, i):
    while i > 0 and ist_marke(t[i]):
        i -= 1
    return i


def buchstaben(t):
    return [i for i, c in enumerate(t)
            if not ist_marke(c) and not c.isspace()
            and c not in WAQF and c not in ZIFFER]


def woerter(t):
    """(Wort, Anfangsposition) — Versnummern und Waqf-Zeichen ausgenommen."""
    out = []
    for m in re.finditer(r"\S+", t):
        w = m.group(0)
        if all(ist_marke(c) or c in WAQF or c in ZIFFER for c in w):
            continue
        out.append((w, m.start()))
    return out


# ----------------------------------------------------------------- Qalqala
VERSE_END = re.compile(r"[٠-٩]+\s*$")


def qalqala_spots(t):
    am_ende = bool(VERSE_END.search(t.rstrip()))
    ws = woerter(t)
    out = []
    for wi, (w, off) in enumerate(ws):
        li = buchstaben(w)
        for k in li:
            if w[k] not in QALQ:
                continue
            letzter = k == li[-1] and wi == len(ws) - 1 and am_ende
            if SUK in w[k + 1:marks_end(w, k)] or letzter:
                out.append((off + k, off + marks_end(w, k)))
    return out


# ------------------------------------------------- Idgham / Ichfāʾ / Iqlāb
def nun_spots(t, regel):
    idx = buchstaben(t)
    out = []
    for s in nr.analyze(t):
        if s["regel"] != regel:
            continue
        out.append((idx[s["i"]], marks_end(t, idx[s["j"]])))
    return out


# -------------------------------------------------------------------- Waqf
def waqf_spots(t, pattern):
    erlaubt = {p[0] for p in (pattern or "").split(":") if p and p[0] in WAQF}
    return [(i, i + 1) for i, c in enumerate(t)
            if c in WAQF and (not erlaubt or c in erlaubt)]


# ---------------------------------------------------------------- Tafkhīm
def _ra_dick(t, i):
    """Rā mit Fatḥa/Ḍamma, oder sākin nach Fatḥa/Ḍamma."""
    marken = t[i + 1:marks_end(t, i)]
    if FATHA in marken or DAMMA in marken or "ٰ" in marken:
        return True
    if KASRA in marken:
        return False
    if SUK in marken or not marken:
        j = basis_start(t, i - 1) if i else -1
        while j > 0 and t[j].isspace():
            j -= 1
        if j < 0:
            return True
        vor = t[j + 1:marks_end(t, j)] if not ist_marke(t[j]) else ""
        b = j
        while b > 0 and ist_marke(t[b]):
            b -= 1
        vor = t[b + 1:marks_end(t, b)]
        return KASRA not in vor
    return True


LAM_ALLAH = re.compile("ٱ?للَّه|ٱ?للَّٰه")

# Lektion für Lektion kommt ein Buchstabe dazu; eine Aufgabe fragt nur nach
# dem, was bis dahin unterrichtet wurde.
TAF_LEKTION = {1: "ق", 2: "قط", 3: "قطخ", 4: "قطخغ", 5: "قطخغض",
               6: "قطخغضظ", 7: "قطخغضظص", 8: "قطخغضظصر", 9: "قطخغضظصر"}


def tafkheem_spots(t, ra_modus, mit_lam, erlaubt=None):
    menge = ISTI if erlaubt is None else (ISTI & set(erlaubt))
    out = []
    for i, c in enumerate(t):
        if ist_marke(c):
            continue
        if c in menge:
            out.append((i, marks_end(t, i)))
        elif c == RA and ra_modus != "keine" and (erlaubt is None or RA in erlaubt):
            if ra_modus == "alle" or _ra_dick(t, i):
                out.append((i, marks_end(t, i)))
    if mit_lam:
        for m in LAM_ALLAH.finditer(t):
            # das Lām mit Shadda in „Allāh"; dick nach Fatḥa/Ḍamma
            j = m.group(0).index("ل", 1) if m.group(0).startswith("ٱل") else m.group(0).index("ل")
            p = m.start() + m.group(0).index("لَّ")
            davor = t[:m.start()]
            b = len(davor) - 1
            while b >= 0 and (davor[b].isspace()):
                b -= 1
            marken = ""
            if b >= 0:
                k = b
                while k > 0 and ist_marke(t[k]):
                    k -= 1
                marken = t[k + 1:marks_end(t, k)]
            if KASRA in marken:
                continue
            out.append((p, marks_end(t, p)))
    return out


# ------------------------------------------------------------------- Madd
MADDA = "ٓ"          # Dehnungszeichen über dem Dehnungsbuchstaben
ALIF_MADDA = "آ"     # Alif mit Dehnungszeichen
SILA = "ۥۦ"          # kleines Wāw / Yāʾ der Ṣila


def _mit_vorlaeufer(t, i, e):
    """Die Stelle beginnt beim Buchstaben davor — der trägt den Vokal."""
    j = basis_start(t, i - 1) if i else 0
    while j > 0 and t[j].isspace():
        j -= 1
    if j < i and not t[j].isspace():
        b = j
        while b > 0 and ist_marke(t[b]):
            b -= 1
        return (b, e)
    return (i, e)


HAMZA = "ءأإؤئآٔ"
DOLCH = "ٰ"


TATWEEL = "ـ"
STUMM = "۟"          # kleiner Kreis: der Buchstabe wird nicht gelesen


def _letters(t):
    """(Position, Buchstabe, Marken, Wortnummer) — ohne Waqf und Versnummer.
    Das Tatwīl zählt hier als Träger und damit als eigener Buchstabe, weil das
    Hamza im Uthmani-Satz darauf sitzt (سِيـَٔتْ)."""
    aus = []
    for wi, (w, off) in enumerate(woerter(t)):
        i = 0
        while i < len(w):
            c = w[i]
            if (ist_marke(c) and c != TATWEEL) or c.isspace() \
                    or c in WAQF or c in ZIFFER:
                i += 1
                continue
            j = i + 1
            while j < len(w) and ist_marke(w[j]) and w[j] != TATWEEL:
                j += 1
            aus.append((off + i, c, w[i + 1:j], wi))
            i = j
    return aus


def madd_struct(t, klassen):
    """Dehnungen, die über die zwei Einheiten des Langvokals hinausgehen:
    Dehnungsbuchstabe + Hamza im Wort (muttasil), am Wortende vor Hamza
    (munfasil), vor Shadda/Sukūn (lazim), und das Ha der Ṣila vor Hamza."""
    ls = [e for e in _letters(t) if STUMM not in e[2]]
    aus = []
    for n, (p, c, mk, wi) in enumerate(ls):
        vor = ls[n - 1] if n else None
        nxt = ls[n + 1] if n + 1 < len(ls) else None
        start, ende, ist = p, marks_end(t, p), False
        if DOLCH in mk or MADDA in mk:
            ist = True
            if c in "اويى" and vor and vor[3] == wi:
                start = vor[0]
        elif c == "ا" and not mk and vor and FATHA in vor[2] and vor[3] == wi:
            ist, start = True, vor[0]
        elif c == "و" and (not mk or SUK in mk) and vor and DAMMA in vor[2] and vor[3] == wi:
            ist, start = True, vor[0]
        elif c in "يى" and (not mk or SUK in mk) and vor and KASRA in vor[2] and vor[3] == wi:
            ist, start = True, vor[0]
        elif c == "آ" and vor and vor[3] == wi and (FATHA in vor[2] or not vor[2]):
            ist, start = True, vor[0]
        if ist:
            if nxt and nxt[3] == wi and (nxt[1] in HAMZA or "ٔ" in nxt[2]):
                art = "muttasil"
            elif nxt and nxt[3] == wi and (SHADDA in nxt[2] or SUK in nxt[2]):
                art = "lazim"
            elif nxt and nxt[3] != wi and (nxt[1] in HAMZA or "ٔ" in nxt[2]):
                art = "munfasil"
            else:
                art = "tabii"
            if art in klassen:
                aus.append((start, ende))
            continue
        # Ṣila: das Ha am Wortende mit Ḍamma/Kasra, gefolgt von Hamza
        if c == "ه" and (DAMMA in mk or KASRA in mk or "ۥ" in mk or "ۦ" in mk) \
                and (not nxt or nxt[3] != wi) and vor and vor[3] == wi:
            if "sila" in klassen and nxt and (nxt[1] in HAMZA or HAMZA[-1] in nxt[2]):
                aus.append((p, marks_end(t, p)))
    return aus


def madd_spots(t, klassen):
    out = []
    for i, c in enumerate(t):
        if c == MADDA and "madda" in klassen:
            b = basis_start(t, i)
            out.append((b, marks_end(t, b)))
        elif c == ALIF_MADDA and "madda" in klassen:
            out.append(_mit_vorlaeufer(t, i, marks_end(t, i)))
        elif c in SILA and "sila" in klassen:
            out.append(_mit_vorlaeufer(t, i, marks_end(t, i)))
    return out


# ------------------------------------------------------- Muster im Klartext
def _scan(t, nadeln):
    nadeln = sorted({n for n in nadeln if n}, key=len, reverse=True)
    out, i = [], 0
    while i < len(t):
        for n in nadeln:
            if t.startswith(n, i):
                s = basis_start(t, i) if ist_marke(t[i]) else i
                e = marks_end(t, i + len(n) - 1)
                out.append((s, max(e, i + len(n))))
                i += len(n)
                break
        else:
            i += 1
    return out


def muster_teile(pattern):
    return [p.replace(DOTTED, "") for p in (pattern or "").split(":") if p.replace(DOTTED, "")]


def muster_genau(t, pattern):
    """Jede Nadel muss genau so oft vorkommen, wie das Muster sie nennt."""
    teile = muster_teile(pattern)
    if not teile:
        return None
    treffer = _scan(t, teile)
    if len(treffer) != len(teile):
        return None
    return treffer


def muster_alle(t, pattern):
    teile = muster_teile(pattern)
    if not teile:
        return None
    return _scan(t, teile)


# ------------------------------------------------------------------ Probe
def opt_text(x, oid):
    for o in (x.get("options") or []):
        if o.get("id") == oid:
            return o.get("text")
    return None


def antwort_texte(x):
    a = x.get("answer")
    if a is None:
        return []
    a = a if isinstance(a, list) else [a]
    return [opt_text(x, i) if isinstance(i, int) else i for i in a]


def wort_von(t, pos):
    a = t.rfind(" ", 0, pos) + 1
    b = t.find(" ", pos)
    return t[a:b if b != -1 else len(t)]


def probe(x, t, spots):
    """True/False, oder None wenn sich nichts prüfen lässt."""
    tt, qt = x.get("task_type"), x.get("question_type")
    at = antwort_texte(x)
    if tt == "select_count":
        if len(at) != 1 or not (at[0] or "").isdigit():
            return None
        return len(spots) == int(at[0])
    if tt == "yes_no":
        if at not in (["yes"], ["no"]):
            return None
        return bool(spots) == (at == ["yes"])
    if tt == "select_position":
        if len(at) != 1 or at[0] not in ("start", "mid", "end") or len(spots) != 1:
            return None
        li = buchstaben(t)
        k = li.index(spots[0][0]) if spots[0][0] in li else -1
        if k < 0:
            return False
        lage = "start" if k == 0 else ("end" if k == len(li) - 1 else "mid")
        return lage == at[0]
    if tt == "select" and qt in ("vowel_on_letter", "vowels_on_letter"):
        if at == ["none"]:
            return not spots
        soll = {v for v in at if v}
        ist = set()
        for a, b in spots:
            for c in t[a:b]:
                if c in VOKAL and c != SHADDA:
                    ist.add(c)
        if ist == soll:
            return True
        # Tanwīn zählt als sein Grundvokal, wenn die Optionen ihn nicht
        # eigens anbieten.
        moeglich = {o.get("text") for o in (x.get("options") or [])}
        if not (moeglich & set("ًٌٍ")):
            return {TANWIN.get(c, c) for c in ist} == {TANWIN.get(c, c) for c in soll}
        return False
    if tt == "select" and qt == "which_letter":
        soll = {v for v in at if v}
        ist = {t[a] for a, b in spots}
        return ist == soll or None
    if tt == "mark_verse":
        soll = [v for v in at if v]
        if not soll:
            return not spots
        if sorted({t[a:b] for a, b in spots}) == sorted(set(soll)):
            return True
        ist = []
        for a, b in spots:
            w = wort_von(t, a)
            if w not in ist:
                ist.append(w)
        return set(ist) == set(soll)
    return None


# ------------------------------------------------------------ Herleitungen
def vor_zeichen(t, ab, zeichen):
    """Steht hinter dieser Stelle das gesuchte Halt-Zeichen? Andere
    Halt-Zeichen dürfen dazwischenstehen (مَّرْقَدِنَا ۜ ۗ)."""
    for c in t[ab:]:
        if c == zeichen:
            return True
        if not c.isspace() and c not in "ۖۗۘۙۚۛۜ":
            return False
    return False


def antwort_spots(x, t):
    """mark_verse: der Antwortschlüssel nennt die Stellen wörtlich. Steht ein
    Wort mehrfach im Vers, zählt die Stelle vor dem gesuchten Halt-Zeichen."""
    pat = x.get("pattern") or ""
    zeichen = pat if len(pat) == 1 and pat in WAQF else None
    aus = []
    anzahl = {}
    for s in antwort_texte(x):
        if s:
            anzahl[s] = anzahl.get(s, 0) + 1
    for s, mal in anzahl.items():
        alle, von = [], 0
        while True:
            k = t.find(s, von)
            if k == -1:
                break
            alle.append((k, k + len(s)))
            von = k + len(s)
        if zeichen:
            passend = [(a, b) for a, b in alle if vor_zeichen(t, b, zeichen)]
            if passend:
                alle = passend
        if not alle:
            return None
        aus += alle[:mal]
    return aus


def kandidaten(x, t):
    r = x["rule"]
    if x.get("task_type") == "mark_verse":
        a = antwort_spots(x, t)
        if a is not None:
            return [a]
    lek = TAF_LEKTION.get(x.get("lesson"))
    if r == "qalqala":
        return [qalqala_spots(t)]
    if r in ("idgham", "ikhfa", "iqlab"):
        return [nun_spots(t, r)]
    if r == "waqf":
        return [waqf_spots(t, x.get("pattern"))]
    if r == "tafkheem":
        aus = []
        for erlaubt in (lek, None):
            for lam in (x.get("lesson", 0) >= 9, False, True):
                for modus in ("regel", "alle", "keine"):
                    aus.append(tafkheem_spots(t, modus, lam, erlaubt))
        aus.append(muster_genau(t, x.get("pattern")))
        aus.append(muster_alle(t, x.get("pattern")))
        aus.append([])
        return [a for a in aus if a is not None]
    if r == "madd":
        aus = [muster_genau(t, x.get("pattern")), muster_alle(t, x.get("pattern"))]
        for kl in (("madda", "sila"), ("madda",), ("sila",)):
            aus.append(madd_spots(t, kl))
        lek = x.get("lesson")
        vorzug = {29: ("muttasil",), 30: ("muttasil",),
                  31: ("munfasil",), 32: ("sila",),
                  33: ("lazim",), 34: ("lazim",)}.get(lek, ())
        for kl in (vorzug,
                   ("muttasil", "munfasil"),
                   ("muttasil", "munfasil", "lazim"),
                   ("muttasil", "munfasil", "lazim", "sila"),
                   ("lazim",), ("munfasil",), ("muttasil",), ("sila",)):
            if kl:
                aus.append(madd_struct(t, kl))
        aus.append([])
        return [a for a in aus if a is not None]
    return []


def waehle(x, t):
    """(spots, status) mit status in geprueft / ungeprueft / offen."""
    kand = kandidaten(x, t)
    erste = None
    for sp in kand:
        p = probe(x, t, sp)
        if p is True:
            return sp, "geprueft"
        if p is None and erste is None:
            erste = sp
    if erste is not None:
        return erste, "ungeprueft"
    return [], "offen"


# --------------------------------------------------------------- Schreiben
def als_liste(text, paare):
    paare = sorted(set(tuple(p) for p in paare))
    zus = []
    for a, b in paare:
        if zus and a <= zus[-1][1]:
            zus[-1][1] = max(zus[-1][1], b)
        else:
            zus.append([a, b])
    return [{"start": a, "end": b, "text": text[a:b]} for a, b in zus]


def setze(obj, key_after, spots):
    items = [(k, v) for k, v in obj.items() if k != "spots"]
    obj.clear()
    for k, v in items:
        obj[k] = v
        if k == key_after and spots:
            obj["spots"] = spots


PLATZ = {"yes", "no", "start", "mid", "end", "none", "Keine", "-", "اختر"}


def option_spots(x, o):
    """Stellen in einer Option — bei Zuordnungen im Zusammenspiel mit dem
    Vorgabewort, sonst im Wort selbst."""
    ot = o.get("text") or ""
    if len(ot) < 2 or ot in PLATZ:
        return []
    r = x["rule"]
    st = (x.get("subject") or {}).get("text") or ""
    if r in ("idgham", "ikhfa", "iqlab") and x.get("task_type") in ("match", "matching"):
        if st and st not in PLATZ:
            komb = st + " " + ot
            v = len(st) + 1
            sp = [(a - v, b - v) for a, b in nun_spots(komb, r) if a >= v or b > v]
            sp = [(max(a, 0), b) for a, b in sp if b > 0]
            if sp:
                return sp
        return nun_spots(ot, r)
    if r == "qalqala":
        return qalqala_spots(ot)
    if r in ("idgham", "ikhfa", "iqlab"):
        return nun_spots(ot, r)
    if r == "tafkheem":
        return tafkheem_spots(ot, "regel", True)
    if r == "madd":
        return muster_alle(ot, x.get("pattern")) or []
    return []


def subject_spots(x, o):
    """Beim Vorgabewort einer Zuordnung ist der Auslöser die Stelle."""
    r = x["rule"]
    st = (x.get("subject") or {}).get("text") or ""
    if r not in ("idgham", "ikhfa", "iqlab"):
        return []
    aus = []
    for op in (x.get("options") or []):
        ot = op.get("text") or ""
        if op.get("id") not in (x.get("answer") or []) or ot in PLATZ or len(ot) < 2:
            continue
        komb = st + " " + ot
        for a, b in nun_spots(komb, r):
            if a < len(st):
                aus.append((a, min(b, len(st))))
    return aus


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)

    stat = {"geprueft": 0, "ungeprueft": 0, "offen": 0, "leer": 0}
    offen = []
    teil = 0
    for x in data:
        t = (x.get("subject") or {}).get("text")
        if t:
            if x.get("task_type") in ("match", "matching"):
                sp = als_liste(t, subject_spots(x, None))
                setze(x["subject"], "text", sp)
            else:
                roh, status = waehle(x, t)
                sp = als_liste(t, roh)
                setze(x["subject"], "text", sp)
                if status == "offen":
                    offen.append(x["id"])
                stat[status if sp or status == "offen" else "leer"] += 1
        for o in (x.get("options") or []) + (x.get("items") or []):
            sp = als_liste(o.get("text") or "", option_spots(x, o))
            setze(o, "text", sp)
            teil += bool(sp)

    neu = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    print(f"Vorgabetexte geprüft: {stat['geprueft']} · ungeprüft: "
          f"{stat['ungeprueft']} · bewusst leer: {stat['leer']} · offen: {stat['offen']}")
    print(f"Optionen/Items mit Stellen: {teil}")
    if offen:
        print("offen:", " ".join(str(i) for i in offen[:60]),
              "…" if len(offen) > 60 else "")
    if DRY:
        return 0
    if neu == blob:
        print("Nichts zu tun – „spots“ sind aktuell.")
        return 0
    HTML.write_text(src.replace(blob, neu, 1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
