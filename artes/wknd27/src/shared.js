// Base comum das 4 artes — formato (feed/story), aleatório com semente, ajuste de texto, logos e grão.
(function () {
  const q = new URLSearchParams(location.search);
  const format = q.get('f') === 'story' ? 'story' : 'feed';
  const SIZES = { feed: [1080, 1350], story: [1080, 1920] };
  const [W, H] = SIZES[format];
  const root = document.documentElement;
  root.dataset.format = format;
  root.style.setProperty('--W', W + 'px');
  root.style.setProperty('--H', H + 'px');

  let s = 20270206;
  const ART = (window.ART = {
    format, W, H, story: format === 'story',
    seed(n) { s = n; },
    rand() { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; },
    range(a, b) { return a + (b - a) * ART.rand(); },
    pick(f, st) { return format === 'story' ? st : f; },
    svg(tag, attrs, parent) {
      const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
      for (const k in attrs) el.setAttribute(k, attrs[k]);
      if (parent) parent.appendChild(el);
      return el;
    },
  });

  // Ajusta o tamanho da fonte de um elemento HTML (inline-block) ou <text> SVG para caber numa largura.
  ART.fitWidth = function (el, target) {
    for (let i = 0; i < 3; i++) {
      const isSvg = el instanceof SVGElement;
      const w = isSvg ? el.getBBox().width : el.getBoundingClientRect().width;
      const fs = parseFloat(isSvg ? el.getAttribute('font-size') : getComputedStyle(el).fontSize);
      const nfs = fs * target / w;
      if (isSvg) el.setAttribute('font-size', nfs); else el.style.fontSize = nfs + 'px';
    }
  };

  // Altura real das maiúsculas (do baseline ao topo) para posicionar coisas encostadas no texto.
  ART.capTop = function (text, font) {
    const c = document.createElement('canvas').getContext('2d');
    c.font = font;
    const m = c.measureText(text);
    return { ascent: m.actualBoundingBoxAscent, descent: m.actualBoundingBoxDescent, width: m.width,
      left: m.actualBoundingBoxLeft, right: m.actualBoundingBoxRight };
  };

  // Medição de texto (canvas) — a fonte já precisa estar carregada.
  ART.measure = function (txt, font) {
    const c = ART._ctx || (ART._ctx = document.createElement('canvas').getContext('2d'));
    c.font = font;
    return c.measureText(txt);
  };

  // Texto letra a letra (com kerning), opcionalmente esticado na vertical e com letras sobrepostas.
  // o: { text, family, weight, style, size | fit, x, y(baseline), track(em), sy, anchor, attrs }
  // Com attrs { stroke: corDoFundo, 'stroke-width': 2*gap, 'paint-order': 'stroke' } cada letra "recorta" a anterior.
  ART.knockText = function (parent, o) {
    const fam = o.family, wt = o.weight || 400, st = o.style || 'normal';
    const F = s => `${st} ${wt} ${s}px "${fam}"`;
    const chars = Array.from(o.text);
    const tr = o.track || 0;
    let s = o.size || 200;
    const met = s => {
      const full = ART.measure(o.text, F(s));
      return { full, vis: full.actualBoundingBoxLeft + full.actualBoundingBoxRight + (chars.length - 1) * tr * s };
    };
    if (o.fit) for (let i = 0; i < 3; i++) s = s * o.fit / met(s).vis;
    const { full, vis } = met(s);
    let left = o.x;
    if (o.anchor === 'middle') left = o.x - vis / 2; else if (o.anchor === 'end') left = o.x - vis;
    const x0 = left + full.actualBoundingBoxLeft;
    const g = ART.svg('g', {}, parent);
    const sy = o.sy || 1, sxk = o.sx || 1;
    if (sy !== 1 || sxk !== 1) g.setAttribute('transform', `translate(${left} ${o.y}) scale(${sxk} ${sy}) translate(${-left} ${-o.y})`);
    const els = [];
    chars.forEach((ch, i) => {
      if (ch === ' ') return;
      const upto = chars.slice(0, i + 1).join('');
      const px = ART.measure(upto, F(s)).width - ART.measure(ch, F(s)).width;
      const t = ART.svg('text', Object.assign({ x: (x0 + px + i * tr * s).toFixed(2), y: o.y, 'font-family': fam, 'font-weight': wt, 'font-style': st, 'font-size': s.toFixed(2) }, o.attrs || {}), g);
      t.textContent = ch;
      els.push(t);
    });
    const asc = full.actualBoundingBoxAscent * sy;
    return { g, els, size: s, left, right: left + vis * sxk, vis, top: o.y - asc, base: o.y, asc, desc: full.actualBoundingBoxDescent * sy };
  };

  // Homografia: leva um elemento HTML w×h (transform-origin 0 0) para um quadrilátero qualquer (perspectiva real).
  ART.quadTransform = function (w, h, p) {
    const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = p; // TL, TR, BR, BL
    const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2;
    const sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
    let g = 0, hh = 0;
    if (Math.abs(sx) > 1e-9 || Math.abs(sy) > 1e-9) {
      const det = dx1 * dy2 - dx2 * dy1;
      g = (sx * dy2 - dx2 * sy) / det;
      hh = (dx1 * sy - sx * dy1) / det;
    }
    const a = x1 - x0 + g * x1, b = x3 - x0 + hh * x3, c = x0;
    const d = y1 - y0 + g * y1, e = y3 - y0 + hh * y3, f = y0;
    const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, hh / h, 0, 0, 1, 0, c, f, 0, 1];
    return `matrix3d(${m.map(v => +v.toFixed(10)).join(',')})`;
  };

  // Grão
  ART.grain = function (parent, freq = 0.85) {
    const g = ART.svg('svg', { class: 'grain', viewBox: `0 0 ${W} ${H}` }, parent);
    const f = ART.svg('filter', { id: 'grainf', x: 0, y: 0, width: '100%', height: '100%' }, g);
    ART.svg('feTurbulence', { type: 'fractalNoise', baseFrequency: freq, numOctaves: 3, seed: 7, stitchTiles: 'stitch' }, f);
    ART.svg('feColorMatrix', { type: 'saturate', values: 0 }, f);
    ART.svg('rect', { width: W, height: H, filter: 'url(#grainf)' }, g);
  };

  // Logos: o render.js injeta window.__LOGOS = { rgnr: dataURI, ipda: dataURI } quando há arquivo em /logos.
  ART.logos = async function () {
    const L = window.__LOGOS || {};
    const tint = window.__LOGO_TINT !== false;
    const slots = document.querySelectorAll('.logo[data-logo]');
    for (const slot of slots) {
      const src = L[slot.dataset.logo];
      if (!src) { slot.classList.add('ph'); continue; }
      let ratio = 1;
      try {
        const im = new Image(); im.src = src; await im.decode();
        ratio = im.naturalWidth && im.naturalHeight ? im.naturalWidth / im.naturalHeight : 1;
      } catch (e) {}
      if (src.startsWith('data:image/svg')) {
        try {
          const txt = src.includes(';base64,') ? atob(src.split(',')[1]) : decodeURIComponent(src.split(',')[1]);
          const vb = txt.match(/viewBox\s*=\s*["']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)/i);
          if (vb) ratio = parseFloat(vb[1]) / parseFloat(vb[2]);
        } catch (e) {}
      }
      const h = parseFloat(getComputedStyle(slot).height);
      slot.textContent = '';
      const span = document.createElement('span');
      span.className = 'img' + (tint ? '' : ' color');
      span.style.setProperty('--src', `url("${src}")`);
      span.style.width = (h * ratio) + 'px';
      slot.appendChild(span);
    }
  };

  ART.ready = async function (build, fonts = []) {
    await Promise.all(fonts.map(f => document.fonts.load(f, 'SÁBADO 06 FEV ’27 AWAKEN')));
    await document.fonts.ready;
    await new Promise(r => setTimeout(r, 50));
    await build();
    await ART.logos();
    await document.fonts.ready;
    window.__ready = true;
  };
})();
