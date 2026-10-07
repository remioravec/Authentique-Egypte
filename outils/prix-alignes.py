#!/usr/bin/env python3
"""« Prix sur devis » sur des séjours qui ont un prix (fils 10738 à 11278).

    WP_AUTH='compte:mdp' python3 outils/prix-alignes.py --essai
    WP_AUTH='compte:mdp' python3 outils/prix-alignes.py --appliquer

Mélanie, quatre fois en septembre : « il manque le prix sur certains
programmes ». On lui avait répondu que quatre séjours n'avaient de prix
nulle part. C'est faux aujourd'hui pour trois d'entre eux : leur propre
page affiche un tarif, et l'accueil aussi. Seules les cartes des pages de
listes disaient encore « Prix sur devis ».

    Le Caire et croisière sur un bateau à voile   1 895 €
    Coucher de soleil et nuit sur le mont Moïse   290 €
    Roadtrip en Égypte sur mesure                 1 635 €

La Nubie reste « sur devis » : sa page n'a de prix nulle part.

La carte prend le prix, la facette de budget la range dans sa tranche, et
les compteurs de la facette sont recomptés.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

RACINE = os.path.dirname(os.path.abspath(__file__))


def charger(nom, fichier):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(RACINE, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CIBLES = charger('cibles', 'cibles.py')
SEJOURS = charger('sejours', 'retours-07-sejours.py')

PRIX = {
    'le-caire-et-croisiere-sur-un-bateau-a-voile': 1895,
    'campement-au-coeur-du-mont-moise': 290,
    'roadtrip-en-egypte': 1635,
}
VIDE = '<span class="carte__prix carte__prix--vide">Prix sur devis</span>'


def tranche(p):
    return '0-500' if p < 500 else ('500-1000' if p < 1000 else '1000+')


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


def aligner(h):
    n = 0
    for d, f, slug in reversed(SEJOURS.cartes(h)):
        c = h[d:f]
        if slug not in PRIX or VIDE not in c:
            continue
        p = PRIX[slug]
        c = c.replace(VIDE, '<span class="carte__prix"><small>À partir de</small>'
                            '<b>%d €</b><i>/ Personne</i></span>' % p)
        c = re.sub(r'data-prix="[^"]*"', 'data-prix="%s"' % tranche(p), c, count=1)
        h = h[:d] + c + h[f:]
        n += 1
    if n:
        h, _ = SEJOURS.recompter(h)
    return h, n


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = session()
    total = 0
    for c in CIBLES.toutes():
        url = '%s/wp-json/wp/v2/%s/%d' % (CIBLES.SITE, c['type'], c['cible'])
        h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
        h2, n = aligner(h)
        if not n:
            continue
        total += n
        print('%-6d %d carte(s)  %s' % (c['cible'], n, c['url'].replace(CIBLES.SITE, '')))
        if a.appliquer:
            print('       écrit :', requete(s, 'POST', url, json={'content': h2}).status_code)
    print('%d carte(s) alignée(s).' % total)


if __name__ == '__main__':
    main()
