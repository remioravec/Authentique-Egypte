#!/usr/bin/env python3
"""« mais » et « jamais » ne sont pas des mois. Réparation.

    WP_AUTH='compte:mdp' python3 outils/retours-07-mais.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-mais.py --appliquer

Mélanie avait demandé de mettre en gras la donnée importante de chaque
réponse de FAQ (12309). Mon motif cherchait un nom de mois sans borne de
mot : il a trouvé « mai » dans « mais » et dans « jamais ». Le site affiche
donc « mais nous organisons » et « nous ne partons jamais sans
autorisations », cent soixante-trois fois sur trente-deux pages.

On défait ces gras-là. Le motif est corrigé dans retours-06-faq.py, qui
remettra le bon gras à la prochaine passe : un <b> déjà présent lui fait
passer son tour, donc il faut bien retirer celui-ci d'abord.

On ne touche qu'aux gras collés à une lettre. « De novembre à mars » reste
en gras, « 1 595 € » aussi.
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
MOIS = ('janvier|février|mars|avril|mai|juin|juillet|août|septembre|'
        'octobre|novembre|décembre')
# un gras de mois collé à une lettre, avant ou après
COLLE = re.compile(r'(?:(?<=[^\W\d_])<b>(?:%s)</b>|<b>(?:%s)</b>(?=[^\W\d_]))'
                   % (MOIS, MOIS), re.I)


def defaire(h):
    return COLLE.subn(lambda m: m.group(0)[3:-4], h)


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
                      params={'context': 'edit'}, timeout=240)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('lecture refusée sur %s' % c['url'])
        h = (r.json().get('content') or {}).get('raw', '')
        neuf, n = defaire(h)
        if not n:
            continue
        if re.sub(r'<[^>]+>', '', neuf) != re.sub(r'<[^>]+>', '', h):
            raise SystemExit('le texte changerait sur %s' % c['url'])
        total += n
        a_ecrire.append((c, neuf))
        print('%-52s %d' % (c['url'].replace(SITE, '')[:52], n))

    print('\n%d gras défaits sur %d page(s)' % (total, len(a_ecrire)))
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
