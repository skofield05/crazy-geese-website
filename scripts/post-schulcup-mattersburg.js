// Bootstrap fuer posts/schulcup-mattersburg-2026-04.html.
// Erzeugt Galerie-Grid + Lightbox aus Bildern in img/blog/<slug>/.

(function () {
  const IMG_BASE = '../img/blog/schulcup-mattersburg-2026-04/';
  const TOTAL = 9;
  const images = Array.from({ length: TOTAL }, (_, i) => {
    const n = String(i + 1).padStart(2, '0');
    return {
      thumb: `${IMG_BASE}schulcup-mattersburg-${n}-thumb.jpg`,
      full: `${IMG_BASE}schulcup-mattersburg-${n}.jpg`,
      caption: `Schulcup Mattersburg – Bild ${i + 1} von ${TOTAL}`
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
