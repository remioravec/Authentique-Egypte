#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le balisage structuré ne garde que ce qu'il peut prouver.

    WP_AUTH='compte:mot de passe' ./outils/jsonld-vrai.py [--essai]

Le JSON-LD a été recopié de gabarit en gabarit sans jamais être
régénéré. Trois paquets de pages portent un bloc identique octet pour
octet : vingt-deux guides décrivent tous « Quand partir en Égypte »,
neuf destinations décrivent toutes « Le Caire », quatre profils
décrivent tous des itinéraires du désert.

Le plus grave est le FAQPage. Vingt-quatre pages annoncent à Google des
questions dont pas une ne figure sur la page. Onze autres en annoncent
une partie. Ce n'est pas une imprécision de balisage : c'est le motif
d'une action manuelle.

Rémi a tranché : on retire. Pas de régénération, pas de reformulation —
on ne garde que ce qui est vérifiable, et on laisse Yoast fournir le
reste. Il émet déjà, sur les trois types de contenu, un WebPage, un
Article et un BreadcrumbList construits depuis la page elle-même.

La règle, nœud par nœud :

  – un FAQPage perd les questions absentes de la page ; s'il n'en reste
    aucune, il part en entier ;
  – un BreadcrumbList dont le dernier maillon désigne une autre page
    part — celui de Yoast prend le relais, en deux niveaux au lieu de
    quatre, ce qui est moins riche mais vrai ;
  – tout autre nœud qui ne porte ni le titre de la page ni son URL part ;
  – ce qui se vérifie reste : les quatorze TouristTrip, les cinq
    CollectionPage, l'Article et l'agence qui sont bien à leur page.

Ce qui est retiré n'est pas remplacé. Une page sans balisage propre
garde celui de Yoast, qui est juste.
"""

import argparse
import html as H
import json
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
CARTE = os.path.join(RACINE, 'docs', 'carte-mise-en-ligne.json')

# Des nœuds de service : ils décrivent une image, une adresse, un prix.
# Ils n'ont pas à porter le titre de la page, on ne les juge pas.
SERVICE = {'ImageObject', 'PostalAddress', 'GeoCoordinates', 'ListItem', 'Offer',
           'ContactPoint', 'Place', 'Question', 'Answer', 'Organization', 'Person',
           'WebSite', 'AggregateRating', 'Review', 'Rating'}


def _txt(x):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', x or ''))).strip().lower()


def _type(n):
    t = n.get('@type')
    return t[0] if isinstance(t, list) else t


def _url(n):
    u = n.get('url') or n.get('@id') or ''
    return u if isinstance(u, str) else ''


def juger(n, h1, url, questions):
    """Garde, allège ou retire. Rend (nœud ou None, motif)."""
    t = _type(n)
    if t in SERVICE:
        return n, None
    if t == 'FAQPage':
        qs = [q for q in (n.get('mainEntity') or []) if isinstance(q, dict)]
        gardees = [q for q in qs if _txt(q.get('name'))[:26] in questions]
        if not gardees:
            return None, 'FAQPage sans question sur la page'
        if len(gardees) < len(qs):
            n = dict(n, mainEntity=gardees)
            return n, 'FAQPage allégé de %d question(s)' % (len(qs) - len(gardees))
        return n, None
    if t == 'BreadcrumbList':
        el = n.get('itemListElement') or []
        it = (el[-1] if el else {}).get('item')
        it = it.get('@id') if isinstance(it, dict) else it
        if (it or '').rstrip('/') != url.rstrip('/'):
            return None, 'fil d’Ariane qui désigne une autre page'
        return n, None
    nom = _txt(n.get('name') or n.get('headline'))
    if (nom and nom == h1) or (_url(n).rstrip('/') == url.rstrip('/') and url):
        return n, None
    return None, '%s qui ne porte ni le titre ni l’URL de la page' % (t or 'nœud')


def _aplatir(d):
    if isinstance(d, list):
        out = []
        for x in d:
            out += _aplatir(x)
        return out
    if not isinstance(d, dict):
        return []
    g = d.get('@graph')
    if isinstance(g, list):
        out = []
        for x in g:
            out += _aplatir(x)
        return out
    return [d]


def corriger(h, url):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    h1 = _txt(m.group(1)) if m else ''
    questions = _txt(' '.join(re.findall(r'<summary[^>]*>(.*?)</summary>', h, re.S)))
    questions = questions  # le texte visible des questions dépliables

    def present(q):
        return q in questions

    bouts, dern, motifs = [], 0, []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        noeuds = _aplatir(d)
        gardes = []
        for n in noeuds:
            g, motif = juger(n, h1, url, questions)
            if motif:
                motifs.append(motif)
            if g is not None:
                gardes.append(g)
        if len(gardes) == len(noeuds) and not motifs:
            continue
        bouts.append(h[dern:m.start()])
        if gardes:
            ctx = d.get('@context') if isinstance(d, dict) else 'https://schema.org'
            corps = ({'@context': ctx or 'https://schema.org', '@graph': gardes}
                     if len(gardes) > 1 else dict(gardes[0], **{'@context': ctx or 'https://schema.org'}))
            bouts.append('<script type="application/ld+json">'
                         + json.dumps(corps, ensure_ascii=False, separators=(',', ':'))
                         + '</script>')
        dern = m.end()
    if not motifs:
        return h, []
    bouts.append(h[dern:])
    return ''.join(bouts), motifs


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--essai', action='store_true')
    a = p.parse_args()
    dep = SourceFileLoader('dep', os.path.join(RACINE, 'outils', 'deployer.py')).load_module()
    carte = {c['refonte']: c for c in json.load(open(CARTE))}

    pages = []
    for d in dep.appel('GET', Q % MERE):
        if d['status'] == 'trash':
            continue
        pages += [k for k in dep.appel('GET', Q % d['id']) if k['status'] != 'trash']

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        url = (carte.get(k['id']) or {}).get('cible_url') or ''
        neuf, motifs = corriger(brut, url)
        if not motifs:
            continue
        n += 1
        compte = {}
        for x in motifs:
            compte[x] = compte.get(x, 0) + 1
        print('   #%-6d %-28s %s'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:28],
                 ' · '.join('%s ×%d' % (x[:44], y) for x, y in compte.items())[:92]))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if not corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                       relu['content']['raw']), url)[1]:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) %s.' % (n, 'à alléger' if a.essai else 'allégée(s)'))


if __name__ == '__main__':
    main()
