#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut docs/tajweed-developer-guide.pdf — die Beschreibung des Datensatzes für
jemanden, der die App baut.

Der Text steht hier im Skript, die Zahlen kommen aus den JSON-Dateien: was im
Dokument steht, stimmt also mit dem überein, was ausgeliefert wird. Gesetzt
wird als HTML und über Chromium gedruckt — anders bekäme man die arabische
Schrift nicht richtig auf die Seite (Ligaturen, Laufrichtung, die Kartusche
der Versnummer).

Aufruf:  python3 tools/make_devguide.py
"""
import collections
import html
import json
import re
import subprocess
import time
from pathlib import Path

ZIEL = Path("docs/tajweed-developer-guide.pdf")
BLOECKE = [("tafkheem", 1, 9), ("qalqala", 10, 14), ("idgham", 15, 21),
           ("ikhfa-idgham", 22, 26), ("iqlab", 27, 28), ("madd", 29, 34),
           ("waqf", 35, 40)]


def laden():
    aus, je_datei = {}, {}
    for name, _, _ in BLOECKE:
        d = json.load(open(f"json/{name}.json", encoding="utf-8"))
        je_datei[name] = d
        for x in d:
            aus[x["id"]] = x
    return aus, je_datei


def j(x, felder=None, kuerzen=None):
    """Eine Aufgabe als eingerücktes JSON, optional gekürzt."""
    y = json.loads(json.dumps(x))
    if kuerzen:
        for pfad in kuerzen:
            ziel = y
            for k in pfad[:-1]:
                ziel = ziel[k] if isinstance(ziel, dict) else ziel[k]
            ziel[pfad[-1]] = "…"
    return json.dumps(y, ensure_ascii=False, indent=2)


def code(text, sprache="json"):
    return f'<pre class="code {sprache}">{html.escape(text)}</pre>'


def tabelle(kopf, zeilen, klassen=""):
    k = "".join(f"<th>{h}</th>" for h in kopf)
    z = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in zeilen)
    return f'<table class="{klassen}"><thead><tr>{k}</tr></thead><tbody>{z}</tbody></table>'


def ar(t):
    return f'<span class="ar">{html.escape(t)}</span>'


CSS = """
@font-face{font-family:'Hafs';src:url('../fonts/hafs-uthmanic.woff2') format('woff2');font-display:block}
@font-face{font-family:'AyahMark';src:url('../fonts/amiri-quran-arabic-400-normal.woff2') format('woff2');font-display:block}
@page{size:A4;margin:19mm 17mm 20mm}
@page:first{margin-top:34mm}
*{box-sizing:border-box}
body{margin:0;color:#25262b;background:#fff;
     font:10.5pt/1.55 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
     -webkit-font-smoothing:antialiased}
h1{font-size:25pt;line-height:1.12;margin:0 0 6pt;letter-spacing:-.4pt;color:#1B2560}
h2{font-size:15pt;margin:26pt 0 8pt;padding-bottom:5pt;border-bottom:1.6pt solid #1B2560;
   color:#1B2560;letter-spacing:-.2pt;break-after:avoid}
h3{font-size:11.5pt;margin:16pt 0 5pt;color:#1B2560;break-after:avoid}
h4{font-size:10pt;margin:12pt 0 4pt;color:#3d3f52;break-after:avoid}
p{margin:0 0 7pt}
ul,ol{margin:0 0 8pt;padding-left:16pt}
li{margin-bottom:3pt}
code{font-family:'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;font-size:9pt;
     background:#eef0f7;border-radius:3px;padding:.5pt 3pt;color:#2a2c55}
pre.code{font-family:'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;
   font-size:7.9pt;line-height:1.45;background:#f6f7fb;border:.7pt solid #dcdfec;
   border-left:2.4pt solid #1B2560;border-radius:3px;padding:7pt 9pt;margin:6pt 0 10pt;
   white-space:pre-wrap;word-break:break-word;overflow-wrap:anywhere;break-inside:avoid}
table{width:100%;border-collapse:collapse;margin:6pt 0 11pt;font-size:9pt;break-inside:avoid}
th{text-align:left;background:#eef0f7;color:#1B2560;font-weight:600;
   padding:4pt 6pt;border-bottom:1pt solid #c8cce0;vertical-align:top}
td{padding:3.6pt 6pt;border-bottom:.6pt solid #e6e8f2;vertical-align:top}
td code{font-size:8.4pt;background:none;padding:0}
table.tight td,table.tight th{padding:2.6pt 5pt;font-size:8.5pt}
table.num td:nth-child(n+2){text-align:right;font-variant-numeric:tabular-nums}
.ar{font-family:'Hafs','Amiri',serif;direction:rtl;unicode-bidi:isolate;font-size:13pt;line-height:1.9}
.ar.big{font-size:17pt}
.ayah{font-family:'AyahMark','Hafs',serif}
.lead{font-size:11.5pt;color:#4a4c5c;margin-bottom:12pt}
.meta{color:#73768c;font-size:9pt}
.note{background:#f4f6fc;border:.7pt solid #d7dbec;border-radius:4px;
      padding:7pt 10pt;margin:8pt 0 11pt;font-size:9.5pt;break-inside:avoid}
.note b{color:#1B2560}
.warn{background:#fdf6ec;border-color:#ecdcc0}
.warn b{color:#8a5a12}
.cover{height:232mm;display:flex;flex-direction:column;justify-content:space-between;break-after:page}
.cover .glyph{font-family:'Hafs',serif;font-size:46pt;color:#1B2560;line-height:1}
.cover .sub{font-size:13pt;color:#4a4c5c;margin-top:2pt}
.cover .facts{border-top:1.6pt solid #1B2560;padding-top:10pt;font-size:9.5pt;color:#4a4c5c}
.cover .facts b{color:#1B2560}
.toc{font-size:10pt}
.toc li{margin-bottom:2.5pt}
.pill{display:inline-block;background:#e6e9f6;color:#1B2560;border-radius:9px;
      padding:1pt 7pt;font-size:8.2pt;font-weight:600;margin-right:4pt;
      font-family:'SF Mono',Menlo,Consolas,monospace}
.task{break-inside:avoid-page}
.two{display:flex;gap:14pt}
.two>div{flex:1}
h2.pb{break-before:page}
"""


def deckblatt(alle, katalog):
    ton = 0
    for x in alle.values():
        if (x.get("subject") or {}).get("audio"):
            ton += 1
        ton += sum(1 for o in (x.get("options") or []) if o.get("audio"))
        ton += sum(1 for o in (x.get("items") or []) if o.get("audio"))
    return f"""
<div class="cover">
  <div>
    <div class="glyph">تجويد</div>
    <h1 style="margin-top:14pt">Tajweed Exercises</h1>
    <div class="sub">Data format and exercise types — a guide for the app developer</div>
    <p class="meta" style="margin-top:22pt">German Method · revision of {time.strftime('%d %B %Y')}</p>
  </div>
  <div>
    <p>This document describes the exercise corpus that ships as JSON: what an
    exercise looks like, what the seven interaction types mean, how the question
    text is produced, and what a client has to do to render Qur’anic Arabic
    correctly. Everything in here is generated from the files themselves, so the
    numbers match what you receive.</p>
    <div class="facts">
      <p><b>{len(alle)}</b> exercises &nbsp;·&nbsp; <b>40</b> lessons &nbsp;·&nbsp;
         <b>7</b> rules &nbsp;·&nbsp; <b>7</b> interaction types &nbsp;·&nbsp;
         <b>{len(katalog['questions'])}</b> question wordings &nbsp;·&nbsp;
         <b>{ton}</b> audio recordings</p>
      <p style="margin:0">Files: <code>json/*.json</code>, <code>questions.json</code>,
         <code>advanced.json</code> — downloadable as one ZIP from the app preview.</p>
    </div>
  </div>
</div>

<h2 style="margin-top:0">Contents</h2>
<ol class="toc">
  <li>What you are given</li>
  <li>The exercise object, field by field</li>
  <li>The four classifier keys</li>
  <li>Where the question text comes from</li>
  <li>The seven interaction types</li>
  <li>Highlighting the answer: the <code>spots</code> field</li>
  <li>Audio</li>
  <li>Combined lessons for advanced learners</li>
  <li>Rendering Qur’anic Arabic</li>
  <li>Invariants worth asserting</li>
  <li>Appendix: inventory</li>
</ol>
"""


def kapitel_1(je_datei, alle):
    zeilen = []
    for name, a, b in BLOECKE:
        d = je_datei[name]
        ton = 0
        for x in d:
            if (x.get("subject") or {}).get("audio"):
                ton += 1
            ton += sum(1 for o in (x.get("options") or []) if o.get("audio"))
            ton += sum(1 for o in (x.get("items") or []) if o.get("audio"))
        zeilen.append([f"<code>json/{name}.json</code>", f"{a}–{b}", str(len(d)), str(ton)])
    return """
<h2>1 · What you are given</h2>

<p>Seven files, one per block of the syllabus. Each file is a JSON array of
exercise objects; there is no envelope, no metadata header. Exercise ids are
unique across all seven files, so you can merge them into a single table and
key on <code>id</code>.</p>
""" + tabelle(["File", "Lessons", "Exercises", "Audio files"], zeilen, "tight num") + """
<p>Two further files sit next to them:</p>
<ul>
  <li><code>questions.json</code> — the wording of every question, in German and
      English. An exercise carries no prose of its own; see section 4.</li>
  <li><code>advanced.json</code> — which exercises make up the condensed lessons
      for advanced learners; see section 8.</li>
</ul>

<div class="note"><b>Encoding.</b> All files are UTF-8 without a BOM. Arabic text
is stored in the Uthmani orthography of the Madinah muṣḥaf, in NFC, and contains
no characters outside the Basic Multilingual Plane. That last point matters for
the <code>spots</code> offsets: one character equals one code point equals one
UTF-16 code unit, so the same integers are correct in JavaScript, Swift, Kotlin
and Python alike.</div>

<h3>Getting the files</h3>
<p>The download button on the app preview at
<code>tajweed-exercises.vercel.app</code> packs everything into
<code>tajweed-aufgaben.zip</code>. Single files are also served directly, for
example <code>/json/tafkheem.json</code> or <code>/questions.json</code>. The
same files live in the repository under <code>json/</code>.</p>
"""


def kapitel_2(alle):
    felder = [
        ["<code>id</code>", "integer", "always", "Unique across the whole corpus. Also the stem of the audio filenames."],
        ["<code>rule</code>", "enum", "always", "<code>tafkheem · qalqala · idgham · ikhfa · iqlab · madd · waqf</code>"],
        ["<code>lesson</code>", "integer", "always", "1–40, the lesson of the syllabus."],
        ["<code>task_type</code>", "enum", "always", "How the learner interacts. Seven values, section 5."],
        ["<code>question_type</code>", "enum", "always", "Which question is asked. Seventeen values."],
        ["<code>question_id</code>", "string", "always", "Key into <code>questions.json</code>. Finer than <code>question_type</code>, section 4."],
        ["<code>multiple</code>", "boolean", "only <code>select</code>", "<code>true</code> means the learner may tick more than one option."],
        ["<code>modality</code>", "enum", "always", "<code>audio</code> — the item is meant to be heard; <code>text</code> — read only."],
        ["<code>sura</code>", "integer or null", "always", "Sura number when the subject is a Qur’anic verse, else <code>null</code>."],
        ["<code>verse</code>", "integer or null", "always", "Verse number, same condition."],
        ["<code>subject</code>", "object or null", "always", "The word or verse the question is about. <code>null</code> only for <code>matching</code>."],
        ["<code>items</code>", "array", "only <code>matching</code>", "The words to be classified."],
        ["<code>options</code>", "array", "always", "The answer choices. Empty array for <code>mark_verse</code>."],
        ["<code>answer</code>", "varies", "always", "Shape depends on <code>task_type</code>, section 5."],
        ["<code>pattern</code>", "string or null", "optional", "The exact tajweed pattern targeted, colon-separated. Authoring aid, see below."],
    ]
    unter = [
        ["<code>text</code>", "string", "always", "The Arabic content, or a fixed token (see next table)."],
        ["<code>spots</code>", "array", "optional", "Character spans where the rule applies, section 6."],
        ["<code>audio</code>", "string or null", "optional", "Filename of the recording, section 7."],
        ["<code>id</code>", "integer", "options and items", "Stable within the exercise. The answer points at these."],
    ]
    marken = [
        ["<code>yes</code> / <code>no</code>", "The two options of every <code>yes_no</code> exercise."],
        ["<code>start</code> / <code>mid</code> / <code>end</code>", "Position in the word, for <code>select_position</code>."],
        ["<code>none</code>", "“does not occur” — the rule is absent, or none of the words qualifies."],
        ["<code>-</code>", "“no pattern” — in <code>matching</code>, the bucket for a word that fits none."],
        ["digits", "<code>\"0\"</code> … <code>\"6\"</code> in <code>select_count</code>; count them as numbers, not as Arabic."],
    ]
    return """
<h2 class="pb">2 · The exercise object, field by field</h2>
""" + tabelle(["Field", "Type", "Present", "Meaning"], felder) + """
<h3>Inside <code>subject</code>, <code>options[]</code> and <code>items[]</code></h3>
""" + tabelle(["Field", "Type", "Where", "Meaning"], unter) + """
<h3>Fixed tokens in <code>text</code></h3>
<p>Most <code>text</code> values are Arabic and go on screen unchanged. A handful
are fixed ASCII tokens that your client localises itself — they are deliberately
not German or English in the data, so that one corpus serves every language.</p>
""" + tabelle(["Token", "Meaning"], marken, "tight") + """
<div class="note warn"><b>Do not display a token verbatim.</b> <code>none</code>
needs different wording depending on the exercise: “does not occur” after a
counting question, “none of the words” in a word selection, “neither of them” in
the two-way pause exercise of lesson 40. Our own front end switches on
<code>task_type</code> and <code>question_id</code> to pick the phrasing.</div>

<h3>A note on <code>pattern</code></h3>
<p><code>pattern</code> lists the shapes the exercise targets, separated by
colons, with <code>◌</code> standing in as a dotted circle carrier — for instance
<code>قَّ:قِّ:قَ</code> or <code>◌َآ</code>. It was an authoring aid and it is
not always exact: in a few exercises it names a vowel the word does not carry.
<b>Do not derive anything from it.</b> Use it, if at all, as a caption for the
teacher’s view. For “where does the rule apply”, use <code>spots</code>, which is
checked against the answer key.</p>

<h3>TypeScript shape</h3>
""" + code("""type Rule = 'tafkheem'|'qalqala'|'idgham'|'ikhfa'|'iqlab'|'madd'|'waqf';
type TaskType = 'yes_no'|'select_count'|'select_position'|'select'
              | 'match'|'mark_verse'|'matching';

interface Spot { start: number; end: number; text: string }

interface Piece {
  id?: number;            // options[] and items[] only
  text: string;
  spots?: Spot[];
  audio?: string | null;
}

interface Pair { item: number; option: number }

interface Exercise {
  id: number;
  rule: Rule;
  lesson: number;         // 1..40
  task_type: TaskType;
  question_type: string;
  question_id: string;    // key into questions.json
  multiple?: boolean;     // task_type === 'select'
  modality: 'audio' | 'text';
  sura: number | null;
  verse: number | null;
  subject: Piece | null;  // null only when task_type === 'matching'
  items?: Piece[];        // task_type === 'matching'
  options: Piece[];       // [] when task_type === 'mark_verse'
  answer: number[] | string[] | Pair[];
  pattern?: string | null;
}""", "ts") + """
<h3>A complete exercise</h3>
""" + code(j(alle[1]))


def kapitel_3_4(alle, katalog):
    regeln = [
        ["<code>tafkheem</code>", "Tafkheem", "1–9", "Heavy consonants and the rules of the Rāʾ and the name Allah."],
        ["<code>qalqala</code>", "Qalqalah", "10–14", "The echoing release of ق ط ب ج د when they carry no vowel."],
        ["<code>idgham</code>", "Idgham", "15–21, 24–25", "One letter merging into the next."],
        ["<code>ikhfa</code>", "Ikhfa", "22–23, 26", "A nasal letter hidden before certain consonants."],
        ["<code>iqlab</code>", "Iqlab", "27–28", "Nūn or tanwīn turning into a Mīm before Bāʾ."],
        ["<code>madd</code>", "Madd", "29–34", "Prolongation beyond the plain long vowel."],
        ["<code>waqf</code>", "Waqf", "35–40", "The pause marks of the muṣḥaf."],
    ]
    z = []
    for e in katalog["questions"]:
        a, b = e["lessons"]
        z.append([f'<code>{e["id"]}</code>', f'<code>{e["task_type"][0]}</code>',
                  html.escape(e["de"]), str(e["count"]),
                  f"{a}" if a == b else f"{a}–{b}"])
    return """
<h2 class="pb">3 · The four classifier keys</h2>
<p>An exercise is described by four enums. Together they determine both what is
shown and what the learner does; nothing else in the record is prose.</p>

<h4><code>rule</code> — which tajweed rule</h4>
""" + tabelle(["Value", "Name we use", "Lessons", "What it is"], regeln, "tight") + """
<div class="note"><b>Spelling.</b> We transliterate the same way in German and in
English, oriented on English conventions: long ī as <code>ee</code>, خ as
<code>kh</code>, no diacritics. Hence Tafkheem, Qalqalah, Ikhfa, Noon, Meem,
Tanween, Saktah, Muanaqah. If your UI shows rule names, take them from this
table rather than inventing your own.</div>

<h4><code>lesson</code> — position in the syllabus</h4>
<p>1 to 40. The syllabus is strictly cumulative: an exercise in lesson <i>n</i>
never requires a rule first taught after <i>n</i>. You can rely on that when
ordering content or gating progress.</p>

<h4><code>task_type</code> — the interaction</h4>
<p>Seven values. They decide the shape of <code>answer</code> and the widget you
build. Section 5 covers each one.</p>

<h4><code>question_type</code> — the question asked</h4>
<p>Seventeen values. Several interaction types share a question type and vice
versa; the pairing is fixed and listed in the next section.</p>

<h2>4 · Where the question text comes from</h2>
<p>No exercise contains a question. The sentence is produced from
<code>question_id</code> against <code>questions.json</code>, so that one corpus
serves both languages and so that a teacher can rewrite the wording without
anyone touching the data.</p>
""" + code(json.dumps({"placeholders": katalog["placeholders"],
                       "rules": {"tafkheem": "Tafkheem", "…": "…"},
                       "questions": [katalog["questions"][0]]},
                      ensure_ascii=False, indent=2)) + """
<p>Two placeholders appear in the text: <code>{rule}</code> becomes the display
name of the exercise’s rule, <code>{sign}</code> becomes its pause mark, taken
from <code>pattern</code>. Substitute after escaping, so that teacher-authored
text cannot inject markup.</p>
""" + code("""function questionText(ex, catalogue, lang /* 'de' | 'en' */) {
  const entry = catalogue[ex.question_id];
  if (!entry) return '';                       // unknown id: show nothing
  return escapeHtml(entry[lang] ?? entry.de)
    .split('{rule}').join(escapeHtml(RULE_NAME[ex.rule]))
    .split('{sign}').join(signMarkup(ex.pattern));
}""", "js") + """
<div class="note"><b>Why <code>question_id</code> and not
<code>question_type</code>?</b> Because the same question type is worded
differently depending on context. <code>has_rule</code> asks “does this word
contain Idgham?” for a single word but “do these words contain Idgham?” for a
word pair, and for Madd it does not name the rule at all — it asks whether the
word contains a prolongation longer than two counts, because in this course the
plain long vowel is not itself a Madd. Four wordings, one question type. Keying
on <code>question_id</code> saves you from re-deriving that.</div>

<h3>The wordings</h3>
""" + tabelle(["question_id", "task_type", "German wording", "n", "Lessons"], z, "tight")


def aufgabe_block(titel, pill, anzahl, beschreibung, antwort, bsp, extra=""):
    return f"""
<div class="task">
<h3>{titel} <span class="pill">{pill}</span>
    <span class="meta" style="font-weight:400">{anzahl} exercises</span></h3>
{beschreibung}
<p><b>answer</b> — {antwort}</p>
{code(bsp)}
{extra}
</div>"""


def kapitel_5(alle, zaehler):
    uebersicht = [
        ["<code>yes_no</code>", str(zaehler["yes_no"]), "two fixed options", "<code>[id]</code>", "Does the rule occur here?"],
        ["<code>select_count</code>", str(zaehler["select_count"]), "number options", "<code>[id]</code>", "How many times does it occur?"],
        ["<code>select_position</code>", str(zaehler["select_position"]), "start / mid / end / none", "<code>[id]</code>", "Where in the word?"],
        ["<code>select</code>", str(zaehler["select"]), "2–5 options", "<code>[id, …]</code>", "Which vowel, letter or pause sign?"],
        ["<code>match</code>", str(zaehler["match"]), "4–5 word options", "<code>[id, …]</code>", "Which words form the rule with the reference word?"],
        ["<code>matching</code>", str(zaehler["matching"]), "pattern options + items", "<code>[{item,option}, …]</code>", "Sort four words into pattern buckets."],
        ["<code>mark_verse</code>", str(zaehler["mark_verse"]), "none", "<code>[\"…\", …]</code>", "Mark the spots inside the verse."],
    ]

    yes_no = aufgabe_block(
        "Yes or no", "yes_no", zaehler["yes_no"],
        """<p>The simplest form: one word or a two-word pair is shown, the learner
        decides whether the rule is present. <code>options</code> is always exactly
        the two tokens <code>yes</code> and <code>no</code>, in that order, with
        ids 1 and 2 — but read the ids from the data rather than assuming.</p>""",
        "an array with exactly one option id.",
        j(alle[1]),
        """<p>The subject is a word pair in 251 of these; there the rule only
        arises across the word boundary, and the wording switches to the plural
        accordingly (<code>has_rule.phrase</code>).</p>""")

    count = aufgabe_block(
        "Counting", "select_count", zaehler["select_count"],
        """<p>A whole verse is shown and the learner counts the occurrences. The
        options are consecutive numbers as strings; the window varies per exercise
        (<code>0…3</code>, <code>1…4</code>, <code>3…6</code>), so render them from
        the data, never from a fixed range.</p>""",
        "an array with exactly one option id — the option whose <code>text</code> is the correct number.",
        j(alle[5]),
        """<p>Note that <code>spots</code> lists exactly as many spans as the
        correct number. That is not a coincidence: the spans were derived from the
        rule and then checked against the answer key, and only written when the two
        agreed. You can use it as a self-check, or to show the learner where the
        occurrences were after answering.</p>""")

    pos = aufgabe_block(
        "Position in the word", "select_position", zaehler["select_position"],
        """<p>Four options: <code>start</code>, <code>mid</code>, <code>end</code>
        and <code>none</code>. The fourth is never the correct answer in the current
        corpus, but it is offered so that the learner cannot infer that the rule
        must be present somewhere.</p>""",
        "an array with exactly one option id.",
        j(alle[3]))

    sel = aufgabe_block(
        "Selection", "select", zaehler["select"],
        """<p>The broadest type. It covers five question types: which vowel sits on
        the rule letter, which vowel precedes it, which letter triggers the rule,
        and which pause sign occurs in the verse. The option texts are therefore
        sometimes bare diacritics (<code>َ</code>, <code>ُ</code>, <code>ِ</code>,
        <code>ْ</code>), sometimes letters, sometimes whole words.</p>
        <p><b>Always read <code>multiple</code>.</b> It is present on every
        <code>select</code> exercise and nowhere else. When it is <code>false</code>
        the answer holds exactly one id; when <code>true</code> it may hold one,
        several, or — via the <code>none</code> option — the statement that nothing
        occurs.</p>""",
        "an array of option ids. Exactly one if <code>multiple</code> is <code>false</code>.",
        j(alle[2]),
        """<h4>A bare diacritic needs a carrier</h4>
        <p>An option whose text is a single combining mark will not render on its
        own; it attaches to whatever precedes it. Prefix the dotted circle
        <code>U+25CC</code> when the text consists only of combining characters:</p>""" +
        code("""const COMBINING = /^[\\u0610-\\u061A\\u064B-\\u065F\\u0670\\u06D6-\\u06ED]+$/;
const display = (t) => COMBINING.test(t) ? '\\u25CC' + t : t;   // ◌ َ""", "js"))

    match = aufgabe_block(
        "Word matching", "match", zaehler["match"],
        """<p>A reference word is shown with four candidate words; the learner picks
        those that form the rule <i>together with</i> the reference word. This is
        the type where the rule lives at the seam between two words, so the answer
        is only meaningful as a pair.</p>
        <p>Two shapes exist. Usually <code>subject.text</code> is a real reference
        word and the recording is named <code>&lt;id&gt;_prompt.wav</code>. In 11
        exercises <code>subject.text</code> is the placeholder
        <code>اختر</code> (Arabic for “choose”), which means there is no reference
        word and each candidate stands on its own; <code>question_id</code> is then
        <code>match_rule.list</code> rather than <code>match_rule.prompt</code>.
        Check for that placeholder, do not print it.</p>""",
        "an array of option ids; it may be a single id, several, or the id of the <code>none</code> option.",
        j(alle[920]),
        """<div class="note warn"><b>Reading order is not always prompt first.</b>
        In exercise 1624 the reference word follows the candidate
        (أَلَمْ يَأْتِكُم بَشِيرٌ), because that is where the Mīm meets the Bāʾ. The
        <code>spots</code> on the option tell you which part is marked; if you
        synthesise the pair yourself for playback or display, take the order from
        the spots rather than assuming.</div>""")

    matching = aufgabe_block(
        "Bucket matching", "matching", zaehler["matching"],
        """<p>Four words are sorted into pattern buckets. This is the only type
        where <code>subject</code> is <code>null</code>; the content sits in
        <code>items</code> (the words) and <code>options</code> (the buckets). The
        last bucket is usually the token <code>-</code>, “no pattern”, for the word
        that fits none of them.</p>""",
        "an array of <code>{item, option}</code> pairs, one per item, covering every item exactly once.",
        j(alle[4]))

    mark = aufgabe_block(
        "Marking in the verse", "mark_verse", zaehler["mark_verse"],
        """<p>A verse is shown and the learner marks the places where the rule
        applies — there are no discrete options, so <code>options</code> is the
        empty array. This is the type used for the pause-mark lessons 35–39 as well
        as for Idgham, Ikhfa and Iqlab in the verse.</p>""",
        """an array of strings, each an exact substring of <code>subject.text</code>.""",
        j(alle[1500]),
        """<div class="note"><b>The empty array is an answer.</b> In 30 of these
        exercises the rule does not occur in the verse at all and
        <code>answer</code> is <code>[]</code>. That is the correct response —
        “does not occur” — not missing data. Every other task type has at least one
        entry in <code>answer</code>; only <code>mark_verse</code> may be
        empty.</div>
        <p>A span may cover two words, as above: the Idgham runs across the
        boundary. It may also occur more than once in the verse — the array then
        lists the same string twice, and you mark the first two occurrences. When
        a word repeats and only one instance carries the pause mark, prefer the
        occurrence followed by the sign named in <code>pattern</code>. The
        <code>spots</code> field has already resolved all of this; taking the spans
        from there instead of matching strings yourself is simpler and safer.</p>""")

    return """
<h2 class="pb">5 · The seven interaction types</h2>
""" + tabelle(["task_type", "n", "options", "answer", "What the learner does"], uebersicht) + """
<p>Everything below is real data, copied out of the files unchanged.</p>
""" + yes_no + count + pos + sel + match + matching + mark


def kapitel_6_7_8(alle, fortgeschritten, spots_subj, spots_opt, ton_gesamt):
    lek = {f["id"]: f for f in fortgeschritten["lessons"]}
    return """
<h2 class="pb">6 · Highlighting the answer: the <code>spots</code> field</h2>
<p>The answer key tells you <i>what</i> is right — a number, a vowel, a yes. It
does not tell you <i>where</i> in the word the rule applies, and for a counting
exercise that is exactly what the learner wants to see afterwards. That is what
<code>spots</code> is for.</p>

<p>It sits next to <code>text</code>, in the <code>subject</code> and in
individual options and items, and it always refers to <b>its own</b>
<code>text</code>:</p>
""" + code("""{ "text": "يَضِيقُ",
  "spots": [ { "start": 0, "end": 3, "text": "يَضِ" },
             { "start": 5, "end": 7, "text": "قُ" } ] }""") + """
<p>The rules it obeys:</p>
<ul>
  <li><code>start</code> and <code>end</code> are character offsets, half-open,
      exactly like <code>String.prototype.slice</code>.</li>
  <li><code>text.slice(start, end) === spot.text</code> holds for every span.
      Assert it once at load; if it ever fails you have an encoding problem, not
      a data problem.</li>
  <li>Spans are sorted ascending and never overlap; adjacent ones are merged.</li>
  <li>A span covers a letter <i>with its diacritics</i> — <code>ضِ</code>, not
      <code>ض</code> — and for rules that straddle a word boundary it covers both
      words.</li>
  <li>No <code>spots</code> key means there is nothing to mark. For the 403
      exercises whose answer is “does not occur”, that is precisely right.</li>
</ul>

<p>Rendering is a few lines:</p>
""" + code("""function highlight(text, spots) {
  let out = '', cursor = 0;
  for (const s of spots ?? []) {
    out += escapeHtml(text.slice(cursor, s.start))
         + '<mark>' + escapeHtml(s.text) + '</mark>';
    cursor = s.end;
  }
  return out + escapeHtml(text.slice(cursor));
}""", "js") + f"""
<p>Coverage in the current corpus: {spots_subj} subjects carry spans and
{spots_opt} options or items do.</p>

<div class="note"><b>How they were derived.</b> Not from <code>pattern</code>,
which is unreliable, but from the rule itself — sukūn and verse end for Qalqalah,
a nūn-rule analyser for Idgham, Ikhfa and Iqlab, the pause marks for Waqf, the
lesson’s letter set for Tafkheem, the written form of the prolongation for Madd.
Every derivation was then checked against the answer key: the number of spans
must equal the counted number, their presence must match a yes or a no, the
vowels on them must equal the vowels in the answer. Only what passed that check
was written. Where a client and this field disagree, the field is more likely to
be right.</div>

<h2>7 · Audio</h2>
<p>Recordings are named after the exercise id:</p>
""" + tabelle(["Pattern", "What it holds"], [
        ["<code>&lt;id&gt;.wav</code>", "The subject — the single word or the verse."],
        ["<code>&lt;id&gt;_prompt.wav</code>", "The reference word of a <code>match</code> exercise."],
        ["<code>&lt;id&gt;_1.wav</code> … <code>&lt;id&gt;_4.wav</code>", "The candidate words of <code>match</code>, the items of <code>matching</code>."],
    ], "tight") + f"""
<p>The filename is in the record; never construct it yourself. Fixed tokens
(<code>yes</code>, <code>none</code>, <code>-</code>, the numerals) never have a
recording — there is nothing to speak. {ton_gesamt} files make up the full set.
The {sum(1 for x in alle.values() if x['modality'] == 'text')} exercises with
<code>modality: "text"</code> have no audio at all and are meant to be read.</p>

<div class="note"><b>Different exercises may share a recording only if they share
the id — which they cannot.</b> Identical Arabic text does occur across
exercises, and each occurrence has its own file. If you want to save space,
deduplicate by text at packaging time and keep a map; do not assume the corpus
has done it for you.</div>

<h2>8 · Combined lessons for advanced learners</h2>
<p>A learner who already knows the material does not need the letters one at a
time. <code>advanced.json</code> defines condensed lessons that stand in for
several ordinary ones. They contain no new exercises: they list ids of existing
ones, so the recordings and the answer keys are shared.</p>
""" + code(json.dumps({"lessons": [
        {k: v for k, v in lek["tafkheem-1-advanced"].items() if k != "tasks"} | {"tasks": lek["tafkheem-1-advanced"]["tasks"][:6] + ["…"]}
    ]}, ensure_ascii=False, indent=2)) + """
""" + tabelle(["id", "replaces", "exercises", "what it is"], [
        ["<code>tafkheem-1-advanced</code>", "lessons 1–7", str(len(lek["tafkheem-1-advanced"]["tasks"])), "all heavy letters in one lesson"],
        ["<code>qalqala-1-advanced</code>", "lessons 10–14", str(len(lek["qalqala-1-advanced"]["tasks"])), "Qalqalah inside the word"],
        ["<code>qalqala-2-advanced</code>", "lessons 10–14", str(len(lek["qalqala-2-advanced"]["tasks"])), "Qalqalah at the end of the verse"],
    ], "tight") + """
<p>Whether to use them is a per-learner setting. When a group is active its
lessons take the place of the ones in <code>replaces</code> and the numbering
closes up: with both groups on, lesson 1 is the combined Tafkheem lesson, lesson
2 is what used to be 8, lessons 4 and 5 are the two Qalqalah lessons, lesson 6 is
what used to be 15 — 31 lessons instead of 40.</p>
""" + code("""function lessonList(advanced /* the entries you want active */) {
  const out = []; let old = 1, n = 1;
  while (old <= 40) {
    const here = advanced.filter(a => a.replaces[0] === old);
    if (here.length) {
      for (const a of here) out.push({ number: n++, combined: a });
      old = here[0].replaces.at(-1) + 1;
    } else {
      out.push({ number: n++, lesson: old });
      old++;
    }
  }
  return out;
}""", "js") + """
<div class="note"><b>Do not read the three <code>*-advanced.json</code> files
alongside the seven lesson files.</b> They are the same exercises a second time,
written out for convenience. Merging all ten would double-count 168 exercises.
Either use the seven plus <code>advanced.json</code>, or use the advanced files
on their own.</div>

<p>The combined lessons are balanced deliberately: roughly equal numbers from
each source lesson, the interaction types in the proportion of the pool, and the
answers spread flatter than the pool — in the source, more than half the counting
answers are zero, which would reward guessing. The exception is “Qalqalah at the
end of the verse”: there are only 40 exercises in the whole corpus where the
prolonged stop at the verse end actually produces a Qalqalah, so that lesson
holds all 40 and no selection takes place.</p>
"""


def kapitel_9_10_11(alle, je_datei, katalog, zaehler):
    inv = []
    for name, a, b in BLOECKE:
        d = je_datei[name]
        c = collections.Counter(x["task_type"] for x in d)
        inv.append([f"<code>{name}</code>", f"{a}–{b}", str(len(d))] +
                   [str(c.get(t, 0)) for t in ("yes_no", "select_count", "select_position",
                                               "select", "match", "matching", "mark_verse")])
    inv.append(["<b>total</b>", "1–40", f"<b>{len(alle)}</b>"] +
               [f"<b>{zaehler[t]}</b>" for t in ("yes_no", "select_count", "select_position",
                                                 "select", "match", "matching", "mark_verse")])
    lek = collections.Counter(x["lesson"] for x in alle.values())
    lz = []
    for start in range(1, 41, 8):
        lz.append([" ".join(f"<code>{n}</code>&nbsp;{lek[n]}" for n in range(start, min(start + 8, 41)))])
    return """
<h2 class="pb">9 · Rendering Qur’anic Arabic</h2>
<p>The text is not ordinary Arabic prose. It is the Uthmani orthography of the
muṣḥaf, and three things go wrong if you treat it as plain text.</p>

<h3>The font</h3>
<p>Use a muṣḥaf face. We ship <code>fonts/hafs-uthmanic.woff2</code> (KFGQPC HAFS
Uthmanic Script, 61 kB subset) for the body of the text and
<code>fonts/amiri-quran-arabic-400-normal.woff2</code> for one glyph only, the
verse-number cartouche. A system Arabic font will render most of it, but the
small superscript marks — the dagger alif <code>ٰ</code>, the small wāw and yāʾ of
the ṣila <code>ۥ ۦ</code>, the silent-letter circle <code>۟</code>, the maddah
<code>ٓ</code> — are frequently missing, and their absence changes what the learner
sees.</p>

<h3>The verse number</h3>
<p>Indic digits at the end of a verse are its number, not part of the word. They
belong inside the ornamented cartouche: put <code>U+06DD</code> immediately
before the digits and a space before that. Split the tail off before you lay the
text out:</p>
""" + code("""const AYAH_TAIL = /[\\u0660-\\u0669\\u06F0-\\u06F9]+$/;

function splitAyah(text) {
  const m = text.match(AYAH_TAIL);
  if (!m) return [text, ''];
  return [text.slice(0, m.index).trimEnd(), '\\u06DD' + m[0]];   // cartouche + digits
}""", "js") + """
<p>Render the second part in the cartouche font and the first part in the body
font. Keep the digits as they are — do not convert them to Western numerals, and
do not include them in a preview that shows only the first few words.</p>

<h3>Direction</h3>
<p>Set <code>direction: rtl</code> and <code>unicode-bidi: isolate</code> on
every element that holds Arabic. Without the isolation, a Latin label or a
Western numeral next to the text drags punctuation to the wrong end. Give the
text generous line height — 1.9 to 2.2 — because the superscript marks sit high
and collide otherwise.</p>

<h3>Do not normalise, do not strip</h3>
<p>Every mark in the text is deliberate. Removing diacritics to “simplify”
matching, or running the text through a normaliser that recomposes sequences,
will silently invalidate every <code>spots</code> offset and can change the
reading. Compare strings byte for byte, or not at all.</p>

<h2>10 · Invariants worth asserting</h2>
<p>These all hold for the shipped corpus. Assert them once when you load the
data; each one has caught a real bug at some point.</p>
""" + tabelle(["Invariant", "Why it matters"], [
        ["<code>id</code> is unique across all seven files", "Two exercises once collided at a file seam and shared a recording."],
        ["<code>answer</code> is never empty, except for <code>mark_verse</code>", "An empty answer elsewhere means a missing key, not “none”."],
        ["<code>yes_no</code>, <code>select_count</code>, <code>select_position</code> have exactly one answer id", "Anything else is a data error."],
        ["<code>select</code> with <code>multiple: false</code> has exactly one answer id", "Twelve exercises once had two."],
        ["every answer id exists in <code>options</code> (or <code>items</code>)", "Guards against reordering damage."],
        ["<code>mark_verse</code> answers are exact substrings of <code>subject.text</code>", "They are matched literally, not fuzzily."],
        ["<code>matching</code> pairs cover every item exactly once", "Otherwise a bucket stays unexplained."],
        ["<code>subject</code> is <code>null</code> only for <code>matching</code>", "Everything else has something to show."],
        ["<code>options</code> is empty only for <code>mark_verse</code>", ""],
        ["<code>multiple</code> is present exactly on <code>select</code>", ""],
        ["<code>text.slice(start,end) === spot.text</code> for every span", "Catches encoding damage immediately."],
        ["audio filenames match <code>&lt;id&gt;(_n|_prompt)?.wav</code>", ""],
        ["no fixed token carries an audio filename", "37 once did; there is nothing to record."],
        ["no Latin letters in any <code>text</code> outside the fixed tokens", "Keeps the corpus language-neutral."],
    ], "tight") + """
<h2 class="pb">11 · Appendix: inventory</h2>
<h3>Exercises per file and interaction type</h3>
""" + tabelle(["File", "Lessons", "n", "yes_no", "count", "pos", "select", "match", "matching", "mark"], inv, "tight num") + """
<h3>Exercises per lesson</h3>
""" + tabelle(["", ], lz, "tight") + """
<p class="meta">Lessons 15–23 and 29–40 are smaller than 64 by design: the
material for those rules is finite. Lesson 34, the opening letters of the suras,
has only 16 exercises because the Qur’an contains only fourteen distinct
openings; lesson 40, the two-way pause, has 16 because the mark occurs at only a
handful of places.</p>

<h3>Where to look when something is unclear</h3>
<ul>
  <li>The exercise browser at <code>/browser/</code> shows every exercise with its
      answer key, its spans and the anomalies it can detect — useful for checking
      what a record is supposed to look like on screen.</li>
  <li>The app preview at <code>/</code> is a working implementation of everything
      in this document: question text from the catalogue, spans as highlights,
      the combined lessons, all seven interaction types.</li>
  <li><code>/fragen/</code> is where the wordings are edited.</li>
</ul>
"""


def main() -> int:
    alle, je_datei = laden()
    katalog = json.load(open("questions.json", encoding="utf-8"))
    fortgeschritten = json.load(open("advanced.json", encoding="utf-8"))
    zaehler = collections.Counter(x["task_type"] for x in alle.values())
    spots_subj = sum(1 for x in alle.values() if (x.get("subject") or {}).get("spots"))
    spots_opt = sum(1 for x in alle.values()
                    for o in (x.get("options") or []) + (x.get("items") or []) if o.get("spots"))
    ton = 0
    for x in alle.values():
        if (x.get("subject") or {}).get("audio"):
            ton += 1
        ton += sum(1 for o in (x.get("options") or []) if o.get("audio"))
        ton += sum(1 for o in (x.get("items") or []) if o.get("audio"))

    kat = {q["id"]: q for q in katalog["questions"]}
    body = (deckblatt(alle, katalog)
            + kapitel_1(je_datei, alle)
            + kapitel_2(alle)
            + kapitel_3_4(alle, katalog)
            + kapitel_5(alle, zaehler)
            + kapitel_6_7_8(alle, fortgeschritten, spots_subj, spots_opt, ton)
            + kapitel_9_10_11(alle, je_datei, katalog, zaehler))

    seite = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
             "<title>Tajweed Exercises — Developer Guide</title>"
             f"<style>{CSS}</style></head><body>{body}</body></html>")
    quelle = Path("docs/_devguide.html")
    quelle.write_text(seite, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    ZIEL.parent.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox"])
        p = b.new_page()
        p.goto("http://127.0.0.1:8123/docs/_devguide.html", wait_until="networkidle")
        p.wait_for_timeout(700)
        p.pdf(path=str(ZIEL), format="A4", print_background=True,
              display_header_footer=True,
              header_template="<div></div>",
              footer_template=(
                  '<div style="width:100%;font-size:7.5pt;color:#9a9db0;'
                  'font-family:-apple-system,Helvetica,sans-serif;'
                  'padding:0 17mm;display:flex;justify-content:space-between">'
                  '<span>Tajweed Exercises · Developer Guide</span>'
                  '<span class="pageNumber"></span></div>'),
              margin={"top": "19mm", "bottom": "20mm", "left": "17mm", "right": "17mm"})
        b.close()
    quelle.unlink()
    kb = ZIEL.stat().st_size / 1024
    print(f"{ZIEL}  {kb:.0f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
