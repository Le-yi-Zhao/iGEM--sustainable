(() => {
  const group = document.getElementById('model-group');
  if (!group) return;
  const search = document.getElementById('model-search');
  const sd = document.getElementById('model-show-sd');
  const tables = [...document.querySelectorAll('.model-matrix')];
  const rows = [...document.querySelectorAll('[data-model-row]')];
  function update() {
    const q = search.value.trim().toLocaleLowerCase();
    const ids = new Set();
    for (const row of rows) {
      const target = row.dataset.id === 'glabridin';
      const match = (group.value === '全部' || row.dataset.group === group.value) && row.dataset.search.toLocaleLowerCase().includes(q);
      row.hidden = !target && !match;
      if (match && !target) ids.add(row.dataset.id);
    }
    tables.forEach(t => t.classList.toggle('hide-sd', !sd.checked));
    document.getElementById('model-count').textContent = `当前显示 ${ids.size} 种参照，光甘草定固定保留。`;
  }
  group.addEventListener('change', update);
  search.addEventListener('input', update);
  sd.addEventListener('change', update);
  document.getElementById('model-reset').addEventListener('click', () => {
    group.value = '全部'; search.value = ''; sd.checked = true; update();
  });
  update();
})();
