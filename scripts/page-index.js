// Bootstrap fuer index.html (Landing Page).
// shared.js muss vor diesem Script geladen sein (wird in der HTML so
// arrangiert) und uebernimmt setFooterYear()/setupMobileMenu() automatisch.

async function loadData() {
  try {
    const data = await fetchJson('data/data.json');
    renderPage(data);
  } catch (error) {
    console.error('Fehler beim Laden der Daten:', error);
    showError(document.getElementById('next-games'), 'Spielplan konnte nicht geladen werden.');
    document.getElementById('standings-body').innerHTML =
      '<tr><td colspan="6" class="error-message" role="alert">⚠️ Tabelle konnte nicht geladen werden.</td></tr>';
  }
}

function renderPage(data) {
  document.getElementById('season-badge').textContent = data.verein.saison;
  document.getElementById('table-phase').textContent = data.tabelle.phase;

  const tbody = document.getElementById('standings-body');
  // Spitzenreiter fuer GB-Berechnung: das erste Team in der Tabelle.
  // ABF sortiert per Liga-Regeln (PCT, dann Tiebreaker), das ist
  // konsistenter als eine eigene siege-niederlagen-Heuristik.
  const teams = data.tabelle.teams || [];
  const leader = teams[0] || null;
  tbody.innerHTML = teams.map(team => `
    <tr class="${isOurTeam(team.name) ? 'highlight' : ''}">
      <td class="col-rank">${escapeHtml(team.rang)}</td>
      <td class="col-team">${escapeHtml(team.name)}</td>
      <td class="col-stat">${escapeHtml(team.siege)}</td>
      <td class="col-stat">${escapeHtml(team.niederlagen)}</td>
      <td class="col-stat">${computePCT(team)}</td>
      <td class="col-stat">${computeGB(team, leader)}</td>
    </tr>
  `).join('');

  const today = new Date().toLocaleDateString('en-CA');

  const baseballGames = (data.spiele.naechste || [])
    .filter(g => g.datum >= today)
    .map(g => ({ ...g, sport: 'baseball' }));
  const softballGames = (data.softball && data.softball.naechste_termine || [])
    .filter(t => t.datum >= today)
    .map(t => ({ ...t, sport: 'softball' }));
  const allGames = [...baseballGames, ...softballGames]
    .sort((a, b) => (a.datum + (a.zeit || '')).localeCompare(b.datum + (b.zeit || '')));

  const nextGame = allGames[0];
  const nextHomeGame = allGames.find(g => isHomeVenue(g.ort));
  const gameKey = g => g.datum + '|' + (g.zeit || '') + '|' + g.sport;
  const sameGame = nextGame && nextHomeGame && gameKey(nextGame) === gameKey(nextHomeGame);

  const highlightsEl = document.querySelector('.hero-highlights');
  const nextGameCard = document.getElementById('next-game-card');
  const nextHomeCard = document.getElementById('next-home-card');

  if (sameGame) {
    // Nächstes Spiel == Nächstes Heimspiel: nur die Heim-Kachel, einspaltig.
    highlightsEl.classList.add('hero-highlights--single');
    nextGameCard.hidden = true;
    nextHomeCard.hidden = false;
    nextHomeCard.innerHTML = `
      <span class="highlight-label">Nächstes Heimspiel</span>
      ${renderHighlightGame(nextHomeGame)}
      <span class="highlight-free">🎟️ Eintritt frei!</span>
    `;
  } else {
    highlightsEl.classList.remove('hero-highlights--single');
    nextGameCard.hidden = false;
    nextHomeCard.hidden = false;
    if (nextGame) {
      nextGameCard.innerHTML = `
        <span class="highlight-label">Nächstes Spiel</span>
        ${renderHighlightGame(nextGame)}
      `;
    } else {
      nextGameCard.innerHTML = '<span class="highlight-label">Nächstes Spiel</span><p class="no-games">Saisonpause</p>';
    }
    if (nextHomeGame) {
      nextHomeCard.innerHTML = `
        <span class="highlight-label">Nächstes Heimspiel</span>
        ${renderHighlightGame(nextHomeGame)}
        <span class="highlight-free">🎟️ Eintritt frei!</span>
      `;
    } else {
      nextHomeCard.innerHTML = '<span class="highlight-label">Nächstes Heimspiel</span><p class="no-games">Keine Heimspiele geplant</p>';
    }
  }

  const nextGamesEl = document.getElementById('next-games');
  const shownIds = [nextGame, nextHomeGame].filter(Boolean).map(gameKey);
  const remaining = allGames.filter(g => !shownIds.includes(gameKey(g))).slice(0, 4);
  if (remaining.length > 0) {
    nextGamesEl.innerHTML = remaining.map(renderGameCompact).join('');
  } else {
    nextGamesEl.innerHTML = '<p class="no-games">Keine weiteren Spiele</p>';
  }

  // Letzte 2 absolvierte Spiele (neueste zuerst). Nur einblenden, wenn
  // ueberhaupt was zu zeigen ist.
  const past = (data.spiele.vergangene || [])
    .slice()
    .sort((a, b) => (b.datum + (b.zeit || '')).localeCompare(a.datum + (a.zeit || '')))
    .slice(0, 2);
  const lastResultsSection = document.getElementById('letzte-ergebnisse');
  if (past.length > 0) {
    document.getElementById('last-results').innerHTML = past.map(g => renderGame(g)).join('');
    lastResultsSection.hidden = false;
  }
}

loadData();
