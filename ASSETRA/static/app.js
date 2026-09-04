// ---------- Toasts (auto-dismiss flash messages) ----------
document.querySelectorAll('.flash').forEach((el, i) => {
  setTimeout(() => el.classList.add('flash-show'), 30 + i * 60);
  const timer = setTimeout(() => dismissFlash(el), 4200);
  el.addEventListener('click', () => { clearTimeout(timer); dismissFlash(el); });
});
function dismissFlash(el) {
  el.classList.remove('flash-show');
  setTimeout(() => el.remove(), 200);
}

// ---------- Global quick search ----------
(function () {
  const input = document.getElementById('quick-search');
  const results = document.getElementById('quick-search-results');
  if (!input || !results) return;

  let controller = null;
  let activeIndex = -1;

  function closeResults() {
    results.classList.remove('open');
    results.innerHTML = '';
    activeIndex = -1;
  }

  function render(items) {
    if (!items.length) {
      results.innerHTML = '<div class="qs-empty">No matching assets</div>';
      results.classList.add('open');
      return;
    }
    results.innerHTML = items.map((a, i) => `
      <a href="/assets/${a.id}" class="qs-item" data-idx="${i}">
        <span class="mono qs-tag">${a.asset_tag}</span>
        <span class="qs-name">${a.name}</span>
        <span class="badge badge-${a.status.toLowerCase().replace(/ /g, '-')}">${a.status}</span>
      </a>`).join('');
    results.classList.add('open');
  }

  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (controller) controller.abort();
    if (!q) { closeResults(); return; }
    controller = new AbortController();
    fetch(`/api/assets/search?q=${encodeURIComponent(q)}`, { signal: controller.signal })
      .then(r => r.json())
      .then(render)
      .catch(() => {});
  });

  input.addEventListener('keydown', (e) => {
    const items = results.querySelectorAll('.qs-item');
    if (e.key === 'ArrowDown') { e.preventDefault(); activeIndex = Math.min(activeIndex + 1, items.length - 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); activeIndex = Math.max(activeIndex - 1, 0); }
    else if (e.key === 'Enter') { if (items[activeIndex]) { items[activeIndex].click(); } return; }
    else if (e.key === 'Escape') { closeResults(); input.blur(); return; }
    else return;
    items.forEach(it => it.classList.remove('qs-active'));
    if (items[activeIndex]) {
      items[activeIndex].classList.add('qs-active');
      items[activeIndex].scrollIntoView({ block: 'nearest' });
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.quick-search')) closeResults();
  });

  document.addEventListener('keydown', (e) => {
    if ((e.key === 'k' && (e.metaKey || e.ctrlKey))) {
      e.preventDefault();
      input.focus();
      input.select();
    }
  });
})();

// ---------- Sortable tables ----------
document.querySelectorAll('table[data-sortable] th[data-key]').forEach((th) => {
  th.addEventListener('click', () => {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const idx = Array.from(th.parentNode.children).indexOf(th);
    const asc = th.getAttribute('data-dir') !== 'asc';

    table.querySelectorAll('th[data-key]').forEach(h => h.removeAttribute('data-dir'));
    th.setAttribute('data-dir', asc ? 'asc' : 'desc');

    rows.sort((a, b) => {
      const av = a.children[idx].getAttribute('data-sort') || a.children[idx].textContent.trim();
      const bv = b.children[idx].getAttribute('data-sort') || b.children[idx].textContent.trim();
      const an = parseFloat(av), bn = parseFloat(bv);
      let cmp;
      if (!isNaN(an) && !isNaN(bn) && av !== '' && bv !== '') cmp = an - bn;
      else cmp = av.localeCompare(bv);
      return asc ? cmp : -cmp;
    });
    rows.forEach(r => tbody.appendChild(r));
  });
});

// ---------- QR download (PNG) ----------
function downloadQR(filename) {
  const canvas = document.querySelector('#qrbox canvas');
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = filename || 'asset-qr.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
}