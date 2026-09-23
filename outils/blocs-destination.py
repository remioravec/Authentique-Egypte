#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deux blocs du gabarit programme portés sur les pages destination.

    WP_AUTH='compte:mot de passe' ./outils/blocs-destination.py [--essai]
    ./outils/blocs-destination.py --local maquettes/site/destination-*.html

Cinq blocs existent sur une fiche séjour et pas sur une page destination.
Deux valent d'être portés, trois non — et c'est le tri qui compte :

PORTÉ · « QUAND PARTIR ». C'est la question qu'on se pose devant une
destination avant même de choisir un séjour. Les données ne sont pas
inventées : le calendrier des douze mois est celui relevé le 14/09 sur
le guide du client, et la recommandation de saison sort de la table
SAISONS, choisie par le même ordre de décision que sur les fiches
séjour. La page cite sa source, comme ailleurs. Forme réduite au mois et
aux degrés, comme Rémi l'a demandé le 22/09.

PORTÉ · LA CARTE DE SITUATION. Une page destination doit dire où se
trouve le lieu. Même Leaflet et même OpenStreetMap que les fiches
séjour : pas de clé d'API, pas de cookie, pas de bandeau de
consentement. Les coordonnées viennent de la table de carte-leaflet.py.

PAS PORTÉ · LA GALERIE. Il faudrait des photos par destination. La
médiathèque n'en a pas, et c'est précisément ce que Mélanie demande dans
six fils encore ouverts. Poser une galerie vide ou remplie d'images
d'ailleurs serait pire que pas de galerie.

PAS PORTÉ · « TARIF PAR PERSONNE ». Une destination n'a pas de prix :
elle a des séjours, qui en ont chacun un. Le bloc tarif n'a rien à dire
ici, et les cartes de la grille portent déjà leur prix.

PAS PORTÉ · « QUI VOUS RÉPOND ». Ce bloc a été retiré des fiches séjour
le 22/09, à la demande de Rémi. Le porter reviendrait à le remettre.
"""

import argparse
import html as H
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTILS = os.path.join(RACINE, 'outils')
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

UX = SourceFileLoader('ux', os.path.join(OUTILS, 'gabarit-ux.py')).load_module()
CARTE = SourceFileLoader('carte', os.path.join(OUTILS, 'carte-leaflet.py')).load_module()

H_ = '.elementor-template-canvas '

# Le désert Noir manquait à la table : il se trouve au nord de Bahariya,
# sur la piste du désert Blanc. Coordonnées relevées, pas déduites.
LIEUX = dict(CARTE.LIEUX)
LIEUX.setdefault('Désert Noir', (28.1000, 28.8500))
LIEUX.setdefault('Mont Sinaï', LIEUX['Sainte-Catherine'])


def lieu_de(titre):
    """Le lieu d'une page destination, cherché dans la table par son nom."""
    nu = re.sub(r'^Refonte · (?:Destination · )?', '', titre).strip()
    nu = re.sub(r'^Voyage (?:au |à l.|à la |à |dans le |en )?', '', nu, flags=re.I).strip()
    for nom in sorted(LIEUX, key=len, reverse=True):
        if nom.lower() in nu.lower() or nom.lower() in titre.lower():
            return nom, LIEUX[nom]
    return None, None


# Deux pages que la table partagée classe mal, et qu'on ne corrige pas
# dans cette table : elle sert aussi aux fiches séjour, on n'y touche pas
# pour une page destination.
#   « Voyage au Caire » — le mot-clé de la table est « le caire », la page
#     dit « au Caire ». Même ville, même saison.
#   « Voyage au Lac Nasser » — le lac est le réservoir du Nil et ses
#     croisières sont classées « Croisières » par le site lui-même ; la
#     saison du Nil est la sienne.
REPRISES = {'caire': 'caire', 'nasser': 'nil'}


def theme_de(titre):
    """Le même ordre de décision que sur les fiches séjour."""
    bas = titre.lower()
    for nom, mots in UX.THEMES:
        if any(m in bas for m in mots):
            return nom
    for mot, theme in REPRISES.items():
        if mot in bas:
            return theme
    return 'general'


def bloc_quand(titre):
    texte, phares = UX.SAISONS[theme_de(titre)]

    def niveau(cond):
        if 'excellent' in cond or 'très bon' in cond:
            return 'q-1'
        if 'canicul' in cond or 'très chaud' in cond:
            return 'q-3'
        return 'q-2'

    # Mois et degrés seulement : les commentaires et l'affluence ont été
    # retirés des fiches séjour le 22/09, la frise doit se lire d'un coup.
    cases = ''.join(
        '<li class="%s%s"><b>%s</b><span class="q-t">%s °C</span></li>'
        % (niveau(cond), ' q-ok' if i in phares else '', mois, temp)
        for i, (mois, temp, cond, aff) in enumerate(UX.CALENDRIER))
    return (
        '<section class="pg-sec quand-dest"><div class="wrap">'
        '<section class="quand"><p class="eyebrow">La bonne période</p>'
        '<h2 id="t-quand">Quand partir ?</h2>'
        '<p class="quand__intro">' + texte + '</p>'
        '<ol class="quand__frise">' + cases + '</ol>'
        '<p class="quand__leg"><span class="q-1">conseillé</span>'
        '<span class="q-2">chaud</span><span class="q-3">à éviter</span>'
        '<span class="q-src">Températures relevées sur '
        '<a href="' + UX.QUAND_PARTIR + '">notre guide quand partir</a>.'
        '</span></p></section></div></section>')


def bloc_carte(nom, coord):
    lat, lon = coord
    return (
        '<section class="pg-sec pg-sec--fond situe"><div class="wrap">'
        '<p class="eyebrow">Sur la carte</p>'
        '<h2 id="t-ou">Où se trouve %s ?</h2>'
        '<figure class="situe__cadre"><div class="situe__map" data-situe=\'%s\'></div>'
        '<figcaption class="situe__note">Fond de carte &copy; '
        '<a href="https://www.openstreetmap.org/copyright" target="_blank" '
        'rel="noopener">OpenStreetMap</a>, contributeurs.</figcaption>'
        '</figure></div></section>'
        % (H.escape(nom), H.escape('{"nom":%s,"lat":%s,"lon":%s}'
                                   % (('"%s"' % nom), lat, lon), quote=True)))


FEUILLE = (
    '<style data-blocs="destination">'
    # La frise arrive sans sa feuille : ces règles vivent dans le gabarit
    # programme, qu'une page destination ne porte pas. Sans elles, les
    # douze mois se lisaient comme une liste numérotée. Valeurs reprises
    # telles quelles de la maquette programme.
    + H_ + '.pg .quand-dest .quand{margin:0}'
    + H_ + '.pg .quand__intro{font-size:1.06rem;color:var(--texte,#5D5D5D);margin:0 0 18px}'
    + H_ + '.pg .quand__intro b{color:var(--nuit-900,#095360)}'
    + H_ + '.pg .quand__frise{list-style:none;margin:0;padding:0;display:grid;'
    'grid-template-columns:repeat(12,1fr);gap:4px}'
    + H_ + '.pg .quand__frise li{display:grid;gap:2px;padding:12px 6px;'
    'border-radius:var(--r-s,10px);text-align:center;font-family:"Manrope",sans-serif;'
    'background:var(--fond,#F7F7F9);border:1px solid var(--ligne-pg,#E4E4EA);min-width:0}'
    + H_ + '.pg .quand__frise b{font-size:.875rem;color:var(--noir,#12211F)}'
    + H_ + '.pg .quand__frise .q-t{font-size:.95rem;font-weight:700;'
    'color:var(--nuit-900,#095360);white-space:nowrap}'
    + H_ + '.pg .quand__frise .q-1{background:var(--teal-fond,#EAF6F9);border-color:#D1E8EB}'
    + H_ + '.pg .quand__frise .q-2{background:var(--or-fond,#FEEDDC);border-color:#F5D9B0}'
    + H_ + '.pg .quand__frise .q-3{background:var(--rouge-fond,#FBE9E3);border-color:#F0C9BE}'
    + H_ + '.pg .quand__frise .q-ok{box-shadow:inset 0 -3px 0 var(--bleu,#106D7C)}'
    + H_ + '.pg .quand__leg{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;'
    'margin:12px 0 0;font-family:"Manrope",sans-serif;font-size:.875rem;'
    'color:var(--gris-lis,#5B6870)}'
    + H_ + '.pg .quand__leg span:not(.q-src){padding:3px 10px;'
    'border-radius:var(--r-pill,99px);border:1px solid var(--ligne-pg,#E4E4EA)}'
    + H_ + '.pg .quand__leg .q-1{background:var(--teal-fond,#EAF6F9)}'
    + H_ + '.pg .quand__leg .q-2{background:var(--or-fond,#FEEDDC)}'
    + H_ + '.pg .quand__leg .q-3{background:var(--rouge-fond,#FBE9E3)}'
    + H_ + '.pg .quand__leg .q-src a{color:var(--teal-txt,#106D7C);text-decoration:underline;'
    'text-underline-offset:2px}'
    '@media (max-width:900px){' + H_ + '.pg .quand__frise{grid-template-columns:repeat(6,1fr)}}'
    '@media (max-width:520px){' + H_ + '.pg .quand__frise{grid-template-columns:repeat(3,1fr)}}'
    + H_ + '.pg .situe__cadre{display:block;width:100%;max-width:820px;margin:18px auto 0;'
    'background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);border-radius:18px;'
    'padding:18px 20px}'
    + H_ + '.pg .situe__map{width:100%;height:340px;border-radius:14px;'
    'border:1px solid var(--ligne-pg,#E4E4EA);background:var(--teal-fond,#EAF6F9);z-index:0}'
    + H_ + '.pg .situe__map .leaflet-container{font-family:"Manrope",sans-serif}'
    + H_ + '.pg .situe__pin{display:grid;place-items:center;width:26px;height:26px;'
    'border-radius:50%;background:var(--nuit-900,#095360);color:#fff;'
    'border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.25)}'
    + H_ + '.pg .situe__pin span{display:block;width:8px;height:8px;'
    'border-radius:50%;background:#fff}'
    + H_ + '.pg .situe__note{margin:12px 0 0;text-align:center;'
    'font-family:"Manrope",sans-serif;font-size:.82rem;color:var(--gris-lis,#5B6870)}'
    + H_ + '.pg .situe__note a{color:var(--teal-txt,#106D7C)}'
    '@media (max-width:640px){' + H_ + '.pg .situe__map{height:280px}}'
    '</style>')

SCRIPT = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script data-blocs="destination">
(function(){
  var d = document.querySelector('[data-situe]');
  if(!d || typeof L === 'undefined') return;
  var p;
  try { p = JSON.parse(d.getAttribute('data-situe')); } catch(e) { return; }
  var carte = L.map(d, {scrollWheelZoom:false, attributionControl:false})
               .setView([p.lat, p.lon], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
              {maxZoom:17}).addTo(carte);
  L.marker([p.lat, p.lon], {icon: L.divIcon({className:'',
    html:'<span class="situe__pin"><span></span></span>',
    iconSize:[26,26], iconAnchor:[13,13]})}).addTo(carte).bindPopup(p.nom);
  // La molette reste à la page : on ne piège pas le défilement.
  carte.on('click', function(){ carte.scrollWheelZoom.enable(); });
  carte.on('mouseout', function(){ carte.scrollWheelZoom.disable(); });
})();
</script>"""


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def corriger(h, titre):
    faits = []
    # On se pose après la grille des séjours : on a vu ce qu'on peut faire,
    # on demande alors quand y aller et où c'est.
    d = h.find('<div class="fac"')
    if d < 0:
        d = h.find('<div class="cartes')
    if d < 0:
        return h, []
    s = h.rfind('<section', 0, d)
    f = _fin(h, s, 'section') if s >= 0 else -1
    if f < 0:
        return h, []

    pose = ''
    if 'class="quand__frise"' not in h:
        pose += bloc_quand(titre)
        faits.append('« Quand partir » posé (%s)' % theme_de(titre))
    nom, coord = lieu_de(titre)
    if 'data-situe' not in h:
        if nom:
            pose += bloc_carte(nom, coord)
            faits.append('carte de situation (%s)' % nom)
        else:
            faits.append('⚠ lieu introuvable dans la table — pas de carte')
    if pose:
        h = h[:f] + pose + h[f:]

    ancienne = re.search(r'<style data-blocs="destination">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-blocs="destination">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<link[^>]+leaflet\.css[^>]*>\s*<script[^>]+leaflet\.js[^>]*></script>\s*'
               r'<script data-blocs="destination">.*?</script>', '', h, flags=re.S)
    h += FEUILLE
    if 'data-situe' in h:
        h += SCRIPT
    return h, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    p.add_argument('--local', nargs='*')
    a = p.parse_args()

    if a.local:
        for f in a.local:
            h = open(f, encoding='utf-8').read()
            t = re.search(r'<title>(.*?)</title>', h, re.S)
            titre = re.sub(r'\s*[-–|].*$', '', t.group(1)).strip() if t else os.path.basename(f)
            neuf, faits = corriger(h, titre)
            open(f.replace('.html', '-blocs.html'), 'w', encoding='utf-8').write(neuf)
            print('%-46s %-34s %s' % (os.path.basename(f)[:46], titre[:34],
                                      ' · '.join(faits) or 'rien'))
        return

    dep = SourceFileLoader('dep', os.path.join(OUTILS, 'deployer.py')).load_module()
    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id'])
                  if k['status'] != 'trash' and k['slug'].startswith('refonte-destination-')]

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        titre = (p_.get('title') or {}).get('raw', '')
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut, titre)
        if not faits:
            continue
        print('   #%-6d %-38s %s' % (k['id'], titre[:38], ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-blocs="destination"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) destination complétée(s).' % n)


if __name__ == '__main__':
    main()
