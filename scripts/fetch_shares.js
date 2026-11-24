// Download Gemini-generated assets from public Gemini share links with a real browser.
// films/<slug>/assets/shares.json: {"guide": "https://share.gemini.google/XXXX", ..., "bgm": "https://share.gemini.google/YYYY"}
// Usage: node scripts/fetch_shares.js films/<slug>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

(async () => {
  const dir = path.join(process.argv[2], 'assets');
  const shares = JSON.parse(fs.readFileSync(path.join(dir, 'shares.json'), 'utf8'));
  const browser = await chromium.launch();
  let ok = true;
  for (const [key, url] of Object.entries(shares)) {
    const ctx = await browser.newContext({ locale: 'ko-KR', viewport: { width: 1400, height: 1000 } });
    const page = await ctx.newPage();
    const got = [];
    page.on('response', async (r) => {
      try {
        const ct = (r.headers()['content-type'] || '').split(';')[0];
        if (!/^(image|audio|video)\//.test(ct) || ct === 'image/svg+xml') return;
        const body = await r.body();
        got.push({ ct, body, url: r.url().slice(0, 80) });
      } catch (e) {}
    });
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
    } catch (e) { console.log(key, 'goto:', e.message.slice(0, 80)); }
    await page.waitForTimeout(4000);
    if (key === 'bgm') {
      // start playback so the audio file is requested
      for (const sel of ['button[aria-label*="재생"]', 'button[aria-label*="Play"]', 'button[aria-label*="play"]']) {
        const b = await page.$(sel); if (b) { try { await b.click(); } catch (e) {} break; }
      }
      await page.waitForTimeout(6000);
      const src = await page.evaluate(() => [...document.querySelectorAll('audio,video,source')].map(a => a.currentSrc || a.src).filter(s => s && !s.startsWith('blob:'))[0] || null);
      if (src) { try { const r = await page.request.get(src); got.push({ ct: r.headers()['content-type'] || 'audio/mpeg', body: await r.body(), url: src.slice(0, 80) }); } catch (e) {} }
      const audio = got.filter(g => /^(audio|video)\//.test(g.ct)).sort((a, b) => b.body.length - a.body.length)[0];
      if (audio && audio.body.length > 100000) {
        fs.writeFileSync(path.join(dir, 'bgm.mp3'), audio.body);
        console.log(`✓ bgm ${audio.body.length} bytes ${audio.ct} ${audio.url}`);
      } else { ok = false; console.log('✗ bgm: no audio;', got.map(g => g.ct + ' ' + g.body.length).slice(0, 10)); }
    } else {
      const imgs = got.filter(g => g.ct.startsWith('image/') && g.body.length > 50000).sort((a, b) => b.body.length - a.body.length);
      if (imgs.length) {
        fs.writeFileSync(path.join(dir, key + '.png'), imgs[0].body);
        console.log(`✓ ${key} ${imgs[0].body.length} bytes ${imgs[0].ct} ${imgs[0].url}`);
      } else { ok = false; console.log(`✗ ${key}: no image;`, got.map(g => g.ct + ' ' + g.body.length).slice(0, 10)); }
    }
    await ctx.close();
  }
  await browser.close();
  process.exit(ok ? 0 : 1);
})();
