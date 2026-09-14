#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Der Katalog der Fragestellungen.

Eine Aufgabe trägt keinen Fragetext, sondern nur Schlüssel (question_type,
rule, task_type); die Formulierung entsteht in der Anzeige. Damit ein Lehrer
die Formulierungen bearbeiten kann, braucht jede eine eigene, stabile ID.

question_type allein reicht dafür nicht: „has_rule" wird je nach Aufgabe
unterschiedlich formuliert — beim Madd fragt der Kurs nach der Dehnung über
zwei Einheiten hinaus statt nach der Regel, und bei einem Wortpaar heißt es
„diese Wörter" statt „dieses Wort". Deshalb gibt es hier IDs der Form
    <question_type>[.<Spielart>]
und zu jeder genau einen deutschen und einen englischen Text.

In den Texten stehen zwei Platzhalter:
    {rule}   der Name der Regel — Tafkheem, Qalqalah, Idgham, Ikhfa, Iqlab,
             Madd, Waqf
    {sign}   das Halt-Zeichen der Aufgabe, aus dem Feld „pattern"

frage_id(x) sagt zu jeder Aufgabe, welche Formulierung sie bekommt. Diese
Funktion ist die einzige Stelle, an der das entschieden wird — sie schreibt
das Feld „question_id" in die JSON-Dateien und baut den Katalog auf.
"""

PLATZHALTER = {
    "rule": "Name der Regel (Tafkheem, Qalqalah, Idgham, Ikhfa, Iqlab, Madd, Waqf)",
    "sign": "das Halt-Zeichen der Aufgabe, z. B. ◌ۚ",
}

# id -> (deutsch, englisch, wann diese Formulierung greift)
TEXTE = {
    "has_rule.word": (
        "Enthält dieses Wort ein {rule}?",
        "Does this word contain {rule}?",
        "Ja/Nein zu einem einzelnen Wort."),
    "has_rule.phrase": (
        "Enthalten diese Wörter ein {rule}?",
        "Do these words contain {rule}?",
        "Ja/Nein zu zwei oder drei Wörtern — die Regel entsteht erst über die "
        "Wortgrenze hinweg."),
    "has_rule.madd.word": (
        "Enthält dieses Wort eine Dehnung, die länger als zwei Einheiten ist?",
        "Does this word contain a prolongation longer than two counts?",
        "Ja/Nein beim Madd. Der Kurs fragt nicht nach dem natürlichen "
        "Langvokal, sondern nach der Dehnung darüber hinaus."),
    "has_rule.madd.phrase": (
        "Enthalten diese Wörter eine Dehnung, die länger als zwei Einheiten ist?",
        "Do these words contain a prolongation longer than two counts?",
        "Dasselbe beim Madd über die Wortgrenze (Madd Munfasil)."),
    "count_rule": (
        "Wie oft kommt {rule} vor?",
        "How often does {rule} occur?",
        "Anzahl der Fundstellen im Vers."),
    "count_rule.madd": (
        "Wie oft kommt eine Dehnung vor, die länger als zwei Einheiten ist?",
        "How often does a prolongation longer than two counts occur?",
        "Anzahl beim Madd."),
    "match_rule.prompt": (
        "Welche der folgenden Wörter bilden mit diesem ein {rule}?",
        "Which of these words form {rule} with it?",
        "Mit Vorgabewort: gemeint ist die Verbindung aus Vorgabewort und "
        "Auswahlwort."),
    "match_rule.list": (
        "Markiere alle Wörter mit {rule}. (Mehrfachauswahl möglich)",
        "Mark every word with {rule}. (more than one may be correct)",
        "Ohne Vorgabewort: jedes Wort für sich."),
    "match_pattern": (
        "Ordne jedes Wort seinem {rule}-Muster zu.",
        "Match each word to its {rule} pattern.",
        "Zuordnung Wort → Muster."),
    "which_letter": (
        "Welcher Buchstabe löst das {rule} aus?",
        "Which letter triggers the {rule}?",
        "Nach dem auslösenden Buchstaben."),
    "vowel_before_letter": (
        "Welcher Vokal steht vor dem {rule}-Buchstaben?",
        "Which vowel comes before the {rule} letter?",
        "Ein Buchstabe im Wort."),
    "vowels_before_letter": (
        "Welche Vokale stehen vor den {rule}-Buchstaben?",
        "Which vowels come before the {rule} letters?",
        "Mehrere Buchstaben im Wort oder Vers."),
    "vowel_on_letter": (
        "Welcher Vokal steht auf dem {rule}-Buchstaben?",
        "Which vowel is on the {rule} letter?",
        "Ein Buchstabe im Wort."),
    "vowels_on_letter": (
        "Welche Vokale stehen auf den {rule}-Buchstaben?",
        "Which vowels are on the {rule} letters?",
        "Mehrere Buchstaben im Wort oder Vers."),
    "position_in_word": (
        "An welcher Stelle im Wort steht das {rule}?",
        "Where in the word is the {rule}?",
        "Anfang, Mitte oder Ende."),
    "mark_rule_in_verse": (
        "Markiere jede Stelle im Vers, an der {rule} vorkommt.",
        "Mark every place in the verse where {rule} occurs.",
        "Der Lernende markiert im Vers selbst."),
    "mark_rule_in_verse.madd": (
        "Markiere jede Stelle im Vers, an der länger als zwei Einheiten gedehnt wird.",
        "Mark every place in the verse prolonged longer than two counts.",
        "Dasselbe beim Madd."),
    "identify_waqf_sign": (
        "Welches Waqf-Zeichen steht in diesem Vers?",
        "Which waqf sign is in this verse?",
        "Mehrfachauswahl: genannt werden alle Zeichen, die im Vers stehen."),
    "identify_waqf_sign.muanaqah": (
        "Muanaqah {sign} — an welchem der beiden Wörter darf angehalten werden? "
        "(nur an einer der beiden Stellen, nicht an beiden)",
        "Muanaqah {sign} — at which of the two words may you pause? "
        "(at one of them, not at both)",
        "Das Zeichen steht doppelt; angehalten wird an einer der beiden "
        "Stellen."),
    "mark_waqf_optional": (
        "Markiere jedes Wort vor einem freiwilligen Halt {sign}.",
        "Mark every word before an optional pause {sign}.",
        "Lektion 35."),
    "mark_waqf_better_continue": (
        "Markiere jedes Wort, an dem besser weitergelesen wird {sign}.",
        "Mark every word where it is better to read on {sign}.",
        "Lektion 36."),
    "mark_waqf_better_pause": (
        "Markiere jedes Wort, an dem besser angehalten wird {sign}.",
        "Mark every word where it is better to pause {sign}.",
        "Lektion 37."),
    "mark_waqf_forbidden": (
        "Markiere jedes Wort, an dem der Halt verboten ist {sign}.",
        "Mark every word where pausing is forbidden {sign}.",
        "Lektion 38."),
    "mark_waqf_mandatory": (
        "An welchen Stellen darf man nicht ohne Anhalten weiterlesen?",
        "Where may you not read on without pausing?",
        "Lektion 39, Waqf Lazim und Saktah zusammen."),
}

PROMPT = "اختر"          # steht im subject, wenn es kein Vorgabewort gibt


def _woerter(x):
    t = (x.get("subject") or {}).get("text") or ""
    return len(t.split())


def frage_id(x):
    """Welche Formulierung bekommt diese Aufgabe?"""
    qt = x["question_type"]
    if qt == "has_rule":
        teil = "phrase" if _woerter(x) > 1 else "word"
        return f"has_rule.madd.{teil}" if x["rule"] == "madd" else f"has_rule.{teil}"
    if qt == "count_rule":
        return "count_rule.madd" if x["rule"] == "madd" else "count_rule"
    if qt == "mark_rule_in_verse":
        return "mark_rule_in_verse.madd" if x["rule"] == "madd" else "mark_rule_in_verse"
    if qt == "match_rule":
        vorgabe = (x.get("subject") or {}).get("text")
        return "match_rule.prompt" if vorgabe and vorgabe != PROMPT else "match_rule.list"
    if qt == "identify_waqf_sign":
        return "identify_waqf_sign.muanaqah" if x.get("pattern") == "ۛ" else "identify_waqf_sign"
    return qt
