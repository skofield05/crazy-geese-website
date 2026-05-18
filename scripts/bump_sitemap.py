"""
Bumpt das `<lastmod>` von dynamisch aktualisierten Seiten in sitemap.xml
auf das aktuelle Datum (Wien-Zeit).

Aufgerufen vom update-standings.yml-Workflow nach erfolgreichem Scrape,
damit Crawler die Standings-/Spielplan-Aenderungen mitbekommen.

Statische Seiten (kontakt, nachwuchs, was-ist-baseball, archiv, posts/*)
bleiben unangetastet – die werden separat gepflegt.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SITEMAP_PATH = Path(__file__).resolve().parent.parent / "sitemap.xml"
TZ_VIENNA = ZoneInfo("Europe/Vienna")

# URLs, die durch Scraper-Updates ihren Inhalt aendern.
# /         -> Landing zeigt naechstes Spiel + Tabelle aus data.json
# /baseball -> Komplette Spielliste + Schema.org SportsEvent aus data.json
DYNAMIC_URLS = {
    "https://crazy-geese.at/",
    "https://crazy-geese.at/baseball.html",
}


def main() -> int:
    if not SITEMAP_PATH.exists():
        print(f"[FEHLER] {SITEMAP_PATH} nicht gefunden")
        return 1

    today = datetime.now(TZ_VIENNA).strftime("%Y-%m-%d")
    xml = SITEMAP_PATH.read_text(encoding="utf-8")

    # Pro <url>-Block: wenn die <loc> in DYNAMIC_URLS, das <lastmod> ersetzen.
    url_block_rx = re.compile(
        r"(<url>\s*<loc>([^<]+)</loc>\s*<lastmod>)([^<]+)(</lastmod>)",
        re.DOTALL,
    )
    changed = 0

    def replace(m: re.Match) -> str:
        nonlocal changed
        loc = m.group(2).strip()
        if loc in DYNAMIC_URLS and m.group(3) != today:
            changed += 1
            return f"{m.group(1)}{today}{m.group(4)}"
        return m.group(0)

    new_xml = url_block_rx.sub(replace, xml)
    if changed == 0:
        print(f"[OK] sitemap.xml bereits auf {today} oder keine dynamischen URLs gefunden")
        return 0

    SITEMAP_PATH.write_text(new_xml, encoding="utf-8")
    print(f"[OK] sitemap.xml: {changed} <lastmod> auf {today} gebumpt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
