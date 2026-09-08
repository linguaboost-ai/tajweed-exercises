#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schreibt alle Aufgaben als JSON in sieben Dateien, eine je Lektionsblock, und
prüft sie vorher gegen den Tajweed Exercise Authoring Guide.

    json/tafkheem.json      Lektion  1– 9
    json/qalqala.json       Lektion 10–14
    json/idgham.json        Lektion 15–21
    json/ikhfa-idgham.json  Lektion 22–26
    json/iqlab.json         Lektion 27–28
    json/madd.json          Lektion 29–34
    json/waqf.json          Lektion 35–40

Jede Datei ist ein Array von Aufgabenobjekten in der Feldreihenfolge des
Guides. Das interne Feld „src" fällt weg. Hinzu kommt „spots" — die
Zeichenspannen, an denen die Regel greift (siehe docs/spots.md).

Aufruf:  python3 tools/export_json.py [index.html] [--out json]
"""
import json
import re
import sys
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
HTML = Path(ARGS[0] if ARGS else "index.html")
OUT = Path(ARGS[1] if len(ARGS) > 1 else "json")

BLOECKE = [("tafkheem", 1, 9), ("qalqala", 10, 14), ("idgham", 15, 21),
           ("ikhfa-idgham", 22, 26), ("iqlab", 27, 28), ("madd", 29, 34),
           ("waqf", 35, 40)]

RULES = {"tafkheem", "qalqala", "idgham", "ikhfa", "iqlab", "madd", "waqf"}
TASKS = {"yes_no", "select_count", "select_position", "select", "match",
         "mark_verse", "matching"}
MODAL = {"audio", "text"}
# question_type -> erlaubte task_types (Katalog des Guides)
KATALOG = {
    "has_rule": {"yes_no"},
    "count_rule": {"select_count"},
    "position_in_word": {"select_position"},
    "vowel_on_letter": {"select"},
    "vowel_before_letter": {"select"},
    "vowels_on_letter": {"select"},
    "vowels_before_letter": {"select"},
    "which_letter": {"select"},
    "match_rule": {"match"},
    "match_pattern": {"matching"},
    "mark_rule_in_verse": {"mark_verse"},
    "identify_waqf_sign": {"select"},
    "mark_waqf_forbidden": {"mark_verse"},
    "mark_waqf_mandatory": {"mark_verse"},
    "mark_waqf_better_continue": {"mark_verse"},
    "mark_waqf_better_pause": {"mark_verse"},
    "mark_waqf_optional": {"mark_verse"},
}
MARKEN = {"yes", "no", "start", "mid", "end", "none", "-"}
LATEIN = re.compile(r"[A-Za-zÄÖÜäöüß]")
REIHE = ["id", "rule", "lesson", "task_type", "question_type", "multiple",
         "modality", "sura", "verse", "subject", "items", "options",
         "answer", "pattern"]


def ordne(x):
    aus = {}
    for k in REIHE:
        if k in x:
            aus[k] = x[k]
    for k in x:
        if k not in aus and k != "src":
            aus[k] = x[k]
    return aus


def pruefe(data):
    fehler = []

    def f(x, text):
        fehler.append(f"{x['id']}: {text}")

    gesehen = {}
    for x in data:
        gesehen[x["id"]] = gesehen.get(x["id"], 0) + 1
    for i, n in gesehen.items():
        if n > 1:
            fehler.append(f"{i}: ID kommt {n}× vor")

    for x in data:
        tt, qt = x.get("task_type"), x.get("question_type")
        if x.get("rule") not in RULES:
            f(x, f"unbekannte rule {x.get('rule')!r}")
        if tt not in TASKS:
            f(x, f"unbekannter task_type {tt!r}")
        if x.get("modality") not in MODAL:
            f(x, f"unbekannte modality {x.get('modality')!r}")
        if qt not in KATALOG:
            f(x, f"unbekannter question_type {qt!r}")
        elif tt not in KATALOG[qt]:
            f(x, f"{qt} passt nicht zu {tt}")
        if not isinstance(x.get("lesson"), int):
            f(x, "lesson fehlt")

        opts = x.get("options")
        if opts is None:
            f(x, "options fehlt")
            opts = []
        ids = [o.get("id") for o in opts]
        if len(set(ids)) != len(ids) or any(not isinstance(i, int) for i in ids):
            f(x, "Options-IDs nicht eindeutig oder keine Zahlen")
        for o in opts + (x.get("items") or []):
            t = o.get("text")
            if t is None:
                f(x, "Option ohne text")
            elif LATEIN.search(t) and t not in MARKEN and not t.isdigit():
                f(x, f"lateinischer Text in einer Option: {t!r}")

        subj = x.get("subject")
        if tt == "matching":
            if subj is not None:
                f(x, "matching braucht subject null")
            if not x.get("items"):
                f(x, "matching ohne items")
        else:
            if not (subj and subj.get("text")):
                f(x, "subject fehlt")
            if "items" in x:
                f(x, "items nur bei matching")
        if tt == "mark_verse" and opts:
            f(x, "mark_verse braucht options []")
        if tt == "select" and not isinstance(x.get("multiple"), bool):
            f(x, "select ohne multiple")
        if tt != "select" and "multiple" in x:
            f(x, "multiple nur bei select")

        a = x.get("answer")
        if a is None:
            f(x, "answer fehlt")
            continue
        if tt == "mark_verse":
            for s in a:
                if not isinstance(s, str) or s not in (subj or {}).get("text", ""):
                    f(x, f"Antwort steht nicht im Vers: {s!r}")
        elif tt == "matching":
            it_ids = {i["id"] for i in x.get("items") or []}
            paare = {p.get("item") for p in a}
            if paare != it_ids:
                f(x, "matching: nicht jedes Item hat ein Paar")
            for p in a:
                if p.get("option") not in set(ids):
                    f(x, f"matching: Option {p.get('option')} gibt es nicht")
        else:
            for i in a:
                if i not in ids:
                    f(x, f"Antwort verweist auf Option {i}, die es nicht gibt")
            if tt in ("yes_no", "select_count", "select_position") and len(a) != 1:
                f(x, f"{tt} braucht genau eine Antwort, hat {len(a)}")
            if tt == "select" and x.get("multiple") is False and len(a) != 1:
                f(x, f"select multiple:false braucht genau eine Antwort, hat {len(a)}")

        # Audio-Namen
        for wo, o in [("subject", subj)] + [("option", o) for o in opts] \
                + [("item", o) for o in x.get("items") or []]:
            if not o:
                continue
            au = o.get("audio")
            if au is None:
                continue
            if not re.fullmatch(rf"{x['id']}(_\d+|_prompt)?\.wav", au):
                f(x, f"Audioname passt nicht zur ID: {au}")

        # Stellen
        for o in [subj] + opts + (x.get("items") or []):
            if not o or not o.get("spots"):
                continue
            for sp in o["spots"]:
                if o["text"][sp["start"]:sp["end"]] != sp["text"]:
                    f(x, "spot passt nicht zum Text")
                    break
    return fehler


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1))

    fehler = pruefe(data)
    if fehler:
        print(f"{len(fehler)} Beanstandungen:")
        for z in fehler[:60]:
            print("  " + z)
        if len(fehler) > 60:
            print(f"  … und {len(fehler) - 60} weitere")
        return 1

    OUT.mkdir(exist_ok=True)
    rest = {x["id"] for x in data}
    for name, a, b in BLOECKE:
        teil = [ordne(x) for x in data if a <= x["lesson"] <= b]
        rest -= {x["id"] for x in teil}
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(teil, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
        kb = p.stat().st_size / 1024
        print(f"{p}  {len(teil):4d} Aufgaben  {kb:7.1f} kB  Lektion {a}–{b}")
    if rest:
        print("nicht zugeordnet:", sorted(rest))
        return 1
    print("Alle Aufgaben zugeordnet, keine Beanstandungen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
