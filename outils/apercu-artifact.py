#!/usr/bin/env python3
"""Une copie AUTOPORTANTE d'une page, pour la montrer en ligne.

Deux choses empêchent une page produite de s'afficher ailleurs que sur
le site :

1. **la charte** est appelée par un chemin relatif (`assets/charte.css`).
   Juste sur le disque, introuvable partout ailleurs : la page perd
   toute sa mise en forme et n'affiche qu'une colonne de liens nus ;
2. **les photos** sont servies par le site de la cliente. Un aperçu
   publié n'a le droit de charger que ses propres fichiers : la page
   arrive sans une seule image.

Ce script fabrique la copie à montrer : la charte entre dans la page,
les photos aussi — réduites à la largeur utile et encodées en WebP par
`outils/apercu-images.js`, jamais agrandies. Le `srcset` disparaît, une
seule définition par image suffit à un aperçu.

Rien d'autre ne change : la copie ne sert qu'à REGARDER, la page livrée
reste celle de `maquettes/`.

    outils/apercu-artifact.py maquettes/site/programme-<slug>.html
    APERCU_SORTIE=/tmp/x outils/apercu-artifact.py <page> [autre…]
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTE = os.path.join(RACINE, 'maquettes', 'assets', 'charte.css')
CACHE = os.environ.get('IMGCACHE') or '/tmp/imgcache'
SORTIE = os.environ.get('APERCU_SORTIE') or '/tmp'
PHOTO = re.compile(r'https://authentiquegypte\.com/wp-content/uploads/[^\s"\',)]+')

# La largeur utile d'une photo dans l'aperçu. Le bandeau tient toute la
# fenêtre, les autres photos vivent dans une colonne de 780 px : les
# servir en 2560 px ne rendrait pas l'aperçu plus net, seulement plus
# lourd — et le poids d'une page publiée est borné.
LARGE, COURANT = 1600, 1100


def cache_de(url):
    return os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())


def telecharger(urls):
    os.makedirs(CACHE, exist_ok=True)
    manquantes = [u for u in urls if not os.path.exists(cache_de(u))]
    for i, u in enumerate(manquantes, 1):
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (apercu)'})
            with urllib.request.urlopen(req, timeout=90) as r, open(cache_de(u), 'wb') as f:
                f.write(r.read())
        except Exception as err:
            print('   introuvable : %s (%s)' % (u.rsplit('/', 1)[-1], err))
    if manquantes:
        print('   %d photo(s) relevée(s) sur le site' % len(manquantes))


def uris(page):
    """Les photos de la page, réduites, en data: URI."""
    urls = sorted(set(PHOTO.findall(page)))
    if not urls:
        return {}
    telecharger(urls)
    # Le bandeau est le seul plein écran ; on le reconnaît à son
    # fetchpriority. Tout le reste vit dans une colonne.
    unes = set(re.findall(r'<img[^>]+src="(%s)"[^>]*fetchpriority' % PHOTO.pattern, page))
    demandes = [{'url': u, 'fichier': cache_de(u),
                 'largeur': LARGE if u in unes else COURANT}
                for u in urls if os.path.exists(cache_de(u))]
    if not demandes:
        return {}
    dossier = os.path.join(SORTIE, '_apercu')
    os.makedirs(dossier, exist_ok=True)
    avec = os.path.join(dossier, 'demandes.json')
    vers = os.path.join(dossier, 'uris.json')
    with open(avec, 'w', encoding='utf-8') as f:
        json.dump(demandes, f)
    subprocess.run(['node', os.path.join(RACINE, 'outils', 'apercu-images.js'), avec, vers],
                   check=True)
    with open(vers, encoding='utf-8') as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        sys.exit('usage : apercu-artifact.py <page.html> [autre.html …]')
    with open(CHARTE, encoding='utf-8') as f:
        charte = f.read()

    for chemin in sys.argv[1:]:
        with open(chemin, encoding='utf-8') as f:
            page = f.read()

        page, n = re.subn(r'<link rel="stylesheet" href="[^"]*charte\.css">',
                          '<style>\n/* charte du site, intégrée pour l\'aperçu */\n'
                          + charte + '\n</style>', page)
        if not n:
            sys.exit('%s : aucun appel à la charte' % chemin)

        print(os.path.basename(chemin))
        # Le srcset part D'ABORD : une seule définition par image suffit
        # à un aperçu, et embarquer les cinq variantes de chaque photo
        # multipliait le poids par quatre — 65 fichiers au lieu de 16.
        page = re.sub(r'\s+srcset="[^"]*"', '', page)
        page = re.sub(r'\s+sizes="[^"]*"', '', page)
        table = uris(page)
        for url, uri in sorted(table.items(), key=lambda kv: -len(kv[0])):
            page = page.replace(url, uri)
        restantes = len(set(PHOTO.findall(page)))
        if restantes:
            print('   %d photo(s) encore servies par le site' % restantes)

        cible = os.path.join(SORTIE, os.path.basename(chemin))
        with open(cible, 'w', encoding='utf-8') as f:
            f.write(page)
        print('   %s — %d Ko' % (cible, os.path.getsize(cible) // 1024))


if __name__ == '__main__':
    main()
