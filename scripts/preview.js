// Screenshot a built film ~3s into every scene and save a contact sheet next to it.
// Usage: node scripts/preview.js dist/<slug>/index.html   -> dist/<slug>/shots/NN.jpg
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const file = path.resolve(process.argv[2]);
  const dir = path.join(path.dirname(file), 'shots'); fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + file);
  await p.evaluate(() => { document.getElementById('gate').hidden = true; });
  const starts = await p.evaluate(() => window.FILM_T);
  let last = 0;
  for (const [i, t0] of starts.entries()) {
    const t = t0 + 3.2;
    await p.waitForTimeout((t - last) * 1000); last = t;
    await p.screenshot({ path: path.join(dir, String(i).padStart(2, '0') + '.jpg'), type: 'jpeg', quality: 70 });
  }
  await b.close();
  console.log(`✓ ${starts.length} shots in ${dir}`);
})();
