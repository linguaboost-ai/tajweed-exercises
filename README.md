# Tajwīd Aufgabenbrowser

Statische Seite (eine `index.html`) zum Durchsehen der Tajwīd-Übungsaufgaben.
Deployment über Vercel, direkt aus diesem Repository.

## Korrekturen gegenüber der Fassung auf übung.qsk-methode.de

1. **Versnummern.** Indische Ziffern am Wortende (z. B. `أَحَدٌ١`) wurden wie
   gewöhnliche Ziffern gesetzt. Sie sind aber Versnummern und gehören in die
   verzierte Kartusche des Mushaf. Umgesetzt über `U+06DD` (ARABIC END OF AYAH)
   direkt vor der Ziffer, plus Leerzeichen zwischen Wort und Nummer.
   Die Kartusche kommt aus *Amiri Quran* (`fonts/`, SIL OFL), der übrige
   arabische Text bleibt in der eingebetteten Hausschrift.

2. **Qalqala: unvollständige Antwortschlüssel.** Gefragt ist der Vokal *vor*
   dem Qalqala-Buchstaben. Bei Versen mit mehreren Fundstellen war nur die
   erste als richtig markiert; die Stelle am Versende (Qalqala beim Anhalten)
   fehlte. 11 Aufgaben korrigiert, hergeleitet aus dem Verstext —
   siehe `docs/qalqala-korrektur.md`.

3. **Versnummer am Versende.** Aufgaben, die einen ganzen Vers zeigen, tragen
   jetzt die Versnummer in der Kartusche (855 Aufgaben). Aufgaben, die nur
   einen Ausschnitt zeigen, bekommen keine — dort endet der Text nicht am
   Versende. Siehe `docs/versnummern.md`.

4. **Qalqala am Versende.** Beim Anhalten verliert der Endbuchstabe seinen
   Vokal — dort entsteht Qalqala kubrā. Angehalten wird am Versende, und das
   ist an der Versnummer zu erkennen; steht der Text nicht am Versende, wird
   mit allen Harakat gelesen und die Stelle zählt nicht. Zwei Aufgaben ließen
   die Stelle aus (735, 831), siehe `docs/qalqala-versende.md`. Nach dieser
   Regel decken sich alle 279 auswertbaren Qalqala-Antwortschlüssel mit dem
   Text — geprüft über `tools/fix_qalqala_answers.py` und
   `tools/fix_qalqala_counts.py`.

5. **Falsch beschriftete Regel bei Idgham / Ikhfāʾ / Iqlāb.** Die Frage im
   Titel entsteht aus dem Feld `rule`. In Lektion 24/25 stand dort „ikhfa",
   obwohl die Fundstellen (م مّ, ن مّ, ٌ مّ …) ein Idgham sind, in Lektion 27/28
   ebenso, obwohl ن ب ein Iqlāb ist. 63 Aufgaben umbeschriftet; dazu 29
   Antworten und 14 Muster berichtigt, weil Fundstellen fehlten.
   Ausgewertet mit `tools/nun_rules.py`, siehe `docs/idgham-ikhfa-iqlab.md`.

6. **Antwortmöglichkeit „kommt nicht vor".** Aufgaben nach Vokal, Stelle oder
   auslösendem Buchstaben setzten voraus, dass die Regel überhaupt vorkommt.
   Alle 485 Aufgaben dieser Fragetypen haben die Option jetzt; bei 1611 und
   1643 (Izhār, kein Ichfāʾ) ist sie die richtige Antwort. 20 Behelfsoptionen
   („Keine", bei 1377 sogar Ja/Nein) sind darin aufgegangen.

7. **Getauschte Verse in den Idgham-Lektionen.** Der Generator zählte in
   Lektion 15–21 nur die Idgham-Art der jeweiligen Lektion; bei elf Aufgaben
   passte die Zahl deshalb nicht zum Text. Sie haben einen anderen Vers
   gleicher Länge und Wortzahl bekommen, in dem nur Idgham aus der laufenden
   oder einer früheren Lektion vorkommt. Siehe
   `docs/idgham-verse-getauscht.md`; **die Tonaufnahmen dieser elf Aufgaben
   müssen neu eingesprochen werden.**

8. **Fragestellung beim Madd.** Der Kurs behandelt den natürlichen Langvokal
   nicht als eigenes Thema — streng genommen ist قَالَ ein Madd ṭabīʿī, im Kurs
   zählt es nicht als Madd. Die Frage „Enthält dieses Wort ein Madd?" stand
   damit im Widerspruch zur hinterlegten Antwort „nein". Alle 257 Aufgaben der
   Lektionen 29–34 fragen jetzt nach der Dehnung über zwei Einheiten hinaus.
   Die Antwortschlüssel bleiben unverändert — sie waren schon so gesetzt.

9. **Zuordnungsfragen.** Der Fragetyp „Welche Wörter enthalten ein …?" deckt
   zwei Bauarten ab: mit Vorgabewort ist die *Verbindung* gemeint („Welche der
   folgenden Wörter bilden mit diesem ein …?"), ohne es das Wort für sich. Dazu 1378 (war unbrauchbar),
   1619, 1624 und die ausgelassenen Antworten in 984, 1577, 1587. „Keine" stand
   bisher nur in den 37 Aufgaben zur Auswahl, in denen es auch die Antwort war —
   jetzt überall.

## Aufbau

    index.html   die Seite selbst (Daten und Hausschrift eingebettet)
    fonts/       Amiri Quran, nur für das Versnummern-Ornament
    tools/       Korrekturskripte, die auf index.html angewandt wurden
    docs/        Begründung der inhaltlichen Korrekturen

Alle Skripte in `tools/` sind idempotent und dokumentieren im Kopfkommentar,
was genau sie ändern. `tools/add_verse_numbers.py` gleicht die Aufgabentexte
mit dem Korantext ab (`quran-json`, Tanzil/Uthmani).

## Deployment

Vercel-Projekt `tajweed-exercises` (Team „Linguaboost AI's projects"), verknüpft
mit diesem Repository. Jeder Push auf den Produktionszweig veröffentlicht die
Seite neu; der alte Pfad `/tajweed/tajweed-exercises.html` wird auf `/` geleitet.
