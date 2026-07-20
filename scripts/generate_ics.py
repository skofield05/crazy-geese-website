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
  - UID-Schema: cg-<spielnr>@crazy-geese.at (z.B. "cg-1234@crazy-geese.at").
    spielnr ist die stabile ABF-ID; damit erkennen Kalender-Apps Termin-
    Verlegungen als Update statt als neues Event. Nur bei fehlender spielnr
    fallback auf altes Schema cg-YYYY-MM-DD-HHMM@crazy-geese.at.

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
    # Verschobene Spiele (status "verschoben") haben keinen gueltigen Termin mehr
    # und gehoeren nicht in den Kalender, sonst zeigen Kalender-Apps ein
    # Phantom-Event am alten Datum.
    games = [
        g for g in games
        if g.get("datum") and g.get("zeit") and g.get("heim") and g.get("gast")
        and g.get("status") != "verschoben"
    ]
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

    # Kompakte Team-Anzeige: bei Geese den Kurznamen verwenden.
    # Team-Namen ICS-escapen (Komma/Semikolon/Backslash sind in ICS Wert-Trenner
    # – ein Name wie "Team, Wien" wuerde die SUMMARY-Zeile sonst zerlegen).
    # `suffix` und die "Baseball Landesliga Ost"-Literale sind konstant und
    # enthalten keine Sonderzeichen.
    gast_short = _ics_escape(_shorten(gast))
    heim_short = _ics_escape(_shorten(heim))
    summary = f"⚾ {gast_short} vs {heim_short}{suffix}"

    # phase escapen; desc_extra bewusst NICHT – es enthaelt literale "\n"-
    # Zeilenumbrueche (ICS-Escape-Sequenz), die _ics_escape durch das
    # Backslash-Doubling ("\\" -> "\\\\") zerstoeren wuerde.
    description = "Baseball Landesliga Ost"
    if phase:
        description += f" – {_ics_escape(phase)}"
    description += desc_extra

    # DTSTART/DTEND: 2,5 Stunden Spielzeit
    start = datetime.datetime.strptime(f"{datum} {zeit}", "%Y-%m-%d %H:%M")
    end = start + datetime.timedelta(hours=2, minutes=30)

    # UID stabil ueber Verlegungen: spielnr ist die ABF-ID, die bleibt gleich
    # auch wenn Datum/Zeit/Ort sich aendern. Fallback nur fuer Spiele die
    # (entgegen validate_data.py) keine spielnr haben.
    spielnr = (game.get("spielnr") or "").lstrip("#").strip()
    if spielnr:
        uid = f"cg-{spielnr}@crazy-geese.at"
    else:
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


# Standard-VTIMEZONE fuer Europe/Vienna (CET/CEST) mit der EU-weiten DST-Regel.
_VTIMEZONE_VIENNA = [
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Vienna",
    "BEGIN:DAYLIGHT",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "TZNAME:CEST",
    "DTSTART:19700329T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "TZNAME:CET",
    "DTSTART:19701025T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "END:VTIMEZONE",
]


def _write_ics(path: pathlib.Path, title: str, events: list[dict]) -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Rohrbach Crazy Geese//Baseball//DE",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{title}",
        "X-WR-TIMEZONE:Europe/Vienna",
    ]
    # VTIMEZONE-Definition fuer die per DTSTART;TZID=Europe/Vienna referenzierte
    # Zeitzone. Google/Apple loesen den Olson-Namen zwar auch ohne auf, strikte
    # Parser (aeltere Outlook-Versionen) brauchen die explizite Definition, sonst
    # koennen sie die Uhrzeit falsch interpretieren. EU-DST-Regel: MESZ vom
    # letzten So im Maerz 02:00 bis letzten So im Oktober 03:00.
    lines.extend(_VTIMEZONE_VIENNA)
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
