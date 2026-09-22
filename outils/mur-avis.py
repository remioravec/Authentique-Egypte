#!/usr/bin/env python3
"""
Le mur d'avis cesse de défiler : les commentaires deviennent lisibles.

    WP_AUTH='compte:mot de passe' ./outils/mur-avis.py [--essai]

Sept fils de la relecture disent la même chose, sur sept pages
différentes : « le texte n'est pas statique, difficile de lire »,
« les commentaires bougent, pas le format que je souhaite », « à refaire,
le format ne convient pas », « le format et les couleurs ne conviennent
pas ». C'est le même objet à chaque fois.

Le mur était un défilement infini : deux colonnes, chacune une fenêtre de
664 px où une piste glissait de -50 % en 75 à 90 secondes, en sens
inverse d'une colonne à l'autre. Pour que la boucle soit sans couture, les
onze avis étaient écrits DEUX fois — d'où les vingt-deux articles. Un
texte qui bouge ne se lit pas : on ne peut ni le parcourir des yeux, ni le
relire, ni le pointer du doigt.

Il devient une grille d'avis, tous visibles, rien ne bouge. Les copies de
bouclage disparaissent, la case à cocher qui mettait le défilement en
pause aussi — il n'y a plus rien à arrêter.

Aucun avis n'est réécrit : ce sont des témoignages publiés sur Google, on
les déplace, on ne les touche pas.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

FEUILLE = (
    '<style data-avis="statique">'
    # La grille remplace les deux colonnes défilantes. Même règle que les
    # autres grilles du site : auto-fit, pour qu'aucune carte ne reste
    # seule sur sa ligne.
    '.pg .mur{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));'
    'gap:18px;align-items:start}'
    '.pg .mur__a{background:#fff;border:1px solid var(--ligne-pg,#E4E4EA);'
    'border-radius:var(--r-l,20px);padding:22px;margin:0}'
    '.pg .mur__a blockquote{margin:0 0 16px;font-size:1rem;line-height:1.7;color:var(--texte)}'
    '.pg .mur__q{display:block;font-size:2.2rem;line-height:.6;color:var(--or);margin:0 0 6px}'
    '.pg .mur__a footer{display:flex;align-items:center;gap:12px;'
    'font-family:"Manrope",sans-serif;font-size:.88rem;color:var(--gris-lis,#5B6870)}'
    # Ce qui ne servait qu'au défilement n'a plus lieu d'être affiché.
    '.pg .mur__f,.pg .mur__d,.pg .mur__c{display:contents}'
    '.pg .mur__stop,.pg .mur__btn{display:none}'
    '</style>')


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def avis_de(bloc):
    """Les avis distincts, dans l'ordre où ils apparaissent.

    Le doublon est cherché sur le TEXTE de l'avis, pas sur le balisage :
    la copie de bouclage porte les mêmes mots mais pas forcément les mêmes
    attributs.
    """
    vus, out = set(), []
    i = 0
    while True:
        d = bloc.find('<article class="mur__a"', i)
        if d < 0:
            break
        f = _fin(bloc, d, 'article')
        if f < 0:
            break
        art = bloc[d:f]
        q = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', art, re.S)
        cle = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', q.group(1))).strip() if q else art
        if cle and cle not in vus:
            vus.add(cle)
            out.append(art)
        i = f
    return out


def corriger(h):
    """Rend (page, nombre d'avis gardés, nombre de copies retirées)."""
    d = h.find('<div class="mur"')
    if d < 0:
        return h, 0, 0
    f = _fin(h, d, 'div')
    if f < 0:
        return h, 0, 0
    bloc = h[d:f]
    avis = avis_de(bloc)
    if not avis:
        return h, 0, 0
    total = len(re.findall(r'<article class="mur__a"', bloc))
    neuf = '<div class="mur">%s</div>' % ''.join(avis)
    h = h[:d] + neuf + h[f:]
    # La case à cocher et son bouton ne commandaient que le défilement.
    h = re.sub(r'<input[^>]*class="[^"]*mur__stop[^"]*"[^>]*>', '', h)
    h = re.sub(r'<label[^>]*class="[^"]*mur__btn[^"]*".*?</label>', '', h, flags=re.S)
    if 'data-avis="statique"' not in h:
        h = h + FEUILLE          # en dernier : c'est lui qui doit l'emporter
    return h, len(avis), total - len(avis)


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
        neuf, gardes, copies = corriger(brut)
        if not gardes:
            continue
        n += 1
        print('   #%-6d %-44s %2d avis, %2d copie(s) retirée(s)'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:44], gardes, copies))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if relu['content']['raw'].count('data-avis="statique"') == 1:
                    break
                print('      reprise %d/3' % (essai + 1))
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON, la page reste telle quelle')
    print('\n%d page(s) touchée(s).' % n)


if __name__ == '__main__':
    main()
