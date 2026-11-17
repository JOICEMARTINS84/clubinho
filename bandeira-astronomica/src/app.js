/* O Céu na Bandeira do Brasil — lógica do atlas.
   Os dados chegam em window.ATLAS = { stars, charts }, injetado por build.py
   a partir de estrelas.json e cartas_celestes.json (fonte única dos dados). */
(() => {
  'use strict';

  const { stars: STARS, charts: CHARTS } = window.ATLAS;

  /* ---------- Constantes ---------- */
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const VIEW_FULL = '0 0 2000 1400';   // bandeira inteira (20 × 14 módulos)
  const VIEW_ZOOM = '650 350 700 700'; // recorte sobre o círculo azul
  const STAR_RADIUS = [15, 12.5, 10, 7, 5];  // raio do pentagrama por grandeza (1ª a 5ª)
  const INNER_RATIO = 0.381966;        // raio interno / externo de um pentagrama regular
  const CHART = { width: 440, height: 285, fitWidth: 369, fitHeight: 221 };
  const HIT_RADIUS = { full: 24, zoom: 41 };

  const stackedQuery = matchMedia('(max-width: 1050px)');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Utilitários ---------- */
  const $ = (selector) => document.querySelector(selector);

  function svgEl(tag, attrs = {}, parent = null, text = null) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    if (text !== null) node.textContent = text;
    if (parent) parent.append(node);
    return node;
  }

  function htmlEl(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /** Minúsculas e sem acentos: "para" encontra "Pará". */
  const fold = (text) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');

  /** Pontos de um pentagrama regular centrado em (cx, cy). */
  function pentagram(cx, cy, radius) {
    const points = [];
    for (let i = 0; i < 10; i++) {
      const angle = -Math.PI / 2 + (i * Math.PI) / 5;
      const r = i % 2 ? radius * INNER_RATIO : radius;
      points.push(`${(cx + Math.cos(angle) * r).toFixed(3)},${(cy + Math.sin(angle) * r).toFixed(3)}`);
    }
    return points.join(' ');
  }

  /* ---------- Estado e referências ---------- */
  const byUf = new Map(STARS.map((s) => [s.uf, s]));
  const haystack = new Map(
    STARS.map((s) => [s.uf, fold([s.nome, s.estado, s.uf, s.constelacao, s.designacao].join(' '))])
  );
  const state = { selected: null, zoomed: false, query: '', constellation: '' };
  const starParts = new Map(); // uf -> { group, hit }
  const alphabetical = [...STARS].sort((a, b) => a.estado.localeCompare(b.estado, 'pt-BR'));
  const catalogueNumber = new Map(alphabetical.map((s, i) => [s.uf, String(i + 1).padStart(2, '0')]));
  let flagCallout;

  const ui = {
    page: $('.page'), detail: $('.detail'),
    wrap: $('#flag-wrap'), flag: $('#flag'), stars: $('#stars'), mag: $('#mag-legend'),
    filter: $('#filter'), search: $('#search'), zoom: $('#zoom'), random: $('#random'),
    results: $('#results'), index: $('#star-index'), picker: $('#picker'), prev: $('#prev'), next: $('#next'), counter: $('#counter'),
    name: $('#name'), state: $('#state'), desc: $('#desc'), con: $('#con'), des: $('#des'),
    grade: $('#grade'), uf: $('#uf'), apparentMag: $('#mag-aparente'), distance: $('#distance'),
    chart: $('#chart'), chartTitle: $('#chart-title'), chartCode: $('#chart-code'), chartCaption: $('#chart-caption'),
  };

  const matches = (s) =>
    (!state.constellation || state.constellation === s.constelacao) &&
    (!state.query || haystack.get(s.uf).includes(state.query));
  const visibleStars = () => STARS.filter(matches);

  /* ---------- Bandeira: camada interativa ---------- */
  function buildStarLayer() {
    for (const s of STARS) {
      const radius = STAR_RADIUS[s.grandeza - 1];
      const group = svgEl('g', {
        class: 'star-group', role: 'button', tabindex: 0,
        'aria-label': `${s.nome} — ${s.estado}, ${s.constelacao}`,
      }, ui.stars);
      svgEl('title', {}, group, `${s.nome} — ${s.estado}`);
      svgEl('circle', { cx: s.cx, cy: s.cy, r: radius + 8, class: 'star-ring' }, group);
      svgEl('polygon', { points: pentagram(s.cx, s.cy, radius), class: 'star-shape' }, group);
      const hit = svgEl('circle', { cx: s.cx, cy: s.cy, class: 'star-hit' }, group);

      group.addEventListener('click', () => showStar(s, { reveal: true }));
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          showStar(s, { reveal: true });
        }
      });
      starParts.set(s.uf, { group, hit });
    }
    flagCallout = svgEl('g', { class: 'flag-callout', 'aria-hidden': 'true' }, ui.stars);
  }

  function updateStarLayer() {
    for (const [uf, { group, hit }] of starParts) {
      const selected = uf === state.selected;
      group.classList.toggle('is-selected', selected);
      group.classList.toggle('is-dim', !matches(byUf.get(uf)));
      group.setAttribute('aria-pressed', String(selected));
      hit.setAttribute('r', state.zoomed ? HIT_RADIUS.zoom : HIT_RADIUS.full);
    }
    updateStarLabel();
  }

  // A marcação numérica evita cobrir os dizeres da faixa e remete à legenda sob a figura.
  function updateStarLabel() {
    flagCallout.replaceChildren();
    const s = byUf.get(state.selected);
    if (!s) return;
    const number = catalogueNumber.get(s.uf);
    $('#flag-number').textContent = number;
    $('#flag-selection').textContent = `${s.nome} — ${s.estado}`;
    const [vx, vy, vw, vh] = (state.zoomed ? VIEW_ZOOM : VIEW_FULL).split(' ').map(Number);
    const size = Math.max(state.zoomed ? 23 : 37, 11 * vw / Math.max(1, ui.wrap.clientWidth));
    const w = size * 1.75, h = size * 1.3;
    const band = $('#motto-band');
    const inBand = (x, y) => band.isPointInFill(new DOMPoint(x, y));
    const candidates = [];
    for (const radius of [70, 100, 135, 180, 230, 290, 360, 440]) {
      for (let i = 0; i < 32; i++) {
        const angle = i * Math.PI / 16;
        const x = s.cx + radius * Math.cos(angle), y = s.cy + radius * Math.sin(angle);
        const left = x - w / 2, top = y - h / 2;
        if (left < vx + 5 || top < vy + 5 || left + w > vx + vw - 5 || top + h > vy + vh - 5) continue;
        const samples = [0, .25, .5, .75, 1];
        if (samples.some(u => samples.some(v => inBand(left + w*u, top + h*v)))) continue;
        if (STARS.some(t => Math.abs(t.cx-x) < w/2 + 19 && Math.abs(t.cy-y) < h/2 + 19)) continue;
        const dx = x-s.cx, dy=y-s.cy;
        const begin = (STAR_RADIUS[s.grandeza-1]+10) / radius;
        const end = 1 - Math.min(w/(2*Math.abs(dx || .001)), h/(2*Math.abs(dy || .001)));
        const line = Array.from({length: 13}, (_, k) => begin+(end-begin)*k/12);
        if (line.some(t => inBand(s.cx+dx*t,s.cy+dy*t))) continue;
        if (STARS.some(t => t.uf !== s.uf && line.some(k => Math.hypot(t.cx-(s.cx+dx*k),t.cy-(s.cy+dy*k)) < STAR_RADIUS[t.grandeza-1]+5))) continue;
        candidates.push({x,y,radius,left,top,dx,dy,begin,end});
      }
      if(candidates.length) break;
    }
    const c = candidates[0];
    if (!c) return; // A estrela continua circulada e identificada na legenda externa.
    svgEl('line', {x1:s.cx+c.dx*c.begin,y1:s.cy+c.dy*c.begin,x2:s.cx+c.dx*c.end,y2:s.cy+c.dy*c.end}, flagCallout);
    svgEl('rect', {x:c.left,y:c.top,width:w,height:h}, flagCallout);
    svgEl('text', {x:c.x,y:c.y,'font-size':size}, flagCallout, number);
  }

  function setZoom(on) {
    state.zoomed = on;
    ui.wrap.classList.toggle('zoomed', on);
    const viewBox = on ? VIEW_ZOOM : VIEW_FULL;
    ui.flag.setAttribute('viewBox', viewBox);
    ui.stars.setAttribute('viewBox', viewBox);
    ui.zoom.textContent = on ? 'Ver bandeira inteira' : 'Ampliar disco';
    ui.zoom.setAttribute('aria-pressed', String(on));
    updateStarLayer();
  }

  function buildMagnitudeLegend() {
    ui.mag.append(htmlEl('span', 'mag-title', 'Grandezas gráficas:'));
    STAR_RADIUS.forEach((radius, index) => {
      const item = htmlEl('span', 'mag-item');
      const icon = svgEl('svg', { viewBox: '-16 -16 32 32', 'aria-hidden': 'true' });
      svgEl('polygon', { points: pentagram(0, 0, radius) }, icon);
      item.append(icon, `${index + 1}ª`);
      ui.mag.append(item);
    });
  }

  /* ---------- Controles: filtro, busca, lista de estados ---------- */
  function buildControls() {
    const constellations = [...new Set(STARS.map((s) => s.constelacao))]
      .sort((a, b) => a.localeCompare(b, 'pt-BR'));
    for (const name of constellations) ui.filter.append(new Option(name, name));

    $('#star-total').textContent = STARS.length;
    $('#constellation-total').textContent = constellations.length;
    $('#index-total').textContent = STARS.length;
    const byState = alphabetical;
    for (const s of byState) ui.picker.append(new Option(`${s.estado} — ${s.nome}`, s.uf));
    byState.forEach((s, number) => {
      const button = htmlEl('button', 'index-entry');
      button.type = 'button';
      button.setAttribute('aria-label', `${s.estado}: ${s.nome}`);
      button.dataset.uf = s.uf;
      button.append(
        htmlEl('span', 'ordinal', String(number + 1).padStart(2, '0')),
        htmlEl('span', 'uf', s.uf),
        htmlEl('span', 'star-name', s.nome)
      );
      button.addEventListener('click', () => showStar(s, { reveal: true }));
      ui.index.append(button);
    });
  }

  function renderResults() {
    const active = Boolean(state.query || state.constellation);
    ui.results.hidden = !active;
    ui.results.replaceChildren();
    if (!active) return;

    const list = visibleStars();
    if (!list.length) {
      ui.results.append(htmlEl('span', 'empty', 'Nenhuma estrela encontrada'));
      return;
    }
    for (const s of list) {
      const chip = htmlEl('button', 'btn chip', `${s.uf} · ${s.nome}`);
      chip.type = 'button';
      chip.addEventListener('click', () => showStar(s, { reveal: true }));
      ui.results.append(chip);
    }
  }

  function updateCounter() {
    const list = visibleStars();
    const index = list.findIndex((s) => s.uf === state.selected);
    ui.counter.textContent = `${index >= 0 ? index + 1 : '—'} / ${list.length}`;
  }

  /** Reaplica filtro e busca em todos os pontos da interface. */
  function updateIndex() {
    ui.index.querySelectorAll('.index-entry').forEach((entry) => {
      const s = byUf.get(entry.dataset.uf);
      const current = entry.dataset.uf === state.selected;
      entry.classList.toggle('is-selected', current);
      entry.classList.toggle('is-dim', !matches(s));
      entry.setAttribute('aria-current', current ? 'true' : 'false');
      entry.hidden = !matches(s) && Boolean(state.query || state.constellation);
    });
  }

  function refresh() {
    renderResults();
    updateStarLayer();
    updateIndex();
    updateCounter();
  }

  function step(delta) {
    const list = visibleStars();
    if (!list.length) return;
    const index = list.findIndex((s) => s.uf === state.selected);
    const next = index < 0 ? (delta > 0 ? 0 : list.length - 1) : (index + delta + list.length) % list.length;
    showStar(list[next]);
  }

  /* ---------- Ficha da estrela ---------- */
  function showStar(s, { reveal = false } = {}) {
    state.selected = s.uf;
    ui.name.textContent = s.nome;
    ui.state.replaceChildren(htmlEl('span', 'state', `${s.estado} · ${s.uf}`));
    // O catálogo é preservado; omitem-se apenas notas que repetem os campos da ficha.
    const redundant = ['AC', 'RO', 'MG', 'CE', 'PE', 'SE'];
    ui.desc.textContent = redundant.includes(s.uf) ? '' : (s.curiosidade || '');
    ui.desc.hidden = !ui.desc.textContent;
    ui.con.textContent = s.constelacao;
    ui.des.textContent = s.designacao;
    ui.grade.textContent = `${s.grandeza}ª de 5`;
    const magnitude = CHARTS[s.constelacao]?.highlights?.[s.uf]?.m;
    ui.apparentMag.textContent = Number.isFinite(magnitude)
      ? magnitude.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' mag'
      : '—';
    // Sem distância na base atual. Não derivar distância da magnitude.
    const distance = s.distancia_anos_luz;
    ui.distance.textContent = Number.isFinite(distance) ? distance.toLocaleString('pt-BR') : '—';
    ui.uf.textContent = `${s.estado} (${s.uf})`;
    ui.picker.value = s.uf;

    drawChart(s);
    updateStarLayer();
    updateIndex();
    updateCounter();

    // Com os painéis empilhados, leva a pessoa até a ficha depois do toque.
    if (reveal && stackedQuery.matches) {
      requestAnimationFrame(() =>
        ui.detail.scrollIntoView({ behavior: reducedMotion.matches ? 'auto' : 'smooth', block: 'start' })
      );
    }
  }

  /* ---------- Carta celeste ---------- */
  /** Diferença de longitude em (-180, 180], tratando a virada em 360°. */
  const deltaLongitude = (lon, origin) => ((((lon - origin + 540) % 360) + 360) % 360) - 180;

  /** Escolhe o canto (cima/baixo × direita/esquerda) onde o rótulo da estrela selecionada
      cobre menos pontos da carta e não ultrapassa a borda. */
  function placeChartLabel(mx, my, text, occupied) {
    const width = text.length * 7.5 + 4;
    let best = null;
    for (const side of [1, -1]) {       // 1 = direita, -1 = esquerda
      for (const rise of [-1, 1]) {     // -1 = acima, 1 = abaixo
        const x = mx + side * 20;
        const y = my + rise * 17 + (rise > 0 ? 8 : 0);
        const box = { x0: side > 0 ? x : x - width, x1: side > 0 ? x + width : x, y0: y - 12, y1: y + 4 };
        let score = occupied.filter(([px, py]) =>
          px > box.x0 - 4 && px < box.x1 + 4 && py > box.y0 - 4 && py < box.y1 + 4).length;
        if (box.x0 < 4 || box.x1 > CHART.width - 4 || box.y0 < 4 || box.y1 > CHART.height - 4) score += 100;
        if (!best || score < best.score) best = { score, side, rise, x, y, lineY: y + (rise < 0 ? 4 : -4) };
      }
    }
    return best;
  }

  function drawChart(s) {
    const chart = CHARTS[s.constelacao];
    const marker = chart && chart.highlights[s.uf];
    const svg = ui.chart;
    svg.replaceChildren();

    if (!marker) {
      ui.chartTitle.textContent = s.constelacao;
      ui.chartCode.textContent = '—';
      svgEl('text', { class: 'chart-empty', x: CHART.width / 2, y: 145, 'text-anchor': 'middle' }, svg, 'Carta celeste indisponível');
      ui.chartCaption.textContent = 'Carta celeste indisponível para esta constelação.';
      return;
    }

    const highlights = Object.entries(chart.highlights);
    const allPoints = [
      ...chart.lines.flat(),
      ...chart.stars.map((star) => star.l),
      ...highlights.map(([, star]) => star.l),
    ];

    // Projeção equiretangular local; polar para Oitante, que cerca o polo sul celeste.
    // A origem é fixa por constelação: o desenho não "salta" ao trocar de estrela.
    const polar = chart.code === 'Oct';
    const origin = highlights[0][1].l[0];
    const meanDec = allPoints.reduce((sum, p) => sum + p[1], 0) / allPoints.length;
    const cosLat = Math.max(0.12, Math.cos((meanDec * Math.PI) / 180));
    const project = ([lon, dec]) => {
      if (polar) {
        const radius = 90 + dec;
        const angle = (lon * Math.PI) / 180;
        return [radius * Math.cos(angle), radius * Math.sin(angle)];
      }
      return [deltaLongitude(lon, origin) * cosLat, -dec];
    };

    const projected = allPoints.map(project);
    const xs = projected.map((p) => p[0]);
    const ys = projected.map((p) => p[1]);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const spanX = Math.max(5, Math.max(...xs) - minX);
    const spanY = Math.max(4, Math.max(...ys) - minY);
    const scale = Math.min(CHART.fitWidth / spanX, CHART.fitHeight / spanY);
    const offsetX = (CHART.width - spanX * scale) / 2;
    const offsetY = (CHART.height - spanY * scale) / 2;
    const toXY = (pair) => {
      const [x, y] = project(pair);
      return [offsetX + (x - minX) * scale, offsetY + (y - minY) * scale];
    };

    svgEl('title', {}, svg, `Carta celeste de ${s.constelacao}, estrela ${s.nome} destacada`);

    // Ligações convencionais entre as estrelas do catálogo.
    for (const segment of chart.lines) {
      const points = segment.map(toXY).map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
      svgEl('polyline', { points, class: 'chart-line' }, svg);
    }

    // Estrelas do catálogo, com diâmetro aproximadamente proporcional à magnitude aparente.
    for (const star of chart.stars) {
      const [x, y] = toXY(star.l);
      const radius = Math.max(1.4, Math.min(4.4, 5.6 - star.m * 0.8));
      svgEl('circle', { cx: x, cy: y, r: radius, class: 'chart-star' }, svg);
    }

    // Outras estrelas da bandeira nesta constelação: clicáveis.
    for (const [uf, star] of highlights) {
      if (uf === s.uf) continue;
      const peer = byUf.get(uf);
      const [x, y] = toXY(star.l);
      const group = svgEl('g', {
        class: 'chart-peer', role: 'button', tabindex: 0,
        'aria-label': `${peer.nome} — ${peer.estado}`,
      }, svg);
      svgEl('title', {}, group, `${peer.nome} — ${peer.estado}`);
      svgEl('circle', { cx: x, cy: y, r: 12, class: 'hit' }, group);
      svgEl('circle', { cx: x, cy: y, r: 3.4, class: 'dot' }, group);
      svgEl('text', { x: x + 6, y: y - 6, class: 'chart-uf' }, group, uf);
      group.addEventListener('click', () => showStar(peer));
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          showStar(peer);
        }
      });
    }

    // Estrela selecionada: marcador, anel, linha de chamada e designação.
    const [mx, my] = toXY(marker.l);
    svgEl('circle', { cx: mx, cy: my, r: 5.2, class: 'chart-active' }, svg);
    svgEl('circle', { cx: mx, cy: my, r: 14, class: 'chart-ring' }, svg);
    const label = placeChartLabel(mx, my, s.designacao, [
      ...chart.stars.map((star) => toXY(star.l)),
      ...highlights.filter(([uf]) => uf !== s.uf).map(([, star]) => toXY(star.l)),
    ]);
    svgEl('line', { x1: mx + label.side * 10, y1: my + label.rise * 10, x2: label.x, y2: label.lineY, class: 'chart-pointer' }, svg);
    svgEl('text', { x: label.x, y: label.y, 'text-anchor': label.side > 0 ? 'start' : 'end', class: 'chart-label' }, svg, s.designacao);

    ui.chartTitle.textContent = s.constelacao;
    ui.chartCode.textContent = chart.code.toUpperCase();
    const total = highlights.length;
    ui.chartCaption.textContent = total > 1
      ? `${total} estrelas desta constelação compõem a bandeira. A estrela selecionada está circulada.`
      : 'Esta é a única estrela da constelação representada na bandeira.';
  }

  /* ---------- Altura responsiva dentro do Streamlit ---------- */
  function fitFrameHeight() {
    let lastHeight = 0;
    const apply = () => {
      const height = Math.ceil(ui.page.getBoundingClientRect().height);
      if (height <= 0 || Math.abs(height - lastHeight) < 2) return;
      lastHeight = height;
      // components.html recebe esta mensagem mesmo quando o iframe é isolado.
      if (window.parent !== window) {
        window.parent.postMessage({
          isStreamlitMessage: true,
          type: 'streamlit:setFrameHeight',
          height,
        }, '*');
      }
      // Fallback para ambientes em que frameElement é acessível.
      try { if (window.frameElement) window.frameElement.style.height = `${height}px`; }
      catch (error) { /* iframe isolado: usa apenas a mensagem acima */ }
    };
    if ('ResizeObserver' in window) new ResizeObserver(apply).observe(ui.page);
    window.addEventListener('load', apply);
    window.addEventListener('resize', apply, { passive: true });
    if (document.fonts?.ready) document.fonts.ready.then(apply);
    apply();
  }

  /* ---------- Eventos e inicialização ---------- */
  ui.filter.addEventListener('change', () => { state.constellation = ui.filter.value; refresh(); });
  ui.search.addEventListener('input', () => { state.query = fold(ui.search.value.trim()); refresh(); });
  ui.zoom.addEventListener('click', () => setZoom(!state.zoomed));
  ui.prev.addEventListener('click', () => step(-1));
  ui.next.addEventListener('click', () => step(1));
  ui.random.addEventListener('click', () => {
    const list = visibleStars();
    const others = list.filter((s) => s.uf !== state.selected);
    const pool = others.length ? others : list;
    if (pool.length) showStar(pool[Math.floor(Math.random() * pool.length)], { reveal: true });
  });
  ui.picker.addEventListener('change', () => {
    const s = byUf.get(ui.picker.value);
    if (!s) return;
    // Escolher pelo estado deve funcionar mesmo com filtro ou busca ativos.
    ui.filter.value = '';
    ui.search.value = '';
    state.constellation = '';
    state.query = '';
    showStar(s, { reveal: true });
    refresh();
  });

  buildControls();
  buildMagnitudeLegend();
  buildStarLayer();
  setZoom(state.zoomed);
  showStar(STARS[0]);
  fitFrameHeight();
  window.addEventListener('resize', updateStarLabel, { passive: true });
})();
