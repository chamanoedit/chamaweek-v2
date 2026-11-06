// Gera as artes do WKND '27 em PNG (Feed 1080x1350 e Story 1080x1920) + folhas de visão geral.
// Uso:  node render.js            (todas)
//       node render.js 07 story   (filtra por número e/ou formato; aceita vários números)
// Logos: coloque rgnr.svg|png e ipda.svg|png em ./logos e rode de novo — o texto provisório é trocado pelo logo.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const CONCEPTS = ['01-horizonte', '02-sol', '03-verao', '04-luz',
  '05-granulado', '06-escada', '07-desfoque', '08-jornal', '09-gigante', '10-telao'];
const SHEETS = { 'wknd27-visao-geral.jpg': CONCEPTS.slice(0, 4), 'wknd27-visao-geral-referencias.jpg': CONCEPTS.slice(4) };
const FORMATS = { feed: [1080, 1350], story: [1080, 1920] };
const args = process.argv.slice(2);
const pickC = args.filter(a => /^\d\d$/.test(a));
const pickF = args.filter(a => FORMATS[a]);

function logo(name) {
  for (const ext of ['svg', 'png', 'webp', 'jpg', 'jpeg']) {
    const p = path.join(ROOT, 'logos', `${name}.${ext}`);
    if (fs.existsSync(p)) {
      const mime = ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' ? 'image/jpeg' : `image/${ext}`;
      return `data:${mime};base64,${fs.readFileSync(p).toString('base64')}`;
    }
  }
  return null;
}

(async () => {
  const logos = { rgnr: logo('rgnr'), ipda: logo('ipda') };
  const tint = !fs.existsSync(path.join(ROOT, 'logos', 'manter-cores'));
  console.log('logos:', Object.fromEntries(Object.entries(logos).map(([k, v]) => [k, v ? 'arquivo' : 'provisório'])));
  const browser = await chromium.launch();
  const outDir = path.join(ROOT, 'export');
  fs.mkdirSync(outDir, { recursive: true });
  for (const c of CONCEPTS) {
    if (pickC.length && !pickC.includes(c.slice(0, 2))) continue;
    if (!fs.existsSync(path.join(ROOT, 'src', c + '.html'))) continue;
    for (const [f, [w, h]] of Object.entries(FORMATS)) {
      if (pickF.length && !pickF.includes(f)) continue;
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
      page.on('pageerror', e => console.error(`[${c}/${f}]`, e.message));
      await page.addInitScript(([l, t]) => { window.__LOGOS = l; window.__LOGO_TINT = t; }, [logos, tint]);
      await page.goto(`file://${path.join(ROOT, 'src', c + '.html')}?f=${f}`);
      await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
      await page.waitForTimeout(400);
      const out = path.join(outDir, `wknd27-${c}-${f}.png`);
      await page.screenshot({ path: out, type: 'png' });
      await page.close();
      console.log('ok', path.relative(ROOT, out));
    }
  }

  // Folhas de visão geral (opções lado a lado) — só quando renderiza tudo.
  if (!pickC.length && !pickF.length) {
    for (const [name, list] of Object.entries(SHEETS)) {
      const rows = list.map(c => `
        <div class="row"><div class="n">${c.slice(0, 2)}</div>
          <img src="wknd27-${c}-feed.png" style="height:675px">
          <img src="wknd27-${c}-story.png" style="height:675px">
        </div>`).join('');
      const html = `<html><body style="margin:0;background:#141010">
        <style>.wrap{display:grid;grid-template-columns:1fr 1fr;gap:56px;padding:64px;width:max-content}.row{display:flex;gap:20px;align-items:flex-start}
        .n{color:#f2e6da;font:700 40px/1 sans-serif;width:56px;opacity:.8}img{border-radius:10px;display:block}</style>
        <div class="wrap">${rows}</div></body></html>`;
      const tmp = path.join(outDir, '_folha.html');
      fs.writeFileSync(tmp, html);
      const page = await browser.newPage({ viewport: { width: 2220, height: 800 }, deviceScaleFactor: 1 });
      await page.goto('file://' + tmp, { waitUntil: 'load' });
      const out = path.join(outDir, name);
      await page.screenshot({ path: out, fullPage: true, type: 'jpeg', quality: 88 });
      await page.close();
      fs.unlinkSync(tmp);
      console.log('ok', path.relative(ROOT, out));
    }
  }
  await browser.close();
})();
