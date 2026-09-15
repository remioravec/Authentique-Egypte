#!/usr/bin/env node
/*
  Netteté, provenance et poids des images — ticket O2 du plan
  `docs/plan-pages-programme.md`.

  Ce que l'outil mesure, et que l'œil ne sait pas mesurer : le FACTEUR
  D'AGRANDISSEMENT de chaque image. On rend la page hors ligne à 390,
  1360 et 1920 px, on relève la boîte réelle de chaque image (object-fit
  compris : un `cover` sur une boîte large tire l'image par sa largeur,
  sur une boîte haute par sa hauteur), on choisit la même candidate de
  `srcset` que le navigateur choisirait, et on divise.

      facteur = pixels demandés à l'écran ÷ pixels réellement disponibles

  Au-dessus de 1,00, l'image est étirée : c'est du flou. C'est la seule
  définition qui tienne — « ça a l'air net » n'en est pas une.

  Les tailles réelles viennent de l'inventaire de la fiche
  (`docs/programmes/<slug>.json`) et du cache médias, jamais du réseau :
  la page est rendue sans requête, comme les autres contrôles du projet.

  usage : node outils/verif/images.js <page.html> [--inventaire <x.json>] [--json]
          [--registre <liste.json>]   images d'interface acceptées (logo, cartes sœurs)
*/
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const fichier = args[0];
if (!fichier) { console.error('usage : images.js <page.html> [--inventaire x.json] [--json]'); process.exit(2); }
const opt = (nom, def = '') => { const i = args.indexOf(nom); return i > 0 ? args[i + 1] : def; };
const enJson = args.includes('--json');
const absolu = path.resolve(fichier);
const RACINE = path.resolve(__dirname, '..', '..');

// Les seuils. Ils sont ici, une seule fois, et l'annexe A du plan les cite.
const VUES = [
  { nom: 'mobile', largeur: 390, dpr: 2, seuilBloquant: 1.0, seuilMajeur: 1.0 },
  { nom: 'bureau', largeur: 1360, dpr: 1, seuilBloquant: 1.0, seuilMajeur: 1.0 },
  { nom: 'grand écran', largeur: 1920, dpr: 1, seuilBloquant: 1.25, seuilMajeur: 1.0 },
];
const POIDS_MAX = 400 * 1024;   // au-delà, sur une image de moins de 1200 px

// ---------------------------------------------------------------- tailles réelles

function chargerTailles() {
  const par = new Map();          // nom de base (minuscules) → { largeur, hauteur }
  // Même règle que l'inventaire : ni la taille, ni le « -scaled » que
  // WordPress ajoute à l'original d'une grande image.
  const base = u => decodeURIComponent(String(u).split('?')[0].split('/').pop() || '')
    .replace(/-\d{2,4}x\d{2,4}(?=\.\w+$)/, '').replace(/-scaled(?=\.\w+$)/, '');

  // Une image et ses déclinaisons portent le même nom de base une fois
  // le suffixe de taille retiré : on garde la PLUS GRANDE, sinon la
  // vignette de 150 px ferait passer un original de 2560 px pour minuscule.
  const ajoute = (url, l, h) => {
    if (!url || !l) return;
    const cle = base(url).toLowerCase();
    const vu = par.get(cle);
    if (!vu || vu.largeur < l) par.set(cle, { largeur: l, hauteur: h });
  };

  const inv = opt('--inventaire');
  if (inv && fs.existsSync(inv)) {
    const d = JSON.parse(fs.readFileSync(inv, 'utf8'));
    for (const e of (d.images || []).concat(d.image_une ? [d.image_une] : [])) {
      ajoute(e.src_original, e.largeur, e.hauteur);
      for (const t of Object.values(e.tailles || {})) ajoute(t.url, t.largeur, t.hauteur);
    }
  }
  const cache = path.join(RACINE, 'docs', 'programmes', '_medias.json');
  if (fs.existsSync(cache)) {
    for (const m of Object.values(JSON.parse(fs.readFileSync(cache, 'utf8')))) {
      if (!m) continue;
      ajoute(m.url, m.largeur, m.hauteur);
      for (const t of Object.values(m.tailles || {})) ajoute(t.url, t.largeur, t.hauteur);
    }
  }
  return { par, base };
}

(async () => {
  const { par: TAILLES, base: nomDeBase } = chargerTailles();
  const registre = opt('--registre');
  const acceptees = registre && fs.existsSync(registre)
    ? new Set(JSON.parse(fs.readFileSync(registre, 'utf8')).map(x => String(x).toLowerCase()))
    : new Set();

  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const releve = { fichier, vues: {}, images: [] };

  for (const vue of VUES) {
    const page = await nav.newPage({
      viewport: { width: vue.largeur, height: 900 },
      deviceScaleFactor: vue.dpr,
    });
    await page.route(/^https?:/, r => r.abort());
    await page.goto('file://' + absolu, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);        // les apparitions au défilement

    const mesures = await page.evaluate((dpr) => {
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
      // Un fond volontairement FLOUTÉ (data-flou) n'a pas de netteté à
      // mesurer : c'est la composition « image contenue » de D14, où la
      // photo nette reste à sa taille réelle et où le flou remplit le
      // reste de l'écran. Lui reprocher son agrandissement reviendrait à
      // exiger qu'un flou soit net.
      return [...document.querySelectorAll('img')]
        .filter(img => !img.closest('[data-flou]'))
        .map((img, i) => {
        const r = img.getBoundingClientRect();
        const s = getComputedStyle(img);
        const visible = s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
        return {
          rang: i,
          src: img.getAttribute('src') || '',
          srcset: img.getAttribute('srcset') || '',
          sizes: img.getAttribute('sizes') || '',
          alt: img.getAttribute('alt'),
          loading: img.getAttribute('loading') || '',
          objectFit: s.objectFit,
          boite: { l: Math.round(r.width), h: Math.round(r.height) },
          visible,
          selecteur: sel(img),
          dpr,
        };
      });
    }, vue.dpr);

    releve.vues[vue.nom] = mesures;
    await page.close();
  }
  await nav.close();

  // ------------------------------------------------------------ calcul

  const candidates = (srcset, src) => {
    const lot = [];
    for (const part of String(srcset).split(',')) {
      const m = part.trim().match(/^(\S+)\s+(\d+)w$/);
      if (m) lot.push({ url: m[1], largeur: Number(m[2]) });
    }
    if (!lot.length && src) {
      const t = TAILLES.get(nomDeBase(src).toLowerCase());
      if (t) lot.push({ url: src, largeur: t.largeur });
    }
    return lot.sort((a, b) => a.largeur - b.largeur);
  };

  // Largeur utile : ce que la boîte demande vraiment à l'image.
  // `cover` recadre : l'image est tirée par le côté le plus contraignant.
  const largeurUtile = (m, naturelle) => {
    const { l, h } = m.boite;
    if (m.objectFit === 'cover' && naturelle && naturelle.largeur && naturelle.hauteur) {
      const ratio = naturelle.largeur / naturelle.hauteur;
      return Math.max(l, h * ratio);
    }
    return l;
  };

  const parRang = new Map();
  for (const vue of VUES) {
    for (const m of releve.vues[vue.nom]) {
      if (!m.visible) continue;
      const base = nomDeBase(m.src).toLowerCase();
      const naturelle = TAILLES.get(base) || null;
      const cand = candidates(m.srcset, m.src);
      const besoin = largeurUtile(m, naturelle) * m.dpr;
      // Le navigateur prend la plus petite candidate qui couvre le besoin.
      const choisie = cand.find(c => c.largeur >= besoin) || cand[cand.length - 1] || null;
      const dispo = choisie ? choisie.largeur : (naturelle ? naturelle.largeur : null);
      const facteur = dispo ? besoin / dispo : null;

      if (!parRang.has(m.rang)) {
        parRang.set(m.rang, {
          base, src: m.src, alt: m.alt, selecteur: m.selecteur,
          naturelle, aSrcset: !!m.srcset, mesures: {},
        });
      }
      parRang.get(m.rang).mesures[vue.nom] = {
        boite: m.boite, objectFit: m.objectFit,
        besoin: Math.round(besoin), dispo,
        facteur: facteur === null ? null : Number(facteur.toFixed(2)),
      };
    }
  }
  releve.images = [...parRang.values()];

  // ------------------------------------------------------------ verdict

  const bloquants = [], majeurs = [], mineurs = [];
  const dit = e => `${e.base} (${e.selecteur})`;

  for (const e of releve.images) {
    for (const vue of VUES) {
      const m = e.mesures[vue.nom];
      if (!m) continue;
      if (m.facteur === null) {
        if (!mineurs.some(x => x.includes(e.base)))
          mineurs.push(`taille réelle inconnue : ${dit(e)} — non résolue dans l'inventaire`);
        continue;
      }
      if (vue.nom === 'grand écran') {
        if (m.facteur > vue.seuilBloquant)
          majeurs.push(`agrandie ×${m.facteur} à 1920 px : ${dit(e)} — ${m.besoin} px demandés, ${m.dispo} px disponibles`);
        else if (m.facteur > vue.seuilMajeur)
          mineurs.push(`légèrement agrandie ×${m.facteur} à 1920 px : ${dit(e)}`);
      } else if (m.facteur > 1.0) {
        bloquants.push(`agrandie ×${m.facteur} en ${vue.nom} (${vue.largeur} px, densité ${vue.dpr}) : `
          + `${dit(e)} — ${m.besoin} px demandés, ${m.dispo} px disponibles`);
      }
    }
    if (/-\d{2,4}x\d{2,4}\.(jpe?g|png|webp)|elementor\/thumbs\//i.test(e.src))
      majeurs.push(`vignette servie au lieu de l'original : ${dit(e)}`);
    if (e.alt === null) mineurs.push(`image sans attribut alt : ${dit(e)}`);
    else if (e.alt !== '' && (/\.(jpe?g|png|webp|avif)$/i.test(e.alt)
      || /^(img|dsc|photo|capture)[-_ ]?\d+/i.test(e.alt) || /^[\w-]{10,}-\w{6,}$/.test(e.alt)))
      mineurs.push(`alt qui n'est qu'un nom de fichier : ${dit(e)}`);
    if (!e.aSrcset && e.naturelle && e.naturelle.largeur >= 1200)
      mineurs.push(`pas de srcset sur une image de ${e.naturelle.largeur} px : ${dit(e)} — le visiteur mobile télécharge tout`);
  }

  // Provenance : toute image doit venir de l'inventaire ou du registre.
  const inv = opt('--inventaire');
  if (inv && fs.existsSync(inv)) {
    const d = JSON.parse(fs.readFileSync(inv, 'utf8'));
    const dedans = new Set((d.images || []).concat(d.image_une ? [d.image_une] : [])
      .map(e => String(e.base).toLowerCase()));
    // Les cartes « séjours proches » portent les photos des fiches
    // voisines : elles appartiennent au site, pas à celle-ci. On les
    // accepte, en disant de quelle fiche elles viennent.
    const corpus = new Map();
    const dossier = path.dirname(inv);
    for (const f of fs.readdirSync(dossier)) {
      if (!f.endsWith('.json') || f.startsWith('_') || path.join(dossier, f) === path.resolve(inv)) continue;
      const v = JSON.parse(fs.readFileSync(path.join(dossier, f), 'utf8'));
      for (const x of (v.images || []).concat(v.image_une ? [v.image_une] : []))
        corpus.set(String(x.base).toLowerCase(), v.slug || f.replace(/\.json$/, ''));
    }
    const soeurs = [];
    for (const e of releve.images) {
      if (dedans.has(e.base) || acceptees.has(e.base)) continue;
      if (corpus.has(e.base)) { soeurs.push(`${e.base} → ${corpus.get(e.base)}`); continue; }
      bloquants.push(`image étrangère à la fiche et absente du registre : ${dit(e)}`);
    }
    if (soeurs.length) releve.soeurs = soeurs;
    // « Aucune photo de la fiche ne disparaît » est une règle de FICHE.
    // Un inventaire dont le slug commence par « _ » est un RÉSERVOIR
    // — les photos de toutes les familles, par exemple — et une page
    // n'a évidemment pas à les porter toutes. La règle de provenance,
    // elle, continue de s'appliquer : rien n'entre qui ne vienne du
    // réservoir ou du registre.
    const reservoir = String(d.slug || '').startsWith('_');
    const posees = new Set(releve.images.map(e => e.base));
    const oubliees = reservoir ? [] : [...dedans].filter(b => !posees.has(b));
    if (oubliees.length)
      majeurs.push(`image(s) de la fiche non reprise(s) : ${oubliees.join(', ')}`);
  }

  releve.defauts = { bloquants, majeurs, mineurs };
  releve.verdict = bloquants.length ? 'REFUSÉ' : majeurs.length ? 'À CORRIGER' : 'CONFORME';

  if (enJson) { console.log(JSON.stringify(releve, null, 1)); return; }

  console.log('IMAGES —', fichier);
  console.log('  verdict :', releve.verdict, '·', releve.images.length, 'image(s) visible(s)');
  if (releve.soeurs) console.log('  photos de fiches sœurs (cartes de fin de page) :', releve.soeurs.join(' · '));
  console.log('  ' + 'image'.padEnd(44) + 'réelle'.padEnd(12) + '390px'.padEnd(9) + '1360px'.padEnd(9) + '1920px');
  for (const e of releve.images) {
    const f = v => {
      const m = e.mesures[v];
      if (!m) return '—'.padEnd(9);
      const s = m.facteur === null ? '?' : '×' + m.facteur.toFixed(2);
      return (m.facteur !== null && m.facteur > 1 ? s + ' !' : s).padEnd(9);
    };
    const n = e.naturelle ? `${e.naturelle.largeur}×${e.naturelle.hauteur}` : 'inconnue';
    console.log('  ' + e.base.slice(0, 42).padEnd(44) + n.padEnd(12) + f('mobile') + f('bureau') + f('grand écran'));
  }
  for (const [k, l] of Object.entries(releve.defauts)) {
    console.log('  ' + k + ' (' + l.length + ')');
    l.forEach(d => console.log('    - ' + d));
  }
})();
