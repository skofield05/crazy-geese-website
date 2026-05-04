// Einfache Lightbox fuer Blog-Galerien.
//
// Benoetigt im DOM:
//   #lightbox, #lightbox-img, #lightbox-caption,
//   #lightbox-close, #lightbox-prev, #lightbox-next
//
// Aufruf (einmal pro Seite, nicht SPA-sicher – global keydown-Listener):
//   setupLightbox('gallery-grid', [{ thumb, full, caption }, ...]);
//
// Features:
//   - Keyboard: ESC schliesst, ArrowLeft/Right navigieren
//   - Touch: horizontaler Swipe navigiert
//   - Fokus-Trap: Tab/Shift-Tab zirkuliert zwischen Close/Prev/Next
//   - Fokus-Restore beim Schliessen auf das Element, das die Lightbox oeffnete
//   - Body-Scroll wird waehrend der Anzeige gesperrt

function setupLightbox(gridId, images) {
  const grid = document.getElementById(gridId);
  const lightbox = document.getElementById('lightbox');
  const img = document.getElementById('lightbox-img');
  const caption = document.getElementById('lightbox-caption');
  const btnClose = document.getElementById('lightbox-close');
  const btnPrev = document.getElementById('lightbox-prev');
  const btnNext = document.getElementById('lightbox-next');
  if (!grid || !lightbox || !img || !btnClose || !btnPrev || !btnNext) return;

  const focusables = [btnClose, btnPrev, btnNext];
  let currentIndex = 0;
  let lastFocus = null;

  function setSiblingsInert(inert) {
    Array.from(document.body.children).forEach(el => {
      if (el === lightbox || el.tagName === 'SCRIPT') return;
      if (inert) el.setAttribute('inert', '');
      else el.removeAttribute('inert');
    });
  }

  function open(index) {
    currentIndex = index;
    render();
    lastFocus = document.activeElement;
    lightbox.hidden = false;
    document.body.style.overflow = 'hidden';
    setSiblingsInert(true);
    btnClose.focus();
  }

  function close() {
    lightbox.hidden = true;
    document.body.style.overflow = '';
    setSiblingsInert(false);
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }

  function next() {
    currentIndex = (currentIndex + 1) % images.length;
    render();
  }

  function prev() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    render();
  }

  // Defensive: nur Pfade unter / oder explizite http(s)-URLs zulassen.
  // Verhindert "javascript:" / "data:text/html" o.ae., falls images[] mal
  // aus weniger vertrauenswuerdiger Quelle kommt (data.json, Drittanbieter).
  function isSafeImageUrl(url) {
    if (typeof url !== 'string' || !url) return false;
    if (url.startsWith('/') || url.startsWith('./') || url.startsWith('../')) return true;
    if (/^https?:\/\//i.test(url)) return true;
    // Relative Pfade ohne fuehrenden Slash (z.B. "img/blog/...") akzeptieren
    return !/^[a-z][a-z0-9+.-]*:/i.test(url);
  }

  function render() {
    const item = images[currentIndex];
    img.src = isSafeImageUrl(item.full) ? item.full : '';
    img.alt = item.caption || '';
    caption.textContent = item.caption || '';
  }

  function trapTab(e) {
    if (e.key !== 'Tab') return;
    const idx = focusables.indexOf(document.activeElement);
    if (idx === -1) {
      e.preventDefault();
      btnClose.focus();
      return;
    }
    if (e.shiftKey && idx === 0) {
      e.preventDefault();
      focusables[focusables.length - 1].focus();
    } else if (!e.shiftKey && idx === focusables.length - 1) {
      e.preventDefault();
      focusables[0].focus();
    }
  }

  grid.addEventListener('click', function(e) {
    const btn = e.target.closest('.gallery-item');
    if (!btn) return;
    const index = Number(btn.dataset.index);
    if (Number.isFinite(index)) open(index);
  });

  btnClose.addEventListener('click', close);
  btnPrev.addEventListener('click', prev);
  btnNext.addEventListener('click', next);

  lightbox.addEventListener('click', function(e) {
    if (e.target === lightbox) close();
  });

  document.addEventListener('keydown', function(e) {
    if (lightbox.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight') next();
    else if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'Tab') trapTab(e);
  });

  // Einfache Swipe-Gesten fuer Touch
  let touchStartX = null;
  lightbox.addEventListener('touchstart', function(e) {
    if (e.touches.length === 1) touchStartX = e.touches[0].clientX;
  }, { passive: true });
  lightbox.addEventListener('touchend', function(e) {
    if (touchStartX === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(dx) < 40) return;
    if (dx < 0) next(); else prev();
  });
}
