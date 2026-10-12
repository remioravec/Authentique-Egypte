#!/usr/bin/env python3
"""Les photos qu'on peut poser sans attendre Mélanie (fils ouverts du 12 octobre).

    WP_AUTH='compte:mdp' python3 outils/photos-1210.py --essai
    WP_AUTH='compte:mdp' python3 outils/photos-1210.py --appliquer

Tout vient de la médiathèque du site, y compris les photos qu'elle y a
déposées elle-même (villages nubiens d'Assouan, Abou Simbel depuis le
bateau, lever du soleil sur le Sinaï).

  10744 « Les autres types de séjours » : la tuile « Voyage culturel » n'avait
        pas de photo sur « Nos séjours », et ailleurs elle montrait la même
        felouque que la tuile « Croisières ». La tuile « Désert » montrait le
        sommet du mont Sinaï. Culturel prend les colonnes d'un temple,
        Désert le désert blanc.
  10438 « des photos de chaque étape sur tous les programmes » : 20 journées
        sur 82 n'en avaient pas. Chacune prend une photo de son lieu, jamais
        deux fois la même dans un séjour. Bahariya reste sans photo : la
        médiathèque n'en a aucune, et on ne met pas une autre oasis à sa
        place.
  10816, 10854 la photo de fond de deux guides, « Égypte hors des sentiers
        battus » et « 10 choses à ne pas faire » : le gabarit des guides la
        prévoit (chapeau__bg) ; ces deux-là n'en avaient pas.
  10856 « Plongée en mer Rouge » dans « Expériences uniques » : une photo de
        la mer Rouge.
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
SITE = CIBLES.SITE
UP = SITE + '/wp-content/uploads/'

CANDIDATS = {
    'assouan': [('2026/09/Aswan-villages-nubiens-scaled.jpg', 'Villages nubiens à Assouan'),
                ('2023/11/flying-carpet-Si1MFhSLNWY-unsplash-scaled.jpg', 'Felouque sur le Nil'),
                ('2025/06/Voyage-sur-mesure-a-Assouan-en-Egypte.png', 'Assouan')],
    'abou-simbel': [('2026/10/WhatsApp-Image-2026-06-10-at-12.44.27.jpeg', 'Les temples d’Abou Simbel')],
    'louxor': [('2023/11/calin-stan-Mv15X2n8JVE-unsplash-scaled.jpg', 'Colonnes d’un temple égyptien'),
               ('2025/06/Voyage-sur-mesure-a-Louxor-en-Egypte.png', 'Louxor')],
    'hurghada': [('2025/07/nassim-wahba-pb8MhOgjlEk-unsplash-scaled.jpg', 'Le littoral de la mer Rouge'),
                 ('2023/11/yuriy-kostin-cc6kWqOr790-unsplash-scaled.jpg', 'Plage de la mer Rouge'),
                 ('2023/11/hotel-hurghada-scaled.jpg', 'Hôtel à Hurghada')],
    'le-caire': [('2023/11/pyramides-scaled.jpg', 'Les pyramides de Gizeh'),
                 ('2025/06/Voyage-sur-mesure-au-Caire-en-Egypte.png', 'Le Caire')],
    'desert-blanc': [('2023/11/thales-botelho-de-sousa-mgGbLjY9jlI-unsplash-scaled.webp', 'Le désert blanc')],
    'sainte-catherine': [('2026/09/artem-labunsky-iZXC2QsdwRk-unsplash-scaled.jpg', 'Lever du soleil sur le Sinaï'),
                         ('2025/06/mohamad-sameh-Jl6Ghf2YsFQ-unsplash-scaled.jpg', 'Paysage du Sinaï')],
    'charm-el-cheikh': [('2025/07/peggy-anke-YxpoB3bvlZQ-unsplash-scaled.jpg', 'Lagon de la mer Rouge'),
                        ('2025/07/nassim-wahba-pb8MhOgjlEk-unsplash-scaled.jpg', 'Le littoral de la mer Rouge')],
}

TEMPLE = UP + '2023/11/calin-stan-Mv15X2n8JVE-unsplash-scaled.jpg'
DESERT = UP + '2023/11/thales-botelho-de-sousa-mgGbLjY9jlI-unsplash-scaled.webp'
GUIDES = {5906: ('2023/11/Siwa_Oasis_sunset_on_Maraqi_Egypt.webp', 'L’oasis de Siwa au coucher du soleil'),
          3907: ('2023/11/pyramides-scaled.jpg', 'Les pyramides de Gizeh')}


def photo(f, alt):
    return ('<a class="etape__photo" data-lb href="%s" data-alt="%s" aria-label="Agrandir la photo : %s">'
            '<img src="%s" alt="%s" decoding="async" sizes="(max-width:1040px) 100vw, 780px" loading="lazy"></a>'
            % (UP + f, alt, alt, UP + f, alt))


def etapes(h, j):
    n = 0
    for m in reversed(list(re.finditer(r'(<article class="etape" id="etape-\d+" data-lieu="([^"]*)">)(.*?)</article>',
                                       h, re.S))):
        if 'etape__photo' in m.group(3):
            continue
        lieu = m.group(2)
        deja = h  # une photo déjà présente dans la page n'est pas reprise
        choix = next(((f, a) for f, a in CANDIDATS.get(lieu, []) if f not in deja), None)
        if not choix:
            continue
        h = h[:m.end(1)] + photo(*choix) + h[m.end(1):]
        n += 1
    if n:
        j.append('%d journée(s) illustrée(s)' % n)
    return h


def tuiles(h, j):
    n = 0
    # Désert : plus le sommet du Sinaï
    h, k = re.subn(r'(<a href="%s/nos-sejours-egypte/desert-egypte/"><div class="fams__img">)<img [^>]*DSC00581[^>]*>'
                   % re.escape(SITE),
                   r'\1<img src="%s" alt="Le désert blanc" decoding="async" loading="lazy">' % DESERT, h)
    n += k
    # Culturel : une photo, et pas la felouque des croisières
    lien = '<a href="%s/nos-sejours-egypte/voyage-culturel-en-egypte/">' % SITE
    img = '<div class="fams__img"><img src="%s" alt="Colonnes d’un temple égyptien" decoding="async" loading="lazy"></div>' % TEMPLE
    h, k = re.subn(re.escape(lien) + r'<div class="fams__img"><img [^>]*flying-carpet[^>]*></div>', lien + img, h)
    n += k
    h, k = re.subn(re.escape(lien) + r'<h3>', lien + img + '<h3>', h)
    n += k
    if n:
        j.append('tuiles : %d photo(s) de catégorie' % n)
    return h


def guide(pid, h, j):
    if pid in GUIDES and '<div class="chapeau__bg"' not in h:
        f, alt = GUIDES[pid]
        h, k = re.subn(r'(<section class="chapeau">)', r'\1<div class="chapeau__bg" aria-hidden="true"><img src="%s" '
                       r'alt="" decoding="async"></div>' % (UP + f), h, count=1)
        if k:
            j.append('photo de fond du guide : %s' % alt)
    if pid == 5826 and 'nassim-wahba' not in h:
        h, k = re.subn(r'(<h3 id="s9">Plongée en Mer Rouge</h3>)', r'\1<figure class="fig"><img src="%s2025/07/nassim-'
                       r'wahba-pb8MhOgjlEk-unsplash-scaled.jpg" alt="Les eaux de la mer Rouge" loading="lazy" '
                       r'decoding="async"><figcaption>Les eaux de la mer Rouge</figcaption></figure>' % UP, h, count=1)
        if k:
            j.append('photo de la mer Rouge (plongée)')
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
        typ = c['type']
        url = '%s/wp-json/wp/v2/%s/%d' % (SITE, typ, c['cible'])
        d = s.get(url, params={'context': 'edit'}, timeout=300).json()
        if 'content' not in d:
            continue
        h = d['content']['raw']
        j = []
        h2 = tuiles(h, j)
        if typ == 'programs':
            h2 = etapes(h2, j)
        h2 = guide(c['cible'], h2, j)
        if not j:
            continue
        print('%-6d %-50s %s' % (c['cible'], c['url'].replace(SITE, ''), ' · '.join(j)))
        if a.appliquer:
            for essai in range(4):
                try:
                    print('       écrit :', s.post(url, json={'content': h2}, timeout=600).status_code)
                    break
                except requests.RequestException:
                    time.sleep(2 ** essai)


if __name__ == '__main__':
    main()
