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
