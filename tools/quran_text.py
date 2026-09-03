#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tanzil-Schreibweise (quran-json) in die Schreibweise des Datensatzes.

Die Regeln sind aus 687 Versen abgeleitet, die in beiden Fassungen vorliegen;
432 davon werden zeichengenau reproduziert, der Rest weicht in Eigenheiten des
Datensatzes ab (etwa ٱلْسَّمَٰوَٰتِ mit Sukūn auf dem Artikel-Lām).
"""
import re
MAP = {"ۡ": "ْ", "ٗ": "ً", "ٖ": "ٍ", "ٞ": "ٌ"}
DROP = "ـۢۥ"
WAQF = "ۖۗۘۙۚۛۜ"

MARKS = set("ًٌٍَُِّْٰٓٔ۟۠ۦٕٖٜٟۧۨ۫۬ٗ٘ٙٚٛٝٞ")

def canon(t):
    """Schadda vor den Vokal — so schreibt es der Datensatz."""
    out, i = [], 0
    while i < len(t):
        c = t[i]
        if c in MARKS:
            j = i
            while j < len(t) and t[j] in MARKS:
                j += 1
            grp = t[i:j]
            out.append("".join(sorted(grp, key=lambda m: 0 if m == "ّ" else 1)))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def to_dataset(t):
    t = "".join(MAP.get(c, c) for c in t if c not in DROP)
    t = t.replace("اْ", "ا۟")          # وا۟
    t = re.sub(r"ي(?=\s|$)", "ى", t)             # auslautendes Ya ohne Punkte
    t = re.sub(r"(?<=[^\s])([" + WAQF + r"])", r" \1", t)  # Waqf-Zeichen abgesetzt
    t = re.sub(r"([" + WAQF + r"])(?=[^\s])", r"\1 ", t)
    t = re.sub(r"(۞)(?=\S)", r"\1 ", t)
    return canon(re.sub(r"\s+", " ", t).strip())
