#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt docs/korrekturen.csv: Aufgabe · Feedback Lehrer · Korrektur.

Verglichen wird der hochgeladene Ursprungsstand mit dem heutigen Datensatz.
Aufgeführt sind alle Aufgaben, die der Lehrer angemerkt hat, dazu die übrigen
inhaltlich geänderten — in der Reihenfolge, in der sie auf der Seite stehen
(das ist die Reihenfolge im Datensatz, nicht die der IDs).

Nicht als eigene Zeile geführt sind die Änderungen, die alle Aufgaben einer
Art gleich betreffen: Versnummer am Versende, die Antwortmöglichkeit „kommt
nicht vor“ bzw. „Keine“, und die neue Formulierung der Zuordnungs- und
Madd-Fragen (die Madd-Aufgaben des Lehrers stehen aber einzeln in der Liste).

    python3 tools/make_korrekturtabelle.py
"""
import csv, json, re, sys

def load(p):
    s = open(p, encoding="utf-8").read()
    return json.loads(re.search(r"const DATA = (\[.*?\]);\n", s, re.S).group(1))

A = load(sys.argv[1] if len(sys.argv) > 1 else "/tmp/orig0.html")
B = load("index.html")
POS = {x["id"]: i for i, x in enumerate(B)}
OLD = {x["id"]: x for x in A}; NEW = {x["id"]: x for x in B}

def opt(x, ids):
    if x["options"] and x["task_type"] != "mark_verse":
        return "+".join(o["text"] for o in x["options"] if o["id"] in ids) or "keine"
    return str(len(ids))

VOK = {"َ": "Fatha", "ُ": "Damma", "ِ": "Kasra", "ْ": "Sukun",
       "ً": "Fathatan", "ٌ": "Dammatan", "ٍ": "Kasratan",
       "none": "kommt nicht vor", "Keine": "Keine", "yes": "ja", "no": "nein",
       "start": "Anfang", "mid": "Mitte", "end": "Ende"}
def de(s): return "+".join(VOK.get(t, t) for t in s.split("+"))

# ---- Feedback des Lehrers, gekürzt --------------------------------------
KEIN_Q  = "Kein Qalqala"
ANTW_F  = "Antwort falsch"
NOCH1   = "Noch eine Antwortmöglichkeit"
ALLE    = "Alle Antworten richtig"
FRAGE_F = "Frage falsch"
FB = {}
for i in (587,603,619,634,635,651,667,683,691,699,715,731,739,747,755,779,795,811,819,827,859,875):
    FB[i] = KEIN_Q
for i in (590,592): FB[i] = "2 Qalqala, also 2 Antworten"
for i in (633,640,646,648,831): FB[i] = ANTW_F
for i in (654,734,774,840,856,1185): FB[i] = NOCH1
for i in (894,1321,1570): FB[i] = ALLE
FB[1220] = "Wenn hier 2 Idgham, dann bei 1236 drei — zählen Schamsi-Buchstaben?"
FB[1378] = "Fehlermeldung bei der Frage"
FB[1388] = ANTW_F
for i in (1484,1485,1492,1532,1541,1549,1557,1608,1611,1643): FB[i] = "Kein Ikhfa — Frage falsch?"
for i in (1493,1503,1543,1556,1575,1590,1591,1606,1607,1623,1646,1662): FB[i] = "1× Ikhfa — Frage falsch?"
for i in (1614,1652,1654): FB[i] = "2× Ikhfa — Frage falsch?"
FB[1509] = "Noch ein Idgham: nach Nun sakin folgt Lam"
FB[1519] = "1× Idgham: nach Sakin-Lam folgt Lam"
FB[1533] = "Antwort falsch, 4× (ohne Halt 5×) — Frage falsch?"
for i in (1534,1535): FB[i] = "Frage falsch? Nach Idgham gefragt: 1×"
FB[1540] = "Frage falsch? Nach Idgham gefragt: 4×"
FB[1548] = "Kein Ikhfa — Frage falsch? Nach Idgham: 3×"
FB[1564] = "Idgham kommt 8× vor"
for i in (1565,1588,1589): FB[i] = "Idgham kommt 3× vor"
FB[1580] = "„Fehum“ muss auch markiert werden"
for i in (1619,1624): FB[i] = "Frage könnte anders formuliert werden"
for i in (1676,1685,1699,1700,1716,1717,1732,1733,1734,1735,1748,1749,1750,1751,
          1764,1765,1766,1767,1780,1781,1782,1783): FB[i] = FRAGE_F
MADD = ([1804,1805,1806,1807] + list(range(1820,1824)) + [1868,1869,1870,1871]
        + list(range(1884,1888)) + [1932,1933,1934,1935] + list(range(1948,1952)))
MADD_MEHR = list(range(1824,1840)) + list(range(1888,1902)) + list(range(1952,1968))
for i in MADD: FB[i] = "Frage anders formulieren, hier kommt Madd vor"
for i in MADD_MEHR: FB[i] = "Frage anders formulieren, hier kommt mehrfach Madd vor"
# Lektion 35-40, Halt-Zeichen
FB[2152] = "Erstes Zeichen ist kein freiwilliger Halt; bei „Firʿaun“ darf man anhalten"
FB[2158] = "Die falsche Stelle wurde markiert"
for i in list(range(2161,2177)) + list(range(2203,2209)) + list(range(2234,2238)) \
        + [2239,2240] + list(range(2297,2305)):
    FB[i] = "Noch eine Antwortmöglichkeit"
FB[2161] = "Noch eine Antwortmöglichkeit oder Frage anders formulieren"
FB[2286] = "Schrift muss verbessert werden"
FB[2294] = "Schrift muss verbessert werden (Mīm-Zeichen besser positionieren)"
FB[2300] = "Noch eine Antwortmöglichkeit; Mīm-Zeichen besser positionieren"
for i in range(2321,2331): FB[i] = "Man darf an einer von beiden anhalten — noch eine Antwort oder Frage ändern"
for i in range(2331,2337): FB[i] = "Antwort ist falsch"

# ---- Korrektur ----------------------------------------------------------
def korrektur(i):
    a, b = OLD[i], NEW[i]
    t = []
    if i in (587,603,619,633,634,635,640,651,667,683,691,699,715,731,739,747,755,
             779,795,811,819,827,859,875):
        ant = de(opt(b, b["answer"]))
        return (f"Unverändert – am Versende (Versnummer dahinter) entsteht beim "
                f"Anhalten Qalqala; „{ant}“ bleibt richtig")
    if i in (1185,1321): return "Auf Wunsch unverändert gelassen"
    if i == 1590: return "Auf Wunsch unverändert – gefragt ist Idgham, das kommt hier nicht vor; das Ikhfa in ٱلْمَنصُورُونَ ist nicht gefragt"
    if i == 1591: return "Auf Wunsch unverändert – hier kommt weder Idgham noch Ikhfa vor (نَحْنُ ist Izhar)"
    if a["rule"] != b["rule"]:
        t.append(f"Frage von {a['rule'].capitalize()} auf {b['rule'].capitalize()} umgestellt")
    ta = (a.get("subject") or {}).get("text") or ""; tb = (b.get("subject") or {}).get("text") or ""
    if (a.get("sura"), a.get("verse")) != (b.get("sura"), b.get("verse")):
        if i == 69: t.append("Stellenangabe berichtigt: Sure 72:14 → 72:15")
        else: t.append(f"Vers getauscht ({a['sura']}:{a['verse']} → {b['sura']}:{b['verse']}): "
                       "gleiche Länge, kein Idgham aus späteren Lektionen")
    elif ta != tb and re.sub(r"\s*[٠-٩]+$", "", tb) != ta.rstrip():
        t.append(f"Text: „{ta}“ → „{tb}“")
    ao = [o["text"] for o in (a["options"] or [])]; bo = [o["text"] for o in (b["options"] or [])]
    ca = [x for x in ao if x not in ("none","Keine")]; cb = [x for x in bo if x not in ("none","Keine")]
    if ca != cb and i not in (1619,1624,1378,1377):
        t.append(f"Auswahl {'/'.join(ca)} → {'/'.join(cb)}")
    la, lb = opt(a, a["answer"]), opt(b, b["answer"])
    if la != lb and i not in (1619,1624,1378,1377):
        if b["task_type"] == "mark_verse":
            t.append(f"Markierte Stellen {la} → {lb}")
        else:
            t.append(f"Antwort {de(la)} → {de(lb)}")
    return "; ".join(t)

SPEZIAL = {
 1377: "Statt Ja/Nein stehen jetzt vier Buchstaben zur Wahl (ع غ ح خ); keiner löst ein Ikhfa aus, richtig ist „kommt nicht vor“",
 1378: "Aufgabe neu aufgebaut: vier Einzelwörter — مُنذِرٌ und أَنزَلَ mit Ikhfa, مِنْهُمْ und وَٱنْحَرْ mit Izhar; Frage: „Markiere alle Wörter mit Ikhfa“",
 1619: "Vorgabewort entfällt; يُمْسِكُ steht jetzt als vierte Antwort, „Keine“ als fünfte und richtige",
 1624: "Vorgabewort ist jetzt بَشِيرٌ, erste Antwort أَلَمْ يَأْتِكُم — erst zusammen entsteht das Ikhfa; richtig ist Antwort 1",
 1625: "Frage neu: „Welche der folgenden Wörter bilden mit diesem ein Ikhfa?“; Antwort war bereits richtig",
 1611: "Text zu يَمْشُونَ بِهَآ ergänzt; neue Antwortmöglichkeit „kommt nicht vor“ ist die richtige",
 1643: "Antwort auf „kommt nicht vor“ gesetzt (Izhar, kein Ikhfa)",
 1570: "Antwort ergänzt: alle vier Wörter bilden mit سِحْرٌ ein Idgham",
 1220: "Antwort 2 → 1; das Lam des Artikels (ٱلنَّعِيمِ) zählt nicht als Idgham — 1236 bleibt daher bei 2",
 2152: "Markierung auf آلَ فِرْعَوْنَ gesetzt; das erste فِرْعَوْنَ trägt „Halt verboten“",
 2158: "Markierung auf يُؤْمِنُ بِهِۦ gesetzt; das erste بِهِۦ trägt „besser weiterlesen“",
 2286: "Unverändert — das kleine Sīn in وَيَبْصُۜطُ ist kein Halt-Zeichen, sondern die Lesehilfe ص/س; braucht deine Entscheidung",
 2294: "Antwortschlüssel war schon vollständig; die Schriftdarstellung ist nicht geändert",
}
def waqf_text(i):
    a, b = OLD[i], NEW[i]
    if NEW[i].get("pattern") == "ۛ":
        return ("Beide Wörter sind richtig; die Frage sagt jetzt, dass nur an einer "
                "der beiden Stellen angehalten wird")
    neu = [o["text"] for o in b["options"] if o["id"] in b["answer"]]
    return "Antwort um alle im Vers vorkommenden Zeichen ergänzt: " + " + ".join(neu)
def madd_text(i):
    q = NEW[i]["question_type"]
    frage = ("Enthält dieses Wort eine Dehnung, die länger als zwei Einheiten ist?"
             if q == "has_rule" else
             "Wie oft kommt eine Dehnung vor, die länger als zwei Einheiten ist?"
             if q == "count_rule" else
             "Markiere jede Stelle im Vers, an der länger als zwei Einheiten gedehnt wird.")
    return f"Frage neu: „{frage}“; Antwort unverändert"

# ---- Zeilen ------------------------------------------------------------
teacher = sorted(FB)
changed = set()
for i in POS:
    a, b = OLD[i], NEW[i]
    ta = (a.get("subject") or {}).get("text") or ""; tb = (b.get("subject") or {}).get("text") or ""
    ao = [o["text"] for o in (a["options"] or []) if o["text"] not in ("none","Keine")]
    bo = [o["text"] for o in (b["options"] or []) if o["text"] not in ("none","Keine")]
    la, lb = opt(a, a["answer"]), opt(b, b["answer"])
    if la in ("Keine",) and lb == "none": continue          # nur andere Beschriftung
    if (a["rule"] != b["rule"] or ao != bo or la != lb
            or (a.get("sura"), a.get("verse")) != (b.get("sura"), b.get("verse"))
            or (ta != tb and re.sub(r"\s*[٠-٩]+$", "", tb) != ta.rstrip())):
        changed.add(i)
changed.add(1625)                                           # nur Fragetext
ids = sorted(set(teacher) | changed, key=lambda i: POS[i])

rows, prev = [], None
for i in ids:
    fb = FB.get(i, "")
    if i in SPEZIAL: k = SPEZIAL[i]
    elif NEW[i]["rule"] == "waqf" and NEW[i]["question_type"] == "identify_waqf_sign": k = waqf_text(i)
    elif NEW[i]["rule"] == "madd": k = madd_text(i)
    else: k = korrektur(i)
    show = "s. o." if fb and fb == prev else fb
    prev = fb
    rows.append((i, show, k))

with open("docs/korrekturen.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Aufgabe ID", "Feedback Lehrer", "Korrektur"])
    w.writerows(rows)
print(f"{len(rows)} Zeilen · davon {sum(1 for r in rows if not r[1])} ohne Lehrer-Feedback")
