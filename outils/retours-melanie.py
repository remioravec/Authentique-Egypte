#!/usr/bin/env python3
"""
Les retraits demandés par Mélanie dans la relecture, appliqués aux brouillons.

    WP_AUTH='compte:mot de passe' ./outils/retours-melanie.py [--essai]

Trois retraits, chacun adossé à un fil de la relecture du 23/09/2026.
Chacun est BORNÉ : Mélanie n'a pas demandé la même chose partout, et
appliquer sa remarque plus largement qu'elle ne l'a écrite, c'est décider
à sa place.

1. La note « Durées et prix relevés sur les fiches du site le 10 septembre
   2026 » (fil #9534, « ?? enlever »). C'est une note de travail, pas une
   phrase de la page. Partout où elle se trouve.

2. Le bandeau de repères des pages CIRCUIT (fils #9557, #9561, #9562,
   « enlever ce bandeau », dit deux fois sur deux pages différentes). Une
   page qui liste des séjours n'a ni prix ni durée propres.

3. Sur les pages DESTINATION, le seul repère de prix (fil #9515 : « enlever
   a partir de… on parle d'une destination, impossible de donner un
   prix »). La durée annoncée, elle, reste — Mélanie la corrige ailleurs,
   elle ne la retire pas.

Les pages PROGRAMME gardent leur bandeau entier : c'est là que le prix par
personne doit se voir, Rémi l'a demandé explicitement le 17/09.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

NOTE = re.compile(r'<p[^>]*class="[^"]*cartes__src[^"]*"[^>]*>[^<]*</p>')
BANDEAU = re.compile(r'<section class="reperes">.*?</section>', re.S)
PRIX = re.compile(r'<li\b(?:(?!</li>).)*?Par personne[^<]*(?:(?!</li>).)*?</li>', re.S)


def famille(slug):
    for prefixe, nom in (('refonte-famille-', 'circuit'),
                         ('refonte-destination-', 'destination'),
                         ('refonte-programme-', 'programme'),
                         ('refonte-qui-part-', 'profil')):
        if slug.startswith(prefixe):
            return nom
    return 'autre'


def corriger(h, quelle):
    """Rend (page, [ce qui a été retiré])."""
    faits = []
    h, n = NOTE.subn('', h)
    if n:
        faits.append('note de relevé ×%d' % n)

    if quelle == 'circuit':
        h, n = BANDEAU.subn('', h)
        if n:
            faits.append('bandeau de repères')
    elif quelle == 'destination':
        def sans_prix(m):
            bloc, k = PRIX.subn('', m.group(0))
            # Un bandeau dont il ne reste aucun repère n'a plus de raison
            # d'occuper une bande de l'écran.
            return '' if k and '<li' not in bloc else bloc
        h, n = BANDEAU.subn(sans_prix, h)
        if n:
            faits.append('repère de prix')
    return h, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true', help='mesurer sans rien écrire')
    a = p.parse_args()

    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    touchees = 0
    for k in pages:
        quelle = famille(k['slug'])
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, quelle)
        if not faits:
            continue
        touchees += 1
        print('   #%-6d %-11s %-40s %s'
              % (k['id'], quelle, (p_.get('title') or {}).get('raw', '')[:40],
                 ', '.join(faits)))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if not NOTE.search(relu['content']['raw']):
                    break
                print('      reprise %d/3' % (essai + 1))
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON, la page reste telle quelle')
    print('\n%d page(s) touchée(s).' % touchees)


if __name__ == '__main__':
    main()
