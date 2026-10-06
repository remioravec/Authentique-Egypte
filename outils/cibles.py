#!/usr/bin/env python3
"""La liste des pages refondues, à un seul endroit.

Le manifeste du 2 octobre est une pièce de sauvegarde : il dit ce qui a été
basculé ce jour-là, et il ne doit pas être réécrit après coup. Les pages
venues après s'ajoutent ici :

  /sur-mesure/ (786) refaite à part le 3 octobre, à la demande de Rémi ;
  /voyage-a-alexandrie/ (5219) et /desert-noir/ (5541) basculées le 6
  octobre, une fois vérifié que leurs brouillons ne perdaient aucun contenu.

Reste dehors : /programs/decouverte-de-la-nubie/ (1337), dont le brouillon
n'a ni carte, ni jour-par-jour, ni tarif — alors que la page en ligne, elle,
déroule ses dix journées.
"""

import json
import os

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne',
                         '2026-10-02', 'MANIFESTE.json')

APRES = [
    {'type': 'pages', 'cible': 786, 'url': SITE + '/sur-mesure/'},
    {'type': 'pages', 'cible': 5219, 'url': SITE + '/voyage-a-alexandrie/'},
    {'type': 'pages', 'cible': 5541, 'url': SITE + '/desert-noir/'},
]


def toutes():
    """Les 58 contenus qui portent le nouveau gabarit."""
    man = json.load(open(MANIFESTE))
    return list(man['couples']) + [dict(c) for c in APRES]


if __name__ == '__main__':
    for c in toutes():
        print('%-9s %-6d %s' % (c['type'], c['cible'], c['url']))
