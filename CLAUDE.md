# CLAUDE.md – Projektkontext für Claude Code

## Was ist das?

Website für den Baseballverein **Kutro Crazy Geese** (crazy-geese.at), spielend in der **Baseball Landesliga Ost** (Österreich).

## Architektur

Statische Website, gehostet auf GitHub Pages. Keine Datenbank, kein Backend.

```
index.html      → Lädt data.json per JavaScript und rendert die Seite
style.css       → Responsive Design, mobile-first
data/data.json  → Alle Vereinsdaten (Tabelle, Spiele, Kontakt)
scripts/        → Python Scraper für automatische Updates
```

## Datenquelle

Die Ligadaten kommen von der Austrian Baseball Softball Federation:
- Tabelle: https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2025/standings
- Spielplan: https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2025/schedule-and-results

Die Tabellen-Seite rendert serverseitig (einfacher Fetch reicht).
Der Spielplan lädt per JavaScript nach (braucht Playwright/Headless Browser).

## Häufige Aufgaben

### Spielergebnis eintragen
Bearbeite `data/data.json` → `spiele.vergangene`, füge neues Spiel hinzu:
```json
{
  "datum": "2025-04-20",
  "zeit": "14:00",
  "heim": "Kutro Crazy Geese",
  "gast": "Vienna Bucks",
  "ergebnis_heim": 12,
  "ergebnis_gast": 4,
  "ort": "Heimplatz"
}
```

### Tabelle aktualisieren
Entweder `python scripts/scraper.py` laufen lassen, oder manuell in `data/data.json` → `tabelle.teams` die Werte anpassen.

### Neue Saison starten
1. In `data/data.json`: `verein.saison` ändern
2. In `scripts/scraper.py`: `ABF_BASE` URL auf neue Saison ändern
3. Tabelle und Spiele zurücksetzen

### Kontaktdaten ändern
Bearbeite `data/data.json` → `kontakt`

## GitHub Actions

Der Workflow `.github/workflows/update-standings.yml` läuft automatisch:
- Sonntag 22:00 Uhr (nach Spieltagen)
- Montag 08:00 Uhr (Backup)

Kann auch manuell getriggert werden über GitHub → Actions → Run workflow.

## Design

- Dark Theme mit Grün als Primärfarbe (Vereinsfarben anpassbar in style.css)
- Mobile-first, responsive
- Fonts: Bebas Neue (Headlines), Source Sans 3 (Body)

## Wichtige Pfade

- Vereinsdaten: `data/data.json`
- Styling anpassen: `style.css` (CSS Variables am Anfang)
- Scraper-URLs: `scripts/scraper.py` (ABF_BASE Variable)
