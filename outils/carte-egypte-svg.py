#!/usr/bin/env python3
"""Une carte d'Égypte dessinée, à la place des tuiles OpenStreetMap (12937).

    python3 outils/carte-egypte-svg.py DOSSIER_NATURAL_EARTH > carte.svg

« Possibilité de mettre une autre carte ? Les écritures sont pixelisées. »
Les tuiles d'OpenStreetMap France sont des images : sur un écran haute
densité, leurs noms de lieux s'étalent et se pixelisent. Les fonds nets
(tuiles « retina », vectorielles) sont payants ou réservés aux usages non
commerciaux chez la plupart des fournisseurs.

On dessine donc la carte : un SVG, net à toutes les tailles, sans appel
extérieur, aux couleurs du site. Les contours viennent de Natural Earth,
domaine public : pays (1:50 m), Nil et lac Nasser (1:10 m). Chaque
destination est un lien vers sa page, au clavier comme à la souris.

Le dossier passé en argument contient ne_50m_admin_0_countries.geojson,
ne_10m_rivers_lake_centerlines.geojson et ne_10m_lakes.geojson.
"""

import json
import math
import os
import sys

LON0, LON1, LAT0, LAT1 = 23.2, 38.6, 21.4, 32.4
K = 60                                   # unités SVG par degré de latitude
CX = math.cos(math.radians(27))          # l'Égypte est à 27° de latitude
W = round((LON1 - LON0) * K * CX)
H = round((LAT1 - LAT0) * K)

LIEUX = [
    ('Le Caire', 30.0444, 31.2357, '/voyage-au-caire/', 'droite'),
    ('Alexandrie', 31.2001, 29.9187, '/voyage-a-alexandrie/', 'gauche'),
    ('Fayoum', 29.3084, 30.8428, '/voyage-a-fayoum/', 'gauche'),
    ('Désert noir', 28.10, 28.85, '/desert-noir/', 'gauche'),
    ('Désert blanc', 27.25, 28.15, '/desert-blanc/', 'gauche'),
    ('Mont Sinaï', 28.5586, 33.9756, '/mont-sinai/', 'droite'),
    ('Louxor', 25.6872, 32.6396, '/voyage-a-louxor/', 'droite'),
    ('Assouan', 24.0889, 32.8998, '/voyage-a-assouan/', 'droite'),
    ('Lac Nasser', 22.95, 32.55, '/lac-nasser/', 'gauche'),
]
VOISINS = {'Libya': ('Libye', 27.0, 24.1), 'Sudan': ('Soudan', 21.7, 30.0),
           'Saudi Arabia': ('Arabie saoudite', 27.2, 36.4), 'Jordan': ('Jordanie', 30.9, 36.4),
           'Israel': ('Israël', 31.0, 34.85)}
MERS = [('Mer Méditerranée', 32.0, 27.6), ('Mer Rouge', 24.4, 35.7)]


def xy(lon, lat):
    return (lon - LON0) * K * CX, (LAT1 - lat) * K


def chemin(anneaux, ferme=True):
    out = []
    for anneau in anneaux:
        pts, prec = [], None
        for lon, lat in anneau:
            x, y = xy(lon, lat)
            if prec and abs(x - prec[0]) + abs(y - prec[1]) < 1.2:
                continue
            pts.append('%.1f %.1f' % (x, y))
            prec = (x, y)
        if len(pts) > 1:
            out.append('M' + ' L'.join(pts) + (' Z' if ferme else ''))
    return ' '.join(out)


def dans_cadre(geom):
    xs = [c[0] for c in iter_coords(geom)]
    ys = [c[1] for c in iter_coords(geom)]
    return xs and min(xs) < LON1 + 2 and max(xs) > LON0 - 2 and min(ys) < LAT1 + 2 and max(ys) > LAT0 - 2


def iter_coords(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        for a in c:
            yield from a
    elif t == 'MultiPolygon':
        for p in c:
            for a in p:
                yield from a
    elif t == 'LineString':
        yield from c
    elif t == 'MultiLineString':
        for a in c:
            yield from a


def anneaux(geom):
    if geom['type'] == 'Polygon':
        return geom['coordinates']
    if geom['type'] == 'MultiPolygon':
        return [a for p in geom['coordinates'] for a in p]
    if geom['type'] == 'LineString':
        return [geom['coordinates']]
    return geom['coordinates']


def main(dossier):
    pays = json.load(open(os.path.join(dossier, 'ne_50m_admin_0_countries.geojson')))
    fleuves = json.load(open(os.path.join(dossier, 'ne_10m_rivers_lake_centerlines.geojson')))
    lacs = json.load(open(os.path.join(dossier, 'ne_10m_lakes.geojson')))

    voisins, egypte = [], ''
    for f in pays['features']:
        nom = f['properties'].get('ADMIN') or f['properties'].get('NAME')
        if not dans_cadre(f['geometry']):
            continue
        d = chemin(anneaux(f['geometry']))
        if nom == 'Egypt':
            egypte = d
        else:
            voisins.append(d)
    nil = [chemin(anneaux(f['geometry']), ferme=False) for f in fleuves['features']
           if (f['properties'].get('name') or '') in ('Nile', 'Rosetta Branch', 'Damietta Branch')
           and dans_cadre(f['geometry'])]
    eaux = [chemin(anneaux(f['geometry'])) for f in lacs['features']
            if dans_cadre(f['geometry']) and (f['properties'].get('name') or '') in
            ('Lake Nasser', 'Lake Qarun', 'Great Bitter Lake', 'Lake Manzala', 'Lake Burullus')]

    p = []
    p.append('<svg class="carte-eg__svg" viewBox="0 0 %d %d" role="img" aria-labelledby="carte-eg-t" '
             'xmlns="http://www.w3.org/2000/svg">' % (W, H))
    p.append('<title id="carte-eg-t">Carte de l’Égypte : %s</title>' % ', '.join(x[0] for x in LIEUX))
    p.append('<rect width="%d" height="%d" class="ce-mer"/>' % (W, H))
    p.append('<path class="ce-voisin" d="%s"/>' % ' '.join(voisins))
    p.append('<path class="ce-egypte" d="%s"/>' % egypte)
    p.append('<path class="ce-eau" d="%s"/>' % ' '.join(eaux))
    p.append('<path class="ce-nil" d="%s"/>' % ' '.join(nil))
    for nom, lat, lon in MERS:
        x, y = xy(lon, lat)
        p.append('<text class="ce-mer-t" x="%.0f" y="%.0f">%s</text>' % (x, y, nom))
    for nom, lat, lon in VOISINS.values():
        x, y = xy(lon, lat)
        p.append('<text class="ce-pays" x="%.0f" y="%.0f">%s</text>' % (x, y, nom))
    x, y = xy(29.6, 25.6)
    p.append('<text class="ce-egypte-t" x="%.0f" y="%.0f">ÉGYPTE</text>' % (x, y))
    for nom, lat, lon, url, sens in LIEUX:
        x, y = xy(lon, lat)
        tx = x + 12 if sens == 'droite' else x - 12
        ancre = 'start' if sens == 'droite' else 'end'
        p.append('<a class="ce-lieu" href="https://authentiquegypte.com%s"><circle cx="%.1f" cy="%.1f" r="7"/>'
                 '<text x="%.1f" y="%.1f" text-anchor="%s">%s</text></a>'
                 % (url, x, y, tx, y + 5, ancre, nom))
    p.append('</svg>')
    sys.stdout.write(''.join(p))


if __name__ == '__main__':
    main(sys.argv[1])
