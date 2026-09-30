(() => {
  const papers = JSON.parse(document.getElementById('lit-data').textContent);
  const host = document.getElementById('lit-host');
  const topic = document.getElementById('lit-topic');
  const search = document.getElementById('lit-search');
  const body = document.getElementById('lit-results');
  const count = document.getElementById('lit-count');
  const more = document.getElementById('lit-more');
  let limit = 25;
  const render = () => {
    const query = search.value.trim().toLowerCase();
    const found = papers.filter(p => (!host.value || p.host === host.value) &&
      (!topic.value || p.strategies.includes(topic.value)) &&
      (!query || (p.title + ' ' + p.doi).toLowerCase().includes(query)));
    body.replaceChildren();
    for (const p of found.slice(0, limit)) {
      const row = document.createElement('tr');
      const title = document.createElement('td');
      const link = document.createElement('a');
      link.href = 'https://doi.org/' + encodeURI(p.doi);
      link.textContent = p.title;
      title.append(link, document.createElement('br'), document.createTextNode(p.doi));
      const categories = document.createElement('td');categories.textContent = p.host + '；' + p.family;
      const tags = document.createElement('td');tags.textContent = p.strategies.join('；') || '未命中本轮工程主题';
      row.append(title, categories, tags);body.append(row);
    }
    count.textContent = '共找到 ' + found.length + ' 篇，当前显示 ' + Math.min(found.length, limit) + ' 篇。';
    more.hidden = found.length <= limit;
  };
  for (const element of [host, topic, search]) element.addEventListener('input', () => {limit = 25; render();});
  more.addEventListener('click', () => {limit += 25; render();});
  render();
})();
