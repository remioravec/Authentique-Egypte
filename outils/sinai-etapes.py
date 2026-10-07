#!/usr/bin/env python3
"""La carte du Sinaï montre les étapes, pas un seul point (fil 12276).

    WP_AUTH='compte:mdp' python3 outils/sinai-etapes.py --essai
    WP_AUTH='compte:mdp' python3 outils/sinai-etapes.py --appliquer

Mélanie : « est-ce possible à la place de mettre une carte interactive avec
les étapes principales : Mont Sinaï, Sainte-Catherine, Sharm el-Cheikh,
Dahab ». La carte de /mont-sinai/ était déjà interactive (Leaflet), mais ne
posait qu'une épingle.

Elle reçoit trois épingles nommées, et le cadrage s'ajuste pour les montrer
toutes. Trois et non quatre : le monastère Sainte-Catherine est au pied du
mont, à deux kilomètres. À l'échelle du Sinaï les deux épingles se
couvriraient l'une l'autre. Elles n'en font donc qu'une, dont la bulle le
précise.

Le script reste celui des autres destinations : sans « etapes » dans
data-situe, il pose son point unique comme avant. Aucun « && » : WordPress
l'encode.
"""

import argparse
import json
import os
import time

import requests

SITE = 'https://authentiquegypte.com'
PAGE = 5547

ETAPES = [
    {'nom': 'Mont Sinaï et Sainte-Catherine', 'lat': 28.5480, 'lon': 33.9755,
     'bulle': 'Le mont Sinaï (mont Moïse) et, à son pied, le monastère '
              'Sainte-Catherine', 'sens': 'left'},
    {'nom': 'Dahab', 'lat': 28.5009, 'lon': 34.5136,
     'bulle': 'Dahab, sur le golfe d’Aqaba', 'sens': 'right'},
    {'nom': 'Charm el-Cheikh', 'lat': 27.9158, 'lon': 34.3300,
     'bulle': 'Charm el-Cheikh, à la pointe sud du Sinaï', 'sens': 'right'},
]

ANCIEN_ATTR = ("data-situe='{&quot;nom&quot;:&quot;Mont Sinaï&quot;,"
               "&quot;lat&quot;:28.5586,&quot;lon&quot;:33.9756}'")
NOUVEL_ATTR = "data-situe='%s'" % json.dumps(
    {'nom': 'Mont Sinaï', 'lat': 28.5586, 'lon': 33.9756, 'etapes': ETAPES},
    ensure_ascii=False, separators=(',', ':')).replace('"', '&quot;')

ANCIEN_TITRE = '<h2 id="t-ou">Où se trouve Mont Sinaï ?</h2>'
NOUVEAU_TITRE = '<h2 id="t-ou">Les étapes du Sinaï</h2>'

SCRIPT = '''<script data-blocs="destination">
(function(){
  var d = document.querySelector('[data-situe]');
  if(!d || typeof L === 'undefined') return;
  var p;
  try { p = JSON.parse(d.getAttribute('data-situe')); } catch(e) { return; }
  var carte = L.map(d, {scrollWheelZoom:false, attributionControl:false})
               .setView([p.lat, p.lon], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
              {maxZoom:17}).addTo(carte);
  function epingle(e){
    return L.marker([e.lat, e.lon], {icon: L.divIcon({className:'',
      html:'<span class="situe__pin"><span></span></span>',
      iconSize:[26,26], iconAnchor:[13,13]})}).addTo(carte)
      .bindPopup(e.bulle || e.nom);
  }
  var etapes = p.etapes || [];
  if(etapes.length){
    // Sur un écran étroit, une étiquette à gauche sortirait du cadre :
    // elle passe au-dessus de son épingle.
    var etroit = d.clientWidth < 520;
    var points = [];
    etapes.forEach(function(e){
      var sens = e.sens || 'right';
      if(etroit){ if(sens === 'left'){ sens = 'top'; } }
      var decale = {left:[-14, 0], right:[14, 0], top:[0, -14]}[sens];
      epingle(e).bindTooltip(e.nom, {permanent:true, direction:sens,
        offset:decale, className:'situe__lbl'});
      points.push([e.lat, e.lon]);
    });
    carte.fitBounds(points, etroit
      ? {paddingTopLeft:[150, 50], paddingBottomRight:[110, 30]}
      : {paddingTopLeft:[150, 40], paddingBottomRight:[140, 40]});
  } else {
    epingle(p);
  }
  // La molette reste à la page : on ne piège pas le défilement.
  carte.on('click', function(){ carte.scrollWheelZoom.enable(); });
  carte.on('mouseout', function(){ carte.scrollWheelZoom.disable(); });
})();
</script>'''

STYLE = ('<style data-sinai="etapes">'
         '.situe__lbl{background:#fff;border:1px solid #E4E4EA;border-radius:999px;'
         'padding:3px 10px;font:600 12.5px/1.3 "Manrope",sans-serif;color:#094D60;'
         'box-shadow:0 2px 6px rgba(9,77,96,.15)}'
         '.situe__lbl::before{display:none}'
         '@media (max-width:640px){.situe__lbl{font-size:11px;padding:2px 8px}}'
         '</style>')


def session():
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    return s


def requete(s, methode, url, **k):
    for essai in range(4):
        try:
            r = s.request(methode, url, timeout=120, **k)
            if r.status_code < 500:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 ** essai)
    raise SystemExit('Le site ne répond pas : ' + url)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    s = session()
    url = '%s/wp-json/wp/v2/pages/%d' % (SITE, PAGE)
    h = requete(s, 'GET', url, params={'context': 'edit'}).json()['content']['raw']
    if 'data-sinai="etapes"' in h:
        print('Déjà fait.')
        return

    debut = h.find('<script data-blocs="destination">')
    fin = h.find('</script>', debut) + len('</script>')
    for nom, ok in (('attribut', ANCIEN_ATTR in h), ('titre', ANCIEN_TITRE in h),
                    ('script', debut > 0)):
        if not ok:
            raise SystemExit('Introuvable : ' + nom)

    h = h.replace(ANCIEN_ATTR, NOUVEL_ATTR, 1).replace(ANCIEN_TITRE, NOUVEAU_TITRE, 1)
    h = h[:debut] + SCRIPT + STYLE + h[fin:]
    print('3 étapes, titre, script et style prêts (%d caractères).' % len(h))
    if a.appliquer:
        r = requete(s, 'POST', url, json={'content': h})
        print('Écrit :', r.status_code)


if __name__ == '__main__':
    main()
