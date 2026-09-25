#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les activités coup de cœur des familles, telles qu'elle les a listées.

    WP_AUTH='compte:mot de passe' ./outils/activites-familles.py [--essai]

#10456 : « mettre aussi nos activités coup de coeur pour les familles :
moments de felouque privative, atelier de hyérogpliphes, cours de
cuisine, balade en kayak, en quad, atelier de poterie, spectacle son et
lumières sur les différents sites ect », puis, dans le même fil :
« sandsurf aussi sympa et activités balnéaires sur la mer rouge ».

Ce sont ses mots, repris tels quels. Deux seules retouches, signalées
dans le fil : « hyérogpliphes » devient « hiéroglyphes », et le « ect »
de fin tombe puisque la liste est complète — elle l'a elle-même
complétée dans sa réponse.

Le bloc se pose après « Ce que les familles adorent » (#10451), qui dit
ce que le séjour garantit ; celui-ci dit ce qu'on peut y ajouter. Les
deux ne se recoupent pas.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
FAMILLE = 8927
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

ACTIVITES = [
    'Un moment de felouque privative',
    'Un atelier de hiéroglyphes',
    'Un cours de cuisine',
    'Une balade en kayak',
    'Une sortie en quad',
    'Un atelier de poterie',
    'Un spectacle son et lumières sur les sites',
    'Du sandsurf',
    'Des activités balnéaires sur la mer Rouge',
]

BLOC = ('<section class="pg-sec coups"><div class="wrap">'
        '<p class="eyebrow">À ajouter au séjour</p>'
        '<h2>Nos activités coup de cœur pour les familles</h2>'
        '<ul class="coups__l">%s</ul></div></section>'
        % ''.join('<li>%s</li>' % a for a in ACTIVITES))

FEUILLE = (
    '<style data-coups="1">'
    + E + '.pg .coups__l{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 0;'
    'padding:0;list-style:none}'
    + E + '.pg .coups__l li{background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:999px;padding:10px 18px;font-size:.95rem;'
    'color:var(--nuit-900,#095360);font-family:"Manrope",sans-serif;font-weight:600}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def corriger(h):
    if 'coups__l' in h:
        return h, False
    d = h.find('<section class="pg-sec adorent">')
    if d < 0:
        # Sans le bloc « ce que les familles adorent », on se pose après
        # la liste des séjours plutôt que n'importe où.
        d = h.find('<section class="pg-sec" id="sejours">')
        if d < 0:
            return h, False
    f = _fin(h, d, 'section')
    if f < 0:
        return h, False
    return h[:f] + BLOC + h[f:] + FEUILLE, True


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    p_ = dep.appel('GET', '/pages/%d?context=edit' % FAMILLE)
    brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
    neuf, fait = corriger(brut)
    if not fait:
        print('   déjà en place.')
        return
    print('   #%d  %s  →  %d activités' % (FAMILLE, p_['title']['raw'][:40], len(ACTIVITES)))
    if a.essai:
        return
    corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
    for essai in range(4):
        try:
            dep.appel('POST', '/pages/%d' % FAMILLE, {'content': corps})
            relu = dep.appel('GET', '/pages/%d?context=edit' % FAMILLE)
            if 'coups__l' in relu['content']['raw']:
                print('   posé et vérifié.')
                return
        except SystemExit as motif:
            print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
        time.sleep(2 ** essai)
    print('   ✗ ABANDON')


if __name__ == '__main__':
    main()
