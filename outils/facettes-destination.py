#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Des filtres à facettes sur les pages destination, et de vraies cartes.

    WP_AUTH='compte:mot de passe' ./outils/facettes-destination.py [--essai]
    ./outils/facettes-destination.py --local maquettes/site/destination-*.html

La section « Les séjours qui passent par … » alignait des cartes et rien
d'autre. Sur une page qui en porte six, le visiteur lisait six fois le
même bloc pour trouver celui qui dure deux jours. Elle devient une
colonne de filtres à gauche et une grille de cartes à droite ; le tri se
fait dans la page, sans rechargement.

LES FACETTES SORTENT DES CARTES, PAS DE MA TÊTE. La durée est lue dans
la pastille de chaque carte, le budget dans son prix. Aucune facette
n'est proposée sur un critère qui n'est pas écrit sur la carte : un
filtre « avec guide francophone » serait une promesse que la page ne
peut pas tenir.

LES BORNES SUIVENT LES DONNÉES. Les séjours vont de 1 à 9 jours et de
185 à 1895 € : d'où « 1 à 2 jours / 3 à 5 / 6 et plus » et « moins de
500 € / 500 à 1 000 / plus de 1 000 ». Une tranche qui ne contient aucun
séjour n'est pas affichée — un filtre qui ne filtre rien fait douter de
tous les autres.

PAS DE FILTRES SOUS QUATRE SÉJOURS. Quatre des neuf pages n'en portent
qu'un seul : y poser une colonne de filtres serait un décor. En dessous
de MINIMUM, la section garde ses cartes redessinées, sans facettes.

CE QUE FAIT LE JAVASCRIPT. Cocher masque et démasque, rien de plus :
pas de requête, pas de rechargement, pas de saut de page. Les compteurs
de chaque option se recalculent selon les autres groupes cochés, donc on
ne peut pas tomber sur une case qui mène à zéro résultat. À l'intérieur
d'un groupe les choix s'additionnent (2 jours OU 4 jours), entre groupes
ils se croisent (2 jours ET moins de 500 €). Sans JavaScript, toutes les
cartes restent visibles : la colonne de filtres n'est posée que par le
script.
"""

import argparse
import glob
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

MINIMUM = 4

H = '.elementor-template-canvas '

# Les tranches, dans l'ordre où elles se lisent.
DUREES = [('1-2', '1 à 2 jours', lambda j: j <= 2),
          ('3-5', '3 à 5 jours', lambda j: 3 <= j <= 5),
          ('6+', '6 jours et plus', lambda j: j >= 6)]
BUDGETS = [('0-500', "moins de 500 €", lambda p: p < 500),
           ('500-1000', "500 à 1 000 €", lambda p: 500 <= p < 1000),
           ('1000+', "plus de 1 000 €", lambda p: p >= 1000)]


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def _nombre(t):
    """Le premier nombre d'un texte, espaces fines comprises."""
    m = re.search(r'\d[\d   ]*', t or '')
    return int(re.sub(r'[^\d]', '', m.group(0))) if m else None


def lire_carte(c):
    """La durée en jours et le prix en euros, tels qu'ils sont écrits."""
    d = re.search(r'<span class="puce">(.*?)</span>', c, re.S)
    p = re.search(r'<b>([\d   ]+)\s*€</b>', c)
    return _nombre(d.group(1) if d else ''), _nombre(p.group(1) if p else '')


FEUILLE = (
    '<style data-facettes="v1">'
    # La zone : filtres à gauche, cartes à droite.
    + H + '.pg .fac{display:grid;grid-template-columns:248px minmax(0,1fr);'
    'gap:34px;align-items:start;margin:26px 0 0}'
    + H + '.pg .fac__col{position:sticky;top:96px;display:grid;gap:18px}'
    + H + '.pg .fac__tete{display:flex;align-items:baseline;justify-content:space-between;gap:10px}'
    + H + '.pg .fac__tete p{margin:0;font-family:"Manrope",sans-serif;font-size:.78rem;'
    'font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--teal-txt,#106D7C)}'
    + H + '.pg .fac__raz{background:none;border:0;padding:0;font-family:"Manrope",sans-serif;'
    'font-size:.86rem;color:var(--teal-txt,#106D7C);text-decoration:underline;'
    'text-underline-offset:3px;cursor:pointer;min-height:auto}'
    + H + '.pg .fac__raz[hidden]{display:none}'
    + H + '.pg .fac__g{border:0;margin:0;padding:0}'
    + H + '.pg .fac__g legend{padding:0 0 9px;font-family:"Manrope",sans-serif;'
    'font-size:.95rem;font-weight:700;color:var(--nuit-900,#095360)}'
    + H + '.pg .fac__o{display:flex;align-items:center;gap:10px;padding:8px 10px;margin:0 -10px;'
    'border-radius:10px;font-size:.95rem;color:var(--texte,#5D5D5D);cursor:pointer;min-height:44px}'
    + H + '.pg .fac__o:hover{background:var(--teal-fond,#EAF6F9)}'
    + H + '.pg .fac__o input{width:18px;height:18px;accent-color:var(--teal-txt,#106D7C);'
    'margin:0;flex:none;cursor:pointer}'
    + H + '.pg .fac__o b{font-weight:500;flex:1 1 auto}'
    + H + '.pg .fac__o small{font-family:"Manrope",sans-serif;font-size:.8rem;'
    'color:var(--gris-lis,#5B6870);font-variant-numeric:tabular-nums}'
    + H + '.pg .fac__o[data-vide]{opacity:.4}'
    + H + '.pg .fac__cpt{margin:0 0 16px;font-family:"Manrope",sans-serif;font-size:.92rem;'
    'color:var(--gris-lis,#5B6870);font-variant-numeric:tabular-nums}'
    + H + '.pg .fac__rien{margin:0;padding:34px 26px;text-align:center;background:var(--fond,#F7F7F9);'
    'border:1px dashed var(--ligne-pg,#E4E4EA);border-radius:var(--r-l,20px);'
    'color:var(--texte,#5D5D5D)}'
    + H + '.pg .fac__rien[hidden]{display:none}'

    # Les cartes, redessinées.
    + H + '.pg .cartes.cartes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}'
    # Le moule pose flex-basis et max-width:calc((100% - 26px)/2) sur chaque
    # carte, pour une rangée en flex. Dans une grille, ce 100% est celui de
    # la COLONNE : la carte se retrouvait à 206px dans une case de 438.
    + H + '.pg .fac .carte.carte{max-width:none;flex-basis:auto;width:auto;'
    'position:relative;display:flex;flex-direction:column;margin:0;'
    'background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);border-radius:18px;overflow:hidden;'
    'box-shadow:0 1px 2px rgba(12,34,37,.04);transition:box-shadow .25s,transform .25s}'
    + H + '.pg .fac .carte.carte:hover{box-shadow:0 10px 28px rgba(12,34,37,.10);transform:translateY(-3px)}'
    + H + '.pg .fac .carte__img{position:relative;margin:0;aspect-ratio:4/3;overflow:hidden;'
    'background:var(--fond,#F7F7F9)}'
    + H + '.pg .fac .carte__img img{width:100%;height:100%;object-fit:cover;display:block;'
    'transition:transform .6s var(--ease,ease)}'
    + H + '.pg .fac .carte.carte:hover .carte__img img{transform:scale(1.06)}'
    + H + '.pg .fac .carte__duree{position:absolute;left:12px;top:12px;'
    'background:rgba(255,255,255,.94);color:var(--nuit-900,#095360);'
    'font-family:"Manrope",sans-serif;font-size:.8rem;font-weight:800;'
    'padding:6px 12px;border-radius:99px;backdrop-filter:blur(4px)}'
    + H + '.pg .fac .carte__corps{display:flex;flex-direction:column;gap:8px;flex:1 1 auto;padding:18px 20px 20px}'
    + H + '.pg .fac .carte__corps h3{margin:0;font-size:1.08rem;line-height:1.3}'
    + H + '.pg .fac .carte__corps h3 a{color:var(--nuit-900,#095360);text-decoration:none}'
    + H + '.pg .fac .carte__corps h3 a::after{content:"";position:absolute;inset:0}'
    + H + '.pg .fac .carte__route{margin:0;font-size:.93rem;line-height:1.55;color:var(--texte,#5D5D5D);'
    'display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}'
    + H + '.pg .fac .carte__meta{display:none}'
    + H + '.pg .fac .carte__pied{display:flex;align-items:center;justify-content:space-between;'
    'gap:10px;flex-wrap:wrap;margin-top:auto;padding-top:14px;'
    'border-top:1px solid var(--ligne-2,#EFEFF3)}'
    + H + '.pg .fac .carte__pied .prix{display:grid;line-height:1.15}'
    + H + '.pg .fac .carte__pied .prix small{font-family:"Manrope",sans-serif;font-size:.72rem;'
    'letter-spacing:.05em;text-transform:uppercase;color:var(--gris-lis,#5B6870)}'
    + H + '.pg .fac .carte__pied .prix b{font-family:"Manrope",sans-serif;font-size:1.32rem;'
    'font-weight:800;color:var(--nuit-900,#095360);font-variant-numeric:tabular-nums;'
    'white-space:nowrap}'
    + H + '.pg .fac .carte__pied .prix i{font-style:normal;font-size:.76rem;color:var(--gris-lis,#5B6870)}'
    + H + '.pg .fac .carte__pied .lien-fl{position:relative;z-index:1;font-family:"Manrope",sans-serif;'
    'font-size:.88rem;font-weight:700;color:var(--teal-txt,#106D7C);white-space:nowrap}'
    + H + '.pg .fac .carte[hidden]{display:none}'
    # Au bureau, le <details> n'est qu'un conteneur : ni cadre, ni résumé.
    + H + '.pg .fac__pli{border:0;padding:0}'
    + H + '.pg .fac__pli>summary{display:none}'

    # Sur tablette et téléphone : les filtres se replient au-dessus.
    '@media (max-width:1040px){'
    + H + '.pg .fac{grid-template-columns:1fr;gap:20px}'
    + H + '.pg .fac__col{position:static}'
    + H + '.pg .fac__pli{border:1px solid var(--ligne-pg,#E4E4EA);border-radius:14px;'
    'background:#fff;padding:0 16px}'
    + H + '.pg .fac__pli>summary{display:flex;list-style:none;cursor:pointer;padding:15px 0;min-height:48px;'
    'display:flex;align-items:center;justify-content:space-between;gap:10px;'
    'font-family:"Manrope",sans-serif;font-weight:700;color:var(--nuit-900,#095360)}'
    + H + '.pg .fac__pli>summary::-webkit-details-marker{display:none}'
    + H + '.pg .fac__pli[open]>summary{border-bottom:1px solid var(--ligne-2,#EFEFF3)}'
    + H + '.pg .fac__col{gap:16px;padding:0 0 16px}}'
    '@media (max-width:720px){'
    + H + '.pg .cartes.cartes{grid-template-columns:1fr}}'
    '@media (prefers-reduced-motion:reduce){'
    + H + '.pg .fac .carte.carte,' + H + '.pg .fac .carte__img img{transition:none}'
    + H + '.pg .fac .carte.carte:hover{transform:none}}'
    '</style>'
)

SCRIPT = """<script data-facettes="v1">
(function(){
  document.querySelectorAll('[data-fac]').forEach(function(zone){
    var cartes = [].slice.call(zone.querySelectorAll('.carte'));
    var cases  = [].slice.call(zone.querySelectorAll('input[type=checkbox][data-g]'));
    var cpt    = zone.querySelector('[data-fac-cpt]');
    var rien   = zone.querySelector('[data-fac-rien]');
    var raz    = zone.querySelector('[data-fac-raz]');
    if(!cartes.length || !cases.length) return;

    function choisis(){
      var g = {};
      cases.forEach(function(c){ if(c.checked){ (g[c.dataset.g] = g[c.dataset.g] || []).push(c.value); } });
      return g;
    }
    // Dans un groupe les choix s'additionnent, entre groupes ils se croisent.
    // « sauf » sert aux compteurs : on compte ce que donnerait un groupe
    // si on ne tenait pas compte de lui-même.
    function garde(carte, g, sauf){
      for(var nom in g){
        if(nom === sauf) continue;
        if(g[nom].indexOf(carte.dataset[nom]) < 0) return false;
      }
      return true;
    }
    function passe(){
      var g = choisis(), visibles = 0;
      cartes.forEach(function(c){
        var ok = garde(c, g, null);
        c.hidden = !ok;
        if(ok) visibles++;
      });
      cases.forEach(function(c){
        var n = cartes.filter(function(k){
          return k.dataset[c.dataset.g] === c.value && garde(k, g, c.dataset.g);
        }).length;
        var pastille = c.parentNode.querySelector('small');
        if(pastille) pastille.textContent = n;
        if(n === 0 && !c.checked) c.parentNode.setAttribute('data-vide','');
        else c.parentNode.removeAttribute('data-vide');
      });
      if(cpt) cpt.textContent = visibles === cartes.length
        ? (cartes.length + (cartes.length > 1 ? ' séjours' : ' séjour'))
        : (visibles + ' séjour' + (visibles > 1 ? 's' : '') + ' sur ' + cartes.length);
      if(rien) rien.hidden = visibles !== 0;
      if(raz) raz.hidden = !cases.some(function(c){ return c.checked; });
    }
    cases.forEach(function(c){ c.addEventListener('change', passe); });
    if(raz) raz.addEventListener('click', function(){
      cases.forEach(function(c){ c.checked = false; });
      passe();
    });
    passe();
  });
})();
</script>"""


def _groupe(nom, legende, options, cartes, cle):
    """Un groupe de facettes, privé des tranches que personne ne remplit."""
    lignes = []
    for val, libelle, test in options:
        n = sum(1 for c in cartes if c[cle] is not None and test(c[cle]))
        if not n:
            continue
        lignes.append(
            '<label class="fac__o"><input type="checkbox" data-g="%s" value="%s">'
            '<b>%s</b><small>%d</small></label>' % (nom, val, libelle, n))
    if len(lignes) < 2:
        return ''
    return ('<fieldset class="fac__g"><legend>%s</legend>%s</fieldset>'
            % (legende, ''.join(lignes)))


def _tranche(options, valeur):
    if valeur is None:
        return ''
    for val, _, test in options:
        if test(valeur):
            return val
    return ''


def refaire_section(bloc):
    """La section des séjours : filtres à gauche, cartes à droite."""
    cartes = re.findall(r'<article class="carte">.*?</article>', bloc, re.S)
    if not cartes:
        return bloc, None

    lues = []
    for c in cartes:
        j, p = lire_carte(c)
        lues.append({'html': c, 'duree': j, 'prix': p})

    # La durée quitte la liste des méta pour venir sur la photo.
    neuves = []
    for x in lues:
        c = x['html']
        c = re.sub(r'<div class="carte__meta">.*?</div>', '', c, flags=re.S)
        if x['duree'] is not None:
            pastille = ('<span class="carte__duree">%d jour%s</span>'
                        % (x['duree'], 's' if x['duree'] > 1 else ''))
            c = re.sub(r'(<div class="carte__img">)', r'\1' + pastille, c, count=1)
        c = c.replace(
            '<article class="carte">',
            '<article class="carte" data-duree="%s" data-prix="%s">'
            % (_tranche(DUREES, x['duree']), _tranche(BUDGETS, x['prix'])), 1)
        neuves.append(c)

    grille = '<div class="cartes cartes--2">%s</div>' % ''.join(neuves)

    if len(cartes) < MINIMUM:
        # Pas de colonne de filtres, mais les cartes redessinées : la zone
        # porte quand même data-fac pour que la feuille s'applique.
        zone = '<div class="fac" data-fac style="grid-template-columns:1fr">%s</div>' % grille
        return zone, len(cartes)

    groupes = (_groupe('duree', 'Durée', DUREES, lues, 'duree')
               + _groupe('prix', 'Budget', BUDGETS, lues, 'prix'))
    if not groupes:
        zone = '<div class="fac" data-fac style="grid-template-columns:1fr">%s</div>' % grille
        return zone, len(cartes)

    colonne = (
        '<div class="fac__col">'
        '<div class="fac__tete"><p>Affiner</p>'
        '<button type="button" class="fac__raz" data-fac-raz hidden>Tout effacer</button></div>'
        '%s</div>' % groupes)
    # Sur petit écran la colonne se replie ; le même balisage sert aux deux,
    # un <details> ouvert par défaut n'enlève rien au bureau.
    colonne = ('<details class="fac__pli" open><summary>Affiner la recherche</summary>%s</details>'
               % colonne)

    zone = (
        '<div class="fac" data-fac>%s<div>'
        '<p class="fac__cpt" data-fac-cpt aria-live="polite">%d séjours</p>'
        '%s'
        '<p class="fac__rien" data-fac-rien hidden>Aucun séjour ne répond à ces critères. '
        'Retirez un filtre, ou <a href="https://authentiquegypte.com/sur-mesure/">'
        'demandez-nous un sur-mesure</a>.</p>'
        '</div></div>' % (colonne, len(cartes), grille))
    return zone, len(cartes)


def corriger(h):
    d = h.find('<div class="cartes')
    if d < 0:
        return h, []
    f = _fin(h, d, 'div')
    if f < 0:
        return h, []
    neuf, n = refaire_section(h[d:f])
    faits = []
    if neuf != h[d:f]:
        h = h[:d] + neuf + h[f:]
        faits.append('cartes redessinées (%d)' % n
                     + (' + facettes' if 'fac__g' in neuf else ' — sans facettes'))

    ancienne = re.search(r'<style data-facettes="v1">.*?</style>', h, re.S)
    if ancienne and ancienne.group(0) != FEUILLE:
        faits.append('feuille mise à jour')
    if not faits:
        return h, faits
    h = re.sub(r'<style data-facettes="v1">.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<script data-facettes="v1">.*?</script>', '', h, flags=re.S)
    return h + FEUILLE + SCRIPT, faits


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    p.add_argument('--local', nargs='*', help='fichiers à traiter sur place, sans toucher au CMS')
    a = p.parse_args()

    if a.local:
        for f in a.local:
            h = open(f, encoding='utf-8').read()
            neuf, faits = corriger(h)
            cible = f.replace('.html', '-facettes.html')
            open(cible, 'w', encoding='utf-8').write(neuf)
            print('%-52s %s' % (os.path.basename(f)[:52], ' · '.join(faits) or 'rien'))
        return

    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id'])
                  if k['status'] != 'trash' and k['slug'].startswith('refonte-destination-')]

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-38s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:38],
                                     ' · '.join(faits)))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-facettes="v1"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) destination retouchée(s).' % n)


if __name__ == '__main__':
    main()
