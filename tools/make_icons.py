#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt das Logo von German Method als Favicon: ein G mit zwei Punkten
darüber, weiß auf navyblau. Die Punkte sind Rauten, wie sie die Rohrfeder
setzt — daher der orientalische Anklang; runde Punkte lesen sich schnell als
deutscher Umlaut.

    icons/favicon.svg        gerundetes Quadrat, für den Browser-Tab
    icons/mark-square.svg    randabfallend, Grundlage für die Bilddateien
    icons/favicon-16.png     ... -32, -48 für Browser ohne SVG-Favicon
    icons/apple-touch-icon.png (180)   iOS rundet selbst, deshalb quadratisch
    icons/icon-192.png, icon-512.png   für das Web-App-Manifest
    favicon.ico              16/32/48 in einem Behälter, für alte Browser

Die PNG kommen aus Chromium (Playwright) — auf dieser Maschine gibt es kein
ImageMagick und kein cairosvg. Die .ico schreibt das Skript selbst; seit
Vista dürfen die Einzelbilder darin PNG sein.

Aufruf:  python3 tools/make_icons.py
"""
import math
import struct
from pathlib import Path

NAVY = "#1B2560"
INK = "#FFFFFF"
OUT = Path("icons")


def g_path(cx=256.0, cy=300.0, r=120.0):
    """Groteskes G: fast geschlossener Kreis, rechts der Querbalken."""
    def pt(grad):
        a = math.radians(grad)
        return cx + r * math.cos(a), cy + r * math.sin(a)
    s, e = pt(-38), pt(2)
    return (f"M {s[0]:.1f} {s[1]:.1f} A {r} {r} 0 1 0 {e[0]:.1f} {e[1]:.1f} "
            f"L {cx - 4:.1f} {e[1]:.1f}")


def raute(cx, cy, rr, rund=5):
    return (f'<path d="M {cx} {cy - rr} L {cx + rr} {cy} L {cx} {cy + rr} '
            f'L {cx - rr} {cy} Z" fill="{INK}" stroke="{INK}" '
            f'stroke-width="{rund}" stroke-linejoin="round"/>')


def svg(rx):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="German Method">
  <title>German Method</title>
  <rect width="512" height="512"{f' rx="{rx}"' if rx else ''} fill="{NAVY}"/>
  <path d="{g_path()}" fill="none" stroke="{INK}" stroke-width="48" stroke-linecap="butt"/>
  {raute(220, 100, 25)}
  {raute(292, 100, 25)}
</svg>
'''


def render(seite, pfad, quelle, groesse):
    """Das SVG steht im Dokument selbst — als Bildquelle müsste es erst
    umständlich kodiert werden."""
    seite.set_viewport_size({"width": groesse, "height": groesse})
    seite.set_content(
        "<style>html,body{margin:0;background:transparent}"
        f"svg{{display:block;width:{groesse}px;height:{groesse}px}}</style>"
        + quelle)
    seite.wait_for_timeout(60)
    seite.screenshot(path=str(pfad), omit_background=True)


def ico(pfad, bilder):
    """ICONDIR + je ein Eintrag, die Bilder selbst als PNG darin."""
    kopf = struct.pack("<HHH", 0, 1, len(bilder))
    off = len(kopf) + 16 * len(bilder)
    eintraege, daten = b"", b""
    for n, roh in bilder:
        eintraege += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32,
                                 len(roh), off)
        daten += roh
        off += len(roh)
    pfad.write_bytes(kopf + eintraege + daten)


def main() -> int:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(exist_ok=True)
    rund, eckig = svg(112), svg(0)
    (OUT / "favicon.svg").write_text(rund, encoding="utf-8")
    (OUT / "mark-square.svg").write_text(eckig, encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox"])
        seite = browser.new_page()
        for n in (16, 32, 48):
            render(seite, OUT / f"favicon-{n}.png", rund, n)
        render(seite, OUT / "apple-touch-icon.png", eckig, 180)
        for n in (192, 512):
            render(seite, OUT / f"icon-{n}.png", eckig, n)
        browser.close()

    ico(Path("favicon.ico"),
        [(n, (OUT / f"favicon-{n}.png").read_bytes()) for n in (16, 32, 48)])

    for f in sorted(OUT.iterdir()) + [Path("favicon.ico")]:
        print(f"{f}  {f.stat().st_size:>7} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
