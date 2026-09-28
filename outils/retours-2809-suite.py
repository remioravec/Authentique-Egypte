#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quatre retours de plus, trouvés en relisant ce qui restait muet.

    WP_AUTH='compte:mot de passe' ./outils/retours-2809-suite.py [--essai]

Trente fils n'avaient encore aucune réponse. Vingt-trois attendent une
photo qu'elle seule peut fournir, mais quatre étaient actionnables et
je les avais rangés trop vite avec les autres :

#10856 « supprimer photo de tom ». Ce n'est pas une photo : c'est un
crédit, « Photo de Tom », resté en légende sous un titre du guide des
expériences. Un seul sur tout le site.

#10783 « enlève ce programme », sur la page Louxor, visant la croisière
du lac Nasser. Son déroulé passe bien par Louxor, donc la liste n'a pas
tort — mais c'est elle qui vend, et une croisière sur le lac Nasser n'est
pas ce qu'on propose à quelqu'un qui cherche Louxor.

#10793 « enlever cette partie », visant le bloc « Pourquoi nous » de la
page couple. Elle l'a demandé ailleurs aussi (#10748), sur la page
croisières, mais là elle veut un remplacement qui demande son contenu :
ici c'est un simple retrait.

#10847 « mettre aussi des articles de blog spécial famille ou guides
pratiques ». Trois guides famille existent déjà sur le site ; on les
lie.
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

GUIDES_FAMILLE = [
    ('Que faire en Égypte avec des enfants',
     'https://authentiquegypte.com/egypte-enfants-activites/'),
    ('Peut-on voyager en Égypte en famille ?',
     'https://authentiquegypte.com/voyager-en-egypte-en-famille/'),
    ('Sécurité en Égypte pour un voyage en famille',
     'https://authentiquegypte.com/securite-en-egypte-pour-un-voyage-en-famille/'),
]

BLOC_GUIDES = (
    '<section class="pg-sec pg-sec--fond guif"><div class="wrap">'
    '<p class="eyebrow">À lire avant de partir</p>'
    '<h2>Nos guides pour voyager en famille</h2>'
    '<ul class="guif__l">%s</ul></div></section>'
    % ''.join('<li><a href="%s">%s</a></li>' % (u, n) for n, u in GUIDES_FAMILLE))

FEUILLE = (
    '<style data-retours="28-09b">'
    + E + '.pg .guif__l{display:grid;gap:10px;margin:18px 0 0;padding:0;list-style:none}'
    + E + '.pg .guif__l a{display:block;background:#fff;'
    'border:1px solid var(--ligne-pg,#E4E4EA);border-radius:14px;padding:15px 20px;'
    'font-family:"Manrope",sans-serif;font-weight:600;font-size:.98rem;'
    'color:var(--nuit-900,#095360);text-decoration:none}'
    + E + '.pg .guif__l a:hover{border-color:var(--or,#FBB50E)}'
    '@media (min-width:820px){' + E + '.pg .guif__l{grid-template-columns:repeat(3,1fr)}}'
    '</style>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def credit_photo(h):
    """« Photo de Tom » : un crédit de banque d'images, pas une légende."""
    neuf = re.sub(r'<p class="note">\s*Photo de [^<]{0,40}</p>', '', h)
    return neuf, neuf != h


def carte_hors_sujet(h, pid):
    """La croisière du lac Nasser quitte la page Louxor (#10783)."""
    if pid != 8924:
        return h, False
    i = h.find('Croisière sur le lac Nasser')
    if i < 0:
        return h, False
    d = h.rfind('<article class="carte', 0, i)
    if d < 0:
        return h, False
    f = _fin(h, d, 'article')
    if f < 0 or 'Croisière sur le lac Nasser' not in h[d:f]:
        return h, False
    return h[:d] + h[f:], True


def bloc_pourquoi(h, pid):
    """« Enlever cette partie » : le bloc « Pourquoi nous » (#10793)."""
    if pid != 8926:
        return h, False
    i = h.find('>Pourquoi nous<')
    if i < 0:
        return h, False
    d = h.rfind('<section', 0, i)
    f = _fin(h, d, 'section')
    if d < 0 or f < 0 or 'Pourquoi nous' not in h[d:f]:
        return h, False
    return h[:d] + h[f:], True


def guides_famille(h, pid):
    """Les guides famille, liés depuis la page famille (#10847)."""
    if pid != 8927 or 'guif__l' in h:
        return h, False
    # Après « Les autres façons de partir », que sa remarque visait.
    i = h.find('Les autres façons de partir')
    d = h.rfind('<section', 0, i) if i > 0 else -1
    f = _fin(h, d, 'section') if d >= 0 else -1
    if f < 0:
        return h, False
    return h[:f] + BLOC_GUIDES + h[f:], True


def corriger(h, pid):
    faits = []
    for etape, nom in ((credit_photo, 'crédit « Photo de Tom » retiré (#10856)'),):
        h, ok = etape(h)
        if ok:
            faits.append(nom)
    for etape, nom in ((carte_hors_sujet, 'croisière lac Nasser retirée de Louxor (#10783)'),
                       (bloc_pourquoi, '« Pourquoi nous » retiré (#10793)'),
                       (guides_famille, 'guides famille liés (#10847)')):
        h, ok = etape(h, pid)
        if ok:
            faits.append(nom)
    if not faits:
        return h, faits
    if 'data-retours="28-09b"' not in h:
        h += FEUILLE
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
        neuf, faits = corriger(brut, k['id'])
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:90]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                   relu['content']['raw']), k['id'])[1] == []:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
