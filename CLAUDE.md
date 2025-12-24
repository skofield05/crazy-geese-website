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

Die Ligadaten kommen von der Austrian Baseball Softball Federation (ABF):

| Seite | URL | Rendering |
|-------|-----|-----------|
| Tabelle | `/standings` | Serverseitig |
| Kalender | `/calendars` | Serverseitig (mit Filtern) |
| Spielplan | `/schedule-and-results` | JavaScript (Datepicker) |

**Basis-URL:** `https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-YYYY`

### Scraper-Logik

Der Scraper (`scripts/scraper.py`) holt Daten in 3 Schritten:

1. **Tabelle** von `/standings` - Team-Platzierungen
2. **Spiele** von `/calendars` - Durchsucht alle Runden (Regular Season, Playoffs, Platzierungsrunde) mit Team-Filter
3. **Spieltage** von `/schedule-and-results` - Navigiert durch Datepicker für echte Daten

**WICHTIG:** Die Kalender-Seite hat einen Bug und zeigt das aktuelle Datum statt des echten Spieldatums. Daher werden die Daten separat von der Schedule-Seite geholt.

### Duplikat-Vermeidung

Der Scraper fügt nur NEUE Spiele hinzu. Ein Spiel gilt als Duplikat wenn:
- Datum + Heim + Gast übereinstimmen, ODER
- Heim + Gast + Ergebnis übereinstimmen (falls Datum fehlt)

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
1. In `scripts/scraper.py`: `ABF_BASE` URL auf neue Saison ändern (z.B. `baseball-landesliga-ost-2026`)
2. In `data/data.json`: `verein.saison` ändern
3. In `data/data.json`: `verein.abf_url` aktualisieren
4. Optional: `spiele.vergangene` leeren für frischen Start (oder behalten für Historie)
5. Scraper laufen lassen: `python scripts/scraper.py`

**Hinweis:** Der Scraper erkennt automatisch:
- Alle verfügbaren Runden (Regular Season, Playoffs, etc.)
- Die Team-ID der Crazy Geese
- Bereits vorhandene Spiele werden nicht doppelt eingetragen

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

## Scraper Details

### Installation
```bash
pip install playwright
python -m playwright install chromium
```

### Ausführung
```bash
python scripts/scraper.py
```

### Ablauf
1. Lädt bestehende `data.json`
2. Scraped Tabelle von `/standings`
3. Extrahiert Runden-IDs und Team-ID automatisch von `/calendars`
4. Durchsucht alle Runden (Regular Season, Playoffs, Platzierungsrunde)
5. Holt echte Spieltage von `/schedule-and-results` via Datepicker-Navigation
6. Merged neue Spiele (keine Duplikate)
7. Speichert aktualisierte `data.json`

### Datepicker-Navigation
Die Schedule-Seite hat einen Datepicker mit 3 Buttons:
- Button 0: Linker Pfeil (vorheriger Spieltag)
- Button 1: Kalender-Icon
- Button 2: Rechter Pfeil (nächster Spieltag)

Der Scraper navigiert 30x zurück zum Saisonstart, dann vorwärts durch alle Spieltage.

## Wichtige Pfade

- Vereinsdaten: `data/data.json`
- Styling anpassen: `style.css` (CSS Variables am Anfang)
- Scraper: `scripts/scraper.py` (ABF_BASE Variable für neue Saison anpassen)
