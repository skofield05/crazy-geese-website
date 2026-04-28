"""
Schema- und Asset-Check fuer data/data.json.

Prueft:
  - Pflichtfelder im verein-, kontakt-, tabelle-, spiele-, softball-, blog-Block
  - Datums- und Zeit-Format (YYYY-MM-DD / HH:MM)
  - Eindeutigkeit von blog-slug, spielnr, Tabellen-Team-Namen
  - Ergebnis-Konsistenz (beide Seiten oder keine)
  - Cross-Check: jedes Spiel in data.json hat ein passendes Event in den ICS-Dateien
  - Heimspiele-ICS enthaelt alle Spiele mit Spielort "Geese Ballpark"

Nutzung (aus dem Repo-Root):
    python scripts/validate_data.py

Exitcode 0 = alles ok, 1 = Fehler gefunden.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "data.json"
ICS_ALL = REPO_ROOT / "data" / "crazy-geese-alle-spiele-2026.ics"
ICS_HOME = REPO_ROOT / "data" / "crazy-geese-heimspiele-2026.ics"

REQUIRED_POST_FIELDS = ("slug", "url", "titel", "datum")
REQUIRED_GAME_FIELDS = ("datum", "heim", "gast")
TIME_RX = re.compile(r"^\d{2}:\d{2}$")
HOME_VENUE_KEYWORD = "Geese Ballpark"
TEAM_NAME = "Crazy Geese"


def _is_valid_date(s: str) -> bool:
    try:
        datetime.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: data.json ist kein valides JSON: {e}")
        return 1

    _check_verein(data.get("verein"), errors, warnings)
    _check_kontakt(data.get("kontakt"), errors, warnings)
    _check_tabelle(data.get("tabelle"), errors, warnings)
    _check_softball(data.get("softball"), errors, warnings)
    _check_blog(data.get("blog"), errors, warnings)
    _check_spiele(data.get("spiele"), errors, warnings)
    _check_ics_sync(data.get("spiele"), errors, warnings)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")

    if errors:
        print(f"\n{len(errors)} Fehler, {len(warnings)} Warnungen.")
        return 1
    print(f"OK: data.json valide, {len(warnings)} Warnungen.")
    return 0


def _check_verein(verein: object, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(verein, dict):
        errors.append("verein-Block fehlt oder ist kein Objekt.")
        return
    for field in ("name", "saison", "website", "abf_url"):
        if not verein.get(field):
            errors.append(f"verein.{field} fehlt oder ist leer.")
    saison = verein.get("saison")
    if saison and not re.match(r"^\d{4}$", str(saison)):
        warnings.append(f"verein.saison '{saison}' – erwarte 4-stelliges Jahr.")


def _check_kontakt(kontakt: object, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(kontakt, dict):
        errors.append("kontakt-Block fehlt oder ist kein Objekt.")
        return
    email = kontakt.get("email")
    if not email or "@" not in str(email):
        errors.append("kontakt.email fehlt oder ist keine gueltige Adresse.")
    if "@crazy-geese.at" in str(email or ""):
        warnings.append(
            "kontakt.email verweist noch auf @crazy-geese.at – sollte crazygeese93@gmail.com sein."
        )
    ansp = kontakt.get("ansprechpartner")
    if ansp and not isinstance(ansp, dict):
        errors.append("kontakt.ansprechpartner muss ein Objekt sein.")


def _check_tabelle(tabelle: object, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(tabelle, dict):
        errors.append("tabelle-Block fehlt oder ist kein Objekt.")
        return
    teams = tabelle.get("teams", [])
    if not isinstance(teams, list):
        errors.append("tabelle.teams muss ein Array sein.")
        return
    if not teams:
        warnings.append("tabelle.teams ist leer – wahrscheinlich Vorsaison oder Scraper-Bug.")
        return

    seen_names: set[str] = set()
    has_geese = False
    for i, team in enumerate(teams):
        where = f"tabelle.teams[{i}]"
        if not isinstance(team, dict):
            errors.append(f"{where} muss ein Objekt sein.")
            continue
        for field in ("rang", "name", "siege", "niederlagen"):
            if team.get(field) is None:
                errors.append(f"{where}.{field} fehlt.")
        name = team.get("name", "")
        if name in seen_names:
            errors.append(f"{where}.name '{name}' ist nicht eindeutig.")
        seen_names.add(name)
        if TEAM_NAME in name:
            has_geese = True

    if not has_geese:
        errors.append("tabelle.teams enthaelt keinen 'Crazy Geese'-Eintrag.")

    stand = tabelle.get("stand")
    if stand and not _is_valid_date(stand):
        errors.append(f"tabelle.stand '{stand}' – erwarte YYYY-MM-DD.")


def _check_softball(softball: object, errors: list[str], warnings: list[str]) -> None:
    if softball is None:
        return  # optional
    if not isinstance(softball, dict):
        errors.append("softball-Block muss ein Objekt sein.")
        return
    termine = softball.get("naechste_termine", [])
    if not isinstance(termine, list):
        errors.append("softball.naechste_termine muss ein Array sein.")
        return
    for i, t in enumerate(termine):
        where = f"softball.naechste_termine[{i}]"
        if not isinstance(t, dict):
            errors.append(f"{where} muss ein Objekt sein.")
            continue
        if not t.get("datum"):
            errors.append(f"{where}.datum fehlt.")
        elif not _is_valid_date(t["datum"]):
            errors.append(f"{where}.datum '{t['datum']}' – erwarte YYYY-MM-DD.")
        zeit = t.get("zeit")
        if zeit and not TIME_RX.match(zeit):
            errors.append(f"{where}.zeit '{zeit}' – erwarte HH:MM.")


def _check_blog(blog: object, errors: list[str], warnings: list[str]) -> None:
    if blog is None:
        warnings.append("blog-Key fehlt in data.json (kein Blog konfiguriert).")
        return
    if not isinstance(blog, dict):
        errors.append("blog muss ein Objekt sein.")
        return

    posts = blog.get("posts", [])
    if not isinstance(posts, list):
        errors.append("blog.posts muss ein Array sein.")
        return

    slugs: set[str] = set()
    for i, post in enumerate(posts):
        where = f"blog.posts[{i}]"
        if not isinstance(post, dict):
            errors.append(f"{where} muss ein Objekt sein.")
            continue

        for field in REQUIRED_POST_FIELDS:
            if not post.get(field):
                errors.append(f"{where}.{field} fehlt oder ist leer.")

        slug = post.get("slug")
        if slug:
            if slug in slugs:
                errors.append(f"{where}.slug '{slug}' ist nicht eindeutig.")
            slugs.add(slug)

        datum = post.get("datum")
        if datum and not _is_valid_date(datum):
            errors.append(f"{where}.datum '{datum}' – erwarte gueltiges YYYY-MM-DD.")

        for path_field in ("url", "cover"):
            p = post.get(path_field)
            if not p:
                continue
            full = REPO_ROOT / p
            if not full.exists():
                errors.append(f"{where}.{path_field} -> {p} existiert nicht.")

        if post.get("cover") and not post.get("cover_alt"):
            warnings.append(f"{where}: cover vorhanden, aber cover_alt fehlt (Barrierefreiheit).")


def _check_spiele(spiele: object, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(spiele, dict):
        return
    seen_spielnr: dict[str, str] = {}
    for bucket in ("naechste", "vergangene"):
        games = spiele.get(bucket, [])
        if not isinstance(games, list):
            errors.append(f"spiele.{bucket} muss ein Array sein.")
            continue
        for i, g in enumerate(games):
            where = f"spiele.{bucket}[{i}]"
            if not isinstance(g, dict):
                errors.append(f"{where} muss ein Objekt sein.")
                continue

            for field in REQUIRED_GAME_FIELDS:
                if not g.get(field):
                    errors.append(f"{where}.{field} fehlt.")

            datum = g.get("datum")
            if datum and not _is_valid_date(datum):
                errors.append(f"{where}.datum '{datum}' – erwarte gueltiges YYYY-MM-DD.")

            zeit = g.get("zeit")
            if zeit and not TIME_RX.match(zeit):
                errors.append(f"{where}.zeit '{zeit}' – erwarte HH:MM.")

            spielnr = g.get("spielnr")
            if spielnr:
                if spielnr in seen_spielnr:
                    errors.append(
                        f"{where}.spielnr '{spielnr}' kollidiert mit {seen_spielnr[spielnr]}."
                    )
                seen_spielnr[spielnr] = where

            erg_h = g.get("ergebnis_heim")
            erg_g = g.get("ergebnis_gast")
            if (erg_h is None) != (erg_g is None):
                errors.append(
                    f"{where}: ergebnis_heim und ergebnis_gast muessen entweder beide gesetzt "
                    f"oder beide null sein (heim={erg_h}, gast={erg_g})."
                )

            # Vergangene Spiele sollten ein Ergebnis haben (ausser Spiel ist heute aber
            # noch nicht gespielt – akzeptable Lockerung).
            if bucket == "vergangene" and erg_h is None:
                warnings.append(f"{where}: vergangenes Spiel ohne Ergebnis.")
            if bucket == "naechste" and erg_h is not None:
                warnings.append(f"{where}: zukuenftiges Spiel hat schon ein Ergebnis – ABF-Platzhalter?")


def _check_ics_sync(spiele: object, errors: list[str], warnings: list[str]) -> None:
    """Pruefe, ob beide ICS-Dateien zu den Spielen in data.json passen."""
    if not isinstance(spiele, dict):
        return
    games = list(spiele.get("naechste", [])) + list(spiele.get("vergangene", []))
    if not games:
        return

    # Erwartete DTSTARTs aus data.json (ohne Sekunden, mit Sekunden-Suffix wie ICS)
    expected_dts: set[str] = set()
    expected_home_dts: set[str] = set()
    for g in games:
        datum = g.get("datum", "")
        zeit = g.get("zeit", "")
        if not datum or not zeit:
            continue
        dt = f"{datum.replace('-', '')}T{zeit.replace(':', '')}00"
        expected_dts.add(dt)
        ort = g.get("ort", "") or ""
        if HOME_VENUE_KEYWORD in ort:
            expected_home_dts.add(dt)

    _check_one_ics(ICS_ALL, expected_dts, "alle-spiele", errors, warnings)
    _check_one_ics(ICS_HOME, expected_home_dts, "heimspiele", errors, warnings)


def _check_one_ics(
    path: pathlib.Path, expected_dts: set[str], label: str,
    errors: list[str], warnings: list[str],
) -> None:
    if not path.exists():
        errors.append(f"ICS '{path.name}' fehlt.")
        return
    text = path.read_text(encoding="utf-8")
    actual_dts = set(re.findall(r"DTSTART;TZID=Europe/Vienna:(\S+)", text))

    missing = expected_dts - actual_dts
    extra = actual_dts - expected_dts

    for dt in sorted(missing):
        errors.append(f"{label}-ICS fehlt Event fuer {dt} (in data.json vorhanden).")
    for dt in sorted(extra):
        errors.append(f"{label}-ICS hat extra Event {dt} (nicht in data.json).")

    # UID-Eindeutigkeit
    uids = re.findall(r"UID:(\S+)", text)
    dups = {u for u in uids if uids.count(u) > 1}
    for u in sorted(dups):
        errors.append(f"{label}-ICS hat doppelte UID: {u}.")


if __name__ == "__main__":
    sys.exit(main())
