#!/usr/bin/env python3
"""
Catégories, destinations, « qui part », agence, accueil, légal et hub,
coulés dans les maquettes de référence — sections comprises.

La version précédente gardait les sections de fin de maquette telles
quelles : une catégorie « Croisières » parlait du désert et de Bahariya,
un Louxor affichait « Les séjours qui passent par Le Caire ». Ici,
chaque section propre au gabarit est reconstruite avec les données de
la page : ses séjours (relevés dans les liens de la page en ligne), ses
sœurs, ses images.

Ce qu'on ne sait pas, on ne l'invente pas : une section sans donnée est
omise, pas remplie au jugé.
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
WHATSAPP = 'https://wa.me/201066619098'
FLECHE = ('<svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">'
          '<path d="M1 5.5h12M9 1.5l4 4-4 4" stroke="currentColor" stroke-width="1.7" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')

# Quel fichier de maquette sert de moule à quel gabarit.
MOULE = {
    'categorie':   'categorie-desert.html',
    'qui-part':    'categorie-desert.html',
    'destination': 'destination.html',
    'agence':      'destination.html',
    'accueil':     'destination.html',
    'legal':       'destination.html',
    'guide':       'article-quand-partir.html',
    'hub-guides':  'article-quand-partir.html',
}

ARIANE = {
    'categorie':   ('https://authentiquegypte.com/nos-sejours-egypte/', 'Nos séjours en Égypte'),
    'qui-part':    ('../index.html', 'Qui part'),
    'destination': ('../index.html', 'Destinations'),
    'agence':      ('../index.html', 'L’agence'),
    'accueil':     ('../index.html', 'Accueil'),
    'legal':       ('../index.html', 'Informations légales'),
    'guide':       ('https://authentiquegypte.com/notre-blog/', 'Guides pratiques'),
    'hub-guides':  ('https://authentiquegypte.com/notre-blog/', 'Guides pratiques'),
}


def nom_court(titre):
    """« Voyage à Louxor » → « Louxor », pour les titres de sections."""
    t = re.sub(r'^(voyages?\s+(à|au|aux|en|dans\s+l[ae’\']s?|sur\s+le)\s+)', '', titre, flags=re.I)
    t = re.sub(r'\s*[—:|].*$', '', t)

    return t.strip() or titre


# ---------------------------------------------------------------- #
# Les briques, dans le balisage exact des maquettes                  #
# ---------------------------------------------------------------- #

def chapeau(x, gabarit, chips, remonte=None):
    lien, nom = ARIANE[gabarit]
    valides = x['_images']
    fond = ('<div class="chapeau__bg"><img src="%s" alt="" fetchpriority="high" decoding="async"></div>'
            % M.e(valides[0]['src'])) if valides else ''
    st = ''
    if chips:
        st = '<div class="chapeau__st">%s</div>' % ''.join(
            '<span><b>%s</b> %s</span>' % (M.e(b), M.e(t)) for b, t in chips)
    rem = ''
    if remonte:
        rem = ('<a class="remonte" href="%s">%s %s</a>' % (M.e(remonte[0]), M.e(remonte[1]), FLECHE))

    return ('<section class="chapeau">\n%s\n<div class="wrap">\n'
            '<nav class="ariane" aria-label="Fil d\'Ariane"><ol>\n'
            '<li><a href="../index.html">Accueil</a></li>\n'
            '<li><a href="%s">%s</a></li>\n'
            '<li><span aria-current="page">%s</span></li>\n</ol></nav>\n'
            '<h1>%s</h1>\n<p class="sous">%s</p>\n%s\n%s</div>\n</section>'
            % (fond, M.e(lien), M.e(nom), M.e(M.coupe(x['titre'], 6)),
               M.e(x['titre']), M.e(x['chapo']), st, rem))


def carte_sejour(v):
    """Une carte de séjour, comme sur la maquette catégorie."""
    img = v['images'][0] if v['images'] else None
    meta = ('<span class="puce">%s</span>' % M.e(v['duree'])) if v['duree'] else ''
    prix = ('<span class="prix"><small>À partir de</small><b>%s</b> <i>/ pers.</i></span>'
            % M.e(v['prix'])) if v['prix'] else '<span class="prix"><b>Sur devis</b></span>'

    return ('<article class="carte">\n'
            '<div class="carte__img"><img src="%s" alt="%s" loading="lazy" decoding="async"></div>\n'
            '<div class="carte__corps">\n<h3><a href="%s">%s</a></h3>\n'
            '<p class="carte__route">%s</p>\n'
            '<div class="carte__meta">%s</div>\n'
            '<div class="carte__pied">\n%s\n'
            '<a href="%s" class="lien-fl" aria-label="Voir le détail : %s">Voir le détail %s</a>\n'
            '</div>\n</div>\n</article>'
            % (M.e(img['src'] if img else ''), M.e(img['alt'] if img else v['titre']),
               M.e(v['url']), M.e(v['titre']),
               M.e(M.coupe(v['chapo'], 14)), meta, prix,
               M.e(v['url']), M.e(v['titre']), FLECHE))


def section_sejours(x, sejours, titre, eyebrow='Nos séjours'):
    if not sejours:
        return ''
    cartes = '\n'.join(carte_sejour(v) for v in sejours[:6])

    return ('<section class="section section--fond">\n<div class="wrap">\n'
            '<p class="eyebrow">%s</p>\n'
            '<h2 style="margin-bottom:14px">%s</h2>\n'
            '<p class="lede" style="margin-bottom:30px">Tous personnalisables&nbsp;: la durée '
            's\'ajuste à ce que vous voulez voir.</p>\n'
            '<div class="grille g-3">\n%s\n</div>\n</div>\n</section>'
            % (M.e(eyebrow), M.e(titre), cartes))


def carte_soeur(s):
    img = s['_images'][0] if s['_images'] else None
    prix = ('<span class="prix"><small>À partir de</small><b>%s</b></span>' % M.e(s['_prix_min'])) \
        if s.get('_prix_min') else '<span></span>'

    return ('<a class="carte" href="%s">\n'
            '<div class="carte__img"><img src="%s" alt="%s" loading="lazy" decoding="async"></div>\n'
            '<div class="carte__corps"><h3>%s</h3><p class="carte__route">%s</p>\n'
            '<div class="carte__pied">%s<span class="lien-fl">Découvrir %s</span></div></div>\n</a>'
            % (M.e(s['url']), M.e(img['src'] if img else ''),
               M.e(img['alt'] if img else s['titre']), M.e(s['titre']),
               M.e(M.coupe(s['chapo'], 10)), prix, FLECHE))


def section_soeurs(titre, eyebrow, phrase, soeurs):
    if not soeurs:
        return ''

    return ('<section class="section">\n<div class="wrap">\n'
            '<p class="eyebrow">%s</p>\n<h2 style="margin-bottom:14px">%s</h2>\n'
            '<p class="lede" style="margin-bottom:32px">%s</p>\n'
            '<div class="grille g-4">\n%s\n</div>\n</div>\n</section>'
            % (M.e(eyebrow), M.e(titre), M.e(phrase),
               '\n'.join(carte_soeur(s) for s in soeurs[:4])))


def sections_propres(x, ctx):
    """Les sections de la page, débarrassées des cartes de séjours que
    le site recopie en pied de page (leurs titres sont ceux des
    voyages) et du chapô déjà affiché dans le chapeau."""
    titres_voyages = ctx.get('titres_voyages', set())
    sortie = []
    for s in x['sections']:
        titre = (s['titre'] or '').strip()
        if titre in titres_voyages:
            continue
        blocs = [b for b in s['blocs'] if b.get('texte', '').strip() != x['chapo'].strip()]
        if blocs:
            sortie.append(dict(s, blocs=blocs))

    return sortie


def corps_editorial(x, ctx, creme=True):
    """Le texte de la page, dans une section pleine largeur."""
    sections = sections_propres(x, ctx)
    if not sections:
        return ''
    out = [M.bandeau_source(x['url'])]
    for s in sections:
        if s['titre'] and s['titre'].strip().lower() != x['titre'].strip().lower():
            out.append('<h%d>%s</h%d>' % (max(s['niveau'], 2), M.e(s['titre']), max(s['niveau'], 2)))
        out.append(M.paragraphes(s['blocs'], ''))

    return ('<section class="section%s">\n<div class="wrap">\n'
            '<div style="max-width:74ch">\n%s\n</div>\n</div>\n</section>'
            % (' section--creme' if creme else '', '\n'.join(out)))


def barre_mob():
    return ('<div class="barre-mob">\n'
            '<a href="%s" class="btn btn--fantome btn--sm" style="flex:0 0 auto">WhatsApp</a>\n'
            '<a href="%s" class="btn btn--or" style="flex:1">Demander mon devis</a>\n</div>'
            % (WHATSAPP, DEVIS))


# ---------------------------------------------------------------- #
# Le montage : tête et pied de la maquette, sections à nous          #
# ---------------------------------------------------------------- #

def monter(gabarit, x, sections_main):
    """Tout ce qui n'est pas <main> vient du moule, intact."""
    page = M.moule(MOULE[gabarit])
    # Les pages générées vivent un cran plus bas que les maquettes :
    # sans ce raccord, la charte liée ne se résout plus — ni en local,
    # ni à la conversion WordPress, qui inline les feuilles locales.
    page = page.replace('href="assets/charte.css"', 'href="../assets/charte.css"')
    page = M.entete_html(page, x['titre'], M.coupe(x['chapo'], 26))
    page = M.poser_style(page)

    debut = page.index('<main')
    debut = page.index('>', debut) + 1
    fin = page.index('</main>')
    ouverture = page[page.index('<main'):debut]

    corps = '\n'.join(s for s in sections_main if s)

    page = page[:page.index('<main')] + ouverture + '\n' + corps + '\n' + page[fin:]

    # La barre mobile vit hors du <main> dans les moules ; on la garde
    # telle quelle si elle y est, on l'ajoute sinon.
    if 'barre-mob' not in page:
        page = page.replace('<footer class="pied">', barre_mob() + '\n<footer class="pied">', 1)

    return page


# ---------------------------------------------------------------- #
# Un montage par gabarit                                            #
# ---------------------------------------------------------------- #

def page_categorie(x, ctx, gabarit):
    sejours = ctx['sejours'].get(x['slug'], [])
    chips = []
    if sejours:
        chips.append((str(len(sejours)), 'séjour%s' % ('s' if len(sejours) > 1 else '')))
        jours = sorted(int(re.match(r'(\d+)', v['duree']).group(1)) for v in sejours if v['duree'])
        if jours:
            chips.append(('%d à %d' % (jours[0], jours[-1]) if jours[0] != jours[-1] else str(jours[0]), 'jours'))
        prix = sorted(int(re.sub(r'\D', '', v['prix'])) for v in sejours if v['prix'])
        if prix:
            chips.append(('%d €' % prix[0], 'à partir de'))

    nc = nom_court(x['titre'])
    if gabarit == 'categorie':
        remonte = (ARIANE['categorie'][0], 'Une des cinq familles de nos séjours en Égypte')
        soeurs = [s for s in ctx['categories'] if s['id'] != x['id'] and s['slug'] != 'nos-sejours-egypte']
        titre_soeurs, eyebrow_s = '%s se combine bien' % nc, 'Autres types de séjours'
        phrase = 'Quelques jours s\'ajoutent facilement à un autre de nos séjours.'
    else:
        remonte = None
        soeurs = [s for s in ctx['qui_part'] if s['id'] != x['id']]
        titre_soeurs, eyebrow_s = 'Les autres façons de partir', 'Qui part'
        phrase = 'Famille, couple, solo ou mobilité réduite : chaque profil a sa page.'

    return monter(gabarit, x, [
        chapeau(x, gabarit, chips, remonte),
        corps_editorial(x, ctx),
        section_sejours(x, sejours, 'Les séjours %s' % (('« %s »' % nc) if gabarit == 'qui-part' else nc.lower()),
                        'Nos séjours' if gabarit == 'categorie' else 'Passer du profil au voyage'),
        section_soeurs(titre_soeurs, eyebrow_s, phrase, soeurs),
    ])


def flanc_destination(x, ctx, sejours):
    """L'aside collant de la maquette destination — le « sticky »."""
    nc = nom_court(x['titre'])
    bref = ''
    lignes = []
    if x['duree']:
        lignes.append(('Durée conseillée', x['duree']))
    if sejours:
        lignes.append(('Séjours qui y passent', str(len(sejours))))
    if lignes:
        bref = ('<div class="lat__b">\n<h4>%s en bref</h4>\n<dl>%s</dl>\n</div>'
                % (M.e(nc), ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (M.e(a), M.e(b))
                                    for a, b in lignes)))
    autres = ''.join(
        '<li><a href="%s">%s %s</a></li>' % (M.e(s['url']), M.e(s['titre']), FLECHE)
        for s in ctx['destinations'] if s['id'] != x['id'])[:2000]

    return ('<aside>\n<div class="lat">\n'
            '<div class="lat__b lat--devis">\n<h4>%s, à votre rythme</h4>\n'
            '<p>Dites-nous combien de jours vous avez&nbsp;: nous vous disons ce qui tient '
            'dedans, et ce qui n\'y tient pas.</p>\n'
            '<a href="%s" class="btn btn--or btn--bloc btn--sm">Demander mon devis</a>\n'
            '<a href="%s" class="btn btn--clair btn--bloc btn--sm" style="margin-top:9px">WhatsApp</a>\n'
            '</div>\n%s\n<div class="lat__b">\n<h4>Autres destinations</h4>\n<ul>%s</ul>\n</div>\n'
            '</div>\n</aside>' % (M.e(nc), DEVIS, WHATSAPP, bref, autres))


def corps_destination(x, ctx):
    """Le corps deux-colonnes : les sections de la page, les sections
    illustrées en blocs .site comme sur la maquette."""
    sections = sections_propres(x, ctx)
    images = list(x['_images'][1:])
    out = [M.bandeau_source(x['url'])]
    sites, libres = [], []
    for s in sections:
        illustrable = s['titre'] and images and len(s['blocs']) <= 6
        if illustrable:
            im = images.pop(0)
            sites.append('<article class="site">\n'
                         '<img src="%s" alt="%s" loading="lazy" decoding="async">\n'
                         '<div class="site__t">\n<h3>%s</h3>\n%s\n</div>\n</article>'
                         % (M.e(im['src']), M.e(im['alt'] or s['titre']),
                            M.e(s['titre']), M.paragraphes(s['blocs'], '')))
        else:
            libres.append((s['titre'], s))
    if sites:
        out.append('<div class="sites">\n%s\n</div>' % '\n'.join(sites))
    for titre, s in libres:
        if titre and titre.strip().lower() != x['titre'].strip().lower():
            out.append('<h%d>%s</h%d>' % (max(s['niveau'], 2), M.e(titre), max(s['niveau'], 2)))
        out.append(M.paragraphes(s['blocs'], ''))

    return '<article class="corps">\n%s\n</article>' % '\n'.join(out)


def page_destination(x, ctx, gabarit):
    sejours = ctx['sejours'].get(x['slug'], [])
    nc = nom_court(x['titre'])
    chips = []
    if x['duree']:
        chips.append((x['duree'], 'conseillés'))
    if sejours:
        chips.append((str(len(sejours)), 'séjour%s y passe%s' % (('s', 'nt') if len(sejours) > 1 else ('', ''))))

    if gabarit == 'destination':
        flanc = flanc_destination(x, ctx, sejours)
        soeurs = [s for s in ctx['destinations'] if s['id'] != x['id']]
        queue = [
            section_sejours(x, sejours, 'Les séjours qui passent par %s' % nc, 'Passer du guide au voyage'),
            section_soeurs('%s se combine bien' % nc, 'Poursuivre le voyage',
                           'Les distances comptent : voici ce qui s\'ajoute sans casser le rythme.', soeurs),
        ]
    else:
        # agence, accueil, légal : le même moule, sans les blocs séjours.
        flanc = '' if gabarit == 'legal' else (
            '<aside>\n<div class="lat">\n<div class="lat__b lat--devis">\n'
            '<h4>Un projet de voyage&nbsp;?</h4>\n'
            '<p>Nous construisons l\'itinéraire avec vous, selon vos dates et votre rythme.</p>\n'
            '<a href="%s" class="btn btn--or btn--bloc btn--sm">Demander mon devis</a>\n'
            '<a href="%s" class="btn btn--clair btn--bloc btn--sm" style="margin-top:9px">WhatsApp</a>\n'
            '</div>\n</div>\n</aside>' % (DEVIS, WHATSAPP))
        queue = []

    colonnes = ('<div class="wrap">\n<div class="colonnes">\n%s\n%s\n</div>\n</div>'
                % (corps_destination(x, ctx), flanc))

    return monter(gabarit, x, [chapeau(x, gabarit, chips)] + [colonnes] + queue)


def page_guide(x, ctx, gabarit):
    """Le gabarit guide n'a pas changé : chapeau, sommaire .som, corps."""
    sections = [s for s in x['sections'] if s['blocs']]
    images = list(x['_images'][1:])
    base, reste = divmod(len(images), max(len(sections), 1))
    som = ''
    titres = [(n, s['titre']) for n, s in enumerate(sections) if s['titre']]
    if len(titres) >= 3:
        som = ('<nav class="som" aria-label="Sommaire"><h4>Sur cette page</h4><ol>%s</ol></nav>'
               % ''.join('<li><a href="#s%d">%s</a></li>' % (n, M.e(t)) for n, t in titres))
    out = [M.bandeau_source(x['url'])]
    for n, s in enumerate(sections):
        if s['titre'] and s['titre'].strip().lower() != x['titre'].strip().lower():
            out.append('<h%d id="s%d">%s</h%d>' % (max(s['niveau'], 2), n, M.e(s['titre']), max(s['niveau'], 2)))
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
    art = ('<div class="wrap">\n<div class="art">\n%s\n<article class="corps">\n%s\n</article>\n</div>\n</div>'
           % (som, '\n'.join(out)))

    # Le moule garde sa section de fin « Les autres guides » : on ne
    # remonte que le chapeau et le corps.
    page = M.moule(MOULE[gabarit])
    page = page.replace('href="assets/charte.css"', 'href="../assets/charte.css"')
    page = M.entete_html(page, x['titre'], M.coupe(x['chapo'], 26))
    page = M.poser_style(page)
    page = M.remplacer(page, 'class="chapeau"', chapeau(x, gabarit, []))
    depart = page.index('</section>', page.index('class="chapeau"'))
    b = M.bornes(page, '<div class="wrap">', depart)
    return page[:b[0]] + art + page[b[1]:]


MONTAGES = {
    'categorie': page_categorie, 'qui-part': page_categorie,
    'destination': page_destination, 'agence': page_destination,
    'accueil': page_destination, 'legal': page_destination,
    'guide': page_guide, 'hub-guides': page_guide,
}


# ---------------------------------------------------------------- #
# Les données                                                       #
# ---------------------------------------------------------------- #

def charger():
    with open(os.path.join(RACINE, 'docs', 'extraits.json'), encoding='utf-8') as f:
        extraits = {x['id']: x for x in json.load(f)}
    with open(os.path.join(RACINE, 'docs', 'inventaire.json'), encoding='utf-8') as f:
        inventaire = json.load(f)
    cassees = set()
    chemin = os.path.join(RACINE, 'docs', 'images-cassees.txt')
    if os.path.exists(chemin):
        with open(chemin, encoding='utf-8') as f:
            cassees = {l.strip() for l in f if l.strip() and not l.startswith('#')}

    for x in extraits.values():
        x['_images'] = [i for i in x['images'] if i['src'] not in cassees]

    # Quels séjours chaque page relie-t-elle ? On lit les liens de la
    # page en ligne : c'est la donnée du site, pas une supposition.
    voyages = {}
    for it in inventaire:
        if it['gabarit'] == 'voyage':
            voyages[it['slug']] = extraits[it['id']]
    sejours = {}
    brut_chemin = os.path.join(RACINE, 'docs', 'contenus.json')
    if os.path.exists(brut_chemin):
        with open(brut_chemin, encoding='utf-8') as f:
            brut = json.load(f)
        for p in brut.get('pages', []):
            raw = (p.get('content', {}) or {}).get('raw', '') or ''
            vus = []
            for m in re.finditer(r'/programs/([a-z0-9-]+)/?', raw):
                if m.group(1) in voyages and m.group(1) not in vus:
                    vus.append(m.group(1))
            sejours[p.get('slug', '')] = [voyages[s] for s in vus]

    gabarits = {}
    for it in inventaire:
        gabarits.setdefault(it['gabarit'], []).append(extraits[it['id']])

    # Le prix plancher d'une famille, pour la carte de sœur.
    for cat in gabarits.get('categorie', []):
        slug = next(i['slug'] for i in inventaire if i['id'] == cat['id'])
        prix = sorted(int(re.sub(r'\D', '', v['prix'])) for v in sejours.get(slug, []) if v['prix'])
        cat['_prix_min'] = ('%d €' % prix[0]) if prix else ''

    return extraits, inventaire, {
        'titres_voyages': {v['titre'].strip() for v in voyages.values()},
        'sejours': sejours,
        'categories': [c for c in gabarits.get('categorie', [])],
        'destinations': gabarits.get('destination', []),
        'qui_part': gabarits.get('qui-part', []),
    }


def main():
    extraits, inventaire, ctx = charger()
    os.makedirs(SORTIE, exist_ok=True)
    compte = {}
    for it in inventaire:
        g = it['gabarit']
        if g not in MONTAGES:
            continue
        x = extraits[it['id']]
        if not x['sections']:
            continue
        with open(os.path.join(SORTIE, '%s-%s.html' % (g, it['slug'][:60])), 'w', encoding='utf-8') as f:
            f.write(MONTAGES[g](x, ctx, g))
        compte[g] = compte.get(g, 0) + 1
    for g, n in sorted(compte.items()):
        print('  %-14s %2d pages, moule %s' % (g, n, MOULE[g]))


if __name__ == '__main__':
    main()
