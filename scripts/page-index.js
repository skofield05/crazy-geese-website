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

  // Verschobene Spiele (status "verschoben") gehoeren nicht in die Highlight-
  // Karten – sie haben keinen gueltigen Termin mehr.
  const baseballGames = (data.spiele.naechste || [])
    .filter(g => g.datum >= today && g.status !== 'verschoben')
    .map(g => ({ ...g, sport: 'baseball' }));
  const softballGames = (data.softball && data.softball.naechste_termine || [])
    .filter(t => t.datum >= today)
    .map(t => ({ ...t, sport: 'softball' }));
  const allGames = [...baseballGames, ...softballGames]
    .sort((a, b) => (a.datum + (a.zeit || '')).localeCompare(b.datum + (b.zeit || '')));

  const gameKey = g => g.datum + '|' + (g.zeit || '') + '|' + g.sport;

  // Baseball ist die Kern-Sportart: das naechste Baseballspiel wird IMMER
  // angezeigt. Softball bekommt nur dann eine eigene Karte, wenn es das
  // chronologisch naechste Event ueberhaupt ist – dann steht es neben dem
  // naechsten Baseballspiel. Die Heimspiel-Karte zaehlt beide Sportarten.
  const nextBaseball = baseballGames[0] || null;
  const nextHomeGame = allGames.find(g => isHomeVenue(g.ort)) || null;
  const softballIsNext = allGames[0] && allGames[0].sport === 'softball';
  const nextSoftball = softballIsNext ? (softballGames[0] || null) : null;

  const homeKey = nextHomeGame ? gameKey(nextHomeGame) : null;
  // Dedup: ein Spiel, das gleichzeitig das naechste Heimspiel ist, erscheint
  // nur in der Heimspiel-Karte (Heimspiel-Label hat Vorrang).
  const showBaseballSeparately = nextBaseball && gameKey(nextBaseball) !== homeKey;
  const showSoftballSeparately = nextSoftball && gameKey(nextSoftball) !== homeKey;

  const highlightsEl = document.querySelector('.hero-highlights');
  const nextGameCard = document.getElementById('next-game-card');
  const nextSoftballCard = document.getElementById('next-softball-card');
  const nextHomeCard = document.getElementById('next-home-card');
  const eventCard = document.getElementById('event-card');

  const upcomingEvent = (data.events || [])
    .filter(e => e.datum >= today)
    .sort((a, b) => (a.datum + (a.zeit || '')).localeCompare(b.datum + (b.zeit || '')))[0];

  if (upcomingEvent) {
    eventCard.hidden = false;
    eventCard.innerHTML = renderEventCard(upcomingEvent);
  } else {
    eventCard.hidden = true;
    eventCard.innerHTML = '';
  }

  // Baseball-Karte: das naechste Baseballspiel. Wenn auch eine Softball-Karte
  // gezeigt wird, praezisiert das Label auf "Baseballspiel", sonst genuegt
  // "Naechstes Spiel".
  if (showBaseballSeparately) {
    const baseballLabel = showSoftballSeparately ? 'Nächstes Baseballspiel' : 'Nächstes Spiel';
    nextGameCard.hidden = false;
    nextGameCard.innerHTML = `
      <span class="highlight-label">${baseballLabel}</span>
      ${renderHighlightGame(nextBaseball)}
    `;
  } else if (!nextBaseball && !nextSoftball && !nextHomeGame) {
    nextGameCard.hidden = false;
    nextGameCard.innerHTML = '<span class="highlight-label">Nächstes Spiel</span><p class="no-games">Saisonpause</p>';
  } else {
    nextGameCard.hidden = true;
    nextGameCard.innerHTML = '';
  }

  // Softball-Karte: nur wenn Softball als Naechstes ansteht und nicht ohnehin
  // schon die Heimspiel-Karte ist.
  if (showSoftballSeparately) {
    nextSoftballCard.hidden = false;
    nextSoftballCard.innerHTML = `
      <span class="highlight-label">Nächster Softball-Termin</span>
      ${renderHighlightGame(nextSoftball)}
    `;
  } else {
    nextSoftballCard.hidden = true;
    nextSoftballCard.innerHTML = '';
  }

  // Heimspiel-Karte (beide Sportarten).
  if (nextHomeGame) {
    nextHomeCard.innerHTML = `
      <span class="highlight-label">Nächstes Heimspiel</span>
      ${renderHighlightGame(nextHomeGame)}
      <span class="highlight-free">🎟️ Eintritt frei!</span>
    `;
  } else {
    nextHomeCard.innerHTML = '<span class="highlight-label">Nächstes Heimspiel</span><p class="no-games">Keine Heimspiele geplant</p>';
  }
  nextHomeCard.hidden = false;

  // Single-Layout (eine zentrierte Karte) nur, wenn ausschliesslich die
  // Heimspiel-Karte ein Spiel zeigt (kein separates Baseball-/Softball-Spiel,
  // kein Event).
  const onlyHomeCard = !showBaseballSeparately && !showSoftballSeparately && !!nextHomeGame;
  highlightsEl.classList.toggle('hero-highlights--single', onlyHomeCard && !upcomingEvent);

  // Karten chronologisch anordnen: naeheres Datum links. Wir setzen CSS-`order`
  // auf jede sichtbare Karte anhand ihres Datums (Sortkey datum+zeit). Karten
  // ohne Spiel (Saisonpause/keine Heimspiele) und ein Flyer-Event bleiben hinten
  // bzw. (Flyer) via CSS oben gepinnt.
  const sortKey = g => g ? g.datum + (g.zeit || '') : '9999';
  const orderCards = [];
  if (!nextGameCard.hidden) orderCards.push({ el: nextGameCard, key: sortKey(nextBaseball) });
  if (!nextSoftballCard.hidden) orderCards.push({ el: nextSoftballCard, key: sortKey(nextSoftball) });
  orderCards.push({ el: nextHomeCard, key: sortKey(nextHomeGame) });
  // Text-Event (ohne Flyer) sortiert chronologisch mit; ein Flyer-Event bleibt
  // via `.highlight-event:has(.event-flyer){order:-1}` oben.
  if (upcomingEvent && !eventCard.querySelector('.event-flyer')) {
    orderCards.push({ el: eventCard, key: sortKey(upcomingEvent) });
  }
  orderCards
    .sort((a, b) => a.key.localeCompare(b.key))
    .forEach((c, i) => { c.el.style.order = String(i); });

  const nextGamesEl = document.getElementById('next-games');
  const shownIds = [nextBaseball, nextSoftball, nextHomeGame].filter(Boolean).map(gameKey);
  const remaining = allGames.filter(g => !shownIds.includes(gameKey(g))).slice(0, 4);
  if (remaining.length > 0) {
    nextGamesEl.innerHTML = remaining.map(renderGameCompact).join('');
  } else {
    nextGamesEl.innerHTML = '<p class="no-games">Keine weiteren Spiele</p>';
  }

  // Letzte 2 absolvierte Spiele (neueste zuerst). Nur einblenden, wenn
  // ueberhaupt was zu zeigen ist. Verschobene Spiele rutschen nach dem
  // Scraper-Re-Split (datum < today) nach vergangene, sind aber kein
  // Ergebnis – sie duerfen "Letzte Ergebnisse" nicht verdraengen.
  const past = (data.spiele.vergangene || [])
    .filter(g => g.status !== 'verschoben')
    .sort((a, b) => (b.datum + (b.zeit || '')).localeCompare(a.datum + (a.zeit || '')))
    .slice(0, 2);
  const lastResultsSection = document.getElementById('letzte-ergebnisse');
  if (past.length > 0) {
    document.getElementById('last-results').innerHTML = past.map(g => renderGame(g)).join('');
    lastResultsSection.hidden = false;
  }
}

function renderEventCard(event) {
  if (event.bild) {
    const link = /^https?:\/\/(www\.)?instagram\.com\//.test(event.instagram_post_url || '')
      ? event.instagram_post_url : null;
    const img = `<img class="event-flyer" src="${escapeHtml(event.bild)}" alt="${escapeHtml(event.bild_alt || event.titel || 'Event')}" loading="lazy">`;
    return link
      ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener">${img}</a>`
      : img;
  }
  const mail = event.kontakt_email
    ? `<a class="event-cta event-cta-mail" href="mailto:${escapeHtml(event.kontakt_email)}?subject=${encodeURIComponent('Interesse ' + (event.titel || 'Event'))}">✉️ ${escapeHtml(event.kontakt_email)}</a>`
    : '';
  const telDigits = event.kontakt_telefon ? event.kontakt_telefon.replace(/[^+\d]/g, '') : '';
  const telLabel = event.kontakt_telefon_name
    ? `${escapeHtml(event.kontakt_telefon_name)} · ${escapeHtml(event.kontakt_telefon)}`
    : escapeHtml(event.kontakt_telefon || '');
  const tel = event.kontakt_telefon
    ? `<a class="event-cta event-cta-tel" href="tel:${escapeHtml(telDigits)}">📞 ${telLabel}</a>`
    : '';
  const highlights = Array.isArray(event.highlights) && event.highlights.length
    ? `<ul class="event-highlights">${event.highlights.map(h => `<li>${escapeHtml(h)}</li>`).join('')}</ul>`
    : '';
  const igPost = /^https?:\/\/(www\.)?instagram\.com\//.test(event.instagram_post_url || '')
    ? `<a class="event-more-link" href="${escapeHtml(event.instagram_post_url)}" target="_blank" rel="noopener">Mehr Infos auf Instagram →</a>`
    : '';
  return `
    <span class="highlight-label">Event</span>
    <span class="game-sport event-tag">${escapeHtml(event.titel || 'Event')}</span>
    <span class="highlight-date">${formatDateLong(event.datum)}</span>
    ${event.zeit ? `<span class="highlight-time">${escapeHtml(event.zeit)} Uhr</span>` : ''}
    ${event.ort ? `<span class="highlight-location">📍 ${escapeHtml(event.ort)}</span>` : ''}
    ${highlights}
    ${(mail || tel) ? `<div class="event-ctas"><span class="event-ctas-label">Bei Interesse melden:</span>${mail}${tel}</div>` : ''}
    ${igPost}
  `;
}

loadData();
