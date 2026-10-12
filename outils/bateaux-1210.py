#!/usr/bin/env python3
"""Les trois bateaux, sur la page Croisières (fil 10748).

    WP_AUTH='compte:mdp' python3 outils/bateaux-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/bateaux-1210.py --appliquer

Mélanie, en septembre : « enlever cette partie (Pourquoi nous), mais plutôt
remplacer par une explication avec image, durée de chaque bateau :
felouque, dahabeya, croisière bateau à moteur 5* ». On lui avait répondu
qu'il fallait son contenu. Il est déjà sur le site : le guide « Croisière en
Égypte : dahabieh, bateau, felouque » (/croisiere-egypte-dahabieh-bateau-
felouque/) décrit les trois, leurs durées et à qui ils conviennent. Le bloc
en reprend l'essentiel, et renvoie au guide pour le détail.

Durées : bateau à moteur 3 à 4 nuits (le guide, et Mélanie le 12 octobre,
#12944) ; felouque, deux nuits minimum (le guide) ; dahabeya, 4 à 5 jours de
navigation (la page du roadtrip, « embarquement sur bateau à voile
traditionnel (dahabieh) pour 4-5 jours de navigation »).

Pas de photo de bateau à moteur dans la médiathèque : sa carte montre le Nil
à Assouan, en attendant la sienne.
"""

import argparse
import os
import re

import requests

SITE = 'https://authentiquegypte.com'
UP = SITE + '/wp-content/uploads/'
URL = SITE + '/wp-json/wp/v2/pages/4961'
GUIDE = SITE + '/croisiere-egypte-dahabieh-bateau-felouque/'
E = '.elementor-template-canvas .pg '

BATEAUX = [
    ('2023/11/flying-carpet-Si1MFhSLNWY-unsplash-768x512.jpg', 'Une felouque sur le Nil', 'La felouque',
     '2 nuits minimum',
     'Le voilier traditionnel, sans moteur : on dort sur le pont, sur des matelas séparés par des rideaux. '
     'Rustique, au plus près du fleuve.',
     'Les aventuriers, les petits budgets.'),
    ('2023/11/e235bfb4-54a3-41cf-9f55-f2ca30fc8a91-1-768x510.jpg', 'Une dahabeya sur le Nil', 'La dahabeya',
     '4 à 5 jours de navigation',
     'Le bateau à voile d’autrefois, pour quelques cabines seulement. Plus lent, il laisse le temps de visites '
     'approfondies et des villages au bord du Nil.',
     'Les couples, et les familles ou les groupes qui le privatisent.'),
    ('2023/11/nile-4069222_1280.jpg', 'Le Nil à Assouan', 'Le bateau à moteur 5*',
     '3 à 4 nuits',
     'La croisière classique entre Assouan et Louxor : cabines climatisées, piscine, restaurant, et un guide '
     'privatif pour vos visites.',
     'Les familles, et les séjours au planning serré.'),
]

STYLE = ('<style data-retours="12-10-bateaux">'
         + E + '.bateaux__l{list-style:none;padding:0;margin:24px 0 0;display:grid;grid-template-columns:repeat(3,1fr);gap:20px}'
         + E + '.bateaux__l li{background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);border-radius:20px;overflow:hidden;'
         'display:flex;flex-direction:column}'
         + E + '.bateaux__l img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover}'
         + E + '.bateaux__c{padding:18px 20px 22px;display:flex;flex-direction:column;gap:10px;flex:1}'
         + E + '.bateaux__c h3{margin:0;font-size:1.2rem;color:var(--nuit-900,#094D60)}'
         + E + '.bateaux__d{align-self:flex-start;background:#E3F4F9;color:var(--nuit-900,#094D60);border-radius:999px;'
         'padding:5px 12px;font:700 .85rem "Manrope",sans-serif}'
         + E + '.bateaux__c p{margin:0;line-height:1.65;color:var(--texte,#5D5D5D)}'
         + E + '.bateaux__c p b{color:var(--nuit-900,#094D60)}'
         + E + '.bateaux__lien{margin:22px 0 0;text-align:center}'
         '@media (max-width:900px){' + E + '.bateaux__l{grid-template-columns:1fr}}'
         '</style>')


def bloc():
    cartes = ''.join(
        '<li><img src="%s" alt="%s" loading="lazy" decoding="async"><div class="bateaux__c"><h3>%s</h3>'
        '<span class="bateaux__d">%s</span><p>%s</p><p><b>Pour qui :</b> %s</p></div></li>'
        % (UP + img, alt, nom, duree, desc, qui) for img, alt, nom, duree, desc, qui in BATEAUX)
    return ('<section class="pg-sec pg-sec--fond bateaux"><div class="wrap"><p class="eyebrow">Choisir son bateau</p>'
            '<h2>Felouque, dahabeya ou bateau à moteur ?</h2><ul class="bateaux__l">%s</ul>'
            '<p class="bateaux__lien"><a class="btn btn--fantome" href="%s">Comparer les trois bateaux en détail</a></p>'
            '</div></section>' % (cartes, GUIDE))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    h = s.get(URL, params={'context': 'edit'}, timeout=300).json()['content']['raw']
    if 'class="pg-sec pg-sec--fond bateaux"' in h:
        print('Déjà fait.')
        return
    i = h.find('<p class="eyebrow">Pourquoi nous</p>')
    if i < 0:
        raise SystemExit('« Pourquoi nous » introuvable')
    a0 = h.rfind('<section', 0, i)
    b0 = h.find('</section>', i) + len('</section>')
    h = h[:a0] + bloc() + h[b0:]
    m = h.find('<main')
    m = h.find('>', m) + 1
    h = h[:m] + STYLE + h[m:]
    print('« Pourquoi nous » remplacé par les trois bateaux')
    if a.appliquer:
        print('écrit :', s.post(URL, json={'content': h}, timeout=600).status_code)


if __name__ == '__main__':
    main()
