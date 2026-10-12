#!/usr/bin/env python3
"""La liste des pages refondues, à un seul endroit.

Le manifeste du 2 octobre est une pièce de sauvegarde : il dit ce qui a été
basculé ce jour-là, et il ne doit pas être réécrit après coup. Les pages
venues après s'ajoutent ici :

  /sur-mesure/ (786) refaite à part le 3 octobre, à la demande de Rémi ;
  /voyage-a-alexandrie/ (5219) et /desert-noir/ (5541) basculées le 6
  octobre, une fois vérifié que leurs brouillons ne perdaient aucun contenu ;
  les mentions légales (3785) et la newsletter (3784), reposées le même jour
  sur le gabarit des guides — la première est dans le pied de chaque page, et
  servait encore l'ancien menu.

Restent dehors, et pour une raison chacune :

  /qui-sommes-nous/ (105), dont la nouvelle version est prête mais que Rémi a
  fait revenir à l'ancienne le 4 octobre ;
  et rien d'autre depuis le 12 octobre : /programs/decouverte-de-la-nubie/
  (1337) est passée au nouveau gabarit à la demande de Mélanie (13122),
  avec le jour par jour qu'elle avait en ligne, pour qu'elle le corrige.
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
    {'type': 'pages', 'cible': 3785,
     'url': SITE + '/mentions-legales-agence-voyage-egypte/'},
    {'type': 'pages', 'cible': 3784, 'url': SITE + '/newsletter/'},
    {'type': 'programs', 'cible': 1337, 'url': SITE + '/programs/decouverte-de-la-nubie/'},
]


def toutes():
    """Les 60 contenus qui portent le nouveau gabarit."""
    man = json.load(open(MANIFESTE))
    return list(man['couples']) + [dict(c) for c in APRES]


if __name__ == '__main__':
    for c in toutes():
        print('%-9s %-6d %s' % (c['type'], c['cible'], c['url']))
