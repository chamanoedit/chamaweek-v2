// Monta o PSD editável do "Culto RGNR — Fim do Mundo" (1080x1350) a partir da reconstrução em src/.
// Camadas: textos editáveis (Anton e Inter Tight), textura do título em máscara de recorte,
// logo regenere e o fundo com os textos removidos.
// Uso:  npm i ag-psd pngjs playwright   (uma vez)  →  node psd.js
const { chromium } = require('playwright');
const { writePsdBuffer } = require('ag-psd');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const hex = h => ({ r: parseInt(h.slice(1, 3), 16), g: parseInt(h.slice(3, 5), 16), b: parseInt(h.slice(5, 7), 16) });

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

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error(e.message));
  await page.goto(`file://${path.join(ROOT, 'src', 'fim-do-mundo.html')}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  await page.waitForTimeout(500);
  const composite = await page.screenshot({ type: 'png' });
  fs.writeFileSync(path.join(ROOT, 'export', 'fim-do-mundo.png'), composite);
  const P = await page.evaluate(() => window.__PSD);

  const shoot = async (id, name, extra = {}) => {
    await page.evaluate(id => {
      document.documentElement.classList.add('iso');
      document.querySelectorAll('[data-layer]').forEach(e => { e.style.visibility = e.dataset.layer === id ? 'visible' : 'hidden'; });
    }, id);
    const c = cropPng(await page.screenshot({ omitBackground: true, type: 'png' }));
    return Object.assign({ name }, c || {}, extra);
  };

  const textLayer = async (b) => {
    const lay = await shoot(b.id + '-texto', b.name);
    const style = (tr) => ({ font: { name: b.font }, fontSize: b.size, fillColor: hex(b.color), horizontalScale: b.hscale, tracking: tr,
      autoKerning: true, autoLeading: b.lines.length === 1, leading: b.leading || undefined });
    const text = b.lines.map(l => l.text).join('\n');
    lay.text = {
      text,
      transform: [1, 0, 0, 1, b.anchor, b.base0],
      antiAlias: 'smooth',
      style: style(b.lines[0].tracking),
      styleRuns: b.lines.map((l, i) => ({ length: [...l.text].length + (i < b.lines.length - 1 ? 1 : 0), style: style(l.tracking) })),
      paragraphStyle: { justification: b.align },
    };
    return lay;
  };

  const B = Object.fromEntries(P.blocks.map(b => [b.id, b]));
  const textura = async () => shoot('textura', 'Textura (máscara de recorte)', { clipping: true });
  const titulo = { name: 'TÍTULO', opened: true, children: [
    await textura(), await textLayer(B.culto),
    await textura(), await textLayer(B.titulo),
  ] };
  const infos = { name: 'INFORMAÇÕES', opened: true, children: [
    await textLayer(B.data), await textLayer(B.hora), await textLayer(B.endereco), await textLayer(B.transfer),
  ] };
  const logo = await shoot('logo', 'Logo regenere (trocar pelo arquivo original)');
  const fundo = await shoot('fundo', 'Fundo — Terra (textos removidos)');

  const psd = {
    width: P.W, height: P.H,
    imageResources: { resolutionInfo: { horizontalResolution: 72, horizontalResolutionUnit: 'PPI', widthUnit: 'Inches', verticalResolution: 72, verticalResolutionUnit: 'PPI', heightUnit: 'Inches' } },
    imageData: fullPng(composite),
    children: [infos, titulo, logo, fundo], // de cima para baixo, como no painel de camadas
  };
  // o ag-psd grava cada lista de baixo para cima: inverte a árvore montada de cima para baixo
  const bottomUp = ls => ls.map(l => (l.children ? { ...l, children: bottomUp(l.children) } : l)).reverse();
  psd.children = bottomUp(psd.children);
  const out = path.join(ROOT, 'export', 'culto-rgnr-fim-do-mundo.psd');
  fs.writeFileSync(out, writePsdBuffer(psd, { generateThumbnail: false }));
  console.log('ok', path.relative(ROOT, out), (fs.statSync(out).size / 1e6).toFixed(1) + ' MB');
  for (const b of P.blocks) console.log(' ', b.name.padEnd(13), b.font, b.size.toFixed(1) + 'px', 'escala', b.hscale, 'track', b.lines.map(l => l.tracking).join('/'));
  await browser.close();
})();
