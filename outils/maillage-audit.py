#!/usr/bin/env python3
"""L'audit du maillage interne, mesuré sur le site en ligne.

    python3 outils/maillage-audit.py

La méthode (phase 2.2) demande un `plan-<client>.json` portant le stade et
la valeur Ads de chaque silo. Il n'existe pas ici : la phase 1 n'a pas eu
lieu sur ce client, le chantier était une refonte de pages existantes. On
mesure donc ce qui est, et le stade se déduit du gabarit — c'est la
typologie même du site :

    guide        → Problème   (22 articles : « quand partir », « vaccins »…)
    destination  → Solution   (un lieu : Louxor, Assouan, le Caire…)
    profil       → Solution   (en famille, en couple, solo, PMR)
    séjour-mère  → Solution   (nos-sejours-egypte et ses cinq filles)
    programme    → Offre      (un séjour daté et tarifé)
    devis        → Achat      (/sur-mesure/)
    accueil, blog, agence → hors funnel

Ce qui compte, et que l'outil sépare : un lien ne vaut que dans le CORPS.
La navigation et le pied pointent partout, et pèsent 0,25 dans la méthode.
On borne donc le corps à `<main>`, en-tête et pied exclus.
"""

import json
import gzip
import re
import os
import urllib.request
import concurrent.futures as cf
from collections import defaultdict, Counter

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STADE = {'guide': 'P', 'destination': 'S', 'profil': 'S', 'sejour': 'S',
         'programme': 'O', 'devis': 'A', 'accueil': '-', 'blog': '-',
         'agence': '-', 'autre': '-'}
RANG = {'P': 1, 'S': 2, 'O': 3, 'A': 4}


def genre(u):
    c = u.replace(SITE, '').strip('/')
    if c == '':
        return 'accueil'
    if c == 'sur-mesure':
        return 'devis'
    if c == 'notre-blog':
        return 'blog'
    if c in ('qui-sommes-nous',):
        return 'agence'
    if c.startswith('programs/'):
        return 'programme'
    if c.startswith('nos-sejours-egypte'):
        return 'sejour'
    if c.startswith('voyage-a-') or c in ('desert-blanc', 'lac-nasser', 'mont-sinai',
                                          'desert-noir'):
        return 'destination'
    if c.startswith('voyage-en-') or c.startswith('voyage-pmr'):
        return 'profil'
    if c in ('newsletter', 'mentions-legales-agence-voyage-egypte'):
        return 'autre'
    return 'guide'


def prendre(u):
    q = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (audit-maillage)',
                                           'Accept-Encoding': 'gzip'})
    r = urllib.request.urlopen(q, timeout=90)
    b = r.read()
    if r.headers.get('Content-Encoding') == 'gzip':
        b = gzip.decompress(b)
    return b.decode('utf-8', 'replace')


def corps(h):
    """Le contenu rédactionnel : <main> sans l'en-tête ni le pied.

    Bornage à la main, par comptage de profondeur : ces pages montent à
    3,7 Mo et une expression régulière gourmande sur du balisage imbriqué
    ne rend jamais la main.
    """
    i = h.find('<main')
    if i < 0:
        # page hors refonte : on retire l'en-tête et le pied d'Elementor
        d = h.find('elementor-location-header')
        if d > 0:
            d = h.find('</header>', d) + 9
        else:
            d = 0
        f = h.find('elementor-location-footer')
        f = h.rfind('<footer', 0, f) if f > 0 else len(h)
        return h[d:f]
    p, k = 0, i
    while k < len(h):
        if h.startswith('<main', k):
            p += 1
        elif h.startswith('</main>', k):
            p -= 1
            if p == 0:
                return h[i:k]
        k += 1
    return h[i:]


def liens(bloc):
    """(url, ancre) des liens internes, ancre nettoyée de son balisage."""
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', bloc, re.S):
        u, a = m.group(1), m.group(2)
        if u.startswith('/'):
            u = SITE + u
        if not u.startswith(SITE):
            continue
        u = u.split('#')[0].split('?')[0]
        if not u or u.endswith(('.jpg', '.png', '.webp', '.pdf')):
            continue
        a = re.sub(r'<[^>]+>', ' ', a)
        a = re.sub(r'\s+', ' ', a).strip()
        out.append((u.rstrip('/') + '/', a))
    return out


def main():
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    urls = sorted({c['url'].rstrip('/') + '/' for c in man['couples']})
    # les pages publiques hors refonte comptent comme cibles
    for u in ('/sur-mesure/', '/newsletter/', '/mentions-legales-agence-voyage-egypte/',
              '/desert-noir/', '/voyage-a-alexandrie/', '/programs/decouverte-de-la-nubie/'):
        urls.append(SITE + u)
    urls = sorted(set(urls))

    pages = {}

    def charger(u):
        try:
            h = prendre(u)
        except Exception as e:
            return u, None, str(e)[:60]
        return u, h, None

    with cf.ThreadPoolExecutor(8) as ex:
        for u, h, err in ex.map(charger, urls):
            if err:
                print('   ✗ %s — %s' % (u, err))
                continue
            c = corps(h)
            pages[u] = {'genre': genre(u), 'stade': STADE[genre(u)],
                        'corps': liens(c), 'nav': liens(h[:h.find('<main')] if '<main' in h else ''),
                        'poids': len(h)}

    print('%d page(s) chargées\n' % len(pages))

    entrants = defaultdict(list)       # cible → [(source, ancre)]
    for u, p in pages.items():
        vus = set()
        for c, a in p['corps']:
            if c == u or c in vus:
                continue
            vus.add(c)
            entrants[c].append((u, a))

    print('— ce que chaque page reçoit DANS LE CORPS —')
    print('%-46s %-11s %4s %4s  %s' % ('page', 'genre', 'ent', 'anc', 'alertes'))
    manque, descendants, pauvres = [], [], []
    for u in sorted(pages, key=lambda x: (pages[x]['genre'], x)):
        p = pages[u]
        e = entrants.get(u, [])
        ancres = {a.lower() for _, a in e if a}
        bas = [s for s, _ in e
               if pages.get(s, {}).get('stade') in RANG and p['stade'] in RANG
               and RANG[pages[s]['stade']] > RANG[p['stade']]]
        al = []
        if len(e) < 11 and p['genre'] in ('destination', 'profil', 'programme', 'sejour', 'guide'):
            al.append('%d/11 entrants' % len(e))
            manque.append((u, len(e)))
        if e and len(ancres) < len(e):
            al.append('%d ancres pour %d liens' % (len(ancres), len(e)))
            pauvres.append(u)
        if bas:
            al.append('%d lien(s) descendant(s)' % len(bas))
            descendants.append((u, bas))
        print('%-46s %-11s %4d %4d  %s'
              % (u.replace(SITE, '')[:46], p['genre'], len(e), len(ancres), ', '.join(al)))

    print('\n— sorties du corps, par page —')
    s = sorted(((len(p['corps']), u) for u, p in pages.items()), reverse=True)
    print('   le plus : %s' % ', '.join('%s (%d)' % (u.replace(SITE, ''), n) for n, u in s[:4]))
    print('   le moins : %s' % ', '.join('%s (%d)' % (u.replace(SITE, ''), n) for n, u in s[-6:]))

    orphelines = [u for u in pages if not entrants.get(u)]
    print('\norphelines dans le corps : %d' % len(orphelines))
    for u in orphelines:
        print('   %s (%s)' % (u.replace(SITE, ''), pages[u]['genre']))

    print('\npages sous les 11 entrants : %d' % len(manque))
    print('ancres répétées : %d page(s)' % len(pauvres))
    print('liens descendants de stade : %d page(s)' % len(descendants))
    for u, bas in descendants[:8]:
        print('   %s ← %s' % (u.replace(SITE, ''),
                              ', '.join(x.replace(SITE, '') for x in bas[:3])))

    json.dump({'pages': {u: {k: v for k, v in p.items() if k != 'nav'}
                         for u, p in pages.items()},
               'entrants': {u: e for u, e in entrants.items()}},
              open(os.path.join(RACINE, 'docs/maillage-etat.json'), 'w'),
              ensure_ascii=False, indent=1)
    print('\nrelevé écrit dans docs/maillage-etat.json')


if __name__ == '__main__':
    main()
