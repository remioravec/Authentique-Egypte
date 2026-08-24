const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const sp = process.env.SP;
let rate = 0;
const dire = (t, ok, detail) => {
  if (!ok) { rate++; }
  console.log((ok ? '  ✓ ' : '  ✗ ') + t + (detail !== undefined ? ' : ' + detail : ''));
};
(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await nav.newPage({ viewport: { width: 1500, height: 950 } });

  const err = []; page.on('pageerror', e => err.push(String(e).slice(0, 160)));
  // Une alerte est un échec : c'est ainsi qu'une erreur avalée par un
  // .catch() se manifeste à la cliente, et le test la manquait.
  const dialogues = [];
  page.on('dialog', async d => { dialogues.push(d.type() + ' « ' + d.message() + ' »'); await d.dismiss(); });

  await page.goto('file://' + sp + '/crm/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(300);

  const compte = () => page.evaluate(() =>
    [...document.querySelectorAll('.crm-col')].map(c =>
      c.dataset.statut + '=' + c.querySelector('.crm-n').textContent).join('  '));

  console.log('\n── Chargement ──');
  dire('la feuille de style est appliquée', await page.evaluate(() =>
    getComputedStyle(document.querySelector('.crm-panne')).display === 'none'));
  dire('le bandeau de panne est masqué', await page.evaluate(() =>
    document.querySelector('.crm-panne').offsetParent === null));
  dire('quatre colonnes côte à côte', await page.evaluate(() =>
    getComputedStyle(document.getElementById('crm-tableau')).gridTemplateColumns.split(' ').length === 4),
    await page.evaluate(() => getComputedStyle(document.getElementById('crm-tableau')).gridTemplateColumns));
  dire('les colonnes sont comptées', (await compte()) === 'nouvelle=2  en_cours=2  traitee=2  archivee=1', await compte());

  console.log('\n── Résistance aux styles de l’admin WordPress ──');
  const carte = await page.evaluate(() => {
    const c = document.querySelector('.crm-carte[data-id="104"]');
    const h = c.querySelector('h3'), a = c.querySelector('.crm-ava');
    const cs = getComputedStyle(h), as = getComputedStyle(a);
    return {
      fond: getComputedStyle(c).backgroundColor,
      rayon: getComputedStyle(c).borderRadius,
      taille: cs.fontSize, gras: cs.fontWeight, casse: cs.textTransform,
      coupe: cs.textOverflow,
      ava: Math.round(a.getBoundingClientRect().width) + '×' + Math.round(a.getBoundingClientRect().height),
      avaFond: as.backgroundColor,
      largeur: Math.round(c.getBoundingClientRect().width),
    };
  });
  dire('carte blanche à coins arrondis', carte.fond === 'rgb(255, 255, 255)' && carte.rayon === '10px', carte.fond + ' r' + carte.rayon);
  dire('titre 15px semi-gras, non capitalisé', carte.taille === '15px' && carte.gras === '600' && carte.casse === 'none',
    carte.taille + ' / ' + carte.gras + ' / ' + carte.casse);
  dire('titre coupé par des points de suspension', carte.coupe === 'ellipsis');
  dire('pastille 30×30 teintée', carte.ava === '30×30' && carte.avaFond !== 'rgba(0, 0, 0, 0)', carte.ava + ' ' + carte.avaFond);

  const deborde = await page.evaluate(() => ({
    cartes: [...document.querySelectorAll('.crm-carte')].filter(f => f.scrollWidth > f.clientWidth + 1).length,
    page: document.documentElement.scrollWidth > window.innerWidth,
  }));
  dire('aucune carte ne déborde', deborde.cartes === 0);
  dire('la page ne déborde pas', !deborde.page);

  console.log('\n── Glisser-déposer ──');
  await page.evaluate(() => {
    const c = document.querySelector('.crm-carte[data-id="101"]');
    const cible = document.querySelector('.crm-pile[data-statut="en_cours"]');
    const dt = new DataTransfer();
    c.dispatchEvent(new DragEvent('dragstart', { bubbles: true, dataTransfer: dt }));
    cible.dispatchEvent(new DragEvent('dragover', { bubbles: true, dataTransfer: dt }));
    cible.dispatchEvent(new DragEvent('drop', { bubbles: true, dataTransfer: dt }));
    c.dispatchEvent(new DragEvent('dragend', { bubbles: true, dataTransfer: dt }));
  });
  await page.waitForTimeout(250);
  dire('la carte a changé de colonne', await page.evaluate(() =>
    document.querySelector('.crm-carte[data-id="101"]').parentElement.dataset.statut === 'en_cours'));
  dire('les compteurs suivent', (await compte()) === 'nouvelle=1  en_cours=3  traitee=2  archivee=1', await compte());
  dire('le serveur est prévenu', await page.evaluate(() =>
    window.__appels.join('') === 'aecrm_deplacer:101→en_cours'), await page.evaluate(() => window.__appels.join(' · ')));

  console.log('\n── Fiche client ──');
  await page.click('.crm-carte[data-id="103"]');
  await page.waitForTimeout(250);
  dire('le tiroir s’ouvre au clic', await page.evaluate(() => !document.getElementById('crm-tiroir').hidden));
  dire('pastille + nom + étiquette', await page.evaluate(() =>
    !!document.querySelector('.crm-tete .crm-ava') && !!document.querySelector('.crm-meta .crm-tag')),
    await page.textContent('.crm-tete h2'));
  dire('les champs sont listés', await page.evaluate(() => document.querySelectorAll('.crm-champs dt').length === 1));
  dire('bouton Répondre présent', await page.evaluate(() =>
    !!document.querySelector('.crm-actions .button-primary')));
  dire('lien Supprimer avec jeton', await page.evaluate(() => {
    const a = document.querySelector('.crm-suppr');
    return !!a && a.href.indexOf('demande=103') > -1 && a.href.indexOf('_wpnonce=') > -1;
  }), await page.evaluate(() => (document.querySelector('.crm-suppr') || {}).href));
  dire('journal existant affiché', await page.evaluate(() => document.querySelectorAll('.crm-journal-ligne').length === 1));

  console.log('\n── Note de suivi ──');
  const cptAvant = await page.evaluate(() =>
    document.querySelector('.crm-carte[data-id="103"] .crm-cpt-n').textContent);
  await page.fill('.crm-note textarea', 'Relancé par téléphone.');
  await page.click('.crm-note button');
  await page.waitForTimeout(300);
  dire('la note est ajoutée au journal', await page.evaluate(() =>
    document.querySelectorAll('.crm-journal-ligne').length === 2));
  dire('le compteur de la carte est à jour', await page.evaluate(() =>
    document.querySelector('.crm-carte[data-id="103"] .crm-cpt-n').textContent === '2'),
    cptAvant + ' → ' + await page.evaluate(() =>
      document.querySelector('.crm-carte[data-id="103"] .crm-cpt-n').textContent));

  console.log('\n── Sélecteur de colonne et fermeture ──');
  await page.selectOption('.crm-statut select', 'archivee');
  await page.waitForTimeout(250);
  dire('la carte suit le sélecteur', (await compte()) === 'nouvelle=1  en_cours=2  traitee=2  archivee=2', await compte());
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  dire('Échap referme', await page.evaluate(() => document.getElementById('crm-tiroir').hidden));

  await page.focus('.crm-carte[data-id="102"]');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(250);
  dire('Entrée ouvre la fiche', await page.evaluate(() => !document.getElementById('crm-tiroir').hidden));
  await page.screenshot({ path: sp + '/crm/fiche.png' });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);

  console.log('\n── Silence ──');
  dire('aucune erreur JavaScript', err.length === 0, err.join(' | ') || 'aucune');
  dire('aucune alerte affichée', dialogues.length === 0, dialogues.join(' | ') || 'aucune');

  await page.screenshot({ path: sp + '/crm/tableau.png' });

  // Le cas « la feuille n'est pas arrivée » : le bandeau doit parler.
  const nu = await nav.newPage({ viewport: { width: 1200, height: 700 } });
  await nu.route('**/crm.css', r => r.abort());
  await nu.goto('file://' + sp + '/crm/index.html', { waitUntil: 'load' });
  await nu.waitForTimeout(200);
  console.log('\n── Sans la feuille de style ──');
  dire('le bandeau de panne s’affiche', await nu.evaluate(() =>
    document.querySelector('.crm-panne').offsetParent !== null));
  await nu.screenshot({ path: sp + '/crm/sans-css.png' });

  await nav.close();
  console.log(rate ? '\n' + rate + ' échec(s)' : '\nTout passe.');
  process.exit(rate ? 1 : 0);
})();
