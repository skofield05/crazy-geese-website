"""
Fallback-Scraper fuer viennametrostars.at-Statistikseite.

Wird vom Haupt-Scraper genutzt:
  - als Fallback fuer Tabelle und Spiele, wenn die ABF-Seite leere Daten
    liefert (transiente ABF-Ausfaelle / Markup-Aenderungen)
  - zur Verifizierung: bei Abweichung zwischen ABF und Metrostars logged
    der Scraper eine Warnung, damit der Maintainer es sieht

Quelle: https://www.viennametrostars.at/de/Ligastatistiken/l2s__550.htm
Die Seite ist server-rendered HTML mit mehreren Tables:
  Table[0]   = Standings (Rank, Team, W, L, PCT, GB, ...)
  Table[1+]  = Games (zwei Varianten, beide werden geparst):
    "Past"    -> 4 Spalten: Datum, Heim, Awayteam, Ergebnis
    "Future"  -> 6 Spalten: Datum, Heim, Awayteam, Umpires, Scorer, Ergebnis
  Erkennung per erste-Spalte-DateMatch, nicht per Index – damit der Parser
  ueberlebt, wenn Metrostars die Reihenfolge oder Anzahl der Tables aendert
  (passierte Mai 2026: erst eine 6-Spalten-Table, dann Split in 4+6).

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


def fetch_html(timeout: int = 30, retries: int = 3, backoff: float = 2.0) -> str | None:
    """
    Holt das HTML der Statistik-Seite. None bei Netzwerkfehler.

    Retry-Politik: bis zu `retries` Versuche, dazwischen exponentielles Backoff
    (backoff * 2**i Sekunden). Metrostars ist Fallback-Quelle wenn ABF kaputt
    ist – ein einzelner Netz-Blip darf den Workflow nicht kippen.
    """
    import time

    req = urllib.request.Request(METROSTARS_URL, headers={"User-Agent": USER_AGENT})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries - 1:
                wait = backoff * (2 ** attempt)
                print(f"      [WARN] Metrostars-Fetch Versuch {attempt + 1}/{retries} "
                      f"fehlgeschlagen: {e} – retry in {wait:.0f}s")
                time.sleep(wait)
    print(f"      [WARN] Metrostars-Fetch nach {retries} Versuchen aufgegeben: {last_err}")
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
    Parsed Spielliste aus ALLEN Game-Tables im HTML (kann mehrere geben:
    z.B. Past + Future getrennt). team_filter: Substring; nur Spiele, in
    denen das Team auf einer der beiden Seiten vorkommt, werden zurueckgegeben.

    Datum-Format: "DD.MM.YYYY HH:MM" – wird auf datum/zeit gesplittet.
    Ergebnis "X - Y" (in der LETZTEN Zelle) -> ergebnis_heim/ergebnis_gast;
    "-" oder "Abgesagt" -> kein Ergebnis-Feld.

    Eine Game-Row wird erkannt an einem matchenden Datum in cells[0],
    nicht an einer fixen Tabellenposition – Metrostars hat das Layout
    schon mehrfach geaendert (4-Spalten Past, 6-Spalten Future, vs. eine
    gemeinsame 6-Spalten-Table). Damit ueberlebt der Parser solche Wechsel.
    """
    seen: set[tuple] = set()
    games: list[dict] = []

    # Erste Tabelle ist die Standings – ueberspringen; alle weiteren werden
    # auf Game-Rows abgeklopft.
    for table_html in _split_tables(html)[1:]:
        for row in _split_rows(table_html):
            cells = [_strip_tags(c) for c in _split_cells(row)]
            if len(cells) < 4:
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

            # Dedup: gleiche Game-Row in Past+Future-Tables vermeiden.
            key = (f"{yyyy}-{mm}-{dd}", hhmm, heim, gast)
            if key in seen:
                continue
            seen.add(key)

            game = {
                "datum": key[0],
                "zeit": hhmm,
                "heim": heim,
                "gast": gast,
            }
            # Score steht immer in der letzten Zelle, egal ob 4 oder 6 Spalten.
            sm = _SCORE_RX.match(cells[-1])
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
