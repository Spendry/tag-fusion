// TagFusion: tag combining on the home page and search on the search page.
// The pages work as plain links without this file; it only adds the live filtering.
(function () {
  'use strict';
  var script = document.currentScript;
  var root = script.getAttribute('data-root') || '';

  function slug(value) {
    return value.toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_-]+/g, '-');
  }
  function domain(url) {
    try { return new URL(url).hostname.replace(/^www\./, ''); } catch (e) { return url; }
  }
  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    for (var key in attrs || {}) node.setAttribute(key, attrs[key]);
    if (text != null) node.textContent = text;
    return node;
  }
  function card(site) {
    var li = el('li', { 'class': 'card' });
    var h = el('h3');
    h.appendChild(el('a', { href: site.url, target: '_blank', rel: 'noopener noreferrer' }, site.name));
    li.appendChild(h);
    var where = el('p', { 'class': 'where' }, domain(site.url) + ' · ');
    where.appendChild(el('a', { href: root + 'category/' + slug(site.category) + '/' }, site.category));
    li.appendChild(where);
    li.appendChild(el('p', {}, site.description));
    var chips = el('ul', { 'class': 'chips' });
    site.tags.forEach(function (tag) {
      var item = el('li');
      item.appendChild(el('a', { 'class': 'chip', href: root + 'tag/' + slug(tag) + '/' }, '#' + tag));
      chips.appendChild(item);
    });
    li.appendChild(chips);
    return li;
  }
  function show(list, sites) {
    list.textContent = '';
    sites.forEach(function (site) { list.appendChild(card(site)); });
  }
  function plural(n, word) { return n + ' ' + word + (n === 1 ? '' : 's'); }

  function startPath(sites) {
    var box = document.getElementById('path');
    if (!box) return;
    var chips = Array.prototype.slice.call(box.querySelectorAll('button.chip'));
    var select = document.getElementById('path-category');
    var list = document.getElementById('path-results');
    var status = document.getElementById('path-status');
    var chosen = [];
    var params = new URLSearchParams(location.search);
    (params.get('tags') || '').split(',').forEach(function (t) { if (t) chosen.push(t); });

    function matches(extra) {
      var want = extra ? chosen.concat([extra]) : chosen;
      return sites.filter(function (site) {
        if (select.value && site.category !== select.value) return false;
        return want.every(function (tag) { return site.tags.indexOf(tag) !== -1; });
      });
    }
    function render() {
      var found = matches();
      chips.forEach(function (chip) {
        var tag = chip.getAttribute('data-tag');
        var on = chosen.indexOf(tag) !== -1;
        chip.setAttribute('aria-pressed', on ? 'true' : 'false');
        chip.disabled = !on && matches(tag).length === 0;
      });
      if (!chosen.length && !select.value) {
        status.textContent = 'Pick a category or a tag to begin. Each tag you add narrows the list.';
        show(list, []);
        return;
      }
      status.textContent = plural(found.length, 'place') + (chosen.length ? ' with ' + chosen.map(function (t) { return '#' + t; }).join(' + ') : '') + (select.value ? ' in ' + select.value : '') + '.';
      show(list, found);
    }
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        var tag = chip.getAttribute('data-tag');
        var at = chosen.indexOf(tag);
        if (at === -1) chosen.push(tag); else chosen.splice(at, 1);
        render();
      });
    });
    select.addEventListener('change', render);
    document.getElementById('path-clear').addEventListener('click', function () {
      chosen = []; select.value = ''; render();
    });
    document.getElementById('path-surprise').addEventListener('click', function () {
      var pool = matches();
      if (!pool.length) pool = sites;
      var pick = pool[Math.floor(Math.random() * pool.length)];
      status.textContent = 'Surprise: one place picked at random.';
      show(list, [pick]);
    });
    box.hidden = false;
    render();
  }

  function startSearch(sites) {
    var form = document.getElementById('search-form');
    if (!form) return;
    var input = document.getElementById('q');
    var list = document.getElementById('search-results');
    var status = document.getElementById('search-status');
    function run() {
      var words = input.value.toLowerCase().split(/\s+/).filter(Boolean);
      if (!words.length) {
        status.textContent = 'Enter a word or phrase to search the directory.';
        show(list, []);
        return;
      }
      var found = sites.filter(function (site) {
        var hay = (site.name + ' ' + site.description + ' ' + site.category + ' ' + site.tags.join(' ') + ' ' + site.url).toLowerCase();
        return words.every(function (w) { return hay.indexOf(w) !== -1; });
      });
      status.textContent = found.length ? found.length + (found.length === 1 ? ' match' : ' matches') + ' for “' + input.value.trim() + '”.' : 'Nothing matches “' + input.value.trim() + '”. Try a shorter word or a tag.';
      show(list, found);
    }
    input.value = new URLSearchParams(location.search).get('q') || '';
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      history.replaceState(null, '', '?q=' + encodeURIComponent(input.value.trim()));
      run();
    });
    input.addEventListener('input', run);
    run();
  }

  if (!document.getElementById('path') && !document.getElementById('search-form')) return;
  fetch(root + 'catalog.json')
    .then(function (response) { return response.json(); })
    .then(function (sites) { startPath(sites); startSearch(sites); })
    .catch(function () {
      var status = document.getElementById('path-status') || document.getElementById('search-status');
      if (status) status.textContent = 'The directory could not be loaded. Browse by tag or category instead.';
    });
})();
