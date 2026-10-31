// Usage: node shot.js input.html output.png width height [transparent=1]
const { chromium } = require('playwright');
(async () => {
  const [,, inp, out, w, h, transp] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  await page.goto('file://' + require('path').resolve(inp));
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.waitForTimeout(150);
  await page.screenshot({ path: out, omitBackground: transp === '1', clip: { x: 0, y: 0, width: +w, height: +h } });
  await browser.close();
})();
