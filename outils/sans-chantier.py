#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ce qui restait du chantier dans les pages, et qui ne doit pas partir.

    WP_AUTH='compte:mot de passe' ./outils/sans-chantier.py [--essai]

Cinq traces, relevées sur les 58 pages.

Une se lit à l'écran. Vingt-deux guides ouvrent leur article par un
paragraphe sur fond crème : « Contenu repris de <lien>, sans réécriture :
seule la mise en page change. » C'était une note pour Mélanie pendant la
relecture, pas une phrase pour un voyageur.

Quatre se lisent dans le code source. Le calque d'annotation du maillage
— 84 attributs data-mm sur les 58 pages, 26 légendes de travail dans le
DOM de 24 pages, et les règles qui les dessinent — servait à montrer les
liens internes pendant une présentation. Les légendes portent des phrases
comme « le guide renvoie d'abord vers l'offre, ensuite seulement vers
d'autres lectures » : du raisonnement interne, masqué à l'affichage,
lisible par qui ouvre le code.

Et le commentaire de tête des 58 pages, « Maquette de refonte servie en
brouillon… Ne pas modifier ici », qui n'aura plus de sens une fois la
page en ligne.

La cinquième est une erreur. Le préfixeur a travaillé à l'intérieur
d'une valeur d'attribut entre guillemets :

    [data-mm="Navigation · poids 0, .elementor-template-canvas 25"]

Il a vu la virgule de « poids 0,25 » comme une virgule de sélecteur. La
règle ne correspond à rien depuis le début. Elle part avec le reste.

Aucune regex gourmande ici : certaines pages font 3,7 Mo et un motif qui
revient sur ses pas n'en sort pas. On borne à la main.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

# (nom, ouverture, fermeture) — la tranche entière s'en va.
BLOCS = [('note de reprise', '<p class="src">', '</p>'),
         ('légende de maillage', '<div class="mm-legende"', '</div>'),
         ('légende de maillage', '<div class="rp-mm-legende"', '</div>'),
         ('bouton de maillage', '<button class="mm-btn"', '</button>')]


def _tranches(h, debut, fin):
    out, i = [], 0
    while True:
        i = h.find(debut, i)
        if i < 0:
            return out
        j = h.find(fin, i)
        if j < 0:
            return out
        out.append((i, j + len(fin)))
        i = j + len(fin)


def _oter(h, tranches):
    if not tranches:
        return h
    bouts, dern = [], 0
    for a, b in sorted(tranches):
        if a < dern:          # chevauchement : on garde la première
            continue
        bouts.append(h[dern:a])
        dern = b
    bouts.append(h[dern:])
    return ''.join(bouts)


def _regles_mm(h):
    """Les règles CSS du calque d'annotation, bornées à la main."""
    out, i = [], 0
    while True:
        i = h.find('body.elementor-template-canvas.mm', i)
        if i < 0:
            return out
        # début : après le } ou le > qui précède, pour ne pas manger la règle d'avant
        d = max(h.rfind('}', 0, i), h.rfind('>', 0, i), h.rfind(';', 0, i))
        j = h.find('}', i)
        if j < 0:
            return out
        out.append((d + 1, j + 1))
        i = j + 1


def _commentaires(h):
    out = []
    for a, b in _tranches(h, '<!--', '-->'):
        s = h[a:b]
        if 'Maquette de refonte' in s or 'Ne pas modifier ici' in s:
            out.append((a, b))
    return out


DATA_MM = re.compile(r' data-mm="[^"]*"')

# Les règles qui dessinaient le calque : leurs éléments sont partis, elles
# restent. Du CSS mort sur cinquante-huit pages.
MORTES = ('.mm-legende', '.mm-btn', '.rp-mm-legende')

# « L'agence » datait son pied de page du jour où la charte a été relevée.
# C'est la seule des cinquante-huit, et c'est le seul de ces restes que le
# visiteur aurait lu.
PIED = ('<span>© 2026 Authentique Égypte — Maquette de refonte, '
        'charte relevée le 21/08/2026</span>')
PIED_PROPRE = '<span>© 2026 Authentique Égypte</span>'


def _regles_mortes(h):
    out = []
    for cl in MORTES:
        i = 0
        while True:
            i = h.find(cl, i)
            if i < 0:
                break
            j = h.find('}', i)
            # dans une feuille, pas dans un attribut de classe
            k = h.rfind('<', 0, i)
            if j < 0 or (k >= 0 and h.rfind('>', 0, i) < k):
                i += len(cl)
                continue
            d = max(h.rfind('}', 0, i), h.rfind('>', 0, i), h.rfind(';', 0, i))
            out.append((d + 1, j + 1))
            i = j + 1
    return out


def corriger(h):
    faits = {}
    for nom, a, b in BLOCS:
        t = _tranches(h, a, b)
        if t:
            faits[nom] = faits.get(nom, 0) + len(t)
            h = _oter(h, t)
    t = _regles_mm(h)
    if t:
        faits['règles du calque'] = len(t)
        h = _oter(h, t)
    t = _commentaires(h)
    if t:
        faits['commentaire de maquette'] = len(t)
        h = _oter(h, t)
    h, n = DATA_MM.subn('', h)
    if n:
        faits['attribut data-mm'] = n
    t = _regles_mortes(h)
    if t:
        faits['règles sans élément'] = len(t)
        h = _oter(h, t)
    if PIED in h:
        faits['pied daté'] = h.count(PIED)
        h = h.replace(PIED, PIED_PROPRE)
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
        n += 1
        print('   #%-6d %-30s %s'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:30],
                 ' · '.join('%s ×%d' % (x, y) for x, y in faits.items())[:86]))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if not corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                       relu['content']['raw']))[1]:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) %s.' % (n, 'à nettoyer' if a.essai else 'nettoyée(s)'))


if __name__ == '__main__':
    main()
