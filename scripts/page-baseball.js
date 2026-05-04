// Bootstrap fuer baseball.html.
// Render Spielplan, Tabelle und injiziere Schema.org SportsEvent JSON-LD.

async function loadData() {
  try {
    const data = await fetchJson('data/data.json');
    renderPage(data);
  } catch (error) {
    console.error('Fehler:', error);
    showError(document.getElementById('next-games'), 'Spiele konnten nicht geladen werden.');
  }
}

function renderPage(data) {
  document.getElementById('season').textContent = data.verein.saison;

  const nextGames = document.getElementById('next-games');
  if (data.spiele.naechste && data.spiele.naechste.length > 0) {
    nextGames.innerHTML = data.spiele.naechste.map((g, i) => renderGame(g, i === 0)).join('');
  } else {
    nextGames.innerHTML = '<p class="no-games">Keine anstehenden Spiele</p>';
  }

  const pastGames = document.getElementById('past-games');
  if (data.spiele.vergangene && data.spiele.vergangene.length > 0) {
    pastGames.innerHTML = [...data.spiele.vergangene].reverse().map(g => renderGame(g)).join('');
  } else {
    pastGames.innerHTML = '<p class="no-games">Noch keine Spiele in dieser Saison</p>';
  }

  // Tabelle (gleich wie auf der Startseite, mit PCT/GB)
  document.getElementById('table-phase').textContent = data.tabelle.phase;
  const teams = data.tabelle.teams || [];
  const leader = teams.reduce((best, t) => {
    if (!best) return t;
    const bd = (Number(best.siege) || 0) - (Number(best.niederlagen) || 0);
    const td = (Number(t.siege) || 0) - (Number(t.niederlagen) || 0);
    return td > bd ? t : best;
  }, null);
  document.getElementById('standings-body').innerHTML = teams.map(team => `
    <tr class="${isOurTeam(team.name) ? 'highlight' : ''}">
      <td class="col-rank">${escapeHtml(team.rang)}</td>
      <td class="col-team">${escapeHtml(team.name)}</td>
      <td class="col-stat">${escapeHtml(team.siege)}</td>
      <td class="col-stat">${escapeHtml(team.niederlagen)}</td>
      <td class="col-stat">${computePCT(team)}</td>
      <td class="col-stat">${computeGB(team, leader)}</td>
    </tr>
  `).join('');

  injectEventSchema([...(data.spiele.naechste || []), ...(data.spiele.vergangene || [])]);
}

function injectEventSchema(games) {
  const events = games
    .filter(g => g.datum && g.heim && g.gast)
    .map(g => {
      const startDate = g.zeit ? `${g.datum}T${g.zeit}:00+02:00` : g.datum;
      const ev = {
        '@context': 'https://schema.org',
        '@type': 'SportsEvent',
        name: `${g.gast} vs ${g.heim}`,
        startDate: startDate,
        sport: 'Baseball',
        homeTeam: { '@type': 'SportsTeam', name: g.heim },
        awayTeam: { '@type': 'SportsTeam', name: g.gast },
        url: 'https://crazy-geese.at/baseball.html',
        eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
        eventStatus: 'https://schema.org/EventScheduled'
      };
      if (g.ort) ev.location = { '@type': 'Place', name: g.ort };
      if (g.ergebnis_heim !== null && g.ergebnis_heim !== undefined) {
        ev.description = `Ergebnis: ${g.ergebnis_gast}:${g.ergebnis_heim}`;
      }
      return ev;
    });
  if (events.length === 0) return;
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(events);
  document.head.appendChild(script);
}

loadData();
