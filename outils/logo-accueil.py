#!/usr/bin/env python3
"""Le logo de l'accueil faisait 44 px sur mobile, 40 px partout ailleurs.

    WP_AUTH='compte:mdp' python3 outils/logo-accueil.py --essai
    WP_AUTH='compte:mdp' python3 outils/logo-accueil.py --appliquer

Une règle `.logo img{height:44px}` ne vit que sur l'accueil, dans son bloc de
retouches tactiles. Les cinquante-sept autres pages servent 40 px. Sur mobile,
le logo changeait donc de taille entre l'accueil et le reste du site.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
REGLE = re.compile(r'\s*\.elementor-template-canvas \.logo img\{height:44px\}')


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
    B = SITE + '/wp-json/wp/v2/pages/38'

    for essai in range(5):
        r = S.get(B, params={'context': 'edit'}, timeout=300)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    h = (r.json().get('content') or {}).get('raw', '')
    neuf, n = REGLE.subn('', h)
    print('%d règle(s) retirée(s) · %d → %d octets' % (n, len(h), len(neuf)))
    if not n or a.essai:
        return
    for essai in range(4):
        r = S.post(B, json={'content': '<!-- wp:html -->\n' + neuf
                            + '\n<!-- /wp:html -->'}, timeout=600)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    else:
        raise SystemExit('écriture refusée')
    print('accueil écrit.')


if __name__ == '__main__':
    main()
