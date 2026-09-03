#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fundstellen für Idgham, Ikhfāʾ und Iqlāb — in der vereinfachten Benennung des
Kurses (keine Unterarten).

  Nūn sākin (ن ohne Vokal) oder Tanwīn (ً ٌ ٍ), danach
      ي ر م ل و ن   -> Idgham      (über die Wortgrenze hinweg)
      ب             -> Iqlāb
      ء ه ع ح غ خ   -> kein Fall (Izhār)
      die übrigen 15 -> Ikhfāʾ

  Mīm sākin (م ohne Vokal), danach
      م             -> Idgham
      ب             -> Ikhfāʾ
      sonst          -> kein Fall (Izhār)

  Dazu der Sonderfall ٱرْكَب مَّعَنَا: bāʾ sākin vor mīm -> Idgham.

Idgham gilt nur über die Wortgrenze; innerhalb eines Wortes (دُنْيَا, صِنْوَان)
wird getrennt gelesen. Ikhfāʾ und Iqlāb gelten auch im Wortinneren.

Über ein Halt-Zeichen hinweg entsteht keine Regel: dort wird angehalten, der
Auslaut fällt weg. Der Kursautor zählt in Aufgabe 1533 entsprechend vier statt
sechs Stellen. ۖ (besser weiterlesen) und ۙ (Halt verboten) zählen nicht als
Halt.
"""
import re

IDGHAM_AFTER_NUN = set("يرملون")
IKHFA_AFTER_NUN = set("تثجدذزسشصضطظفقك")
IZHAR_AFTER_NUN = set("ءأإآؤئهعحغخ")
NAME = {"idgham": "Idghām", "ikhfa": "Ichfāʾ", "iqlab": "Iqlāb"}

# Lange Vokale und Hamza lösen kein Idgham aus; Alif-Wasl gehört zum Wort davor
NO_TRIGGER = set("اىويءأإآؤئٱ")
VOWELS = set("َُِ")          # Fatha, Damma, Kasra
TANWIN = set("ًٌٍ")
SHADDA, SUKUN = "ّ", "ْ"
WAQF = set("ۖۗۘۙۚۛۜ۩۞ۭ")
# Nur an diesen Zeichen wird angehalten. ۖ (besser weiterlesen) und ۙ (Halt
# verboten) sind keine Halte — über sie hinweg gilt die Regel weiter.
WAQF_STOP = set("ۗۘۚۛۜ")
DIGITS = set("٠١٢٣٤٥٦٧٨٩")
# Alles, was kein Buchstabe ist: Harakat und quranische Zusatzzeichen
MARKS = set("ًٌٍَُِّْٰٰٕٓٔٓٔ۟۠ۡۢۥ"
            "ۦً۪ۭۧۨ۫۬ۜـ"
            "۝ۤ۩۞ٖٜٗ٘ۖۗ"
            "ۘۙۚۛ")


def tokenize(text):
    """[(buchstabe, marks, wort_nr)] — Waqf-Zeichen und Ziffern fallen weg,
    zwischen zwei Wörtern steigt wort_nr."""
    out, word, prev_space = [], 0, True
    for ch in text:
        if ch.isspace():
            prev_space = True
            continue
        if ch in DIGITS:
            continue
        if ch in WAQF:
            if out and ch in WAQF_STOP:
                out[-1][3] = True          # danach wird angehalten
            continue
        if ch in MARKS or ch == "ـ":
            if out:
                out[-1][1].append(ch)
            continue
        if prev_space and out:
            word += 1
        prev_space = False
        out.append([ch, [], word, False])
    return out


def _article_lam(toks, i):
    """Sonnenbuchstabe im Artikel ٱل — das ist Leseregel, keine Idgham-Aufgabe."""
    if toks[i][0] != "ل" or i == 0:
        return False
    prev = toks[i - 1]
    if prev[2] != toks[i][2]:
        return False
    if prev[0] in "ٱا" and not prev[1]:
        return True
    # لِلنَّاسِ, لِلزَّكَوٰةِ: das Alif des Artikels fällt nach لِ weg
    return prev[0] == "ل" and "ِ" in prev[1] and (i < 2 or toks[i - 2][2] != toks[i][2])


def _next_letter(toks, i):
    """Nächster Buchstabe nach i; ein stummes Alif hinter Tanwīn wird
    übersprungen (صُحُفًا مُّطَهَّرَةً)."""
    j = i + 1
    if j < len(toks) and toks[j][0] in "اى" and not toks[j][1] and toks[j][2] == toks[i][2]:
        j += 1
    return j if j < len(toks) else None


def analyze(text):
    """Liste der Fundstellen: {regel, ausloeser, folgt, wort, i}."""
    toks = tokenize(text)
    out = []
    for i, (ch, marks, w, _stop) in enumerate(toks):
        ms = set(marks)
        sakin = not (ms & VOWELS) and SHADDA not in ms
        trigger = None
        if ms & TANWIN:
            trigger = "tanwin"
        elif sakin and ch == "ن":
            trigger = "nun"
        elif sakin and ch == "م":
            trigger = "mim"
        elif sakin and ch not in NO_TRIGGER and not _article_lam(toks, i):
            trigger = "sakin"
        if not trigger:
            continue
        j = _next_letter(toks, i)
        if j is None:
            continue
        nxt, nmarks, nw, _ = toks[j]
        across = nw != w
        if any(toks[k][3] for k in range(i, j)):
            continue                       # dazwischen wird angehalten
        shadda = SHADDA in set(nmarks)
        rule = None
        if trigger in ("nun", "tanwin"):
            if nxt in IDGHAM_AFTER_NUN and across:
                rule = "idgham"
            elif nxt == "ب":
                rule = "iqlab"
            elif nxt in IKHFA_AFTER_NUN:
                rule = "ikhfa"
            elif shadda and across:
                rule = "idgham"
        elif trigger == "mim":
            if nxt == "م":
                rule = "idgham"
            elif nxt == "ب":
                rule = "ikhfa"
        elif trigger == "sakin" and shadda and nxt not in NO_TRIGGER:
            # gleicher, verwandter oder benachbarter Buchstabe verschmilzt
            rule = "idgham"
        if rule:
            out.append({"regel": rule, "ausloeser": ch + "".join(marks),
                        "folgt": nxt + "".join(nmarks), "wort": w, "folgt_wort": nw, "i": i, "j": j,
                        "stelle": "".join(t[0] + "".join(t[1]) for t in toks[max(0, i - 4):j + 4])})
    return out


def words_raw(text):
    """Die Wörter des Textes in derselben Zählung wie tokenize(): reine
    Waqf- oder Ziffernmarken sind keine Wörter."""
    return [w for w in text.split()
            if any(c not in WAQF and c not in DIGITS and c not in MARKS and not c.isspace()
                   for c in w)]


def spans(text, rule):
    """Markierungstext je Fundstelle: das Wortpaar bzw. das einzelne Wort."""
    ws = words_raw(text)
    out = []
    for s in analyze(text):
        if s["regel"] != rule:
            continue
        a, b = s["wort"], s["folgt_wort"]
        out.append(ws[a] if a == b else ws[a] + " " + ws[b])
    return out


def pattern(text, rule):
    """Musterangabe im Aufgabentitel: je Fundstelle „Auslöser Folgebuchstabe",
    ohne Leerzeichen, wenn beide im selben Wort stehen."""
    toks = tokenize(text)
    parts = []
    for s in analyze(text):
        if s["regel"] != rule:
            continue
        i, j = s["i"], s["j"]
        ms = set(toks[i][1])
        tan = ms & TANWIN
        if tan:
            head = "".join(sorted(tan))
            if j > i + 1:                       # stummes Alif hinter Tanwīn
                head += toks[i + 1][0]
        else:
            head = toks[i][0]
        tail = toks[j][0] + (SHADDA if SHADDA in set(toks[j][1]) else "")
        parts.append(head + (" " if toks[i][2] != toks[j][2] else "") + tail)
    return ":".join(parts) or None


def count(text, rule):
    return sum(1 for s in analyze(text) if s["regel"] == rule)


if __name__ == "__main__":
    import sys
    for t in sys.argv[1:]:
        print(t)
        for s in analyze(t):
            print("   ", s["regel"], s["ausloeser"], "->", s["folgt"])
