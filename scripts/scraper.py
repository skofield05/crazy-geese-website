#!/usr/bin/env python3
"""
Scraper für die ABF Baseball-Seite
Aktualisiert die Vereinsdaten automatisch
"""

import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Konfiguration
TEAM_NAME = "Crazy Geese"
TEAM_KUERZEL = "CG"
DATA_FILE = Path(__file__).parent.parent / "data" / "data.json"

# ABF URLs - hier die aktuelle Saison eintragen
ABF_BASE = "https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2025"
ABF_STANDINGS = f"{ABF_BASE}/standings"
ABF_SCHEDULE = f"{ABF_BASE}/schedule-and-results"


def load_data():
    """Lädt die aktuelle data.json"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """Speichert die aktualisierte data.json"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Daten gespeichert: {DATA_FILE}")


def scrape_standings(page):
    """Scraped die Tabelle von der ABF-Seite"""
    print(f"→ Lade Tabelle: {ABF_STANDINGS}")
    page.goto(ABF_STANDINGS, wait_until="networkidle")
    
    teams = []
    
    # Suche nach der Regular Season Tabelle
    tables = page.query_selector_all("table")
    
    for table in tables:
        rows = table.query_selector_all("tbody tr")
        
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 5:
                try:
                    # Rang aus erster Spalte
                    rang_text = cells[0].inner_text().strip()
                    rang = int(rang_text) if rang_text.isdigit() else 0
                    
                    # Teamname aus zweiter Spalte
                    team_cell = cells[1].inner_text().strip()
                    
                    # Kürzel und Name extrahieren
                    lines = team_cell.split('\n')
                    kuerzel = lines[0].strip() if lines else ""
                    name = lines[1].strip() if len(lines) > 1 else team_cell
                    
                    # Statistiken
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
                except (ValueError, IndexError) as e:
                    continue
    
    # Duplikate entfernen und nach Rang sortieren
    seen = set()
    unique_teams = []
    for team in sorted(teams, key=lambda x: x["rang"]):
        if team["name"] not in seen:
            seen.add(team["name"])
            unique_teams.append(team)
    
    print(f"  ✓ {len(unique_teams)} Teams gefunden")
    return unique_teams


def scrape_schedule(page):
    """Scraped den Spielplan von der ABF-Seite (benötigt JavaScript)"""
    print(f"→ Lade Spielplan: {ABF_SCHEDULE}")
    page.goto(ABF_SCHEDULE, wait_until="networkidle")
    
    # Warte auf dynamischen Content
    page.wait_for_timeout(3000)
    
    games = []
    today = datetime.now().date()
    
    # Suche nach Spielkarten
    game_elements = page.query_selector_all("[class*='game'], [class*='match'], .schedule-item, tr[data-game]")
    
    # Alternative: Tabellen-basierte Darstellung
    if not game_elements:
        tables = page.query_selector_all("table")
        for table in tables:
            rows = table.query_selector_all("tbody tr")
            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 4:
                    try:
                        # Versuche Spielinfos zu extrahieren
                        text = row.inner_text()
                        
                        # Prüfe ob Crazy Geese beteiligt
                        if TEAM_NAME.lower() not in text.lower():
                            continue
                        
                        # Datum finden (Format: DD.MM.YYYY oder YYYY-MM-DD)
                        date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
                        if not date_match:
                            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
                        
                        if date_match:
                            # Weitere Parsing-Logik hier
                            pass
                            
                    except Exception as e:
                        continue
    
    # Wenn keine strukturierten Daten gefunden, versuche Text-Parsing
    page_text = page.inner_text("body")
    
    # Hier könnte spezifischeres Parsing implementiert werden
    # basierend auf der tatsächlichen Struktur der ABF-Seite
    
    print(f"  ✓ {len(games)} Spiele gefunden")
    return games


def determine_phase(data):
    """Bestimmt die aktuelle Saisonphase"""
    today = datetime.now()
    
    # Einfache Logik: Nach September = Endklassement
    if today.month >= 10:
        return "Endklassement"
    elif today.month >= 4:
        return "Regular Season"
    else:
        return "Vorsaison"


def update_data():
    """Hauptfunktion: Aktualisiert alle Daten"""
    print("=" * 50)
    print("ABF Scraper für Crazy Geese")
    print("=" * 50)
    
    data = load_data()
    
    with sync_playwright() as p:
        # Browser starten (headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Tabelle scrapen
            teams = scrape_standings(page)
            if teams:
                data["tabelle"]["teams"] = teams
                data["tabelle"]["stand"] = datetime.now().strftime("%Y-%m-%d")
                data["tabelle"]["phase"] = determine_phase(data)
            
            # Spielplan scrapen
            games = scrape_schedule(page)
            if games:
                today = datetime.now().date()
                
                naechste = []
                vergangene = []
                
                for game in games:
                    game_date = datetime.strptime(game["datum"], "%Y-%m-%d").date()
                    if game_date >= today:
                        naechste.append(game)
                    else:
                        vergangene.append(game)
                
                # Sortieren
                naechste.sort(key=lambda x: x["datum"])
                vergangene.sort(key=lambda x: x["datum"], reverse=True)
                
                data["spiele"]["naechste"] = naechste
                data["spiele"]["vergangene"] = vergangene
                data["spiele"]["letztes_update"] = datetime.now().strftime("%Y-%m-%d")
        
        finally:
            browser.close()
    
    # Speichern
    save_data(data)
    
    # Zusammenfassung
    print("\n" + "=" * 50)
    print("Zusammenfassung:")
    print(f"  Tabelle: {len(data['tabelle']['teams'])} Teams")
    
    cg = next((t for t in data["tabelle"]["teams"] if TEAM_KUERZEL in t.get("kuerzel", "")), None)
    if cg:
        print(f"  Crazy Geese: Platz {cg['rang']} ({cg['siege']}W-{cg['niederlagen']}L)")
    
    print("=" * 50)


if __name__ == "__main__":
    update_data()
