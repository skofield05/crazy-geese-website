// Bootstrap fuer posts/meister-2026-09.html.
// Erzeugt Galerie-Grid + Lightbox aus Bildern in img/blog/meister-2026-09/.

(function () {
  const IMG_BASE = '../img/blog/meister-2026-09/';
  // Reihenfolge ist kuratiert (Teamfoto zuerst, dann Spielende -> Jubel ->
  // Pokale -> Presse -> Rahmenprogramm) und entspricht der Nummerierung der
  // Dateien. CAPTIONS ist die sichtbare Bildunterschrift; ALTS beschreibt das
  // Bild fuer Screenreader und ist ausfuehrlicher.
  const PHOTOS = [
    ['Die Meistermannschaft 2026 vor der Tribüne am Geese Ballpark',
     'Das Team der Rohrbach Crazy Geese in weißen Champions-Shirts, vordere Reihe kniend mit zwei Pokalen, davor die Tribüne des Geese Ballpark'],
    ['Handshake-Line nach dem Schlussout',
     'Beide Mannschaften stehen nach dem Finale in einer Reihe am Feld und klatschen sich ab'],
    ['Der Jubel unmittelbar nach dem Spiel',
     'Die Crazy Geese in ihren dunkelblauen Spieltrikots jubeln mit erhobenen Armen am Feld'],
    ['Die ersten Flaschen gehen auf',
     'Drei Spieler in Champions-Shirts reißen die Arme hoch, um sie herum liegen Sektflaschen im Gras'],
    ['Pokale und Medaillen vor der Siegerehrung',
     'Ein langer Tisch voller goldener Pokale, jeder mit einem Baseball als Aufsatz, daneben Kisten mit Sektflaschen'],
    ['Der Meisterpokal geht in die Höhe',
     'Ein Spieler hält den Meisterpokal mit beiden Händen über den Kopf, dahinter ein Fotograf und Zuschauer hinter dem Fangnetz'],
    ['Jubel mit dem Pokal am Feld',
     'Ein Spieler reißt den Pokal mit einer Hand in die Höhe und jubelt'],
    ['Zwei Geese mit ihren Auszeichnungen',
     'Zwei Spieler stehen Arm in Arm im Gras und halten ihre Pokale in die Kamera, auf den Shirts steht Back to Back Champions'],
    ['Die Mannschaft im Kreis um den Pokal',
     'Die Mannschaft steht im Kreis am Feld, in der Mitte wird der Pokal hochgehalten, im Hintergrund die Felder hinter dem Ballpark'],
    ['Interview direkt nach dem Spiel',
     'Ein Spieler im Champions-Shirt steht am Infield und spricht in ein Mikrofon, ihm gegenüber ein Reporter'],
    ['Das ORF-Kamerateam am Feld',
     'Ein Kameramann mit Schulterkamera und Licht filmt einen Spieler am Rand des Infields, im Gras steht ein Pokal neben einer Sektflasche'],
    ['Volle Tribüne am Finaltag',
     'Zuschauer sitzen auf den grünen Sitzschalen der überdachten Tribüne und verfolgen das Spiel durch das Fangnetz'],
    ['Hüpfburg für die jüngsten Fans',
     'Eine bunte Hüpfburg neben dem Spielfeld, davor Familien mit Kindern auf der Wiese']
  ];

  const images = PHOTOS.map(function (entry, i) {
    const n = String(i + 1).padStart(2, '0');
    return {
      thumb: IMG_BASE + 'meister-2026-' + n + '-thumb.jpg',
      full: IMG_BASE + 'meister-2026-' + n + '.jpg',
      caption: entry[0],
      alt: entry[1]
    };
  });

  const grid = document.getElementById('gallery-grid');
  if (!grid) return;
  grid.innerHTML = images.map(function (img, i) {
    return '<button type="button" class="gallery-item" data-index="' + i + '"' +
      ' aria-label="Bild ' + (i + 1) + ' öffnen: ' + escapeHtml(img.caption) + '">' +
      '<img src="' + escapeHtml(img.thumb) + '" alt="' + escapeHtml(img.alt) + '"' +
      ' loading="lazy" decoding="async"></button>';
  }).join('');

  setupLightbox('gallery-grid', images);
})();
