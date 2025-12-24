# CLAUDE.md – Projektkontext für Claude Code

## Was ist das?

Website für den Baseballverein **Kutro Crazy Geese** (crazy-geese.at), spielend in der **Baseball Landesliga Ost** (Österreich).

**Live:** https://skofield05.github.io/crazy-geese-website/
**Repo:** https://github.com/skofield05/crazy-geese-website

## Architektur

Statische Website, gehostet auf GitHub Pages. Keine Datenbank, kein Backend.

```
index.html        → Hauptseite (lädt data.json per JavaScript)
style.css         → Styling (CSS Variables für Farben)
data/data.json    → Alle Daten (Tabelle, Spiele, Kontakt)
scripts/scraper.py → Python Scraper für automatische Updates
geese_logo.png    → Vereinslogo (auch Favicon)
CLAUDE.md         → Diese Dokumentation
```

## Aktuelle Saison (2025)

- **Ergebnis:** 13 Siege, 0 Niederlagen – **MEISTER!**
- **Finale:** 12:1 gegen Danube Titans (20.09.2025)
- Alle 13 Spiele sind in `data/data.json` gespeichert

---

## Datenquelle: ABF Website

Die Ligadaten kommen von der Austrian Baseball Softball Federation:

| Seite | URL-Suffix | Rendering | Verwendung |
|-------|------------|-----------|------------|
| Tabelle | `/standings` | Serverseitig | Team-Platzierungen |
| Kalender | `/calendars` | Serverseitig | Spiele + Ergebnisse (mit Filter) |
| Spielplan | `/schedule-and-results` | JavaScript | Echte Spieltage |

**Basis-URL:** `https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-YYYY`

### Bekannter ABF-Bug

Die Kalender-Seite (`/calendars`) zeigt das **aktuelle Datum** statt des echten Spieldatums an. Daher holt der Scraper:
1. Spiele + Ergebnisse von `/calendars` (mit Team-Filter)
2. Echte Spieltage separat von `/schedule-and-results` (via Datepicker-Navigation)

---

## Scraper (`scripts/scraper.py`)

### Installation

```bash
pip install playwright
python -m playwright install chromium
```

### Ausführung

```bash
cd crazy-geese-website
python scripts/scraper.py
```

### Was der Scraper macht

1. **Tabelle laden** von `/standings`
2. **Runden-IDs extrahieren** automatisch von `/calendars` (Regular Season, Playoffs, Platzierungsrunde)
3. **Team-ID finden** automatisch aus Dropdown (Crazy Geese = 35667 für 2025)
4. **Alle Runden durchsuchen** mit Team-Filter
5. **Spieltage holen** von `/schedule-and-results`:
   - Navigiert 30x zurück zum Saisonstart
   - Geht vorwärts durch alle Spieltage
   - Matcht Spielnummern (#1, #3, etc.) mit Daten
6. **Duplikate vermeiden** - nur neue Spiele werden hinzugefügt
7. **data.json speichern**

### Datepicker-Navigation

Die Schedule-Seite hat einen Datepicker mit 3 Buttons im `.date-picker`:
- `buttons[0]`: Linker Pfeil (← vorheriger Spieltag)
- `buttons[1]`: Kalender-Icon (ignorieren)
- `buttons[2]`: Rechter Pfeil (→ nächster Spieltag)

### Duplikat-Erkennung

Ein Spiel gilt als Duplikat wenn:
- Datum + Heim + Gast übereinstimmen, ODER
- Heim + Gast + Ergebnis übereinstimmen (falls Datum fehlt)

---

## Häufige Aufgaben

### Scraper laufen lassen (empfohlen)

```bash
python scripts/scraper.py
```

Holt automatisch neue Spiele und aktualisiert die Tabelle.

### Manuell Spiel eintragen

In `data/data.json` → `spiele.vergangene`:

```json
{
  "datum": "2025-05-03",
  "zeit": "11:00",
  "heim": "Kutro Crazy Geese",
  "gast": "Vienna Bucks",
  "ergebnis_heim": 14,
  "ergebnis_gast": 4,
  "ort": "Geese Ballpark, Rohrbach bei Mattersburg",
  "phase": "Regular Season"
}
```

### Neue Saison starten (z.B. 2026)

1. **Scraper anpassen** (`scripts/scraper.py`):
   ```python
   ABF_BASE = "https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2026"
   ```

2. **data.json anpassen**:
   ```json
   "verein": {
     "saison": "2026",
     "abf_url": "https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2026"
   }
   ```

3. **Optional:** `spiele.vergangene` und `spiele.naechste` leeren

4. **Scraper ausführen:**
   ```bash
   python scripts/scraper.py
   ```

Der Scraper erkennt automatisch die neuen Runden-IDs und Team-IDs.

---

## Design

### Farben (Farbenblind-freundlich)

```css
/* In style.css :root */
--color-primary: #1e2d4d;     /* Navy Blau (Logo) */
--color-win: #2563eb;         /* Blau für Siege */
--color-loss: #ea580c;        /* Orange für Niederlagen */
--color-tie: #a3a3a3;         /* Grau für Unentschieden */
```

**Warum Blau/Orange?** Für Rot-Grün-Schwäche optimal unterscheidbar.

### Logo

- Datei: `geese_logo.png`
- Verwendet als: Header-Logo + Favicon
- Farben: Navy (#1e2d4d), Rot, Weiß

### Fonts

- Headlines: Bebas Neue
- Body: Source Sans 3

---

## Automatische Updates (TODO)

Für automatische Updates via GitHub Actions:

### Geplanter Workflow (`.github/workflows/update-standings.yml`)

```yaml
name: Update Standings

on:
  schedule:
    # Sonntag 22:00 UTC (nach Spieltagen)
    - cron: '0 22 * * 0'
    # Montag 08:00 UTC (Backup)
    - cron: '0 8 * * 1'
  workflow_dispatch:  # Manueller Trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install playwright
          playwright install chromium

      - name: Run scraper
        run: python scripts/scraper.py

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/data.json
          git diff --staged --quiet || git commit -m "Auto-update standings"
          git push
```

### Aktivierung

1. Datei `.github/workflows/update-standings.yml` erstellen
2. In GitHub → Settings → Actions → General:
   - "Allow all actions" aktivieren
   - "Read and write permissions" für GITHUB_TOKEN

---

## Wichtige Pfade

| Was | Wo |
|-----|-----|
| Vereinsdaten | `data/data.json` |
| Styling/Farben | `style.css` (CSS Variables am Anfang) |
| Scraper-URL | `scripts/scraper.py` → `ABF_BASE` Variable |
| Logo | `geese_logo.png` |

---

## Changelog

### 2025-12-24
- Alle 13 Spiele der Saison 2025 importiert
- Neuer Scraper: durchsucht alle Runden automatisch
- Logo integriert (Header + Favicon)
- Farbenblind-freundliches Design (Blau/Orange)
- Kompakter Header
- "Alle Spiele anzeigen" Button
- Dokumentation aktualisiert
