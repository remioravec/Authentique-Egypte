#!/usr/bin/env python3
"""
Guides, destinations, catégories et pages « qui part », coulés dans les
maquettes correspondantes.

Même principe que les fiches séjour : la maquette commande, on ne
remplace que le contenu. Le chapeau garde son image de fond et son fil
d'Ariane ; le corps est refait avec les sections de la page ; les blocs
de fin — autres guides, séjours qui passent par là — sont conservés.
"""

import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, 'outils'))
import moules as M

SORTIE = os.path.join(RACINE, 'maquettes', 'site')
DEVIS = 'https://authentiquegypte.com/sur-mesure/'

MOULES = {
    'guide':       ('article-quand-partir.html', 'Guide pratique',
                    'https://authentiquegypte.com/notre-blog/', 'Guides pratiques'),
    'destination': ('destination.html', 'Destination', 'index.html#destinations', 'Destinations'),
    'categorie':   ('categorie-desert.html', 'Nos séjours',
                    'https://authentiquegypte.com/nos-sejours-egypte/', 'Nos séjours en Égypte'),
    'qui-part':    ('categorie-desert.html', 'Qui part', 'index.html', 'Qui part'),
    'hub-guides':  ('article-quand-partir.html', 'Guides pratiques',
                    'https://authentiquegypte.com/notre-blog/', 'Guides pratiques'),
    'agence':      ('destination.html', 'L’agence', 'index.html', 'L’agence'),
    'accueil':     ('destination.html', 'Accueil', 'index.html', 'Accueil'),
    'legal':       ('destination.html', 'Informations légales', 'index.html', 'Légal'),
}


def chapeau(x, gabarit, cassees):
    _, surtitre, lien_parent, nom_parent = MOULES[gabarit]
    valides = [i for i in x['images'] if i['src'] not in cassees]
    fond = ('<div class="chapeau__bg"><img src="%s" alt="" fetchpriority="high" decoding="async"></div>'
            % M.e(valides[0]['src'])) if valides else ''

    return ('<section class="chapeau">\n%s\n<div class="wrap">\n'
            '<nav class="ariane" aria-label="Fil d\'Ariane"><ol>\n'
            '<li><a href="../index.html">Accueil</a></li>\n'
            '<li><a href="%s">%s</a></li>\n'
            '<li><span aria-current="page">%s</span></li>\n</ol></nav>\n'
            '<h1>%s</h1>\n<p class="sous">%s</p>\n</div>\n</section>'
            % (fond, M.e(lien_parent), M.e(nom_parent), M.e(M.coupe(x['titre'], 6)),
               M.e(x['titre']), M.e(x['chapo'])))


def sommaire(sections):
    titres = [(n, s['titre']) for n, s in enumerate(sections) if s['titre'] and s['blocs']]
    if len(titres) < 3:
        return ''

    return ('<nav class="som" aria-label="Sommaire"><h4>Sur cette page</h4><ol>%s</ol></nav>'
            % ''.join('<li><a href="#s%d">%s</a></li>' % (n, M.e(t)) for n, t in titres))


def corps(x, cassees):
    """Les sections de la page, dans la typographie de la maquette."""
    sections = [s for s in x['sections'] if s['blocs']]
    images = [i for i in x['images'] if i['src'] not in cassees][1:]
    base, reste = divmod(len(images), max(len(sections), 1))

    out = [M.bandeau_source(x['url']), sommaire(sections)]
    for n, s in enumerate(sections):
        if s['titre']:
            out.append('<h%d id="s%d">%s</h%d>' % (s['niveau'], n, M.e(s['titre']), s['niveau']))
        out.append(M.paragraphes(s['blocs'], 'lede' if n == 0 else ''))
        combien = base + (1 if n < reste else 0)
        lot = [images.pop(0) for _ in range(min(combien, len(images)))]
        if len(lot) == 1:
            im = lot[0]
            out.append('<figure class="fig"><img src="%s" alt="%s" loading="lazy" decoding="async">%s</figure>'
                       % (M.e(im['src']), M.e(im['alt']),
                          ('<figcaption>%s</figcaption>' % M.e(im['alt'])) if im['alt'] else ''))
        elif lot:
            out.append('<div class="bande">%s</div>' % ''.join(
                '<a href="%s"><img src="%s" alt="%s" loading="lazy" decoding="async"></a>'
                % (M.e(i['src']), M.e(i['src']), M.e(i['alt'])) for i in lot))

    out.append('<div class="encart">\n<h3>Envie de partir&nbsp;?</h3>\n'
               '<p>Nous construisons l\'itinéraire avec vous, selon vos dates et votre rythme. '
               'Réponse sous 48&nbsp;h, hors vendredi et samedi.</p>\n'
               '<p style="margin-top:14px"><a href="%s" class="btn btn--nuit btn--sm">Demander mon devis</a></p>\n'
               '</div>' % DEVIS)

    # .art enveloppe le sommaire et le corps, comme dans la maquette.
    som = sommaire(sections)
    reste = '\n'.join(c for c in out if c and c != som)

    return ('<div class="wrap">\n<div class="art">\n%s\n<article class="corps">\n%s\n</article>\n</div>\n</div>'
            % (som, reste))


def rendre(x, gabarit, cassees):
    fichier = MOULES[gabarit][0]
    page = M.moule(fichier)
    page = M.entete_html(page, x['titre'], M.coupe(x['chapo'], 26))
    page = M.poser_style(page)

    page = M.remplacer(page, 'class="chapeau"', chapeau(x, gabarit, cassees))

    # Le corps : le premier .wrap du <main> après le chapeau.
    depart = page.index('</section>', page.index('class="chapeau"'))
    b = M.bornes(page, '<div class="wrap">', depart)
    page = page[:b[0]] + corps(x, cassees) + page[b[1]:]

    return page


def main():
    with open(os.path.join(RACINE, 'docs', 'extraits.json'), encoding='utf-8') as f:
        extraits = {x['id']: x for x in json.load(f)}
    with open(os.path.join(RACINE, 'docs', 'inventaire.json'), encoding='utf-8') as f:
        inventaire = json.load(f)
    chemin = os.path.join(RACINE, 'docs', 'images-cassees.txt')
    cassees = set()
    if os.path.exists(chemin):
        with open(chemin, encoding='utf-8') as f:
            cassees = {l.strip() for l in f if l.strip() and not l.startswith('#')}

    os.makedirs(SORTIE, exist_ok=True)
    compte = {}
    for item in inventaire:
        g = item['gabarit']
        if g not in MOULES:
            continue
        x = extraits.get(item['id'])
        if not x or not x['sections']:
            continue
        with open(os.path.join(SORTIE, '%s-%s.html' % (g, item['slug'][:60])), 'w', encoding='utf-8') as f:
            f.write(rendre(x, g, cassees))
        compte[g] = compte.get(g, 0) + 1

    for g, n in sorted(compte.items()):
        print('  %-14s %2d pages coulées dans %s' % (g, n, MOULES[g][0]))


if __name__ == '__main__':
    main()
