#!/usr/bin/env python3
"""Les croisières se filtrent par type de bateau.

    WP_AUTH='compte:mdp' python3 outils/croisieres-bateau.py --essai
    WP_AUTH='compte:mdp' python3 outils/croisieres-bateau.py --appliquer

Mélanie, le 6 octobre, sur /nos-sejours-egypte/croisieres-en-egypte/ :
  12676 « mettre dans les filtres types de bateau : bateau à moteur ou à
        voile » ;
  12675 « Mer Rouge — enlever cette option ».

Le groupe « Type de séjour » ne proposait que « Croisières » (les quatre
cartes) et « Mer Rouge » (une) : sur une page de croisières, il ne filtrait
rien d'utile. Il cède la place au type de bateau.

D'où viennent les types :
  · « Le Caire et croisière sur un bateau à voile » : dahabeya, « sans
    moteur » dit sa carte → voile ;
  · « Pyramides et croisière sur le Nil » et « Pyramides, croisière et mer
    rouge en famille » : « Hébergement : bateau de croisière 5* » dans leur
    jour 4 → moteur ;
  · « Croisière sur le lac Nasser » : aucune dahabeya ne franchit le haut
    barrage d'Assouan, le lac ne se navigue qu'en bateau de croisière à
    moteur → moteur.

Le script de filtre de la page lit n'importe quel groupe `data-g` contre
l'attribut `data-<groupe>` des cartes : rien à y changer.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
PAGE = 4961
BATEAU = {
    'le-caire-et-croisiere-sur-un-bateau-a-voile': 'voile',
    'pyramides-et-croisiere-sur-le-nil': 'moteur',
    'mer-rouge': 'moteur',
    'croisiere-sur-le-lac-nasser': 'moteur',
}


def corriger(h):
    j = {}
    # data-bateau sur chaque carte
    def poser(m):
        bloc = m.group(0)
        s = re.search(r'/programs/([a-z0-9-]+)/', h[m.end():m.end() + 1500])
        if not s or s.group(1) not in BATEAU or 'data-bateau' in bloc:
            return bloc
        j['cartes typées'] = j.get('cartes typées', 0) + 1
        return bloc[:-1] + ' data-bateau="%s">' % BATEAU[s.group(1)]
    h = re.sub(r'<article class="carte"[^>]*>', poser, h)

    n = {'moteur': list(BATEAU.values()).count('moteur'),
         'voile': list(BATEAU.values()).count('voile')}
    groupe = ('<fieldset class="fac__g"><legend>Type de bateau</legend>'
              '<label class="fac__o"><input type="checkbox" data-g="bateau" '
              'value="moteur"><b>Bateau à moteur</b><small>%d</small></label>'
              '<label class="fac__o"><input type="checkbox" data-g="bateau" '
              'value="voile"><b>Bateau à voile (dahabeya)</b><small>%d</small>'
              '</label></fieldset>' % (n['moteur'], n['voile']))
    h, k = re.subn(r'<fieldset class="fac__g"><legend>Type de séjour</legend>'
                   r'(?:(?!</fieldset>).)*?</fieldset>', groupe, h, flags=re.S)
    if k:
        j['12675 « Mer Rouge » retiré · 12676 type de bateau'] = k
    return h, j


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
    B = SITE + '/wp-json/wp/v2/pages/%d' % PAGE
    for essai in range(5):
        r = S.get(B, params={'context': 'edit'}, timeout=300)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    h = (r.json().get('content') or {}).get('raw', '')
    neuf, j = corriger(h)
    for k, v in j.items():
        print('   %-48s %d' % (k, v))
    if neuf == h or a.essai:
        return
    for essai in range(4):
        r = S.post(B, json={'content': '<!-- wp:html -->\n' + neuf
                            + '\n<!-- /wp:html -->'}, timeout=600)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    else:
        raise SystemExit('écriture refusée')
    print('page écrite.')


if __name__ == '__main__':
    main()
