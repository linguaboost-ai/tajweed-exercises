# Aufgaben als JSON

Sieben Dateien, eine je Lektionsblock, zusammen 2037 Aufgaben:

| Datei | Lektionen | Aufgaben |
|---|---|---|
| `tafkheem.json` | 1–9 | 575 |
| `qalqala.json` | 10–14 | 319 |
| `idgham.json` | 15–21 | 288 |
| `ikhfa-idgham.json` | 22–26 | 294 |
| `iqlab.json` | 27–28 | 128 |
| `madd.json` | 29–34 | 257 |
| `waqf.json` | 35–40 | 176 |

Jede Datei ist ein JSON-Array von Aufgabenobjekten nach dem Tajweed Exercise
Authoring Guide, in der Feldreihenfolge des Guides. Zwei Abweichungen:

* Das interne Feld `src` ist nicht enthalten.
* Neu ist `spots` — die Zeichenspannen, an denen die Regel greift, damit ein
  Frontend die richtige Antwort im Wort oder Vers einfärben kann. Beschreibung
  in [`../docs/spots.md`](../docs/spots.md).

Neu erzeugen: `python3 tools/export_json.py index.html json`. Das Skript prüft
vorher die Prüfliste des Guides (eindeutige IDs, erlaubte Werte, question_type
passend zum task_type, Options-IDs, Antwortverweise, kein deutscher oder
englischer Text außer den festen Marken, Audionamen nach `<id>.wav`) und
schreibt nur, wenn nichts zu beanstanden ist.
