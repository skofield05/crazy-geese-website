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
| FINALE | Gold (#eab308) | Spiele mit `phase: "Finale"` |

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

**Optional: Turnier-Anwurfzeiten (`spiele`)** – für Turniertage (z.B. ABBQS) kann
ein Termin ein optionales `spiele`-Array mit den Geese-Spielen bekommen:

```json
{
  "datum": "2026-07-05",
  "zeit": "10:00",
  "beschreibung": "ABBQS Turnier",
  "ort": "Geese Ballpark, Rohrbach",
  "spiele": [
    { "zeit": "10:00", "gegner": "Monkeys", "heim": false },
    { "zeit": "12:40", "gegner": "Rubberducks", "heim": true }
  ]
}
```

`zeit` des Termins = erste Anwurfzeit (erscheint auf der Startseiten-Karte als
„Beginn HH:MM Uhr"). Jedes `spiele`-Objekt braucht `gegner` + `heim` (bool);
`heim` ist hier die **formale Rolle im Spiel** (wer zuletzt schlägt), nicht der
Spielort – beim Turnier sind alle Spiele am selben Ort. `page-softball.js`
rendert daraus eine Anwurfzeiten-Tabelle (nach `zeit` sortiert); `page-index.js`
blendet einen „Details →"-Link zur Softball-Seite ein, sobald `spiele` gesetzt
ist. `validate_data.py` prüft das Array (Pflicht: `gegner`, `heim`-bool;
`zeit`-Format optional).

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

**Optional: `platzhalter`** – `true` markiert ein Spiel, das schon beworben
wird, bevor der Gegner feststeht (Erstanwendung: das Finale am 13.09.2026).
`gast` traegt dann einen Platzhaltertext („Danube Titans oder Schremser Beers
2"). Sobald ABF/Metrostars die echte Paarung liefert, loest der Scraper den
Eintrag auf: `find_existing_game` matcht Stufe 3 ueber **Datum + geteiltes
Team**, der Merge ersetzt `heim`/`gast`, entfernt `platzhalter` und den
(dann veralteten) `hinweis` – und **behaelt die eigene `spielnr`**, weil die
ICS-UID daran haengt und eine neue UID Kalender-Apps ein zweites Event
anlegen liesse. Dazu setzt er **`spielnr_fest: true`** – ein Flag, das
dauerhaft bleibt: `platzhalter` selbst taugt nicht als Schutz, weil es bei
der Aufloesung entfernt wird und der naechste Lauf die spielnr sonst doch
noch ueberschreiben wuerde. Das Datum ist im Match bewusst Pflicht: ohne es wuerde jedes
andere Playoff-Spiel des Teams den Platzhalter still ueberschreiben; ein
Duplikat nach einer Verlegung faellt dagegen sofort auf.

**Optional: `fremdspiel`** – `true` markiert ein Spiel, das an unserem
Ballpark stattfindet, an dem die Geese aber **nicht beteiligt** sind
(Erstanwendung: das Spiel um Platz 3 am 13.09.2026 um 11:00, direkt vor dem
Finale). Es gibt dort kein „wir": HEIM/AUSWAERTS, das W/L-Badge und die
`.team.us`-Hervorhebung ergeben keinen Sinn, stattdessen steht ein neutral-
graues **OHNE GEESE**-Badge und beide Teams werden genannt. Das Spiel bleibt
**sichtbar** im Startseiten-Spielplan und auf `baseball.html` (es gehoert zum
Spieltag), wird aber ausgenommen aus: den Highlight-Karten (sonst waere das
11:00-Spiel „Nächstes Spiel" statt des Finales um 14:00), „Letzte Ergebnisse",
dem Schema.org-JSON-LD und **beiden ICS-Dateien** (ein Termin „Sieger X vs
Verlierer Y" in einem Crazy-Geese-Kalender waere nur verwirrend). Bewusst
**kein** `platzhalter`, obwohl die Paarung noch offen ist: der Scraper filtert
nach Team-ID und bekommt Fremdspiele nie zu sehen, koennte den Platzhalter also
nie aufloesen – der Validator-Staleness-Check wuerde ab dem 13.09. dauerhaft
rot laufen. `validate_data.py` prueft nur den bool-Typ.

**Optional: `bild` / `bild_alt`** – Ankuendigungs-Flyer am Spiel. Steht als
**eigenes Grid-Item neben** der Hero-Karte (`#flyer-card` in `index.html`,
befuellt von `page-index.js`), nicht in ihr: die Karte ist Column-Flex, ein
Hochformat-Flyer darin macht sie sehr lang und schiebt Datum/Uhrzeit aus dem
Blick. Traeger ist die erste sichtbare Karte, deren Spiel ein `bild` hat; der
Flyer wird beim Ordering direkt hinter diese Karte einsortiert. Das feste
Zweispalten-Layout (`.hero-highlights--with-flyer`, max. 920 px) greift nur,
wenn ausser dem Flyer genau **eine** Karte sichtbar ist – sonst bleibt
`auto-fit`, weil der Flyer bei drei Items sonst in eine zweite Zeile faellt.
Unter 600 px ist das Grid einspaltig, der Flyer rutscht also unter die Karte.
Die Klasse heisst `.highlight-flyer` und **nicht** `.event-flyer`: letztere
triggert `:has()`-Regeln fuer das Event-Layout.

Der Flyer ist ein `<button class="gallery-item flyer-trigger">` und oeffnet
die **Lightbox** (`scripts/lightbox.js`, auf `index.html` eingebunden) – per
Klick, Enter und Leertaste. Optionales **`bild_full`** liefert das Grossformat
fuer die Lightbox (Fallback: `bild`); es wird erst beim Klick geladen, die
Landing Page zieht nur das kleine `bild`. Konvention wie beim Blog: `bild` =
Anzeigegroesse (640 px = 2x der 320-px-Darstellung), `bild_full` = native
Aufloesung der Quelle. Die sichtbare Bildunterschrift wird kurz aus den
Spieldaten gebaut (`phase · Datum · Zeit · Ort`); `bild_alt` beschreibt den
ganzen Flyer und bleibt als `alt` am Thumbnail sowie im `aria-label` des
Buttons – als sichtbare Zeile waere es eine Textwand unter einem Bild, das
dasselbe schon sagt. `validate_data.py` prueft Typ und Existenz beider
Dateien und warnt bei fehlendem `bild_alt`.

**Optional: `hinweis`** – Freitext-Kontexthinweis am Spiel-Objekt (in `naechste`
oder `vergangene`), z.B. `"hinweis": "Fortsetzung des in Graz im 2. Inning
abgebrochenen Spiels."`. Erscheint als ℹ️-Info-Zeile auf der Startseiten-
Highlight-Karte, im Spielplan und auf `baseball.html`. Überlebt Re-Scrapes
(Scraper fasst nur bekannte Keys an). `validate_data.py` prüft optional den
String-Typ.

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

1. **Logo aufbereiten** und unter `img/sponsoren/<slug>.{png,jpg}` ablegen. Zielgrösse ca. 400 px breit. **Konvention: dunkles Logo auf weisser Kachel** (mit ~18-20 % Padding der Logohöhe rundherum). Die Sponsoren-Section liegt auf `--color-bg-card` (#161b22, fast schwarz) — die bestehenden Sponsoren-Logos sind alle helle Kacheln, weil sie weissen Hintergrund eingebrannt haben. Eine freigestellte weisse-Logo-auf-Transparent-Variante würde optisch aus der Reihe brechen (frei schwebende Schrift neben Kacheln). Den CSS-Filter `grayscale(100%) brightness(1.2)` nicht überbewerten: macht echtes Schwarz nicht hell, sondern bleicht nur die weisse Kachel leicht zusätzlich aus.

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

### 2026-09-06 (5)
- **Code-Review ueber das ganze Repo, 2 Findings – beide behoben:**
  1. **(HIGH) Der Flyer wurde auf 1:1 zugeschnitten.** `.flyer-trigger` stand bei Zeile ~606, `.gallery-item` steht bei ~2180 – **gleiche Spezifitaet, spaetere Regel gewinnt**. Damit verlor der komplette Override-Block gegen genau die Klasse, die er ueberschreiben sollte: `aspect-ratio: 1/1`, `object-fit: cover` und `all: unset` blieben aktiv. Gemessen 320x320 statt 320x400 – bei einer 640x800-Quelle also **je 40px oben und unten abgeschnitten** (Liga-Logo-Band oben, „LET'S GO GEESE"/Hüpfburg-Streifen unten). Der Kommentar am Block behauptete das Gegenteil. **Warum es durchrutschte:** die Verifikation hat nur Breiten gemessen (320px → 850px in der Lightbox); die 320er-Hoehe stand sogar in der Testausgabe, wurde aber als Breite gelesen. Fix ueber den Elternselektor (`.highlight-flyer-card .flyer-trigger`) statt Verschieben ans Dateiende – so bleibt der Block bei den anderen Flyer-Regeln und ueberlebt Umsortierungen. Dazu `transform: none` bei Hover mit **(0,3,1)**, weil `.gallery-item:hover img` selbst schon (0,2,1) hat und spaeter steht: dessen `scale(1.05)` haette dem Flyer zusammen mit dem geerbten `overflow: hidden` bei jedem Hover die Raender abgeschnitten. Neuer Test prueft jetzt das **Seitenverhaeltnis gegen `naturalWidth/naturalHeight`**, nicht mehr nur die Breite.
  2. **(LOW) Der beschreibende `bild_alt` erreichte das vergroesserte Bild nie.** `render()` setzte `img.alt = item.caption`, und die Lightbox bekam nur die kurze generierte Unterschrift. Waehrend die Lightbox offen ist, sind alle Geschwister `inert` – der ausfuehrliche alt des Thumbnails ist dann unerreichbar, und Screenreader hoerten denselben kurzen Text doppelt (als alt und aus `#lightbox-caption`). `setupLightbox` akzeptiert jetzt ein optionales **`alt`** pro Bild und faellt ohne Angabe auf `caption` zurueck – die Blog-Galerien bleiben also unveraendert (gegengeprueft).
- **Cache-Buster** `style.css` (10 Files) auf `?v=2026-09-06e`, `page-index.js` auf `?v=2026-09-06d`, `lightbox.js` auf `?v=2026-09-06b`.

### 2026-09-06 (4)
- **Finale-Flyer ist anklickbar und oeffnet die Lightbox** (auf Wunsch). Der Flyer ist jetzt ein `<button class="gallery-item flyer-trigger">` statt eines nackten `<img>` – ein Bild mit Click-Handler waere fuer Tastatur und Screenreader tot gewesen. `scripts/lightbox.js` ist dafuer erstmals auf `index.html` eingebunden (samt Lightbox-Markup), wird also nicht neu erfunden.
- **Zwei Bildgroessen**, Konvention wie beim Blog: `img/finale-2026-thumb.jpg` (640x800, 123 KB) steht auf der Startseite, `img/finale-2026.jpg` (1080x1350, native Quellaufloesung) laedt **erst beim Klick**. Neues optionales Feld **`bild_full`** am Spiel-Objekt, Fallback auf `bild`. Gemessen: 320 px in der Seite → 850 px in der Lightbox.
- **`lightbox.js` kann jetzt Einzelbilder**: bei genau einem Bild werden Vor/Zurueck ausgeblendet, Pfeiltasten und Swipe sind inaktiv und der Fokus-Trap zirkuliert nur noch ueber den Schliessen-Button. Vorher waeren die Pfeile dagewesen und haetten auf dasselbe Bild zurueckgesprungen. Dazu `.lightbox-prev[hidden]/.lightbox-next[hidden]{display:none}` – ohne die Regel bliebe `hidden` wirkungslos, weil beide `display:flex` gesetzt haben. Die Blog-Galerie (4 Bilder) ist gegengeprueft und blaettert unveraendert.
- **Sichtbare Bildunterschrift kurz** (`phase · Datum · Zeit · Ort`); der lange `bild_alt` bleibt als `alt` am Thumbnail und im `aria-label` des Buttons, statt als 200-Zeichen-Zeile unter einem Bild zu stehen, das dasselbe schon sagt.
- Auf Touch-Geraeten steht der „🔍 Größer anzeigen"-Hinweis dauerhaft (`@media (hover: none)`) – ohne Hover waere sonst nicht erkennbar, dass der Flyer anklickbar ist.
- Verifiziert: 17 Assertions (oeffnen per Klick/Enter, Grossformat geladen mit naturalWidth 1080, Pfeile ausgeblendet, ESC + Hintergrundklick schliessen, **Fokus kehrt auf den Flyer zurueck**, Blog-Galerie unveraendert), dazu 10 Seiten x 6 Viewports ohne Overflow.
- **Cache-Buster** `style.css` + `page-index.js` auf `?v=2026-09-06c`, `lightbox.js` auf `?v=2026-09-06`.

### 2026-09-06 (3)
- **Finale-Flyer steht jetzt neben der Highlight-Karte statt darunter** (auf Wunsch). Er ist aus `renderHighlightGame` raus und ein eigenes Grid-Item (`#flyer-card`) im `hero-highlights`-Grid; `page-index.js` befuellt es und sortiert es beim Ordering direkt hinter die Karte, deren Spiel das `bild` traegt. Neuer Modifier `.hero-highlights--with-flyer` (zwei Spalten `1fr / 320px`, vertikal zentriert, max. 920 px – ohne die gezaehmte Gesamtbreite stuenden Karte und Flyer 1200 px auseinander). Der Modifier greift bewusst nur, wenn ausser dem Flyer genau **eine** Karte sichtbar ist; bei mehr Karten bleibt `auto-fit`, sonst faellt der Flyer bei drei Items in eine zweite Zeile und stuende wieder unter statt neben seiner Karte. Unter 600 px ist das Grid ohnehin einspaltig – dort stapelt es weiterhin, was bei einem Hochformat-Flyer auch richtig ist.
- Gemessen: 1280 px Karte 584 px / Flyer 320 px nebeneinander, 768 px 400/320 nebeneinander, 390 px gestapelt. 10 Seiten x 6 Viewports (320–1280) ohne Overflow, keine JS-Fehler, Gold-Rahmen und Spielplan unveraendert.
- **Cache-Buster** `shared.js` + `style.css` (10 Files) und `page-index.js` auf `?v=2026-09-06b`.

### 2026-09-06 (2)
- **Awards-Blogpost** (`posts/awards-2026-09.html`): Die Liga hat ihre Regular Season Awards vergeben, **acht** gehen an **sechs** Geese-Spieler (Suchard und Ecker doppelt) – Christian Suchard (#36) als **MVP** + Silver Slugger Pitcher, Michael Rigby (#3) Gold Glove Catcher, Bernd Ecker (#52) Gold Glove *und* Silver Slugger 2nd Base, Joey Vickery (#35) Gold Glove 3rd Base, Peter Moser (#22) Gold Glove Outfield, Jörg Dorner (#12) Silver Slugger Outfield. Vier Grafiken nach `img/blog/awards-2026-09/` (Reihenfolge bewusst gesetzt: Uebersicht → Spieler I → Spieler II → Glossar; die UUID-Dateinamen der Quellen haetten sonst eine zufaellige Reihenfolge ergeben). Bootstrap `scripts/post-awards-2026.js` mit echten Bildunterschriften statt „Bild n von m", Eintrag in `blog.posts`, `sitemap.xml` ergaenzt.
- **`optimize_blog_images.py` akzeptiert jetzt `.jfif`** – Windows/WhatsApp liefern JPEGs oft mit dieser Endung, der Helper meldete bisher nur „Keine Bilder in ...".
- **Finale-Flyer auf der Startseite**: neues optionales Feld **`bild`/`bild_alt`** am Spiel-Objekt (siehe „Manuell Spiel eintragen"). Der Flyer haengt an der bestehenden Finale-Karte statt an einem eigenen `events`-Eintrag – so erscheint das Finale nicht doppelt (einmal als Event-Flyer, einmal als Spiel-Highlight).
- **Spiel um Platz 3 eingetragen** (ABF #79, 13.09. 11:00 bei uns am Ballpark): neues optionales Feld **`fremdspiel`** fuer Spiele ohne Geese-Beteiligung, samt Guards in allen Konsumenten (Highlight-Karten, „Letzte Ergebnisse", Schema.org, beide ICS) – analog zum bestehenden `status: "verschoben"`-Muster. **Erster Anlauf war zu grob:** der Filter sass an `baseballGames` und hat das Spiel aus der ganzen Pipeline geworfen, also auch aus dem Spielplan, wo es hingehoert. Jetzt haengt der Guard nur an `nextBaseball`/`nextHomeGame`.
- **Rahmenprogramm vom Flyer als `hinweis`** am Finale (Hüpfburg, Kantine).
- **Playoff-Baum von ABF geholt** (Runde „Playoffs" ohne Team-Filter, weil der Standard-Scrape nur Geese-Spiele sieht): #77 Vienna Bucks @ Graz Dirty Sox und #78 Schremser Beers 2 @ Danube Titans, beide **06.09. in Stockerau** und beide noch 0:0 – die Halbfinals laufen also erst. #79 = Sieger #77 @ Verlierer #78, #80 = Sieger #78 @ Geese. Der Platzhaltertext im `gast`-Feld deckt sich exakt mit #78.
- Verifiziert: 10 Seiten x 4 Viewports (320–1280) ohne Overflow und ohne JS-Fehler, 19 Content-Assertions (Finale-Karte traegt den Flyer und nicht Platz 3, Platz-3-Zeile ohne HEIM-Badge, Fremdspiel nicht im JSON-LD, Galerie + Lightbox inkl. Blaettern/ESC). Scraper-Lauf gegengeprueft: `fremdspiel`, `bild`, `bild_alt`, `hinweis` und `platzhalter` ueberleben, #79 wird nicht angefasst. Validator 0 Fehler, beide ICS weiterhin 1 Event.
- **Cache-Buster:** `shared.js` + `style.css` (10 Files), `page-index.js`, `page-baseball.js` auf `?v=2026-09-06`.

### 2026-09-06
- **Workflow-Fehlschlag vom 05.09. war transient** – ABF UND Metrostars waren im selben Lauf (23:46 Wien) nicht erreichbar, beide "beide leer"-Checks schlugen zu, Exit 1. Zwei Laeufe zwei Stunden vorher waren gruen, beide Quellen antworten wieder normal (Metrostars in 1,3 s). Kein Fix noetig – aber der Lauf hat drei echte Bugs sichtbar gemacht:
- **(HIGH) Der Platzhalter wurde "aufgeloest", ohne dass ein Gegner feststand.** ABF listet das Finale inzwischen als **#80** (13.09., 14:00) – aber mit **leerem `gast`**, weil das Halbfinale noch laeuft. Der Merge schuetzt zwar jedes Feld mit `if new_val` und schrieb den Leerstring korrekt nicht, entfernte `platzhalter` aber **bedingungslos**. Ergebnis: Flag weg, Phantasie-Gegner ("Danube Titans oder Schremser Beers 2") bleibt stehen – und Match-Stufe 3 liest `platzhalter`, haette also nie wieder greifen koennen. Die echte Paarung waere als **zweites Spiel am 13.09.** dazugekommen, der Phantasie-Gegner fuer immer auf Startseite, `baseball.html` und in beiden ICS geblieben. Fix: Aufloesung nur noch bei **vollstaendiger Paarung** (`heim` UND `gast` gesetzt). Bleibt der Platzhalter stehen, greift `spielnr_locked` weiterhin ueber `is_placeholder` – die `#FINALE`-UID ist also auch im Zwischenzustand geschuetzt.
- **(HIGH) `find_existing_game` Regel 2 matchte datumsblind.** `if len(candidates) == 1: return candidates[0]` prueft das Datum nie. Die Geese haben **jeden** der beiden moeglichen Finalgegner genau einmal daheim gespielt – sobald ABF die echte Paarung liefert, haette Regel 2 also das **gespielte Grunddurchgangsspiel** zurueckgegeben, noch bevor Regel 3 (Platzhalter) ueberhaupt drankommt, und ihm `datum`/`zeit`/`spielnr` des Finales aufgezwungen. Konkret gemessen: #28 (13.06., 4:7 vs Danube Titans) waere zum Finale umdatiert worden, das Saisonergebnis dabei verloren, der Platzhalter ungeloest geblieben. Fix: erst (heim, gast) **+ gleiches Datum**; ein einzelner Kandidat an einem anderen Tag zaehlt nur noch als Verlegung, wenn er **noch nicht gespielt** ist (ein Spiel mit Endstand wandert nicht in die Zukunft). 9 Match-Faelle als Unit-Check, dazu 3 simulierte Scraper-Laeufe mit echter Paarung: in-place aufgeloest, kein Duplikat, `spielnr` bleibt `#FINALE`, #28 unangetastet.
- **(MEDIUM) Die ABF-Tabelle wurde seit Laengerem gar nicht mehr gelesen.** `wait_for_selector("table.standings-print")` laeuft im Default `state="visible"`; die Seite liefert **zwei** solche Tabellen und die erste ist unsichtbar, also lief jeder Lauf in den 15-s-Timeout und fiel still auf Metrostars zurueck – die `[WARNUNG]`-Zeile las sich wie ein ABF-Ausfall, obwohl ABF die Tabelle sauber ausliefert. Genau diese stille Einquellen-Abhaengigkeit hat den Metrostars-Blip vom 05.09. ueberhaupt erst zum roten Lauf gemacht. Fix: `state="attached"` – das Parsing braucht keine Sichtbarkeit, es geht ohnehin ueber alle Tabellen und nimmt die erste nicht-leere. Verifiziert: "Gefunden: 9 Teams", Platz 1 (15W-1L), deckungsgleich mit Metrostars.
- **`save_data` schreibt wieder ein abschliessendes Newline** – ohne das produzierte jeder Scraper-Lauf ein "\ No newline at end of file" im Diff.
- **Daten:** Tabelle auf Stand 06.09. (Platzierungsrunde gespielt: Red Devils 5-11 auf Rang 7, Metrostars 3 4-12 auf Rang 8), `phase` auf "Playoffs". Das **Finale bleibt Platzhalter** – ABF kennt Termin und Heimrecht (13.09., 14:00, Rohrbach), aber noch keinen Gegner. Der naechste Lauf nach dem Halbfinale loest ihn jetzt korrekt auf. Validator 0 Fehler, beide ICS regeneriert (1 Event).

### 2026-08-24 (5)
- **Horizontaler Overflow auf Handys behoben** (vorbestehend, betraf jede Breite unter ~440px). Ursache war nicht das Hero-Logo (das wird von `overflow: hidden` geclippt und traegt gar nicht zur `scrollWidth` bei), sondern die Tabelle: `.tabelle-card` ist ein **Grid-Item**, und Grid-Items haben per Default `min-width: auto`, was auf die **min-content-Breite** des Inhalts aufloest – hier 422px. Die einspaltige `.hero-grid`-Spalte wurde dadurch breiter als der Viewport, und weil `.spielplan-card` in derselben Spalte liegt, wurde sie mitgezogen (gemessen: beide exakt 422px bei Viewports von 320 bis 430). Der bereits vorhandene `.table-container { overflow-x: auto }` half nicht – das Auto-Minimum schlaegt den Scroll-Container.
  - **Fix 1:** `min-width: 0` auf `.spielplan-card`/`.tabelle-card`, damit die Grid-Spalte schrumpfen darf.
  - **Fix 2:** Zellpolsterung der Tabelle unter 500px auf `var(--space-sm) var(--space-xs)` reduziert, damit die Tabelle gar nicht erst horizontal scrollen muss. Gegengemessen: passt jetzt ab 320px vollstaendig (vorher 404px Inhalt in 270px Fenster). **Reihenfolge beachtet** – die Media-Query steht bewusst NACH `.standings th, .standings td`; ein erster Versuch weiter oben in der Datei wurde von der Basisregel geschlagen (gleiche Spezifitaet, Media-Queries erhoehen sie nicht).
  - Verifiziert: 9 Seiten x 7 Viewports (320–1280px), kein Seiten-Overflow mehr, `.table-container` bleibt als Sicherheitsnetz.
- **Cache-Buster jetzt auch auf `style.css`** (`?v=2026-08-24`, alle 9 HTML-Files). GitHub Pages liefert die Datei mit `Cache-Control: max-age=600` aus – der Browser revalidiert bis zu 10 Minuten gar nicht, reine CSS-Aenderungen waren also nach dem Deploy nicht sofort sichtbar. Analog zur bestehenden JS-Konvention. **Nicht abgedeckt bleibt `data/data.json`** (bewusst ohne Buster, siehe 2026-04-22): reine Datenaenderungen brauchen weiterhin einen harten Reload oder 10 Minuten Geduld.

### 2026-08-24 (4)
- **Code-Review ueber das ganze Repo, 5 Findings – 5 behoben:**
  1. **(HIGH) Der ICS-UID-Schutz am Platzhalter hielt nur einen einzigen Scraper-Lauf.** Die Bedingung las `platzhalter`, aber der Block direkt darueber loescht dieses Flag im selben Lauf. Beim naechsten Lauf matchte der Eintrag per Regel 2 `(heim, gast)` – beide Namen sind nach der Aufloesung echt – und die spielnr wurde doch noch auf die ABF-Nummer ueberschrieben. Die UID waere also eine Woche spaeter trotzdem gewandert und haette genau das Doppel-Event im Kalender erzeugt, das der Kommentar zu verhindern behauptete. Fix: persistentes Feld **`spielnr_fest: true`**, das bei der Aufloesung gesetzt wird und dauerhaft im JSON bleibt. Ueber 3 simulierte Laeufe verifiziert: `spielnr` bleibt `#FINALE`.
  2. **(MEDIUM) Der FINALE-Badge lag auf Handys exakt ueber dem HEIM-Badge.** `.game-homeaway` ist in der 500px-Media-Query fest auf `grid-column: 2 / grid-row: 3` genagelt – zwei Badges mit dieser Klasse landeten in derselben Zelle (headless gemessen: identische x/y, HEIM unsichtbar). Ab 501px fiel der dritte Badge stattdessen aus dem 5-Spalten-Template in eine eigene Zeile. Betraf latent auch das VERSCHOBEN-Badge, wurde aber erst durch den vollstaendigen Startseiten-Spielplan sichtbar. Fix: neuer `.game-tags-compact`-Flex-Wrapper buendelt alle Badges in EINER Grid-Zelle; Desktop-Template von 5 auf 4 Spalten. Bei 390/768/1200px gegengemessen – keine Ueberlappung mehr.
  3. **(LOW) Ein liegengebliebener Platzhalter faellt niemandem auf.** Der Datums-Match ist streng; legt ABF das Finale auf den 12.09. statt 13.09., wird das echte Spiel neu angelegt und der Platzhalter bleibt fuer immer stehen – Seite und ICS zeigen dann zwei Finals, eines mit Phantasie-Gegner, und der Scraper-Lauf bleibt gruen. `validate_data.py` prueft jetzt: **Fehler**, wenn ein Platzhalter-Datum in der Vergangenheit liegt (blockt via Validator-Gate den Commit), **Warnung** ab 3 Tagen vorher. Beide Zweige gegengeprueft.
  4. **(LOW) Das Finale-Styling hing pauschal an der Heimspiel-Karte.** Bei einem Auswaertsfinale haette die generische „Nächstes Spiel"-Karte das Finale gezeigt (ohne Gold), waehrend die rote Heimspiel-Karte daneben ein beliebiges anderes Spiel prominent gemacht haette. Gold + Label haengen jetzt an der Karte, die das Finale tatsaechlich traegt.
  5. **(LOW) `hinweis` wurde bei der Platzhalter-Aufloesung bedingungslos geloescht.** Der Code nahm an, ein `hinweis` am Platzhalter koenne nur die „Gegner steht fest"-Notiz sein – dabei ist das laut Doku ein allgemeines Kuratoren-Feld, dessen Kernversprechen ist, Re-Scrapes zu ueberleben. Der Sonderfall ist ersatzlos raus.
- **Cache-Buster:** `shared.js` (9 Files) auf `?v=2026-08-24b`, `page-index.js` auf `?v=2026-08-24c`.
- Regressionslauf: 9 Seiten x 2 Viewports ohne JS-Fehler, `validate_data.py` 0 Fehler, beide ICS regeneriert.

### 2026-08-24 (3)
- **Startseiten-Spielplan zeigt jetzt alle anstehenden Termine.** Bisher filterte `page-index.js` jedes Spiel aus der Liste, das schon in einer Highlight-Karte stand (`shownIds`/`remaining`, seit der ersten Landing-Page-Version). Effekt: Das Finale stand in der Hero-Karte, fehlte aber im Spielplan – und die Section heisst „Spielplan 2026", nicht „Weitere Spiele". Ein Spielplan ohne das naechste Spiel liest sich wie ein Fehler, deshalb faellt der Filter weg (`upcoming = allGames.slice(0, 4)`). Die Wiederholung stoert nicht: Hero-Karte ist gross und beschriftet, die Liste eine kompakte Zeile. `gameKey` bleibt in Gebrauch – es dedupliziert weiterhin die Highlight-Karten untereinander (ein Spiel soll nicht gleichzeitig „Nächstes Spiel" und „Nächstes Heimspiel" sein). Leer-Text entsprechend „Keine weiteren Spiele" → „Keine anstehenden Spiele".
- **`hinweis` am Finale entfernt** (auf Wunsch). Der Platzhaltertext im `gast`-Feld („Danube Titans oder Schremser Beers 2") traegt die Information ohnehin. Der Hinweis am Juli-Spiel #35 (abgebrochenes Graz-Spiel) bleibt unberuehrt.
- **Cache-Buster** `page-index.js` auf `?v=2026-08-24b`.

### 2026-08-24 (2)
- **Finale am 13.09. wird beworben, obwohl der Gegner noch offen ist.** Geese haben durch Platz 1 im Grunddurchgang Heimrecht; der Gegner (Danube Titans oder Schremser Beers 2) entscheidet sich am 06.09. Neues optionales Feld **`platzhalter: true`** an Spiel-Objekten (siehe „Manuell Spiel eintragen") – das Spiel liegt als normaler Eintrag in `spiele.naechste` und laeuft dadurch automatisch durch alle Kanaele: Hero-Karte, Spielplan, `baseball.html`, beide ICS und das Schema.org-JSON-LD.
- **Scraper loest den Platzhalter selbst auf:** neue Match-Stufe 3 in `find_existing_game` (Datum + geteiltes Team), Merge ersetzt `heim`/`gast`, entfernt `platzhalter` + `hinweis`, behaelt aber die eigene `spielnr` (`#FINALE`) – sonst waere die ICS-UID gewandert und jeder, der den Termin schon importiert hat, haette ein zweites Event im Kalender. **End-to-End verifiziert:** Platzhalter testweise auf den 22.08. gesetzt und den echten Scraper laufen lassen → in-place aufgeloest (Graz Dirty Sox 9:20 Geese), kein Duplikat, `spielnr` stabil. Zusaetzlich 6 Match-Faelle als Unit-Check, u.a. dass das Halbfinale Titans-Beers und ein hypothetisches anderes Geese-Playoffspiel den Platzhalter **nicht** kapern.
- **FINALE-Badge (Gold `#eab308`)** in allen drei Render-Funktionen (`renderGame`, `renderGameCompact`, `renderHighlightGame`) fuer `phase === 'Finale'`. Die Heimspiel-Hero-Karte bekommt Gold-Rahmen + Glow (`.highlight-finale`) und das Label „Finale in Rohrbach" statt „Nächstes Heimspiel". Farbe ist nie alleiniger Traeger – der Badge sagt „FINALE"; das ist hier besonders wichtig, weil Gold und das Niederlagen-Orange bei Rot-Gruen-Schwaeche aehnlich wirken. Die `.game-phase`-Zeile entfaellt, wenn der Badge steht (sonst stuende „FINALE" zweimal auf derselben Karte).
- **CSS-Reihenfolge beachtet:** `.highlight-finale .highlight-label` muss **nach** `.highlight-home .highlight-label` stehen – gleiche Spezifitaet, und die Finale-Karte traegt beide Klassen. Neuer `.highlight-tags`-Wrapper buendelt BASEBALL + FINALE in eine Zeile (die Karte ist Column-Flex, ohne Wrapper stapeln die Badges).
- **ICS-SUMMARY beginnt bei `phase: "Finale"` mit `⚾ FINALE:`** – Kalender-Monatsansichten kuerzen die SUMMARY hart ab, und „FINALE" ist die Information, die dabei ueberleben soll.
- `validate_data.py` prueft `platzhalter` auf bool. **Cache-Buster** `shared.js` (9 Files) + `page-index.js` auf `?v=2026-08-24`.
- **Bekannt, nicht angefasst:** `index.html` hat auf schmalen Viewports (~390 px) horizontalen Overflow – `.spielplan-card`/`.tabelle-card` werden breiter als der Viewport. Vorbestehend, tritt auch ohne den Finale-Eintrag auf.

### 2026-08-24
- **Grunddurchgang abgeschlossen – Geese auf Platz 1 (15-1):** Ergebnis #36 nachgetragen (22.08., Graz Dirty Sox 9:20 Rohrbach Crazy Geese, formal auswaerts aber in Rohrbach gespielt). Tabelle auf Stand 24.08. Alle 16 Spiele sind jetzt in `spiele.vergangene`, `spiele.naechste` ist leer.
- **Warum es haengen blieb:** Der Workflow-Cron kennt nur die urspruenglichen Spieltage. Die zwei regenbedingt verlegten Spiele (#35 -> 25.07., #36 -> 22.08.) fielen auf keinen davon. #35 wurde noch vom 02.08.-Lauf mitgenommen, #36 haette bis zum Playoff-Lauf am 05.09. gewartet. **Fix:** Sicherheitsnetz-Cron `0 5 * 5-9 1` (jeden Montag 07:00 MESZ, Mai-September) in `update-standings.yml`.
- **ABF war beim Lauf nicht erreichbar** (keine standings-Tabelle, keine Runden-IDs, kein Team-Dropdown; per WebFetch 403). Der Metrostars-Fallback hat Tabelle + Spiele vollstaendig geliefert – genau der Fall, fuer den er gebaut wurde. Kein `scrape_errors`-Eintrag, Validator 0 Fehler.
- **Beide ICS regeneriert** und dadurch leer (0 Events) – korrekt, weil keine Spiele mehr anstehen. Struktur (VCALENDAR + VTIMEZONE) bleibt valide, die Download-Buttons auf `baseball.html` liefern also keine kaputte Datei.
- **Playoffs (05./06. + 12./13.09.) sind noch nicht angesetzt** – weder ABF noch Metrostars listen Paarungen. Sobald sie da sind, zieht der Playoff-Cron sie automatisch. Bis dahin zeigt die Startseite als einzige Highlight-Karte den ABBQS-Softballtermin am 27.09.

### 2026-07-20 (3)
- **Code-Review-Fixes (5 Findings aus Gesamt-Review):**
  1. **`escapeHtml` maskiert jetzt auch `"` und `'`** (`shared.js`): Die Ausgabe wird nicht nur in Text-, sondern auch in Attribut-Kontexte interpoliert (`aria-label="…"`, `href="…"`, `alt="…"`). Team-/Ortsnamen kommen aus dem Scraper (ABF/Metrostars) – ein `"` darin hätte das Attribut aufgebrochen (Markup-Bruch/Attribut-Injection). Implementierung von DOM-basiert (`textContent`→`innerHTML`) auf expliziten 5-Zeichen-Replace (`& < > " '`) umgestellt. Headless verifiziert: `A"B<C>D&E'F` → `A&quot;B&lt;C&gt;D&amp;E&#39;F`, kein rohes `"` mehr im gerenderten Attribut.
  2. **ICS SUMMARY/DESCRIPTION werden ICS-escaped** (`generate_ics.py`): Vorher lief nur `LOCATION` durch `_ics_escape`; ein Teamname mit `,`/`;`/`\` hätte die SUMMARY-Zeile per RFC 5545 zerlegt. Jetzt Team-Namen + `phase` escaped. **Sorgfalt:** `desc_extra` bewusst NICHT escaped (enthält literale `\n`-ICS-Zeilenumbrüche, die das Backslash-Doubling zerstört hätte) – per Byte-Check verifiziert (Single-Backslash bleibt).
  3. **VTIMEZONE-Block in beiden ICS** (`generate_ics.py`): `DTSTART;TZID=Europe/Vienna` war ohne `VTIMEZONE`-Definition referenziert (strikte Parser wie ältere Outlook interpretieren die Uhrzeit sonst falsch). Standard-Block mit EU-DST-Regel (CEST letzter So März 02:00 → CET letzter So Okt 03:00) ergänzt. Validator-`DTSTART`-Regex matcht die VTIMEZONE-`DTSTART:`-Zeilen (ohne TZID-Param) nicht → kein False-Positive.
  4. **Workflow-Härtung** (`update-standings.yml`): `concurrency: {group, cancel-in-progress: false}` serialisiert überlappende Spieltag-Läufe (stündlicher Cron); `git pull --rebase origin main` vor dem Push verhindert non-fast-forward-Fehlschläge, wenn zwischen Checkout und Push ein Commit landet.
  5. **Zeitzonen-sicheres Datum-Parsing** (`shared.js`): `new Date("YYYY-MM-DD")` wurde als UTC-Mitternacht geparst → westlich von UTC konnte ein Spiel einen Tag zu früh erscheinen. Neuer `parseLocalDate()`-Helper hängt `T00:00:00` an (lokale Mitternacht); genutzt von `formatDate`/`formatDateShort`/`formatDateLong`.
- **Cache-Buster** aller `shared.js`/`page-index.js`/`page-softball.js`-Verweise auf `?v=2026-07-20b` (shared.js geändert). Beide ICS regeneriert, `validate_data.py`: 0 Fehler.

### 2026-07-20 (2)
- **Optionales `hinweis`-Feld an Spiel-Objekten:** Freitext-Kontexthinweis, der in allen drei Render-Funktionen (`shared.js`: `renderHighlightGame`, `renderGame`, `renderGameCompact`) als Info-Zeile mit ℹ️ erscheint (Info-Blau `--color-win`, farbenblind-freundlich, klar abgesetzt ohne wie eine Warnung zu wirken). CSS: `.highlight-hinweis` (Hero-Karte, zentrierte Box), `.game-hinweis` (volle Karte, linker Border), `.game-hinweis-compact` (Spielplan-Zeile, Full-Width-Grid-Row). `validate_data.py` prüft optional auf String-Typ. Der Scraper mutiert bestehende Spiele in-place und fasst nur bekannte Keys an → `hinweis` überlebt Re-Scrapes (analog `status`). **Erstanwendung:** #35 vs Tulln Ravens (25.07.) ist die **Fortsetzung des in Graz im 2. Inning abgebrochenen Spiels** – Hinweis erscheint auf der „Nächstes Heimspiel"-Karte der Startseite und auf `baseball.html`. Headless verifiziert.
- **Cache-Buster** aller `shared.js`/`page-index.js`/`page-softball.js`-Verweise auf `?v=2026-07-20`

### 2026-07-20 (1)
- **Scraper-Fixes (3 Bugs, Workflow-Fehler Spieltag 19.07.):** Der „Update Standings"-Run scheiterte mit Exit 1, obwohl der Metrostars-Fallback korrekte Daten lieferte. Drei ineinandergreifende Bugs behoben:
  1. **Harter Fehler trotz Fallback:** Wenn ABF unten ist (keine Team-ID im Calendar-Dropdown), deckt der Metrostars-Fallback Tabelle UND Spiele vollständig ab. Der Team-ID-Check hängte trotzdem einen `scrape_errors`-Eintrag an → `exit 1` → kein Commit trotz gültiger Daten. Jetzt nur noch `[WARNUNG]`-Print (analog zum dokumentierten Prinzip in `_resolve_games`). Echte Totalausfälle (ABF + Metrostars beide leer) fangen die „beide leer"-Checks in `_resolve_standings`/`_resolve_games` weiter unten ab und färben den Run weiterhin rot.
  2. **`0:0`-Platzhalter bei gespielten Spielen:** ABF trägt Ergebnisse oft tagelang verspätet ein und zeigt bis dahin `0:0`. Die `0:0`-Neutralisierung im Merge griff nur für Zukunfts-Spiele (`if not game_in_past`) – ein am Vortag gespieltes Spiel bekam einen falschen `0:0`-Endstand. Ein Baseballspiel kann nie `0:0` enden (kein Unentschieden in der Liga: Mercy-/Extra-Innings), also ist `0:0` immer ein Platzhalter. Wird jetzt am ABF-Parse-Punkt (`scrape_games_from_calendar`) generell auf `None` neutralisiert, damit `_fill_results_from()` den echten Wert aus Metrostars übernimmt.
  3. **Kanonisierung vor dem Fill:** `_fill_results_from`/`_diff_game_results` matchen auf `(datum, heim, gast)`. ABF liefert Rohnamen („Metrostars", „Kutro Crazy Geese"), Metrostars ist schon kanonisch („Vienna Metrostars 3", „Rohrbach Crazy Geese") – das Matching scheiterte komplett, der Metrostars-Fill für ABF-Lücken griff nie. ABF-Spielnamen werden jetzt via `canonical_team_name` **vor** `_resolve_games` kanonisiert (die spätere `normalize_team`-Runde im Merge bleibt für Substring-/Overlap-Fälle).
- **Daten aktualisiert:** Ergebnisse #52 (Vienna Metrostars 3 2:13 Geese) + #53 (Tulln Ravens 6:18 Geese) eingetragen (beide Geese-Siege), Tabelle auf Stand 20.07. (Geese 9-1, Platz 2). Beide ICS regeneriert (gespielte Spiele aus alle-spiele entfernt). `validate_data.py`: 0 Fehler

### 2026-07-02
- **Nachholtermine 20.06.:** Die zwei regenbedingt verschobenen Spiele haben neue Termine (aus der Metrostars-Seite verifiziert): #35 vs Tulln Ravens jetzt **25.07.** (Heim, Geese Ballpark), #36 vs Graz Dirty Sox jetzt **22.08.**. `status: "verschoben"` entfernt, beide wieder in `spiele.naechste` (chronologisch einsortiert – `baseball.html` rendert `naechste` in Array-Reihenfolge ohne eigenen Sort). #36 findet trotz formalem Gast-Status **in Rohrbach** statt: `ort` auf „Geese Ballpark, Rohrbach" → HEIMSPIEL-Badge (UI badged nach Spielort via `isHomeVenue`) + Aufnahme in die Heimspiele-ICS mit „(in Rohrbach)"-Suffix. Beide ICS regeneriert
- **Softball-Turnier-Anwurfzeiten:** Neues optionales `spiele`-Array auf `softball.naechste_termine`-Objekten (Turniertage wie ABBQS). Jedes Element `{ zeit, gegner, heim }`, wobei `heim` die formale Spielrolle meint (nicht den Spielort – beim Turnier alle Spiele am selben Ort). `page-softball.js` rendert daraus die `.turnier-spiele`-Tabelle (nach `zeit` sortiert, Caption „Geese-Spiele"); der Termin selbst zeigt „Beginn HH:MM" (auch die Softball-Highlight-Karte via `renderHighlightGame` in `shared.js`). `page-index.js` blendet einen „Details →"-Link (`.highlight-details-link`) zur Softball-Seite ein, sobald `spiele` gesetzt ist – hängt an Softball- ODER Heimspiel-Karte (der ABBQS-Tag 05.07. in Rohrbach ist beides, per Dedup nur einmal). `validate_data.py` prüft das Array (`gegner`+`heim`-bool Pflicht, `zeit`-Format). Erstanwendung: ABBQS-Tag 05.07. (4 Geese-Spiele). CSS in `style.css`
- **Cache-Buster** aller `shared.js`-Verweise (9 HTML-Files) auf `?v=2026-07-02`, dazu `page-index.js` und `page-softball.js`

### 2026-06-21
- **Highlight-Cards baseball-priorisiert:** Die Hero-Karten (`.highlight-card` im `.hero-highlights`-Grid) zeigen jetzt IMMER das nächste Baseballspiel. Softball bekommt nur dann eine eigene Karte (`#next-softball-card`, lila wie SOFTBALL-Tag), wenn es das chronologisch nächste Event überhaupt ist – dann steht es neben dem nächsten Baseballspiel. Baseball-Karten-Label wird in dem Fall auf „Nächstes Baseballspiel" präzisiert, sonst bleibt „Nächstes Spiel". Heimspiel-Karte zählt weiterhin beide Sportarten (nächstes Heim-Event egal welche Sportart). Dedup: ein Spiel, das gleichzeitig nächstes Heimspiel ist, erscheint nur in der Heimspiel-Karte. Logik in `page-index.js`, neue Karte in `index.html`, CSS `.highlight-softball` in `style.css`
- **Highlight-Cards chronologisch:** Die sichtbaren Karten werden per CSS-`order` (gesetzt in `page-index.js`) nach Datum sortiert – näheres Datum links, egal welche Sportart. Karten ohne Spiel (Saisonpause/keine Heimspiele) landen hinten; ein Flyer-Event bleibt via `.highlight-event:has(.event-flyer){order:-1}` oben gepinnt
- **Verschobene Spiele:** Neues optionales Feld `status: "verschoben"` auf Spiel-Objekten in `data.json`. `renderGame`/`renderGameCompact` (`shared.js`) zeigen ein oranges „VERSCHOBEN"-Badge + leicht gedimmte Karte (Datum durchgestrichen). Verschobene Spiele werden aus den Highlight-Cards (`page-index.js`), aus „Letzte Ergebnisse" (`page-index.js`), aus dem Schema.org-JSON-LD (`page-baseball.js`), aus beiden ICS-Dateien (`generate_ics.py`) und aus dem ICS-Cross-Check (`validate_data.py`) ausgenommen – sie haben keinen gültigen Termin mehr. Spiel bleibt in `data.json` erhalten und auf `baseball.html` mit Badge sichtbar. `validate_data.py` prüft `status` jetzt gegen eine Allow-List (`ALLOWED_GAME_STATUS`), damit ein Tippfehler nicht die exakte Gleichheitsprüfung der anderen Konsumenten umgeht. Erstanwendung: die zwei regenbedingt abgesagten Spiele vom 20.06. (#35 vs Tulln Ravens, #36 @ Graz Dirty Sox). Der Scraper fasst `status` nicht an (mergt nur bekannte Keys in `existing`), das Feld überlebt also Re-Scrapes. Nachholtermin noch offen
- **Cache-Buster** aller `shared.js`-Verweise (9 HTML-Files) auf `?v=2026-06-21`, dazu `page-index.js` und `page-baseball.js` (geändert in diesem Commit)

### 2026-05-26
- **Firmenturnier-Flyer:** Event-Karte auf Landing Page zeigt jetzt das WhatsApp-Flyer-Bild (`img/firmenturnier-2026.jpg`, 800x1131, 174 KB) statt der generierten Text-Karte. Neues `bild`/`bild_alt`-Feld in `data.json` events steuert den Modus; Fallback auf Text-Karte bleibt fuer Events ohne Bild. Flyer verlinkt auf Instagram-Post. Layout: Flyer zentriert oben (max-width 450px), Heimspiel-Karte darunter (Grid auf single-column via `:has(.event-flyer)`)
- **Neue Sponsoren:** ASVOE (https://www.asvoe.at/) und Sportland Burgenland (https://www.burgenland.at/themen/sport/) in Sponsorenleiste. Logos aus webp/jpg aufbereitet mit weisser Kachel auf 400 px Breite -> `img/sponsoren/asvoe.png` (22 KB), `img/sponsoren/sportland-burgenland.jpg` (11 KB). Quelldateien in `Sponsoren/ASVÖ/` und `Sponsoren/Land Burgenland/`
- **Neuer Sponsor:** NIC Solutions (https://nic-solutions.at/) in der Sponsorenleiste auf `index.html`. Logo aus EPS-Quelle ueber Ghostscript (TinyTeX) auf 600 dpi mit Alpha gerendert; Claim „we make IT" weggeschnitten via spaltenweiser Alpha-Analyse (findet die Luecke zwischen Marke und Claim, ohne in den Text reinzuschneiden); auf 400 px Breite skaliert -> `img/sponsoren/nic-solutions.png` (16 KB, 400x219). Quelldateien liegen lokal in `Sponsoren/nic/`
- **`.gitignore`:** `/Sponsoren/` ergaenzt (analog zu `*.xls`/`*.pdf`). Fuehrender Slash ist load-bearing — ohne ihn wuerde die Regel auf Windows wegen Case-Insensitivity auch `img/sponsoren/` filtern und alle Sponsor-Logos verstecken. Mit `git check-ignore -v` verifiziert
- **Doku:** „Neuen Sponsor eintragen" in „Haeufige Aufgaben" ergaenzt (EPS->PNG-Workflow, .gitignore-Gotcha)
- **Fix (1. Anlauf):** PNG durch weisse PSD-Variante ersetzt — die zuerst genommene EPS-Variante (schwarze Schrift auf Alpha) war auf `--color-bg-card` (#161b22) unsichtbar. Der CSS-Filter `grayscale + brightness(1.2)` macht echtes Schwarz nicht hell genug
- **Fix (2. Anlauf):** weisse Variante hat im Kontext der Sponsorenwand visuell ausgebrochen — alle anderen Sponsoren-Logos sind helle Kacheln (JPGs mit weissem Hintergrund eingebrannt). NIC jetzt aus EPS gerendert mit schwarzer Schrift + lila Original-Punkt auf weisser Kachel (PNG, ~16 KB), passt zum Kachel-Look der bestehenden Sponsoren. „Haeufige Aufgaben" entsprechend korrigiert: Konvention ist „dunkles Logo auf weisser Kachel", nicht freigestellt

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
