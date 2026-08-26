#!/usr/bin/env python3
"""
Les 14 fiches séjour, coulées dans la maquette « produit-siwa ».

C'est la maquette qui commande : hero, galerie, deux colonnes avec le
panneau de réservation collant, itinéraire jour par jour, inclusions,
FAQ, séjours sœurs, barre de réservation mobile. On ne remplace que le
contenu.
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
COCHE = ('<svg width="16" height="16" viewBox="0 0 17 17" fill="none" aria-hidden="true">'
         '<path d="M3 8.8l3.6 3.6L14 5" stroke="#0F6E73" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg> ')

ETAPES = re.compile(r"(étapes|programme|itinéraire|déroul|jour\s*\d)", re.I)


def tete(x):
    return ('<div class="tete">\n'
            '<p class="eyebrow">Voyage sur mesure en Égypte</p>\n'
            '<h1>%s</h1>\n<p>%s</p>\n</div>' % (M.e(x['titre']), M.e(M.coupe(x['chapo'], 32))))


def galerie(x, cassees):
    images = [i for i in x['images'] if i['src'] not in cassees][:5]
    if not images:
        return ''
    out = ['<div class="galerie">']
    for n, im in enumerate(images):
        leg = ('<span class="galerie__leg">%s</span>' % M.e(im['alt'])) if (n == 0 and im['alt']) else ''
        out.append('<a href="%s"><img src="%s" alt="%s" %s decoding="async">%s</a>' % (
            M.e(im['src']), M.e(im['src']), M.e(im['alt']),
            'fetchpriority="high"' if n == 0 else 'loading="lazy"', leg))
    out.append('</div>')

    return '\n'.join(out)


def itineraire(section):
    """Les étapes, dans le balisage .jour / .etape de la maquette."""
    etapes = []
    for b in section['blocs']:
        if b['type'] != 'p':
            continue
        texte = b['texte']
        # La première phrase fait le titre de l'étape, le reste le corps.
        coupure = re.match(r'(.{10,120}?[.!?])\s+(.+)', texte, re.S)
        if coupure:
            etapes.append('<div class="etape"><h4>%s</h4><p>%s</p></div>'
                          % (M.e(coupure.group(1)), M.e(coupure.group(2))))
        else:
            etapes.append('<div class="etape"><p>%s</p></div>' % M.e(texte))
    listes = [b for b in section['blocs'] if b['type'] == 'liste']
    puces = ''.join('<ul>%s</ul>' % ''.join('<li>%s</li>' % M.e(i) for i in b['items'])
                    for b in listes)
    if not etapes and not puces:
        return ''

    return ('<div class="bloc-t">\n<p class="eyebrow">Le programme</p>\n'
            '<h2 style="margin-bottom:16px">%s</h2>\n<div class="jour">\n%s\n%s</div>\n</div>'
            % (M.e(section['titre'].rstrip(' :')), '\n'.join(etapes), puces))


def inclusions(x):
    if not x['inclus'] and not x['exclus']:
        return ''
    gauche = ('<div><h3 style="color:var(--teal-txt)">Le programme inclut</h3><ul class="oui">%s</ul></div>'
              % ''.join('<li>%s</li>' % M.e(i) for i in x['inclus'])) if x['inclus'] else '<div></div>'
    droite = ('<div><h3 style="color:var(--gris)">N\'inclut pas</h3><ul class="non">%s</ul></div>'
              % ''.join('<li>%s</li>' % M.e(i) for i in x['exclus'])) if x['exclus'] else '<div></div>'

    return ('<div class="bloc-t">\n<p class="eyebrow">Ce qui est compris</p>\n'
            '<h2 style="margin-bottom:16px">Le détail du prix</h2>\n'
            '<div class="incl">%s%s</div>\n</div>' % (gauche, droite))


def faq(sections):
    """Les sections en h3 tiennent lieu de questions, comme sur la maquette."""
    questions = [s for s in sections if s['niveau'] == 3 and s['blocs']]
    if not questions:
        return ''
    out = []
    for n, s in enumerate(questions):
        out.append('<details%s><summary>%s</summary><div class="faq__c">%s</div></details>'
                   % (' open' if n == 0 else '', M.e(s['titre']), M.paragraphes(s['blocs'], '')))

    return ('<div class="bloc-t">\n<p class="eyebrow">Bon à savoir</p>\n'
            '<h2 style="margin-bottom:16px">Ce qu\'on nous demande le plus</h2>\n'
            '<div class="faq">%s</div>\n</div>' % '\n'.join(out))


def resa(x):
    puces = []
    if x['duree']:
        puces.append(x['duree'] + ' minimum')
    puces += ['Guide privatif francophone', 'Chauffeur et véhicule sécurisé', 'Itinéraire modifiable']
    prix = ('<p class="prix" style="margin:0 0 2px"><small>À partir de</small><b>%s</b> <i>/ personne</i></p>'
            % M.e(x['prix'])) if x['prix'] else \
           '<p class="prix" style="margin:0 0 2px"><b class="aremplir">Prix à confirmer</b></p>'

    return ('<div class="resa" data-mm="Bloc de conversion · collant">\n%s\n<ul>%s</ul>\n'
            '<div class="act"><a href="%s" class="btn btn--or btn--bloc">Personnaliser ce séjour</a>\n'
            '<a href="https://wa.me/201066619098" class="btn btn--wa btn--bloc btn--sm">Écrire sur WhatsApp</a></div>\n'
            '<p class="note" style="margin:12px 0 0;text-align:center">Devis gratuit · réponse sous 48 h '
            '(hors vendredi et samedi)</p>\n</div>'
            % (prix, ''.join('<li>%s%s</li>' % (COCHE, M.e(p)) for p in puces), DEVIS))


def soeurs(x, tous):
    """Les autres séjours, en cartes — le bloc de sœurs de la maquette."""
    autres = [a for a in tous if a['id'] != x['id']][:3]
    if not autres:
        return ''
    cartes = []
    for a in autres:
        img = a['images'][0]['src'] if a['images'] else ''
        cartes.append(
            '<article class="carte">'
            '<div class="carte__img"><img src="%s" alt="%s" loading="lazy" decoding="async"></div>'
            '<div class="carte__corps"><h3>%s</h3>'
            '<p class="carte__route">%s</p></div>'
            '<div class="carte__pied"><span class="prix"><small>À partir de</small><b>%s</b></span>'
            '<a href="%s" class="lien-fl">Découvrir</a></div></article>'
            % (M.e(img), M.e(a['images'][0]['alt'] if a['images'] else a['titre']),
               M.e(a['titre']), M.e(a['duree'] or 'Sur mesure'),
               M.e(a['prix'] or '—'), M.e(a['url'])))

    return ('<section class="section">\n<div class="wrap">\n'
            '<p class="eyebrow">Et aussi</p>\n'
            '<h2 style="margin-bottom:22px">Nos autres séjours</h2>\n'
            '<div class="grille g-3">%s</div>\n</div>\n</section>' % '\n'.join(cartes))


def rendre(x, tous, cassees):
    page = M.moule('produit-siwa.html')
    page = M.entete_html(page, x['titre'], M.coupe(x['chapo'], 26))
    page = M.poser_style(page)

    # Le fil d'Ariane et le hero.
    page = M.remplacer(page, 'class="tete"', tete(x))
    g = galerie(x, cassees)
    page = M.remplacer(page, 'class="galerie"', g) if g else M.vider(page, 'class="galerie"')

    # La colonne de gauche, refaite de bout en bout.
    corps = [M.bandeau_source(x['url'])]
    intro = [s for s in x['sections'] if s['blocs'] and not ETAPES.search(s['titre'] or '')
             and s['niveau'] == 2]
    if intro:
        corps.append('<p class="eyebrow">Vue d\'ensemble</p>')
        corps.append('<h2 style="margin-bottom:14px">%s</h2>' % M.e(intro[0]['titre'] or x['titre']))
        for s in intro:
            if s is not intro[0] and s['titre']:
                corps.append('<h3 style="margin-top:26px">%s</h3>' % M.e(s['titre']))
            corps.append(M.paragraphes(s['blocs']))
    for s in x['sections']:
        if s['niveau'] == 2 and ETAPES.search(s['titre'] or '') and s['blocs']:
            corps.append(itineraire(s))
    corps.append(inclusions(x))
    corps.append(faq(x['sections']))

    b = M.bornes(page, 'class="colonnes"')
    interieur = page[b[0]:b[1]]
    premier = M.bornes(interieur, '<div>')
    interieur = interieur[:premier[0]] + '<div>\n' + '\n'.join(c for c in corps if c) + '\n</div>' + interieur[premier[1]:]
    page = page[:b[0]] + interieur + page[b[1]:]

    page = M.remplacer(page, 'class="resa"', resa(x))
    page = M.remplacer(page, 'class="resa-mob"',
                       '<div class="resa-mob"><span class="p"><small>%s</small><b>%s</b> <i>/ pers.</i></span>'
                       '<a href="%s" class="btn btn--or btn--sm">Personnaliser</a></div>'
                       % (M.e(M.coupe(x['titre'], 4)), M.e(x['prix'] or 'Sur devis'), DEVIS))

    # Le bloc de sœurs, avec les vrais autres séjours.
    b = M.bornes(page, 'class="grille g-3"')
    if b:
        s = soeurs(x, tous)
        deb = page.rfind('<section', 0, b[0])
        fin = page.index('</section>', b[1]) + len('</section>')
        page = page[:deb] + s + page[fin:]

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

    lot = [extraits[i['id']] for i in inventaire if i['gabarit'] == 'voyage']
    os.makedirs(SORTIE, exist_ok=True)
    for x in lot:
        slug = next(i['slug'] for i in inventaire if i['id'] == x['id'])
        with open(os.path.join(SORTIE, 'voyage-%s.html' % slug[:60]), 'w', encoding='utf-8') as f:
            f.write(rendre(x, lot, cassees))
    print('%d fiches séjour coulées dans la maquette produit-siwa.' % len(lot))


if __name__ == '__main__':
    main()
