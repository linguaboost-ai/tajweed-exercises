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

4. **Qalqala am Vers-/Wortende.** Beim Anhalten verliert der Endbuchstabe
   seinen Vokal — dort entsteht Qalqala kubrā. Der Datensatz zählt das meist
   schon mit; drei Aufgaben taten es nicht (735, 777, 831). Alle 121 Zähl- und
   Ja/Nein-Aufgaben gegen den Text geprüft, siehe `docs/qalqala-versende.md`.

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
