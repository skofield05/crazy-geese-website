# 🪿 Kutro Crazy Geese – Website

Statische Vereinswebsite für die Crazy Geese Baseball, automatisch aktualisiert via GitHub Actions.

## Setup

### 1. Repository erstellen

```bash
# Neues Repo auf GitHub erstellen: crazy-geese-website
# Dann lokal:
git init
git remote add origin https://github.com/DEIN-USERNAME/crazy-geese-website.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 2. GitHub Pages aktivieren

1. Gehe zu **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **(root)**
4. Save

Die Seite ist dann unter `https://DEIN-USERNAME.github.io/crazy-geese-website/` erreichbar.

### 3. Custom Domain (optional)

Für `crazy-geese.at`:

1. Erstelle eine Datei `CNAME` mit dem Inhalt: `crazy-geese.at`
2. Bei deinem Domain-Provider: CNAME-Eintrag auf `DEIN-USERNAME.github.io` setzen

## Dateien

```
├── index.html          # Hauptseite
├── style.css           # Styling
├── data/
│   └── data.json       # Alle Vereinsdaten (wird automatisch aktualisiert)
├── scripts/
│   └── scraper.py      # ABF-Scraper
└── .github/
    └── workflows/
        └── update-standings.yml  # Automatische Aktualisierung
```

## Daten anpassen

Bearbeite `data/data.json`:

- **Kontaktdaten**: Email, Adresse, Social Media
- **Vereinsinfos**: Name, Liga, Saison

## Automatische Updates

Der GitHub Actions Workflow läuft automatisch:
- **Sonntag 22:00** (nach den Spielen)
- **Montag 08:00** (Backup)

Manuell auslösen: **Actions → Update Standings → Run workflow**

## Lokale Entwicklung

```bash
# Einfacher Webserver
python -m http.server 8000

# Dann öffnen: http://localhost:8000
```

## Scraper testen

```bash
pip install playwright
playwright install chromium

python scripts/scraper.py
```

## Saison-Update

Für eine neue Saison die URLs in `scripts/scraper.py` anpassen:

```python
ABF_BASE = "https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2026"
```

---

Made with ⚾ for the Crazy Geese
