// Bootstrap fuer posts/awards-2026-09.html.
// Erzeugt Galerie-Grid + Lightbox aus Bildern in img/blog/<slug>/.

(function () {
  const IMG_BASE = '../img/blog/awards-2026-09/';
  // Reihenfolge wie im Artikel: Uebersicht, Spieler I, Spieler II, Glossar.
  const CAPTIONS = [
    'Regular Season Awards der Baseball Landesliga Ost – alle sechs ausgezeichneten Crazy Geese',
    'Awards & Positionen: Christian Suchard (#36), Michael Rigby (#3) und Bernd Ecker (#52)',
    'Awards & Positionen: Joey Vickery (#35), Peter Moser (#22) und Jörg Dorner (#12)',
    'Was die Auszeichnungen bedeuten: MVP, Silver Slugger und Gold Glove erklärt'
  ];
  const images = CAPTIONS.map((caption, i) => {
    const n = String(i + 1).padStart(2, '0');
    return {
      thumb: `${IMG_BASE}awards-2026-${n}-thumb.jpg`,
      full: `${IMG_BASE}awards-2026-${n}.jpg`,
      caption: caption
    };
  });

  const grid = document.getElementById('gallery-grid');
  if (!grid) return;
  grid.innerHTML = images.map((img, i) => `
    <button type="button" class="gallery-item" data-index="${i}" aria-label="Bild ${i + 1} öffnen">
      <img src="${escapeHtml(img.thumb)}" alt="${escapeHtml(img.caption)}" loading="lazy" decoding="async">
    </button>
  `).join('');

  setupLightbox('gallery-grid', images);
})();
