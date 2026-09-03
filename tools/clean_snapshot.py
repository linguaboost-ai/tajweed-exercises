#!/usr/bin/env python3
"""
Die hochgeladene Datei war ein im Browser gespeicherter Seitenzustand, kein
Auslieferungsstand: Sie enthielt den bereits gerenderten DOM (Filterpillen,
Trefferliste, Detailansicht) und ein eingeschleustes Stylesheet einer
Browser-Erweiterung. Beim Laden baute das Skript alles ein zweites Mal auf —
daher die doppelten Filterpillen.

Dieses Skript stellt den Ursprungszustand her:
  * Kommentar „saved from url" und Snapshot-Kopfzeilen entfernen
  * fremdes <style> (Werbeblocker) entfernen
  * die vom Skript befüllten Container wieder leeren
  * Anzeigezustände (Zähler, Schalterstellungen) zurücksetzen

Idempotent: ein zweiter Lauf findet nichts mehr zu tun.
"""
import re
import sys
from pathlib import Path

HTML = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")

# Container, die das Skript zur Laufzeit füllt -> müssen leer ausgeliefert werden
EMPTY_IDS = ["bank-rule", "bank-task", "list", "sheet", "summary", "flag-n"]
TAG = re.compile(r"<(/?)([a-zA-Z][\w-]*)\b[^>]*?(/?)>")


def element_span(html: str, elem_id: str):
    """(start_of_inner, end_of_inner) des Elements mit dieser id."""
    m = re.search(r'id="%s"[^>]*>' % re.escape(elem_id), html)
    if not m:
        return None
    open_tag = html.rfind("<", 0, m.start())
    name = re.match(r"<([a-zA-Z][\w-]*)", html[open_tag:]).group(1)
    depth, pos = 1, m.end()
    for t in TAG.finditer(html, m.end()):
        if t.group(2).lower() != name.lower() or t.group(3):
            continue
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return m.end(), t.start()
    return None


def main() -> int:
    src = HTML.read_text(encoding="utf-8")
    out, notes = src, []

    # 1) Snapshot-Kopf
    out = re.sub(r"<!-- saved from url=\([0-9]+\)[^>]*-->\n?", "", out, count=1)
    head_old = '<html lang="de"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
    if head_old in out:
        out = out.replace(head_old, '<html lang="de">\n<head>\n<meta charset="utf-8">', 1)
        notes.append("Kopfzeilen bereinigt")

    # 2a) Von Browser-Erweiterungen eingeschleuste Skripte
    out, n = re.subn(
        r'<script src="(?:chrome|moz)-extension://[^"]*"></script>\s*', "", out
    )
    if n:
        notes.append(f"{n} Skript(e) einer Browser-Erweiterung entfernt")

    # 2) Eingeschleustes Stylesheet: alles, was nicht die Themedatei der Seite ist
    def drop_foreign(m):
        block = m.group(0)
        return "" if "--ground" not in block and "@font-face" not in block else block

    before = out
    out = re.sub(r"<style>.*?</style>\s*", drop_foreign, out, flags=re.S)
    if out != before:
        notes.append(f"fremdes Stylesheet entfernt ({(len(before)-len(out))//1024} KB)")

    # 3) Gerenderte Inhalte aus den Containern nehmen
    for eid in EMPTY_IDS:
        span = element_span(out, eid)
        if span and span[1] > span[0]:
            notes.append(f"#{eid} geleert ({span[1]-span[0]} Zeichen)")
            out = out[: span[0]] + out[span[1] :]

    # 4) Anzeigezustände zurücksetzen
    resets = [
        (r'(<span class="tally" id="tally">).*?(</span>)', r"\1&ndash;\2"),
        (r'(<button type="button" id="prev"[^>]*?)\s*disabled=""', r"\1"),
        (r'(<button type="button" id="next"[^>]*?)\s*disabled=""', r"\1"),
        (r'(id="deck-toggle"[^>]*aria-expanded=")false(")', r"\1true\2"),
        (r'(<div class="deck)\s+folded(" id="deck")', r"\1\2"),
    ]
    for pat, rep in resets:
        out, n = re.subn(pat, rep, out, count=1)
        if n:
            notes.append("Anzeigezustand zurückgesetzt: " + pat.split('"')[1])

    if not notes:
        print("Nichts zu tun – Datei ist bereits im Auslieferungszustand.")
        return 0

    HTML.write_text(out, encoding="utf-8")
    for n in notes:
        print("  ✓", n)
    print(f"\n{HTML}: {len(src)//1024} KB → {len(out)//1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
