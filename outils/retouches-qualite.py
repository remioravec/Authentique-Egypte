#!/usr/bin/env python3
"""Les retouches que le contrôle qualité a trouvées et que je peux faire seul.

    WP_AUTH='compte:mdp' python3 outils/retouches-qualite.py --essai
    WP_AUTH='compte:mdp' python3 outils/retouches-qualite.py --appliquer

Ce qui est traité ici, et rien d'autre : ce qui vit dans le contenu de la
page et ne demande aucune décision éditoriale.

  1. Les textes alternatifs qui valent un nom de fichier
     (« 6213959105_d7ee5e6528_b »). On ne les invente pas : on va chercher
     dans la médiathèque le texte alternatif, la légende ou le titre de
     l'image. Si la médiathèque n'a rien non plus, on ne touche à rien et
     l'image part dans la liste pour Mélanie — décrire une photo qu'on n'a
     pas prise n'est pas notre travail.
  2. Les degrés Celsius écrits « °c », et les en-têtes de tableau en
     minuscules, sur le guide « Quand partir ».
  3. « Où se trouve Caire ? », qui veut dire « Le Caire ».
  4. L'avertissement de chantier resté visible sur l'oasis de Siwa. Le
     texte part ; le déroulé reste faux, et ça, c'est un arbitrage.
  5. L'accent d'« Égypte » dans le titre d'un article — et nulle part
     ailleurs : les trente-deux autres « Egypte » sans accent sont dans un
     avis Google, qu'on ne réécrit jamais.
"""

import argparse
import base64
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = re.compile(r'^[a-zA-Z0-9]+[-_][a-zA-Z0-9\-_]{10,}$')


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
    B = SITE + '/wp-json/wp/v2/'
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    couples = list(man['couples']) + [{'type': 'pages', 'cible': 786,
                                       'url': SITE + '/sur-mesure/'}]

    cache = {}

    def mediatheque(slug):
        """Le texte que la médiathèque donne à cette image, ou rien."""
        if slug in cache:
            return cache[slug]
        r = S.get(B + 'media', params={'search': slug, 'per_page': 5},
                  timeout=60)
        bon = None
        if r.status_code == 200:
            for x in r.json():
                src = (x.get('source_url') or '')
                if slug not in src:
                    continue
                for v in ((x.get('alt_text') or '').strip(),
                          re.sub(r'<[^>]+>', '', (x.get('caption') or {})
                                 .get('rendered', '')).strip(),
                          (x.get('title') or {}).get('rendered', '').strip()):
                    if v and not FICHIER.match(v) and len(v) > 3:
                        bon = v
                        break
                if bon:
                    break
        cache[slug] = bon
        return bon

    journal = {'alt': 0, 'alt_sans_source': [], 'celsius': 0, 'caire': 0,
               'chantier': 0}
    a_ecrire = []
    for c in couples:
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        neuf = h

        # 1 · les alt qui valent un nom de fichier
        for mm in set(re.findall(r'(?:data-)?alt="([^"]+)"', neuf)):
            if not FICHIER.match(mm):
                continue
            bon = mediatheque(mm)
            if not bon:
                journal['alt_sans_source'].append(
                    (c['url'].replace(SITE, ''), mm))
                continue
            neuf = neuf.replace('alt="%s"' % mm, 'alt="%s"' % bon)
            journal['alt'] += 1

        # 2 · les degrés
        neuf, n = re.subn(r'°c\b', '°C', neuf)
        journal['celsius'] += n

        # 3 · la capitale
        neuf, n = re.subn(r'se trouve Caire', 'se trouve Le Caire', neuf)
        journal['caire'] += n

        # 4 · l'avertissement de chantier — il est dans un <p class="atelier">
        #     dont le premier enfant est <span class="aremplir">. On ne retire
        #     que ceux-là : un .atelier sans cette marque est du contenu.
        while True:
            i = neuf.find('<p class="atelier">')
            if i < 0:
                break
            j = neuf.find('</p>', i)
            if 'class="aremplir"' not in neuf[i:j]:
                break
            neuf = neuf[:i] + neuf[j + 4:]
            journal['chantier'] += 1

        if neuf != h:
            a_ecrire.append((c, neuf))

    print('alt repris de la médiathèque : %d' % journal['alt'])
    print('alt sans source, à décrire   : %d' % len(journal['alt_sans_source']))
    for u2, s in journal['alt_sans_source'][:10]:
        print('     %-46s %s' % (u2[:46], s[:40]))
    print('degrés Celsius corrigés      : %d' % journal['celsius'])
    print('« se trouve Caire » corrigé  : %d' % journal['caire'])
    print('avertissement de chantier ôté: %d' % journal['chantier'])
    print('%d page(s) à écrire' % len(a_ecrire))

    json.dump(journal['alt_sans_source'],
              open(os.path.join(RACINE, 'docs/alt-a-decrire.json'), 'w'),
              ensure_ascii=False, indent=1)
    if a.essai:
        return

    for c, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        print('   %s' % c['url'].replace(SITE, ''))

    # le titre de l'article, et lui seul
    r = S.get(B + 'posts', params={'search': 'Sécurité en Egypte',
                                   'per_page': 5, 'context': 'edit'}, timeout=60)
    for x in r.json():
        t = (x.get('title') or {}).get('raw', '')
        if 'Egypte' in t:
            S.post(B + 'posts/%d' % x['id'],
                   json={'title': t.replace('Egypte', 'Égypte')},
                   timeout=60).raise_for_status()
            print('   titre corrigé : %s → %s' % (t, t.replace('Egypte', 'Égypte')))
    print('\n%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
