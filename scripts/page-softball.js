// Bootstrap fuer softball.html (ABBQS-Termine).

async function loadSoftballTermine() {
  const container = document.getElementById('softball-termine');
  try {
    const data = await fetchJson('data/data.json');
    const today = new Date().toLocaleDateString('en-CA');
    const termine = (data.softball && data.softball.naechste_termine || [])
      .filter(t => t.datum >= today)
      .sort((a, b) => (a.datum + (a.zeit || '')).localeCompare(b.datum + (b.zeit || '')));

    if (termine.length === 0) {
      container.innerHTML = '<p class="no-games">Termine werden bekanntgegeben</p>';
      return;
    }

    container.innerHTML = termine.map(t => {
      const isHome = isHomeVenue(t.ort);
      const badge = isHome
        ? '<span class="game-badge home">HEIM</span>'
        : '<span class="game-badge away">AUSWÄRTS</span>';
      const label = escapeHtml(t.gegner || t.beschreibung || 'Softball Termin');
      return `
        <div class="game-card" role="article" aria-label="${label}">
          <div class="game-card-header">
            <div class="game-date">${formatDate(t.datum)}${t.zeit ? ' • ' + escapeHtml(t.zeit) : ''}</div>
            <div class="game-tags">${badge}</div>
          </div>
          <div class="game-matchup">
            <span class="team us">${label}</span>
          </div>
          ${t.ort ? `<div class="game-location">📍 ${escapeHtml(t.ort)}</div>` : ''}
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error('Fehler:', error);
    showError(container, 'Termine konnten nicht geladen werden.');
  }
}

loadSoftballTermine();
