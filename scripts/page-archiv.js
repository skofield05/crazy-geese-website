// Bootstrap fuer archiv.html (Saison 2025).

async function loadArchiv() {
  try {
    const data = await fetchJson('data/archiv/2025.json');
    renderArchiv(data);
  } catch (error) {
    console.error('Fehler:', error);
    showError(document.getElementById('archiv-games-2025'), 'Archiv konnte nicht geladen werden.');
  }
}

function renderArchiv(data) {
  const tbody = document.getElementById('archiv-standings-2025');
  // ABF-Rang ist authoritativ (PCT-sortiert) – erstes Team = Leader.
  const teams = data.tabelle.teams || [];
  const leader = teams[0] || null;
  tbody.innerHTML = teams.map(team => `
    <tr class="${isOurKuerzel(team.kuerzel) || isOurTeam(team.name) ? 'highlight' : ''}">
      <td class="col-rank">${escapeHtml(team.rang)}</td>
      <td class="col-team">${escapeHtml(team.name)}</td>
      <td class="col-stat">${escapeHtml(team.siege)}</td>
      <td class="col-stat">${escapeHtml(team.niederlagen)}</td>
      <td class="col-stat">${computePCT(team)}</td>
      <td class="col-stat">${computeGB(team, leader)}</td>
    </tr>
  `).join('');

  const gamesDiv = document.getElementById('archiv-games-2025');
  gamesDiv.innerHTML = data.spiele.map(g => renderGame(g)).join('');
}

loadArchiv();
