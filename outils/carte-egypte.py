#!/usr/bin/env python3
"""
Le fond de carte de l'Égypte, relevé sur une source publique.

La première carte du gabarit était dessinée à la main : une trentaine de
points posés de mémoire. Elle situait correctement les lieux mais son
littoral était faux, et une carte fausse sur une page qui vend un voyage
est un défaut, pas une décoration.

Ce script prend le tracé réel dans **Natural Earth 1:50m** (domaine
public, le fond de carte de référence des cartographes), en extrait
l'Égypte, le Nil et le lac Nasser, simplifie chaque ligne à la précision
utile pour un dessin de 560 pixels, et écrit `outils/carte-egypte.json`.

Le fichier produit est versionné : le gabarit ne va jamais sur le réseau.

    outils/carte-egypte.py            écrit outils/carte-egypte.json
    outils/carte-egypte.py --verifier compare au fichier existant
"""

import json
import math
import os
import sys
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, 'outils', 'carte-egypte.json')
BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
SOURCES = {
    'pays': 'ne_50m_admin_0_countries.geojson',
    'fleuves': 'ne_50m_rivers_lake_centerlines.geojson',
    'lacs': 'ne_50m_lakes.geojson',
}
# La fenêtre de la carte : l'Égypte, plus une marge à l'est pour la mer
# Rouge et la place des libellés.
CADRE = (23.8, 38.2, 21.5, 32.2)


def lire(nom):
    cache = os.path.join('/tmp', nom)
    if not os.path.exists(cache) or os.path.getsize(cache) < 10000:
        req = urllib.request.Request(BASE + nom, headers={'User-Agent': 'carte-egypte'})
        with urllib.request.urlopen(req, timeout=300) as r, open(cache, 'wb') as f:
            f.write(r.read())
    with open(cache, encoding='utf-8') as f:
        return json.load(f)


def anneaux(geom):
    """Tous les contours d'une géométrie, polygone simple ou multiple."""
    if geom['type'] == 'Polygon':
        return [geom['coordinates'][0]]
    if geom['type'] == 'MultiPolygon':
        return [p[0] for p in geom['coordinates']]
    if geom['type'] == 'LineString':
        return [geom['coordinates']]
    if geom['type'] == 'MultiLineString':
        return list(geom['coordinates'])
    return []


def aire(anneau):
    s = 0.0
    for i in range(len(anneau) - 1):
        s += anneau[i][0] * anneau[i + 1][1] - anneau[i + 1][0] * anneau[i][1]
    return abs(s) / 2


def simplifier(points, tolerance):
    """Douglas-Peucker : on ne garde que les points qui changent la forme."""
    if len(points) < 3:
        return list(points)

    def distance(p, a, b):
        if a == b:
            return math.hypot(p[0] - a[0], p[1] - a[1])
        t = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1]))
                       / ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)))
        proj = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        return math.hypot(p[0] - proj[0], p[1] - proj[1])

    pire, rang = 0.0, 0
    for i in range(1, len(points) - 1):
        d = distance(points[i], points[0], points[-1])
        if d > pire:
            pire, rang = d, i
    if pire <= tolerance:
        return [points[0], points[-1]]
    return simplifier(points[:rang + 1], tolerance)[:-1] + simplifier(points[rang:], tolerance)


def dans_le_cadre(p):
    lo1, lo2, la1, la2 = CADRE
    return lo1 - 1 <= p[0] <= lo2 + 1 and la1 - 1 <= p[1] <= la2 + 1


def morceaux_dans_le_cadre(ligne):
    """Découpe une ligne en tronçons visibles dans la fenêtre."""
    lot, courant = [], []
    for p in ligne:
        if dans_le_cadre(p):
            courant.append([round(p[0], 3), round(p[1], 3)])
        elif courant:
            if len(courant) > 1:
                lot.append(courant)
            courant = []
    if len(courant) > 1:
        lot.append(courant)
    return lot


def main():
    # Le tracé brut compte plusieurs milliers de points : la
    # simplification récursive descend plus profond que la limite par
    # défaut de Python.
    sys.setrecursionlimit(20000)
    pays = lire(SOURCES['pays'])
    egypte = next(x for x in pays['features']
                  if (x['properties'].get('ADM0_A3') or x['properties'].get('adm0_a3')) == 'EGY')
    rings = sorted(anneaux(egypte['geometry']), key=aire, reverse=True)
    # Le premier anneau est le pays ; les suivants sont des îles de
    # quelques kilomètres, invisibles à cette échelle.
    contour = [[round(x, 3), round(y, 3)] for x, y in simplifier(rings[0], 0.045)]

    fleuves = lire(SOURCES['fleuves'])
    nil = []
    for f in fleuves['features']:
        nom = (f['properties'].get('name') or '')
        if 'Nile' not in nom:
            continue
        for ligne in anneaux(f['geometry']):
            for bout in morceaux_dans_le_cadre(ligne):
                simple = simplifier([tuple(p) for p in bout], 0.03)
                if len(simple) > 1:
                    nil.append([[round(x, 3), round(y, 3)] for x, y in simple])

    lacs = lire(SOURCES['lacs'])
    nasser = []
    for f in lacs['features']:
        nom = (f['properties'].get('name') or '')
        if 'Nasser' not in nom:
            continue
        for anneau in anneaux(f['geometry']):
            simple = simplifier([tuple(p) for p in anneau], 0.03)
            nasser.append([[round(x, 3), round(y, 3)] for x, y in simple])

    data = {
        'source': 'Natural Earth 1:50m, domaine public (naturalearthdata.com)',
        'releve': __import__('datetime').date.today().isoformat(),
        'cadre': list(CADRE),
        'contour': contour,
        'nil': nil,
        'nasser': nasser,
    }
    if '--verifier' in sys.argv:
        ancien = json.load(open(SORTIE, encoding='utf-8')) if os.path.exists(SORTIE) else {}
        pareil = ancien.get('contour') == data['contour']
        print('contour identique' if pareil else 'contour DIFFÉRENT')
        return 0 if pareil else 1

    with open(SORTIE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print('%s : contour %d points · Nil %d tronçon(s) · lac Nasser %d anneau(x) · %s octets'
          % (os.path.relpath(SORTIE, RACINE), len(contour), len(nil), len(nasser),
             os.path.getsize(SORTIE)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
