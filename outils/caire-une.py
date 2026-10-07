#!/usr/bin/env python3
"""La photo de une du Caire, et la durée de son chapô (fils 10853 et 10774).

    WP_AUTH='compte:mdp' python3 outils/caire-une.py [--appliquer]

« Changer la photo, mettre une pyramide » : la une du Caire montrait la
dahabeya, une photo de croisière. Mélanie a répondu « voici l'image », mais
le plugin n'a rien reçu : le champ image du commentaire est vide. On pose
la photo de Gizeh de la médiathèque (le Sphinx devant Khéphren), qu'elle
pourra remplacer par la sienne.

Et le chapô disait « comptez trois à cinq jours ». Sa réponse à « combien
de jours rester au Caire » dit une journée, deux pour le vieux Caire, une
troisième pour Saqqara et Dahchour : le chapô suit.
"""
import argparse
import os

import requests

URL = 'https://authentiquegypte.com/wp-json/wp/v2/pages/5191'
AVANT = 'https://authentiquegypte.com/wp-content/uploads/2023/11/e235bfb4-54a3-41cf-9f55-f2ca30fc8a91-1.jpg'
APRES = 'https://authentiquegypte.com/wp-content/uploads/2023/11/pyramides-scaled.jpg'
CHAPO_AVANT = 'Comptez trois à cinq jours pour en voir l’essentiel sans courir'
CHAPO_APRES = 'Comptez deux à trois jours pour en voir l’essentiel sans courir'

a = argparse.ArgumentParser()
a.add_argument('--appliquer', action='store_true')
a = a.parse_args()
s = requests.Session()
s.verify = '/root/.ccr/ca-bundle.crt'
s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
h = s.get(URL, params={'context': 'edit'}, timeout=180).json()['content']['raw']
i = h.find('<section class="hero')
j = h.find('<h1>', i)
tete = h[i:j]
n = tete.count(AVANT)
if n != 2 or h.count(CHAPO_AVANT) != 1:
    raise SystemExit('Une : %d image(s), chapô : %d — j’arrête.' % (n, h.count(CHAPO_AVANT)))
h = h[:i] + tete.replace(AVANT, APRES) + h[j:]
h = h.replace(CHAPO_AVANT, CHAPO_APRES)
print('une : 2 images remplacées · chapô : deux à trois jours')
if a.appliquer:
    print('écrit :', s.post(URL, json={'content': h}, timeout=300).status_code)
