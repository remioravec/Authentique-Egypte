#!/usr/bin/env python3
"""La page Croisières, et la photo de la catégorie Sinaï (12 octobre).

    WP_AUTH='compte:mdp' python3 outils/croisieres-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/croisieres-1210.py --appliquer

  12942 « possibilité dans les filtres de mettre croisière sur le Nil et
        croisière lac Nasser » : un groupe « Croisière » avant « Type de
        bateau ». Le script de filtre lit tout groupe data-g contre
        l'attribut data-<groupe> des cartes ; il suffit de poser
        data-croisiere sur les quatre cartes.
  12944 « 3 à 4 nuits généralement, ça dépend du sens de la croisière et du
        type de bateau ; possibilité de croisière plus longue mais plus
        lente avec plus de temps libre » : la réponse « 4 à 7 nuits » est
        réécrite avec ses mots, partout où la question paraît.
  12946 « J'ai déjà demandé à modifier cette photo », avec la photo jointe :
        la tuile « Sinaï » du bloc « Les autres types de séjours » montrait
        encore la plage retirée de la carte du Sinaï le 7. Elle prend sa
        photo des montagnes, sur toutes les pages qui portent la tuile.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('cibles', os.path.join(ICI, 'cibles.py'))
CIBLES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CIBLES)
spec = importlib.util.spec_from_file_location('sejours', os.path.join(ICI, 'retours-07-sejours.py'))
SEJ = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SEJ)
SITE = CIBLES.SITE

CROISIERE = {'croisiere-sur-le-lac-nasser': 'nasser', 'le-caire-et-croisiere-sur-un-bateau-a-voile': 'nil',
             'pyramides-et-croisiere-sur-le-nil': 'nil', 'mer-rouge': 'nil'}

DUREE_AVANT = re.compile(r'(<summary>Quelle est la durée idéale pour une croisière \?</summary><div class="faq__r">)'
                         r'.*?(</div></details>)', re.S)
DUREE_APRES = ('<p>En général <strong>3 à 4 nuits</strong> : cela dépend du sens de la croisière, '
               'de <a href="https://authentiquegypte.com/voyage-a-assouan/" data-ml>Assouan</a> vers '
               '<a href="https://authentiquegypte.com/voyage-a-louxor/" data-ml>Louxor</a> ou l’inverse, et du '
               'type de bateau. Des croisières <strong>plus longues</strong> sont possibles : plus lentes, avec '
               'davantage de temps libre.</p>')

U = SITE + '/wp-content/uploads/2026/10/artem-labunsky-zVKAExjrloM-unsplash'
SINAI_IMG = ('<img src="%s-768x512.jpg" alt="Les montagnes du Sinaï" decoding="async" srcset="%s-300x200.jpg 300w, '
             '%s-768x512.jpg 768w, %s-1024x683.jpg 1024w, %s-1536x1024.jpg 1536w" sizes="(max-width:860px) 50vw, '
             '300px" width="768" height="512" loading="lazy">' % (U, U, U, U, U))
TUILE = re.compile(r'(<a href="%s/nos-sejours-egypte/sinai-moise-et-saint-catherine/"><div class="fams__img">)'
                   r'<img [^>]*peggy-anke-YxpoB3bvlZQ[^>]*>' % re.escape(SITE))


def croisieres(h, j):
    for d, f, slug in reversed(SEJ.cartes(h)):
        v = CROISIERE.get(slug)
        if v and 'data-croisiere=' not in h[d:f][:300]:
            h = h[:d] + h[d:f].replace('<article class="carte"', '<article class="carte" data-croisiere="%s"' % v, 1) + h[f:]
    nil = sum(1 for v in CROISIERE.values() if v == 'nil')
    if 'data-g="croisiere"' not in h:
        h = h.replace('<fieldset class="fac__g"><legend>Type de bateau</legend>',
                      '<fieldset class="fac__g"><legend>Croisière</legend><label class="fac__o"><input type="checkbox" '
                      'data-g="croisiere" value="nil"><b>Sur le Nil</b><small>%d</small></label><label class="fac__o">'
                      '<input type="checkbox" data-g="croisiere" value="nasser"><b>Sur le lac Nasser</b><small>1</small>'
                      '</label></fieldset><fieldset class="fac__g"><legend>Type de bateau</legend>' % nil, 1)
        j.append('filtre « Croisière » : sur le Nil (%d), sur le lac Nasser (1)' % nil)
    return h


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--essai', action='store_true')
    a.add_argument('--appliquer', action='store_true')
    a = a.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    for c in CIBLES.toutes():
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, c['type'], c['cible'])
        h = s.get(url, params={'context': 'edit'}, timeout=300).json()['content']['raw']
        j = []
        if c['cible'] == 4961:
            h = croisieres(h, j)
        if '<strong>4 à 7 nuits</strong>' in h:
            h, k = DUREE_AVANT.subn(lambda m: m.group(1) + DUREE_APRES + m.group(2), h)
            if k:
                j.append('durée des croisières : 3 à 4 nuits')
        h, k = TUILE.subn(lambda m: m.group(1) + SINAI_IMG, h)
        if k:
            j.append('tuile Sinaï : photo des montagnes')
        if not j:
            continue
        print('%-6d %-45s %s' % (c['cible'], c['url'].replace(SITE, ''), ' · '.join(j)))
        if a.appliquer:
            for essai in range(4):
                try:
                    print('       écrit :', s.post(url, json={'content': h}, timeout=600).status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
