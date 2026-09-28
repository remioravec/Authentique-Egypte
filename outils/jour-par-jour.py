#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le sommaire des étapes, et le lien vers la carte.

    WP_AUTH='compte:mot de passe' ./outils/jour-par-jour.py [--essai]

#10761 demande quatre choses au jour par jour. Voici les deux que je
peux faire sans rien inventer.

LE SOMMAIRE. « Une sorte de sommaire avec les différentes étapes pour
chaque programme. » Il se construit à partir des titres de journée, qui
existent déjà : chaque entrée renvoie à sa journée, et le lecteur voit
d'un coup la forme du séjour avant d'entrer dans le détail.

LE LIEN VERS LA CARTE. « Un lien qui renvoie vers la carte. » La carte
d'itinéraire est juste au-dessus depuis la semaine dernière ; le
sommaire y renvoie.

CE QUE JE NE FAIS PAS, ET POURQUOI

« Différencier par des petites icônes les hébergements et les repas
inclus ou pas inclus selon la journée, car parfois c'est marqué parfois
non. » Elle a raison, et le trou est plus large qu'elle ne le pense :
sur soixante-cinq journées, treize portent une mention d'hébergement et
AUCUNE ne porte de mention de repas. Les mettre en icônes ne réglerait
rien — il manque la donnée elle-même sur cinquante-deux journées, et je
ne vais pas la déduire du texte courant : « dîner sur le Nil » dans le
déroulé ne dit pas si le dîner est compris dans le prix.

Les photos par journée, de même, il me les faut.
"""

import argparse
import html as H
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '

FEUILLE = (
    '<style data-jpj="1">'
    + E + '.pg .jpjs{margin:0 0 26px;padding:18px 20px;border-radius:var(--r-l,20px);'
    'background:var(--fond,#F9F9FB);border:1px solid var(--ligne-pg,#E4E4EA)}'
    + E + '.pg .jpjs__t{display:flex;align-items:baseline;justify-content:space-between;'
    'gap:16px;flex-wrap:wrap;margin:0 0 12px}'
    + E + '.pg .jpjs__t p{margin:0;font-family:"Manrope",sans-serif;font-weight:700;'
    'font-size:.82rem;letter-spacing:.06em;text-transform:uppercase;'
    'color:var(--teal-txt,#106D7C)}'
    + E + '.pg .jpjs__t a{font-family:"Manrope",sans-serif;font-weight:600;'
    'font-size:.88rem;color:var(--teal-txt,#106D7C)}'
    + E + '.pg .jpjs__l{list-style:none;margin:0;padding:0;display:grid;gap:6px}'
    '@media (min-width:760px){' + E + '.pg .jpjs__l{grid-template-columns:repeat(2,1fr);'
    'column-gap:26px}}'
    + E + '.pg .jpjs__l li{display:flex;gap:10px;align-items:baseline;'
    'font-size:.96rem;line-height:1.45}'
    + E + '.pg .jpjs__l a{color:var(--texte,#5D5D5D);text-decoration:none}'
    + E + '.pg .jpjs__l a:hover{color:var(--nuit-900,#095360);'
    'text-decoration:underline;text-underline-offset:2px}'
    + E + '.pg .jpjs__n{flex:0 0 auto;min-width:26px;padding:1px 7px;border-radius:999px;'
    'background:var(--or-fond,#FEEDDC);color:var(--nuit-900,#095360);'
    'font-family:"Manrope",sans-serif;font-weight:700;font-size:.76rem;text-align:center}'
    '</style>')

LIEN_CARTE = ('<a href="#t-carte">Voir la carte de l’itinéraire</a>')


def _fin(h, d, nom):
    p = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % nom, h[d:]):
        p += 1 if not t.group(1) else -1
        if p == 0:
            return d + t.end()
    return -1


def etapes(h):
    """Les journées : leur numéro, leur titre, et l'ancre qui y mène."""
    out = []
    for m in re.finditer(r'<div class="jour__tete">(.*?)</div>', h, re.S):
        titre = re.search(r'<h3[^>]*>(.*?)</h3>', m.group(1), re.S)
        no = re.search(r'<span class="jour__no">(.*?)</span>', m.group(1), re.S)
        if not titre:
            continue
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', titre.group(1))).strip()
        n = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', no.group(1))).strip() if no else ''
        # Le titre répète parfois le nom du séjour avant un tiret :
        # « Désert et oasis en Egypte - Arrivée à Aswan ». Le sommaire
        # n'a besoin que de ce qui distingue la journée.
        court = re.sub(r'^.{6,60}?\s[–-]\s', '', t).strip() or t
        out.append((n, court))
    return out


def ancrer_jours(h):
    """Chaque journée reçoit un identifiant, pour que le sommaire y mène."""
    n = [0]

    def pose(m):
        n[0] += 1
        if 'id=' in m.group(0):
            return m.group(0)
        return '<div class="jour" id="jour-%d">' % n[0]

    return re.sub(r'<div class="jour"(?: id="jour-\d+")?>', pose, h), n[0]


def sommaire(h):
    d = h.find('<h2 id="t-jpj"')
    if d < 0 or 'jpjs__l' in h:
        return h, False
    liste = etapes(h)
    if len(liste) < 3:
        # Un séjour d'une ou deux journées n'a pas besoin d'un sommaire :
        # il tient déjà sous les yeux.
        return h, False
    h, combien = ancrer_jours(h)
    if combien != len(liste):
        return h, False

    items = ''.join(
        '<li><span class="jpjs__n">%s</span>'
        '<a href="#jour-%d">%s</a></li>'
        % (H.escape(n.replace('Jour ', 'J') or str(i + 1)), i + 1, H.escape(t))
        for i, (n, t) in enumerate(liste))

    # Le lien ne s'affiche que si l'ancre a bien été posée.
    carte = LIEN_CARTE if 'id="t-carte"' in h else ''
    bloc = ('<nav class="jpjs" aria-label="Les étapes du séjour">'
            '<div class="jpjs__t"><p>Les étapes</p>%s</div>'
            '<ol class="jpjs__l">%s</ol></nav>' % (carte, items))

    # Après le titre de section, avant la première journée.
    f = h.find('</h2>', d) + len('</h2>')
    return h[:f] + bloc + h[f:], True


def ancre_carte(h):
    """L'ancre vers laquelle le sommaire pointe.

    Deux cartes coexistent sur le site. Celle posée la semaine dernière
    a un titre — « L'itinéraire de votre séjour » — sur lequel l'ancre
    se pose naturellement. L'autre, issue de la conversion du dessin
    d'origine, n'a qu'une <figure> sans titre : l'ancre va sur la
    figure. Sans ce second cas, six programmes recevaient un lien « voir
    la carte » qui ne menait nulle part.
    """
    if 'id="t-carte"' in h:
        return h, False
    m = re.search(r'<h2>(L’itinéraire de votre séjour)</h2>', h)
    if m:
        return h[:m.start()] + '<h2 id="t-carte">%s</h2>' % m.group(1) + h[m.end():], True
    m = re.search(r'<figure class="carte">', h)
    if m and 'carte__map' in h:
        return h[:m.start()] + '<figure class="carte" id="t-carte">' + h[m.end():], True
    return h, False


def corriger(h):
    faits = []
    h, ok = ancre_carte(h)
    if ok:
        faits.append('ancre posée sur la carte')
    h, ok = sommaire(h)
    if ok:
        faits.append('sommaire des étapes (#10761)')
    if not faits:
        return h, faits
    if 'data-jpj="1"' not in h:
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
        neuf, faits = corriger(brut)
        if not faits:
            continue
        print('   #%-6d %-34s %s' % (k['id'], (p_.get('title') or {}).get('raw', '')[:34],
                                     ' · '.join(faits)[:80]))
        if a.essai:
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if 'data-jpj="1"' in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) corrigée(s).' % n)


if __name__ == '__main__':
    main()
