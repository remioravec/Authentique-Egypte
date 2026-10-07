#!/usr/bin/env python3
"""L'accueil, sur les onze remarques de Mélanie du 6 octobre.

    WP_AUTH='compte:mdp' python3 outils/retours-07-10-accueil.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-07-10-accueil.py --appliquer

  12656 « enlever ce texte » — « Aucun critère : les 12 itinéraires de cette
        page. » La phrase reste vide tant qu'on n'a rien choisi. Au passage,
        le script la réécrivait à « les 8 itinéraires » après « Tout effacer ».
  12657 « mettre un espace entre composez votre voyage et la partie blanche,
        recentrer, ça fait pâté » — le titre du compositeur est centré, et
        le bloc respire.
  12658 « changer le design du texte » — les titres de l'accueil étaient
        noirs ; ceux des 58 autres pages sont bleu nuit. Même couleur ici,
        et le surtitre « Nos itinéraires » que portent les autres sections.
  12659 « ajouter le prix » — la croisière en bateau à voile disait « sur
        devis » ; sa propre page dit « à partir de 1 895 € ».
  12660 « le jour par jour est trop répétitif » — douze libellés, tous
        différents.
  12661 « une carte d'Égypte pour illustrer » — une carte, les neuf
        destinations du site épinglées, chacune menant à sa page.
  12662 « enlever ce texte » — « Chaque page détaille les sites… ».
  12663 « mettre ce bloc au dessus » — « Quatre étapes » remonte juste sous
        les itinéraires.
  12664, 12665 « enlever illimité », « enlever le jour J ».
  12669 « pourquoi cette partie ? Le mieux est de l'enlever » — le bloc
        « Pour aller plus loin » quitte l'accueil (et l'outil de maillage
        ne l'y remettra plus).
  12677 le voile de la photo du haut, plus léger ici aussi.

Et « Notre agence locale au Caire », dernier écho de la formule que Mélanie
a fait retirer partout (12256), devient « Découvrir l'agence ».
"""

import argparse
import base64
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
E = '.elementor-template-canvas'

LIBELLES = {
    'pyramides-et-croisiere-sur-le-nil': 'Voir l’itinéraire sur le Nil',
    'le-caire-et-croisiere-sur-un-bateau-a-voile': 'Découvrir la dahabeya',
    'croisiere-sur-le-lac-nasser': 'Voir la croisière sur le lac',
    'mer-rouge': 'Voir le séjour en famille',
    'excursion-a-loasis-de-siwa': 'Partir vers Siwa',
    'excursion-dans-le-desert-blanc': 'Voir l’excursion au désert',
    'sainte-catherine': 'Voir la nuit au monastère',
    'itineraire-sinai-sainte-catherine-mont-moise-et-mer-rouge':
        'Voir le circuit du Sinaï',
    'excursion-a-loasis-de-fayoum': 'Voir les deux jours au Fayoum',
    'roadtrip-en-egypte': 'Voir le roadtrip',
    'pyramides-louxor-et-mer-rouge-en-famille': 'Voir Louxor et la mer Rouge',
    'campement-au-coeur-du-mont-moise': 'Voir l’ascension du mont Moïse',
}

# Les coordonnées sont celles que chaque page de destination porte déjà.
LIEUX = [
    ('Le Caire', 30.0444, 31.2357, '/voyage-au-caire/', 'right'),
    ('Alexandrie', 31.2001, 29.9187, '/voyage-a-alexandrie/', 'top'),
    ('Fayoum', 29.3084, 30.8428, '/voyage-a-fayoum/', 'left'),
    ('Désert noir', 28.1, 28.85, '/desert-noir/', 'left'),
    ('Désert blanc', 27.25, 28.15, '/desert-blanc/', 'left'),
    ('Mont Sinaï', 28.5586, 33.9756, '/mont-sinai/', 'right'),
    ('Louxor', 25.6872, 32.6396, '/voyage-a-louxor/', 'right'),
    ('Assouan', 24.0889, 32.8998, '/voyage-a-assouan/', 'right'),
    ('Lac Nasser', 23.2, 32.75, '/lac-nasser/', 'left'),
]

CARTE = (
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/'
    'leaflet/1.9.4/leaflet.css">'
    '<figure class="carte-eg"><div class="carte-eg__map" id="carte-eg" '
    'role="img" aria-label="Carte de l’Égypte : ' +
    ', '.join(n for n, *_ in LIEUX) + '"></div>'
    '<figcaption>&copy; <a href="https://www.openstreetmap.org/copyright" '
    'target="_blank" rel="noopener">OpenStreetMap</a></figcaption></figure>'
    # Écrit sans esperluette ni chevron : WordPress encode « && » au rendu.
    '<script id="carte-eg-js">(function(){'
    'var el=document.getElementById("carte-eg");if(!el){return;}'
    'var P=' + json.dumps([[n, la, lo, SITE + u, d] for n, la, lo, u, d in LIEUX],
                          ensure_ascii=False) + ';'
    'function pastille(){var s=document.createElement("span");'
    's.className="carte-eg__pin";return s;}'
    'function va(){if(typeof L==="undefined"){return;}'
    'var m=L.map(el,{scrollWheelZoom:false,attributionControl:false});'
    'L.tileLayer("https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",'
    '{maxZoom:12}).addTo(m);var b=[];'
    'P.forEach(function(p){'
    'var mk=L.marker([p[1],p[2]],{title:p[0],icon:L.divIcon({className:"",'
    'html:pastille(),iconSize:[18,18],iconAnchor:[9,9]})}).addTo(m);'
    'var a=document.createElement("a");a.href=p[3];a.textContent=p[0];'
    'mk.bindTooltip(a,{permanent:true,direction:p[4],interactive:true,'
    'offset:p[4]==="left"?[-8,0]:(p[4]==="right"?[8,0]:[0,-8]),'
    'className:"carte-eg__lab"});'
    'mk.on("click",function(){window.location.href=p[3];});'
    'b.push([p[1],p[2]]);});'
    'm.fitBounds(b,{paddingTopLeft:[64,34],paddingBottomRight:[48,18]});'
    'm.on("click",function(){m.scrollWheelZoom.enable();});'
    'm.on("mouseout",function(){m.scrollWheelZoom.disable();});}'
    'if(typeof L==="undefined"){var s=document.createElement("script");'
    's.src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js";'
    's.onload=va;document.head.appendChild(s);}else{va();}'
    '})();</script>')

STYLE = (
    '<style id="accueil-07-10">'
    # 12677 · le voile de la photo du haut
    + E + ' .hero .hero__bg::after{background:'
    'linear-gradient(100deg,rgba(9,77,96,.70) 0%,rgba(9,77,96,.56) 40%,'
    'rgba(20,129,148,.28) 70%,rgba(20,129,148,.10) 100%),'
    'linear-gradient(180deg,rgba(9,77,96,.30) 0%,rgba(9,77,96,0) 30%,'
    'rgba(9,77,96,0) 70%,rgba(9,77,96,.32) 100%)}'
    '@media (max-width:860px){' + E + ' .hero .hero__bg::after{background:'
    'linear-gradient(180deg,rgba(9,77,96,.60) 0%,rgba(9,77,96,.46) 45%,'
    'rgba(9,77,96,.64) 100%)}}'
    + E + ' .hero h1,' + E + ' .hero .hero__lede{'
    'text-shadow:0 2px 14px rgba(3,38,45,.8),0 1px 3px rgba(3,38,45,.6)}'
    # 12657 · le compositeur respire
    + E + ' .compo.compo{padding:30px 32px 26px}'
    + E + ' .compo.compo .compo__t{flex-direction:column;align-items:center;'
    'text-align:center;gap:6px;margin:0 0 24px}'
    + E + ' .compo.compo .compo__t h2{font-size:1.5rem;'
    'color:var(--nuit-900,#094D60)}'
    + E + ' .compo.compo .compo__t p::before{content:none}'
    + E + ' .compo.compo .compo__res{margin-top:24px}'
    + E + ' .compo.compo .compo__phrase:empty{display:none}'
    + E + ' .compo.compo .compo__res:has(.compo__phrase:empty){'
    'justify-content:center}'
    + E + ' .compo.compo .compo__res:has(.compo__phrase:empty) .compo__act{'
    'margin-left:0}'
    '@media (max-width:640px){' + E + ' .compo.compo{padding:22px 18px 18px}'
    + E + ' .compo.compo .compo__t{margin-bottom:16px}}'
    # 12658 · les titres de l'accueil, bleu nuit comme partout
    + E + ' #main .section:not(.section--nuit) .wrap > h2,'
    + E + ' #main #titre-res{color:#116676}'
    # 12661 · la carte
    '.carte-eg{margin:6px 0 30px}'
    '.carte-eg__map{height:500px;border-radius:18px;'
    'border:1px solid var(--ligne,#E4E4EA);background:#BEE6F1;z-index:0}'
    '@media (max-width:640px){.carte-eg__map{height:380px}}'
    '.carte-eg__pin{display:block;width:18px;height:18px;border-radius:50%;'
    'background:#094D60;border:3px solid #fff;'
    'box-shadow:0 2px 6px rgba(0,0,0,.3);cursor:pointer}'
    '.leaflet-tooltip.carte-eg__lab{background:#fff;border:1px solid #E4E4EA;'
    'border-radius:999px;padding:3px 10px;font-weight:700;font-size:13px;'
    'color:#094D60;box-shadow:0 2px 8px rgba(9,77,96,.15)}'
    '.leaflet-tooltip.carte-eg__lab::before{display:none}'
    '.carte-eg__lab a{color:inherit;text-decoration:none}'
    '.carte-eg figcaption{text-align:right;font-size:11px;opacity:.5;'
    'margin:8px 0 0}'
    '</style>')


def bornes_section(h, debut):
    """(début, fin) de la <section> qui commence à `debut`."""
    p, k = 0, debut
    while k < len(h):
        if h.startswith('<section', k):
            p += 1
        elif h.startswith('</section>', k):
            p -= 1
            if p == 0:
                return debut, k + len('</section>')
        k += 1
    return None


def corriger(h):
    j = {}

    def note(c, n):
        if n:
            j[c] = j.get(c, 0) + n

    # 12656 · la phrase par défaut, dans le balisage et dans le script
    h, n = re.subn(r'(<p class="compo__phrase" id="phrase"[^>]*>)Aucun critère'
                   r'(?:(?!</p>).)*?(</p>)', r'\1\2', h, flags=re.S)
    note('12656 phrase par défaut retirée', n)
    h, n = re.subn(r"phrase\.innerHTML='Aucun critère : <b>les \d+ itinéraires</b>"
                   r" de cette page\. Choisissez pour affiner\.';",
                   "phrase.innerHTML='';", h)
    note('12656 script : plus de « les 8 itinéraires »', n)

    # 12658 · le surtitre des itinéraires
    if '<p class="eyebrow">Nos itinéraires</p><h2 id="titre-res">' not in h:
        h, n = re.subn(r'(<section class="section section--fond" id="resultats">'
                       r'<div class="wrap">)(<h2 id="titre-res">)',
                       r'\1<p class="eyebrow">Nos itinéraires</p>\2', h)
        note('12658 surtitre', n)

    # 12659 · le prix de la croisière en bateau à voile
    k = h.find('/programs/le-caire-et-croisiere-sur-un-bateau-a-voile/">Le Caire')
    if k > 0:
        f = h.find('</article>', k)
        seg = h[k:f]
        neuf = seg.replace('<span class="prix"><small>Prix</small><b>sur devis</b></span>',
                           '<span class="prix"><small>À partir de</small><b>1895 €</b>'
                           '<i>/ Personne</i></span>')
        if neuf != seg:
            h = h[:k] + neuf + h[f:]
            note('12659 prix de la dahabeya', 1)

    # 12660 · douze libellés
    def libelle(m):
        slug, attrs = m.group(1), m.group(2)
        t = LIBELLES.get(slug)
        if not t:
            return m.group(0)
        titre = re.search(r'aria-label="[^:"]*:\s*([^"]*)"', attrs)
        attrs = re.sub(r'aria-label="[^"]*"',
                       'aria-label="%s : %s"' % (t, titre.group(1) if titre else ''),
                       attrs)
        return ('<a href="%s/programs/%s/" %s>%s ' % (SITE, slug, attrs, t))
    h, n = re.subn(r'<a href="https://authentiquegypte\.com/programs/([a-z0-9-]+)/" '
                   r'(class="lien-fl" aria-label="[^"]*")>\s*Le jour par jour\s*',
                   libelle, h)
    note('12660 libellés variés', n)

    # 12662 · le texte sous « Six des régions », remplacé par la carte (12661)
    if 'id="carte-eg"' not in h:
        h, n = re.subn(r'<p class="lede" style="margin-bottom:32px">Chaque page '
                       r'détaille les sites, la durée conseillée et la meilleure '
                       r'période\.</p>', CARTE, h)
        note('12662 texte retiré · 12661 carte posée', n)

    # 12664, 12665 · « Illimité », « Le jour J »
    h, n = re.subn(r'<span class="quand">(?:Illimité|Le jour J)</span>', '', h)
    note('12664 · 12665 pastilles retirées', n)
    h, n = re.subn(r'(<a class="vers" href="https://authentiquegypte\.com/'
                   r'qui-sommes-nous/">)Notre agence locale au Caire', r'\1Découvrir l’agence', h)
    note('12256 « agence locale au Caire »', n)

    # 12669 · le bloc « Pour aller plus loin »
    k = h.find('<section class="pg-sec pg-sec--serre" data-maillage>')
    if k > 0:
        b = bornes_section(h, k)
        h = h[:b[0]] + h[b[1]:]
        note('12669 « Pour aller plus loin » retiré', 1)

    # 12663 · « Quatre étapes » remonte sous les itinéraires
    k = h.find('<section class="section section--creme">')
    r = h.find('<section class="section section--fond" id="resultats">')
    if 0 < r < k:
        bk = bornes_section(h, k)
        br = bornes_section(h, r)
        etapes = h[bk[0]:bk[1]]
        if h[br[1]:br[1] + 60].lstrip().startswith('<section class="section section--creme">'):
            pass  # déjà en place
        else:
            h = h[:bk[0]] + h[bk[1]:]
            br = bornes_section(h, r)
            h = h[:br[1]] + etapes + h[br[1]:]
            note('12663 « Quatre étapes » remonté', 1)

    # la feuille, une seule fois
    h = re.sub(r'<style id="accueil-07-10">.*?</style>', '', h, flags=re.S)
    m = h.find('<main')
    h = h[:m] + STYLE + h[m:]
    return h, j


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
    B = SITE + '/wp-json/wp/v2/pages/38'
    for essai in range(5):
        r = S.get(B, params={'context': 'edit'}, timeout=300)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    h = (r.json().get('content') or {}).get('raw', '')
    neuf, j = corriger(h)
    for k, v in sorted(j.items()):
        print('   %-46s %d' % (k, v))
    print('%d → %d octets' % (len(h), len(neuf)))
    sections = [x for x in re.findall(r'<section[^>]*>', neuf[neuf.find('<main'):])]
    print('ordre des sections :', ' | '.join(s[9:60] for s in sections))
    if a.essai:
        open('/tmp/claude-0/qc/accueil-essai.html', 'w').write(neuf)
        return
    for essai in range(4):
        r = S.post(B, json={'content': '<!-- wp:html -->\n' + neuf
                            + '\n<!-- /wp:html -->'}, timeout=900)
        if r.status_code < 300:
            break
        time.sleep(2 ** essai)
    else:
        raise SystemExit('écriture refusée')
    print('accueil écrit.')


if __name__ == '__main__':
    main()
