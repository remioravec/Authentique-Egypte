#!/usr/bin/env node
/*
  Captures d'écran d'une page, images comprises.

  Le navigateur de contrôle rend les pages HORS LIGNE : c'est voulu pour
  les mesures, mais on ne voit alors pas les photos. Ici on sert les
  images depuis un cache local (/tmp/imgcache, rempli une fois par
  curl) : le rendu est complet, sans dépendre du réseau à chaque essai.

  usage : node outils/verif/apercu.js <page.html> [prefixe] [0,0.4,0.75]
*/
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const path = require('path'); const crypto = require('crypto');

const fichier = process.argv[2];
const prefixe = process.argv[3] || '/tmp/apercu';
const fractions = (process.argv[4] || '0,0.42,0.72').split(',').map(Number);
const CACHE = '/tmp/imgcache';

const local = u => {
  const nom = crypto.createHash('md5').update(u).digest('hex') + path.extname(new URL(u).pathname);
  const p = path.join(CACHE, nom);
  return fs.existsSync(p) ? p : null;
};
const type = p => ({ '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.webp': 'image/webp', '.avif': 'image/avif' })[path.extname(p).toLowerCase()] || 'image/jpeg';

(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await nav.newContext({ viewport: { width: 1360, height: 900 } });
  await ctx.route(/^https?:/, route => {
    const u = route.request().url();
    const p = /\.(jpe?g|png|webp|avif)($|\?)/i.test(u) ? local(u.split('?')[0]) : null;
    if (p) return route.fulfill({ status: 200, contentType: type(p), body: fs.readFileSync(p) });
    return route.abort();          // polices et scripts tiers : coupés, comme les autres contrôles
  });

  for (const [nom, l, h] of [['bureau', 1360, 900], ['mobile', 390, 844]]) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: l, height: h });
    await page.goto('file://' + path.resolve(fichier), { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => { document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; }); });
    await page.waitForTimeout(2500);
    const casses = await page.evaluate(() =>
      [...document.images].filter(i => !i.naturalWidth).map(i => i.currentSrc || i.src));
    const etapes = ['haut', 'milieu', 'bas', 'q4', 'q5'];
    for (let k = 0; k < fractions.length; k++) {
      await page.evaluate(y => window.scrollTo(0, document.body.scrollHeight * y), fractions[k]);
      await page.waitForTimeout(700);
      await page.screenshot({ path: `${prefixe}-${nom}-${etapes[k]}.png` });
    }
    console.log(`${nom} · ${casses.length} image(s) non rendue(s)` + (casses.length ? ' : ' + casses.slice(0, 4).join(' ') : ''));
    await page.close();
  }
  await nav.close();
})();
