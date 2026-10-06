#!/usr/bin/env python3
"""Neuf tableaux qu'on ne peut pas lire en entier sur un téléphone.

    WP_AUTH='compte:mdp' python3 outils/tableaux-mobiles.py --essai
    WP_AUTH='compte:mdp' python3 outils/tableaux-mobiles.py --appliquer

Le contrôle d'interface à 390 px montre, sur /quand-partir-en-egypte/, un
tableau de 552 px dans une fenêtre de 390. La page, elle, ne défile pas
latéralement&nbsp;: un parent coupe ce qui dépasse. Les colonnes de droite —
celles qui portent justement la réponse — sont donc hors d'atteinte.

Neuf tableaux sont dans ce cas, sur six guides. On les enveloppe dans un
conteneur qui défile horizontalement, avec un filet d'ombre à droite tant
qu'il reste quelque chose à voir, et on annonce le conteneur au lecteur
d'écran comme une région défilable au clavier.
"""

import argparse
import base64
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cibles

SITE = 'https://authentiquegypte.com'

STYLE = (
    '<style id="tableaux-css-2">'
    # Pas de `.pg` devant : les guides ouvrent sur un <main> nu, et une règle
    # scopée sur .pg n'y produirait rien du tout.
    '.tableau{overflow-x:auto;-webkit-overflow-scrolling:touch;'
    'margin:18px 0;border-radius:var(--r-m,14px);'
    'background:linear-gradient(90deg,#fff 30%,rgba(255,255,255,0)),'
    'linear-gradient(90deg,rgba(255,255,255,0),#fff 70%) 100% 0,'
    'radial-gradient(farthest-side at 0 50%,rgba(9,77,96,.16),transparent),'
    'radial-gradient(farthest-side at 100% 50%,rgba(9,77,96,.16),transparent) '
    '100% 0;background-repeat:no-repeat;background-size:40px 100%,40px 100%,'
    '14px 100%,14px 100%;background-attachment:local,local,scroll,scroll}'
    '.tableau table{margin:0;min-width:34em}'
    '.tableau:focus-visible{outline:2px solid var(--or,#ECAA24);'
    'outline-offset:2px}'
    '</style>')

OUVRE = ('<div class="tableau" tabindex="0" role="region" '
         'aria-label="Tableau, défilement horizontal">')


def bornes(h, i):
    """(début, fin) du <table> qui commence à i."""
    p, k = 0, i
    while k < len(h):
        if h.startswith('<table', k):
            p += 1
        elif h.startswith('</table>', k):
            p -= 1
            if p == 0:
                return i, k + len('</table>')
        k += 1
    return None


def corriger(h):
    a = h.find('<main')
    b = h.find('</main>', a)
    if a < 0 or b < 0:
        return h, 0
    tete, corps, pied = h[:a], h[a:b], h[b:]
    n, i = 0, 0
    while True:
        i = corps.find('<table', i)
        if i < 0:
            break
        if corps.rfind('<div class="tableau"', 0, i) > corps.rfind('</div>', 0, i):
            i += 6
            continue
        bb = bornes(corps, i)
        if not bb:
            break
        corps = corps[:bb[0]] + OUVRE + corps[bb[0]:bb[1]] + '</div>' + corps[bb[1]:]
        n += 1
        i = bb[1] + len(OUVRE) + len('</div>')
    corps = re.sub(r'<style id="tableaux-css(?:-\d+)?">.*?</style>', '', corps,
                   flags=re.S)
    if 'class="tableau"' in corps:
        corps = STYLE + corps
    return tete + corps + pied, n


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

    a_ecrire, total = [], 0
    for c in cibles.toutes():
        for essai in range(5):
            r = S.get(B + '%s/%d' % (c['type'], c['cible']),
                      params={'context': 'edit'}, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        h = (r.json().get('content') or {}).get('raw', '')
        if '<table' not in h:
            continue
        neuf, n = corriger(h)
        if neuf == h:
            continue
        if neuf.count('<table') != h.count('<table'):
            raise SystemExit('un tableau se serait perdu sur %s' % c['url'])
        total += n
        a_ecrire.append((c, neuf))
        print('%-52s %d tableau(x) enveloppé(s)%s'
              % (c['url'].replace(SITE, '')[:52], n,
                 '' if n else ' (feuille mise à jour)'))

    print('\n%d tableau(x) sur %d page(s)' % (total, len(a_ecrire)))
    if a.essai:
        return
    for c, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
