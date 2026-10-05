#!/usr/bin/env python3
"""Rendre au client la signature de ses contenus.

    WP_AUTH='compte:mdp' python3 outils/auteurs.py --essai
    WP_AUTH='compte:mdp' python3 outils/auteurs.py --appliquer

Yoast fabrique un nœud `Person` à partir de l'auteur WordPress de chaque
contenu, et ce nœud part dans le JSON-LD public. Or quinze pages et un
article du site sont signés par des comptes de l'agence prestataire —
`Remi.seomonkey` et `Eloïse` (seo-monkey.fr). Le site du client déclarait
donc publiquement, en données structurées, que son contenu est écrit par
son prestataire. Une archive d'auteur `/author/eloise-blandinseo-monkey-fr/`
est même dans le sitemap.

On réattribue à Mélanie, seule identité éditoriale du client sur ce site.
Rien d'autre ne bouge : ni le contenu, ni la date, ni l'URL.
"""

import argparse
import base64
import os
import sys
import time
from collections import Counter

import requests

SITE = 'https://authentiquegypte.com'
VERS = 1          # Mélanie
PRESTATAIRE = {4, 6, 8}      # Remi.seomonkey, Just, Eloïse


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
    noms = {x['id']: x['name'] for x in
            S.get(B + 'users', params={'per_page': 100, 'context': 'edit'},
                  timeout=60).json()}
    if VERS not in noms:
        sys.exit('destinataire inconnu')

    a_faire = []
    for base in ('posts', 'pages', 'programs'):
        page = 1
        while True:
            r = S.get(B + base, params={'per_page': 100, 'status': 'any',
                                        'page': page, 'context': 'edit'}, timeout=90)
            if r.status_code != 200:
                break
            d = r.json()
            if not d:
                break
            for x in d:
                if x.get('author') in PRESTATAIRE:
                    a_faire.append((base, x['id'], x['status'],
                                    noms.get(x['author']), x['link']))
            if len(d) < 100:
                break
            page += 1

    print('%d contenu(s) signés par un compte prestataire' % len(a_faire))
    print('   par compte :', dict(Counter(x[3] for x in a_faire)))
    print('   par état   :', dict(Counter(x[2] for x in a_faire)))
    publies = [x for x in a_faire if x[2] == 'publish']
    print('   dont publiés : %d' % len(publies))
    for base, pid, st, qui, lien in publies[:20]:
        print('      %-9s #%-6d %-16s %s' % (base, pid, qui, lien.replace(SITE, '')[:60]))

    if a.essai:
        return

    n = 0
    for base, pid, st, qui, lien in a_faire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (base, pid), json={'author': VERS}, timeout=120)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            print('      ✗ refus sur %s #%d' % (base, pid))
            continue
        # la relecture tranche : sur ce site, un 200 ne prouve rien
        ap = S.get(B + '%s/%d' % (base, pid), params={'context': 'edit'},
                   timeout=60).json()
        if ap.get('author') != VERS:
            print('      ✗ non gardé sur %s #%d (auteur %s)' % (base, pid, ap.get('author')))
            continue
        n += 1
    print('\n%d / %d contenu(s) réattribués à %s.' % (n, len(a_faire), noms[VERS]))


if __name__ == '__main__':
    main()
