// Bootstrap fuer blog.html (Blog-Uebersicht).

async function loadBlog() {
  const list = document.getElementById('blog-list');
  try {
    const data = await fetchJson('data/data.json');
    const posts = (data.blog && data.blog.posts) || [];
    if (posts.length === 0) {
      list.innerHTML = '<p class="no-games">Noch keine Beiträge.</p>';
      return;
    }
    const sorted = [...posts].sort((a, b) => (b.datum || '').localeCompare(a.datum || ''));
    list.innerHTML = sorted.map(renderPost).join('');
  } catch (err) {
    console.error(err);
    showError(list, 'Beiträge konnten nicht geladen werden.');
  }
}

function renderPost(post) {
  const url = escapeHtml(post.url);
  const title = escapeHtml(post.titel);
  const date = post.datum ? formatDateLong(post.datum) : '';
  const category = escapeHtml(post.kategorie || '');
  const teaser = escapeHtml(post.teaser || '');
  const cover = post.cover ? escapeHtml(post.cover) : '';
  const coverAlt = escapeHtml(post.cover_alt || post.titel || '');
  return `
    <article class="blog-card">
      <a href="${url}" class="blog-card-link">
        ${cover ? `<div class="blog-card-cover"><img src="${cover}" alt="${coverAlt}" loading="lazy" decoding="async"></div>` : ''}
        <div class="blog-card-body">
          <p class="blog-card-meta">
            ${date ? `<time datetime="${escapeHtml(post.datum)}">${date}</time>` : ''}
            ${category ? `<span class="blog-card-category">${category}</span>` : ''}
          </p>
          <h2 class="blog-card-title">${title}</h2>
          ${teaser ? `<p class="blog-card-teaser">${teaser}</p>` : ''}
          <span class="blog-card-more">Weiterlesen →</span>
        </div>
      </a>
    </article>
  `;
}

loadBlog();
