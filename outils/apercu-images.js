#!/usr/bin/env node
/*
  Réduit des photos et les rend en data: URI, pour la copie autoportante
  d'une page (voir outils/apercu-artifact.py).

  L'aperçu publié n'a le droit de charger que SES PROPRES fichiers : les
  photos servies par le site de la cliente y sont bloquées, et la page
  arrive sans une seule image. Elles doivent donc voyager DANS la page.

  Telles quelles, elles pèsent 15 Mo. On les redessine à la largeur
  utile — jamais au-delà de leur taille réelle, une image réduite ne
  redevient pas nette — et on les encode en WebP. Le redimensionnement
  passe par le canvas de Chromium : c'est le seul décodeur d'images
  disponible ici, et il lit le WebP comme le JPEG.

    node outils/apercu-images.js <demandes.json> <sortie.json>

  demandes.json : [{ "url": "...", "fichier": "/tmp/imgcache/…", "largeur": 1400 }]
  sortie.json   : { "<url>": "data:image/webp;base64,…" }
*/
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');

(async () => {
  const [entree, sortie] = process.argv.slice(2);
  if (!entree || !sortie) { console.error('usage : apercu-images.js <demandes.json> <sortie.json>'); process.exit(2); }
  const demandes = JSON.parse(fs.readFileSync(entree, 'utf8'));

  const nav = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await nav.newPage();
  await page.goto('about:blank');

  const table = {};
  let poids = 0;
  for (const d of demandes) {
    if (!fs.existsSync(d.fichier)) { console.error('   absente du cache : ' + d.url); continue; }
    const brut = fs.readFileSync(d.fichier).toString('base64');
    const type = /\.png$/i.test(d.url) ? 'image/png' : /\.webp$/i.test(d.url) ? 'image/webp' : 'image/jpeg';
    const uri = await page.evaluate(async ([b64, mime, largeur, qualite]) => {
      const img = new Image();
      await new Promise(ok => { img.onload = ok; img.onerror = ok; img.src = `data:${mime};base64,` + b64; });
      if (!img.width) return null;
      // Jamais au-delà de la taille réelle : agrandir ne rend rien.
      const l = Math.min(largeur, img.naturalWidth);
      const h = Math.round(img.naturalHeight * (l / img.naturalWidth));
      const c = document.createElement('canvas');
      c.width = l; c.height = h;
      const ctx = c.getContext('2d');
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, l, h);
      return c.toDataURL('image/webp', qualite);
    }, [brut, type, d.largeur || 1400, d.qualite || 0.82]);
    if (!uri || uri.length < 100) { console.error('   illisible : ' + d.url); continue; }
    table[d.url] = uri;
    poids += uri.length;
  }
  await nav.close();

  fs.writeFileSync(sortie, JSON.stringify(table));
  console.log('%d image(s) embarquée(s), %d Ko', Object.keys(table).length, Math.round(poids / 1024));
})();
