"""
Regeneriert beide ICS-Dateien aus data/data.json:
  data/crazy-geese-alle-spiele-2026.ics    (alle Spiele)
  data/crazy-geese-heimspiele-2026.ics     (nur Spiele in Rohrbach)

Konventionen:
  - SUMMARY-Reihenfolge: GAST vs HEIM (Baseball-Konvention).
  - Suffix:
      "(HEIM)"        -> Crazy Geese sind formal Heim UND Spielort in Rohrbach
      "(in Rohrbach)" -> Crazy Geese sind formal Gast, Spielort aber Rohrbach
      kein Suffix     -> alle anderen
  - DESCRIPTION enthaelt die Phase und ggf. den Heim-Hinweis.
  - UID-Schema: cg-YYYY-MM-DD-HHMM@crazy-geese.at (stabil, bleibt zwischen
    Laeufen gleich, damit Kalender-Apps Updates erkennen).

Nutzung (aus dem Repo-Root):
    python scripts/generate_ics.py

Im Workflow nach scripts/scraper.py aufrufen, damit ICS automatisch nachgezogen
wird, wenn der Scraper Spiele aktualisiert hat.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "data.json"
ICS_ALL = REPO_ROOT / "data" / "crazy-geese-alle-spiele-2026.ics"
ICS_HOME = REPO_ROOT / "data" / "crazy-geese-heimspiele-2026.ics"

TEAM_FULL_NAME = "Rohrbach Crazy Geese"
TEAM_SHORT = "Crazy Geese"
HOME_VENUE_KEYWORD = "Geese Ballpark"


def main() -> int:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"FAIL: data.json nicht lesbar: {e}", file=sys.stderr)
        return 1

    # Nur zukuenftige Spiele in den Kalender. data.spiele.naechste enthaelt
    # alle ab heute (Re-Split im Scraper bewegt vergangene Spiele in
    # spiele.vergangene). Vergangene Spiele in einem Termin-Kalender bringen
    # Kalender-Apps nur durcheinander.
    games = list(data.get("spiele", {}).get("naechste", []))
    games = [g for g in games if g.get("datum") and g.get("zeit") and g.get("heim") and g.get("gast")]
    games.sort(key=lambda g: (g["datum"], g["zeit"]))

    home_games = [g for g in games if HOME_VENUE_KEYWORD in (g.get("ort") or "")]

    _write_ics(
        ICS_ALL,
        title="Crazy Geese – Alle Spiele 2026",
        events=[_event(g) for g in games],
    )
    _write_ics(
        ICS_HOME,
        title="Crazy Geese – Heimspiele 2026",
        events=[_event(g) for g in home_games],
    )

    print(f"OK: {ICS_ALL.name} ({len(games)} Events)")
    print(f"OK: {ICS_HOME.name} ({len(home_games)} Events)")
    return 0


def _event(game: dict) -> dict:
    """Baut die Event-Felder fuer ein Spiel."""
    datum = game["datum"]
    zeit = game["zeit"]
    heim = game["heim"]
    gast = game["gast"]
    ort = game.get("ort") or ""
    phase = game.get("phase") or ""

    # SUMMARY-Suffix nach Konvention
    in_rohrbach = HOME_VENUE_KEYWORD in ort
    geese_is_home = TEAM_FULL_NAME in heim or TEAM_SHORT in heim
    geese_is_away = TEAM_FULL_NAME in gast or TEAM_SHORT in gast

    if in_rohrbach and geese_is_home:
        suffix = " (HEIM)"
        desc_extra = "\\nHeimspiel – Eintritt frei!"
    elif in_rohrbach and geese_is_away:
        suffix = " (in Rohrbach)"
        desc_extra = "\\nSpielort verlegt nach Rohrbach – Eintritt frei!"
    else:
        suffix = ""
        desc_extra = ""

    # Kompakte Team-Anzeige: bei Geese den Kurznamen verwenden
    gast_short = _shorten(gast)
    heim_short = _shorten(heim)
    summary = f"⚾ {gast_short} vs {heim_short}{suffix}"

    description = f"Baseball Landesliga Ost"
    if phase:
        description += f" – {phase}"
    description += desc_extra

    # DTSTART/DTEND: 2,5 Stunden Spielzeit
    start = datetime.datetime.strptime(f"{datum} {zeit}", "%Y-%m-%d %H:%M")
    end = start + datetime.timedelta(hours=2, minutes=30)

    uid = f"cg-{datum}-{zeit.replace(':', '')}@crazy-geese.at"

    return {
        "dtstart": start.strftime("%Y%m%dT%H%M%S"),
        "dtend": end.strftime("%Y%m%dT%H%M%S"),
        "summary": summary,
        "location": _ics_escape(ort),
        "description": description,
        "uid": uid,
    }


def _shorten(name: str) -> str:
    """Gibt 'Crazy Geese' fuer alle Geese-Varianten, sonst den vollen Namen."""
    if TEAM_FULL_NAME in name or TEAM_SHORT in name:
        return TEAM_SHORT
    return name


def _ics_escape(value: str) -> str:
    """Escaping fuer ICS-Werte (LOCATION, DESCRIPTION)."""
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def _write_ics(path: pathlib.Path, title: str, events: list[dict]) -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Rohrbach Crazy Geese//Baseball//DE",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{title}",
        "X-WR-TIMEZONE:Europe/Vienna",
    ]
    for ev in events:
        lines.extend([
            "BEGIN:VEVENT",
            f"DTSTART;TZID=Europe/Vienna:{ev['dtstart']}",
            f"DTEND;TZID=Europe/Vienna:{ev['dtend']}",
            f"SUMMARY:{ev['summary']}",
            f"LOCATION:{ev['location']}",
            f"DESCRIPTION:{ev['description']}",
            f"UID:{ev['uid']}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    # ICS-Dateien sollen mit LF enden (RFC 5545 erwartet CRLF, aber unsere
    # bestehenden Files nutzen LF und Kalender-Apps sind tolerant).
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
