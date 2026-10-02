#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trois finitions mécaniques, mesurées avant d'être faites.

    WP_AUTH='compte:mot de passe' ./outils/finitions.py [--essai]

1. Quinze pages ne referment jamais leur <main> : les neuf destinations,
   les quatre profils, le blog et l'agence. Le navigateur le referme
   tout seul à </body>, ce qui met le pied de page à l'intérieur du
   contenu principal et brise le repère ARIA contentinfo. On pose le
   </main> là où il manque, juste avant le pied.

2. « Egypte » sans accent, 177 fois. Mais il y a trois endroits où il ne
   faut surtout pas y toucher :

     – les soixante-quatorze occurrences dans les avis Google. Ce sont
       les mots des voyageurs, on ne corrige pas l'orthographe de
       quelqu'un qu'on cite ;
     – les cinquante-neuf dans des src, des srcset et des href : ce sont
       des noms de fichiers réels, les accentuer casserait les images ;
     – rien d'autre.

   Restent soixante-dix-neuf occurrences dans le texte visible et
   soixante-cinq dans des attributs que lit un lecteur d'écran — alt,
   data-alt, aria-label, title. Ce sont celles-là qu'on accentue.

3. Dix-huit phrases collées à la suivante, sur neuf pages : « fait
   rêver.Les pyramides », « pour la soirée.Mars à mai ». La passe du
   29/09 avait rendu 209 espaces avalées après une balise ; celles-ci
   sont dans du texte nu, elle ne pouvait pas les voir.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

EGYPTE = re.compile(r'\bEgypt(e|iens?|iennes?)\b')
# Les attributs qu'un humain lit. Les autres portent des chemins.
LISIBLES = ('alt', 'data-alt', 'aria-label', 'title')
PHRASE = re.compile(r'([a-zàâçéèêëîïôûùü]{3}[.!?])([A-ZÀÂÇÉÈÊËÎÏÔÛÙÜ][a-zàâçéèêëîïôûùü]{2})')


def _zones_citees(h):
    """Les avis sont verbatim : on relève leurs bornes pour les épargner."""
    out = []
    i = 0
    while True:
        i = h.find('<blockquote', i)
        if i < 0:
            return out
        j = h.find('</blockquote>', i)
        if j < 0:
            return out
        out.append((i, j + 13))
        i = j + 13


def _dedans(zones, i):
    return any(a <= i < b for a, b in zones)


def _attribut(h, i):
    """Dans quel attribut tombe la position i ? None si c'est du texte."""
    d = h.rfind('<', 0, i)
    g = h.rfind('>', 0, i)
    if g > d:
        return None
    m = re.findall(r'(\w[\w-]*)="[^"]*$', h[d:i])
    return m[-1].lower() if m else '?'


def accents(h):
    cites = _zones_citees(h)
    bouts, dern, n = [], 0, 0
    for m in EGYPTE.finditer(h):
        if _dedans(cites, m.start()):
            continue
        a = _attribut(h, m.start())
        if a is not None and a not in LISIBLES:
            continue
        bouts.append(h[dern:m.start()])
        bouts.append('Égypt' + m.group(1))
        dern = m.end()
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def phrases(h):
    cites = _zones_citees(h)
    bouts, dern, n = [], 0, 0
    for m in PHRASE.finditer(h):
        if _dedans(cites, m.start()) or _attribut(h, m.start()) is not None:
            continue
        bouts.append(h[dern:m.end(1)])
        bouts.append(' ')
        dern = m.end(1)
        n += 1
    if not n:
        return h, 0
    bouts.append(h[dern:])
    return ''.join(bouts), n


def main_referme(h):
    if len(re.findall(r'<main[\s>]', h)) <= h.count('</main>'):
        return h, False
    i = h.rfind('<footer')
    if i < 0:
        return h, False
    return h[:i] + '</main>' + h[i:], True


def corriger(h):
    faits = []
    h, ok = main_referme(h)
    if ok:
        faits.append('</main> rendu')
    h, n = accents(h)
    if n:
        faits.append('%d accent(s) à Égypte' % n)
    h, n = phrases(h)
    if n:
        faits.append('%d espace(s) entre phrases' % n)
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
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:30], ' · '.join(faits)[:72]))
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
    print('\n%d page(s) %s.' % (n, 'à finir' if a.essai else 'finie(s)'))


if __name__ == '__main__':
    main()
