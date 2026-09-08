# Antwortstellen im Datensatz („spots")

Der Authoring Guide beschreibt, **was** die richtige Antwort ist — eine Zahl,
ein Vokal, ein Ja, eine Options-ID. Er beschreibt nicht, **wo** im Wort oder im
Vers die Regel greift. Für die Zählaufgaben („Wie oft kommt Tafchīm vor?") und
die Ja/Nein-Aufgaben ließe sich die Antwort im Frontend deshalb bisher nicht
zeigen; nur die Markieraufgaben nennen die Stellen selbst, weil ihr Schlüssel
aus Textstücken besteht.

Damit jede Aufgabe ihre Antwort im Text zeigen kann, trägt jeder Text seine
Fundstellen jetzt selbst.

## Das Feld

`spots` steht neben `text` — im `subject`, in jeder `option` und in jedem
`item`. Es ist eine Liste von Zeichenspannen in **genau dem Text, an dem es
hängt**:

```json
"subject": {
  "text": "يَضِيقُ",
  "spots": [
    { "start": 0, "end": 3, "text": "يَضِ" },
    { "start": 5, "end": 7, "text": "قُ" }
  ],
  "audio": "290.wav"
}
```

* `start` und `end` sind Zeichenpositionen, halboffen wie `String.prototype.slice`.
* Es gilt immer `text.slice(start, end) === spot.text`. Die Seite prüft das beim
  Laden; ein Verstoß erscheint als Auffälligkeit.
* Der Datensatz enthält keine Zeichen außerhalb der BMP. Zeichen, Codepoint und
  UTF-16-Einheit sind also dasselbe — die Werte stimmen in JavaScript, Python
  und Swift überein.
* Die Spannen sind aufsteigend sortiert und überschneidungsfrei; angrenzende
  Stellen sind zusammengefasst.
* Eine Spanne umfasst den Buchstaben **mit seinen Harakat** (`ضِ`, nicht `ض`),
  bei Regeln über die Wortgrenze auch beide Wörter (`أَفَرَءَيْتُم مَّا`).
* Fehlt `spots`, gibt es an diesem Text nichts zu markieren — bei den 403
  Aufgaben mit dem Schlüssel „kommt nicht vor" ist genau das die Antwort.

Ein Frontend braucht damit nur:

```js
function markiere(text, spots){
  let out = "", cur = 0;
  for (const s of spots || []){
    out += esc(text.slice(cur, s.start)) + '<mark>' + esc(s.text) + '</mark>';
    cur = s.end;
  }
  return out + esc(text.slice(cur));
}
```

## Wo die Stellen hängen

| Aufgabentyp | Stellen im `subject` | Stellen in `options` / `items` |
|---|---|---|
| yes_no, select_count, select, select_position | die Fundstellen im Wort/Vers | – |
| mark_verse | die Spannen aus dem Antwortschlüssel | – |
| match | der Auslöser im Vorgabewort (`كَانَتْ` → `تْ`) | die Stelle im jeweiligen Wort |
| matching | – (kein Vorgabewort) | die Stelle im jeweiligen Wort |

Bei `match` entsteht die Regel erst im Zusammenspiel: das Vorgabewort trägt den
auslösenden Buchstaben, jede richtige Option die Stelle in sich selbst.

## Wie die Stellen hergeleitet sind

Nicht aus dem `pattern` — das ist eine Anzeigehilfe für den Titel und an
einigen Stellen ungenau —, sondern aus der Regel selbst:

* **Qalqala** aus dem Sukūn im Wort bzw. dem Wortende vor der Versnummer.
* **Idghām, Ichfāʾ, Iqlāb** aus `tools/nun_rules.py`.
* **Waqf** aus den Halt-Zeichen; bei den Markieraufgaben aus dem Schlüssel.
* **Tafchīm** aus den Buchstaben der bis dahin unterrichteten Lektionen
  (1 ق, 2 ط, 3 خ, 4 غ, 5 ض, 6 ظ, 7 ص, 8 ر, 9 das Lām in „Allāh"), das Rā nach
  seinem Vokal.
* **Madd** aus dem Schriftbild: Dehnungsbuchstabe mit Hamza im Wort
  (muttaṣil), am Wortende vor einem Hamza (munfaṣil), vor Shadda oder Sukūn
  (lāzim), und das Hāʾ der Ṣila vor einem Hamza.

Anschließend wird jede Herleitung gegen den Antwortschlüssel geprüft: die
Anzahl bei den Zählaufgaben, Ja/Nein, die Lage im Wort, die Vokale, die
markierten Wörter. Geschrieben wird nur, was diese Probe besteht.

Stand: 1108 Vorgabetexte geprüft, 403 bewusst leer, 249 nicht gegenprüfbar
(dort zählt die Regelherleitung), 0 offen. Dazu 1032 Optionen und Wortpaare.

Die Probe hat zwölf Aufgaben mit unvollständigem Schlüssel gefunden — siehe den
Commit „Antwortstellen: jede Aufgabe bringt ihre Fundstellen mit".

## Erzeugt von

`tools/add_spots.py` (idempotent, schreibt in `index.html`),
`tools/export_json.py` (schreibt die sieben JSON-Dateien und prüft sie gegen
den Authoring Guide).
