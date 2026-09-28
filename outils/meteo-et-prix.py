#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La frise météo qui débordait, et le bloc prix remis à sa place.

    WP_AUTH='compte:mot de passe' ./outils/meteo-et-prix.py [--essai]

LA FRISE (#10757). « Refaire un format pour la météo, ça ne s'affiche
pas bien. » Mesuré avant de toucher à quoi que ce soit : à 1280 px les
douze cellules font 61 px de large, alors que « 15-22 °C » — posé en
white-space:nowrap — en réclame 80. Les douze températures débordent de
leur case, jusqu'à 19 px. Ce n'est pas une affaire de goût, c'est un
texte qui sort de sa boîte.

La cause est la grille figée à douze colonnes sur une seule ligne. On
la laisse respirer : six colonnes au large, quatre en tablette, trois
sur téléphone. Douze mois se divisent par six, quatre et trois — aucune
ligne ne reste orpheline, et chaque case passe de 61 à plus de 110 px.

LE BLOC PRIX (#10758). « Mettre ce que comprend le prix juste après le
prix et pas après la météo. » L'ordre était Tarif → Quand partir → Ce
que le prix comprend ; les deux sections échangent leur place.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

FEUILLE = (
    '<style data-meteo="1">'
    # Six colonnes, puis quatre, puis trois : douze mois se divisent par
    # chacune, donc jamais de dernière ligne à moitié vide.
    + E + '.pg .quand__frise{grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}'
    '@media (max-width:1000px){' + E + '.pg .quand__frise'
    '{grid-template-columns:repeat(4,minmax(0,1fr))}}'
    '@media (max-width:620px){' + E + '.pg .quand__frise'
    '{grid-template-columns:repeat(3,minmax(0,1fr))}}'
    # La case respire, et la température ne force plus sa sortie.
    + E + '.pg .quand__frise li{padding:12px 10px;gap:4px;align-content:center}'
    + E + '.pg .quand__frise .q-t{white-space:normal;font-size:1rem;line-height:1.3}'
    + E + '.pg .quand__frise b{font-size:.92rem;letter-spacing:.01em}'
    # Le trait des mois conseillés passe sur le côté : en bas il se
    # confondait avec la bordure de la case.
    + E + '.pg .quand__frise .q-ok{box-shadow:inset 3px 0 0 var(--teal,#24AEC6)}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def _section_de(h, texte):
    """La section qui contient ce texte, bornes comprises."""
    i = h.find(texte)
    if i < 0:
        return -1, -1
    d = h.rfind('<section', 0, i)
    if d < 0:
        return -1, -1
    f = _fin(h, d, 'section')
    return (d, f) if f > i else (-1, -1)


def prix_avant_meteo(h):
    """« Ce que le prix comprend » remonte devant « Quand partir ». """
    dq, fq = _section_de(h, '<h2 id="t-quand"')
    dp, fp = _section_de(h, '>Ce que le prix comprend<')
    if fq < 0 or fp < 0 or dp < dq:
        return h, False
    bloc = h[dp:fp]
    h = h[:dp] + h[fp:]
    dq, _ = _section_de(h, '<h2 id="t-quand"')
    if dq < 0:
        return h, False
    return h[:dq] + bloc + h[dq:], True


def corriger(h):
    faits = []
    if 'quand__frise' in h:
        faits.append('frise météo desserrée (#10757)')
    h, ok = prix_avant_meteo(h)
    if ok:
        faits.append('« ce que le prix comprend » remonté avant la météo (#10758)')
    if not faits:
        return h, faits
    if 'data-meteo="1"' not in h:
        h += FEUILLE
    elif 'frise météo desserrée (#10757)' in faits and re.search(
            r'<style data-meteo="1">.*?</style>', h, re.S).group(0) != FEUILLE:
        h = re.sub(r'<style data-meteo="1">.*?</style>', '', h, flags=re.S) + FEUILLE
    elif faits == ['frise météo desserrée (#10757)']:
        return h, []
    return h, faits


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
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-32s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:32],
                                     ' · '.join(faits)[:88]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-meteo="1"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
