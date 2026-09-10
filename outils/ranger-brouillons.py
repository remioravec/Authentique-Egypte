#!/usr/bin/env python3
"""
Range la zone « Refonte 2026 » du back-office comme elle l'était, et y
ajoute les pages produites depuis, toutes en BROUILLON.

    WP_AUTH='compte:mot de passe d application' \\
        ./outils/ranger-brouillons.py --site /chemin/vers/maquettes/site \\
            [--accueil-artefact fichier.html] [--seulement programme,famille]

Dossiers posés sous « Refonte 2026 » :

    Refonte · Maquettes de référence   la HOME (7643), la page programme
                                       « UX concurrent » et le circuit test
    Refonte · Programmes               les 14 fiches du gabarit « programme »
    Refonte · Types de séjour          les 6 pages « famille »
    Refonte · Séjours / Catégories de séjours / Destinations / Qui part /
    Guides / Pages diverses            les 59 pages reprises du site, comme
                                       au déploiement d'août

Rien de ce qui est en ligne n'est touché : ni page publiée, ni menu, ni
redirection. Le script est idempotent, la reconnaissance se fait sur le
slug ; les pages mises à la corbeille (slug suffixé « __trashed ») ne sont
ni retrouvées ni restaurées, une page neuve est posée à leur place.
"""

import argparse
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, 'outils'))
from importlib.machinery import SourceFileLoader

dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
conv = SourceFileLoader('conv', os.path.join(RACINE, 'outils', 'vers-page-wp.py')).load_module()

# Les liens relatifs des entêtes et pieds de maquette, vers les pages en
# ligne correspondantes (mêmes cibles que outils/gabarit-programme.py).
LIENS_LIVE = {
    'index.html': 'https://authentiquegypte.com/',
    'qui-sommes-nous.html': 'https://authentiquegypte.com/qui-sommes-nous/',
    'devis.html': 'https://authentiquegypte.com/sur-mesure/',
    'blog.html': 'https://authentiquegypte.com/notre-blog/',
    'categorie.html': 'https://authentiquegypte.com/nos-sejours-egypte/croisieres-en-egypte/',
    'categorie-desert.html': 'https://authentiquegypte.com/nos-sejours-egypte/desert-egypte/',
    'destination.html': 'https://authentiquegypte.com/voyage-au-caire/',
    'article-quand-partir.html': 'https://authentiquegypte.com/quand-partir-en-egypte/',
    'produit-siwa.html': 'https://authentiquegypte.com/programs/excursion-a-loasis-de-siwa/',
}

# (gabarit du fichier, préfixe de slug, dossier)
FAMILLES = [
    ('programme',   'programme',   'Refonte · Programmes'),
    ('famille',     'famille',     'Refonte · Types de séjour'),
    ('voyage',      'voyage',      'Refonte · Séjours'),
    ('categorie',   'categorie',   'Refonte · Catégories de séjours'),
    ('destination', 'destination', 'Refonte · Destinations'),
    ('qui-part',    'qui-part',    'Refonte · Qui part'),
    ('guide',       'guide',       'Refonte · Guides'),
    ('hub-guides',  'hub-guides',  'Refonte · Pages diverses'),
    ('agence',      'agence',      'Refonte · Pages diverses'),
    ('accueil',     'accueil',     'Refonte · Pages diverses'),
    ('legal',       'legal',       'Refonte · Pages diverses'),
]
# Les fichiers « programme » et « famille » portent le slug d'une fiche
# de l'inventaire d'un autre gabarit : c'est là qu'on lit leur titre.
TITRES_DANS = {'programme': 'voyage', 'famille': 'categorie'}
REFERENCE = 'Refonte · Maquettes de référence'


def slug_dossier(titre):
    return re.sub(r'[^a-z0-9]+', '-', titre.lower()).strip('-')


def contenu_wp(chemin, liens, dossier=None):
    with open(chemin, encoding='utf-8') as f:
        html = f.read()
    contenu = conv.convertir(html, dossier or os.path.dirname(chemin))
    for fichier, url in liens.items():
        contenu = contenu.replace('href="%s"' % fichier, 'href="%s"' % url)
        contenu = contenu.replace('href="../%s"' % fichier, 'href="%s"' % url)
    return contenu


def poser(slug, titre, parent, contenu, rang=0):
    page, action = dep.poser_page(slug, {
        'title': titre, 'status': 'draft', 'parent': parent,
        'menu_order': rang, 'template': 'elementor_canvas', 'content': contenu,
    })
    print('   %-58s id %-6d %-11s %7d o' % (slug[:58], page['id'], action, len(contenu)), flush=True)
    return page


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True, help='dossier des pages générées (maquettes/site)')
    p.add_argument('--inventaire', default='', help='docs/inventaire.json à utiliser (défaut : celui à côté de --site)')
    p.add_argument('--accueil-artefact', default='', help="HTML de l'accueil publié en artefact, à poser tel quel")
    p.add_argument('--seulement', default='', help='gabarits à traiter, séparés par des virgules')
    p.add_argument('--sans-reference', action='store_true', help='ne pas toucher au dossier des maquettes de référence')
    a = p.parse_args()

    site = os.path.abspath(a.site)
    inventaire_path = a.inventaire or os.path.join(os.path.dirname(os.path.dirname(site)), 'docs', 'inventaire.json')
    with open(inventaire_path, encoding='utf-8') as f:
        inventaire = json.load(f)
    vise = set(a.seulement.split(',')) if a.seulement else None

    print('→ Page mère', flush=True)
    mere, action = dep.poser_page(dep.PARENT_SLUG, {'title': dep.PARENT_TITRE, 'status': 'draft'})
    print('   %s — id %d (%s)' % (dep.PARENT_TITRE, mere['id'], action), flush=True)

    # Les liens de l'entête et du pied : vers le brouillon quand il existe,
    # vers la page en ligne sinon.
    liens = dict(LIENS_LIVE)
    for etape in dep.PARCOURS:
        page = dep.trouver_page(etape['slug'])
        if page:
            liens[etape['fichier']] = '%s/?page_id=%d' % (dep.SITE, page['id'])

    print('→ Dossiers', flush=True)
    dossiers = {}
    for titre in [REFERENCE] + [t for _, _, t in FAMILLES]:
        if titre in dossiers:
            continue
        page, action = dep.poser_page(slug_dossier(titre), {
            'title': titre, 'status': 'draft', 'parent': mere['id'],
            'menu_order': len(dossiers) + 1,
            'content': ('<!-- wp:paragraph --><p>Pages de refonte, en brouillon. '
                        'Elles ne remplacent aucune page en ligne.</p><!-- /wp:paragraph -->'),
        })
        dossiers[titre] = page
        print('   %-36s id %-6d %s' % (titre, page['id'], action), flush=True)

    # ---- maquettes de référence : la HOME et les pages programme de ce dépôt
    if not a.sans_reference:
        print('→ Maquettes de référence', flush=True)
        ref = dossiers[REFERENCE]['id']
        for rang, slug in enumerate(('accueil', 'refonte-programme-oasis-de-siwa'), start=1):
            page = dep.trouver_page(slug)
            if page:
                dep.appel('POST', '/pages/%d' % page['id'], {'parent': ref, 'menu_order': rang})
                print('   %-58s id %-6d déplacée' % (slug, page['id']), flush=True)
        circuit = os.path.join(RACINE, 'maquettes', 'programme-alexandrie-abou-simbel.html')
        if os.path.exists(circuit):
            poser('refonte-circuit-test-alexandrie-abou-simbel',
                  "Refonte · Circuit test — D'Alexandrie à Abou Simbel (contenu concurrent, charte AE)",
                  ref, contenu_wp(circuit, liens), 3)

    # ---- les pages générées, famille par famille
    faits = 0
    for gabarit, prefixe, titre_dossier in FAMILLES:
        if vise and gabarit not in vise:
            continue
        source = TITRES_DANS.get(gabarit, gabarit)
        lot = sorted((x for x in inventaire if x['gabarit'] == source), key=lambda x: x['slug'])
        fichiers = [(x, os.path.join(site, '%s-%s.html' % (gabarit, x['slug'][:60]))) for x in lot]
        fichiers = [(x, f) for x, f in fichiers if os.path.exists(f)]
        if not fichiers:
            continue
        print('→ %s (%d)' % (titre_dossier, len(fichiers)), flush=True)
        for rang, (item, fichier) in enumerate(fichiers, start=1):
            poser('refonte-%s-%s' % (prefixe, item['slug'][:48]),
                  'Refonte · %s' % item['titre'][:120],
                  dossiers[titre_dossier]['id'], contenu_wp(fichier, liens), rang)
            faits += 1

    # ---- l'accueil publié en artefact (pas encore dans le dépôt)
    if a.accueil_artefact:
        print('→ Accueil (artefact)', flush=True)
        with open(a.accueil_artefact, encoding='utf-8', errors='replace') as f:
            brut = f.read()
        debut = brut.find('<!DOCTYPE html>', 10)
        html = brut[debut:] if debut > 0 else brut
        html = html.rsplit('</html>', 1)[0] + '</html>'
        tmp = os.path.join(os.path.dirname(a.accueil_artefact), 'accueil-artefact-nettoye.html')
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(html)
        poser('refonte-accueil-version-artefact', 'Refonte · Accueil (version du 10/09, depuis l\'artefact)',
              dossiers['Refonte · Pages diverses']['id'], contenu_wp(tmp, liens, site), 99)
        faits += 1

    print('\n%d pages posées ou mises à jour. Toutes en BROUILLON, aucune page en ligne modifiée.' % faits)


if __name__ == '__main__':
    main()
