# CLAUDE.md – Projektkontext für Claude Code

---
## Was ist das?

Website für den Baseballverein **Rohrbach Crazy Geese** (crazy-geese.at), spielend in der **Baseball Landesliga Ost** (Österreich).

**Live:** https://crazy-geese.at
**Repo:** https://github.com/skofield05/crazy-geese-website

---

## Aktuelle Saison (2026)

- **Liga:** Baseball Landesliga Ost
- **Teamname:** Rohrbach Crazy Geese (bis 2025: "Kutro Crazy Geese")
- **Vorjahr:** 2025 – 13 Siege, 0 Niederlagen – **MEISTER!**
- **Spielplan 2026:** 16 Spiele (8 Spieltage, Mai–August), verifiziert gegen Excel + ABF
- **E-Mail:** crazygeese93@gmail.com (keine @crazy-geese.at Adressen mehr)

### Trainingszeiten

| Sportart | Wann | Kontakt |
|----------|------|---------|
| **Baseball** | Sonntag ab 15:00, Mittwoch ab 18:00 (Pitcher/Catcher) | — |
| **Kindertraining** | Montag & Donnerstag ab 17:00 | Joey Vickery, Harald (Harry) Burian |
| **Slowpitch Softball** | Termine werden bekanntgegeben | Mike Rigby, Thomas Kissich |

### Vorstand (laut Vereinsregisterauszug 2025)

| Name | Funktion |
|------|----------|
| Thomas Soffried | Obmann |
| Jörg Dorner | Obmann Stellvertreter |
| Christian Suchard | Kassier |
| Maria Fridecky | Kassier Stellvertreterin |
| Mike Rigby | Schriftführer |
| Thomas Kissich | Schriftführer Stellvertreter |

---

## Architektur

Statische Website, gehostet auf GitHub Pages. Keine Datenbank, kein Backend.

```
index.html                          → Landing Page (Spielplan, Tabelle, Mitmachen)
baseball.html                       → Baseball-Seite (Training, alle Spiele, ICS-Download)
softball.html                       → Slowpitch Softball
nachwuchs.html                      → Kindertraining & Schulkooperationen
kontakt.html                        → Kontakt, Vorstand, Ballpark
archiv.html                         → Saisonarchiv (2025)
blog.html                           → Blog-Übersicht (rendert data.blog.posts)
posts/<slug>.html                   → Einzelne Blogbeiträge
was-ist-baseball.html               → Erklär-Seite
style.css                           → Styling (CSS Variables, responsive, barrierefrei)
data/data.json                      → Alle Daten (Tabelle, Spiele, Kontakt, Softball, Blog)
data/*.ics                          → Kalender-Dateien (alle Spiele + nur Heimspiele)
scripts/scraper.py                  → Python Scraper für automatische Updates (ABF -> data.json)
scripts/generate_ics.py             → Regeneriert beide ICS aus data.json
scripts/validate_data.py            → Schema-Check (Pflichtfelder, Eindeutigkeit, ICS-Sync)
scripts/shared.js                   → Gemeinsame JS-Helpers (escapeHtml, fetchJson, Render)
scripts/lightbox.js                 → Wiederverwendbare Lightbox für Blog-Galerien
scripts/optimize_blog_images.py     → Einmal-Helper für Blog-Bildaufbereitung
img/blog/<slug>/                    → Aufbereitete Blog-Bilder (full + thumb)
geese_logo.png                      → Vereinslogo (Header, Favicon, Hero-Hintergrund)
.github/workflows/                  → GitHub Actions (Scraper an Spieltagen)
```

### Landing Page (index.html)

- **Hero-Bereich:** Logo als dezenter Hintergrund (Blur + Puls-Animation)
- **Zwei Highlight-Karten:** "Nächstes Spiel" + "Nächstes Heimspiel" (prominent)
- **Spielplan-Liste:** Weitere Spiele mit BASEBALL/SOFTBALL + HEIM/AUSWÄRTS Tags
- **Tabelle:** Baseball Landesliga Ost
- **Mitmachen:** Einladung zum Schnuppertraining
- **Sponsoren**
- Baseball + Softball Termine werden chronologisch zusammengeführt

### Daten-Struktur (data.json)

```json
{
  "verein": { "name", "saison", "website", "abf_url" },
  "kontakt": { "ansprechpartner", "email", "adresse", "social" },
  "tabelle": { "phase", "teams": [...] },
  "spiele": { "naechste": [...], "vergangene": [...] },
  "events": [ { "slug", "titel", "datum", "zeit", "ort", "highlights": [], "kontakt_email", "kontakt_telefon", "kontakt_telefon_name", "instagram_post_url" } ],
  "softball": { "naechste_termine": [] },
  "archiv": { "2025": { "ergebnis", "bilanz", "datei" } },
  "blog": { "posts": [ { "slug", "url", "titel", "datum", "kategorie", "teaser", "cover", "cover_alt" } ] }
}
```

`events` ist optional (z.B. Slowpitch Firmenturnier). page-index.js rendert pro zukunftigem Event eine eigene `highlight-card.highlight-event` neben Spiel/Heimspiel. Karte verschwindet automatisch, sobald `datum < today`.

---

## Datenquelle: ABF Website

Die Ligadaten kommen von der Austrian Baseball Softball Federation:

| Seite | URL-Suffix | Rendering | Verwendung |
|-------|------------|-----------|------------|
| Tabelle | `/standings` | Serverseitig | Team-Platzierungen |
| Kalender | `/calendars` | Serverseitig | Spiele + Ergebnisse (mit Filter) |
| Spielplan | `/schedule-and-results` | JavaScript | Echte Spieltage |

**Basis-URL:** `https://www.baseballsoftball.at/de/events/baseball-landesliga-ost-2026`

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
2. **Runden-IDs extrahieren** automatisch von `/calendars`
3. **Team-ID finden** automatisch aus Dropdown
4. **Alle Runden durchsuchen** mit Team-Filter
5. **Spieltage holen** von `/schedule-and-results` (Datepicker-Navigation)
6. **Duplikate vermeiden** - nur neue Spiele werden hinzugefügt
7. **data.json speichern**

### Scraper-Filter (2026-04-20)

Der Scraper verarbeitet ABF-Daten:
- **Normalisierung:** Die ABF-Datenbank führt uns teils noch als "Kutro Crazy Geese" – Teamnamen werden beim Import auf "Rohrbach Crazy Geese" umgeschrieben (Tabelle + Spiele)
- **Ghost-Filter:** Einträge ohne Datum **und** ohne Ergebnis werden verworfen
- **Dedup:** Match auf (datum, heim, gast) bzw. (heim, gast) wenn ein Datum fehlt – damit Geisterdaten nicht neben echten Einträgen landen
- **Mutation-Fix:** `existing_games` wird als Kopie gebaut, damit die Aggregation nicht `vergangene` mit `naechste` erweitert

---

## Automatische Updates (GitHub Actions)

Der Workflow `.github/workflows/update-standings.yml` ist aktiv und läuft automatisch.

**Schedule:** An jedem Spieltag alle 3 Stunden (9-21 Uhr MESZ) + Backup am Montag danach.

Spieltage 2026: 03.05., 16.05., 23.05., 13.06., 20.06., 19.07., 02.08., 15.08.
Playoffs: 05.-06.09., 12.-13.09.

**Manuell auslösen:**
```bash
gh workflow run "Update Standings"
```

---

## Design

### Farben (Farbenblind-freundlich)

```css
--color-primary: #191934;     /* Navy Blau (Logo) */
--color-win: #2563eb;         /* Blau für Siege */
--color-loss: #ea580c;        /* Orange für Niederlagen */
--color-tie: #a3a3a3;         /* Grau für Unentschieden */
```

**Warum Blau/Orange?** Für Rot-Grün-Schwäche optimal unterscheidbar.

### Sport-Tags

| Tag | Farbe | Verwendung |
|-----|-------|------------|
| BASEBALL | Navy | Baseball-Spiele |
| SOFTBALL | Lila (#7c3aed) | Softball-Termine |
| HEIM | Blau (#2563eb) | Heimspiele |
| AUSWÄRTS | Grau | Auswärtsspiele |

### Logo

- Datei: `geese_logo.png`
- Verwendet als: Header-Logo, Favicon, Hero-Hintergrund (transparent + blur)

### Fonts

- Headlines: Bebas Neue
- Body: Raleway

### Barrierefreiheit

- Skip-Links auf allen Seiten
- ARIA-Labels (Navigation, Tabelle, Mobile-Menü)
- Fokus-Styles für Tastaturnavigation
- Farben nie alleiniger Informationsträger (immer auch Text)
- Telefonnummern als klickbare `tel:` Links

---

## Kalender-Dateien (ICS)

Zwei ICS-Dateien für Kalender-Import:
- `data/crazy-geese-alle-spiele-2026.ics` – Alle Spiele
- `data/crazy-geese-heimspiele-2026.ics` – Nur Spiele am Geese Ballpark, Rohrbach

Beide werden von `scripts/generate_ics.py` aus `data/data.json` regeneriert (im Workflow nach jedem Scraper-Lauf, lokal nach manuellen Änderungen). Konventionen:

- SUMMARY: `GAST vs HEIM` (Baseball-Konvention)
- Suffix `(HEIM)` wenn Crazy Geese formal heim und Spielort in Rohrbach
- Suffix `(in Rohrbach)` wenn Crazy Geese formal Gast aber Spielort Rohrbach
- UID stabil als `cg-YYYY-MM-DD-HHMM@crazy-geese.at`

Download-Buttons auf `baseball.html`.

---

## Domain & Hosting

| Was | Wo |
|-----|-----|
| Domain | crazy-geese.at (Cloudflare DNS) |
| Hosting | GitHub Pages |
| E-Mail | crazygeese93@gmail.com (keine @crazy-geese.at mehr) |
| Analytics | Cloudflare Web Analytics |

---

## Häufige Aufgaben

### Scraper laufen lassen

```bash
python scripts/scraper.py
# oder remote:
gh workflow run "Update Standings"
```

### Softball-Termine eintragen

In `data/data.json` → `softball.naechste_termine`:

```json
{
  "datum": "2026-06-01",
  "zeit": "18:00",
  "gegner": "Team XY",
  "ort": "Geese Ballpark, Rohrbach"
}
```

Erscheinen automatisch auf der Landing Page mit SOFTBALL-Tag.

### ICS-Dateien regenerieren

```bash
python scripts/generate_ics.py
```

Liest `data/data.json` und schreibt beide ICS-Dateien neu. Wird im `update-standings.yml`-Workflow automatisch nach dem Scraper aufgerufen.

### Manuell Spiel eintragen

In `data/data.json` → `spiele.vergangene`:

```json
{
  "datum": "2026-05-03",
  "zeit": "13:30",
  "heim": "Rohrbach Crazy Geese",
  "gast": "Woodquarter Red Devils",
  "ergebnis_heim": 10,
  "ergebnis_gast": 3,
  "ort": "Sportzentrum Spenadlwiese, Wien",
  "phase": "Grunddurchgang"
}
```

### Neuen Blogpost anlegen

1. **Bilder aufbereiten:** Quellbilder (z.B. aus WhatsApp) in einen beliebigen Ordner legen, dann:
   ```bash
   python scripts/optimize_blog_images.py \
     --src "<Quellordner>" \
     --dst "img/blog/<slug>" \
     --slug <slug-kurzform>
   ```
   Erzeugt zu jedem Bild eine `-<nn>.jpg` (max. 1600px, Lightbox) und `-<nn>-thumb.jpg` (max. 800px, Galerie-Kachel). Slug ohne Datum, z.B. `schulcup-mattersburg`.

2. **Artikel-HTML anlegen:** `posts/<slug>.html` – als Vorlage den bestehenden Artikel kopieren. Wichtige Stellen:
   - `<title>`, `<meta description>`, Canonical, OG-Tags, `article:published_time`
   - `IMG_BASE`, `TOTAL`, `slug`-Präfix im Bildpfad im inline-Script anpassen
   - `aria-current="page"` auf dem Blog-Nav-Link lassen

3. **data.json erweitern:** Neuen Eintrag in `blog.posts` (neueste zuerst):
   ```json
   {
     "slug": "schulcup-mattersburg-2026-04",
     "url": "posts/schulcup-mattersburg-2026-04.html",
     "titel": "Baseball-Schulcup an der NMS Mattersburg",
     "datum": "2026-04-22",
     "kategorie": "Nachwuchs",
     "teaser": "…",
     "cover": "img/blog/<slug>/<slug>-01-thumb.jpg",
     "cover_alt": "…"
   }
   ```
   `blog.html` sortiert automatisch nach `datum` absteigend.

4. **Sitemap erweitern:** `sitemap.xml` um `blog.html` (bei Erstanlage) und `posts/<slug>.html` ergänzen.

5. **Smoke-Test:** Lokal `python -m http.server` im Repo-Root, dann Artikel + Galerie + Lightbox im Browser durchklicken (Prev/Next/ESC/Swipe).

### Neuen Sponsor eintragen

Die Sponsorenliste ist hardcoded in `index.html` → `#sponsoren` → `.sponsors-grid` (nicht datengetrieben). Vorgehen:

1. **Logo aufbereiten** und als PNG mit Alpha unter `img/sponsoren/<slug>.png` ablegen. Zielgrösse ca. 400 px breit. **Helle/weisse Logo-Variante verwenden** — die Sponsoren-Section liegt auf `--color-bg-card` (#161b22, fast schwarz), schwarze Logos auf Alpha-Hintergrund sind dort unsichtbar. Der CSS-Filter `grayscale(100%) brightness(1.2)` rettet nur leicht-graue Bereiche, nicht echtes Schwarz. Wenn der Sponsor mehrere Varianten liefert (z. B. EPS farbig + PSD weiss), die weisse nehmen. Die anderen bestehenden Sponsoren-JPGs werden nur sichtbar, weil sie weissen Hintergrund eingebrannt haben.

   Vektor-Quellen (EPS/AI/PDF) per Ghostscript auf hohe DPI rendern, dann mit Pillow auf 400 px Breite skalieren:
   ```bash
   # EPS -> PNG (alpha, 600 dpi, EPS-Bounding-Box croppen):
   gswin64c -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pngalpha -r600 -dEPSCrop \
     -sOutputFile=tmp.png "Sponsoren/<sponsor>/logo.eps"
   # dann mit Pillow trimmen + auf 400 px skalieren
   ```
   Bei Logos mit Claim/Beiwerk (z. B. „we make IT" neben der Marke) den Claim wegschneiden — bei 50 px Anzeigehöhe in der Grid wäre der ohnehin unter 10 px hoch und unleserlich. Verlässlicher als ein Fix-Prozent-Crop: spaltenweise Alpha-Analyse mit `numpy` findet die Lücke zwischen Marke und Claim.

2. **Eintrag in `index.html`** in `.sponsors-grid` ergänzen (Pattern der existierenden Einträge folgen):
   ```html
   <a href="https://<sponsor-url>/" target="_blank" rel="noopener" class="sponsor-logo" title="<Sponsorname>">
     <img loading="lazy" src="img/sponsoren/<slug>.png" alt="<Sponsorname>">
   </a>
   ```

3. **Quelldateien** (EPS/PSD/AI) gehören NICHT ins Repo — analog zu `.xls` und `.pdf`. Liegen sie unter einem eigenen Ordner (z. B. `Sponsoren/`), per `/<ordner>/` in `.gitignore` filtern. **Führender Slash ist wichtig**, sonst filtert die Regel auf Windows wegen Case-Insensitivity auch `img/sponsoren/` weg (`git check-ignore -v <pfad>` zur Verifikation).

---

## Wichtige Pfade

| Was | Wo |
|-----|-----|
| Vereinsdaten | `data/data.json` |
| Styling/Farben | `style.css` (CSS Variables am Anfang) |
| Scraper-URL | `scripts/scraper.py` → `ABF_BASE` Variable |
| GitHub Actions | `.github/workflows/update-standings.yml` |
| Spielplan (Excel) | `Landesliga Ost 2026 Spielplan V1.xls` (nicht im Repo) |
| Vereinsregisterauszug | `Vereinsregisterauszug_CrazyGeese_2025.pdf` (nicht im Repo) |
| Logo | `geese_logo.png` |
| ICS-Kalender | `data/crazy-geese-*-2026.ics` |
| Blog-Artikel | `posts/<slug>.html` |
| Blog-Bilder | `img/blog/<slug>/` (full + thumb) |
| Blog-Helpers | `scripts/lightbox.js`, `scripts/optimize_blog_images.py` |
| Page-Bootstraps | `scripts/page-<name>.js` (index, baseball, blog, archiv, softball), `scripts/post-<slug>.js` |
| Metrostars-Fallback | `scripts/metrostars.py` (HTTP-only Backup-Datenquelle, vom Scraper importiert) |
| Python-Deps | `requirements.txt` (Playwright, gepinnt) |

---

## TODO

- [ ] Hintergrundbild: besseres Foto statt Logo (Actionfoto oder Teamfoto)
- [ ] Schema.org JSON-LD Markup für bessere Google-Ergebnisse
- [ ] Nachwuchs-Emoji: besseres als Baby-Emoji finden

---

## Changelog

### 2026-05-26
- **Neuer Sponsor:** NIC Solutions (https://nic-solutions.at/) in der Sponsorenleiste auf `index.html`. Logo aus EPS-Quelle ueber Ghostscript (TinyTeX) auf 600 dpi mit Alpha gerendert; Claim „we make IT" weggeschnitten via spaltenweiser Alpha-Analyse (findet die Luecke zwischen Marke und Claim, ohne in den Text reinzuschneiden); auf 400 px Breite skaliert -> `img/sponsoren/nic-solutions.png` (16 KB, 400x219). Quelldateien liegen lokal in `Sponsoren/nic/`
- **`.gitignore`:** `/Sponsoren/` ergaenzt (analog zu `*.xls`/`*.pdf`). Fuehrender Slash ist load-bearing — ohne ihn wuerde die Regel auf Windows wegen Case-Insensitivity auch `img/sponsoren/` filtern und alle Sponsor-Logos verstecken. Mit `git check-ignore -v` verifiziert
- **Doku:** „Neuen Sponsor eintragen" in „Haeufige Aufgaben" ergaenzt (EPS->PNG-Workflow, .gitignore-Gotcha)
- **Fix:** PNG durch weisse PSD-Variante ersetzt — die zuerst genommene EPS-Variante (schwarze Schrift auf Alpha) war auf `--color-bg-card` (#161b22) unsichtbar. Der CSS-Filter `grayscale + brightness(1.2)` macht echtes Schwarz nicht hell genug; die anderen Sponsor-JPGs funktionieren nur, weil sie weissen Hintergrund eingebrannt haben. „Haeufige Aufgaben" entsprechend korrigiert

### 2026-05-22
- **Event-Karte auf Landing Page:** Neuer optionaler Top-Level-Key `events` in `data.json` fuer Veranstaltungen ausserhalb des regulaeren Spielplans (Slowpitch Firmenturnier 30.05. als Erstanwendung). `page-index.js` rendert eine dritte `highlight-card.highlight-event` (Lila, Softball-Akzentfarbe) neben Spiel/Heimspiel mit Datum, Ort, Highlights-Liste und Mail-/Tel-CTAs sowie sekundaerem Link zum IG-Post. Karte verschwindet automatisch nach `event.datum`
- **Grid-Refactor:** `.hero-highlights` von festem `1fr 1fr` auf `repeat(auto-fit, minmax(280px, 1fr))` umgestellt — 1/2/3 sichtbare Karten passen jetzt ohne Sonderfall-CSS. Single-Layout (eine zentrierte Karte) greift nur noch, wenn sameGame UND kein Event aktiv ist
- **Validator:** `validate_data.py` um `_check_events()` erweitert (titel+datum pflicht, datum/zeit-Format, `instagram_post_url`-Regex)

### 2026-05-04
- **Security/CSP-Haertung:** `'unsafe-inline'` aus `script-src` und `style-src` der CSP entfernt (alle 9 HTML-Files konsistent). Dazu pro Seite ein per-page Bootstrap nach `scripts/page-<name>.js` ausgelagert (`page-index`, `page-baseball`, `page-blog`, `page-archiv`, `page-softball`, `post-schulcup-mattersburg`); einfache Seiten (kontakt, nachwuchs, was-ist-baseball) brauchen keinen eigenen Bootstrap mehr, weil `shared.js` jetzt am Ende `setFooterYear()` + `setupMobileMenu()` selbst aufruft (idempotent via `dataset.menuInit`-Guard). Eine letzte Inline-`style=`-Stelle in `nachwuchs.html` durch `.schule-interesse`-Klasse ersetzt
- **Workflow als Gate:** `update-standings.yml` ruft `validate_data.py` jetzt zwischen Scraper und ICS-Regenerierung auf — bei kaputten Daten wird nicht mehr committet. Dependencies via neuer `requirements.txt` (Playwright auf 1.57.0 gepinnt) statt `pip install playwright` ohne Pin
- **Validator schaerfer:** `REQUIRED_GAME_FIELDS` jetzt `(datum, heim, gast, spielnr)` (vorher ohne `spielnr`); `RECOMMENDED_GAME_FIELDS` (`zeit, ort, phase`) als Warnung. Saison-Regex `^(19|20)\d{2}$`. UID-Duplikat-Check auf `Counter` (O(n))
- **Scraper-Fixes:** `datetime.now()` durchgaengig auf `Europe/Vienna` umgestellt (GitHub-Runner laufen UTC -> Spielzeitvergleiche standen halbtags falsch). Browser-Lifecycle: `browser.new_page()` jetzt im `try`-Block, damit `finally browser.close()` auch bei `new_page()`-Failures greift
- **ICS UID stabilisiert:** UIDs basieren jetzt auf `spielnr` (`cg-<spielnr>@crazy-geese.at`) statt Datum+Zeit — Termin-Verlegungen werden von Kalender-Apps als Update erkannt, nicht als neues Event. Fallback auf altes Schema nur ohne `spielnr`. Beide ICS-Files regeneriert
- **Lightbox haerter:** URL-Validierung in `lightbox.js render()` — `javascript:`/`data:`-URIs werden durch `isSafeImageUrl()` blockiert, falls images aus weniger vertrauenswuerdiger Quelle kommen
- **A11y:** `<h1>` (visually-hidden) auf `index.html` ergaenzt — Heading-Hierarchie war broken. `prefers-reduced-motion` jetzt komplett (globaler Reset auf `*` plus explizit `.hero-logo-bg`); vorher liefen `.hero-logo-pulse` und andere Animationen weiter
- **Privacy:** Telefonnummern und private @gmail/@gmx/@icloud-Adressen aus `data/alte-website-infos.md` redigiert — gehoeren nicht in ein oeffentliches Repo
- **Aufraeumen:** `scripts/download_images.py` geloescht (Einmal-Backup, hat seinen Job getan, Bilder liegen schon in `data/alte-website-bilder/`). `metrostars.py` als HTTP-Fallback im Scraper jetzt in den "Wichtige Pfade"-Tabelle dokumentiert
- Cache-Buster aller `shared.js`/`lightbox.js`-Verweise auf `?v=2026-05-04`

### 2026-04-28
- Code-Review-Folgearbeiten: Tabellen-Scraper repariert (ABF-Markup hat sich geaendert, scrape_standings parst nun heuristisch ueber die Team-Cell statt fester Indices), `TEAM_NAME_OVERRIDES` zentralisiert kanonische Teamnamen ("Dirty Sox Graz" -> "Graz Dirty Sox" etc.) damit Tabelle und Spiele konsistent sind
- Scraper hat jetzt Failure-Detection: bei 0 Teams oder 0 Spielen exit 1, GitHub Actions schlaegt Alarm
- Neuer Generator `scripts/generate_ics.py` regeneriert beide ICS-Dateien aus `data.json` (laeuft im Workflow nach `scraper.py`); ICS-Suffix-Logik (HEIM/in Rohrbach/leer) zentral implementiert
- `scripts/validate_data.py` deutlich erweitert: pruefte vorher nur blog+spiele(datum/heim/gast), jetzt auch verein, kontakt, tabelle, softball, eindeutige spielnr, Ergebnis-Konsistenz und ICS-Cross-Check (DTSTART-Set in JSON vs. ICS)
- Cache-Buster fuer `shared.js` auf `?v=2026-04-28` angehoben (alle 9 HTML-Files)
- Flyer-Generator (`generate-flyer.py` + `flyer-a6.pdf`) entfernt – wird nicht mehr gebraucht
- Spielplan: 23.05. nach Rohrbach verlegt (Doppelheader gegen Danube Titans 11:00 + Vienna Lawnmowers 16:00, vorher 13:30 in Stockerau). `data/data.json` und beide ICS aktualisiert
- Baseball-Konvention "Gast zuerst" durchgezogen: `renderGame()` (`scripts/shared.js`) tauscht Heim/Gast in der Game-Card und stellt Score auf `gast:heim` um; Schema.org `SportsEvent.name` auf `${gast} vs ${heim}`; alle ICS-`SUMMARY` umgedreht
- ICS-Suffix-Konvention: `(HEIM)` für formal-Heim in Rohrbach, `(in Rohrbach)` für formal-Auswärts mit Spielort Rohrbach, sonst kein Suffix
- Scraper kann jetzt bestehende Spiele aktualisieren (vorher nur neue hinzufügen): `find_existing_game()` matcht primär per `spielnr` (persistent ID, neues Feld in `data.json`), Fallback `(heim, gast)` mit Datum-Disambiguierung. Re-Split vergangene/nächste am Ende, damit Datums-Verlegungen sauber wandern
- Scraper schützt manuell gepflegte Felder: `phase` wird nie überschrieben, `ort` nur bei klarem Verlegungssignal (datum/zeit-Diff). ABF-Platzhalter `0:0` für ungespielte Spiele wird gefiltert (Ergebnis nur für vergangene Spiele übernommen)

### 2026-04-22
- Blog-Bereich eingeführt: `blog.html` als Übersicht (rendert `data.blog.posts`), `posts/<slug>.html` für Einzelartikel
- Erster Artikel: Baseball-Schulcup an der NMS Mattersburg
- Wiederverwendbare Lightbox (`scripts/lightbox.js`) mit Keyboard-Nav (←/→/ESC) und Swipe-Gesten
- Bilder-Pipeline: `scripts/optimize_blog_images.py` (Full 1600px + Thumb 800px mit progressive JPEG)
- Navigation: Blog-Link an zweiter Stelle (nach Home) auf allen 9 Seiten
- Neu: `scripts/validate_data.py` – Schema- und Asset-Check für `data/data.json`
- Neuer Workflow `.github/workflows/validate-data.yml`: validiert `data.json` bei jedem Push auf `main` und jedem PR
- Mobile-Responsiveness-Test um `blog.html`, `was-ist-baseball.html` und den Artikel erweitert
- Scraper robuster: Retry-Wrapper um jeden `page.goto` (3 Versuche bei TimeoutError), Datum pro Spiel aus Kontext-Fenster (statt globalem Body-Match), Ort-Erkennung via `awaiting_ort`-State statt Whitelist, `determine_phase` dead parameter entfernt
- Flyer (`generate-flyer.py`) liest Heimspiele jetzt aus `data/data.json` (kein Hardcoding), Trainingszeiten laut CLAUDE.md, „US-Coach"-Zeile entfernt, dead code aufgeräumt
- Schema.org JSON-LD: `SportsClub` statisch auf Landing Page, `SportsEvent[]` dynamisch auf `baseball.html`
- CSP-Meta-Tag auf allen 9 Seiten (nur self + Cloudflare Analytics + Google Fonts + YouTube-Embed)
- YouTube-Iframe auf `youtube-nocookie.com` umgestellt, `allow`-Permissions reduziert
- Navigation komplett überarbeitet: Brand-Badge aus HTML entfernt, „Archiv" aus Top-Nav in den Footer verschoben, Social-Media-Icons im Header behalten, fluide Schrift via `clamp()`, adaptive Nav via `setupAdaptiveNav()` in `shared.js` (misst Nav-Breite, schaltet auf Hamburger-Modus wenn's nicht passt), `.compact` als HTML-Default gegen FOUC
- Lightbox mit Fokus-Trap (Tab bleibt in Close/Prev/Next) und `inert` auf Siblings
- `shared.js`: Kein Cache-Bust-Param mehr auf `fetchJson` (GitHub Pages ETag reicht), Header-Kommentar aktualisiert, Close-on-Link-Click auf Drawer-Nav
- `README.md` komplett überarbeitet – Seitenstruktur, Blog-Workflow, Validator-Nutzung

### 2026-04-09
- Komplettes Website-Update für Saison 2026
- Trainingszeiten aktualisiert (Baseball, Kinder, Softball)
- Kontakte: Joey Vickery, Harald Burian (Nachwuchs), Mike Rigby, Thomas Kissich (Softball)
- Vorstand laut Vereinsregisterauszug 2025 aktualisiert
- Alle @crazy-geese.at Adressen durch crazygeese93@gmail.com ersetzt
- Landing Page: Highlight-Karten (Nächstes Spiel + Heimspiel), Sport-Tags
- Slideshow durch Logo-Hintergrund ersetzt (Blur + Puls-Animation)
- ICS-Kalenderdateien für alle Spiele + Heimspiele
- Barrierefreiheit: Skip-Links, ARIA, Fokus-Styles auf allen Seiten
- Spielplan-Texte vergrößert für bessere Lesbarkeit
- Mitmachen-Sektion: Einladung zum Schnuppertraining
- Baseball + Softball chronologisch zusammengeführt
- Mitgliedschafts-Sektion entfernt
- Ben Miller, Daniel Horky, Jörg Dorner (als Trainer) entfernt
- US-Coach-Referenzen entfernt

### 2026-01-18
- TODO: Domain- & E-Mail-Migration dokumentiert

### 2026-01-15
- GitHub Actions Fix: Schreibrechte für GITHUB_TOKEN
- Backup aller Infos von crazy-geese.at
- 25 Bilder von alter Website gesichert

### 2025-12-24
- Alle 13 Spiele der Saison 2025 importiert
- Neuer Scraper: durchsucht alle Runden automatisch
- Logo integriert (Header + Favicon)
- Farbenblind-freundliches Design (Blau/Orange)
