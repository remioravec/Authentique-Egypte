#!/usr/bin/env node
/*
  Espacement, lisibilité, contraste — ticket O3 du plan
  `docs/plan-pages-programme.md`.

  Ce que l'outil mesure, page rendue, à 1360 et 390 px :

    · la taille de chaque texte visible (plancher 15 px sur mobile) ;
    · l'interligne, en rapport de la taille ;
    · la longueur de ligne, en caractères — au-delà de 90, l'œil perd
      la ligne suivante ;
    · le contraste du texte sur son fond, quand ce fond est une couleur ;
    · le TEXTE TRONQUÉ : une ellipse CSS sur du contenu de la cliente
      n'est pas un choix de mise en page, c'est une phrase amputée ;
    · les recouvrements entre voisins, et ce qu'une barre collante cache ;
    · le rythme vertical : les sections doivent prendre leurs valeurs
      dans une échelle, pas au hasard.

  Limite assumée : le rendu se fait hors ligne, comme les autres
  contrôles du projet. Le contraste d'un texte posé sur une PHOTO ne se
  mesure donc pas au pixel ; l'outil vérifie qu'un voile (dégradé ou
  couche sombre) et une ombre portée existent, et le signale sinon.
  La netteté des images, elle, est l'affaire de `images.js`.

  usage : node outils/verif/lisibilite.js <page.html> [--json]
*/
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

const fichier = process.argv[2];
if (!fichier) { console.error('usage : lisibilite.js <page.html> [--json]'); process.exit(2); }
const enJson = process.argv.includes('--json');
const absolu = path.resolve(fichier);

const VUES = [
  { nom: 'bureau', largeur: 1360, planchePolice: 12.5, echelleSection: [40, 48, 56, 64, 72, 88] },
  { nom: 'mobile', largeur: 390, planchePolice: 15, echelleSection: [28, 32, 40, 48, 56] },
];

(async () => {
  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const releve = { fichier, vues: {} };

  for (const vue of VUES) {
    const page = await nav.newPage({ viewport: { width: vue.largeur, height: 900 } });
    await page.route(/^https?:/, r => r.abort());
    await page.goto('file://' + absolu, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);

    releve.vues[vue.nom] = await page.evaluate((cfg) => {
      const sel = el => {
        const p = [];
        for (let e = el; e && e.nodeType === 1 && p.length < 4; e = e.parentElement) {
          if (e.id) { p.unshift('#' + e.id); break; }
          let t = e.tagName.toLowerCase();
          if (e.classList.length) t += '.' + [...e.classList].slice(0, 2).join('.');
          p.unshift(t);
        }
        return p.join(' > ');
      };
      const txt = el => (el.textContent || '').replace(/\s+/g, ' ').trim();
      const vu = el => {
        const s = getComputedStyle(el), r = el.getBoundingClientRect();
        return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0.05
          && r.width > 0 && r.height > 0;
      };
      // Un élément qui ne porte QUE des enfants n'a pas de texte à lui.
      const texteDirect = el => [...el.childNodes]
        .filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();

      const rgb = c => {
        const m = String(c).match(/rgba?\(([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?/);
        return m ? { r: +m[1], v: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] } : null;
      };
      const lum = c => {
        const f = x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(c.r) + 0.7152 * f(c.v) + 0.0722 * f(c.b);
      };
      const contraste = (a, b) => {
        const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
        return (x + 0.05) / (y + 0.05);
      };
      // Le fond effectif : on remonte jusqu'à une couleur opaque.
      // Une photo ou un dégradé interrompt la remontée : on le dit.
      const fondDe = el => {
        for (let e = el; e; e = e.parentElement) {
          const s = getComputedStyle(e);
          const fi = s.backgroundImage;
          if (fi && fi !== 'none') {
            // Une photo (`url(...)`) ne se mesure pas hors ligne. Un
            // dégradé, si : on prend celle de ses couleurs qui donne le
            // PIRE contraste, et on juge là-dessus.
            if (/url\(/.test(fi)) return { photo: true, sur: sel(e) };
            const stops = (fi.match(/rgba?\([^)]+\)/g) || []).map(rgb)
              .filter(c => c && c.a >= 0.85);
            if (stops.length) return { stops, sur: sel(e) };
          }
          const c = rgb(s.backgroundColor);
          if (c && c.a >= 0.95) return { couleur: c };
        }
        return { couleur: { r: 255, v: 255, b: 255, a: 1 } };
      };

      const PORTEURS = 'p,li,h1,h2,h3,h4,h5,h6,span,b,strong,em,small,td,th,summary,figcaption,a,button,label,blockquote,dt,dd';
      const textes = [];
      for (const el of document.querySelectorAll(PORTEURS)) {
        if (!vu(el)) continue;
        const propre = texteDirect(el);
        if (propre.length < 2) continue;
        const s = getComputedStyle(el), r = el.getBoundingClientRect();
        const taille = parseFloat(s.fontSize);
        const inter = parseFloat(s.lineHeight) || taille * 1.2;
        const couleur = rgb(s.color) || { r: 0, v: 0, b: 0, a: 1 };
        const fond = fondDe(el);
        const gras = Number(s.fontWeight) >= 600;
        // Largeur d'une ligne, en caractères : la largeur de la boîte
        // divisée par la largeur moyenne d'un caractère (≈ 0,5 em).
        // Caractères par ligne : la largeur de la boîte divisée par la
        // largeur moyenne d'un caractère (≈ 0,5 em). Un texte court dans
        // une boîte large n'enroule pas : il ne se mesure pas.
        const capacite = Math.round(r.width / (taille * 0.5));
        const lignes = Math.max(1, Math.round(r.height / inter));
        const parLigne = (lignes > 1 && propre.length > capacite) ? capacite : null;
        // Un glyphe décoratif, masqué aux lecteurs d'écran et doublé
        // par un texte voisin, ne porte pas d'information : le critère
        // de contraste des TEXTES ne s'y applique pas.
        const decoratif = el.closest('[aria-hidden="true"]') !== null;
        // Un texte n'est coupé que si le débordement est MASQUÉ. Le
        // « text-overflow: clip » par défaut ne coupe rien tout seul.
        const masque = /hidden|clip/.test(s.overflow) || /hidden|clip/.test(s.overflowX);
        const tronque = el.scrollWidth > el.clientWidth + 1
          && (masque || (s.textOverflow === 'ellipsis' && s.whiteSpace === 'nowrap'));
        textes.push({
          selecteur: sel(el), extrait: propre.slice(0, 60), balise: el.tagName.toLowerCase(),
          taille: Math.round(taille * 10) / 10,
          interligne: Math.round((inter / taille) * 100) / 100,
          parLigne,
          gras, tronque,
          ombre: s.textShadow !== 'none',
          contraste: decoratif ? null
            : fond.couleur ? Math.round(contraste(couleur, fond.couleur) * 100) / 100
            : fond.stops ? Math.round(Math.min(...fond.stops.map(c => contraste(couleur, c))) * 100) / 100
            : null,
          decoratif,
          surPhoto: !!fond.photo,
        });
      }

      // Une marge verticale déclarée sur un élément EN LIGNE est
      // purement ignorée par le navigateur. Le défaut est invisible à la
      // relecture du CSS — la règle est bien là — et ne se voit qu'à la
      // mesure. Il a coûté 36 px d'air sous chaque photo d'étape.
      const margesMortes = [...document.querySelectorAll('main *')].filter(el => {
        if (!vu(el)) return false;
        const s = getComputedStyle(el);
        if (s.display !== 'inline') return false;
        return parseFloat(s.marginTop) > 1 || parseFloat(s.marginBottom) > 1;
      }).map(el => ({ selecteur: sel(el),
                      marges: getComputedStyle(el).marginTop + ' / ' + getComputedStyle(el).marginBottom }));

      // Cibles tactiles.
      // Une case dérobée à l'œil mais laissée au clavier n'est pas une
      // cible de 1 px : ce qu'on touche, c'est son <label>, et c'est LUI
      // qui doit faire 44 px. On l'écarte donc, mais seulement si ce
      // label existe vraiment et tient la mesure — sinon la commande
      // n'est atteignable ni au doigt ni au clavier, et le défaut est
      // réel.
      const derobee = el => {
        if (!(el.tagName === 'INPUT' || el.tagName === 'SELECT')) return false;
        const r = el.getBoundingClientRect();
        if (r.width > 2 || r.height > 2) return false;
        const lab = el.id ? document.querySelector(`label[for="${el.id}"]`) : el.closest('label');
        if (!lab) return false;
        const rl = lab.getBoundingClientRect();
        return rl.width >= 44 && rl.height >= 44;
      };
      const cibles = [...document.querySelectorAll('a,button,summary,input,select,[role="button"]')]
        .filter(el => vu(el) && !derobee(el)).map(el => {
          const r = el.getBoundingClientRect();
          return { selecteur: sel(el), extrait: txt(el).slice(0, 40), l: Math.round(r.width), h: Math.round(r.height),
                   enLigne: getComputedStyle(el).display === 'inline' };
        });

      // Rythme vertical : les sections de premier niveau
      const sections = [...document.querySelectorAll('main > section, main > div.wrap, main > div, body > section')]
        .filter(vu).map(el => {
          const s = getComputedStyle(el), r = el.getBoundingClientRect();
          return { selecteur: sel(el), haut: Math.round(parseFloat(s.paddingTop)),
                   bas: Math.round(parseFloat(s.paddingBottom)), hauteur: Math.round(r.height) };
        });

      // Recouvrements entre frères posés dans le flux
      const recouvre = [];
      for (const parent of document.querySelectorAll('main, main *')) {
        // Un <svg> a son propre système de coordonnées : deux points
        // voisins sur une carte s'y touchent par construction.
        if (parent.closest('svg')) continue;
        const enfants = [...parent.children].filter(e => vu(e)
          && !['absolute', 'fixed', 'sticky'].includes(getComputedStyle(e).position));
        for (let i = 0; i < enfants.length - 1; i++) {
          // Deux éléments EN LIGNE dans un même paragraphe ne se
          // recouvrent pas : leur rectangle est l'UNION de leurs lignes,
          // et un lien qui court sur deux lignes englobe forcément le
          // gras posé au début de la seconde. Ce n'est pas un défaut de
          // mise en page, c'est la définition d'une boîte en ligne.
          const enLigne = el => getComputedStyle(el).display === 'inline';
          if (enLigne(enfants[i]) && enLigne(enfants[i + 1])) continue;
          const a = enfants[i].getBoundingClientRect(), b = enfants[i + 1].getBoundingClientRect();
          const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          const l = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          if (h > 4 && l > 4 && txt(enfants[i]) && txt(enfants[i + 1]))
            recouvre.push(sel(enfants[i]) + ' ⨯ ' + sel(enfants[i + 1]));
        }
      }

      // Ce qu'une barre fixe recouvre en bas de page
      const fixes = [...document.querySelectorAll('*')].filter(e => vu(e)
        && ['fixed'].includes(getComputedStyle(e).position)).map(e => {
          const r = e.getBoundingClientRect();
          return { selecteur: sel(e), haut: Math.round(r.top), hauteur: Math.round(r.height) };
        });
      const padBody = Math.round(parseFloat(getComputedStyle(document.body).paddingBottom));

      return {
        textes, cibles, sections, margesMortes, recouvre: [...new Set(recouvre)], fixes, padBody,
        deborde: document.documentElement.scrollWidth > window.innerWidth,
        largeur: document.documentElement.scrollWidth,
      };
    }, vue);

    await page.close();
  }
  await nav.close();

  // ------------------------------------------------------------- verdict
  const bloquants = [], majeurs = [], mineurs = [];
  const unique = (lot, ligne) => { if (!lot.includes(ligne)) lot.push(ligne); };

  for (const vue of VUES) {
    const d = releve.vues[vue.nom];
    const ou = vue.nom;

    for (const t of d.textes) {
      if (t.tronque)
        unique(bloquants, `texte tronqué (${ou}) : « ${t.extrait} » — ${t.selecteur}`);
      if (t.taille < vue.planchePolice)
        unique(majeurs, `police ${t.taille} px sous le plancher de ${vue.planchePolice} px (${ou}) : `
          + `« ${t.extrait} » — ${t.selecteur}`);
      if (!/^h[1-4]$/.test(t.balise) && t.interligne < 1.35 && t.parLigne)
        unique(majeurs, `interligne ${t.interligne} trop serré (${ou}) : « ${t.extrait} » — ${t.selecteur}`);
      if (t.parLigne && t.parLigne > 90)
        unique(majeurs, `ligne de ${t.parLigne} caractères (${ou}, max 90) : ${t.selecteur}`);
      else if (t.parLigne && t.parLigne > 80)
        unique(mineurs, `ligne de ${t.parLigne} caractères (${ou}, confort 45–80) : ${t.selecteur}`);
      const grand = t.taille >= 24 || (t.taille >= 19 && t.gras);
      const exige = grand ? 3 : 4.5;
      if (t.surPhoto) {
        if (!t.ombre)
          unique(mineurs, `texte sur photo sans ombre portée (${ou}) : « ${t.extrait} » — ${t.selecteur} `
            + `— contraste à confirmer à l'œil`);
      } else if (t.contraste !== null && t.contraste < exige) {
        unique(majeurs, `contraste ${t.contraste}:1 sous le minimum de ${exige}:1 (${ou}) : `
          + `« ${t.extrait} » — ${t.selecteur}`);
      }
    }

    if (ou === 'mobile') {
      for (const c of d.cibles) {
        if (c.enLigne) continue;                 // un lien dans une phrase suit la ligne
        if (c.h < 44 || c.l < 44)
          unique(majeurs, `cible tactile ${c.l}×${c.h} px sous 44×44 (mobile) : `
            + `« ${c.extrait} » — ${c.selecteur}`);
      }
      for (const f of d.fixes) {
        if (f.haut > 400 && d.padBody < f.hauteur)
          unique(majeurs, `la barre fixe ${f.selecteur} (${f.hauteur} px) recouvre le bas de page : `
            + `le corps ne réserve que ${d.padBody} px`);
      }
    }

    for (const s of d.sections) {
      for (const [cote, v] of [['haut', s.haut], ['bas', s.bas]]) {
        if (v > 8 && !vue.echelleSection.includes(v))
          unique(majeurs, `marge ${cote} de ${v} px hors échelle ${vue.echelleSection.join('/')} (${ou}) : ${s.selecteur}`);
      }
    }
    for (const m of d.margesMortes)
      unique(majeurs, `marge verticale ignorée (${ou}) : ${m.selecteur} est en ligne, `
        + `ses marges ${m.marges} ne s'appliquent pas`);
    for (const r of d.recouvre) unique(bloquants, `recouvrement (${ou}) : ${r}`);
    if (d.deborde) unique(majeurs, `débordement horizontal (${ou}) : ${d.largeur} px pour ${vue.largeur} px`);
  }

  releve.defauts = { bloquants, majeurs, mineurs };
  releve.verdict = bloquants.length ? 'REFUSÉ' : majeurs.length ? 'À CORRIGER' : 'CONFORME';

  if (enJson) { console.log(JSON.stringify(releve, null, 1)); return; }
  console.log('LISIBILITÉ —', fichier);
  console.log('  verdict :', releve.verdict);
  for (const vue of VUES) {
    const d = releve.vues[vue.nom];
    const min = Math.min(...d.textes.map(t => t.taille));
    console.log(`  ${vue.nom.padEnd(7)} ${d.textes.length} textes · plus petite police ${min} px · `
      + `${d.cibles.length} cibles · ${d.sections.length} sections · ${d.recouvre.length} recouvrement(s)`);
  }
  for (const [k, l] of Object.entries(releve.defauts)) {
    console.log('  ' + k + ' (' + l.length + ')');
    l.slice(0, 40).forEach(x => console.log('    - ' + x));
    if (l.length > 40) console.log(`    … et ${l.length - 40} de plus`);
  }
})();
