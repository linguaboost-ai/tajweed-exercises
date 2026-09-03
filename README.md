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

## Aufbau

    index.html   die Seite selbst (Daten und Hausschrift eingebettet)
    fonts/       Amiri Quran, nur für das Versnummern-Ornament
    tools/       Korrekturskripte, die auf index.html angewandt wurden

`tools/fix_ayah.py` ist idempotent und dokumentiert, was genau geändert wurde.
