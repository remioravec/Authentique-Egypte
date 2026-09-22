#!/usr/bin/env python3
"""
Les quatre retouches du gabarit programme demandées de vive voix.

    WP_AUTH='compte:mot de passe' ./outils/gabarit-programme-retouches.py [--essai]

1. LE BANDEAU DE REPÈRES sous le hero disparaît, et ses repères — le prix
   par personne, la durée — montent dans la colonne collante, où ils
   restent sous les yeux pendant toute la lecture. Le bandeau les
   montrait une fois, au passage ; la colonne les montre tout le temps.
   Le fil d'Ariane se retrouve directement sous le hero, à sa place.

2. « QUAND PARTIR » descend. Placée juste après le hero, la météo arrivait
   avant qu'on sache ce qu'on achète. Elle se pose au-dessus de « Ce que
   le prix comprend » : on lit l'itinéraire, puis quand partir, puis ce
   qui est inclus.

3. LA CARTE de l'itinéraire est trop grande. Elle est bornée en largeur et
   centrée — un plan de trajet n'a pas besoin de mille cent pixels.

4. Le prix reste visible : il quitte le bandeau pour la colonne, il ne
   disparaît pas. C'était la demande de Rémi du 17/09, elle tient
   toujours.
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
    '<style data-prog="retouches">'
    # Les repères, en tête de la colonne collante.
    '.pg .pan__cles{display:grid;gap:10px;margin:0 0 16px;padding:0 0 16px;'
    'border-bottom:1px solid var(--ligne,#E4E4EA)}'
    '.pg .pan__cle{display:flex;align-items:baseline;justify-content:space-between;gap:12px}'
    '.pg .pan__cle small{font-family:"Manrope",sans-serif;font-size:.78rem;font-weight:700;'
    'letter-spacing:.06em;text-transform:uppercase;color:var(--teal-txt,#106D7C)}'
    '.pg .pan__cle b{font-family:"Manrope",sans-serif;font-size:1.28rem;font-weight:800;'
    'line-height:1.1;color:var(--nuit-900,#095360);font-variant-numeric:tabular-nums}'
    # La colonne, plus aérée : les repères respirent, le reste se serre.
    '.pg .pan__inclus{display:grid;gap:7px;margin:0;padding:0;list-style:none;'
    'font-size:.92rem;line-height:1.45}'
    '.pg .pan__qui{padding-top:14px}'
    # La carte : bornée, centrée.
    '.pg .carte__svg{max-width:560px;margin-inline:auto}'
    '@media (max-width:900px){.pg .carte__svg{max-width:100%}}'
    '</style>')


def _fin(h, debut, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[debut:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return debut + t.end()
    return -1


def reperes_de(bloc):
    """Les couples (étiquette, valeur) du bandeau, sans ses icônes."""
    out = []
    for li in re.findall(r'<li\b.*?</li>', bloc, re.S):
        s = re.search(r'<small[^>]*>(.*?)</small>', li, re.S)
        b = re.search(r'<b[^>]*>(.*?)</b>', li, re.S)
        if s and b:
            out.append((re.sub(r'<[^>]+>', '', s.group(1)).strip(),
                        re.sub(r'<[^>]+>', '', b.group(1)).strip()))
    return out


def corriger(h):
    faits = []

    # 1. Le bandeau monte dans la colonne collante.
    m = re.search(r'<section class="reperes">', h)
    if m and 'pan__cles' not in h:
        f = _fin(h, m.start(), 'section')
        bloc = h[m.start():f]
        cles = reperes_de(bloc)
        a = re.search(r'<aside class="pan">\s*<div class="pan__carte">', h)
        if cles and a:
            bloc_cles = ('<div class="pan__cles">%s</div>' % ''.join(
                '<div class="pan__cle"><small>%s</small><b>%s</b></div>' % (e, v)
                for e, v in cles))
            h = h[:m.start()] + h[f:]          # le bandeau disparaît
            a = re.search(r'<aside class="pan">\s*<div class="pan__carte">', h)
            h = h[:a.end()] + bloc_cles + h[a.end():]
            faits.append('repères → colonne collante (%d)' % len(cles))

    # 1bis. Le sticky disait deux fois la même chose. « pan__liste » (sept
    #       lignes) et « pan__inclus » (quatre) listent tous deux ce qui
    #       est inclus, et le corps de la page porte déjà « Ce que le prix
    #       comprend » avec ses douze lignes. Trois fois la même
    #       information, dont deux dans une colonne qu'on veut lisible
    #       d'un coup d'œil. On garde la plus courte, dans la colonne ;
    #       la longue vit dans le corps, à sa place.
    m = re.search(r'<ul class="pan__liste">', h)
    if m and '<ul class="pan__inclus">' in h:
        f = _fin(h, m.start(), 'ul')
        if f > 0:
            h = h[:m.start()] + h[f:]
            faits.append('liste d’inclusions en double retirée du sticky')

    # 1ter. Le bloc « L'agence / Qui vous répond » quitte les fiches de
    #       séjour. Mélanie, fil #9570 : « ce n'est pas moi qui gère les
    #       demandes, donc enlever cette partie ». Mettre un visage et un
    #       délai de réponse sur quelqu'un qui ne répond pas est une
    #       promesse qu'on ne tient pas. La colonne collante garde le
    #       contact, qui lui est juste.
    m = re.search(r'<section class="pg-sec equipe"', h)
    if m:
        f = _fin(h, m.start(), 'section')
        if f > 0:
            h = h[:m.start()] + h[f:]
            faits.append('bloc « Qui vous répond » retiré')

    # 2. « Quand partir » descend au-dessus de « Ce que le prix comprend ».
    q = re.search(r'<section class="quand"[^>]*>', h)
    if q:
        fq = _fin(h, q.start(), 'section')
        bloc_q = h[q.start():fq]
        reste = h[:q.start()] + h[fq:]
        # Le titre « Ce que le prix comprend » vit dans une section : on se
        # pose juste AVANT elle.
        cible = None
        for s in re.finditer(r'<section\b[^>]*>', reste):
            fs = _fin(reste, s.start(), 'section')
            if fs > 0 and 'Ce que le prix comprend' in reste[s.start():fs]:
                cible = s.start()
                break
        if cible is not None:
            h = reste[:cible] + bloc_q + reste[cible:]
            faits.append('« Quand partir » descendu')

    if faits and 'data-prog="retouches"' not in h:
        h += FEUILLE
    elif faits:
        h = re.sub(r'<style data-prog="retouches">.*?</style>', '', h, flags=re.S) + FEUILLE
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
        pages += [k for k in dep.appel('GET', Q % d['id'])
                  if k['status'] != 'trash' and k['slug'].startswith('refonte-programme-')]

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, faits = corriger(brut)
        titre = (p_.get('title') or {}).get('raw', '')
        print('   #%-6d %-42s %s' % (k['id'], titre[:42], ' · '.join(faits) or 'rien à faire'))
        if not faits or a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'pan__cles' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON')
    print('\n%d page(s) programme retouchée(s).' % n)


if __name__ == '__main__':
    main()
