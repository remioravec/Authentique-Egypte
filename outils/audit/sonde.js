/*
 * Sonde d'audit — mesure une page RENDUE, en bureau et en mobile.
 *
 *   node outils/audit/sonde.js DOSSIER PRÉFIXE SORTIE.json
 *
 * Tout ce qui est mesuré ici l'est sur le rendu, jamais sur la règle CSS.
 * Trois versions successives de la mesure du contraste ont donné trois
 * réponses différentes en lisant les feuilles de style : c'est la couleur
 * réellement composée à l'écran qui décide, et elle seule.
 */
const {chromium, devices} = require('playwright');
const fs = require('fs'), path = require('path');

const MESURE = () => {
  // ── outils de couleur ────────────────────────────────────────────────
  const canal = v => { v /= 255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); };
  const nb = c => (c.match(/[\d.]+/g) || []).map(Number);
  const lum = c => { const [r,g,b] = nb(c).slice(0,3).map(canal); return .2126*r + .7152*g + .0722*b; };
  const ratio = (a,b) => { const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05); };
  // Un fond translucide se COMPOSE sur celui qui est derrière : sans ce
  // calcul, du blanc sur un voile blanc à 8 % se lit 1,00:1 alors qu'il
  // est à 7,04:1 sur le bleu nuit qui porte le voile.
  const composer = (dessus, dessous) => {
    const a = nb(dessus), b = nb(dessous), alpha = a.length > 3 ? a[3] : 1;
    if (alpha >= 1) return `rgb(${a[0]}, ${a[1]}, ${a[2]})`;
    return `rgb(${[0,1,2].map(i => Math.round(a[i]*alpha + b[i]*(1-alpha))).join(', ')})`;
  };
  const fond = el => {
    let n = el, pile = [];
    while (n && n !== document.documentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage !== 'none') return null;   // photo ou dégradé : indécidable
      const bg = s.backgroundColor, a = nb(bg);
      if (bg && !(a.length > 3 && a[3] === 0)) { pile.push(bg); if (a.length < 4 || a[3] >= 1) break; }
      n = n.parentElement;
    }
    let couleur = 'rgb(255, 255, 255)';
    for (let i = pile.length - 1; i >= 0; i--) couleur = composer(pile[i], couleur);
    return couleur;
  };
  const nom = el => el.tagName.toLowerCase() + (el.className
    ? '.' + el.className.toString().trim().split(/\s+/).slice(0,2).join('.') : '');

  // ── A · structure ────────────────────────────────────────────────────
  const d = document.documentElement, L = innerWidth;
  const larges = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (!r.width || (r.right <= L + 2 && r.left >= -2)) continue;
    const s = getComputedStyle(el);
    if (s.position === 'fixed' || /auto|scroll/.test(s.overflowX)) continue;
    if (el.closest('[style*="overflow"],.mef-tab,.mur,.carrousel,.hero__flou')) continue;
    larges.push(nom(el) + '@' + Math.round(r.right));
  }
  const mur = document.querySelector('.mur');
  const structure = {
    debord: d.scrollWidth > L + 1 ? d.scrollWidth : 0,
    larges: [...new Set(larges)].slice(0, 5),
    h1: document.querySelectorAll('h1').length,
    hauteur: d.scrollHeight,
    sectionsMain: document.querySelectorAll('main > section').length,
    horsMain: [...document.querySelectorAll('body > section, body > div.wrap')].map(nom),
    imgSansSrc: [...document.images].filter(i => !i.getAttribute('src')
      && !i.closest('[role="dialog"],[hidden]')).length,
    murHaut: mur ? Math.round(mur.getBoundingClientRect().height) : 0,
    // Un bloc encore à l'opacité d'entrée dans le PREMIER écran : ailleurs
    // l'animation n'a simplement pas encore eu lieu.
    pales: [...document.querySelectorAll('[data-rev]')].filter(e => {
      const r = e.getBoundingClientRect();
      return r.top < innerHeight && r.bottom > 0 && parseFloat(getComputedStyle(e).opacity) < .5;
    }).length,
  };

  // ── B · UX / UI ──────────────────────────────────────────────────────
  const contraste = [], petits = [], cibles = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.opacity === '0') continue;
    const porteDuTexte = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const px = parseFloat(s.fontSize);
    if (porteDuTexte) {
      const fd = fond(el);
      if (fd) {
        const gras = parseInt(s.fontWeight, 10) >= 700;
        const seuil = (px >= 24 || (px >= 18.66 && gras)) ? 3 : 4.5;
        const ct = ratio(composer(s.color, fd), fd);
        if (ct < seuil) contraste.push({sel: nom(el), ct: +ct.toFixed(2), seuil, px: +px.toFixed(1),
          txt: el.textContent.trim().slice(0, 34)});
      }
      if (px < 14) petits.push({sel: nom(el), px: +px.toFixed(1), txt: el.textContent.trim().slice(0, 28)});
    }
    if (el.matches('a[href],button,input:not([type=hidden]),select,summary,label[for]')
        && el.offsetParent !== null && r.height < 44 && r.width < 240 && r.width > 4)
      cibles.push({sel: nom(el), h: Math.round(r.height), w: Math.round(r.width),
        txt: el.textContent.trim().slice(0, 24),
        // Un lien posé au milieu d'une phrase : la règle l'excepte.
        enLigne: !!el.closest('p,li,dd,blockquote,figcaption')
                 && getComputedStyle(el).display.startsWith('inline')});
  }

  // ── C · cohérence interne ────────────────────────────────────────────
  const propre = x => x.replace(/\s+/g, ' ').trim();
  const h1 = document.querySelector('h1');
  const fil = document.querySelector('.ariane [aria-current], .ariane li:last-child');
  const titres = [...document.querySelectorAll('h2')].map(x => propre(x.textContent));
  const compte = {};
  for (const t of titres) if (t) compte[t] = (compte[t] || 0) + 1;
  const niveaux = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(x => +x.tagName[1]);
  const sauts = [];
  for (let i = 1; i < niveaux.length; i++)
    if (niveaux[i] - niveaux[i-1] > 1) sauts.push('h' + niveaux[i-1] + '→h' + niveaux[i]);
  const coherence = {
    h1: h1 ? propre(h1.textContent) : null,
    fil: fil ? propre(fil.textContent) : null,
    // Le fil tronque les longs titres avec des points de suspension :
    // « 10 choses à ne pas faire… » sous « 10 choses à ne pas faire en
    // Égypte ! » n'est pas un fil emprunté, c'est le même titre abrégé.
    // Sans cette nuance la sonde criait au loup sur dix guides.
    filFaux: (() => {
      if (!h1 || !fil) return false;
      const a = propre(h1.textContent), b = propre(fil.textContent);
      if (a === b) return false;
      const nu = b.replace(/[…\.]+$/, '').trim();
      return !(nu && a.startsWith(nu));
    })(),
    h2Doubles: Object.entries(compte).filter(([, n]) => n > 1).map(([t, n]) => t.slice(0, 44) + ' ×' + n),
    sautsTitres: [...new Set(sauts)],
    liensMorts: [...new Set([...document.querySelectorAll('a[href]')]
      .map(a => a.getAttribute('href'))
      .filter(h => h && (h.endsWith('.html') || h === '#' || h === '')))].slice(0, 6),
    imgSansAlt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
  };

  const uniq = (a, k) => [...new Map(a.map(x => [k(x), x])).values()];
  return {structure, coherence,
    contraste: uniq(contraste, x => x.sel + x.ct),
    petits: uniq(petits, x => x.sel + x.px),
    cibles: uniq(cibles, x => x.sel + x.h)};
};

(async () => {
  const [dossier, prefixe, sortie] = process.argv.slice(2);
  const fichiers = fs.readdirSync(dossier)
    .filter(f => f.endsWith('.html') && (!prefixe || prefixe === '*' || f.startsWith(prefixe)))
    .sort();
  const b = await chromium.launch({args: ['--no-sandbox']});
  const out = [];
  for (const f of fichiers) {
    const ligne = {f};
    for (const [vue, ctx] of [['bureau', {viewport: {width: 1280, height: 900}}],
                              ['mobile', {...devices['Pixel 5']}]]) {
      const c = await b.newContext(ctx);
      const p = await c.newPage();
      await p.goto('file://' + path.join(dossier, f), {waitUntil: 'load'});
      await p.waitForTimeout(2200);
      ligne[vue] = await p.evaluate(MESURE);
      await c.close();
    }
    out.push(ligne);
    process.stderr.write('.');
  }
  await b.close();
  fs.writeFileSync(sortie, JSON.stringify(out, null, 1));
  process.stderr.write('\n');
  console.log(out.length);
})();
