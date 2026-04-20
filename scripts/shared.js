// Gemeinsame Funktionen fuer alle Seiten.
// Wird von index.html, baseball.html, softball.html und archiv.html geladen.

const OUR_TEAM_NAME = 'Crazy Geese';
const OUR_TEAM_KUERZEL = 'CG';
const HOME_LOCATION_KEYWORD = 'rohrbach';

function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(value);
  return div.innerHTML;
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

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('de-AT', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateShort(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit' });
}

function formatDateLong(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('de-AT', { weekday: 'long', day: '2-digit', month: 'long' });
}

function setupMobileMenu() {
  const btn = document.getElementById('mobile-menu-btn');
  if (!btn) return;
  btn.addEventListener('click', function() {
    const nav = document.querySelector('.nav');
    if (!nav) return;
    nav.classList.toggle('open');
    this.setAttribute('aria-expanded', nav.classList.contains('open'));
  });
}

function setFooterYear() {
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
}

async function fetchJson(path) {
  const response = await fetch(path + '?v=' + Date.now());
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
  const isHomeGame = isHomeVenue(game.ort);
  const badge = isHomeGame
    ? '<span class="game-badge home">HEIMSPIEL</span>'
    : '<span class="game-badge away">AUSWÄRTS</span>';

  let resultClass = '';
  if (hasResult) {
    const ourScore = isHome ? game.ergebnis_heim : game.ergebnis_gast;
    const theirScore = isHome ? game.ergebnis_gast : game.ergebnis_heim;
    resultClass = ourScore > theirScore ? 'win' : (ourScore < theirScore ? 'loss' : 'tie');
  }

  const heim = escapeHtml(game.heim);
  const gast = escapeHtml(game.gast);
  const score = hasResult
    ? escapeHtml(game.ergebnis_heim) + ':' + escapeHtml(game.ergebnis_gast)
    : 'vs';
  const featuredClass = isFeatured ? 'next-game-featured' : '';

  return `
    <div class="game-card ${resultClass} ${featuredClass}" role="article" aria-label="${heim} gegen ${gast}">
      <div class="game-card-header">
        <div class="game-date">${formatDate(game.datum)}${game.zeit ? ' • ' + escapeHtml(game.zeit) : ''}</div>
        <div class="game-tags">${badge}</div>
      </div>
      <div class="game-matchup">
        <span class="team ${isHome ? 'us' : ''}">${heim}</span>
        <span class="vs">${score}</span>
        <span class="team ${!isHome ? 'us' : ''}">${gast}</span>
      </div>
      ${game.ort ? `<div class="game-location">📍 ${escapeHtml(game.ort)}</div>` : ''}
      ${game.phase ? `<div class="game-phase">${escapeHtml(game.phase)}</div>` : ''}
    </div>
  `;
}

function renderGameCompact(game) {
  const sport = game.sport === 'softball' ? 'softball' : 'baseball';
  const sportTag = sport === 'softball' ? 'SOFTBALL' : 'BASEBALL';
  const isHomeGame = isHomeVenue(game.ort);
  const homeAwayText = isHomeGame ? 'HEIM' : 'AUSWÄRTS';
  const homeAwayClass = isHomeGame ? 'home' : 'away';

  if (sport === 'softball') {
    const label = escapeHtml(game.gegner || game.beschreibung || 'Softball');
    return `
      <div class="game-compact">
        <span class="game-date-compact">${formatDateShort(game.datum)}</span>
        <span class="game-time-compact">${game.zeit ? escapeHtml(game.zeit) : ''}</span>
        <span class="game-opponent">${label}</span>
        <span class="game-sport ${sport}">${sportTag}</span>
        <span class="game-homeaway ${homeAwayClass}">${homeAwayText}</span>
        ${game.ort ? `<span class="game-location-compact">📍 ${escapeHtml(game.ort)}</span>` : ''}
      </div>
    `;
  }

  const isHome = isOurTeam(game.heim);
  const opponent = escapeHtml(isHome ? game.gast : game.heim);

  return `
    <div class="game-compact">
      <span class="game-date-compact">${formatDateShort(game.datum)}</span>
      <span class="game-time-compact">${game.zeit ? escapeHtml(game.zeit) : ''}</span>
      <span class="game-opponent">${opponent}</span>
      <span class="game-sport ${sport}">${sportTag}</span>
      <span class="game-homeaway ${homeAwayClass}">${homeAwayText}</span>
      ${game.ort ? `<span class="game-location-compact">📍 ${escapeHtml(game.ort)}</span>` : ''}
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
      ${game.zeit ? `<span class="highlight-time">${escapeHtml(game.zeit)} Uhr</span>` : ''}
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
  `;
}
