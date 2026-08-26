#!/usr/bin/env python3
"""
Déploie les 59 pages reprises du site, en BROUILLON, rangées par gabarit.

Rien de ce qui est en ligne n'est touché : ni page, ni menu, ni
redirection, ni réglage. Chaque page est une fille d'un dossier de
gabarit, lui-même fils de « Refonte 2026 ». Le rangement du back-office
reflète ainsi le classement, sans qu'on ait à le tenir à la main.

    WP_AUTH="identifiant:mot de passe" ./outils/deployer-site.py
    ... --gabarit voyage      ne déploie qu'un gabarit
"""

import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, 'outils'))

from importlib.machinery import SourceFileLoader

dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
conv = SourceFileLoader('conv', os.path.join(RACINE, 'outils', 'vers-page-wp.py')).load_module()

SITE_DIR = os.path.join(RACINE, 'maquettes', 'site')

# Un dossier par gabarit, dans l'ordre où on les lit.
DOSSIERS = [
    ('voyage',      'Refonte · Séjours'),
    ('categorie',   'Refonte · Catégories de séjours'),
    ('destination', 'Refonte · Destinations'),
    ('qui-part',    'Refonte · Qui part'),
    ('guide',       'Refonte · Guides'),
    ('hub-guides',  'Refonte · Pages diverses'),
    ('agence',      'Refonte · Pages diverses'),
    ('accueil',     'Refonte · Pages diverses'),
    ('legal',       'Refonte · Pages diverses'),
]


def main():
    vise = None
    if '--gabarit' in sys.argv:
        vise = sys.argv[sys.argv.index('--gabarit') + 1]

    with open(os.path.join(RACINE, 'docs', 'inventaire.json'), encoding='utf-8') as f:
        inventaire = json.load(f)
    par_id = {x['id']: x for x in inventaire}

    print('→ Blocs communs')
    dep.controler_blocs()
    print('   entête et pied identiques')

    print('→ Page mère')
    mere, action = dep.poser_page(dep.PARENT_SLUG, {
        'title': dep.PARENT_TITRE, 'status': 'draft',
    })
    print('   %s — id %d (%s)' % (dep.PARENT_TITRE, mere['id'], action))

    # Un dossier par gabarit. Quatre gabarits partagent le même dossier
    # — un pour chacun aurait donné quatre dossiers d'une seule page.
    print('→ Dossiers de gabarit')
    pages_dossier, dossiers = {}, {}
    for gabarit, titre in DOSSIERS:
        if titre not in pages_dossier:
            slug = re.sub(r'[^a-z0-9]+', '-', titre.lower()).strip('-')
            page, action = dep.poser_page(slug, {
                'title': titre, 'status': 'draft', 'parent': mere['id'],
                'content': ('<!-- wp:paragraph --><p>Pages reprises du site, en brouillon. '
                            'Elles ne remplacent aucune page en ligne.</p><!-- /wp:paragraph -->'),
            })
            pages_dossier[titre] = page
            print('   %-40s id %d (%s)' % (titre, page['id'], action))
        dossiers[gabarit] = pages_dossier[titre]

    # Les fichiers générés, dans l'ordre des dossiers.
    print('→ Pages')
    faits, octets = 0, 0
    for gabarit, _ in DOSSIERS:
        if vise and gabarit != vise:
            continue
        lot = [x for x in inventaire if x['gabarit'] == gabarit]
        for item in sorted(lot, key=lambda x: x['slug']):
            fichier = os.path.join(SITE_DIR, '%s-%s.html' % (gabarit, item['slug'][:60]))
            if not os.path.exists(fichier):
                continue
            with open(fichier, encoding='utf-8') as f:
                contenu = conv.convertir(f.read(), os.path.dirname(fichier))
            # Le gabarit entre dans le slug : « mer-rouge » existe deux
            # fois sur le site, une fois comme catégorie et une fois
            # comme séjour. Sans lui, la seconde écrase la première.
            page, action = dep.poser_page('refonte-%s-%s' % (gabarit, item['slug'][:48]), {
                'title': 'Refonte · %s' % item['titre'][:120],
                'status': 'draft',
                'parent': dossiers[gabarit]['id'],
                'template': 'elementor_canvas',
                'content': contenu,
            })
            faits += 1
            octets += len(contenu)
            print('   %-11s %-44s id %-6d %s' % (gabarit, item['slug'][:44], page['id'], action))

    print('\n%d pages déployées, %s octets. Toutes en BROUILLON.' % (faits, '{:,}'.format(octets).replace(',', ' ')))
    print('Aucune page existante n\'a été modifiée.')


if __name__ == '__main__':
    main()
