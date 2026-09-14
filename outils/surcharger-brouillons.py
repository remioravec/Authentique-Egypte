#!/usr/bin/env python3
"""
Injecte une feuille de surcharge CSS dans des brouillons de refonte déjà
posés, sans toucher à leur titre, leur rangement ni leur statut.

    WP_AUTH='compte:mot de passe d application' \\
        ./outils/surcharger-brouillons.py --css maquettes/surcharges/texte-large.css \\
            slug-du-brouillon=chemin/de/la/source.html [...]

La source est la maquette HTML dont le brouillon a été produit ; la feuille
est posée juste avant </head>, puis la page est reconvertie par
outils/vers-page-wp.py exactement comme au premier dépôt. Seul le champ
« content » du brouillon est réécrit. Rien de ce qui est en ligne n'est
touché.
"""

import argparse
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from importlib.machinery import SourceFileLoader

dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
ranger = SourceFileLoader('ranger', os.path.join(RACINE, 'outils', 'ranger-brouillons.py')).load_module()


def injecter(html, css, ident='texte-large'):
    """Pose (ou remplace) le bloc <style id=…> juste avant </head>."""
    import re
    html = re.sub(r'<style id="%s">.*?</style>\n' % ident, '', html, flags=re.S)
    assert html.count('</head>') == 1, 'un seul </head> attendu'
    return html.replace('</head>', '<style id="%s">\n%s</style>\n</head>' % (ident, css))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--css', required=True, help='feuille de surcharge à injecter')
    p.add_argument('--id', default='texte-large', help='identifiant du bloc <style> (défaut : texte-large)')
    p.add_argument('--dossier', default='', help='dossier des feuilles locales (défaut : celui de la source)')
    p.add_argument('pages', nargs='+', help='slug=chemin/source.html')
    a = p.parse_args()

    with open(a.css, encoding='utf-8') as f:
        css = f.read()

    liens = dict(ranger.LIENS_LIVE)
    for etape in dep.PARCOURS:
        page = dep.trouver_page(etape['slug'])
        if page:
            liens[etape['fichier']] = '%s/?page_id=%d' % (dep.SITE, page['id'])

    for spec in a.pages:
        slug, source = spec.split('=', 1)
        page = dep.trouver_page(slug)
        if not page:
            print('   %-58s introuvable, ignoré' % slug, flush=True)
            continue
        if page.get('status') != 'draft':
            print('   %-58s id %-6d statut %s : on ne touche pas' % (slug, page['id'], page.get('status')), flush=True)
            continue
        with open(source, encoding='utf-8', errors='replace') as f:
            brut = f.read()
        debut = brut.find('<!DOCTYPE html>', 10)
        html = brut[debut:] if debut > 0 else brut
        html = html.rsplit('</html>', 1)[0] + '</html>'
        tmp = os.path.join(os.path.dirname(os.path.abspath(source)), '.surcharge-' + os.path.basename(source))
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(injecter(html, css, a.id))
        try:
            contenu = ranger.contenu_wp(tmp, liens, a.dossier or os.path.dirname(os.path.abspath(source)))
        finally:
            os.remove(tmp)
        res = dep.appel('POST', '/pages/%d' % page['id'], {'content': contenu})
        print('   %-58s id %-6d %-7s %7d o' % (slug[:58], res['id'], res.get('status'), len(contenu)), flush=True)


if __name__ == '__main__':
    main()
