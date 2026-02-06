#!/usr/bin/env python3
"""
=============================================================================
ABF Scraper für Kutro Crazy Geese
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
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# =============================================================================
# KONFIGURATION
# =============================================================================

# Vereinsdaten
TEAM_NAME = "Crazy Geese"
TEAM_FULL_NAME = "Kutro Crazy Geese"

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


def game_exists(existing_games, new_game):
    """
    Prüft ob ein Spiel bereits existiert (Duplikat-Vermeidung).
    Ein Spiel ist identisch wenn Datum, Heim und Gast übereinstimmen.
    Falls Datum leer ist, wird nach Heim/Gast/Ergebnis verglichen.
    """
    for game in existing_games:
        # Wenn beide Daten haben, vergleiche Datum + Teams
        if new_game.get("datum") and game.get("datum"):
            if (game["datum"] == new_game["datum"] and
                game["heim"] == new_game["heim"] and
                game["gast"] == new_game["gast"]):
                return True
        # Sonst vergleiche Teams + Ergebnis
        else:
            if (game["heim"] == new_game["heim"] and
                game["gast"] == new_game["gast"] and
                game.get("ergebnis_heim") == new_game.get("ergebnis_heim") and
                game.get("ergebnis_gast") == new_game.get("ergebnis_gast")):
                return True
    return False


def determine_phase(data):
    """Bestimmt die aktuelle Saisonphase basierend auf dem Datum"""
    today = datetime.now()

    if today.month >= 10:
        return "Endklassement"
    elif today.month >= 4:
        return "Regular Season"
    else:
        return "Vorsaison"


# =============================================================================
# SCRAPER: TABELLE
# =============================================================================

def scrape_standings(page):
    """
    Scraped die Tabelle von der ABF Standings-Seite.
    Die Seite rendert serverseitig, daher einfacher Zugriff.

    Returns:
        Liste von Team-Dictionaries mit: rang, name, kuerzel, siege, niederlagen, unentschieden
    """
    print(f"\n[1/3] TABELLE")
    print(f"      URL: {ABF_STANDINGS}")

    page.goto(ABF_STANDINGS, wait_until="networkidle")
    page.wait_for_timeout(2000)

    teams = []

    # Suche nach Tabellen
    tables = page.query_selector_all("table")

    for table in tables:
        rows = table.query_selector_all("tbody tr")

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 5:
                try:
                    rang_text = cells[0].inner_text().strip()
                    rang = int(rang_text) if rang_text.isdigit() else 0

                    team_cell = cells[1].inner_text().strip()
                    lines = team_cell.split('\n')
                    kuerzel = lines[0].strip() if lines else ""
                    name = lines[1].strip() if len(lines) > 1 else team_cell

                    wins = int(cells[2].inner_text().strip())
                    losses = int(cells[3].inner_text().strip())
                    ties = int(cells[4].inner_text().strip()) if len(cells) > 4 else 0

                    if rang > 0 and name:
                        teams.append({
                            "rang": rang,
                            "name": name,
                            "kuerzel": kuerzel,
                            "siege": wins,
                            "niederlagen": losses,
                            "unentschieden": ties
                        })
                except (ValueError, IndexError):
                    continue

    # Duplikate entfernen
    seen = set()
    unique_teams = []
    for team in sorted(teams, key=lambda x: x["rang"]):
        if team["name"] not in seen:
            seen.add(team["name"])
            unique_teams.append(team)

    print(f"      Gefunden: {len(unique_teams)} Teams")

    # Zeige Crazy Geese Position
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
    page.goto(ABF_CALENDAR, wait_until="networkidle")
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

        page.goto(url, wait_until="networkidle")
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

    for i, line in enumerate(lines):
        # Spielnummer
        if line.startswith('#') and ' - ' in line:
            if current_game and 'spielnr' in current_game:
                games.append(current_game)
            current_game = {'spielnr': line, 'phase': phase}
            awaiting_gast = False
            awaiting_heim = False

        # Ort
        elif any(x in line for x in ['Ballpark', 'Cubsfield', 'Sportplatz']):
            if 'ort' not in current_game:
                current_game['ort'] = line

        # GAST marker
        elif line in ['GAST', 'Gast', 'VISITOR']:
            awaiting_gast = True
            awaiting_heim = False

        # HEIM marker
        elif line in ['HEIM', 'Heim', 'HOME']:
            awaiting_heim = True
            awaiting_gast = False

        # Score
        elif re.match(r'^\d+\s*:\s*\d+$', line):
            scores = line.split(':')
            current_game['ergebnis_gast'] = int(scores[0].strip())
            current_game['ergebnis_heim'] = int(scores[1].strip())

        # Teamnamen (nach Kürzel)
        elif awaiting_gast and 'gast' not in current_game:
            if len(line) <= 3 and line.isupper():
                current_game['gast_kuerzel'] = line
            elif len(line) > 3 and 'gast_kuerzel' in current_game:
                current_game['gast'] = line
                awaiting_gast = False
        elif awaiting_heim and 'heim' not in current_game:
            if len(line) <= 3 and line.isupper():
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

    page.goto(ABF_SCHEDULE, wait_until="networkidle")
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
    for click in range(60):  # Max 60 Spieltage
        page.wait_for_timeout(400)
        body = page.inner_text("body")

        # Finde Datum auf der Seite
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4}),\s*(\d{1,2}:\d{2})', body)
        if date_match:
            d, m, y, zeit = date_match.groups()
            datum = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

            # Suche welche unserer Spiele auf dieser Seite sind
            for nr in target_numbers - found_numbers:
                if f'{nr} -' in body:
                    # Finde die Zeit für dieses spezifische Spiel
                    pos = body.find(f'{nr} -')
                    context = body[pos:pos+600]

                    if TEAM_NAME in context:
                        time_match = re.search(r'(\d{1,2}:\d{2})', context)
                        game_zeit = time_match.group(1) if time_match else zeit

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
    print("ABF SCRAPER - Kutro Crazy Geese")
    print("=" * 60)
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Datenquelle: {ABF_BASE}")

    # Bestehende Daten laden
    data = load_data()
    existing_games = data.get("spiele", {}).get("vergangene", [])
    existing_games += data.get("spiele", {}).get("naechste", [])
    print(f"\nBestehende Spiele in data.json: {len(existing_games)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Tabelle scrapen
            teams = scrape_standings(page)
            if teams:
                data["tabelle"]["teams"] = teams
                data["tabelle"]["stand"] = datetime.now().strftime("%Y-%m-%d")
                data["tabelle"]["phase"] = determine_phase(data)

            # 2. Runden und Team-ID holen
            print(f"\n[2/3] SPIELE")
            rounds, team_id = get_rounds_and_team_id(page)

            if not team_id:
                print("      [FEHLER] Team-ID nicht gefunden!")
                return

            # 3. Spiele aus Kalender holen
            new_games = scrape_games_from_calendar(page, rounds, team_id)

            # 4. Spieltage holen
            if new_games:
                new_games = scrape_game_dates(page, new_games)

        finally:
            browser.close()

    # 5. Neue Spiele filtern (keine Duplikate)
    print(f"\n[MERGE]")
    added_count = 0
    today = datetime.now().date()

    vergangene = list(data.get("spiele", {}).get("vergangene", []))
    naechste = list(data.get("spiele", {}).get("naechste", []))

    for game in new_games:
        # Konvertiere zu data.json Format
        formatted_game = {
            "datum": game.get("datum", ""),
            "zeit": game.get("zeit", ""),
            "heim": game.get("heim", ""),
            "gast": game.get("gast", ""),
            "ergebnis_heim": game.get("ergebnis_heim"),
            "ergebnis_gast": game.get("ergebnis_gast"),
            "ort": game.get("ort", ""),
            "phase": game.get("phase", "Regular Season")
        }

        # Prüfe ob Spiel bereits existiert
        all_existing = vergangene + naechste
        if game_exists(all_existing, formatted_game):
            continue

        # Sortiere in vergangene/nächste
        if formatted_game["datum"]:
            game_date = datetime.strptime(formatted_game["datum"], "%Y-%m-%d").date()
            if game_date < today:
                vergangene.append(formatted_game)
            else:
                naechste.append(formatted_game)
        else:
            # Ohne Datum: Wenn Ergebnis vorhanden = vergangen
            if formatted_game.get("ergebnis_heim") is not None:
                vergangene.append(formatted_game)
            else:
                naechste.append(formatted_game)

        added_count += 1
        print(f"      + NEU: {formatted_game['gast']} @ {formatted_game['heim']} ({formatted_game['datum']})")

    # Sortiere nach Datum
    vergangene.sort(key=lambda x: x.get("datum", "9999"))
    naechste.sort(key=lambda x: x.get("datum", "9999"))

    data["spiele"]["vergangene"] = vergangene
    data["spiele"]["naechste"] = naechste
    data["spiele"]["letztes_update"] = datetime.now().strftime("%Y-%m-%d")

    print(f"      Neue Spiele hinzugefügt: {added_count}")
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


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    update_data()
