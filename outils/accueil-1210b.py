#!/usr/bin/env python3
"""L'accueil, sur les trois commentaires de Mélanie du 12 octobre à 14 h.

    WP_AUTH='compte:mdp' python3 outils/accueil-1210b.py --essai
    WP_AUTH='compte:mdp' python3 outils/accueil-1210b.py --appliquer

  13514 « la carte est trop grande » : en pleine largeur, la carte faisait
        près de 1 000 px de haut sur ordinateur. Elle passe à gauche, les six
        vignettes de destination à droite (trois par ligne) : le bloc fait
        la moitié de sa hauteur. Sur tablette, elle est limitée à 640 px.
  13515 « modifier le texte » sur le titre « Neuf destinations, d'Alexandrie
        au lac Nasser » : il devient « Nos destinations en Égypte », plus
        direct.
  13516 « le fond est pas assez transparent » : le fond du composeur passe de
        78 % à 55 % de blanc, le flou de 8 à 6 px ; ses intitulés gris
        foncent pour rester lisibles.

Relancé sur une page déjà traitée, il ne remet que la feuille de style.
"""

import argparse
import os
import re

import requests

URL = 'https://authentiquegypte.com/wp-json/wp/v2/pages/38'
P = '.elementor-template-canvas '

STYLE = ('<style data-retours="12-10-accueil-b">'
         + P + '.ou-aller{display:grid;gap:24px}'
         + P + '.ou-aller .carte-eg{margin:0}'
         '@media (min-width:1000px){'
         + P + '.ou-aller{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);align-items:center;gap:32px}'
         + P + '.ou-aller .vign{grid-template-columns:repeat(3,minmax(0,1fr))}'
         + P + '.ou-aller .vign img{aspect-ratio:4/3}'
         # la carte est réduite d'un quart : on grossit ses écritures d'autant
         + P + '.ou-aller .ce-lieu text{font-size:19px;stroke-width:5px}'
         + P + '.ou-aller .ce-lieu circle{r:8}'
         + P + '.ou-aller .ce-mer-t{font-size:18px}' + P + '.ou-aller .ce-pays{font-size:15px}}'
         '@media (max-width:999px){' + P + '.ou-aller .carte-eg{width:100%;max-width:640px;margin:0 auto}}'
         # sur le fond plus transparent, les intitulés gris foncent
         + P + '.compo.compo .compo__t p,' + P + '.compo.compo .champ>span{color:#3E4650}'
         '</style>')


def remplacer(h, avant, apres, quoi, j):
    if avant not in h:
        raise SystemExit('Introuvable : ' + quoi)
    j.append(quoi)
    return h.replace(avant, apres, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    a = p.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    h = s.get(URL, params={'context': 'edit'}, timeout=300).json()['content']['raw']
    if 'data-retours="12-10-accueil-b"' in h:
        h2 = re.sub(r'<style data-retours="12-10-accueil-b">.*?</style>', lambda m: STYLE, h, count=1, flags=re.S)
        print('feuille de style', 'à jour' if h2 == h else 'remplacée')
        if a.appliquer and h2 != h:
            print('écrit :', s.post(URL, json={'content': h2}, timeout=600).status_code)
        return
    j = []

    # 13514 : la carte et les vignettes côte à côte
    d = h.find('<figure class="carte-eg">')
    v = h.find('<div class="vign">', d)
    f = h.find('</a></div>', v) + len('</a></div>')
    if d < 0 or v < 0 or f < len('</a></div>') or h.find('<div', v + 1, f) >= 0:
        raise SystemExit('Bloc carte + vignettes introuvable')
    h = h[:d] + '<div class="ou-aller">' + h[d:f] + '</div>' + h[f:]
    j.append('13514 carte à gauche, vignettes à droite')

    # 13515 : le titre
    h = remplacer(h, '>Neuf destinations, d’Alexandrie au lac Nasser</h2>', '>Nos destinations en Égypte</h2>',
                  '13515 « Nos destinations en Égypte »', j)

    # 13516 : le composeur plus transparent
    h = remplacer(h, '.compo.compo{background:rgba(255,255,255,.78);-webkit-backdrop-filter:blur(8px);'
                     'backdrop-filter:blur(8px);',
                  '.compo.compo{background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(6px);'
                  'backdrop-filter:blur(6px);', '13516 composeur à 55 %', j)

    i = h.find('<main')
    i = h.find('>', i) + 1
    h = h[:i] + STYLE + h[i:]

    for x in j:
        print('  ' + x)
    if a.appliquer:
        print('écrit :', s.post(URL, json={'content': h}, timeout=600).status_code)


if __name__ == '__main__':
    main()
