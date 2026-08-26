#!/usr/bin/env python3
"""
Les 14 fiches séjour, coulées dans la maquette « produit-siwa ».

La maquette commande : hero, galerie, deux colonnes avec le panneau de
réservation collant, itinéraire jour par jour, inclusions, FAQ, séjours
sœurs, barre mobile. On ne remplace que le contenu.

Ce que la première version ratait, et pourquoi :
- les jours de l'itinéraire n'étaient pas regroupés — le site écrit un
  titre court (« Arrivée à Aswan ») suivi de ses détails, et tout
  partait dans une même liste plate ;
- les questions fréquentes (sections h3) tombaient au mauvais endroit ;
- le bloc de sœurs restait celui de Siwa sur les 14 fiches : l'ancre
  visée n'existait pas dans la maquette et l'échec était silencieux —
  les remplacements lèvent désormais une erreur quand l'ancre manque.
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
COCHE = ('<svg width="16" height="16" viewBox="0 0 17 17" fill="none" aria-hidden="true">'
         '<path d="M3 8.8l3.6 3.6L14 5" stroke="#0F6E73" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg> ')

ETAPES = re.compile(r'étapes|programme|itinéraire|déroul', re.I)
PRIX_SEUL = re.compile(r'^[AÀ]\s*partir\s*de', re.I)
# L'écriture du site : un titre d'étape est une phrase courte, sans
# point final, qui n'est ni une mention d'intendance ni une option.
PAS_TITRE = re.compile(r'^(en option|hébergement|nuit|dîner|déjeuner|petit-déjeuner|repas|note)\b', re.I)


def filename_alt(alt):
    """Un alt qui n'est qu'un nom de fichier ne fait pas une légende."""
    return not alt or 'unsplash' in alt.lower() or re.fullmatch(r'[\w-]+', alt) is not None


# ---------------------------------------------------------------- #
# Le tri des sections                                               #
# ---------------------------------------------------------------- #

def trier(x, titres_voyages):
    """Range les sections du séjour : intro, itinéraire, corps, FAQ."""
    intro, itineraire, corps, faq = [], [], [], []
    sous_titre = ''
    zone = 'intro'
    faq_ouverte = None

    for s in x['sections']:
        titre = (s['titre'] or '').strip()
        meme = titre.lower() == x['titre'].strip().lower()

        # Les queues de page du site : titres d'autres séjours, blocs
        # de prix, sections vides. On les écarte.
        if s['niveau'] == 2:
            if titre in titres_voyages and not meme:
                zone = 'fin'
                continue
            if s['blocs'] and all(b['type'] == 'p' and PRIX_SEUL.match(b['texte']) or b['type'] == 'liste'
                                  for b in s['blocs']) and any(PRIX_SEUL.match(b.get('texte', ''))
                                                               for b in s['blocs'] if b['type'] == 'p'):
                continue
            if not s['blocs']:
                if zone == 'intro' and titre and not meme and not sous_titre:
                    sous_titre = titre
                continue
            if ETAPES.search(titre):
                zone = 'itineraire'
                itineraire.append(s)
                continue
            if 'faq' in titre.lower():
                zone = 'faq'
                continue
            if zone == 'intro':
                intro.append(s)
            else:
                zone = 'corps'
                corps.append(s)
            continue

        if s['niveau'] == 3:
            if '?' in titre or zone == 'faq':
                faq.append({'q': titre, 'blocs': list(s['blocs'])})
                faq_ouverte = faq[-1]
                zone = 'faq'
            elif zone == 'itineraire':
                itineraire.append(s)
            else:
                corps.append(s)
            continue

        if s['niveau'] == 4 and faq_ouverte is not None:
            # Les sous-parties d'une réponse (🎒, 🏕…) restent dedans.
            if titre:
                faq_ouverte['blocs'].append({'type': 'p', 'texte': titre})
            faq_ouverte['blocs'] += s['blocs']
            continue

        if zone == 'intro' and s['blocs']:
            intro.append(s)

    return sous_titre, intro, itineraire, corps, faq


# ---------------------------------------------------------------- #
# Les briques de la maquette                                        #
# ---------------------------------------------------------------- #

def tete(x):
    return ('<div class="tete">\n<p class="eyebrow">Voyage sur mesure en Égypte</p>\n'
            '<h1>%s</h1>\n<p>%s</p>\n</div>' % (M.e(x['titre']), M.e(M.coupe(x['chapo'], 30))))


def galerie(x):
    images = x['_images'][:5]
    if not images:
        return ''
    out = ['<div class="galerie">']
    for n, im in enumerate(images):
        leg = ''
        if n == 0 and not filename_alt(im['alt']):
            leg = '<span class="galerie__leg">%s</span>' % M.e(im['alt'])
        out.append('<a href="%s"><img src="%s" alt="%s" %s decoding="async">%s</a>'
                   % (M.e(im['src']), M.e(im['src']), M.e(im['alt']),
                      'fetchpriority="high"' if n == 0 else 'loading="lazy"', leg))
    out.append('</div>')

    return '\n'.join(out)


def rendre_jours(sections):
    """L'itinéraire, dans le balisage .jour / .etape de la maquette."""
    jours = []

    def jour(titre):
        jours.append({'titre': titre, 'etapes': []})
        return jours[-1]

    # Le site marque ses étapes de deux façons : des titres d'accordéon
    # (<a tabindex>) quand la page est riche, de simples phrases courtes
    # sans point final sinon. Quand les titres existent, on ne devine pas.
    balises = any(b['type'] == 'titre_etape' for s in sections for b in s['blocs'])

    courant = None
    for s in sections:
        if s['niveau'] == 3:
            courant = jour(s['titre'])
        for b in s['blocs']:
            if b['type'] == 'titre_etape':
                courant = jour(b['texte'])
            elif b['type'] == 'p':
                t = b['texte']
                titre_like = not balises and ((len(t) <= 60 and not t.rstrip().endswith('.')
                              and not PAS_TITRE.match(t)) or re.match(r'^jour\s*\d', t, re.I))
                if titre_like:
                    courant = jour(t)
                else:
                    if courant is None:
                        courant = jour('')
                    courant['etapes'].append(('p', t))
            elif b['type'] == 'liste':
                if courant is None:
                    courant = jour('')
                courant['etapes'].append(('ul', b['items']))

    out = []
    for j in jours:
        dedans = []
        for genre, contenu in j['etapes']:
            if genre == 'p':
                dedans.append('<p>%s</p>' % M.e(contenu))
            else:
                dedans.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % M.e(i) for i in contenu))
        titre = ('<h4>%s</h4>' % M.e(j['titre'])) if j['titre'] else ''
        out.append('<div class="etape">%s%s</div>' % (titre, '\n'.join(dedans)))

    if not out:
        return ''

    return ('<div class="bloc-t">\n<p class="eyebrow">Le programme</p>\n'
            '<h2 style="margin-bottom:16px">Les étapes de votre séjour</h2>\n'
            '<div class="jour">\n%s\n</div>\n</div>' % '\n'.join(out))


def rendre_corps(sections):
    out = []
    for s in sections:
        if s['titre']:
            out.append('<div class="bloc-t"><h2 style="margin-bottom:14px">%s</h2>%s</div>'
                       % (M.e(s['titre']), M.paragraphes(s['blocs'], '')))
        else:
            out.append(M.paragraphes(s['blocs'], ''))

    return '\n'.join(out)


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


def rendre_faq(faq):
    if not faq:
        return ''
    out = []
    for n, q in enumerate(faq):
        out.append('<details%s><summary>%s</summary><div class="faq__c">%s</div></details>'
                   % (' open' if n == 0 else '', M.e(q['q']), M.paragraphes(q['blocs'], '')))

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
            '<a href="%s" class="btn btn--wa btn--bloc btn--sm">Écrire sur WhatsApp</a></div>\n'
            '<p class="note" style="margin:12px 0 0;text-align:center">Devis gratuit · réponse sous 48 h '
            '(hors vendredi et samedi)</p>\n</div>'
            % (prix, ''.join('<li>%s%s</li>' % (COCHE, M.e(p)) for p in puces), DEVIS, WHATSAPP))


def soeurs(x, tous):
    autres = [a for a in tous if a['id'] != x['id']][:3]
    cartes = []
    for a in autres:
        img = a['_images'][0] if a['_images'] else None
        cartes.append(
            '<article class="carte">'
            '<div class="carte__img"><img src="%s" alt="%s" loading="lazy" decoding="async"></div>'
            '<div class="carte__corps"><h3><a href="%s">%s</a></h3>'
            '<p class="carte__route">%s</p>'
            '<div class="carte__pied"><span class="prix"><small>À partir de</small><b>%s</b></span>'
            '<a href="%s" class="lien-fl">Découvrir</a></div></div></article>'
            % (M.e(img['src'] if img else ''), M.e((img['alt'] if img and not filename_alt(img['alt']) else a['titre'])),
               M.e(a['url']), M.e(a['titre']), M.e(a['duree'] or 'Sur mesure'),
               M.e(a['prix'] or '—'), M.e(a['url'])))

    return ('<section class="section">\n<div class="wrap">\n'
            '<p class="eyebrow">Et aussi</p>\n'
            '<h2 style="margin-bottom:22px">Ce séjour se combine, ou se remplace</h2>\n'
            '<div class="grille g-3">%s</div>\n</div>\n</section>' % '\n'.join(cartes))


# ---------------------------------------------------------------- #
# Le montage                                                        #
# ---------------------------------------------------------------- #

def rendre(x, tous, titres_voyages):
    page = M.moule('produit-siwa.html')
    page = M.entete_html(page, x['titre'], M.coupe(x['chapo'], 26))
    page = M.poser_style(page)

    page = M.remplacer(page, 'class="tete"', tete(x))
    g = galerie(x)
    page = M.remplacer(page, 'class="galerie"', g) if g else M.vider(page, 'class="galerie"')

    sous_titre, intro, itin, corps, faq = trier(x, titres_voyages)

    colonne = [M.bandeau_source(x['url']),
               '<p class="eyebrow">Vue d\'ensemble</p>']
    if sous_titre:
        colonne.append('<h2 style="margin-bottom:14px">%s</h2>' % M.e(sous_titre))
    for s in intro:
        if s['titre'] and s['titre'].strip().lower() not in ('vue d\'ensemble', x['titre'].strip().lower()):
            colonne.append('<h3 style="margin-top:22px">%s</h3>' % M.e(s['titre']))
        colonne.append(M.paragraphes(s['blocs']))
    colonne.append(rendre_jours(itin))
    colonne.append(rendre_corps(corps))
    colonne.append(inclusions(x))
    colonne.append(rendre_faq(faq))

    b = M.bornes(page, 'class="colonnes"')
    interieur = page[b[0]:b[1]]
    premier = M.bornes(interieur, '<div>')
    interieur = (interieur[:premier[0]] + '<div>\n' + '\n'.join(c for c in colonne if c)
                 + '\n</div>' + interieur[premier[1]:])
    page = page[:b[0]] + interieur + page[b[1]:]

    page = M.remplacer(page, 'class="resa"', resa(x))
    page = M.remplacer(page, 'class="resa-mob"',
                       '<div class="resa-mob"><span class="p"><small>%s</small><b>%s</b> <i>/ pers.</i></span>'
                       '<a href="%s" class="btn btn--or btn--sm">Personnaliser</a></div>'
                       % (M.e(M.coupe(x['titre'], 4)), M.e(x['prix'] or 'Sur devis'), DEVIS))

    # Le bloc de sœurs : la section dont le titre contient « se combine ».
    ancre = page.index('se combine, ou se remplace')
    deb = page.rfind('<section', 0, ancre)
    fin = page.index('</section>', ancre) + len('</section>')
    page = page[:deb] + soeurs(x, tous) + page[fin:]

    return page


def main():
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

    lot = [extraits[i['id']] for i in inventaire if i['gabarit'] == 'voyage']
    titres = {v['titre'].strip() for v in lot}
    os.makedirs(SORTIE, exist_ok=True)
    for x in lot:
        slug = next(i['slug'] for i in inventaire if i['id'] == x['id'])
        with open(os.path.join(SORTIE, 'voyage-%s.html' % slug[:60]), 'w', encoding='utf-8') as f:
            f.write(rendre(x, lot, titres))
    print('%d fiches séjour coulées dans produit-siwa.html' % len(lot))


if __name__ == '__main__':
    main()
