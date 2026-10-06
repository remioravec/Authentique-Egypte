#!/usr/bin/env python3
"""Les séjours qui manquaient, et les durées qui se contredisaient.

    WP_AUTH='compte:mdp' python3 outils/retours-07-sejours.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-sejours.py --appliquer

Trois questions de Mélanie auxquelles le site répond lui-même, à condition de
compter :

12306 « il manque des programmes pouvez vous les ajouter » (Assouan). Six
    séjours passent par Assouan dans leur déroulé ; la page en montrait trois.
    Manquaient la croisière sur le lac Nasser, dont le jour 1 est l'arrivée à
    Assouan, et la croisière en bateau à voile, dont Assouan est la deuxième
    étape.

12283 « il y a un autre séjour avec Abu Simbel qui passe par le lac nasser ».
    Abou Simbel se dresse sur la rive ouest du lac. Deux séjours y conduisent
    en étape ferme : « Pyramides et croisière sur le Nil » et « Pyramides,
    croisière et mer rouge en famille ». Un troisième l'offre en option, on ne
    le compte pas.

12349 « il manque des itinéraires » (accueil). L'accueil en montrait huit sur
    les quatorze programmes publiés. Deux sont le même séjour en double
    (/programs/sainte-catherine/ et /programs/lever-du-soleil…/ ont le même
    titre et les mêmes étapes) et « Découverte de la Nubie » est encore dans
    l'ancienne maquette : on ne l'envoie pas sur l'accueil avant de l'avoir
    refaite. Restent quatre itinéraires à ajouter.

Et une incohérence que le contrôle qualité avait relevée : la durée annoncée
sur les cartes contredit le déroulé de la page. On prend le déroulé pour
référence, là seulement où il appartient bien au séjour. Deux pages gardent
leur durée telle quelle : /programs/mer-rouge/ et la croisière sur le lac
Nasser déroulent l'itinéraire d'un autre séjour, on ne va pas propager cette
erreur dans leur durée.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'

# ---------------------------------------------------------------- les durées
# Nombre de journées du déroulé de chaque programme, relevé sur sa page.
DUREE = {
    'le-caire-et-croisiere-sur-un-bateau-a-voile': 8,
    'pyramides-et-croisiere-sur-le-nil': 8,
    'excursion-dans-le-desert-blanc': 3,
    'excursion-a-loasis-de-fayoum': 2,
    'roadtrip-en-egypte': 9,
    'pyramides-louxor-et-mer-rouge-en-famille': 8,
}

TITRE = {
    'croisiere-sur-le-lac-nasser': 'Croisière sur le lac Nasser',
    'le-caire-et-croisiere-sur-un-bateau-a-voile':
        'Le Caire et croisière sur un bateau à voile',
    'pyramides-et-croisiere-sur-le-nil': 'Pyramides et croisière sur le Nil',
    'mer-rouge': 'Pyramides, croisière et mer rouge en famille',
    'excursion-a-loasis-de-fayoum': 'Excursion à l’Oasis de Fayoum',
    'excursion-a-loasis-de-siwa': 'Voyage à l’Oasis de Siwa',
    'excursion-dans-le-desert-blanc': 'Excursion dans le désert blanc',
    'roadtrip-en-egypte': 'Roadtrip en Égypte sur mesure',
    'pyramides-louxor-et-mer-rouge-en-famille':
        'Pyramides, Louxor et mer rouge en famille',
    'campement-au-coeur-du-mont-moise':
        'Coucher de soleil et nuit sur le mont Moïse',
    'sainte-catherine':
        'Lever du soleil, monastère et nuit à Sainte-Catherine',
    'itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge':
        'Du littoral de la mer Rouge aux montagnes du Sinaï',
}

# --------------------------------------------------------- ce qu'on ajoute
A_AJOUTER = {
    5210: ['croisiere-sur-le-lac-nasser',                  # 12306 · Assouan
           'le-caire-et-croisiere-sur-un-bateau-a-voile'],
    5556: ['pyramides-et-croisiere-sur-le-nil',            # 12283 · Lac Nasser
           'mer-rouge'],
}

# Les pages où l'on va chercher les cartes toutes faites, dans l'ordre.
RESERVOIR = (5191, 5201, 5210, 5556, 5547, 5532, 5229)

LEDE_NASSER = (
    '<p class="lede" style="margin:14px 0 30px">Abou Simbel se dresse sur la '
    'rive ouest du lac&nbsp;: on y accède en navigant, ou par la route depuis '
    'Assouan. Tous ces séjours sont personnalisables&nbsp;: la durée s\'ajuste '
    'à ce que vous voulez voir.</p>')

# ------------------------------------------------------------ cartes accueil
# Quatre itinéraires absents de l'accueil (12349). Mêmes facettes que les
# cartes déjà en place, images prises dans la médiathèque et non en base64 :
# la page pèse déjà 3,7 Mo.
ACCUEIL = [
    ('excursion-a-loasis-de-fayoum',
     'famille couple solo groupe amis', 'desert caire', 'court',
     '2023/11/peter-ragheb-naYLQxASRTE-unsplash-scaled.webp',
     'Désert dans l’Oasis de Fayoum',
     'Le Caire <b>→</b> Wadi El Rayan <b>→</b> Wadi Al-Hitan '
     '<b>→</b> Tunis Village',
     [('', '2 jours minimum'), ('teal', 'Vallée des baleines, UNESCO'),
      ('teal', 'Pistes en 4x4')],
     'À partir de', '185 €'),
    ('roadtrip-en-egypte',
     'famille couple solo groupe amis', 'culturel desert caire', 'long',
     '2023/11/kristina-tamasauskaite-bVRArO7LwB0-unsplash-scaled.jpg',
     'Roadtrip en Égypte sur mesure',
     'Le Caire <b>→</b> Assouan <b>→</b> Kom Ombo <b>→</b> Edfou '
     '<b>→</b> Louxor <b>→</b> Hurghada',
     [('', '9 jours minimum'), ('teal', 'Véhicule et chauffeur privés')],
     'À partir de', '1635 €'),
    ('pyramides-louxor-et-mer-rouge-en-famille',
     'famille', 'culturel mer caire', 'moyen',
     '2023/11/WhatsApp-Image-2025-08-14-at-13.23.16.jpeg',
     'Pyramides, Louxor et mer rouge en famille',
     'Le Caire <b>→</b> Louxor <b>→</b> Hurghada',
     [('', '8 jours minimum'), ('teal', 'Sans croisière'),
      ('teal', 'Fin de séjour à la mer')],
     'À partir de', '1485 €'),
    ('campement-au-coeur-du-mont-moise',
     'couple solo groupe amis', 'sinai', 'court',
     '2025/07/WhatsApp-Image-2025-06-27-at-15.33.21_37e02dae.jpg',
     'Bédouin au coucher du soleil',
     'Sharm el-Sheikh ou Dahab <b>→</b> Sainte-Catherine <b>→</b> Mont Moïse',
     [('', '2 jours minimum'), ('teal', 'Ascension de nuit'),
      ('teal', 'Guide bédouin')],
     'À partir de', '290 €'),
]

FLECHE = ('<svg width="15" height="11" viewBox="0 0 15 11" fill="none" '
          'aria-hidden="true"><path d="M1 5.5h12M9 1.5l4 4-4 4" '
          'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
          'stroke-linejoin="round"/></svg>')

LEDE_ACCUEIL = (
    'Nos agents vivent en Égypte&nbsp;: ce sont eux qui réservent l’hôtel à '
    'Gizeh, le bateau à Assouan et le guide à Sainte-Catherine, et qui restent '
    'joignables pendant votre séjour. C’est ce qui permet d’ajuster une étape '
    'en cours de route.')


def carte_accueil(c):
    (slug, qui, envie, duree, img, alt, route, puces, pt, prix) = c
    u = SITE + '/programs/%s/' % slug
    t = TITRE[slug]
    return (
        '<article class="carte" data-qui="%s" data-envie="%s" data-duree="%s">'
        '<div class="carte__img"><img src="%s/wp-content/uploads/%s" alt="%s" '
        'loading="lazy" decoding="async"></div><div class="carte__corps">'
        '<h3><a href="%s">%s</a></h3><p class="carte__route">%s</p>'
        '<div class="carte__meta">%s</div><div class="carte__pied">'
        '<span class="prix"><small>%s</small><b>%s</b><i>/ Personne</i></span>'
        '<a href="%s" class="lien-fl" aria-label="Voir le jour par jour : %s">'
        'Le jour par jour %s</a></div></div></article>'
        % (qui, envie, duree, SITE, img, alt, u, t, route,
           ''.join('<span class="puce%s">%s</span>'
                   % (' puce--teal' if k == 'teal' else '', v)
                   for k, v in puces),
           pt, prix, u, t, FLECHE))


# ----------------------------------------------------------------- outillage

def mal_refermee(h):
    """Combien de balises de structure ne trouvent pas leur paire."""
    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        return 0
    pile, seules = [], 0
    for m in re.finditer(
            r'<(section|div|details|article)(?:\s[^>]*)?>'
            r'|</(section|div|details|article)>', h[a:b]):
        if m.group(0).startswith('</'):
            if pile and pile[-1] == m.group(2):
                pile.pop()
            else:
                seules += 1
        else:
            pile.append(m.group(1))
    return seules + len(pile)


def bornes_grille(h):
    """(début, fin) du <div class="cartes …"> de la section des séjours."""
    i = h.find('id="sejours"')
    if i < 0:
        return None
    d = h.find('<div class="cartes', i)
    if d < 0:
        return None
    p, k = 0, d
    while k < len(h):
        if h.startswith('<div', k):
            p += 1
        elif h.startswith('</div>', k):
            p -= 1
            if p == 0:
                return d, k
        k += 1
    return None


def cartes(h):
    """(début, fin, slug) de chaque carte de séjour du corps de page."""
    out, i = [], 0
    while True:
        i = h.find('<article class="carte"', i)
        if i < 0:
            return out
        p, k = 0, i
        while k < len(h):
            if h.startswith('<article', k):
                p += 1
            elif h.startswith('</article>', k):
                p -= 1
                if p == 0:
                    k += len('</article>')
                    break
            k += 1
        m = re.search(r'/programs/([a-z0-9-]+)/', h[i:k])
        out.append((i, k, m.group(1) if m else ''))
        i = k


def recompter(h):
    """« N séjours y passent » suit les cartes, et les facettes aussi."""
    n, fait = len(cartes(h)), 0
    if not n:
        return h, 0
    h, k = re.subn(r'<b>\d+</b>\s*séjours?\s*y\s*passe(?:nt)?',
                   '<b>%d</b> séjour%s y passe%s'
                   % (n, 's' if n > 1 else '', 'nt' if n > 1 else ''), h)
    fait += k
    h, k = re.subn(r'(<p class="fac__cpt"[^>]*>)\d+ séjours?',
                   lambda m: m.group(1) + '%d séjour%s' % (n, 's' if n > 1 else ''),
                   h)
    fait += k
    # les compteurs de chaque case à cocher
    for groupe in ('duree', 'prix'):
        vus = {}
        for d, f, _ in cartes(h):
            v = re.search(r'data-%s="([^"]*)"' % groupe, h[d:f])
            if v and v.group(1):
                vus[v.group(1)] = vus.get(v.group(1), 0) + 1

        def remet(m, vus=vus):
            return '%s<small>%d</small>' % (m.group(1), vus.get(m.group(2), 0))

        h, k = re.subn(
            r'(<input type="checkbox" data-g="%s" value="([^"]*)">'
            r'<b>[^<]*</b>)<small>\d+</small>' % groupe, remet, h)
        fait += k
    return h, fait


def seau(S, B):
    """Toutes les cartes de destination disponibles, par slug."""
    out = {}
    for i in RESERVOIR:
        d = S.get(B + 'pages/%d' % i, params={'context': 'edit'},
                  timeout=180).json()
        h = (d.get('content') or {}).get('raw', '')
        a = h.find('<main')
        b = h.find('</main>', a)
        for deb, fin, slug in cartes(h[a:b]):
            c = h[a:b][deb:fin]
            if slug and slug not in out and 'carte__route' in c:
                out[slug] = c
    return out


def duree_carte(c, slug, pastilles=False):
    """Aligne la durée affichée et la facette sur le déroulé du séjour."""
    n = DUREE.get(slug)
    if not n:
        return c, 0
    fait = 0
    if pastilles and 'carte__duree' not in c and '<div class="carte__img">' in c:
        # une carte sur treize n'avait pas sa pastille de durée, alors que le
        # gabarit de la page en met une sur toutes les autres
        c = c.replace('<div class="carte__img">',
                      '<div class="carte__img"><span class="carte__duree">'
                      '%d jour%s</span>' % (n, 's' if n > 1 else ''), 1)
        fait += 1
    c, k = re.subn(r'(<span class="carte__duree">)\d+\s*jours?(</span>)',
                   lambda m: m.group(1) + '%d jour%s' % (n, 's' if n > 1 else '')
                   + m.group(2), c)
    fait += k
    c, k = re.subn(r'<span>\d+\s*jours?( minimum)?</span>',
                   '<span>%d jour%s minimum</span>' % (n, 's' if n > 1 else ''), c)
    fait += k
    c, k = re.subn(r'<span class="puce">\d+\s*jours?[^<]*</span>',
                   '<span class="puce">%d jour%s minimum</span>'
                   % (n, 's' if n > 1 else ''), c)
    fait += k
    tranche = '1-2' if n <= 2 else ('3-5' if n <= 5 else '6+')
    c, k = re.subn(r'data-duree="(?:1-2|3-5|6\+)"', 'data-duree="%s"' % tranche, c)
    fait += k
    large = 'court' if n <= 5 else ('moyen' if n <= 8 else 'long')
    c, k = re.subn(r'data-duree="(?:court|moyen|long)"',
                   'data-duree="%s"' % large, c)
    fait += k
    return c, fait


def alt_vide(c, slug):
    """Une image de carte sans alternative textuelle prend le titre du séjour."""
    t = TITRE.get(slug)
    if not t:
        return c, 0
    return re.subn(r'(<img [^>]*?)alt=""', r'\1alt="%s"' % t, c)


def corriger(ident, h, dispo):
    j = {}

    def note(cle, n):
        if n:
            j[cle] = j.get(cle, 0) + n

    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        raise SystemExit('pas de main refermé sur %s' % ident)
    tete, corps, pied = h[:a], h[a:b], h[b:]

    # 1. les cartes qui manquent. On regarde les cartes, pas la page entière :
    # le bloc « Pour aller plus loin » cite déjà des programmes en lien.
    deja = {s for _, _, s in cartes(corps)}
    for slug in A_AJOUTER.get(ident, []):
        if slug in deja:
            continue
        if slug not in dispo:
            raise SystemExit('pas de carte toute faite pour %s' % slug)
        # Viser la grille des séjours, et surtout pas le dernier </article> de
        # la page : le mur d'avis est fait d'<article class="mur__a">, et une
        # carte greffée là tombe au milieu des témoignages.
        g = bornes_grille(corps)
        if not g:
            raise SystemExit('grille des séjours introuvable sur %s' % ident)
        corps = corps[:g[1]] + dispo[slug] + corps[g[1]:]
        note('carte ajoutée', 1)

    if ident == 38:
        for c in ACCUEIL:
            if c[0] in {s for _, _, s in cartes(corps)}:
                continue
            k = corps.find('</article></div><div id="vide"')
            if k < 0:
                raise SystemExit('fin de grille introuvable sur l accueil')
            k += len('</article>')
            corps = corps[:k] + carte_accueil(c) + corps[k:]
            note('itinéraire ajouté à l accueil', 1)
        n = len(cartes(corps))
        corps, k = re.subn(r'<b>les \d+ itinéraires</b>',
                           '<b>les %d itinéraires</b>' % n, corps)
        note('phrase du compositeur', k)
        corps, k = re.subn(
            r'<p class="lede" style="margin-bottom:40px">Confiez l'
            r'(?:&#x27;|&#039;|\'|’)organisation(?:(?!</p>).)*?</p>',
            '<p class="lede" style="margin-bottom:40px">' + LEDE_ACCUEIL
            + '</p>', corps, flags=re.S)
        note('texte générique remplacé', k)

    if ident == 5556 and 'rive ouest du lac' not in corps:
        corps, k = re.subn(
            r'<p class="lede" style="margin:14px 0 30px">Tous '
            r'personnalisables(?:(?!</p>).)*?</p>', LEDE_NASSER, corps,
            flags=re.S)
        note('Abou Simbel situé', k)

    # 2. durées et alternatives textuelles, carte par carte
    pastilles = 'carte__duree' in corps
    for deb, fin, slug in reversed(cartes(corps)):
        c = corps[deb:fin]
        neuf, k = duree_carte(c, slug, pastilles)
        note('durée alignée', 1 if k else 0)
        neuf, k2 = alt_vide(neuf, slug)
        note('alt rempli', k2)
        if neuf != c:
            corps = corps[:deb] + neuf + corps[fin:]

    # 3. compteurs et facettes
    corps, k = recompter(corps)
    note('compteurs recalculés', k)

    return tete + corps + pied, j


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    dispo = seau(S, B)
    print('%d cartes de séjour disponibles au réservoir\n' % len(dispo))

    pages = sorted(set(list(A_AJOUTER) + [38]
                       + [5191, 5201, 5210, 5229, 5532, 5547, 5556,
                          116, 470, 2370, 4961, 5011, 5035, 5044, 5052, 5095]))
    a_ecrire = []
    for i in pages:
        d = S.get(B + 'pages/%d' % i, params={'context': 'edit'},
                  timeout=300).json()
        h = (d.get('content') or {}).get('raw', '')
        if not h:
            continue
        neuf, j = corriger(i, h, dispo)
        if neuf == h:
            continue
        if mal_refermee(neuf) > mal_refermee(h):
            raise SystemExit('la page %d serait moins bien refermée' % i)
        a_ecrire.append((i, neuf))
        print('%-6d %s' % (i, ' · '.join('%s ×%d' % (k, v)
                                         for k, v in sorted(j.items()))))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for i, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + 'pages/%d' % i, json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %d' % i)
        print('%-6d écrite' % i)
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
