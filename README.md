# Rohrbach Crazy Geese – Website

Statische Vereinswebsite für die **Rohrbach Crazy Geese** – Baseball in der Landesliga Ost (Österreich).

**Live:** https://crazy-geese.at
**Hosting:** GitHub Pages · Cloudflare DNS/Analytics
**Automation:** GitHub Actions (Scraper an Spieltagen, Daten-Validierung bei jedem PR)

## Seitenstruktur

| Datei | Inhalt |
|-------|--------|
| `index.html` | Landing Page – Spielplan, Tabelle, Mitmachen |
| `baseball.html` | Training, alle Spiele, ICS-Kalender-Download |
| `softball.html` | Slowpitch Softball, ABBQS-Termine |
| `nachwuchs.html` | Kindertraining, Schulkooperationen |
| `blog.html` + `posts/*.html` | News & Berichte |
| `kontakt.html` | Kontakt, Vorstand, Ballpark-Anfahrt |
| `archiv.html` | Saisonarchiv |
| `was-ist-baseball.html` | Baseball-Erklärung für Einsteiger |

## Daten

Alle Vereinsdaten liegen in `data/data.json`. Struktur:
- `verein`, `kontakt`, `tabelle`, `spiele.{naechste,vergangene}`
- `softball.naechste_termine`
- `archiv.YYYY` (Archiv-Zeiger → `data/archiv/YYYY.json`)
- `blog.posts`

Die ICS-Kalender (`data/crazy-geese-*-2026.ics`) werden von `scripts/generate_ics.py` aus `data.json` regeneriert (im Workflow nach jedem Scraper-Lauf, lokal nach manuellen Änderungen).

## Lokale Entwicklung

```bash
python -m http.server 8000
# → http://localhost:8000
```

## Scraper

Aktualisiert Tabelle + Spiele automatisch von der [Austrian Baseball Softball Federation](https://www.baseballsoftball.at). Läuft via GitHub Actions an allen Spieltagen (alle 3 Stunden 9–21 Uhr MESZ) plus Montag-Backup nach jedem Spieltag.

Manuell:
```bash
pip install playwright
playwright install chromium
python scripts/scraper.py
```

Oder remote:
```bash
gh workflow run "Update Standings"
```

## Blog-Workflow

Neuen Beitrag anlegen: siehe [`CLAUDE.md#neuen-blogpost-anlegen`](CLAUDE.md). Kurz:
1. `python scripts/optimize_blog_images.py --src ... --dst img/blog/<slug> --slug <slug>`
2. `posts/<slug>.html` nach Vorlage
3. Neuen Eintrag in `data/data.json` → `blog.posts`
4. `sitemap.xml` ergänzen

## Daten-Validator

`scripts/validate_data.py` prüft JSON-Schema, Pflichtfelder, Datumsformat, Slug-Eindeutigkeit, eindeutige Spielnummern, Ergebnis-Konsistenz und ob ICS und data.json synchron sind (Cross-Check über DTSTART). Läuft automatisch bei jedem Push/PR auf relevante Pfade (`.github/workflows/validate-data.yml`).

Manuell:
```bash
python scripts/validate_data.py
```

## Dokumentation

Die ausführliche technische Dokumentation (Architektur, Scraper-Details, Datenstruktur, Design-Entscheidungen, häufige Aufgaben) steht in [`CLAUDE.md`](CLAUDE.md).

---

Made with ⚾ for the Crazy Geese
