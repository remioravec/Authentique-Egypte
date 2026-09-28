#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La charte graphique de l'agence, appliquée aux 57 pages.

    WD_AUTH= ; WP_AUTH='compte:mot de passe' ./outils/charte.py [--essai]

Sa charte donne trois couleurs et une police : ocre #bc8a2c, or #ecaa24,
bleu clair #bee6f1, Corbel Bold.

CE QUE LA MESURE A CHANGÉ À MA LECTURE

J'avais annoncé à Rémi qu'appliquer sa charte obligerait à repenser tous
les blocs sombres du site, puisqu'elle ne contient aucune couleur foncée.
C'était vrai sur le papier et faux dans les faits : son bleu clair est à
193° de teinte, notre bleu nuit à 189°. Son or est à 40°, le nôtre à 42°.

Les deux palettes sont la même famille. La sienne donne les valeurs
claires d'une identité de marque ; le site avait besoin, en plus, des
valeurs foncées qu'aucune charte de trois couleurs ne fournit — un fond
sur lequel poser du texte blanc. Il n'y a donc rien à repenser : il y a
à aligner.

CE QUE FAIT CET OUTIL

Trois valeurs prennent exactement les siennes : l'or, le bleu clair, et
l'ocre qui entre comme couleur neuve pour les bordures et les survols.
Les six autres — les bleus foncés, les ors dérivés — sont tournées à SA
teinte : 193° pour les bleus, 40° pour les ors. Après quoi chaque bleu
du site est littéralement une nuance du sien.

CE QU'IL NE FAIT PAS

Le blanc sur son or donne 2,03 de contraste : illisible. Aucun bouton du
site n'était dans ce cas — ils portent tous du texte foncé — et cet outil
n'en crée pas.

La police attendra : Corbel est une police système Microsoft, ni
diffusable sur le web ni présente sur Google Fonts. Il faut soit acheter
la licence web, soit choisir un équivalent libre, et cela se décide sur
un rendu, pas sur un nom.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# avant → après. Les trois premières sont ses valeurs exactes ; les autres
# sont les nôtres tournées à sa teinte, luminosité et saturation gardées.
PALETTE = [
    ('#FBB50E', '#ECAA24'),   # --or        : son or
    ('#EAF6F9', '#BEE6F1'),   # --teal-fond : son bleu clair
    ('#FFD958', '#FFC758'),   # --or-clair
    ('#FEEDDC', '#FEF3DC'),   # --or-fond
    ('#095360', '#094D60'),   # --nuit-900
    ('#148194', '#147894'),   # --nuit
    ('#1995AA', '#198BAA'),   # --nuit-700
    ('#24AEC6', '#24A3C6'),   # --teal
    ('#106D7C', '#10657C'),   # --teal-txt
    ('#F0FCFD', '#F0FAFD'),   # --fond-2
]

# Les ombres écrivent le bleu nuit en décimal, pas en hexadécimal : sans
# cette ligne, tout le site prendrait la nouvelle teinte sauf ses ombres.
RGBA = [('9,83,96', '9,77,96')]

# Son ocre entre comme variable neuve. Personne ne s'en sert encore : on
# la déclare pour qu'elle existe, et on l'emploie là où une bordure d'or
# était devinée au jugé plutôt que tirée de la charte.
OCRE = '#BC8A2C'
BORDURES = [('#F3D9A8', OCRE + '55'), ('#F5D9B0', OCRE + '55')]

# Le guillemet des cartes d'avis était posé en or : 2,03 de contraste sur
# blanc, soit un ornement à peine visible. Son ocre monte à 3,08 et reste
# dans sa charte — c'est le premier emploi réel de sa troisième couleur.
GUILLEMET = [('.mur__q{color:var(--or,#ECAA24)',
              '.mur__q{color:var(--ocre,%s)' % OCRE)]


def corriger(h):
    faits = []
    n = 0
    for av, ap in PALETTE:
        for forme in (av, av.lower()):
            if forme in h:
                n += h.count(forme)
                h = h.replace(forme, ap)
    if n:
        faits.append('%d valeurs alignées sur la charte' % n)

    m = 0
    for av, ap in RGBA:
        if av in h:
            m += h.count(av)
            h = h.replace(av, ap)
    if m:
        faits.append('%d ombres retournées' % m)

    b = 0
    for av, ap in BORDURES:
        if av in h:
            b += h.count(av)
            h = h.replace(av, ap)
    if b:
        faits.append('%d bordures passées à son ocre' % b)

    q = 0
    for av, ap in GUILLEMET:
        if av in h:
            q += h.count(av)
            h = h.replace(av, ap)
    if q:
        faits.append('guillemet des avis passé à son ocre')

    # La variable, déclarée une fois, pour la suite.
    if '--ocre:' not in h and '--or:' in h:
        h = h.replace('--or:', '--ocre:%s; --or:' % OCRE, 1)
        faits.append('--ocre déclaré')

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
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:74]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                   relu['content']['raw']))[1] == []:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
