const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const sp = process.env.SP;
(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await nav.newPage({ viewport: { width: 1500, height: 950 } });
  const err = []; page.on('pageerror', e => err.push(String(e).slice(0, 130)));
  await page.goto('file://' + sp + '/crm/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(300);

  const compte = () => page.evaluate(() =>
    [...document.querySelectorAll('.abo-col')].map(c =>
      c.dataset.statut + '=' + c.querySelector('.abo-n').textContent).join('  '));

  console.log('1. colonnes au départ    :', await compte());
  console.log('   pastilles de colonne  :', await page.evaluate(() =>
    [...document.querySelectorAll('.abo-pastille')].map(p =>
      p.textContent + ' ' + getComputedStyle(p).backgroundColor).join(' | ')));

  // Pas de débordement horizontal : la carte doit contenir un e-mail très long.
  console.log('2. débordement           :', await page.evaluate(() => {
    const mauvais = [...document.querySelectorAll('.abo-fiche')]
      .filter(f => f.scrollWidth > f.clientWidth + 1)
      .map(f => f.dataset.id + ' (' + f.scrollWidth + '>' + f.clientWidth + ')');
    return mauvais.length ? mauvais.join(', ') : 'aucun';
  }));
  console.log('   page                  :', await page.evaluate(() =>
    document.documentElement.scrollWidth <= window.innerWidth ? 'aucun' : 'déborde'));

  // Le style de l'admin WordPress ne doit rien écraser sur les cartes.
  console.log('3. carte 104 (nom long)  :', await page.evaluate(() => {
    const h = document.querySelector('.abo-fiche[data-id="104"] h3');
    const a = document.querySelector('.abo-fiche[data-id="104"] .abo-ava');
    return 'h3 ' + Math.round(h.getBoundingClientRect().width) + 'px, ellipse '
      + getComputedStyle(h).textOverflow + ' | pastille '
      + Math.round(a.getBoundingClientRect().width) + '×' + Math.round(a.getBoundingClientRect().height);
  }));
  console.log('   compteur de notes     :', await page.evaluate(() =>
    document.querySelector('.abo-fiche[data-id="104"] .abo-cpt').textContent.trim()));
  console.log('   lignes de la carte    :', await page.evaluate(() =>
    [...document.querySelectorAll('.abo-fiche[data-id="104"] .abo-ligne')]
      .map(l => l.textContent.replace(/\s+/g, ' ').trim()).join(' / ')));

  await page.evaluate(() => {
    const fiche = document.querySelector('.abo-fiche[data-id="101"]');
    const cible = document.querySelector('.abo-pile[data-statut="en_cours"]');
    const dt = new DataTransfer();
    fiche.dispatchEvent(new DragEvent('dragstart', { bubbles: true, dataTransfer: dt }));
    cible.dispatchEvent(new DragEvent('dragover', { bubbles: true, dataTransfer: dt }));
    cible.dispatchEvent(new DragEvent('drop', { bubbles: true, dataTransfer: dt }));
    fiche.dispatchEvent(new DragEvent('dragend', { bubbles: true, dataTransfer: dt }));
  });
  await page.waitForTimeout(250);
  console.log('4. après glisser-déposer :', await compte());
  console.log('   la fiche 101 est dans :', await page.evaluate(() =>
    document.querySelector('.abo-fiche[data-id="101"]').parentElement.dataset.statut));
  console.log('   appel serveur         :', await page.evaluate(() => window.__appels.join(' · ')));

  await page.click('.abo-fiche[data-id="103"]');
  await page.waitForTimeout(250);
  console.log('5. tiroir ouvert         :', await page.evaluate(() => !document.getElementById('abo-tiroir').hidden));
  console.log('   entête                :', await page.evaluate(() => {
    const t = document.querySelector('.abo-fiche-tete');
    const m = document.querySelector('.abo-fiche-meta');
    return (t.querySelector('.abo-ava') ? 'pastille ' : 'sans pastille ')
      + (m.querySelector('.abo-tag') ? '+ étiquette ' : '+ SANS étiquette ')
      + '| ' + t.querySelector('h2').textContent.trim() + ' | ' + m.textContent.trim();
  }));
  console.log('   champs affichés       :', await page.evaluate(() => document.querySelectorAll('.abo-fiche-champs dt').length));
  console.log('   bouton Répondre       :', await page.evaluate(() => {
    const b = document.querySelector('.abo-fiche-actions .button-primary');
    return b ? b.textContent.trim() : 'absent';
  }));
  console.log('   journal existant      :', await page.evaluate(() => document.querySelectorAll('.abo-journal-ligne').length), 'ligne(s)');

  await page.fill('.abo-note textarea', 'Relancé par téléphone.');
  await page.click('.abo-note button');
  await page.waitForTimeout(250);
  console.log('6. note ajoutée          :', await page.evaluate(() => document.querySelectorAll('.abo-journal-ligne').length), 'ligne(s)');

  await page.selectOption('.abo-fiche-statut select', 'archivee');
  await page.waitForTimeout(250);
  console.log('7. via le sélecteur      :', await compte());

  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  console.log('8. Échap ferme           :', await page.evaluate(() => document.getElementById('abo-tiroir').hidden));

  // Ouverture au clavier : les cartes sont focalisables.
  await page.focus('.abo-fiche[data-id="102"]');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(250);
  console.log('9. ouverture au clavier  :', await page.evaluate(() => !document.getElementById('abo-tiroir').hidden));
  await page.screenshot({ path: sp + '/crm/fiche.png' });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);

  console.log('   erreurs JS            :', err.length ? err : 'aucune');
  await page.screenshot({ path: sp + '/crm/kanban.png' });
  await nav.close();
})();
