/* Contrôle mesuré des pages en ligne, au bureau et sur mobile.
 *
 *   node outils/controle-qualite.js <dossier de pages> <sortie.json>
 *
 * Les pages sont celles que le serveur rend, enregistrées telles quelles.
 * Les images distantes ne se chargent pas hors ligne : on ne mesure donc
 * pas leur rendu, mais on vérifie qu'elles déclarent leurs dimensions —
 * ce qui est justement ce qui évite les sauts de mise en page.
 */
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');

const LARGEURS = [[1280, 'bureau'], [390, 'mobile']];

(async () => {
  const dossier = process.argv[2], sortie = process.argv[3];
  const fichiers = fs.readdirSync(dossier).filter(f => f.endsWith('.html')).sort();
  const b = await chromium.launch({args: ['--no-sandbox']});
  const out = {};
  for (const f of fichiers) {
    out[f] = {};
    for (const [L, nom] of LARGEURS) {
      const p = await b.newPage({viewport: {width: L, height: 900}});
      const erreurs = [];
      p.on('pageerror', e => erreurs.push(String(e.message).slice(0, 80)));
      await p.goto('file://' + path.resolve(dossier, f), {waitUntil: 'domcontentloaded'}).catch(() => {});
      await p.waitForTimeout(450);
      const r = await p.evaluate(() => {
        const vu = e => {
          const r = e.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden';
        };
        const img = [...document.querySelectorAll('main img, [data-maillage] img')];
        const liens = [...document.querySelectorAll('main a')].filter(vu);
        const txt = [...document.querySelectorAll('main p, main li, main td')].filter(vu);
        const petits = txt.filter(e => parseFloat(getComputedStyle(e).fontSize) < 14).length;
        const cibles = liens.filter(a => a.getBoundingClientRect().height < 44).length;
        const vides = [...document.querySelectorAll('main a')]
          .filter(a => !a.textContent.trim() && !a.querySelector('img,svg')).length;
        const deborde = [...document.querySelectorAll('main *')]
          .filter(e => e.getBoundingClientRect().right > document.documentElement.clientWidth + 2).length;
        const bouton = document.querySelector('.entete button, .entete [aria-expanded]');
        return {
          h1: document.querySelectorAll('h1').length,
          entete: document.querySelectorAll('header.entete').length,
          pied: document.querySelectorAll('footer.pied').length,
          images: img.length,
          img_sans_alt: img.filter(i => !i.hasAttribute('alt')).length,
          img_sans_taille: img.filter(i => !i.getAttribute('width') || !i.getAttribute('height')).length,
          liens: liens.length,
          liens_vides: vides,
          cibles_sous_44: cibles,
          texte_sous_14: petits,
          debordements: deborde,
          largeur_doc: document.documentElement.scrollWidth,
          hauteur: document.body.scrollHeight,
          bouton_menu: !!bouton,
          lang: document.documentElement.lang || '',
        };
      });
      // le menu mobile s'ouvre-t-il vraiment ?
      if (L === 390) {
        r.menu_ouvre = await p.evaluate(() => {
          try {
            const b = document.querySelector('.entete button, .entete [aria-expanded]');
            if (!b) return false;
            const nav = document.querySelector('.entete nav, .nav');
            const avant = nav ? nav.getBoundingClientRect().height : 0;
            b.click();
            const apres = nav ? nav.getBoundingClientRect().height : 0;
            return apres > avant || document.body.classList.contains('ouvert')
              || b.getAttribute('aria-expanded') === 'true';
          } catch (e) { return false; }
        });
      }
      r.erreurs = erreurs.length;
      out[f][nom] = r;
      await p.close();
    }
  }
  await b.close();
  fs.writeFileSync(sortie, JSON.stringify(out, null, 1));
  console.log('mesuré : ' + fichiers.length + ' page(s) × ' + LARGEURS.length + ' largeurs');
})();
