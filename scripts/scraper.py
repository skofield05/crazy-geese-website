#!/usr/bin/env python3
"""
=============================================================================
ABF Scraper für Rohrbach Crazy Geese
=============================================================================

Dieser Scraper holt automatisch Tabellen- und Spieldaten von der
Austrian Baseball Softball Federation (ABF) Website.

VERWENDUNG:
    python scripts/scraper.py

FUNKTIONSWEISE:
    1. Lädt die Tabelle von der Standings-Seite (serverseitig gerendert)
    2. Lädt alle Spiele der Crazy Geese von der Kalender-Seite
       - Durchsucht alle Runden: Regular Season, Playoffs, Platzierungsrunde
       - Filtert nach Team-ID der Crazy Geese
    3. Holt die echten Spieltage von der Schedule-Seite
       - Navigiert durch alle Spieltage mit dem Datepicker
    4. Speichert nur NEUE Spiele (keine Duplikate)
    5. Trennt in vergangene und zukünftige Spiele

DATENQUELLEN:
    - Tabelle: /standings (serverseitig, einfacher Fetch)
    - Kalender: /calendars?round=X&team=Y (für Ergebnisse und Gegner)
    - Spielplan: /schedule-and-results (für echte Spieltage via Datepicker)

RUNDEN-IDs (können sich jede Saison ändern!):
    Die Runden-IDs werden automatisch von der Kalender-Seite extrahiert.
    Typische Runden: Regular Season, Playoffs, Platzierungsrunde

TEAM-ID:
    Die Team-ID der Crazy Geese wird automatisch aus dem Dropdown extrahiert.

HINWEISE:
    - Der Scraper braucht Playwright mit Chromium
    - Installation: pip install playwright && python -m playwright install chromium
    - Die ABF-Seite hat einen Bug: Kalender zeigt falsches Datum
    - Daher werden Daten separat von der Schedule-Seite geholt

AUTOR: Claude Code
LETZTE AKTUALISIERUNG: 2026-02-06
=============================================================================
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

# Spiel-Datumsvergleiche müssen in Wiener Lokalzeit laufen, nicht UTC.
# Sonst landen Spiele am späten Abend MESZ in der falschen Tagesbucket,
# weil GitHub-Runner in UTC laufen.
TZ_VIENNA = ZoneInfo("Europe/Vienna")

# Lokales Modul (gleicher Ordner)
sys.path.insert(0, str(Path(__file__).parent))
from metrostars import scrape_standings_metrostars, scrape_games_metrostars


def goto_with_retry(page, url, retries=3, **kwargs):
    """
    Wrapper um page.goto mit Retry bei TimeoutError.
    GitHub Actions-Runner haben gelegentlich Netzwerkhänger – ein Blip
    soll nicht den ganzen Cron-Job killen.
    """
    kwargs.setdefault("wait_until", "networkidle")
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return page.goto(url, **kwargs)
        except PlaywrightTimeoutError as e:
            last_err = e
            print(f"      [RETRY {attempt}/{retries}] Timeout bei {url}")
            page.wait_for_timeout(2000)
    raise last_err

# =============================================================================
# KONFIGURATION
# =============================================================================

# Vereinsdaten
TEAM_NAME = "Crazy Geese"
TEAM_FULL_NAME = "Rohrbach Crazy Geese"

# Mapping ABF-Phasen -> Konvention in data.json. Bestand verwendet
# "Grunddurchgang" statt ABFs "Regular Season".
PHASE_MAP = {
    "Regular Season": "Grunddurchgang",
}

# ABF schreibt Teamnamen zwischen Tabelle und Kalender-Sicht uneinheitlich
# ("Dirty Sox Graz" vs. "Graz Dirty Sox", "Metrostars" vs. "Vienna Metrostars 3"
# u.a.). Wir zentralisieren die kanonische Form, damit Tabelle und Spiele
# denselben Wortlaut benutzen.
TEAM_NAME_OVERRIDES = {
    "Kutro Crazy Geese": TEAM_FULL_NAME,
    "Dirty Sox Graz": "Graz Dirty Sox",
    "Metrostars": "Vienna Metrostars 3",
}


def canonical_team_name(name):
    """Wendet TEAM_NAME_OVERRIDES an. Unbekannte Namen bleiben unveraendert."""
    if not name:
        return name
    return TEAM_NAME_OVERRIDES.get(name.strip(), name)

# Dateipfade
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / "data" / "data.json"

# ABF URLs - WICHTIG: Bei neuer Saison hier die URL anpassen!
# Format: baseball-landesliga-ost-YYYY
ABF_BASE = "https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2026"
ABF_STANDINGS = f"{ABF_BASE}/standings"
ABF_CALENDAR = f"{ABF_BASE}/calendars"
ABF_SCHEDULE = f"{ABF_BASE}/schedule-and-results"


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def load_data():
    """Lädt die aktuelle data.json"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """Speichert die aktualisierte data.json"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Daten gespeichert: {DATA_FILE}")


def find_existing_game(existing_games, new_game):
    """
    Sucht ein bestehendes Spiel, das zu new_game gehoert. Gibt das Dict
    zurueck (mutierbar – Caller updated direkt) oder None.

    Match-Reihenfolge:
      1. spielnr (eindeutig pro Liga, bleibt auch bei Verlegung gleich)
      2. (heim, gast). Bei mehreren Kandidaten: gleiches Datum bevorzugt.
         Wenn nicht aufloesbar, kein Match (→ neues Spiel).

    Hintergrund: ABF kann Termine/Orte aendern, ohne dass das Spiel "neu" ist.
    Match per spielnr toleriert solche Aenderungen; Fallback per (heim, gast)
    deckt Bestandsspiele ab, die noch keine spielnr im JSON haben.
    """
    new_spielnr = new_game.get("spielnr")
    if new_spielnr:
        for g in existing_games:
            if g.get("spielnr") == new_spielnr:
                return g

    candidates = [
        g for g in existing_games
        if g.get("heim") == new_game.get("heim")
        and g.get("gast") == new_game.get("gast")
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        new_datum = new_game.get("datum")
        if new_datum:
            for c in candidates:
                if c.get("datum") == new_datum:
                    return c
    return None


def determine_phase():
    """Bestimmt die aktuelle Saisonphase basierend auf dem Datum.

    Heuristik pro Monat:
      Jan–Mär   -> Vorsaison
      Apr–Aug   -> Regular Season
      Sep       -> Playoffs
      Okt–Dez   -> Endklassement
    """
    month = datetime.now(TZ_VIENNA).month
    if month <= 3:
        return "Vorsaison"
    if month <= 8:
        return "Regular Season"
    if month == 9:
        return "Playoffs"
    return "Endklassement"


# =============================================================================
# SCRAPER: TABELLE
# =============================================================================

def scrape_standings(page):
    """
    Scraped die Tabelle von der ABF Standings-Seite.

    Robust gegen Markup-Aenderungen: liest die Header-Zeile, ermittelt fuer
    jede Spalte (#, Mannschaft, W, L, T) den Index, und greift die Datenzeilen
    ueber diese dynamische Map zu. Frueher waren die Indizes hartkodiert –
    ABF hat das Markup inzwischen verschoben (Logo-Spalte vor Mannschaft).

    Returns:
        Liste von Team-Dicts: rang, name, kuerzel, siege, niederlagen, unentschieden
    """
    print(f"\n[1/3] TABELLE")
    print(f"      URL: {ABF_STANDINGS}")

    # /standings macht nach dem initialen Load noch eine Client-Side-Navigation
    # (eingebettete React-Komponente). Wir laden mit domcontentloaded und
    # warten dann gezielt auf das Tabellen-Element, statt auf networkidle.
    goto_with_retry(page, ABF_STANDINGS, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("table.standings-print", timeout=15000)
    except PlaywrightTimeoutError:
        # Frueher Ausstieg: ohne Tabelle braucht der nachfolgende
        # query_selector_all gar nicht erst zu laufen – die React-App
        # navigiert oft genau dann nochmal weg, was den Execution-Context
        # zerstoert (Run #22 / 2026-05-04 06:42 UTC). Caller faellt auf
        # Metrostars zurueck.
        print("      [WARNUNG] standings-print-Tabelle nicht gefunden – ABF lieferte "
              "keine Tabelle aus. Fallback auf Metrostars folgt.")
        return []
    page.wait_for_timeout(1000)

    teams = []
    # ABF: <table class="table table-hover standings-print">. Mehrere Tabellen
    # pro Seite (Regular Season + Platzierungsrunde) – wir nehmen die erste
    # nicht-leere.
    try:
        tables = page.query_selector_all("table.standings-print") or page.query_selector_all("table")
    except PlaywrightError as e:
        print(f"      [WARNUNG] query_selector_all warf {type(e).__name__} – "
              "vermutlich Late-Navigation der React-App. Fallback auf Metrostars folgt.")
        return []

    # Heuristisches Parsing: Header hat 7 Spalten (#, Mannschaft, W, L, T, PCT, GB),
    # Body hat 8 (zusaetzliche Logo-Spalte vor Mannschaft) – Indices passen nicht
    # 1:1. Stattdessen suchen wir die "Team-Cell" (mehrzeilig: Kuerzel + Name) und
    # nehmen die folgenden 3 Cells als W/L/T. Das ist robust gegen Layout-Aenderungen.
    for table in tables:
        body_rows = table.query_selector_all("tbody tr") or table.query_selector_all("tr")

        for row in body_rows:
            cells = row.query_selector_all("td")
            if len(cells) < 4:
                continue

            # Team-Cell: erste Zelle mit Kuerzel\nName (zwei nicht-leere Zeilen)
            team_idx = None
            for i, c in enumerate(cells):
                text = c.inner_text().strip()
                if "\n" not in text:
                    continue
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) >= 2:
                    team_idx = i
                    break

            if team_idx is None or team_idx + 3 >= len(cells):
                continue

            team_text = cells[team_idx].inner_text().strip()
            lines = [l.strip() for l in team_text.split("\n") if l.strip()]
            kuerzel = lines[0]
            name = canonical_team_name(lines[1])

            try:
                wins = int(cells[team_idx + 1].inner_text().strip() or 0)
                losses = int(cells[team_idx + 2].inner_text().strip() or 0)
                ties = int(cells[team_idx + 3].inner_text().strip() or 0)
            except ValueError:
                continue

            # Rang: erste numerische Cell vor der Team-Cell. Wenn keine: Vorsaison.
            rang = 0
            for i in range(team_idx):
                t = cells[i].inner_text().strip()
                if t.isdigit():
                    rang = int(t)
                    break
            if rang == 0:
                rang = 1  # Vorsaison: alle Teams gleichauf

            teams.append({
                "rang": rang,
                "name": name,
                "kuerzel": kuerzel,
                "siege": wins,
                "niederlagen": losses,
                "unentschieden": ties,
            })

        if teams:  # erste passende Tabelle reicht
            break

    # Duplikate entfernen
    seen = set()
    unique_teams = []
    for team in sorted(teams, key=lambda x: x["rang"]):
        if team["name"] not in seen:
            seen.add(team["name"])
            unique_teams.append(team)

    print(f"      Gefunden: {len(unique_teams)} Teams")
    cg = next((t for t in unique_teams if TEAM_NAME in t["name"]), None)
    if cg:
        print(f"      {TEAM_FULL_NAME}: Platz {cg['rang']} ({cg['siege']}W-{cg['niederlagen']}L)")

    return unique_teams


# =============================================================================
# SCRAPER: SPIELE (KALENDER)
# =============================================================================

def get_rounds_and_team_id(page):
    """
    Extrahiert die verfügbaren Runden und die Team-ID aus der Kalender-Seite.
    Diese IDs können sich jede Saison ändern!

    Returns:
        tuple: (rounds_dict, team_id)
        - rounds_dict: {"Regular Season": "4907", "Playoffs": "4908", ...}
        - team_id: "35667" (ID der Crazy Geese)
    """
    goto_with_retry(page, ABF_CALENDAR)
    page.wait_for_timeout(2000)

    rounds = {}
    team_id = None

    # Runden aus Select extrahieren
    round_select = page.query_selector("#selectRound")
    if round_select:
        options = round_select.query_selector_all("option")
        for opt in options:
            value = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if value and text and "Filtern" not in text:
                rounds[text] = value

    # Team-ID extrahieren
    team_select = page.query_selector("#selectTeam")
    if team_select:
        options = team_select.query_selector_all("option")
        for opt in options:
            text = opt.inner_text().strip()
            if TEAM_NAME in text:
                team_id = opt.get_attribute("value")
                break

    print(f"      Runden gefunden: {list(rounds.keys())}")
    print(f"      Team-ID: {team_id}")

    return rounds, team_id


def scrape_games_from_calendar(page, rounds, team_id):
    """
    Scraped alle Spiele der Crazy Geese von der Kalender-Seite.
    Geht durch alle Runden (Regular Season, Playoffs, Platzierungsrunde).

    HINWEIS: Die Kalender-Seite zeigt ein falsches Datum (aktuelles Datum).
    Die echten Spieltage werden später von der Schedule-Seite geholt.

    Returns:
        Liste von Spiel-Dictionaries
    """
    print(f"\n[2/3] SPIELE (Kalender)")

    all_games = []

    for round_name, round_id in rounds.items():
        url = f"{ABF_CALENDAR}?round={round_id}&team={team_id}"
        print(f"      Lade: {round_name}...")

        goto_with_retry(page, url)
        page.wait_for_timeout(2000)

        body = page.inner_text("body")
        games = parse_games_from_calendar_text(body, round_name)

        print(f"      -> {len(games)} Spiele gefunden")
        all_games.extend(games)

    print(f"      Gesamt: {len(all_games)} Spiele")
    return all_games


def parse_games_from_calendar_text(body_text, phase):
    """
    Parst die Spiele aus dem Kalender-Seitentext.

    Die Struktur ist:
        #XX - Beschreibung
        Ort
        GAST
        Kürzel
        Teamname
        XX : XX (Score)
        HEIM
        Kürzel
        Teamname
    """
    games = []
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]

    current_game = {}
    awaiting_gast = False
    awaiting_heim = False
    awaiting_ort = False

    score_rx = re.compile(r'^\d+\s*:\s*\d+$')
    gast_markers = {'GAST', 'Gast', 'VISITOR'}
    heim_markers = {'HEIM', 'Heim', 'HOME'}

    def looks_like_kuerzel(s):
        return len(s) <= 4 and s.isupper()

    for i, line in enumerate(lines):
        # Spielnummer
        if line.startswith('#') and ' - ' in line:
            if current_game and 'spielnr' in current_game:
                games.append(current_game)
            current_game = {'spielnr': line, 'phase': phase}
            awaiting_gast = False
            awaiting_heim = False
            awaiting_ort = True

        # GAST marker
        elif line in gast_markers:
            awaiting_gast = True
            awaiting_heim = False
            awaiting_ort = False

        # HEIM marker
        elif line in heim_markers:
            awaiting_heim = True
            awaiting_gast = False
            awaiting_ort = False

        # Score
        elif score_rx.match(line):
            awaiting_ort = False
            scores = line.split(':')
            current_game['ergebnis_gast'] = int(scores[0].strip())
            current_game['ergebnis_heim'] = int(scores[1].strip())

        # Ort: erste nicht-Marker-Zeile nach der Spielnummer, die nicht wie
        # ein Teamkuerzel aussieht. Ersetzt die frühere Whitelist, damit neue
        # Venues (Spenadlwiese, Freudenau, Beers Field, ...) nicht verloren gehen.
        elif awaiting_ort and 'ort' not in current_game and not looks_like_kuerzel(line):
            current_game['ort'] = line
            awaiting_ort = False

        # Teamnamen (nach Kürzel)
        elif awaiting_gast and 'gast' not in current_game:
            if looks_like_kuerzel(line):
                current_game['gast_kuerzel'] = line
            elif len(line) > 3 and 'gast_kuerzel' in current_game:
                current_game['gast'] = line
                awaiting_gast = False
        elif awaiting_heim and 'heim' not in current_game:
            if looks_like_kuerzel(line):
                current_game['heim_kuerzel'] = line
            elif len(line) > 3 and 'heim_kuerzel' in current_game:
                current_game['heim'] = line
                awaiting_heim = False

    # Letztes Spiel hinzufügen
    if current_game and 'spielnr' in current_game:
        games.append(current_game)

    # Nur Crazy Geese Spiele behalten
    cg_games = []
    for g in games:
        gast = g.get('gast', '')
        heim = g.get('heim', '')
        if TEAM_NAME in gast or TEAM_NAME in heim:
            cg_games.append(g)

    return cg_games


# =============================================================================
# SCRAPER: SPIELTAGE (SCHEDULE)
# =============================================================================

def scrape_game_dates(page, games):
    """
    Holt die echten Spieltage von der Schedule-Seite.
    Navigiert durch alle Spieltage mit dem Datepicker.

    Die Kalender-Seite zeigt leider das aktuelle Datum statt des echten
    Spieldatums (Bug auf der ABF-Seite). Daher holen wir die Daten hier.

    Args:
        page: Playwright Page-Objekt
        games: Liste von Spielen (aus scrape_games_from_calendar)

    Returns:
        Die games-Liste mit ausgefüllten datum/zeit Feldern
    """
    print(f"\n[3/3] SPIELTAGE (Schedule)")
    print(f"      URL: {ABF_SCHEDULE}")

    goto_with_retry(page, ABF_SCHEDULE)
    page.wait_for_timeout(3000)

    # Finde die Pfeil-Buttons im Datepicker
    # Button 0 = links (zurück), Button 1 = Kalender, Button 2 = rechts (vor)
    buttons = page.query_selector_all('.date-picker button')
    if len(buttons) < 3:
        print("      [WARNUNG] Datepicker-Buttons nicht gefunden!")
        return games

    left_arrow = buttons[0]
    right_arrow = buttons[2]

    # Erstelle Lookup für Spielnummern
    game_lookup = {}
    for g in games:
        nr_match = re.match(r'(#\d+)', g.get('spielnr', ''))
        if nr_match:
            game_lookup[nr_match.group(1)] = g

    target_numbers = set(game_lookup.keys())
    found_numbers = set()

    print(f"      Suche Daten für {len(target_numbers)} Spiele...")

    # Navigiere zum Saisonstart (30x zurück sollte reichen)
    for _ in range(30):
        left_arrow.click()
        page.wait_for_timeout(200)

    page.wait_for_timeout(1000)

    # Navigiere durch alle Spieltage
    date_in_context_rx = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})(?:,\s*(\d{1,2}:\d{2}))?')
    time_rx = re.compile(r'(\d{1,2}:\d{2})')

    for click in range(60):  # Max 60 Spieltage
        page.wait_for_timeout(400)
        body = page.inner_text("body")

        # Pro Spiel im Kontext-Fenster Datum + Zeit extrahieren – wichtig fuer
        # Doppel-Spieltage wo Sa und So auf derselben Seite angezeigt werden.
        for nr in target_numbers - found_numbers:
            marker = f'{nr} -'
            if marker not in body:
                continue
            pos = body.find(marker)
            context = body[pos:pos + 600]
            if TEAM_NAME not in context:
                continue

            date_match = date_in_context_rx.search(context)
            if not date_match:
                continue
            d, m, y, zeit_from_date = date_match.group(1), date_match.group(2), date_match.group(3), date_match.group(4)
            datum = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

            time_match = time_rx.search(context)
            game_zeit = (time_match.group(1) if time_match else zeit_from_date) or ''

            game_lookup[nr]['datum'] = datum
            game_lookup[nr]['zeit'] = game_zeit
            found_numbers.add(nr)
            print(f"      {nr}: {datum} {game_zeit}")

        # Fertig wenn alle gefunden
        if found_numbers == target_numbers:
            print(f"      Alle {len(found_numbers)} Spieltage gefunden!")
            break

        right_arrow.click()

    if found_numbers != target_numbers:
        missing = target_numbers - found_numbers
        print(f"      [WARNUNG] Nicht gefunden: {missing}")

    return games


# =============================================================================
# QUELLEN-RESOLVE: ABF + METROSTARS
# =============================================================================

def _resolve_standings(abf_teams, mets_teams, data, scrape_errors):
    """
    Entscheidet, welche Tabellen-Daten in data.json wandern.

    Strategie "mehr Spiele = aktueller":
      Pro Quelle das Total aller absolvierten Spiele (sum W+L) berechnen,
      die Quelle mit mehr Total gewinnt. ABF bei Gleichstand (kanonische
      Quelle, sollten dann ohnehin identisch sein). Hintergrund: wenn ABF
      einen Spieltag noch nicht eingetragen hat, Metrostars aber schon,
      wuerde 'ABF immer primaer' veraltete Records reinschreiben.

    Edge-Cases:
      - Nur eine Quelle hat Daten -> die nutzen.
      - Beide leer                -> Fehler sammeln, alte Tabelle bleibt.

    Bei beiden Quellen: Diff-Warnung in jedem Fall (auch bei selbem Total).
    Kuerzel werden ergaenzt, falls die gewaehlte Quelle keine liefert
    (Metrostars hat keine).
    """
    if abf_teams and mets_teams:
        for d in _diff_standings(abf_teams, mets_teams):
            print(f"      [DIVERGENZ] {d}")

        abf_total = sum(_team_games(t) for t in abf_teams)
        mets_total = sum(_team_games(t) for t in mets_teams)
        if mets_total > abf_total:
            print(f"      [WAEHLE METROSTARS] {mets_total} Total-Spiele vs ABF {abf_total} – "
                  "Metrostars ist aktueller.")
            _ensure_kuerzel(mets_teams, [abf_teams, data.get("tabelle", {}).get("teams", [])])
            return mets_teams
        return abf_teams

    if abf_teams:
        return abf_teams

    if mets_teams:
        print(f"      [FALLBACK] ABF-Tabelle leer – nutze Metrostars ({len(mets_teams)} Teams)")
        _ensure_kuerzel(mets_teams, [data.get("tabelle", {}).get("teams", [])])
        return mets_teams

    scrape_errors.append(
        "Tabelle: weder ABF noch Metrostars haben Teams zurueckgegeben."
    )
    return []


def _team_games(team):
    """Total absolvierte Spiele = Siege + Niederlagen (Unentschieden zaehlen mit)."""
    return (
        (team.get("siege") or 0)
        + (team.get("niederlagen") or 0)
        + (team.get("unentschieden") or 0)
    )


def _ensure_kuerzel(teams, fallback_lists):
    """Fuellt fehlende kuerzel-Felder aus den ersten Lookup-Listen, die was haben."""
    lookups = []
    for src in fallback_lists:
        lookups.append({t.get("name"): t.get("kuerzel", "") for t in src if t.get("name")})
    for t in teams:
        if t.get("kuerzel"):
            continue
        for lk in lookups:
            k = lk.get(t["name"])
            if k:
                t["kuerzel"] = k
                break


def _diff_standings(abf_teams, mets_teams):
    """Vergleicht W/L pro Team und liefert menschenlesbare Diff-Strings."""
    abf_by_name = {t["name"]: t for t in abf_teams}
    mets_by_name = {t["name"]: t for t in mets_teams}
    diffs = []
    for name in sorted(set(abf_by_name) | set(mets_by_name)):
        a = abf_by_name.get(name)
        m = mets_by_name.get(name)
        if a and not m:
            diffs.append(f"'{name}': ABF hat, Metrostars nicht.")
            continue
        if m and not a:
            diffs.append(f"'{name}': Metrostars hat, ABF nicht.")
            continue
        if a["siege"] != m["siege"] or a["niederlagen"] != m["niederlagen"]:
            diffs.append(
                f"'{name}': ABF {a['siege']}-{a['niederlagen']} vs "
                f"Metrostars {m['siege']}-{m['niederlagen']}"
            )
    return diffs


def _resolve_games(abf_games, mets_games, rounds, scrape_errors):
    """
    Entscheidet, welche Spiele-Daten in den Merge-Pipeline-Schritt gehen.

    Strategie:
      - ABF lieferte Spiele -> ABF nutzen, ABER pro Spiel das Ergebnis von
        Metrostars uebernehmen, wenn ABF noch keins hat. Hintergrund:
        ABFs 0:0-Platzhalter fuer ungespielte Spiele wird zwar vom Scraper
        gefiltert, aber Metrostars hat manchmal das echte Ergebnis bevor
        ABF es eintraegt – damit fuellen wir solche Luecken. Bei beidseitigem
        Ergebnis und Diff: Warnung loggen.
      - ABF leer            -> Metrostars als Fallback (mit Errorhinweis,
        falls Runden vorhanden waren).
      - Beide leer          -> Fehler sammeln, leere Liste zurueck.
    """
    if abf_games:
        if mets_games:
            filled = _fill_results_from(abf_games, mets_games)
            if filled:
                print(f"      [METROSTARS-FILL] {filled} Spielergebnisse von Metrostars "
                      f"uebernommen (ABF hatte noch keins).")
            for d in _diff_game_results(abf_games, mets_games):
                print(f"      [DIVERGENZ] {d}")
        return abf_games

    if mets_games:
        if rounds:
            scrape_errors.append(
                f"Spiele: 0 Treffer in {len(rounds)} ABF-Runde(n) – nutze "
                f"Metrostars-Fallback. ABF-Kalender-Markup vermutlich geaendert."
            )
        else:
            print(f"      [FALLBACK] ABF-Spiele leer – nutze Metrostars ({len(mets_games)} Spiele)")
        return mets_games

    scrape_errors.append(
        "Spiele: weder ABF noch Metrostars haben Spiele zurueckgegeben."
    )
    return []


def _fill_results_from(target_games, source_games):
    """
    Fuer jedes target-Spiel ohne Ergebnis: schaue im source nach (Match per
    datum/heim/gast) und uebernimm dort das Ergebnis. Mutiert target_games
    in-place. Returns Anzahl der aufgefuellten Spiele.
    """
    source_by_key = {
        (g.get("datum"), g.get("heim"), g.get("gast")): g
        for g in source_games
        if g.get("ergebnis_heim") is not None
    }
    filled = 0
    for tg in target_games:
        if tg.get("ergebnis_heim") is not None:
            continue
        sg = source_by_key.get((tg.get("datum"), tg.get("heim"), tg.get("gast")))
        if sg:
            tg["ergebnis_heim"] = sg["ergebnis_heim"]
            tg["ergebnis_gast"] = sg["ergebnis_gast"]
            filled += 1
    return filled


def _diff_game_results(abf_games, mets_games):
    """
    Vergleicht Ergebnisse fuer Spiele, die in beiden Quellen vorkommen.
    Match per (datum, heim, gast) – Teamnamen sind beide kanonisiert.
    """
    abf_by_key = {}
    for g in abf_games:
        if g.get("datum") and g.get("heim") and g.get("gast"):
            abf_by_key[(g["datum"], g["heim"], g["gast"])] = g

    diffs = []
    for mg in mets_games:
        key = (mg.get("datum"), mg.get("heim"), mg.get("gast"))
        ag = abf_by_key.get(key)
        if not ag:
            continue  # Spiel nicht in ABF – kein Verify moeglich, kein Diff
        a_h, a_g = ag.get("ergebnis_heim"), ag.get("ergebnis_gast")
        m_h, m_g = mg.get("ergebnis_heim"), mg.get("ergebnis_gast")
        # Beide haben Ergebnis: vergleichen
        if a_h is not None and m_h is not None and (a_h != m_h or a_g != m_g):
            diffs.append(
                f"{key[0]} {key[1]} vs {key[2]}: "
                f"ABF {a_h}-{a_g} vs Metrostars {m_h}-{m_g}"
            )
        # Nur einer hat Ergebnis: Hinweis (kein Fehler – kann timing sein)
        elif (a_h is None) != (m_h is None):
            who = "ABF" if a_h is not None else "Metrostars"
            diffs.append(
                f"{key[0]} {key[1]} vs {key[2]}: nur {who} hat Ergebnis"
            )
    return diffs


# =============================================================================
# HAUPTFUNKTION
# =============================================================================

def update_data():
    """
    Hauptfunktion: Aktualisiert alle Daten von der ABF-Website.

    1. Lädt bestehende Daten
    2. Scraped Tabelle
    3. Scraped Spiele (alle Runden)
    4. Holt Spieltage
    5. Merged mit bestehenden Daten (keine Duplikate)
    6. Speichert
    """
    print("=" * 60)
    print("ABF SCRAPER - Rohrbach Crazy Geese")
    print("=" * 60)
    print(f"Zeitpunkt: {datetime.now(TZ_VIENNA).strftime('%Y-%m-%d %H:%M:%S')} (Wien)")
    print(f"Datenquelle: {ABF_BASE}")

    # Bestehende Daten laden
    data = load_data()
    existing_games = (
        list(data.get("spiele", {}).get("vergangene", []))
        + list(data.get("spiele", {}).get("naechste", []))
    )
    print(f"\nBestehende Spiele in data.json: {len(existing_games)}")

    # Fehler werden gesammelt und am Ende mit Exit-Code 1 ausgegeben, damit
    # GitHub Actions den Job rot faerbt und der Maintainer eine Notification
    # bekommt. data.json wird trotzdem gespeichert – mit den Daten, die wir
    # bekommen haben (oft sind das immer noch Updates, z.B. Spiele wenn nur
    # die Tabelle scheitert).
    scrape_errors = []
    abf_teams = []
    abf_games = []
    rounds = []
    team_id = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()

            # 1. Tabelle scrapen (ABF primaer)
            abf_teams = scrape_standings(page)

            # 2. Runden und Team-ID holen
            print(f"\n[2/3] SPIELE")
            rounds, team_id = get_rounds_and_team_id(page)

            if not team_id:
                scrape_errors.append(
                    f"Team-ID fuer '{TEAM_NAME}' nicht im Calendar-Dropdown gefunden. "
                    f"Saison-URL pruefen ({ABF_BASE})."
                )
            else:
                # 3. Spiele aus Kalender holen
                abf_games = scrape_games_from_calendar(page, rounds, team_id)

                # 4. Spieltage holen (echte Spieltage von /schedule-and-results)
                if abf_games:
                    abf_games = scrape_game_dates(page, abf_games)

        finally:
            browser.close()

    # Metrostars-Statistikseite als Fallback und Verifizierung.
    # Reine HTTP-Quelle, kein Browser noetig – funktioniert auch wenn ABF
    # gerade kaputt ist (Run #22 / 2026-05-04 06:42 UTC).
    print(f"\n[FALLBACK/VERIFY] viennametrostars.at")
    mets_teams = scrape_standings_metrostars(canonicalize=canonical_team_name)
    mets_games = scrape_games_metrostars(canonicalize=canonical_team_name, team_filter=TEAM_NAME)
    if mets_teams:
        print(f"      Metrostars-Tabelle: {len(mets_teams)} Teams")
    if mets_games:
        print(f"      Metrostars-Spiele:  {len(mets_games)}")

    # Tabelle: ABF bevorzugen, Metrostars als Fallback. Bei Disagreement warnen.
    teams = _resolve_standings(abf_teams, mets_teams, data, scrape_errors)
    if teams:
        data["tabelle"]["teams"] = teams
        data["tabelle"]["stand"] = datetime.now(TZ_VIENNA).strftime("%Y-%m-%d")
        data["tabelle"]["phase"] = determine_phase()

    # Spiele: ABF bevorzugen, Metrostars als Fallback. Bei beiden vorhanden:
    # Ergebnis-Verify gegen Metrostars (Datum-/Team-Match).
    new_games = _resolve_games(abf_games, mets_games, rounds, scrape_errors)

    # 5. Spiele mergen: bestehende updaten (Verlegungen!), neue hinzufuegen
    print(f"\n[MERGE]")
    added_count = 0
    updated_count = 0
    skipped_ghost = 0
    normalized_count = 0
    today = datetime.now(TZ_VIENNA).date()

    # Arbeite auf flacher Liste-Kopie. Die Dict-Objekte sind shared mit
    # data["spiele"][...], Mutationen wirken automatisch durch.
    all_games = (
        list(data.get("spiele", {}).get("vergangene", []))
        + list(data.get("spiele", {}).get("naechste", []))
    )

    canonical_names = [t.get("name", "") for t in data.get("tabelle", {}).get("teams", []) if t.get("name")]

    def normalize_team(name):
        # 1. Hartes Override-Mapping zuerst (deckt "Kutro -> Rohrbach",
        #    "Dirty Sox Graz -> Graz Dirty Sox", "Metrostars -> Vienna Metrostars 3").
        name = canonical_team_name(name)
        if not name or name in canonical_names:
            return name
        # 2. Substring-Match (Fallback fuer noch nicht gemappte Varianten)
        for canonical in canonical_names:
            if canonical and (canonical in name or name in canonical):
                return canonical
        # 3. Wort-Overlap-Heuristik
        name_words = set(name.lower().split())
        best = None
        best_overlap = 0
        for canonical in canonical_names:
            overlap = len(name_words & set(canonical.lower().split()))
            if overlap > best_overlap and overlap >= 2:
                best = canonical
                best_overlap = overlap
        return best or name

    spielnr_rx = re.compile(r'(#\d+)')

    for game in new_games:
        heim = normalize_team(game.get("heim", ""))
        gast = normalize_team(game.get("gast", ""))
        if heim != game.get("heim", "") or gast != game.get("gast", ""):
            normalized_count += 1

        nr_match = spielnr_rx.match(game.get("spielnr", "") or "")
        spielnr = nr_match.group(1) if nr_match else None

        raw_phase = game.get("phase", "")
        phase = PHASE_MAP.get(raw_phase, raw_phase or "Grunddurchgang")

        formatted_game = {
            "spielnr": spielnr,
            "datum": game.get("datum", ""),
            "zeit": game.get("zeit", ""),
            "heim": heim,
            "gast": gast,
            "ergebnis_heim": game.get("ergebnis_heim"),
            "ergebnis_gast": game.get("ergebnis_gast"),
            "ort": game.get("ort", ""),
            "phase": phase,
        }

        # ABF zeigt fuer ungespielte Spiele 0:0 als Platzhalter. Ergebnis erst
        # neutralisieren, dann Geist-Check – sonst rutscht ein "0:0 ohne Datum"
        # am Geist-Filter vorbei und landet datums- und ergebnislos im JSON.
        game_in_past = False
        if formatted_game["datum"]:
            try:
                game_in_past = (
                    datetime.strptime(formatted_game["datum"], "%Y-%m-%d").date() <= today
                )
            except ValueError:
                pass
        if not game_in_past:
            formatted_game["ergebnis_heim"] = None
            formatted_game["ergebnis_gast"] = None

        if not formatted_game["datum"] and formatted_game.get("ergebnis_heim") is None:
            skipped_ghost += 1
            continue

        existing = find_existing_game(all_games, formatted_game)
        if existing is not None:
            # phase nicht antasten – kann user-curated sein
            # ("Grunddurchgang" statt ABFs "Regular Season").
            changes = []

            # spielnr: persistenter Schluessel, immer (re-)setzen
            new_nr = formatted_game.get("spielnr")
            if new_nr and existing.get("spielnr") != new_nr:
                changes.append(f"spielnr: {existing.get('spielnr')!r}->{new_nr!r}")
                existing["spielnr"] = new_nr

            # datum, zeit: ABF ist authoritativ
            datum_or_zeit_changed = False
            for key in ("datum", "zeit"):
                new_val = formatted_game.get(key)
                if not new_val:
                    continue
                if existing.get(key) != new_val:
                    changes.append(f"{key}: {existing.get(key)!r}->{new_val!r}")
                    existing[key] = new_val
                    datum_or_zeit_changed = True

            # ort: nur bei Verlegungs-Signal (datum/zeit hat sich geaendert).
            # Sonst behalten wir den oft user-gepflegten Wortlaut, statt ihn
            # bei jedem Lauf auf die ABF-Schreibweise zu normalisieren
            # ("Wien" -> "Vienna" o.ae.).
            if datum_or_zeit_changed:
                new_ort = formatted_game.get("ort")
                if new_ort and existing.get("ort") != new_ort:
                    changes.append(f"ort: {existing.get('ort')!r}->{new_ort!r}")
                    existing["ort"] = new_ort

            # Ergebnis: ABF ist authoritativ (Platzhalter 0:0 ist oben gefiltert)
            for key in ("ergebnis_heim", "ergebnis_gast"):
                new_val = formatted_game.get(key)
                if new_val is None:
                    continue
                if existing.get(key) != new_val:
                    changes.append(f"{key}: {existing.get(key)!r}->{new_val!r}")
                    existing[key] = new_val

            if changes:
                updated_count += 1
                label = existing.get("spielnr") or f"{existing.get('heim')} vs {existing.get('gast')}"
                print(f"      ~ UPD {label}: {', '.join(changes)}")
            continue

        all_games.append(formatted_game)
        added_count += 1
        print(f"      + NEU: {gast} @ {heim} ({formatted_game['datum']})")

    # Re-Split nach datum / Ergebnis (datum-Aenderungen koennen ein Spiel
    # zwischen 'vergangene' und 'naechste' wandern lassen).
    vergangene = []
    naechste = []
    for g in all_games:
        if g.get("datum"):
            try:
                game_date = datetime.strptime(g["datum"], "%Y-%m-%d").date()
            except ValueError:
                naechste.append(g)
                continue
            (vergangene if game_date < today else naechste).append(g)
        elif g.get("ergebnis_heim") is not None:
            vergangene.append(g)
        else:
            naechste.append(g)

    vergangene.sort(key=lambda x: (x.get("datum", "9999"), x.get("zeit", "")))
    naechste.sort(key=lambda x: (x.get("datum", "9999"), x.get("zeit", "")))

    data["spiele"]["vergangene"] = vergangene
    data["spiele"]["naechste"] = naechste
    data["spiele"]["letztes_update"] = datetime.now(TZ_VIENNA).strftime("%Y-%m-%d")

    print(f"      Neue Spiele hinzugefügt: {added_count}")
    print(f"      Aktualisiert: {updated_count}")
    if normalized_count:
        print(f"      Teamnamen normalisiert (Kutro -> Rohrbach): {normalized_count}")
    if skipped_ghost:
        print(f"      Ignoriert (ohne Datum & Ergebnis): {skipped_ghost}")
    print(f"      Gesamt vergangene: {len(vergangene)}")
    print(f"      Gesamt nächste: {len(naechste)}")

    # 6. Speichern
    save_data(data)

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Tabelle: {len(data['tabelle']['teams'])} Teams")

    cg = next((t for t in data["tabelle"]["teams"] if TEAM_NAME in t.get("name", "")), None)
    if cg:
        print(f"{TEAM_FULL_NAME}: Platz {cg['rang']} ({cg['siege']}W-{cg['niederlagen']}L)")

    print(f"Spiele gesamt: {len(vergangene) + len(naechste)}")
    print(f"  - Vergangene: {len(vergangene)}")
    print(f"  - Nächste: {len(naechste)}")
    print("=" * 60)

    if scrape_errors:
        print("\n" + "!" * 60)
        print("FEHLER BEIM SCRAPING – Workflow scheitert mit Exit-Code 1")
        print("!" * 60)
        for err in scrape_errors:
            print(f"  - {err}")
        print("\nMaintainer-Hinweis: data.json wurde mit dem aktuellen Stand")
        print("gespeichert (oft sind das vorherige Werte). Bitte ABF-Markup")
        print("pruefen und Selektoren in scripts/scraper.py anpassen.")
        sys.exit(1)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    update_data()
