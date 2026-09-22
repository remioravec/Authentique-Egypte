#!/usr/bin/env python3
"""
La carte d'itinéraire devient interactive, sans Google et sans traceur.

    WP_AUTH='compte:mot de passe' ./outils/carte-leaflet.py [--essai]

Rémi voulait une carte interactive. Google Maps demande une clé facturée
au chargement et dépose des traceurs, ce qui oblige à une bannière de
consentement. Leaflet sur les fonds d'OpenStreetMap ne demande ni clé ni
compte, ne pose aucun cookie, et la licence n'exige que l'attribution —
qui est affichée.

Le dessin SVG fait à la main est remplacé, pas supprimé du raisonnement :
il montrait les mêmes étapes, mais figées, à une échelle fausse et sans
possibilité de zoomer. La carte reprend exactement ses étapes, dans le
même ordre.

Les coordonnées sont celles des villes, relevées en WGS84. Ce sont des
faits géographiques, pas des données inventées : Le Caire est à
30,0444 N / 31,2357 E, et ça ne dépend de personne.

Sans JavaScript, la carte laisse la place à la liste des étapes, qui dit
la même chose en toutes lettres.
"""

import argparse
import html as H
import json
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# Latitude, longitude. Relevé sur les coordonnées publiques des villes.
LIEUX = {
    'Le Caire':        (30.0444, 31.2357),
    'Caire':           (30.0444, 31.2357),
    'Louxor':          (25.6872, 32.6396),
    'Assouan':         (24.0889, 32.8998),
    'Abu Simbel':      (22.3372, 31.6258),
    'Abou Simbel':     (22.3372, 31.6258),
    'Hurghada':        (27.2579, 33.8116),
    'Sainte-Catherine': (28.5586, 33.9756),
    'Gebel Moussa':    (28.5392, 33.9750),
    'Fayoum':          (29.3084, 30.8428),
    'Désert Blanc':    (27.2500, 28.1500),
    'Bahariya':        (28.3494, 28.8636),
    'Sharm el-Sheikh': (27.9158, 34.3300),
    'Dahab':           (28.5091, 34.5136),
    'Siwa':            (29.2032, 25.5195),
    'Alexandrie':      (31.2001, 29.9187),
    'Lac Nasser':      (23.2000, 32.7500),
    'Edfou':           (24.9781, 32.8733),
    'Kom Ombo':        (24.4764, 32.9445),
}

TETE = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">'
    '<style data-carte-css="leaflet">'
    '.pg .carte__map{width:100%;height:380px;max-width:720px;margin:0 auto;'
    'border-radius:var(--r-m,14px);border:1px solid var(--ligne,#E4E4EA);'
    'background:var(--teal-fond,#EAF6F9);z-index:0}'
    '.pg .carte__map .leaflet-container{font-family:"Manrope",sans-serif}'
    '.pg .carte__pin{display:grid;place-items:center;width:26px;height:26px;'
    'border-radius:50%;background:var(--nuit-900,#095360);color:#fff;'
    'border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.25);'
    'font-family:"Manrope",sans-serif;font-weight:800;font-size:.8rem}'
    '.pg .carte__etapes{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;'
    'margin:14px 0 0;padding:0;list-style:none}'
    '.pg .carte__etapes li{display:flex;align-items:center;gap:7px;'
    'padding:6px 12px;border:1px solid var(--ligne,#E4E4EA);border-radius:999px;'
    'background:#fff;font-size:.88rem;color:var(--nuit-900,#095360)}'
    '.pg .carte__etapes b{font-family:"Manrope",sans-serif;font-size:.74rem;'
    'font-weight:800;color:var(--teal-txt,#106D7C)}'
    '@media (max-width:640px){.pg .carte__map{height:300px}}'
    '</style>')

# Le script, écrit en une seule chaîne triple : les apostrophes du
# JavaScript n'ont alors pas à être échappées, et une chaîne d'échappements
# imbriqués est exactement le genre de code qu'on relit mal.
SCRIPT = """<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script>(function(){
if(typeof L==="undefined")return;
document.querySelectorAll('[data-carte]').forEach(function(n){
var brut=n.getAttribute("data-carte");
if(!brut||brut.charAt(0)!=="[")return;
var e=JSON.parse(brut);if(!e.length)return;
var c=L.map(n,{scrollWheelZoom:false});
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:14,
attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(c);
var pts=[];
e.forEach(function(p,i){pts.push([p.lat,p.lon]);
L.marker([p.lat,p.lon],{icon:L.divIcon({className:"",
html:'<span class="carte__pin">'+(i+1)+'</span>',iconSize:[26,26],iconAnchor:[13,13]})})
.addTo(c).bindPopup(p.n);});
if(pts.length>1)L.polyline(pts,{color:"#FBB50E",weight:3,opacity:.95,dashArray:"7 5"}).addTo(c);
c.fitBounds(L.latLngBounds(pts).pad(0.25));
if(pts.length===1)c.setZoom(9);
});
})();</script>"""


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def etapes_de(h):
    """Les étapes du dessin, dans l'ordre où il les pose."""
    m = re.search(r'<figure class="carte"', h)
    if not m:
        return []
    f = _fin(h, m.start(), 'figure')
    bloc = h[m.start():f if f > 0 else m.start() + 9000]
    out = []
    for x in re.finditer(r'<text[^>]*class="carte__lbl"[^>]*>(.*?)</text>', bloc, re.S):
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x.group(1))).strip()
        if t and t not in out:
            out.append(t)
    return out


def corriger(h):
    etapes = [e for e in etapes_de(h) if e in LIEUX]
    inconnus = [e for e in etapes_de(h) if e not in LIEUX]
    if not etapes:
        return h, [], inconnus
    m = re.search(r'<svg[^>]*class="carte__svg"', h)
    if not m:
        return h, [], inconnus
    f = _fin(h, m.start(), 'svg')
    if f < 0:
        return h, [], inconnus
    donnees = [{'n': e, 'lat': LIEUX[e][0], 'lon': LIEUX[e][1]} for e in etapes]
    liste = ''.join('<li><b>%d</b>%s</li>' % (i + 1, H.escape(e))
                    for i, e in enumerate(etapes))
    neuf = ('<div class="carte__map" data-carte=\'%s\' role="img" '
            'aria-label="Carte de l’itinéraire : %s"></div>'
            '<ul class="carte__etapes">%s</ul>'
            % (json.dumps(donnees, ensure_ascii=False).replace("'", '&#39;'),
               H.escape(' puis '.join(etapes)), liste))
    h = h[:m.start()] + neuf + h[f:]
    # La légende du dessin citait sa source — « Fond de carte : Natural
    # Earth ». Ce fond n'existe plus : la laisser, c'est créditer une
    # source qu'on n'utilise pas. Leaflet affiche sa propre attribution
    # dans la carte, comme la licence d'OpenStreetMap l'exige.
    h = re.sub(r'<p[^>]*class="carte__(?:note|aide)"[^>]*>(?:(?!</p>).)*?'
               r'(?:Natural Earth|naturalearthdata)(?:(?!</p>).)*?</p>', '', h, flags=re.S)
    h = re.sub(r'<link[^>]*leaflet[^>]*>|<style data-carte-css="leaflet">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<script[^>]*leaflet[^>]*></script>', '', h)
    h = TETE + h + SCRIPT
    return h, etapes, inconnus


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, etapes, inconnus = corriger(brut)
        if not etapes:
            continue
        n += 1
        print('   #%-6d %-38s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:38],
                                     ' → '.join(etapes)))
        if inconnus:
            print('      ✗ lieu(x) sans coordonnées, non placé(s) :', ', '.join(inconnus))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'carte__map' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON')
    print('\n%d carte(s) rendue(s) interactive(s).' % n)


if __name__ == '__main__':
    main()
