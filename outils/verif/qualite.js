#!/usr/bin/env node
/*
  Relevé de qualité d'une page HTML — l'outil de l'agent QUALITÉ.

  Ouvre la page hors ligne (aucune requête réseau, comme les audits du
  projet) à 1360 px puis à 390 px, et mesure ce qui se mesure : erreurs
  JS, débordement horizontal, sections vides, hiérarchie des titres,
  images réduites, liens morts, textes de chantier, accordéons, appels
  à l'action, panneau collant. Sort un JSON ; le jugement (cohérence,
  pertinence) reste à l'agent.

  usage : node outils/verif/qualite.js <fichier.html> [--json]
*/
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const fichier = process.argv[2];
if (!fichier) { console.error('usage : qualite.js <fichier.html> [--json]'); process.exit(2); }
const enJson = process.argv.includes('--json');
const absolu = path.resolve(fichier);

const CHANTIER = /lorem ipsum|à compléter|a completer|aremplir|xxx|todo|placeholder|\[image\]|\[texte\]/i;

(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const releve = { fichier, bureau: null, mobile: null };

  for (const [nom, largeur] of [['bureau', 1360], ['mobile', 390]]) {
    const page = await nav.newPage({ viewport: { width: largeur, height: 900 } });
    const erreurs = [];
    page.on('pageerror', e => erreurs.push(String(e).slice(0, 160)));
    page.on('dialog', d => { erreurs.push('dialogue bloquant : ' + d.message()); d.dismiss(); });
    await page.route(/^https?:/, r => r.abort());
    await page.goto('file://' + absolu, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000); // laisse passer les animations d'apparition et leur garde-fou

    const r = await page.evaluate((CHANTIER_SRC) => {
      const chantier = new RegExp(CHANTIER_SRC, 'i');
      const texte = el => (el.textContent || '').replace(/\s+/g, ' ').trim();
      const visible = el => { const s = getComputedStyle(el); const b = el.getBoundingClientRect();
        return s.display !== 'none' && s.visibility !== 'hidden' && b.width > 0 && b.height > 0; };
      const sel = el => {
        const parts = [];
        for (let e = el; e && e.nodeType === 1 && parts.length < 5; e = e.parentElement) {
          let p = e.tagName.toLowerCase();
          if (e.id) { parts.unshift('#' + e.id); break; }
          if (e.classList.length) p += '.' + [...e.classList].slice(0, 2).join('.');
          parts.unshift(p);
        }
        return parts.join(' > ');
      };

      const h1 = [...document.querySelectorAll('h1')];
      const titres = [...document.querySelectorAll('h1,h2,h3,h4')].filter(visible);
      const niveaux = titres.map(t => Number(t.tagName[1]));
      const sauts = [];
      for (let i = 1; i < niveaux.length; i++) if (niveaux[i] > niveaux[i - 1] + 1)
        sauts.push(titres[i - 1].tagName + ' → ' + titres[i].tagName + ' : « ' + texte(titres[i]).slice(0, 60) + ' »');
      const comptes = {};
      titres.forEach(t => { const k = t.tagName + '|' + texte(t).toLowerCase(); comptes[k] = (comptes[k] || 0) + 1; });
      const doublons = Object.entries(comptes).filter(([, n]) => n > 1).map(([k, n]) => k.split('|')[1] + ' ×' + n);

      const sections = [...document.querySelectorAll('section, main > div, article')].filter(visible);
      const vides = sections.filter(s => texte(s).length < 20 && !s.querySelector('img,svg,video')).map(sel);
      const titresOrphelins = titres.filter(t => {
        if (t.closest('summary')) return false;     // le titre d'un accordéon : son contenu est le corps du details
        let n = t.nextElementSibling;
        return !n || /^H[1-4]$/.test(n.tagName) && Number(n.tagName[1]) <= Number(t.tagName[1]);
      }).map(t => texte(t).slice(0, 70));

      const imgs = [...document.querySelectorAll('img')];
      const reduites = imgs.filter(i => /-\d{2,4}x\d{2,4}\.(jpe?g|png|webp)|elementor\/thumbs\//i.test(i.getAttribute('src') || ''))
        .map(i => (i.getAttribute('src') || '').split('/').pop());
      const sansAlt = imgs.filter(i => !i.hasAttribute('alt')).length;
      // Un alt d'un seul mot n'est pas un nom de fichier : « Guesthouse »
      // décrit l'image. On ne signale que ce qui EST un nom de fichier.
      const altFichier = imgs.filter(i => {
        const a = i.getAttribute('alt') || '';
        return /\.(jpe?g|png|webp|avif)$/i.test(a) || /^(img|dsc|photo|capture)[-_ ]?\d+/i.test(a)
          || /^[\w-]{10,}-\w{6,}$/.test(a);
      }).length;

      const liens = [...document.querySelectorAll('a[href]')];
      const morts = liens.filter(a => { const h = a.getAttribute('href') || ''; return h === '#' || h === '' || /^javascript:/.test(h); }).length;
      const relatifs = [...new Set(liens.map(a => a.getAttribute('href') || '')
        .filter(h => /^[a-z0-9_.-]+\.html/i.test(h) || /^\.\.\//.test(h)))];

      const chantiers = [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && chantier.test(texte(e)))
        .map(e => texte(e).slice(0, 80)).slice(0, 10);

      const details = [...document.querySelectorAll('details')];
      const boutons = [...document.querySelectorAll('a.btn, button, a[class*="cta"], a[class*="btn"]')].filter(visible);
      const devis = boutons.filter(b => /devis|whatsapp|contact|réserver|reserver|personnaliser/i.test(texte(b))).length;
      const collants = [...document.querySelectorAll('*')].filter(e => getComputedStyle(e).position === 'sticky').map(sel);

      return {
        h1: h1.map(texte), nbH1: h1.length,
        titre: document.title, description: (document.querySelector('meta[name="description"]') || {}).content || '',
        sautsHierarchie: sauts, titresDoublons: doublons, titresOrphelins,
        sectionsVides: vides,
        images: { total: imgs.length, reduites, sansAlt, altNomDeFichier: altFichier },
        liens: { total: liens.length, morts, relatifsLocaux: relatifs },
        textesDeChantier: chantiers,
        accordeons: { total: details.length, ouverts: details.filter(d => d.open).length },
        appelsAction: { boutons: boutons.length, conversion: devis },
        collants,
        deborde: document.documentElement.scrollWidth > window.innerWidth,
        largeurDefilement: document.documentElement.scrollWidth,
        mots: texte(document.body).split(' ').length,
      };
    }, CHANTIER.source);
    r.erreursJS = erreurs;
    releve[nom] = r;
    await page.close();
  }
  await nav.close();

  // Les défauts, classés — l'agent en fait sa lecture.
  const b = releve.bureau, m = releve.mobile;
  const bloquants = [], majeurs = [], mineurs = [];
  if (b.erreursJS.length) bloquants.push('erreurs JS : ' + b.erreursJS.join(' | '));
  if (b.nbH1 !== 1) bloquants.push('H1 : ' + b.nbH1 + ' trouvé(s) (attendu 1)');
  if (b.textesDeChantier.length) bloquants.push('textes de chantier : ' + b.textesDeChantier.join(' | '));
  if (b.sectionsVides.length) majeurs.push('sections vides : ' + b.sectionsVides.join(', '));
  if (b.deborde) majeurs.push('déborde horizontalement à 1360 px (' + b.largeurDefilement + ' px)');
  if (m.deborde) majeurs.push('déborde horizontalement à 390 px (' + m.largeurDefilement + ' px)');
  if (b.images.reduites.length) majeurs.push('images réduites (floues en grand) : ' + b.images.reduites.join(', '));
  if (b.liens.relatifsLocaux.length) majeurs.push('liens relatifs locaux (morts une fois en ligne) : ' + b.liens.relatifsLocaux.join(', '));
  if (!b.appelsAction.conversion) majeurs.push('aucun appel à l’action de conversion (devis / WhatsApp)');
  if (b.titresDoublons.length) majeurs.push('titres en double : ' + b.titresDoublons.join(', '));
  if (b.sautsHierarchie.length) mineurs.push('sauts de hiérarchie : ' + b.sautsHierarchie.join(' ; '));
  if (b.titresOrphelins.length) mineurs.push('titres sans contenu dessous : ' + b.titresOrphelins.join(' ; '));
  if (b.liens.morts) mineurs.push(b.liens.morts + ' lien(s) vers « # »');
  if (b.images.sansAlt) mineurs.push(b.images.sansAlt + ' image(s) sans alt');
  if (b.images.altNomDeFichier) mineurs.push(b.images.altNomDeFichier + ' alt qui ne sont qu’un nom de fichier');
  if (!b.description) mineurs.push('meta description absente');
  releve.defauts = { bloquants, majeurs, mineurs };
  releve.verdict = bloquants.length ? 'REFUSÉ' : majeurs.length ? 'À CORRIGER' : 'CONFORME';

  if (enJson) { console.log(JSON.stringify(releve, null, 1)); return; }
  console.log('QUALITÉ —', fichier);
  console.log('  verdict :', releve.verdict);
  console.log('  H1 :', b.h1.join(' / ') || '—', '| titres :', b.titre || '—');
  console.log('  mots :', b.mots, '| images :', b.images.total, '| accordéons :', b.accordeons.total,
    '(ouverts ' + b.accordeons.ouverts + ') | CTA conversion :', b.appelsAction.conversion, '| collants :', b.collants.length);
  for (const [k, l] of Object.entries(releve.defauts)) {
    console.log('  ' + k + ' (' + l.length + ')');
    l.forEach(d => console.log('    - ' + d));
  }
})();
