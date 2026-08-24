const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const sp = process.env.SP;
(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  for (const [nom, w, h] of [['écran 1280', 1280, 900], ['tablette 900', 900, 1200], ['téléphone 390', 390, 900]]) {
    const page = await nav.newPage({ viewport: { width: w, height: h } });
    await page.goto('file://' + sp + '/crm/index.html', { waitUntil: 'load' });
    await page.waitForTimeout(200);
    const r = await page.evaluate(() => {
      const k = document.getElementById('abo-kanban');
      return {
        cols: getComputedStyle(k).gridTemplateColumns,
        defileTableau: k.scrollWidth > k.clientWidth,
        defilePage: document.documentElement.scrollWidth > window.innerWidth,
        carte: Math.round(document.querySelector('.abo-fiche').getBoundingClientRect().width),
        coupe: [...document.querySelectorAll('.abo-fiche')].filter(f => f.scrollWidth > f.clientWidth + 1).length,
      };
    });
    console.log(nom.padEnd(14), 'colonnes', r.cols.split(' ').length,
      '| tableau défile', r.defileTableau, '| page déborde', r.defilePage,
      '| carte', r.carte + 'px | cartes coupées', r.coupe);
    await page.screenshot({ path: sp + '/crm/l-' + w + '.png' });
    await page.close();
  }
  await nav.close();
})();
