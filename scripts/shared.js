// Gemeinsame Funktionen fuer alle Seiten.
// Wird von allen HTML-Seiten geladen (index, baseball, softball, nachwuchs,
// kontakt, archiv, was-ist-baseball, blog, posts/*).
//
// Auto-Init am Ende der Datei: setFooterYear() + setupMobileMenu() laufen
// automatisch, damit Seiten ohne eigene Render-Logik (kontakt, nachwuchs,
// was-ist-baseball) keinen eigenen Bootstrap-Script brauchen. Seiten mit
// eigener Logik laden zusaetzlich scripts/page-<name>.js.

const OUR_TEAM_NAME = 'Crazy Geese';
const OUR_TEAM_KUERZEL = 'CG';
const HOME_LOCATION_KEYWORD = 'rohrbach';

function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  // Auch " und ' maskieren: die Ausgabe wird nicht nur in Text-, sondern auch
  // in Attribut-Kontexte interpoliert (aria-label="…", href="…", alt="…").
  // Team-/Ortsnamen kommen aus dem Scraper (ABF/Metrostars) – ein " darin
  // wuerde sonst das Attribut aufbrechen. In Text-Kontext rendern die Entities
  // identisch, die Erweiterung ist also fuer beide Faelle sicher.
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function isOurTeam(name) {
  return typeof name === 'string' && name.includes(OUR_TEAM_NAME);
}

function isOurKuerzel(kuerzel) {
  return kuerzel === OUR_TEAM_KUERZEL;
}

function isHomeVenue(ort) {
  return typeof ort === 'string' && ort.toLowerCase().includes(HOME_LOCATION_KEYWORD);
}

// YYYY-MM-DD als LOKALE Mitternacht parsen. `new Date("2026-07-25")` wuerde als
// UTC-Mitternacht interpretiert; toLocaleDateString rendert dann in der Zeitzone
// des Besuchers – westlich von UTC kann das Spiel einen Tag zu frueh erscheinen.
// Mit explizitem "T00:00:00" (ohne Z) parst JS lokal -> in jeder Zeitzone der
// korrekte Kalendertag. Strings mit Zeitanteil bleiben unveraendert.
function parseLocalDate(dateStr) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return new Date(dateStr + 'T00:00:00');
  return new Date(dateStr);
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = parseLocalDate(dateStr);
  return date.toLocaleDateString('de-AT', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateShort(dateStr) {
  if (!dateStr) return '-';
  const date = parseLocalDate(dateStr);
  return date.toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit' });
}

function formatDateLong(dateStr) {
  if (!dateStr) return '-';
  const date = parseLocalDate(dateStr);
  return date.toLocaleDateString('de-AT', { weekday: 'long', day: '2-digit', month: 'long' });
}

function setupMobileMenu() {
  const btn = document.getElementById('mobile-menu-btn');
  if (!btn) return;
  if (btn.dataset.menuInit === 'on') return;
  btn.dataset.menuInit = 'on';
  const nav = document.querySelector('.nav');
  if (!nav) return;

  btn.addEventListener('click', function() {
    nav.classList.toggle('open');
    this.setAttribute('aria-expanded', nav.classList.contains('open'));
  });

  // Im Compact-Mode schliesst ein Link-Klick das Drawer-Menue.
  nav.addEventListener('click', function(e) {
    if (e.target.closest('.nav-link')) {
      nav.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    }
  });

  setupAdaptiveNav();
}

/**
 * Misst dynamisch, ob die Nav in einer Zeile neben dem Logo Platz hat.
 * Wenn nicht: `.compact` auf die Header-Bar -> Hamburger-Modus.
 * Wird bei Load, nach Font-Load und bei jedem Resize neu berechnet.
 */
function setupAdaptiveNav() {
  const header = document.querySelector('.header-bar');
  if (!header) return;
  // Double-init-Guard: nur einmal pro Page verbinden.
  if (header.dataset.adaptiveNav === 'on') return;
  header.dataset.adaptiveNav = 'on';
  const nav = header.querySelector('.nav');
  const brand = header.querySelector('.header-brand');
  if (!nav || !brand) return;

  let rafId = null;

  function measure() {
    // Auf Desktop-Mode zuruecksetzen fuer ehrliche Messung
    header.classList.remove('compact');
    nav.classList.remove('open');
    const btn = document.getElementById('mobile-menu-btn');
    if (btn) btn.setAttribute('aria-expanded', 'false');

    // Reflow erzwingen
    void header.offsetWidth;

    // Brand + optionale Icons + Nav-Kinder mit Margins summieren.
    const brandW = brand.offsetWidth;
    const icons = header.querySelector('.header-icons');
    const iconsW = icons ? icons.offsetWidth : 0;

    let navContentW = 0;
    Array.from(nav.children).forEach(el => {
      const s = window.getComputedStyle(el);
      const ml = parseFloat(s.marginLeft) || 0;
      const mr = parseFloat(s.marginRight) || 0;
      navContentW += el.offsetWidth + ml + mr;
    });

    const hs = window.getComputedStyle(header);
    const padLR = (parseFloat(hs.paddingLeft) || 0) + (parseFloat(hs.paddingRight) || 0);
    const gap = parseFloat(hs.gap) || 16;

    // Gaps zwischen Brand/Icons/Nav (maximal 2 in Desktop-Zeile).
    const gapsBetween = gap * (icons ? 2 : 1);
    const needed = brandW + iconsW + navContentW + gapsBetween;
    const available = header.clientWidth - padLR;

    if (needed > available) {
      header.classList.add('compact');
    }
  }

  function scheduleMeasure() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(measure);
  }

  measure();
  // Nochmal messen, sobald Webfonts geladen sind (Nav-Breite aendert sich).
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(measure);
  }
  window.addEventListener('resize', scheduleMeasure);
}

function setFooterYear() {
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
}

async function fetchJson(path) {
  // Kein Cache-Buster: GitHub Pages liefert ETag/Last-Modified, Browser macht
  // 304-Requests. Bei Updates darf der CDN-Cache bis zu seiner TTL (Standard
  // 10 min) veraltet bleiben – das ist fuer Vereinsdaten akzeptabel.
  const response = await fetch(path);
  if (!response.ok) throw new Error('HTTP ' + response.status + ' beim Laden von ' + path);
  return await response.json();
}

function showError(container, message) {
  if (!container) return;
  container.innerHTML = '<p class="error-message" role="alert">⚠️ ' + escapeHtml(message) + '</p>';
}

function renderGame(game, isFeatured) {
  const isHome = isOurTeam(game.heim);
  const hasResult = game.ergebnis_heim !== null && game.ergebnis_heim !== undefined;
  const isPostponed = game.status === 'verschoben';
  const isHomeGame = isHomeVenue(game.ort);
  const venueBadge = isHomeGame
    ? '<span class="game-badge home">HEIMSPIEL</span>'
    : '<span class="game-badge away">AUSWÄRTS</span>';
  const postponedBadge = isPostponed
    ? '<span class="game-badge postponed" aria-label="Verschoben">VERSCHOBEN</span>'
    : '';

  let resultClass = '';
  let resultBadge = '';
  if (hasResult) {
    const ourScore = isHome ? game.ergebnis_heim : game.ergebnis_gast;
    const theirScore = isHome ? game.ergebnis_gast : game.ergebnis_heim;
    if (ourScore > theirScore) {
      resultClass = 'win';
      resultBadge = '<span class="game-badge result-win" aria-label="Sieg">W</span>';
    } else if (ourScore < theirScore) {
      resultClass = 'loss';
      resultBadge = '<span class="game-badge result-loss" aria-label="Niederlage">L</span>';
    } else {
      resultClass = 'tie';
      resultBadge = '<span class="game-badge result-tie" aria-label="Unentschieden">T</span>';
    }
  }

  const heim = escapeHtml(game.heim);
  const gast = escapeHtml(game.gast);
  // Baseball-Konvention: Gast links, Heim rechts. Score "gast:heim".
  const score = hasResult
    ? escapeHtml(game.ergebnis_gast) + ':' + escapeHtml(game.ergebnis_heim)
    : 'vs';
  const featuredClass = isFeatured ? 'next-game-featured' : '';
  const scoreClass = hasResult ? 'score score-' + resultClass : 'vs';

  return `
    <div class="game-card ${resultClass} ${featuredClass} ${isPostponed ? 'postponed' : ''}" role="article" aria-label="${gast} bei ${heim}">
      <div class="game-card-header">
        <div class="game-date">${formatDate(game.datum)}${game.zeit ? ' • ' + escapeHtml(game.zeit) : ''}</div>
        <div class="game-tags">${postponedBadge}${resultBadge}${venueBadge}</div>
      </div>
      <div class="game-matchup">
        <span class="team ${!isHome ? 'us' : ''}">${gast}</span>
        <span class="${scoreClass}">${score}</span>
        <span class="team ${isHome ? 'us' : ''}">${heim}</span>
      </div>
      ${game.ort ? `<div class="game-location">📍 ${escapeHtml(game.ort)}</div>` : ''}
      ${game.hinweis ? `<div class="game-hinweis">ℹ️ ${escapeHtml(game.hinweis)}</div>` : ''}
      ${game.phase ? `<div class="game-phase">${escapeHtml(game.phase)}</div>` : ''}
    </div>
  `;
}

// Tabellen-Helpers: PCT (Win-Pct) und GB (Games Behind) clientseitig berechnen,
// damit die data.json-Schemata schlank bleiben.
function computePCT(team) {
  const w = Number(team.siege) || 0;
  const l = Number(team.niederlagen) || 0;
  const total = w + l;
  if (total === 0) return '-';
  return (w / total).toFixed(3).replace(/^0/, '');
}

function computeGB(team, leader) {
  if (!leader || team === leader) return '-';
  const w = Number(team.siege) || 0;
  const l = Number(team.niederlagen) || 0;
  const lw = Number(leader.siege) || 0;
  const ll = Number(leader.niederlagen) || 0;
  const gb = ((lw - w) + (l - ll)) / 2;
  if (gb <= 0) return '-';
  // Half-Game (.5) ist im Baseball ueblich, sonst ganze Zahl
  return (gb % 1 === 0) ? String(gb) : gb.toFixed(1);
}

function renderGameCompact(game) {
  const sport = game.sport === 'softball' ? 'softball' : 'baseball';
  const sportTag = sport === 'softball' ? 'SOFTBALL' : 'BASEBALL';
  const isHomeGame = isHomeVenue(game.ort);
  const homeAwayText = isHomeGame ? 'HEIM' : 'AUSWÄRTS';
  const homeAwayClass = isHomeGame ? 'home' : 'away';
  const isPostponed = game.status === 'verschoben';
  const compactClass = isPostponed ? 'game-compact postponed' : 'game-compact';
  const postponedTag = isPostponed
    ? '<span class="game-homeaway postponed">VERSCHOBEN</span>'
    : '';

  if (sport === 'softball') {
    const label = escapeHtml(game.gegner || game.beschreibung || 'Softball');
    return `
      <div class="${compactClass}">
        <span class="game-date-compact">${formatDateShort(game.datum)}</span>
        <span class="game-time-compact">${game.zeit ? escapeHtml(game.zeit) : ''}</span>
        <span class="game-opponent">${label}</span>
        <span class="game-sport ${sport}">${sportTag}</span>
        <span class="game-homeaway ${homeAwayClass}">${homeAwayText}</span>
        ${postponedTag}
        ${game.ort ? `<span class="game-location-compact">📍 ${escapeHtml(game.ort)}</span>` : ''}
        ${game.hinweis ? `<span class="game-hinweis-compact">ℹ️ ${escapeHtml(game.hinweis)}</span>` : ''}
      </div>
    `;
  }

  const isHome = isOurTeam(game.heim);
  const opponent = escapeHtml(isHome ? game.gast : game.heim);

  return `
    <div class="${compactClass}">
      <span class="game-date-compact">${formatDateShort(game.datum)}</span>
      <span class="game-time-compact">${game.zeit ? escapeHtml(game.zeit) : ''}</span>
      <span class="game-opponent">${opponent}</span>
      <span class="game-sport ${sport}">${sportTag}</span>
      <span class="game-homeaway ${homeAwayClass}">${homeAwayText}</span>
      ${postponedTag}
      ${game.ort ? `<span class="game-location-compact">📍 ${escapeHtml(game.ort)}</span>` : ''}
      ${game.hinweis ? `<span class="game-hinweis-compact">ℹ️ ${escapeHtml(game.hinweis)}</span>` : ''}
    </div>
  `;
}

function renderHighlightGame(game) {
  const sport = game.sport === 'softball' ? 'softball' : 'baseball';
  const sportTag = sport === 'softball' ? 'SOFTBALL' : 'BASEBALL';
  const isHomeGame = isHomeVenue(game.ort);
  const homeAwayText = isHomeGame ? 'HEIM' : 'AUSWÄRTS';
  const homeAwayClass = isHomeGame ? 'home' : 'away';

  if (sport === 'softball') {
    const label = escapeHtml(game.gegner || game.beschreibung || 'Softball');
    return `
      <span class="game-sport ${sport}">${sportTag}</span>
      <span class="game-homeaway ${homeAwayClass}">${homeAwayText}</span>
      <span class="highlight-date">${formatDateLong(game.datum)}</span>
      ${game.zeit ? `<span class="highlight-time">Beginn ${escapeHtml(game.zeit)} Uhr</span>` : ''}
      <span class="highlight-opponent">${label}</span>
      ${game.ort ? `<span class="highlight-location">📍 ${escapeHtml(game.ort)}</span>` : ''}
    `;
  }

  const isHome = isOurTeam(game.heim);
  const opponent = escapeHtml(isHome ? game.gast : game.heim);

  return `
    <span class="game-sport ${sport}">${sportTag}</span>
    <span class="highlight-date">${formatDateLong(game.datum)}</span>
    ${game.zeit ? `<span class="highlight-time">${escapeHtml(game.zeit)} Uhr</span>` : ''}
    <span class="highlight-opponent">vs ${opponent}</span>
    ${game.ort ? `<span class="highlight-location">📍 ${escapeHtml(game.ort)}</span>` : ''}
    ${game.hinweis ? `<span class="highlight-hinweis">ℹ️ ${escapeHtml(game.hinweis)}</span>` : ''}
  `;
}

// ----------------------------------------------------------------------------
// Auto-Init: laeuft sobald shared.js eingebunden wird. Da alle <script>-Tags
// im <body>-Footer stehen, ist das DOM zu diesem Zeitpunkt geparst.
// Idempotent dank header.dataset.adaptiveNav-Guard in setupAdaptiveNav().
// ----------------------------------------------------------------------------
setFooterYear();
setupMobileMenu();
