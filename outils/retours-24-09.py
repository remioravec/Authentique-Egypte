#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Les retours de Mélanie du 24/09 qui se traitent sans rien lui demander.

    WP_AUTH='compte:mot de passe' ./outils/retours-24-09.py [--essai]

Soixante-huit fils déposés le 24/09. Celui-ci fait ce qui ne demande
aucun arbitrage : des retraits qu'elle désigne, des corrections de forme
qu'elle décrit, et ses propres mots là où elle les donne. Tout le reste
— ses textes à écrire, ses photos, ses listes de séjours — attend sa
réponse, et n'est pas inventé ici.

1. LE VOILE DU HERO, SUR TOUTES LES PAGES. « Le fond de l'image est trop
   sombre, c'est le cas pour toutes les pages » (#10426), et trois fils
   le redisent page par page. La charte pose le voile à 93 % : le titre
   passe, la photo disparaît dessous. Il descend à 80 %, dégradé jusqu'à
   46 %. Le contraste du titre est mesuré sur la couleur composée, pas
   supposé — c'est ce qui borne l'allègement.

2. LES CONDITIONS DE TARIF S'EN VONT. « Enlever cette partie », trois
   fois de suite sur Paiement, Annulation et Pourquoi ce prix (#10432 à
   #10434). Elles répètent mot pour mot trois réponses de la FAQ qui se
   trouve deux sections plus bas. Le lien « Le détail, question par
   question » reste : il y mène.

3. LA FRISE DES DEGRÉS EST TROP PETITE (#10429). Les douze mois passent
   de .95 à 1.05 rem, et le mois de .875 à .95.

4. LE BANDEAU DE REPÈRES quitte les trois dernières pages qui le
   portaient (#10449, #10459) — les pages profil, après les circuits,
   les fiches séjour et les destinations.

5. LA CARTE EN FRANÇAIS (#10416, #10485). OpenStreetMap sert ses
   libellés dans la langue du pays : en Égypte, en arabe. Les tuiles
   d'OpenStreetMap France rendent les noms français là où ils existent.
   Même licence, même attribution, toujours aucun cookie.

6. « LIRE LE GUIDE », VINGT-DEUX FOIS (#10467 à #10470). Le libellé est
   de moi, pas d'elle : il devient celui de la page qu'il ouvre.
"""

import argparse
import html as H
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

FEUILLE = (
    '<style data-retours="24-09">'
    # 1 · le voile, allégé partout
    + E + '.pg .hero::after{background:linear-gradient(96deg,'
    'rgba(6,61,71,.80) 0%,rgba(6,61,71,.62) 52%,rgba(6,61,71,.46) 100%)}'
    '@media (max-width:860px){' + E + '.pg .hero::after{background:linear-gradient(180deg,'
    'rgba(8,70,80,.58) 0%,rgba(6,61,71,.78) 100%)}}'
    # 3 · la frise, plus lisible
    + E + '.pg .quand__frise b{font-size:.95rem}'
    + E + '.pg .quand__frise .q-t{font-size:1.05rem}'
    + E + '.pg .quand__frise li{padding:13px 6px}'
    '</style>')


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def sans_conditions_tarif(h):
    """Paiement, Annulation, Pourquoi ce prix : trois fois « enlever »."""
    d = h.find('<div class="tarif__cond">')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    return h[:d] + h[f:], ['conditions de tarif retirées (#10432-34)']


def sans_bandeau(h):
    faits = []
    while True:
        d = h.find('<section class="reperes"')
        if d < 0:
            break
        f = _fin(h, d, 'section')
        if f < 0:
            break
        h = h[:d] + h[f:]
        faits = ['bandeau de repères retiré (#10449, #10459)']
    return h, faits


def carte_francais(h):
    """Les tuiles d'OpenStreetMap France, qui portent les noms français."""
    avant = h
    h = h.replace('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                  'https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png')
    h = h.replace('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  'https://a.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png')
    if h == avant:
        return h, []
    # L'attribution change de porteur : OSM France sert, OSM fournit.
    h = h.replace('Fond de carte &copy; <a href="https://www.openstreetmap.org/copyright"',
                  'Fond de carte OpenStreetMap France &copy; <a '
                  'href="https://www.openstreetmap.org/copyright"')
    return h, ['carte en français (#10416, #10485)']


def lire_le_guide(h):
    """Le libellé répété devient celui de la page qu'il ouvre.

    « Lire le guide » vingt-deux fois de suite, c'est mon libellé de
    gabarit, pas un texte de Mélanie : on peut le changer. Le titre de la
    carte dit déjà où l'on va ; le lien le reprend, tronqué à ce qui tient
    sur une ligne, et garde son intitulé complet pour les lecteurs d'écran.
    """
    if 'Lire le guide' not in h:
        return h, []
    n = [0]

    def par_carte(m):
        bloc = m.group(0)
        if 'Lire le guide' not in bloc:
            return bloc
        t = re.search(r'<h3[^>]*>(?:<a[^>]*>)?(.*?)(?:</a>)?</h3>', bloc, re.S)
        if not t:
            return bloc
        titre = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t.group(1))).strip()
        court = titre if len(titre) <= 34 else titre[:33].rstrip(' ,;:') + '…'
        n[0] += 1
        return bloc.replace(
            '>Lire le guide</a>',
            ' aria-label="Lire : %s">%s</a>' % (H.escape(titre), H.escape(court)))

    h = re.sub(r'<article class="carte">.*?</article>', par_carte, h, flags=re.S)
    return (h, ['%d × « Lire le guide » remplacé (#10467-70)' % n[0]]) if n[0] else (h, [])


# Ce que Mélanie dicte elle-même : ses mots, pas les miens.
TEXTES = [
    # (fil, page, à remplacer, par)
    ('10417', 8917,
     "Entre le Désert noir et l’oasis de Farafra, au cœur de l’Égypte.",
     "Entre le Désert noir et l’oasis de Farafra, au cœur de l’Égypte. "
     "À 5 h du Caire en voiture."),
    ('10418', 8917, "Quelles activités y pratiquer&nbsp;?", "Que voir&nbsp;?"),
    ('10418b', 8917, "Quelles activités y pratiquer ?", "Que voir ?"),
    ('10419', 8917,
     "Oui, en camping organisé, souvent inclus dans un circuit dans le désert.",
     "Oui, en camping, avec les autorisations nécessaires et selon les "
     "disponibilités ; sinon en guest house ou en eco-lodge."),
    ('10444', 8582, "Survol des Pyramides en hélicoptère.",
     "Visite du Grand Musée égyptien (GEM)."),
]

# « Enlever » : elle désigne, on retire. Le texte de l'ancre suffit à
# borner le retrait, à condition de remonter à l'élément qui le porte.
RETRAITS = [
    ('10439', 8582, 'li', "Visite des temples de Ramsès II et de Néfertari."),
    ('10443', 8582, 'li', "Visite du Musée Égyptien et de la collection des trésors"),
    ('10473', 8660, 'span', "voyageurs accompagnés"),
    ('10474', 8660, 'span', "</b>avis Google"),
]


def _retirer_porteur(h, balise, texte):
    """Retire le plus petit élément `balise` qui contient vraiment `texte`.

    Un simple rfind sur la balise ouvrante remonte au premier <balise>
    rencontré vers l'amont — qui peut être un tout autre élément, très
    au-dessus, dont la portée engloberait la cible. Sur l'accueil, cela
    emportait une image entière encodée en base64 et déséquilibrait le
    balisage. On retient donc les seules ouvertures dont la portée
    contient la cible, et parmi elles la plus tardive : la plus proche,
    donc la plus petite.
    """
    i = h.find(texte)
    if i < 0:
        return h, False
    candidat = None
    for m in re.finditer(r'<%s\b[^>]*>' % balise, h[:i]):
        f = _fin(h, m.start(), balise)
        if f > i + len(texte):
            candidat = (m.start(), f)
    if not candidat:
        return h, False
    d, f = candidat
    if texte not in h[d:f]:
        return h, False
    return h[:d] + h[f:], True


def corriger(h, pid):
    faits = []
    for etape in (sans_conditions_tarif, sans_bandeau, carte_francais, lire_le_guide):
        h, f = etape(h)
        faits += f

    for fil, page, avant, apres in TEXTES:
        # Le texte ajouté contient parfois l'ancien en entier (#10417) :
        # sans ce garde-fou, chaque passage le rallongerait d'autant.
        if page == pid and avant in h and apres not in h:
            h = h.replace(avant, apres)
            faits.append('texte de Mélanie posé (#%s)' % fil.rstrip('b'))

    for fil, page, balise, texte in RETRAITS:
        if page == pid:
            h, ok = _retirer_porteur(h, balise, texte)
            if ok:
                faits.append('retrait demandé (#%s)' % fil)

    ancienne = re.search(r'<style data-retours="24-09">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    elif not ancienne:
        faits.append('voile allégé et frise agrandie (#10426, #10429)')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-retours="24-09">.*?</style>', '', h, flags=re.S)
    return h + FEUILLE, faits


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
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        print('   #%-6d %-36s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:36],
                                     ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-retours="24-09"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
