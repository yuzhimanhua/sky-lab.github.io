// Progressive enhancement: all research content is readable without JavaScript.
(() => {
  const toolbar = document.querySelector('.publication-toolbar');
  if (!toolbar) return;

  const search = document.querySelector('#publication-search');
  const year = document.querySelector('#publication-year');
  const items = [...document.querySelectorAll('#publication-results .publication-item')];
  const sections = [...document.querySelectorAll('#publication-results .publication-year')];
  const count = toolbar.querySelector('.result-count');
  const emptyState = document.querySelector('.empty-state');
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const index = items.map(item => ({ item, text: normalize(item.dataset.search) }));

  const filter = () => {
    const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const { item, text } of index) {
      const matches = (year.value === 'all' || item.dataset.year === year.value)
        && terms.every(term => text.includes(term));
      item.hidden = !matches;
      if (matches) visible++;
    }
    for (const section of sections) {
      const shown = section.querySelectorAll('.publication-item:not([hidden])').length;
      section.hidden = shown === 0;
      section.querySelector('.group-count').textContent = `${shown} ${shown === 1 ? 'paper' : 'papers'}`;
    }
    count.textContent = `${visible} ${visible === 1 ? 'publication' : 'publications'}`;
    emptyState.hidden = visible !== 0;
  };

  toolbar.hidden = false;
  toolbar.addEventListener('submit', event => event.preventDefault());
  search.addEventListener('input', filter);
  year.addEventListener('change', filter);
  document.querySelector('#reset-filters').addEventListener('click', () => {
    search.value = '';
    year.value = 'all';
    filter();
    search.focus();
  });
  filter();
})();
