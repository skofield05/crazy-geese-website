// Bootstrap fuer softball.html (ABBQS-Termine).

// Rendert die Anwurfzeiten eines Turnier-Termins als kleine Tabelle. Erwartet
// ein Array von { zeit, gegner, heim } (nur die Geese-Spiele). HEIM/AUSW hier
// bezieht sich auf die formale Rolle im jeweiligen Spiel (wer zuletzt schlaegt),
// nicht auf den Spielort – beim Turnier sind alle Spiele am selben Ort.
function renderTurnierSpiele(spiele) {
  if (!Array.isArray(spiele) || spiele.length === 0) return '';
  const rows = [...spiele]
    .sort((a, b) => (a.zeit || '').localeCompare(b.zeit || ''))
    .map(s => {
    const heim = s.heim === true;
    const roleClass = heim ? 'home' : 'away';
    const roleText = heim ? 'HEIM' : 'AUSWÄRTS';
    const gegner = escapeHtml(s.gegner || '');
    const matchup = heim ? `vs ${gegner}` : `@ ${gegner}`;
    return `
      <tr>
        <td class="turnier-zeit">${s.zeit ? escapeHtml(s.zeit) : ''}</td>
        <td class="turnier-gegner">${matchup}</td>
        <td><span class="game-badge ${roleClass}">${roleText}</span></td>
      </tr>
    `;
  }).join('');
  return `
    <table class="turnier-spiele">
      <caption>Geese-Spiele</caption>
      <tbody>${rows}</tbody>
    </table>
  `;
}

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
            <div class="game-date">${formatDate(t.datum)}${t.zeit ? ' • Beginn ' + escapeHtml(t.zeit) : ''}</div>
            <div class="game-tags">${badge}</div>
          </div>
          <div class="game-matchup">
            <span class="team us">${label}</span>
          </div>
          ${t.ort ? `<div class="game-location">📍 ${escapeHtml(t.ort)}</div>` : ''}
          ${renderTurnierSpiele(t.spiele)}
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error('Fehler:', error);
    showError(container, 'Termine konnten nicht geladen werden.');
  }
}

loadSoftballTermine();
