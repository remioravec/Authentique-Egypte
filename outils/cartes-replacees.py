#!/usr/bin/env python3
"""Les deux cartes d'Assouan et du lac Nasser étaient tombées dans les avis.

    WP_AUTH='compte:mdp' python3 outils/cartes-replacees.py --essai
    WP_AUTH='compte:mdp' python3 outils/cartes-replacees.py --appliquer

En ajoutant les séjours manquants (12306, 12283), j'ai greffé les cartes
après le dernier `</article>` de la page. Or le mur d'avis est fait
d'`<article class="mur__a">` : le dernier `</article>` d'une page de
destination n'est pas la dernière carte de séjour, c'est le dernier avis.

Les quatre cartes se sont donc posées au milieu des témoignages. Le compteur
« 5 séjours y passent » disait vrai — il compte les cartes, et elles étaient
bien là — mais pas au bon endroit. C'est le contrôle d'interface qui l'a
montré : deux titres de cartes débordaient de leur colonne, parce qu'une
colonne d'avis est deux fois plus étroite qu'une colonne de séjour.

On les remet dans la grille des séjours. La cause est corrigée dans
retours-07-sejours.py, qui vise désormais la grille et non la page.
"""

import argparse
import base64
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
CIBLES = (5210, 5556)


def cartes(h):
    """(début, fin, slug) de chaque <article class="carte">."""
    out, i = [], 0
    while True:
        i = h.find('<article class="carte"', i)
        if i < 0:
            return out
        p, k = 0, i
        while k < len(h):
            if h.startswith('<article', k):
                p += 1
            elif h.startswith('</article>', k):
                p -= 1
                if p == 0:
                    k += len('</article>')
                    break
            k += 1
        m = re.search(r'/programs/([a-z0-9-]+)/', h[i:k])
        out.append((i, k, m.group(1) if m else ''))
        i = k


def bornes_grille(h):
    """(début, fin) du <div class="cartes …"> de la section des séjours."""
    i = h.find('id="sejours"')
    if i < 0:
        return None
    d = h.find('<div class="cartes', i)
    if d < 0:
        return None
    p, k = 0, d
    while k < len(h):
        if h.startswith('<div', k):
            p += 1
        elif h.startswith('</div>', k):
            p -= 1
            if p == 0:
                return d, k
        k += 1
    return None


def corriger(h):
    a = h.find('<main')
    b = h.find('</main>', a)
    tete, corps, pied = h[:a], h[a:b], h[b:]
    g = bornes_grille(corps)
    if not g:
        raise SystemExit('grille des séjours introuvable')
    egares = [(d, f, s) for d, f, s in cartes(corps) if d > g[1]]
    if not egares:
        return h, []
    blocs = [corps[d:f] for d, f, _ in egares]
    for d, f, _ in reversed(egares):
        corps = corps[:d] + corps[f:]
    g = bornes_grille(corps)
    corps = corps[:g[1]] + ''.join(blocs) + corps[g[1]:]
    return tete + corps + pied, [s for _, _, s in egares]


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
    B = SITE + '/wp-json/wp/v2/pages/'

    a_ecrire = []
    for i in CIBLES:
        for essai in range(5):
            r = S.get(B + str(i), params={'context': 'edit'}, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        h = (r.json().get('content') or {}).get('raw', '')
        neuf, bouges = corriger(h)
        if not bouges:
            print('%-6d rien à déplacer' % i)
            continue
        # le texte ne change pas, seul l'ordre des blocs
        if sorted(re.sub(r'<[^>]+>', '', neuf)) != sorted(re.sub(r'<[^>]+>', '', h)):
            raise SystemExit('le texte changerait sur %d' % i)
        gg = bornes_grille(neuf[neuf.find('<main'):neuf.find('</main>')])
        print('%-6d %d carte(s) remises dans la grille : %s'
              % (i, len(bouges), ', '.join(bouges)))
        a_ecrire.append((i, neuf))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for i, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + str(i), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %d' % i)
        print('%-6d écrite' % i)


if __name__ == '__main__':
    main()
