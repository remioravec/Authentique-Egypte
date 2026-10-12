#!/usr/bin/env python3
"""Les prix et les durées dictés par Mélanie le 12 octobre, partout où ils paraissent.

    WP_AUTH='compte:mdp' python3 outils/prix-durees-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/prix-durees-1210.py --appliquer

Un prix paraît six fois sur la page du séjour (haut de page, « Tarif par
personne », panneau de devis, formulaire, barre mobile, données
structurées) et une fois sur chaque carte qui mène à ce séjour, sur toutes
les autres pages. On ne remplace jamais un nombre à l'aveugle : deux
séjours coûtaient 1 485 €, et les blocs « Ces séjours se combinent bien »
d'une page montrent les prix des autres séjours. Sur la page du séjour, on
vise les balises de son propre prix ; ailleurs, on vise la carte par le
lien qu'elle porte.

  Fayoum 295 € (13000-13003) · Pyramides et croisière sur le Nil 1 495 €
  (13021-13023) · Désert blanc 680 € (13029-13031 ; il disait 520 € le 5
  octobre, c'est le plus récent qui compte) · Siwa 695 € (13046, 13047,
  13053) · Sainte-Catherine 445 € (13067-13069) · Pyramides, croisière et
  mer Rouge en famille 1 690 € (13074-13076) · Nubie 1 190 € (13123 ; un
  commentaire plus ancien du même matin, sur le brouillon, disait 1 290 €).

Durées : roadtrip 6 jours minimum (13102) ; Siwa 4 jours, son nouvel
itinéraire ; Pyramides, Louxor et mer Rouge en famille 8 jours, avec les
deux journées ajoutées.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))


def charger(nom, fichier):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(ICI, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CIBLES = charger('cibles', 'cibles.py')
SEJOURS = charger('sejours', 'retours-07-sejours.py')
SITE = CIBLES.SITE

PRIX = {
    'excursion-a-loasis-de-fayoum': 295,
    'pyramides-et-croisiere-sur-le-nil': 1495,
    'excursion-dans-le-desert-blanc': 680,
    'excursion-a-loasis-de-siwa': 695,
    'sainte-catherine': 445,
    'mer-rouge': 1690,
    'decouverte-de-la-nubie': 1190,
}
DUREES = {
    'roadtrip-en-egypte': 6,
    'excursion-a-loasis-de-siwa': 4,
    'pyramides-louxor-et-mer-rouge-en-famille': 8,
}
PROGRAMMES = {'excursion-a-loasis-de-fayoum': 2054, 'pyramides-et-croisiere-sur-le-nil': 1168,
              'excursion-dans-le-desert-blanc': 2193, 'excursion-a-loasis-de-siwa': 2393,
              'sainte-catherine': 5109, 'mer-rouge': 540, 'roadtrip-en-egypte': 1369,
              'pyramides-louxor-et-mer-rouge-en-famille': 7336}


def tranche_prix(p):
    return '0-500' if p < 500 else ('500-1000' if p < 1000 else '1000+')


def jours(n):
    return '%d jour%s' % (n, 's' if n > 1 else '')


def page_du_sejour(h, slug):
    """Le prix et la durée du séjour sur sa propre page."""
    n = 0
    p = PRIX.get(slug)
    if p:
        for motif in (r'(<div class="hero__prix"><small>À partir de</small><b>)\d+ €',
                      r'(<div class="tarif__ligne"><span>À partir de</span><b>)\d+ €',
                      r'(<small>Par personne, à partir de</small><b>)\d+ €',
                      r'(data-prix=")\d+ €',
                      r'(name="prix" value=")\d+ €',
                      r'(<span class="p"><small>À partir de</small><b>)\d+ €'):
            h, k = re.subn(motif, lambda m: m.group(1) + '%d €' % p, h)
            n += k
        h, k = re.subn(r'("offers":\s*\{"@type":\s*"Offer",\s*"price":\s*)\d+', lambda m: m.group(1) + str(p), h)
        n += k
    d = DUREES.get(slug)
    if d:
        h, k = re.subn(r'(<small>Durée</small><b>)\d+ jours? minimum', lambda m: m.group(1) + jours(d) + ' minimum', h)
        n += k
        h, k = re.subn(r'(<span class="pill">(?:<svg(?:(?!</svg>).)*</svg>))\d+ jours? minimum',
                       lambda m: m.group(1) + jours(d) + ' minimum', h, flags=re.S)
        n += k
    return h, n


def carte(c, slug):
    """Une carte (ou un bloc « proches ») qui mène au séjour."""
    n = 0
    p = PRIX.get(slug)
    if p:
        for motif in (r'(<span class="carte__prix"><small>À partir de</small><b>)\d+ €',
                      r'(À partir de\s*<b>)\d+ €',
                      r'(À partir de</small>\s*<b>)\d+ €',
                      r'(<span class="carte__prix[^"]*">(?:<small>)?À partir de(?:</small>)?\s*(?:<b>)?)\d+ €'):
            c, k = re.subn(motif, lambda m: m.group(1) + '%d €' % p, c)
            n += k
            if k:
                break
        c, k = re.subn(r'data-prix="(?:0-500|500-1000|1000\+)"', 'data-prix="%s"' % tranche_prix(p), c)
        n += k
    d = DUREES.get(slug)
    if d:
        SEJOURS.DUREE[slug] = d
        c, k = SEJOURS.duree_carte(c, slug)
        n += k
    return c, n


def toutes_les_cartes(h):
    n = 0
    for d, f, slug in reversed(SEJOURS.cartes(h)):
        if slug in PRIX or slug in DUREES:
            c, k = carte(h[d:f], slug)
            h = h[:d] + c + h[f:]
            n += k
    # les blocs « Ces séjours se combinent bien »
    for slug in set(PRIX) | set(DUREES):
        motif = r'<a href="%s/programs/%s/"><div class="proches__img">.*?</a>' % (re.escape(SITE), slug)
        for m in reversed(list(re.finditer(motif, h, re.S))):
            c, k = carte(m.group(0), slug)
            h = h[:m.start()] + c + h[m.end():]
            n += k
    if n:
        h, _ = SEJOURS.recompter(h)
    return h, n


def session():
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    return s


def requete(s, methode, url, **k):
    for essai in range(4):
        try:
            r = s.request(methode, url, timeout=300, **k)
            if r.status_code < 500:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** essai)
    raise SystemExit('Le site ne répond pas : ' + url)


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = session()
    for c in CIBLES.toutes():
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, c['type'], c['cible'])
        h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
        n0 = 0
        slug = c['url'].rstrip('/').split('/')[-1] if '/programs/' in c['url'] else None
        if slug:
            h, n0 = page_du_sejour(h, slug)
        h, n1 = toutes_les_cartes(h)
        if not (n0 or n1):
            continue
        print('%-6d page %2d · cartes %2d  %s' % (c['cible'], n0, n1, c['url'].replace(SITE, '')))
        if a.appliquer:
            print('       écrit :', requete(s, 'POST', url, json={'content': h}).status_code)


if __name__ == '__main__':
    main()
