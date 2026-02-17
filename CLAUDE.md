# CLAUDE.md – Projektkontext für Claude Code

---
## ⚠️ REMINDER FÜR CLAUDE

**Bei Saisonstart 2026:** Frage den User, ob der neue Spielplan schon verfügbar ist!
Wenn ja → GitHub Actions an die echten Spieltage anpassen (siehe "TODO: Saison 2026").

**Nach Mitgliederversammlung:** Trainingszeiten für "Mitmachen"-Sektion erfragen!
- Kindertraining (bisher Di 17:00-18:00)
- Slowpitch (bisher Di 18:00-20:00)
- Erwachsenen-Training?

---

## TODO: Domain- & E-Mail-Migration (Gandi/Uberspace → Dynadot)

**Ziel:** Weg von Gandi (Private Equity) und Uberspace-Kosten für crazy-geese.at reduzieren.

**Hintergrund:**
- Gandi wurde 2023 von Total Web Solutions (Private Equity) übernommen
- Gandi bietet keine kostenlosen E-Mails mehr
- Dynadot ist unabhängig, nicht PE-owned, und bietet kostenlose E-Mail-Weiterleitung

### Domains

| Domain | Registrar | E-Mail |
|--------|-----------|--------|
| **crazy-geese.at** | Gandi → Dynadot | Uberspace → Dynadot Weiterleitung |
| **berndschmidl.com** | Gandi → Dynadot | Bleibt bei Uberspace |
| **friedrichgradisnik.com** | Gandi → Dynadot | Keine E-Mails |

### Dynadot Preise
- .at Domain: €10.08/Jahr
- .com Domain: ~$10-12/Jahr
- Transfer: €0.30 für .at
- E-Mail-Weiterleitung: Kostenlos (bis 10 Adressen/Domain, 500 Mails/Tag)

### Schritte

1. **Dynadot-Account erstellen**
   - https://www.dynadot.com

2. **Auth-Codes bei Gandi holen**
   - Für alle 3 Domains Transfer-Codes anfordern

3. **Domains zu Dynadot transferieren**
   - Transfer starten mit Auth-Codes
   - Transfer bestätigen (E-Mail)

4. **DNS-Einstellungen bei Dynadot**
   - **crazy-geese.at:** GitHub Pages + E-Mail-Weiterleitung
   - **berndschmidl.com:** MX-Records auf Uberspace setzen
   - **friedrichgradisnik.com:** Nur Website-DNS (falls nötig)

5. **E-Mail-Weiterleitung für crazy-geese.at einrichten**
   - Dynadot Dashboard → Domain → Email Forwarding
   - Alle bisherigen Adressen als Weiterleitungen anlegen

6. **Testen** – E-Mails und Websites prüfen

7. **Uberspace crazy-geese.at Konto kündigen** – erst wenn alles funktioniert!
   - berndschmidl.com Konto bei Uberspace bleibt aktiv

### Einschränkungen E-Mail-Weiterleitung
- **Empfangen:** ✓ Kostenlos
- **Senden:** ✗ Nicht möglich (Antworten kommen von privater Adresse)
- Max. 10 Weiterleitungen pro Domain, 500 Mails/Tag

---

## Was ist das?

Website für den Baseballverein **Rohrbach Crazy Geese** (crazy-geese.at), spielend in der **Baseball Landesliga Ost** (Österreich).

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
  "heim": "Rohrbach Crazy Geese",
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

## Automatische Updates (GitHub Actions)

Der Workflow `.github/workflows/update-standings.yml` ist aktiv und läuft automatisch.

**Aktueller Schedule:**
- Sonntag 22:00 MESZ (20:00 UTC)
- Montag 08:00 MESZ (06:00 UTC) - Backup

**Manuell auslösen:**
```bash
gh workflow run "Update Standings"
```

---

## TODO: Saison 2026

**Wenn der neue Spielplan verfügbar ist:**

1. **GitHub Actions an Spieltage anpassen** - Schedule so ändern, dass der Scraper nur an echten Spieltagen läuft (spart Ressourcen, vermeidet Rate-Limiting):
   ```yaml
   schedule:
     # Beispiel: Nur an Spieltagen alle 3 Stunden
     - cron: '0 9,12,15,18,21 3 5 *'   # 03.05. (Spieltag 1)
     - cron: '0 9,12,15,18,21 17 5 *'  # 17.05. (Spieltag 2)
     # ... etc. für jeden Spieltag
   ```

2. **Scraper auf 2026 umstellen** (siehe "Neue Saison starten")

3. **data.json zurücksetzen** - alte Spiele archivieren oder leeren

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

### 2026-01-18
- TODO: Domain- & E-Mail-Migration von Gandi/Uberspace zu Dynadot dokumentiert
- Dynadot statt Cloudflare (unabhängig, nicht Private Equity)

### 2026-01-15
- GitHub Actions Fix: Schreibrechte für GITHUB_TOKEN
- Backup aller Infos von crazy-geese.at (`data/alte-website-infos.md`)
- 25 Bilder von alter Website gesichert (`data/alte-website-bilder/`)
- Reminder für Saison 2026 hinzugefügt

### 2025-12-24
- Alle 13 Spiele der Saison 2025 importiert
- Neuer Scraper: durchsucht alle Runden automatisch
- Logo integriert (Header + Favicon)
- Farbenblind-freundliches Design (Blau/Orange)
- Kompakter Header
- "Alle Spiele anzeigen" Button
- Dokumentation aktualisiert
