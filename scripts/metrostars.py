"""
Fallback-Scraper fuer viennametrostars.at-Statistikseite.

Wird vom Haupt-Scraper genutzt:
  - als Fallback fuer Tabelle und Spiele, wenn die ABF-Seite leere Daten
    liefert (transiente ABF-Ausfaelle / Markup-Aenderungen)
  - zur Verifizierung: bei Abweichung zwischen ABF und Metrostars logged
    der Scraper eine Warnung, damit der Maintainer es sieht

Quelle: https://www.viennametrostars.at/de/Ligastatistiken/l2s__550.htm
Die Seite ist server-rendered HTML mit zwei Tables:
  Table[0] = Standings (Rank, Team, W, L, PCT, GB, ...)
  Table[1] = Games (Datum, Heim, Awayteam, Umpires, Scorer, Ergebnis)

Kein Playwright noetig – plain urllib + Regex reicht.

HINWEIS: Bei neuer Saison muss METROSTARS_URL angepasst werden (Liga-ID
im Pfad-Suffix l2s__NNN.htm).
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request


METROSTARS_URL = "https://www.viennametrostars.at/de/Ligastatistiken/l2s__550.htm"
USER_AGENT = "Mozilla/5.0 (compatible; Crazy-Geese-Scraper; +https://crazy-geese.at)"

_DATE_RX = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4}) (\d{2}:\d{2})$")
_SCORE_RX = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
_RANK_RX = re.compile(r"^(\d+)\.?$")


def fetch_html(timeout: int = 30) -> str | None:
    """Holt das HTML der Statistik-Seite. None bei Netzwerkfehler."""
    req = urllib.request.Request(METROSTARS_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"      [WARN] Metrostars-Fetch fehlgeschlagen: {e}")
        return None


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _split_tables(html: str) -> list[str]:
    return re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL)


def _split_rows(table_html: str) -> list[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)


def _split_cells(row_html: str) -> list[str]:
    return re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row_html, re.DOTALL)


def parse_standings(html: str, canonicalize=None) -> list[dict]:
    """
    Parsed Tabelle aus dem HTML. canonicalize ist optional ein Callable, das
    Teamnamen auf den kanonischen Wortlaut mappt (z.B. scraper.canonical_team_name).
    """
    tables = _split_tables(html)
    if not tables:
        return []

    teams: list[dict] = []
    for row in _split_rows(tables[0]):
        cells = [_strip_tags(c) for c in _split_cells(row)]
        if len(cells) < 4:
            continue
        m = _RANK_RX.match(cells[0])
        if not m:
            continue
        try:
            rang = int(m.group(1))
            name = cells[1]
            wins = int(cells[2])
            losses = int(cells[3])
        except (ValueError, IndexError):
            continue
        if not name:
            continue
        if canonicalize:
            name = canonicalize(name)
        teams.append({
            "rang": rang,
            "name": name,
            "kuerzel": "",  # liefert die Seite nicht; Caller fuellt aus data.json
            "siege": wins,
            "niederlagen": losses,
            "unentschieden": 0,  # nicht von Metrostars getrackt
        })
    return teams


def parse_games(html: str, canonicalize=None, team_filter: str | None = None) -> list[dict]:
    """
    Parsed Spielliste aus dem HTML. team_filter: Substring; nur Spiele, in denen
    das Team auf einer der beiden Seiten vorkommt, werden zurueckgegeben.

    Datum-Format im HTML: "DD.MM.YYYY HH:MM" – wird auf datum/zeit gesplittet.
    Ergebnis "X - Y" -> ergebnis_heim/ergebnis_gast; "-" -> kein Ergebnis-Feld.
    """
    tables = _split_tables(html)
    if len(tables) < 2:
        return []

    games: list[dict] = []
    for row in _split_rows(tables[1]):
        cells = [_strip_tags(c) for c in _split_cells(row)]
        if len(cells) < 6:
            continue
        m = _DATE_RX.match(cells[0])
        if not m:
            continue
        dd, mm, yyyy, hhmm = m.groups()
        heim = cells[1]
        gast = cells[2]
        if not heim or not gast:
            continue
        if canonicalize:
            heim = canonicalize(heim)
            gast = canonicalize(gast)
        if team_filter and team_filter not in heim and team_filter not in gast:
            continue

        game = {
            "datum": f"{yyyy}-{mm}-{dd}",
            "zeit": hhmm,
            "heim": heim,
            "gast": gast,
        }
        sm = _SCORE_RX.match(cells[5])
        if sm:
            game["ergebnis_heim"] = int(sm.group(1))
            game["ergebnis_gast"] = int(sm.group(2))
        games.append(game)
    return games


def scrape_standings_metrostars(canonicalize=None) -> list[dict]:
    """High-Level: Fetch + Parse Tabelle. [] bei Fehler."""
    html = fetch_html()
    if not html:
        return []
    return parse_standings(html, canonicalize=canonicalize)


def scrape_games_metrostars(canonicalize=None, team_filter: str | None = None) -> list[dict]:
    """High-Level: Fetch + Parse Spielliste. [] bei Fehler."""
    html = fetch_html()
    if not html:
        return []
    return parse_games(html, canonicalize=canonicalize, team_filter=team_filter)


if __name__ == "__main__":
    # Smoke-Test: python scripts/metrostars.py
    teams = scrape_standings_metrostars()
    print(f"Tabelle: {len(teams)} Teams")
    for t in teams:
        print(f"  {t['rang']}. {t['name']:30} {t['siege']}-{t['niederlagen']}")
    games = scrape_games_metrostars(team_filter="Crazy Geese")
    print(f"\nGeese-Spiele: {len(games)}")
    for g in games:
        score = ""
        if "ergebnis_heim" in g:
            score = f" {g['ergebnis_heim']}-{g['ergebnis_gast']}"
        print(f"  {g['datum']} {g['zeit']} {g['heim']} vs {g['gast']}{score}")
