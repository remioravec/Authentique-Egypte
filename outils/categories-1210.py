#!/usr/bin/env python3
"""Où chaque séjour est rangé, et les cartes qui manquaient (12 octobre).

    WP_AUTH='compte:mdp' python3 outils/categories-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/categories-1210.py --appliquer

  13099 « Roadtrip » : catégorie culturel et famille.
  13100 « Pyramides, Louxor et mer Rouge en famille » : culturel, famille,
        et mer Rouge. Sa carte de « Nos séjours » était incomplète — ni
        durée, ni étapes, ni « / Personne » — : elle est refaite sur le
        modèle des autres.
  13097 « Pyramides, croisière et mer Rouge en famille » : un voyage en
        famille. Son parcours ne passe plus par Abou Simbel (13081).
  12990 page famille : les séjours « en famille » d'abord. « Pyramides,
        Louxor et mer Rouge en famille » n'y était pas : il ouvre la liste.
        Et la carte de la croisière en famille y portait une photo de Siwa.
  12947 Assouan : « il manque l'itinéraire en Nubie ».
  13123 la Nubie : 1 190 €, sur toutes ses cartes.

Sur « Nos séjours », le filtre « Type de séjour » gagne une case « En
famille ». Les compteurs des filtres sont recomptés sur les cartes.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('sejours', os.path.join(ICI, 'retours-07-sejours.py'))
SEJ = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SEJ)

SITE = 'https://authentiquegypte.com'
UP = SITE + '/wp-content/uploads/'
SVG = r'<svg(?:(?!</svg>).)*</svg>'

ROUTE_MER_ROUGE_AVANT = 'Le Caire → Assouan → Abu Simbel → Assouan → Kom Ombo → Edfou → Louxor → Hurghada'
ROUTE_MER_ROUGE = 'Le Caire → Assouan → Kom Ombo → Edfou → Louxor → Hurghada'
IMG_FAMILLE = UP + '2023/11/WhatsApp-Image-2025-08-14-at-13.23.16.jpeg'


def carte_de(h, slug):
    for d, f, s in SEJ.cartes(h):
        if s == slug:
            return d, f
    return None


def remplacer_carte(h, slug, neuve):
    b = carte_de(h, slug)
    return h[:b[0]] + neuve + h[b[1]:] if b else h


def ajouter_cartes(h, cartes, en_tete=False):
    g = SEJ.bornes_grille(h)
    if not g:
        raise SystemExit('grille introuvable')
    d, f = g
    if en_tete:
        i = h.find('>', d) + 1
        return h[:i] + ''.join(cartes) + h[i:]
    return h[:f] + ''.join(cartes) + h[f:]


def famille_attr(c, valeur):
    return re.sub(r'data-famille="[^"]*"', 'data-famille="%s"' % valeur, c, count=1)


def recompter_familles(h):
    vus = {}
    for d, f, _ in SEJ.cartes(h):
        m = re.search(r'data-famille="([^"]*)"', h[d:f])
        for v in (m.group(1).split() if m else []):
            vus[v] = vus.get(v, 0) + 1
    return re.sub(r'(<input type="checkbox" data-g="famille" value="([^"]*)"><b>[^<]*</b>)<small>\d+</small>',
                  lambda m: '%s<small>%d</small>' % (m.group(1), vus.get(m.group(2), 0)), h)


def mod_116(h, j):
    """Nos séjours : modèle complet des cartes, catégories, case « En famille »."""
    b = carte_de(h, 'mer-rouge')
    modele = h[b[0]:b[1]]
    famille = (modele.replace('/programs/mer-rouge/', '/programs/pyramides-louxor-et-mer-rouge-en-famille/')
               .replace('Pyramides, croisière et mer rouge en famille', 'Pyramides, Louxor et mer rouge en famille')
               .replace(ROUTE_MER_ROUGE_AVANT, 'Le Caire → Louxor → Hurghada')
               .replace(ROUTE_MER_ROUGE, 'Le Caire → Louxor → Hurghada'))
    famille = re.sub(r'<span>\d+ jours minimum</span>', '<span>8 jours minimum</span>', famille)
    famille = re.sub(r'(<span class="carte__prix"><small>À partir de</small><b>)\d+ €', r'\g<1>1485 €', famille)
    famille = famille_attr(famille, 'culturel mer famille')
    h = remplacer_carte(h, 'pyramides-louxor-et-mer-rouge-en-famille', famille)
    j.append('carte « Pyramides, Louxor et mer Rouge en famille » refaite : culturel, mer Rouge, famille')
    b = carte_de(h, 'roadtrip-en-egypte')
    h = h[:b[0]] + famille_attr(h[b[0]:b[1]], 'culturel famille') + h[b[1]:]
    b = carte_de(h, 'mer-rouge')
    h = h[:b[0]] + famille_attr(h[b[0]:b[1]], 'croisiere mer famille') + h[b[1]:]
    j.append('roadtrip : culturel et famille ; croisière en famille : + famille')
    if 'data-g="famille" value="famille"' not in h:
        h = h.replace('<b>Culturel</b><small>3</small></label></fieldset>',
                      '<b>Culturel</b><small>3</small></label><label class="fac__o"><input type="checkbox" '
                      'data-g="famille" value="famille"><b>En famille</b><small>0</small></label></fieldset>', 1)
        j.append('filtre : case « En famille »')
    return h, famille


def nubie_prix(h, j):
    b = carte_de(h, 'decouverte-de-la-nubie')
    if not b:
        return h
    c = h[b[0]:b[1]]
    c2 = c.replace('<span class="carte__prix carte__prix--vide">Prix sur devis</span>',
                   '<span class="carte__prix"><small>À partir de</small><b>1190 €</b><i>/ Personne</i></span>')
    c2 = re.sub(r'data-prix="[^"]*"', 'data-prix="1000+"', c2, count=1)
    if c2 != c:
        j.append('Nubie : 1 190 €')
    return h[:b[0]] + c2 + h[b[1]:]


def routes(h, j):
    b = carte_de(h, 'mer-rouge')
    if b and ROUTE_MER_ROUGE_AVANT in h[b[0]:b[1]]:
        h = h[:b[0]] + h[b[0]:b[1]].replace(ROUTE_MER_ROUGE_AVANT, ROUTE_MER_ROUGE) + h[b[1]:]
        j.append('parcours de la croisière en famille sans Abou Simbel')
    return h


def session():
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    return s


def lire(s, pid):
    for essai in range(4):
        try:
            return s.get('%s/wp-json/wp/v2/pages/%d' % (SITE, pid), params={'context': 'edit'},
                         timeout=300).json()['content']['raw']
        except Exception:
            time.sleep(2 ** essai)
    raise SystemExit('lecture impossible %d' % pid)


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = session()
    pages = {}

    # 116 d'abord : elle fournit le modèle de carte complet.
    j = []
    h = lire(s, 116)
    h, carte_famille = mod_116(h, j)
    h = nubie_prix(h, j)
    h = routes(h, j)
    h = recompter_familles(h)
    h, _ = SEJ.recompter(h)
    pages[116] = (h, j)
    roadtrip = h[slice(*carte_de(h, 'roadtrip-en-egypte'))]

    # Culturel : roadtrip et Pyramides-Louxor-mer Rouge en famille
    j = []
    h = lire(s, 5011)
    neuves = [c for sl, c in (('roadtrip-en-egypte', roadtrip), ('pyramides-louxor-et-mer-rouge-en-famille', carte_famille))
              if not carte_de(h, sl)]
    if neuves:
        h = ajouter_cartes(h, neuves)
        j.append('%d carte(s) ajoutée(s) : roadtrip, Pyramides-Louxor-mer Rouge' % len(neuves))
    h = routes(h, j)
    h = recompter_familles(h)
    h, _ = SEJ.recompter(h)
    pages[5011] = (h, j)

    # Mer Rouge
    j = []
    h = lire(s, 470)
    if not carte_de(h, 'pyramides-louxor-et-mer-rouge-en-famille'):
        h = ajouter_cartes(h, [carte_famille])
        j.append('carte « Pyramides, Louxor et mer Rouge en famille » ajoutée')
    h = routes(h, j)
    h = recompter_familles(h)
    h, _ = SEJ.recompter(h)
    pages[470] = (h, j)

    # Page famille : les séjours « en famille » en tête
    j = []
    h = lire(s, 5035)
    b = carte_de(h, 'mer-rouge')
    croisiere = h[b[0]:b[1]]
    croisiere = re.sub(r'<img src="[^"]*" alt="[^"]*"', '<img src="%s" alt="Pyramides, croisière et mer rouge '
                       'en famille"' % IMG_FAMILLE, croisiere, count=1)
    croisiere = famille_attr(croisiere, 'croisiere mer')
    h = h[:b[0]] + h[b[1]:]
    louxor = (croisiere.replace('/programs/mer-rouge/', '/programs/pyramides-louxor-et-mer-rouge-en-famille/')
              .replace('Pyramides, croisière et mer rouge en famille', 'Pyramides, Louxor et mer rouge en famille'))
    louxor = re.sub(r'<span class="puce">\d+ jours?[^<]*</span>', '<span class="puce">8 jours</span>', louxor)
    louxor = re.sub(r'(<span class="prix"><small>À partir de</small><b>)\d+ €', r'\g<1>1485 €', louxor)
    louxor = famille_attr(louxor, 'mer')
    h = ajouter_cartes(h, [louxor, croisiere], en_tete=True)
    j.append('« Pyramides, Louxor et mer Rouge en famille » ajouté en tête, la croisière en famille ensuite, '
             'avec sa propre photo')
    h = recompter_familles(h)
    h, _ = SEJ.recompter(h)
    pages[5035] = (h, j)

    # Assouan : la Nubie
    j = []
    h = lire(s, 5210)
    if not carte_de(h, 'decouverte-de-la-nubie'):
        b = carte_de(h, 'le-caire-et-croisiere-sur-un-bateau-a-voile')
        m = h[b[0]:b[1]]
        nubie = (m.replace('/programs/le-caire-et-croisiere-sur-un-bateau-a-voile/', '/programs/decouverte-de-la-nubie/')
                 .replace('Le Caire et croisière sur un bateau à voile', 'Découverte de la Nubie'))
        nubie = re.sub(r'<span class="carte__duree">[^<]*</span>', '<span class="carte__duree">5 jours</span>', nubie)
        nubie = re.sub(r'<img src="[^"]*" alt="[^"]*"', '<img src="%s2023/11/gonzalo-pedroviejo-gomez-_Ex6joK1ebQ-'
                       'unsplash-scaled.jpg" alt="Village nubien"' % UP, nubie, count=1)
        nubie = re.sub(r'<p class="carte__route">[^<]*</p>', '<p class="carte__route">Assouan → villages nubiens</p>', nubie)
        nubie = re.sub(r'(<span class="prix"><small>À partir de</small><b>)\d+ €', r'\g<1>1190 €', nubie)
        nubie = re.sub(r'data-duree="[^"]*"', 'data-duree="3-5"', nubie, count=1)
        h = ajouter_cartes(h, [nubie])
        h, _ = SEJ.recompter(h)
        j.append('carte « Découverte de la Nubie » ajoutée')
    h = routes(h, j)
    pages[5210] = (h, j)

    # le parcours de la croisière en famille, partout ailleurs
    for pid in (4961, 5191, 5201, 5044, 5052, 38):
        j = []
        h = lire(s, pid)
        h = routes(h, j)
        if j:
            pages[pid] = (h, j)

    for pid, (h, j) in pages.items():
        print('%-6d %s' % (pid, ' · '.join(j)))
        if a.appliquer and j:
            for essai in range(4):
                try:
                    r = s.post('%s/wp-json/wp/v2/pages/%d' % (SITE, pid), json={'content': h}, timeout=600)
                    print('       écrit :', r.status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
