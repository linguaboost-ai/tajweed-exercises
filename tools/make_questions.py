#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schreibt den Fragenkatalog und die Übersicht für den Lehrer.

    questions.json    der Katalog: je Formulierung eine ID, ein deutscher und
                      ein englischer Text. Das ist die Datei, die bearbeitet
                      wird; beide Seiten lesen sie.
    fragen/index.html die Übersicht zum Bearbeiten: jede Formulierung mit
                      einem einfachen Beispiel, den Texten zum Ändern und
                      einem Knopf, der das geänderte questions.json ausgibt.

Vorhandene Texte in questions.json bleiben erhalten — das Skript ergänzt nur,
was fehlt, und schreibt Zahlen und Beispiele neu. Bearbeitungen des Lehrers
gehen also nicht verloren, wenn es erneut läuft.

Aufruf:  python3 tools/make_questions.py
"""
import glob
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from questions import TEXTE, PLATZHALTER, frage_id            # noqa: E402

KATALOG = Path("questions.json")
SEITE = Path("fragen/index.html")

RULE = {"tafkheem": "Tafkheem", "qalqala": "Qalqalah", "idgham": "Idgham",
        "ikhfa": "Ikhfa", "iqlab": "Iqlab", "madd": "Madd", "waqf": "Waqf"}

# Reihenfolge und Überschriften der Übersicht
GRUPPEN = [
    ("Ja oder Nein", ["has_rule.word", "has_rule.phrase",
                      "has_rule.madd.word", "has_rule.madd.phrase"]),
    ("Anzahl", ["count_rule", "count_rule.madd"]),
    ("Vokale und Stelle", ["vowel_on_letter", "vowels_on_letter",
                           "vowel_before_letter", "vowels_before_letter",
                           "which_letter", "position_in_word"]),
    ("Wörter auswählen", ["match_rule.prompt", "match_rule.list"]),
    ("Zuordnen", ["match_pattern"]),
    ("Im Vers markieren", ["mark_rule_in_verse", "mark_rule_in_verse.madd"]),
    ("Halt-Zeichen", ["identify_waqf_sign", "identify_waqf_sign.muanaqah",
                      "mark_waqf_optional", "mark_waqf_better_continue",
                      "mark_waqf_better_pause", "mark_waqf_forbidden",
                      "mark_waqf_mandatory"]),
]


def aufgaben():
    aus = []
    for f in sorted(glob.glob("json/*.json")):
        aus += json.load(open(f, encoding="utf-8"))
    aus.sort(key=lambda x: x["id"])
    return aus


def einfachstes(kandidaten):
    """Ein Beispiel, an dem sich die Frage schnell erfassen lässt: kurzer
    Vorgabetext, wenige Optionen."""
    def rang(x):
        t = (x.get("subject") or {}).get("text") or ""
        return (len(t.split()), len(t), len(x.get("options") or []), x["id"])
    return sorted(kandidaten, key=rang)[0]


def katalog(alle):
    alt = {}
    if KATALOG.exists():
        for e in json.loads(KATALOG.read_text(encoding="utf-8"))["questions"]:
            alt[e["id"]] = e

    gruppiert = {}
    for x in alle:
        gruppiert.setdefault(frage_id(x), []).append(x)

    fehlend = set(gruppiert) - set(TEXTE)
    if fehlend:
        raise SystemExit(f"Formulierung ohne Text: {sorted(fehlend)}")

    reihe = [i for _, ids in GRUPPEN for i in ids]
    assert set(reihe) == set(TEXTE), set(reihe) ^ set(TEXTE)

    aus = []
    for i in reihe:
        teil = gruppiert.get(i, [])
        de, en, wann = TEXTE[i]
        vor = alt.get(i, {})
        bsp = einfachstes(teil) if teil else None
        aus.append({
            "id": i,
            "de": vor.get("de", de),
            "en": vor.get("en", en),
            "question_type": teil[0]["question_type"] if teil else None,
            "task_type": sorted({x["task_type"] for x in teil}),
            "note": wann,
            "rules": sorted({x["rule"] for x in teil}, key=list(RULE).index),
            "lessons": [min(x["lesson"] for x in teil),
                        max(x["lesson"] for x in teil)] if teil else None,
            "count": len(teil),
            "example": bsp["id"] if bsp else None,
        })
    return aus, gruppiert


def schreibe_katalog(eintraege):
    KATALOG.write_text(json.dumps({
        "note": ("Die Fragetexte der App. Eine Aufgabe trägt keinen Text, "
                 "sondern nur ihre question_id; die Formulierung steht hier. "
                 "Bearbeitet werden die Felder de und en, alles andere ist "
                 "aus den Aufgaben abgeleitet und wird überschrieben."),
        "placeholders": PLATZHALTER,
        "rules": RULE,
        "questions": eintraege,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------- Übersicht
def frage_vorschau(text, x):
    t = text.replace("{rule}", RULE[x["rule"]])
    return t.replace("{sign}", (x.get("pattern") or "") if "{sign}" in t else "")


def beispiel_html(x):
    OPT = {"yes": "Ja", "no": "Nein", "start": "Anfang", "mid": "Mitte",
           "end": "Ende", "none": "kommt nicht vor", "-": "kein Muster"}
    teile = []
    subj = (x.get("subject") or {}).get("text")
    if subj and subj != "اختر":
        teile.append(f'<p class="ar subj">{html.escape(subj)}</p>')
    richtig = {a for a in (x.get("answer") or []) if isinstance(a, int)}
    if x["task_type"] == "mark_verse":
        marken = [html.escape(s) for s in (x.get("answer") or []) if isinstance(s, str)]
        teile.append('<p class="loesung">Antwort: ' +
                     (" · ".join(f'<span class="ar">{m}</span>' for m in marken)
                      or "kommt nicht vor") + "</p>")
    elif x["task_type"] == "matching":
        nach = {o["id"]: o["text"] for o in x["options"]}
        wort = {i["id"]: i["text"] for i in x["items"]}
        zeilen = "".join(
            f'<li><span class="ar">{html.escape(wort[p["item"]])}</span>'
            f'<span class="pfeil">→</span>'
            f'<span class="ar">{html.escape(OPT.get(nach[p["option"]], nach[p["option"]]))}</span></li>'
            for p in x["answer"])
        teile.append(f'<ul class="paare">{zeilen}</ul>')
    else:
        knoepfe = "".join(
            f'<li class="{"r" if o["id"] in richtig else ""}">'
            f'<span class="{"ar" if o["text"] not in OPT and not o["text"].isdigit() else ""}">'
            f'{html.escape(OPT.get(o["text"], o["text"]))}</span></li>'
            for o in x["options"])
        teile.append(f'<ul class="opts">{knoepfe}</ul>')
    quelle = (f'Sure {x["sura"]} : {x["verse"]}' if x["sura"] else "Einzelwort")
    teile.append(f'<p class="quelle">Aufgabe {x["id"]} · {quelle}</p>')
    return "".join(teile)


def seite(eintraege, gruppiert):
    nach_id = {e["id"]: e for e in eintraege}
    alle = {x["id"]: x for xs in gruppiert.values() for x in xs}
    karten = []
    for titel, ids in GRUPPEN:
        karten.append(f'<h2>{html.escape(titel)}</h2>')
        for i in ids:
            e, x = nach_id[i], alle[nach_id[i]["example"]]
            regeln = " · ".join(RULE[r] for r in e["rules"])
            a, b = e["lessons"]
            lek = f"Lektion {a}" if a == b else f"Lektion {a}–{b}"
            karten.append(f'''
<section class="karte" data-id="{i}">
  <header>
    <code class="kid">{i}</code>
    <span class="zahl">{e["count"]} Aufgaben</span>
  </header>
  <p class="wann">{html.escape(e["note"])}</p>
  <p class="gilt"><b>{html.escape(regeln)}</b> · {lek}</p>
  <label>Deutsch<textarea class="de" rows="2">{html.escape(e["de"])}</textarea></label>
  <label>English<textarea class="en" rows="2">{html.escape(e["en"])}</textarea></label>
  <div class="bsp">
    <p class="frage" data-vorlage="{html.escape(e["de"])}">{html.escape(frage_vorschau(e["de"], x))}</p>
    {beispiel_html(x)}
  </div>
</section>''')
    return KOPF + "\n".join(karten) + FUSS


KOPF = '''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="../icons/favicon.svg" type="image/svg+xml">
<link rel="icon" href="../icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="../icons/apple-touch-icon.png">
<meta name="theme-color" content="#1B2560">
<title>Fragestellungen bearbeiten</title>
<style>
@font-face{font-family:'Hafs';src:url('../fonts/hafs-uthmanic.woff2') format('woff2');font-display:swap}
:root{--ground:#F4F0EB;--surface:#FFFFFF;--surface-2:#E9E8F1;--surface-3:#F3E9DD;
 --ink:#363636;--ink-2:#6D6D6D;--ink-3:#9B9B9F;--line:#D5D4DF;--line-strong:#C1C0C9;
 --accent:#26247B;--accent-soft:#D0CCF0;--ok:#4E8A56;--ok-line:#63C36F;--ok-bg:#E9F1EE;
 --gold-soft:#E4DCC9;--radius:1rem;--pill:9999px;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
 -webkit-font-smoothing:antialiased}
.ar{font-family:'Hafs','Amiri',serif;direction:rtl;unicode-bidi:isolate}
.wrap{max-width:940px;margin:0 auto;padding:28px 22px 80px}
header.top{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;margin-bottom:8px}
h1{margin:0;font-size:20px}
.lead{color:var(--ink-2);max-width:62ch;margin:8px 0 0}
.lead code{background:var(--surface-2);border-radius:5px;padding:1px 5px;font-size:12.5px}
.werkzeug{position:sticky;top:0;z-index:5;display:flex;gap:9px;flex-wrap:wrap;align-items:center;
 margin:20px 0 26px;padding:11px 0;background:var(--ground);border-bottom:1px solid var(--line)}
button{font:inherit;cursor:pointer;border:1.5px solid var(--line);background:var(--surface);
 color:var(--ink);border-radius:var(--pill);padding:8px 16px;font-weight:600;font-size:13px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button:hover{border-color:var(--line-strong)}
.stand{color:var(--ink-3);font-size:12.5px;margin-left:auto}
h2{margin:34px 0 12px;font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3)}
.karte{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
 padding:16px 18px;margin-bottom:14px}
.karte header{display:flex;gap:12px;align-items:baseline}
.kid{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;font-weight:600;
 color:var(--accent);background:var(--accent-soft);border-radius:7px;padding:2px 9px}
.zahl{margin-left:auto;color:var(--ink-3);font-size:12px;font-variant-numeric:tabular-nums}
.wann{margin:10px 0 2px;color:var(--ink-2)}
.gilt{margin:0 0 12px;color:var(--ink-3);font-size:12.5px}
.gilt b{color:var(--ink-2);font-weight:600}
label{display:block;margin-bottom:9px;font-size:11px;font-weight:700;letter-spacing:.09em;
 text-transform:uppercase;color:var(--ink-3)}
textarea{display:block;width:100%;margin-top:5px;padding:9px 11px;border:1.5px solid var(--line);
 border-radius:10px;font-family:inherit;font-size:15px;line-height:1.45;
 color:var(--ink);background:var(--surface);resize:vertical}
textarea:focus{outline:2px solid var(--accent);outline-offset:-1px;border-color:var(--accent)}
.karte.geaendert{border-color:var(--accent)}
.karte.geaendert .kid::after{content:" · geändert";font-weight:400}
.bsp{margin-top:14px;padding:14px 16px;background:var(--surface-3);
 border:1px solid var(--gold-soft);border-radius:12px}
.frage{margin:0 0 10px;font-weight:600}
.subj{margin:6px 0 12px;font-size:25px;line-height:2;text-align:center}
.opts{list-style:none;display:flex;flex-wrap:wrap;gap:7px;margin:0;padding:0}
.opts li{border:1.5px solid var(--line);background:var(--surface);border-radius:10px;
 padding:6px 13px;font-size:14px}
.opts li .ar{font-size:19px}
.opts li.r{border-color:var(--ok-line);background:var(--ok-bg);color:var(--ok);font-weight:600}
.opts li.r::after{content:" ✓"}
.paare{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.paare li{display:flex;align-items:center;gap:10px;background:var(--surface);
 border:1px solid var(--line);border-radius:10px;padding:6px 12px}
.paare .ar{font-size:19px}
.pfeil{color:var(--ink-3)}
.loesung{margin:0;color:var(--ok);font-weight:600}
.loesung .ar{font-size:19px}
.quelle{margin:10px 0 0;color:var(--ink-3);font-size:11.5px}
dialog{border:1px solid var(--line);border-radius:var(--radius);padding:0;max-width:min(92vw,820px);width:100%}
dialog::backdrop{background:rgba(30,28,60,.34)}
dialog .inner{padding:18px 20px}
dialog textarea{height:56vh;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;line-height:1.5}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div>
    <h1>Fragestellungen bearbeiten</h1>
    <p class="lead">Jede Aufgabe trägt keinen Fragetext, sondern nur eine <code>question_id</code>.
    Die Formulierung steht hier — eine je Zeile, für alle Regeln zugleich.
    <code>{rule}</code> wird zur Regel der Aufgabe (Tafkheem, Qalqalah, Idgham, Ikhfa, Iqlab,
    Madd, Waqf), <code>{sign}</code> zum Halt-Zeichen. Die Beispiele zeigen, wie die Frage
    ankommt; die Vorschau ändert sich beim Tippen mit.</p>
  </div>
</header>
<div class="werkzeug">
  <button type="button" class="primary" id="kopieren">JSON kopieren</button>
  <button type="button" id="laden">JSON herunterladen</button>
  <button type="button" id="zeigen">JSON ansehen</button>
  <button type="button" id="zuruecksetzen">Änderungen verwerfen</button>
  <span class="stand" id="stand"></span>
</div>
'''

FUSS = '''
</div>

<dialog id="dlg"><div class="inner">
  <textarea id="roh" readonly></textarea>
  <p style="text-align:right;margin:12px 0 0"><button type="button" id="zu">Schließen</button></p>
</div></dialog>

<script>
"use strict";
const KARTEN = [...document.querySelectorAll(".karte")];
const SPEICHER = "tajweed.fragen";

KARTEN.forEach(k => {
  k.dataset.de = k.querySelector(".de").value;
  k.dataset.en = k.querySelector(".en").value;
});

function vorschau(k){
  const p = k.querySelector(".frage");
  const roh = k.querySelector(".de").value;
  /* Die Platzhalter werden wie im Beispiel gefüllt. */
  p.textContent = roh.replace("{rule}", p.dataset.regel).replace("{sign}", p.dataset.zeichen);
}
KARTEN.forEach(k => {
  const p = k.querySelector(".frage");
  const alt = k.dataset.de, neu = p.textContent;
  /* Aus Vorlage und gerendertem Text die eingesetzten Werte zurückgewinnen. */
  p.dataset.regel = werte(alt, neu, "{rule}");
  p.dataset.zeichen = werte(alt, neu, "{sign}");
});
function werte(vorlage, gerendert, platz){
  const i = vorlage.indexOf(platz);
  if (i < 0) return "";
  const vorn = vorlage.slice(0, i);
  const hinten = vorlage.slice(i + platz.length).replace(/\\{[a-z]+\\}/g, "");
  let rest = gerendert.slice(vorn.length);
  if (hinten) rest = rest.slice(0, rest.length - hinten.length);
  return rest;
}

function geaendert(){
  return KARTEN.filter(k => k.querySelector(".de").value !== k.dataset.de
                         || k.querySelector(".en").value !== k.dataset.en);
}
function stand(){
  const n = geaendert().length;
  document.getElementById("stand").textContent =
    n ? `${n} von ${KARTEN.length} geändert` : `${KARTEN.length} Fragestellungen, nichts geändert`;
  KARTEN.forEach(k => k.classList.toggle("geaendert",
    k.querySelector(".de").value !== k.dataset.de || k.querySelector(".en").value !== k.dataset.en));
}
function sichern(){
  const d = {};
  KARTEN.forEach(k => { d[k.dataset.id] = {de: k.querySelector(".de").value,
                                           en: k.querySelector(".en").value}; });
  try { localStorage.setItem(SPEICHER, JSON.stringify(d)); } catch(e){}
}
(function laden(){
  let d = null;
  try { d = JSON.parse(localStorage.getItem(SPEICHER) || "null"); } catch(e){}
  if (d) KARTEN.forEach(k => {
    const e = d[k.dataset.id];
    if (!e) return;
    k.querySelector(".de").value = e.de;
    k.querySelector(".en").value = e.en;
  });
})();

KARTEN.forEach(k => ["de","en"].forEach(f =>
  k.querySelector("." + f).addEventListener("input", () => {
    if (f === "de") vorschau(k);
    stand(); sichern();
  })));
KARTEN.forEach(vorschau);
stand();

function json(){
  const d = JSON.parse(JSON.stringify(KATALOG));
  const nach = Object.fromEntries(KARTEN.map(k => [k.dataset.id, k]));
  d.questions.forEach(q => {
    const k = nach[q.id];
    if (!k) return;
    q.de = k.querySelector(".de").value.trim();
    q.en = k.querySelector(".en").value.trim();
  });
  return JSON.stringify(d, null, 2) + "\\n";
}
document.getElementById("kopieren").addEventListener("click", async ev => {
  try { await navigator.clipboard.writeText(json());
        ev.target.textContent = "kopiert ✓";
        setTimeout(() => ev.target.textContent = "JSON kopieren", 1600); }
  catch(e){ document.getElementById("zeigen").click(); }
});
document.getElementById("laden").addEventListener("click", () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([json()], {type:"application/json"}));
  a.download = "questions.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
});
document.getElementById("zeigen").addEventListener("click", () => {
  document.getElementById("roh").value = json();
  document.getElementById("dlg").showModal();
});
document.getElementById("zu").addEventListener("click", () => document.getElementById("dlg").close());
document.getElementById("zuruecksetzen").addEventListener("click", () => {
  if (!confirm("Alle Änderungen verwerfen?")) return;
  KARTEN.forEach(k => { k.querySelector(".de").value = k.dataset.de;
                        k.querySelector(".en").value = k.dataset.en;
                        vorschau(k); });
  try { localStorage.removeItem(SPEICHER); } catch(e){}
  stand();
});
</script>
</body>
</html>
'''


def main() -> int:
    alle = aufgaben()
    eintraege, gruppiert = katalog(alle)
    schreibe_katalog(eintraege)
    SEITE.parent.mkdir(exist_ok=True)
    text = seite(eintraege, gruppiert)
    text = text.replace("</head>", "<script>const KATALOG = "
                        + json.dumps(json.loads(KATALOG.read_text(encoding="utf-8")),
                                     ensure_ascii=False)
                        + ";</script>\n</head>")
    SEITE.write_text(text, encoding="utf-8")
    print(f"{KATALOG}  {len(eintraege)} Fragestellungen, {sum(e['count'] for e in eintraege)} Aufgaben")
    print(f"{SEITE}  {SEITE.stat().st_size / 1024:.0f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
