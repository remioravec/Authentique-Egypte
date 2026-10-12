#!/usr/bin/env python3
"""Deux finitions après le passage des séjours du 12 octobre.

    WP_AUTH='compte:mdp' python3 outils/retouches-1210.py [--appliquer]

- Dans un sous-titre de journée, un mot en gras collé à une apostrophe
  (« d’<b>Assouan</b> ») s'affiche avec une espace parasite : le gras du
  sous-titre est retiré là où il suit une apostrophe.
- La pastille du haut de Siwa et du Désert blanc dit « Guide privatif » ;
  la page dit maintenant « Guide privé bédouin » (13054, 13063).
"""
import argparse, os, re, requests

SITE = 'https://authentiquegypte.com/wp-json/wp/v2/programs/'
a = argparse.ArgumentParser(); a.add_argument('--appliquer', action='store_true'); a = a.parse_args()
s = requests.Session(); s.verify = '/root/.ccr/ca-bundle.crt'; s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
for pid in (540, 1168, 2393, 2193, 7336, 1369, 1408):
    h = s.get(SITE + str(pid), params={'context': 'edit'}, timeout=300).json()['content']['raw']
    avant = h
    h = re.sub(r'(<h4 class="etape__t">[^<]*’)<b>([^<]*)</b>', r'\1\2', h)
    if pid in (2393, 2193):
        h = re.sub(r'(<span class="pill">(?:<svg(?:(?!</svg>).)*</svg>))Guide privatif</span>',
                   r'\1Guide privé bédouin</span>', h, flags=re.S)
    if h != avant:
        print(pid, 'modifiée')
        if a.appliquer:
            print('   écrit :', s.post(SITE + str(pid), json={'content': h}, timeout=300).status_code)
