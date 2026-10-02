#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trois derniers détails, dont un qui se voit.

    WP_AUTH='compte:mot de passe' ./outils/derniers-details.py [--essai]

1. Une plaque grise derrière le logo. La feuille pose
   `img{background:var(--fond)}` sur toutes les images — une réserve
   utile pendant le chargement, sauf derrière un PNG transparent. Le
   logo est transparent, et le fond du gabarit vaut #F9F9FB : sur un
   en-tête blanc, cela dessine un rectangle gris pâle autour du logo.
   Sur les 58 pages, en-tête et pied. Le logo seul repasse en
   transparent, les autres images gardent leur réserve.

2. Un saut de niveau de titre sur « Les arnaques et erreurs à éviter ».
   Les sections de cette page alternent h2 et h3 ; deux d'entre elles —
   « Les balades à cheval et à dos de dromadaire » et « Les magasins de
   papyrus » — sont en h4, entre deux h2. C'est le seul saut de niveau
   des 58 pages, et il casse le plan de lecture autant pour un lecteur
   d'écran que pour un moteur.

3. Le titre de cette même page finit sur un deux-points orphelin :
   « Les arnaques et erreurs à éviter en Égypte : ». Il est repris tel
   quel dans le fil d'Ariane et sur la carte du blog.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
H = '.elementor-template-canvas' * 6 + ' '
MARQUE = 'data-det1="1"'

# On vise le fichier du logo plutôt qu'un conteneur : il paraît dans un
# <a class="logo"> en haut et dans un <div> nu en bas.
FEUILLE = ('<style ' + MARQUE + '>'
           + H + '.logo img,' + H + 'img[src*="Logo_authentique"]'
           '{background:transparent}'
           '</style>')

ARNAQUES = 8942
# Deux sections au mauvais niveau, et le deux-points de trop.
NIVEAUX = [('<h4 id="s7">', '<h3 id="s7">'), ('<h4 id="s8">', '<h3 id="s8">')]
TITRE = ('Les arnaques et erreurs à éviter en Égypte :',
         'Les arnaques et erreurs à éviter en Égypte')


def _fermer(h, ouvre, ferme, depuis):
    """Referme la balise ouverte en `depuis`, en comptant la profondeur."""
    p = 0
    for m in re.finditer(r'<(/?)h[34]\b[^>]*>', h[depuis:]):
        p += 1 if not m.group(1) else -1
        if p == 0:
            return depuis + m.start(), depuis + m.end()
    return -1, -1


def corriger(h, pid):
    faits = []
    if MARQUE not in h and 'Logo_authentique' in h:
        h += FEUILLE
        faits.append('plaque du logo retirée')
    if pid == ARNAQUES:
        for av, ap in NIVEAUX:
            i = h.find(av)
            if i < 0:
                continue
            d, f = _fermer(h, 'h4', '</h4>', i)
            if d < 0:
                continue
            h = h[:i] + ap + h[i + len(av):d] + '</h3>' + h[f:]
            faits.append('niveau de titre rendu')
        for a in (TITRE[0], TITRE[0].replace(' ', ' '),
                  TITRE[0].replace(' :', ' :'), TITRE[0].replace(' ', '&nbsp;')):
            if a in h:
                h = h.replace(a, TITRE[1])
                faits.append('deux-points orphelin retiré')
                break
    return h, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        n += 1
        print('   #%-6d %-30s %s'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:30], ' · '.join(faits)[:62]))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if not corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                       relu['content']['raw']), k['id'])[1]:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) %s.' % (n, 'à finir' if a.essai else 'finie(s)'))


if __name__ == '__main__':
    main()
