#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cinq retouches de mise en page, toutes mesurées d'abord.

    WP_AUTH='compte:mot de passe' ./outils/retouches-css.py [--essai]

1. Le héros ne couvre pas les grands écrans. La règle dit
   `width:min(100%,var(--une-l))`, et --une-l vaut la largeur du fichier
   source : 1280 px sur dix-neuf pages, 1024 px sur une. Au-delà, la
   photo s'arrête et laisse une bande de 80 à 450 px de chaque côté.
   Invisible à 1280 px — la largeur sur laquelle la passe du 29/09
   travaillait — voyante sur tout écran plus large. La photo prend
   désormais toute la largeur ; object-fit:cover était déjà là pour
   recadrer. Celles dont le fichier est petit seront un peu molles :
   c'est une photo à remplacer, pas une règle à écrire.

2. Les avis courts sont voilés sans raison. Le dégradé blanc qui annonce
   « ça continue plus bas » est posé sur tous les avis, y compris ceux
   qui tiennent entiers. Soixante-seize cartes sur deux cent quatre-vingts
   finissent donc en gris délavé sans qu'il y ait quoi que ce soit à
   lire de plus. Le voile ne paraît plus que sur les cartes marquées
   data-deborde, celles que le bouton « Lire la suite » ouvre vraiment.

3. L'itinéraire des cartes se coupe sur tablette et sur téléphone. Deux
   lignes pour « Le Caire → Louxor → Edfou → Kom Ombo → Abu Simbel →
   Assouan → Louxor » : la fin disparaît. Trois lignes sous 900 px.

4. Les étiquettes des filtres font trente-quatre pixels de haut. Le
   doigt en demande quarante-quatre.

5. « Lire la suite » et « Voir le détail » font vingt-quatre pixels.
   Même raison.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
# Le moule pose ses règles avec trois classes ou plus. On répète la classe
# hôte pour passer devant sans toucher au moule.
H = '.elementor-template-canvas' * 6 + ' '
MARQUE = 'data-css2="1"'

FEUILLE = (
    '<style ' + MARQUE + '>'
    # 1. le héros couvre, quelle que soit la largeur de l'écran
    + H + '.hero__fond img,' + H + '.hero__flou img'
    '{width:100%;min-width:100%;max-width:none}'
    # 2. le voile, seulement là où il y a vraiment une suite
    + H + '.mur__a blockquote::after{content:none}'
    + H + '.mur__a[data-deborde] blockquote::after{content:""}'
    # 5. de quoi poser le doigt
    + H + '.mur__plus{min-height:44px;display:none;align-items:center}'
    + H + '.mur__a[data-deborde] .mur__plus{display:inline-flex}'
    + H + '.lien-fl{display:inline-flex;align-items:center;min-height:44px}'
    '@media (max-width:900px){'
    # 3. l'itinéraire tient en trois lignes plutôt que deux
    + H + '.fac .carte__route,' + H + '.carte__route'
    '{-webkit-line-clamp:3}'
    # 4. l'étiquette de filtre fait la taille d'un doigt
    + H + '.fac__o{min-height:44px;padding-top:11px;padding-bottom:11px}'
    + H + '.fac__o input{width:22px;height:22px}'
    '}</style>')


def corriger(h):
    if MARQUE in h:
        return h, False
    # Rien à retoucher sur une page qui n'a ni héros, ni avis, ni filtre.
    if not any(x in h for x in ('hero__fond', 'mur__a', 'carte__route', 'fac__o')):
        return h, False
    return h + FEUILLE, True


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
        neuf, ok = corriger(brut)
        if not ok:
            continue
        n += 1
        print('   #%-6d %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:46]))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if not corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                       relu['content']['raw']))[1]:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) %s.' % (n, 'à retoucher' if a.essai else 'retouchée(s)'))


if __name__ == '__main__':
    main()
