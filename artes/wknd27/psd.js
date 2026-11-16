// Exporta a 06 Escada como PSD editável (Feed 1080x1350 e Story 1080x1920).
// Camadas: fundo (cor editável), texturas, sombra, cada degrau em grupo próprio com
// texto editável + formas vetoriais (frente, topo em degradê, lateral), textos do topo e logos.
// Uso:  npm i ag-psd pngjs playwright   (uma vez)  →  node psd.js
const { chromium } = require('playwright');
const { writePsdBuffer } = require('ag-psd');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const FORMATS = { feed: [1080, 1350], story: [1080, 1920] };
const FONT_PS = { // nomes PostScript (Google Fonts: Archivo e Inter Tight)
  'Archivo/900': 'Archivo-ExpandedBlack',
  'Inter Tight/600': 'InterTight-SemiBold',
  'Inter Tight/800': 'InterTight-ExtraBold',
};

const hex = h => ({ r: parseInt(h.slice(1, 3), 16), g: parseInt(h.slice(3, 5), 16), b: parseInt(h.slice(5, 7), 16) });
const rgb = s => { const m = s.match(/[\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2] }; };

// PNG com transparência → recorte no que tem pixel (camada com left/top)
function cropPng(buf) {
  const png = PNG.sync.read(buf);
  const { width: w, height: h, data } = png;
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (data[(y * w + x) * 4 + 3]) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 < 0) return null;
  const cw = x1 - x0 + 1, ch = y1 - y0 + 1, out = new Uint8ClampedArray(cw * ch * 4);
  for (let y = 0; y < ch; y++) out.set(data.subarray(((y0 + y) * w + x0) * 4, ((y0 + y) * w + x1 + 1) * 4), y * cw * 4);
  return { left: x0, top: y0, imageData: { width: cw, height: ch, data: out } };
}
const fullPng = buf => { const p = PNG.sync.read(buf); return { width: p.width, height: p.height, data: new Uint8ClampedArray(p.data) }; };
const quadPath = pts => ({ paths: [{ open: false, operation: 'combine', fillRule: 'non-zero', knots: pts.map(([x, y]) => ({ linked: false, points: [x, y, x, y, x, y] })) }] });
const rectPath = (x, y, w, h) => quadPath([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]);

async function shoot(page, id, mode) {
  await page.evaluate(([id, mode]) => {
    document.documentElement.classList.add('iso');
    document.querySelectorAll('[data-layer]').forEach(e => {
      const on = e.dataset.layer === id;
      e.style.visibility = on ? 'visible' : 'hidden';
      if (on) e.style.removeProperty('opacity'); else e.style.setProperty('opacity', '0', 'important'); // o grão (feTurbulence) ignora visibility
      e.classList.remove('notext', 'textonly');
    });
    if (mode) document.querySelector(`[data-layer="${id}"]`).classList.add(mode);
  }, [id, mode]);
  return page.screenshot({ omitBackground: true, type: 'png' });
}

(async () => {
  const browser = await chromium.launch();
  for (const [f, [W, H]] of Object.entries(FORMATS)) {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    page.on('pageerror', e => console.error(`[${f}]`, e.message));
    await page.goto(`file://${path.join(ROOT, 'src', '06-escada.html')}?f=${f}&psd=1`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    await page.waitForTimeout(400);
    const composite = fullPng(await page.screenshot({ type: 'png' }));

    // textos pequenos e logos: posição da linha de base, fonte, cor e espaçamento
    const info = await page.evaluate(() => {
      const ctx = document.createElement('canvas').getContext('2d');
      const texts = ['m-evento', 'm-salve', 'm-data', 'm-dia', 'm-pontos', 'm-ponto', 'logo-rgnr', 'logo-ipda'].map(id => {
        const el = document.querySelector(`[data-layer="${id}"]`), cs = getComputedStyle(el);
        const range = document.createRange(); range.selectNodeContents(el);
        const r = range.getBoundingClientRect();
        const fam = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
        ctx.font = `${cs.fontWeight} ${cs.fontSize} "${fam}"`;
        const raw = el.textContent;
        const text = cs.textTransform === 'uppercase' ? raw.toUpperCase() : raw;
        const ls = cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing);
        return { id, text, fam, weight: +cs.fontWeight, size: parseFloat(cs.fontSize), ls, color: cs.color,
          x: r.left, y: r.top + ctx.measureText(text).fontBoundingBoxAscent };
      });
      const rects = Object.fromEntries(['m-linha', 'logo-sep'].map(id => {
        const el = document.querySelector(`[data-layer="${id}"]`), r = el.getBoundingClientRect(), cs = getComputedStyle(el);
        return [id, { x: r.left, y: r.top, w: r.width, h: r.height, color: cs.backgroundColor, opacity: +cs.opacity }];
      }));
      return { psd: window.__PSD, texts, rects };
    });
    const P = info.psd;

    const raster = async (id, name, extra = {}, mode) => {
      const c = cropPng(await shoot(page, id, mode));
      return c ? Object.assign({ name }, c, extra) : null;
    };
    const textLayer = async (t, name, layerId, mode) => {
      const key = `${t.fam}/${t.weight}`;
      const lay = await raster(layerId, name, {}, mode);
      return Object.assign(lay || { name }, {
        name,
        text: {
          text: t.text,
          transform: t.transform || [1, 0, 0, 1, t.x, t.y],
          antiAlias: 'smooth',
          style: { font: { name: FONT_PS[key] || key }, fontSize: t.size, fillColor: rgb(t.color), tracking: Math.round(t.tracking ?? (t.ls / t.size * 1000)), autoKerning: true },
          paragraphStyle: { justification: 'left' },
        },
      });
    };

    // --- escada: um grupo por degrau, do mais próximo (topo da pilha) ao mais distante
    const N = P.steps.length, steps = [];
    for (let i = 0; i < N; i++) {
      const children = [];
      const tx = P.texts.find(t => t.i === i);
      if (tx) children.push(await textLayer({ ...tx, fam: 'Archivo', weight: 900, size: tx.fontSize, color: 'rgb(255,255,255)' }, 'Texto (editável)', tx.face, 'textonly'));
      for (const face of P.faces.filter(x => x.i === i)) {
        const label = { front: 'Frente', top: 'Topo (degradê)', left: 'Lateral', bottom: 'Base', right: 'Lateral (ponta)' }[face.kind];
        const lay = await raster(face.id, label, {}, face.kind === 'front' ? 'notext' : undefined);
        if (!lay) continue;
        lay.vectorMask = quadPath(face.pts);
        if (face.grad) {
          const [a, b] = face.grad;
          const ang = Math.atan2(-(face.to[1] - face.from[1]), face.to[0] - face.from[0]) * 180 / Math.PI;
          lay.vectorFill = { type: 'solid', name: 'Degradê do degrau', style: 'linear', angle: ang, scale: 1, align: true,
            colorStops: [{ color: hex(a), location: 0, midpoint: 0.5 }, { color: hex(b), location: 1, midpoint: 0.5 }],
            opacityStops: [{ opacity: 1, location: 0, midpoint: 0.5 }, { opacity: 1, location: 1, midpoint: 0.5 }] };
        } else lay.vectorFill = { type: 'color', color: hex(face.fill) };
        children.push(lay);
      }
      steps.push({ name: `${N - i} · ${P.steps[i].toUpperCase()}`, opened: false, children });
    }

    // --- textos do topo
    const T = Object.fromEntries(info.texts.map(t => [t.id, t]));
    const line = info.rects['m-linha'];
    const topo = [
      await textLayer(T['m-evento'], 'RGNR WEEKEND ’27', 'm-evento'),
      await textLayer(T['m-salve'], 'SALVE ESSA DATA!', 'm-salve'),
      await textLayer(T['m-data'], '06 FEV', 'm-data'),
      Object.assign(await raster('m-linha', 'Linha'), { vectorMask: rectPath(line.x, line.y, line.w, line.h), vectorFill: { type: 'color', color: rgb(line.color) } }),
      await textLayer(T['m-dia'], 'SÁBADO', 'm-dia'),
      await textLayer(T['m-pontos'], 'Pontos ••', 'm-pontos'),
      await textLayer(T['m-ponto'], 'Ponto •', 'm-ponto'),
    ];
    // --- logos (provisórios)
    const sep = info.rects['logo-sep'];
    const logos = [
      await textLayer(T['logo-rgnr'], 'RGNR (trocar pelo logo)', 'logo-rgnr'),
      Object.assign(await raster('logo-sep', 'Divisória'), { opacity: sep.opacity, vectorMask: rectPath(sep.x, sep.y, sep.w, sep.h), vectorFill: { type: 'color', color: rgb(sep.color) } }),
      await textLayer(T['logo-ipda'], 'IPDA (trocar pelo logo)', 'logo-ipda'),
    ];
    // --- fundo, texturas e sombra
    const sombra = await raster('sombra', 'Sombra da escada', { opacity: 0.2 });
    for (let k = 0; k < sombra.imageData.data.length; k += 4) { sombra.imageData.data[k] = 60; sombra.imageData.data[k + 1] = 25; sombra.imageData.data[k + 2] = 10; }
    const grao = await raster('granulado', 'Granulado', { blendMode: 'overlay', opacity: 0.22 });
    const pont = await raster('pontilhado', 'Pontilhado');
    const luz = await raster('luz', 'Luz');
    const bgc = hex(P.bg), bgData = new Uint8ClampedArray(W * H * 4);
    for (let k = 0; k < bgData.length; k += 4) { bgData[k] = bgc.r; bgData[k + 1] = bgc.g; bgData[k + 2] = bgc.b; bgData[k + 3] = 255; }

    const psd = {
      width: W, height: H,
      imageResources: { resolutionInfo: { horizontalResolution: 72, horizontalResolutionUnit: 'PPI', widthUnit: 'Inches', verticalResolution: 72, verticalResolutionUnit: 'PPI', heightUnit: 'Inches' } },
      imageData: composite,
      children: [ // de cima para baixo, como no painel de camadas
        grao,
        { name: 'LOGOS (provisórios — trocar pelos oficiais)', opened: true, children: logos },
        { name: 'TEXTOS DO TOPO', opened: true, children: topo },
        { name: 'ESCADA (de cima para baixo: 1 a 6)', opened: true, children: steps },
        sombra,
        { name: 'FUNDO', opened: false, children: [luz, pont, { name: 'Cor de fundo', left: 0, top: 0, imageData: { width: W, height: H, data: bgData }, vectorFill: { type: 'color', color: bgc } }] },
      ],
    };
    // o ag-psd grava cada lista de baixo para cima: inverte a árvore montada de cima para baixo
    const bottomUp = ls => ls.map(l => (l.children ? { ...l, children: bottomUp(l.children) } : l)).reverse();
    psd.children = bottomUp(psd.children);
    const out = path.join(ROOT, 'export', `wknd27-06-escada-${f}.psd`);
    fs.writeFileSync(out, writePsdBuffer(psd, { generateThumbnail: false }));
    console.log('ok', path.relative(ROOT, out), (fs.statSync(out).size / 1e6).toFixed(1) + ' MB');
    await page.close();
  }
  await browser.close();
})();
