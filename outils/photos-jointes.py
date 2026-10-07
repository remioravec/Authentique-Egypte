#!/usr/bin/env python3
"""Les deux photos que Mélanie avait jointes et que personne n'avait posées.

    WP_AUTH='compte:mdp' python3 outils/photos-jointes.py --essai
    WP_AUTH='compte:mdp' python3 outils/photos-jointes.py --appliquer

Le plugin range l'image jointe à un commentaire dans le champ « image » du
fil lui-même. Les outils de réponse ne lisaient que le texte : deux photos
attendaient là depuis des jours, et on lui répondait « envoyez-la-moi ».

  11271 « changer la photo » sur la carte « Du littoral de la mer Rouge aux
        montagnes du Sinaï », avec le lever du soleil sur les sommets du
        Sinaï (médiathèque 11270). C'est la même carte que vise 12274
        (« changer pour cette photo », sur la page Mont Sinaï). La carte
        change partout où elle paraît : listes de séjours, accueil, page
        Mont Sinaï, blocs « Ces séjours se combinent bien ».
  12340 « ajouter image » sur la carte de Hend, page « L'agence » (brouillon
        9126) : sa photo (médiathèque 12339) remplace le monogramme, dans le
        même rond de 52 px.

L'image de la page du séjour elle-même et celle du méga-menu (la catégorie
Sinaï) ne bougent pas : ce n'est pas ce qu'elle a désigné.
"""

import argparse
import importlib.util
import os
import re
import time

import requests

RACINE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('cibles', os.path.join(RACINE, 'cibles.py'))
CIBLES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CIBLES)

SLUG = 'itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge'
U = 'https://authentiquegypte.com/wp-content/uploads/2026/09/artem-labunsky-iZXC2QsdwRk-unsplash'
SINAI_SRC = U + '-768x1152.jpg'
SINAI_SRCSET = ', '.join('%s-%s.jpg %dw' % (U, t, w) for t, w in
                         (('200x300', 200), ('683x1024', 683), ('768x1152', 768),
                          ('1024x1536', 1024)))
SINAI_ALT = 'Lever du soleil sur les sommets du Sinaï'

HEND = ('<img class="pers__m" src="https://authentiquegypte.com/wp-content/uploads/'
        '2026/10/1674642_w-768_h-1024_q-70_m-crop-2-150x150.jpg" alt="Hend" '
        'width="52" height="52" loading="lazy" decoding="async" '
        'style="object-fit:cover;padding:0">')


def nouvelle_img(tag):
    """Même balise, autre photo : src, srcset, alt et proportions changent."""
    attrs = re.sub(r'\s(?:src|srcset|alt|width|height)="[^"]*"', '', tag[4:].rstrip('>').rstrip('/'))
    return ('<img src="%s" srcset="%s" alt="%s" width="768" height="1152"%s>'
            % (SINAI_SRC, SINAI_SRCSET, SINAI_ALT, attrs))


def changer_cartes(h):
    """Chaque bloc qui mène au séjour et porte une image : la carte, le
    bloc « proches ». On remplace la première image de ce bloc."""
    n = 0
    lien = 'programs/%s/' % SLUG
    for motif in (r'<article class="carte"', r'<a href="[^"]*%s"><div class="proches__img">' % re.escape(lien)):
        pos = 0
        while True:
            m = re.compile(motif).search(h, pos)
            if not m:
                break
            debut = m.start()
            fin = h.find('</article>' if motif.startswith('<article') else '</a>', debut)
            bloc = h[debut:fin]
            pos = fin
            if lien not in bloc:
                continue
            i = bloc.find('<img')
            if i < 0:
                continue
            j = bloc.find('>', i) + 1
            if 'iZXC2QsdwRk' in bloc[i:j]:
                continue
            bloc = bloc[:i] + nouvelle_img(bloc[i:j]) + bloc[j:]
            h = h[:debut] + bloc + h[fin:]
            pos = debut + len(bloc)
            n += 1
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
    total = 0
    for c in CIBLES.toutes():
        url = '%s/wp-json/wp/v2/%s/%d' % (CIBLES.SITE, c['type'], c['cible'])
        h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
        h2, n = changer_cartes(h)
        if not n:
            continue
        total += n
        print('%-6d %d image(s)  %s' % (c['cible'], n, c['url'].replace(CIBLES.SITE, '')))
        if a.appliquer:
            print('       écrit :', requete(s, 'POST', url, json={'content': h2}).status_code)
    print('%d carte(s) du Sinaï changée(s).' % total)

    url = '%s/wp-json/wp/v2/pages/9126' % CIBLES.SITE
    h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
    avant = '<span class="pers__m" aria-hidden="true">H</span><h3>Hend</h3>'
    if avant in h:
        h = h.replace(avant, HEND + '<h3>Hend</h3>', 1)
        print('9126   photo de Hend posée')
        if a.appliquer:
            print('       écrit :', requete(s, 'POST', url, json={'content': h}).status_code)
    else:
        print('9126   photo de Hend : déjà faite ou monogramme introuvable')


if __name__ == '__main__':
    main()
