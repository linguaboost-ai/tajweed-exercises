#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrektur 5: falsch beschriftete Regel (und daraus folgend falsche Antworten)
bei den Aufgaben zu Idgham, Ikhfāʾ und Iqlāb.

Die Frage im Titel entsteht aus dem Feld "rule". Bei einer Reihe von Aufgaben
steht dort "ikhfa", obwohl die Fundstellen im Text ein Idgham (Lektion 24/25:
م مّ, ن مّ, ٌ مّ …) oder ein Iqlāb (Lektion 27/28: ن ب) sind. Gefragt wurde
also nach der falschen Regel. In Lektion 26 stimmt die Beschriftung, dort
zählte der Datensatz aber nur das Ikhfāʾ nach Mīm sākin und ließ das Ikhfāʾ
nach Nūn sākin aus.

Grundlage der Auswertung ist tools/nun_rules.py in der vereinfachten Benennung
des Lehrplans (keine Unterarten von Idgham).

Geändert werden nur die vom Kursautor gemeldeten Aufgaben. Idempotent.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nun_rules as nr                                            # noqa: E402

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
REPORT = Path("docs/idgham-ikhfa-iqlab.md")

def relabel_for(x):
    """Richtige Regel für eine falsch beschriftete Aufgabe.

    Lektion 24/25 üben das Idgham nach Mīm sākin und Tanwīn (م مّ, ن مّ, ٌ مّ),
    Lektion 27/28 das Iqlāb (ن ب). Wo dort "ikhfa" steht, ist die Frage falsch.
    Dazu die eine Aufgabe 1608 (ٱرْكَب مَّعَنَا) — bāʾ sākin vor Mīm ist Idgham.
    """
    if x["rule"] != "ikhfa":
        return None
    if x["id"] == 1608:
        return "idgham"
    if x["lesson"] in (24, 25):
        return "idgham"
    if x["lesson"] in (27, 28):
        return "iqlab"
    return None


# Vom Kursautor gemeldet: Lektion 26 zählte nur das Ikhfāʾ nach Mīm sākin,
# das nach Nūn sākin fiel weg. Dazu die Markieraufgaben in Lektion 24/25,
# in denen Fundstellen fehlten.
RECOUNT_EXTRA = {1606, 1607, 1614, 1623, 1646, 1652, 1654, 1662,
                 1509, 1519, 1564, 1565, 1580, 1588, 1589}
# Nicht gemeldet, beim Gegenlesen gefunden: dieselben Lücken in Lektion 22/23
# (Ikhfāʾ im Zählschlüssel) und 24 (Idgham nach Tanwīn beim Markieren).
RECOUNT_FOUND = {1388, 1420, 1422, 1445, 1501, 1524}

# Zuordnungsaufgabe: alle vier Optionen ergeben mit سِحْرٌ ein Idgham,
# im Schlüssel stand Option 1 doppelt statt Option 4.
FIX_ANSWER = {1570: [1, 2, 3, 4]}


def set_pattern(x, pat):
    """Muster setzen und dabei an seiner angestammten Stelle halten (hinter
    "verse"), damit der Datensatz einheitlich bleibt."""
    items = [(k, v) for k, v in x.items() if k != "pattern"]
    if pat is None:
        rebuilt = items
    else:
        rebuilt = []
        for k, v in items:
            rebuilt.append((k, v))
            if k == "verse":
                rebuilt.append(("pattern", pat))
        if not any(k == "pattern" for k, _ in rebuilt):
            rebuilt.insert(len(rebuilt) - 1, ("pattern", pat))
    x.clear()
    x.update(rebuilt)


def new_answer(x, rule):
    t = (x.get("subject") or {}).get("text") or ""
    if x["question_type"] == "count_rule":
        want = str(nr.count(t, rule))
        return [o["id"] for o in x["options"] if o["text"] == want], want
    if x["question_type"] == "has_rule":
        want = "yes" if nr.count(t, rule) else "no"
        return [o["id"] for o in x["options"] if o["text"] == want], want
    if x["question_type"] == "mark_rule_in_verse":
        sp = nr.spans(t, rule)
        return sp, f"{len(sp)} Stellen"
    return None, None


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    blob = re.search(r"const DATA = (\[.*?\]);\n", src, re.S).group(1)
    data = json.loads(blob)
    by_id = {x["id"]: x for x in data}

    relabel = {x["id"]: r for x in data if (r := relabel_for(x))}
    todo = sorted(set(relabel) | RECOUNT_EXTRA | RECOUNT_FOUND | set(FIX_ANSWER))

    out, changes = src, []
    for i in todo:
        x = by_id[i]
        before = json.dumps(x, ensure_ascii=False, separators=(",", ":"))
        note = []

        rule = relabel.get(i, x["rule"])
        if rule != x["rule"]:
            note.append(f"Frage: {nr.NAME[x['rule']]} → {nr.NAME[rule]}")
            x["rule"] = rule

        if i in FIX_ANSWER:
            if x["answer"] != FIX_ANSWER[i]:
                note.append("Antwortschlüssel vervollständigt")
                x["answer"] = FIX_ANSWER[i]
        else:
            was = fmt(x, x["answer"])          # vor jeder Änderung festhalten
            ans, shown = new_answer(x, rule)
            if ans is None:
                pass
            else:
                if not ans and x["question_type"] == "count_rule":
                    # Der richtige Wert steht nicht zur Auswahl
                    want = str(nr.count((x["subject"] or {}).get("text", ""), rule))
                    lo = max(0, int(want) - 3)
                    x["options"] = [{"id": k + 1, "text": str(lo + k)} for k in range(4)]
                    ans = [o["id"] for o in x["options"] if o["text"] == want]
                    note.append(f"Auswahl auf {lo}–{lo+3} verschoben, {want} war nicht wählbar")
                if ans != x["answer"] or shown != was:
                    note.append(f"Antwort: {was} → {shown}")
                    x["answer"] = ans

        # Das Muster im Titel nennt die Fundstellen — nach einer Änderung der
        # Antwort muss es mitwandern (bei Zuordnungsaufgaben beschreibt es die
        # Optionen, nicht den Vorgabetext, und bleibt deshalb unberührt).
        t = (x.get("subject") or {}).get("text")
        if note and t and x["task_type"] not in ("match", "matching"):
            pat = nr.pattern(t, rule)
            if pat != x.get("pattern") and any(n.startswith(("Antwort", "Auswahl")) for n in note):
                note.append(f"Muster: {x.get('pattern') or '—'} → {pat or '—'}")
                set_pattern(x, pat)

        after = json.dumps(x, ensure_ascii=False, separators=(",", ":"))
        if before == after:
            continue
        if out.count(before) != 1:
            raise SystemExit(f"FEHLER: Aufgabe {i} nicht eindeutig im Quelltext.")
        out = out.replace(before, after, 1)
        changes.append((x, note))

    if not changes:
        print("Nichts zu tun – alle gemeldeten Aufgaben sind bereits korrigiert.")
        return 0

    HTML.write_text(out, encoding="utf-8")
    write_report(changes)
    for x, note in changes:
        print(f"  {x['id']:>5} L{x['lesson']:<3} {' · '.join(note)}")
    print(f"\n{len(changes)} Aufgaben geändert · Bericht: {REPORT}")
    return 0


def fmt(x, answer):
    if x["question_type"] == "mark_rule_in_verse":
        return f"{len(answer)} Stellen"
    return "+".join(o["text"] for o in x["options"] if o["id"] in answer) or "—"


def write_report(changes):
    L = ["# Idgham, Ikhfāʾ und Iqlāb: falsch beschriftete Regel", "",
         "Die Frage im Aufgabentitel entsteht aus dem Feld `rule`. Wo dort die",
         "falsche Regel stand, wurde nach etwas anderem gefragt, als im Text",
         "vorkommt — die Antwort gehörte oft zur richtigen Regel und stimmte",
         "damit nach der Umbeschriftung von selbst.", "",
         "Ausgewertet mit `tools/nun_rules.py` in der Benennung des Lehrplans",
         "(keine Unterarten von Idgham). Über ein Halt-Zeichen hinweg entsteht",
         "keine Regel.", "",
         "| ID | Lektion | Frage | Änderung | Text |", "|---|---|---|---|---|"]
    for x, note in changes:
        t = (x.get("subject") or {}).get("text") or "—"
        L.append(f"| {x['id']} | {x['lesson']} | {nr.NAME[x['rule']]} | {' · '.join(note)} | {t} |")
    L += ["", "## Fundstellen der geänderten Aufgaben", ""]
    for x, note in changes:
        t = (x.get("subject") or {}).get("text")
        if not t:
            continue
        L += [f"### {x['id']} — {nr.NAME[x['rule']]}", "", f"> {t}", "",
              "| Auslöser | danach | Regel |", "|---|---|---|"]
        for s in nr.analyze(t):
            L.append(f"| {s['ausloeser']} | {s['folgt']} | {nr.NAME[s['regel']]} |")
        L.append("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
