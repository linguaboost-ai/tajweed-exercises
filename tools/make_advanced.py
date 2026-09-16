#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Die Lektionen für Fortgeschrittene.

Wer den Stoff schon kennt, braucht die Buchstaben nicht einzeln durchzugehen.
Dafür werden Lektionen zusammengefasst — aus denselben Aufgaben, mit denselben
IDs, nur anders gebündelt:

    tafkheem-1-advanced   Lektion 1–7 in einer (alle Tafkheem-Buchstaben)
    qalqala-1-advanced    Lektion 10–14, die Qalqalah im Wort
    qalqala-2-advanced    Lektion 10–14, die Qalqalah am Versende — also nur
                          die Aufgaben, bei denen der letzte Buchstabe vor der
                          Versnummer beim Anhalten sein Sukūn bekommt

Ausgewogen heißt dabei: ungefähr gleich viele Aufgaben je Herkunftslektion,
die Aufgabentypen im Verhältnis des Vorrats, und die Antworten flacher
verteilt als im Vorrat — sonst wäre bei den Zählaufgaben fast jede zweite
Antwort „0" und Raten würde sich lohnen. Gedämpft wird über die Wurzel des
Anteils: nicht ganz flach, nicht so schief wie der Vorrat.

Ergebnis ist advanced.json — die Seite liest daraus, welche Aufgaben zu
welcher Lektion gehören; tools/export_json.py schreibt die drei Dateien.

Aufruf:  python3 tools/make_advanced.py
"""
import collections
import glob
import json
import math
import re
from pathlib import Path

ZIEL = Path("advanced.json")
VERSNUMMER = re.compile(r"[٠-٩]+\s*$")

# Die Auswahl für Tafkheem ist durchgesehen und abgenommen; sie wird nicht
# neu gewürfelt, sondern steht hier fest. 379 (مَظِفَ) ist gegen 355 (عِظَامَ)
# getauscht — ein Übungswort ohne koranischen Beleg gehört nicht in eine
# Lektion für Fortgeschrittene.
TAFKHEEM = [
    45, 53, 61, 9, 12, 11, 18, 32, 42,
    77, 93, 65, 73, 68, 75, 106, 74, 122,
    173, 183, 137, 140, 139, 155, 130, 168, 176,
    207, 229, 225, 196, 204, 219, 210, 200, 224, 248,
    279, 301, 257, 260, 275, 266, 278, 290, 302,
    325, 343, 321, 324, 355, 322, 328, 352, 384,
    389, 391, 447, 393, 396, 411, 434, 418, 440,
]


def alle_aufgaben():
    aus = {}
    for f in sorted(glob.glob("json/*.json")):
        if "-advanced" in f:
            continue
        for x in json.load(open(f, encoding="utf-8")):
            aus[x["id"]] = x
    return aus


def antwort(x):
    m = {o["id"]: o["text"] for o in x["options"]}
    return [m.get(i) if isinstance(i, int) else i for i in x["answer"]]


def klasse(x):
    """Wonach innerhalb eines Fragetyps ausgewogen wird."""
    q = x["question_id"]
    if q == "match_pattern":
        m = {o["id"]: o["text"] for o in x["options"]}
        return "ohne Muster" if any(m[p["option"]] == "-" for p in x["answer"]) else "alle zugeordnet"
    a = antwort(x)
    if q in ("vowels_on_letter", "vowels_before_letter"):
        return "keine" if a == ["none"] else f"{len(a)} Vokale"
    return a[0] if a else "—"


def am_versende(x):
    """Steht eine Fundstelle auf dem letzten Buchstaben vor der Versnummer?"""
    s = x.get("subject") or {}
    t = s.get("text") or ""
    if not VERSNUMMER.search(t.rstrip()):
        return False
    stamm = VERSNUMMER.sub("", t).rstrip()
    return any(sp["end"] >= len(stamm) for sp in (s.get("spots") or []))


def mit_versnummer(x):
    return bool(VERSNUMMER.search(((x.get("subject") or {}).get("text") or "").rstrip()))


def verteile(n, gewichte):
    """n Plätze nach Gewichten, größte Reste zuerst, gedeckelt durch den Vorrat."""
    summe = sum(gewichte.values())
    if not summe:
        return {}
    roh = {k: n * g / summe for k, g in gewichte.items()}
    aus = {k: int(v) for k, v in roh.items()}
    rest = n - sum(aus.values())
    for k in sorted(roh, key=lambda k: -(roh[k] - aus[k]))[:rest]:
        aus[k] += 1
    return aus


def gedaempft(vorrat):
    """Wurzel des Anteils: flacher als der Vorrat, aber nicht gleichmacherisch."""
    return {k: math.sqrt(v) for k, v in vorrat.items()}


def waehle(pool, n, lektionen, bevorzugt=None, ohne=(), mindestens=5):
    """n Aufgaben aus pool, ausgewogen über Lektionen, Typen und Antworten.
    Fragetypen mit weniger als „mindestens" Aufgaben im Vorrat bleiben weg —
    ein Typ, den nur ein oder zwei Aufgaben vertreten, ist keine Gattung."""
    vorrat = collections.Counter(x["question_id"] for x in pool)
    pool = [x for x in pool if x["question_id"] not in ohne
            and vorrat[x["question_id"]] >= mindestens]
    typ_quote = verteile(n, collections.Counter(x["question_id"] for x in pool))
    gewaehlt, genommen, belegt = [], set(), set()
    versatz = 0
    for q in sorted(typ_quote, key=lambda q: -typ_quote[q]):
        anzahl = typ_quote[q]
        if not anzahl:
            continue
        teil = [x for x in pool if x["question_id"] == q]
        ziel = verteile(anzahl, gedaempft(collections.Counter(klasse(x) for x in teil)))
        offen = dict(zip(lektionen, lektions_quote(anzahl, len(lektionen), versatz)))
        versatz = (versatz + anzahl) % len(lektionen)
        haben = collections.Counter()
        for _ in range(anzahl):
            frei = [x for x in teil if x["id"] not in genommen
                    and offen.get(x["lesson"], 0) > 0
                    and kern(x) not in belegt]
            if not frei:
                frei = [x for x in teil if x["id"] not in genommen
                        and offen.get(x["lesson"], 0) > 0]
            if not frei:
                break

            def rang(x):
                fehlt = ziel.get(klasse(x), 0) - haben[klasse(x)]
                # Wo es um das Versende geht, zählt das Thema vor der
                # Antwortverteilung — sonst landen Verse in der Lektion, in
                # denen die Qalqalah am Ende gar nicht vorkommt.
                thema = 0 if (bevorzugt is None or bevorzugt(x)) else 1
                return (thema, -fehlt, -offen[x["lesson"]], len(kern(x)), x["id"])

            x = min(frei, key=rang)
            gewaehlt.append(x)
            genommen.add(x["id"])
            haben[klasse(x)] += 1
            offen[x["lesson"]] -= 1
            belegt.add(kern(x))

    # Bleibt ein Platz offen, weil eine Lektion nichts mehr hergab, wird er
    # aus dem übrigen Vorrat aufgefüllt — lieber 64 als eine krumme Zahl.
    while len(gewaehlt) < n:
        frei = [x for x in pool if x["id"] not in genommen and kern(x) not in belegt]
        if not frei:
            break
        haben_lektion = collections.Counter(x["lesson"] for x in gewaehlt)
        haben_typ = collections.Counter(x["question_id"] for x in gewaehlt)
        x = min(frei, key=lambda x: (haben_lektion[x["lesson"]],
                                     haben_typ[x["question_id"]] - typ_quote.get(x["question_id"], 0),
                                     x["id"]))
        gewaehlt.append(x)
        genommen.add(x["id"])
        belegt.add(kern(x))
    return gewaehlt


def lektions_quote(n, anzahl_lektionen, versatz):
    aus = [n // anzahl_lektionen] * anzahl_lektionen
    for k in range(n % anzahl_lektionen):
        aus[(versatz + k) % anzahl_lektionen] += 1
    return aus


def kern(x):
    """Vorgabetext ohne Waqf-Zeichen und Versnummer — damit derselbe Vers in
    zwei Zuschnitten als Dublette auffällt."""
    t = ((x.get("subject") or {}).get("text") or "")
    if not t:
        return f"#{x['id']}"
    t = re.sub(r"[ۖ-ۜ٠-٩\s]+", " ", t).strip()
    return re.sub(r"^وَ", "", t)


def bericht(name, gewaehlt):
    print(f"\n{name} — {len(gewaehlt)} Aufgaben")
    print("  Lektion  ", dict(sorted(collections.Counter(x["lesson"] for x in gewaehlt).items())))
    print("  Typ      ", dict(collections.Counter(x["question_id"] for x in gewaehlt)))
    print("  Wort/Vers", dict(collections.Counter("Vers" if x["sura"] else "Wort" for x in gewaehlt)))
    for q in sorted({x["question_id"] for x in gewaehlt}):
        t = [x for x in gewaehlt if x["question_id"] == q]
        print(f"    {q:22s}", dict(collections.Counter(klasse(x) for x in t)))


def main() -> int:
    alle = alle_aufgaben()

    fehlt = [i for i in TAFKHEEM if i not in alle]
    if fehlt or len(TAFKHEEM) != len(set(TAFKHEEM)):
        raise SystemExit(f"Tafkheem-Auswahl stimmt nicht: {fehlt or 'doppelte IDs'}")
    tafkheem = [alle[i] for i in TAFKHEEM]
    if any(not 1 <= x["lesson"] <= 7 for x in tafkheem):
        raise SystemExit("Tafkheem-Auswahl enthält Aufgaben außerhalb der Lektionen 1–7")

    # Lektion 2 sind die Aufgaben, in denen die Qalqalah am Versende steht —
    # nicht die, in denen irgendwo im Vers eine vorkommt. Alles andere gehört
    # in Lektion 1, auch Verse ohne Fundstelle am Ende.
    #
    # „An welcher Stelle im Wort?" fällt in beiden weg: durch die Aufteilung
    # steht die Antwort schon vorher fest — im Wort liegt die Qalqalah immer
    # in der Mitte (am Wortanfang gibt es kein Sukūn), am Versende immer am
    # Ende. Alle 40 Aufgaben dieses Typs bestätigen das ausnahmslos.
    ohne = ("position_in_word",)
    qalqala = [x for x in alle.values() if 10 <= x["lesson"] <= 14
               and x["question_id"] not in ohne]
    am_ende = [x for x in qalqala if am_versende(x)]
    im_wort = [x for x in qalqala if not am_versende(x)]
    q1 = waehle(im_wort, 64, range(10, 15))
    # Am Versende gibt der Vorrat nur diese Aufgaben her — hier ist nichts
    # auszuwählen, es sind alle.
    q2 = sorted(am_ende, key=lambda x: (x["lesson"], x["question_id"], x["id"]))

    lektionen = [
        {"id": "tafkheem-1-advanced", "group": "tafkheem", "block": "tafkheem",
         "replaces": list(range(1, 8)),
         "de": "Tafkheem — alle Buchstaben", "en": "Tafkheem — all letters",
         "tasks": [x["id"] for x in tafkheem]},
        {"id": "qalqala-1-advanced", "group": "qalqala", "block": "qalqala",
         "replaces": list(range(10, 15)),
         "de": "Qalqalah im Wort", "en": "Qalqalah within the word",
         "tasks": sorted(x["id"] for x in q1)},
        {"id": "qalqala-2-advanced", "group": "qalqala", "block": "qalqala",
         "replaces": list(range(10, 15)),
         "de": "Qalqalah am Versende", "en": "Qalqalah at the end of the verse",
         "tasks": sorted(x["id"] for x in q2)},
    ]
    ZIEL.write_text(json.dumps({
        "note": ("Zusammengefasste Lektionen für Fortgeschrittene. Sie enthalten "
                 "keine eigenen Aufgaben, sondern verweisen auf vorhandene — "
                 "dieselben IDs, dieselben Tonaufnahmen. „replaces\" nennt die "
                 "Lektionen, die sie ersetzen."),
        "lessons": lektionen,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bericht("Tafkheem 1 (Lektion 1–7)", tafkheem)
    bericht("Qalqalah 1 (im Wort)", q1)
    bericht("Qalqalah 2 (am Versende)", q2)
    print(f"\n  Vorrat an Versende-Aufgaben insgesamt: "
          f"{sum(1 for x in alle.values() if 10 <= x['lesson'] <= 14 and am_versende(x))}, "
          f"davon brauchbar {len(am_ende)}")
    print(f"\n{ZIEL} geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
