#!/usr/bin/env python3
"""Alexandrie et le Désert noir passent enfin au nouveau gabarit.

    WP_AUTH='compte:mdp' python3 outils/deux-destinations.py --essai
    WP_AUTH='compte:mdp' python3 outils/deux-destinations.py --appliquer

Le 2 octobre, trois pages avaient été écartées de la bascule : « Découverte
de la Nubie », « Désert noir » et « Alexandrie ». Le motif pour les deux
destinations : leur brouillon n'expose aucun séjour. C'est exact — aucun de
nos quatorze programmes ne passe par Alexandrie ni par le Désert noir — mais
leurs pages en ligne n'en exposent pas davantage : elles affichent un carrousel
de séjours qui n'ont rien à voir avec le lieu, de « Sainte-Catherine » à
« l'Oasis de Siwa ».

Entre-temps elles sont restées en ligne dans l'ancienne maquette, avec
l'ancien menu — « Oasis de Dakhla », « Sinai – Moise et Saint Catherine » —
que le reste du site ne connaît plus. Un visiteur qui arrive sur Alexandrie
change de site. Et Mélanie, qui écrit « je vais en ajouter » (12298) et
demande un texte de ville pour Alexandrie (12321), regarde justement cette
page-là.

Avant de basculer, on a vérifié que rien ne se perd : les neuf questions de
la page Alexandrie et les dix-huit du Désert noir se retrouvent une à une
dans le brouillon, qui en ajoute d'autres.

Ce que fait la bascule, exactement comme les 55 du 2 octobre :
  1. sauvegarde l'état actuel (contenu, gabarit, titre, slug) ;
  2. remplace le contenu par celui du brouillon ;
  3. passe le gabarit à elementor_canvas, sans quoi Astra ajouterait son
     en-tête et son pied à ceux que la page embarque ;
  4. vide `_elementor_edit_mode`, sans quoi Elementor rend ses propres
     données et ignore le contenu — c'est ce qui avait cassé 39 pages ;
  5. réécrit les liens ?page_id= vers les URL définitives.

Les `_elementor_data` ne sont pas touchées : c'est le filet qui permet de
revenir en arrière.
"""

import argparse
import base64
import datetime
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
CANVAS = 'elementor_canvas'
CLE = '_elementor_edit_mode'

COUPLES = [
    {'brouillon': 8921, 'type': 'pages', 'cible': 5219,
     'url': SITE + '/voyage-a-alexandrie/'},
    {'brouillon': 8918, 'type': 'pages', 'cible': 5541,
     'url': SITE + '/desert-noir/'},
]

# Les épingles de l'extension de relecture n'ont rien à faire en ligne.
RELECTURE = [re.compile(r'<div[^>]*\bclass="[^"]*\baec[-_][^"]*"[^>]*>.*?</div>',
                        re.S),
             re.compile(r'<script[^>]*\baec[-_][^>]*>.*?</script>', re.S)]


def nu(h):
    return re.sub(r'<!-- /?wp:html -->\n?', '', h or '')


def nettoyer(h):
    for r in RELECTURE:
        h = r.sub('', h)
    return h


def liens(h, vers):
    """?page_id=8660 devient l'URL définitive. On dit ceux qui manquent."""
    manquants = set()

    def _un(m):
        u = vers.get(int(m.group(1)))
        if not u:
            manquants.add(int(m.group(1)))
            return m.group(0)
        return u

    h = re.sub(r'https://authentiquegypte\.com/\?page_id=(\d+)/?', _un, h)
    h = re.sub(r'\?page_id=(\d+)', _un, h)
    return h, manquants


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    def lire(chemin, **kw):
        for essai in range(5):
            r = S.get(B + chemin, params=kw, timeout=240)
            if r.status_code < 300:
                return r.json()
            time.sleep(2 ** essai)
        raise SystemExit('lecture refusée sur %s : %d' % (chemin, r.status_code))

    man = json.load(open(os.path.join(SAUVE, '2026-10-02', 'MANIFESTE.json')))
    vers = {c['brouillon']: c['url'] for c in man['couples']}
    for c in COUPLES:
        vers[c['brouillon']] = c['url']

    prepare = []
    for c in COUPLES:
        b = lire('pages/%d' % c['brouillon'], context='edit')
        v = lire('%s/%d' % (c['type'], c['cible']), context='edit')
        neuf, manquants = liens(nettoyer(nu(b['content']['raw'])), vers)
        prepare.append({
            'c': c, 'neuf': neuf, 'manquants': sorted(manquants),
            'avant': {'contenu': v['content']['raw'],
                      'modele': v.get('template') or '',
                      'titre': v['title']['raw'], 'slug': v['slug']},
        })
        print('%-26s %7d → %7d car. · gabarit %-18s · liens à réécrire %s'
              % (c['url'].replace(SITE, ''), len(v['content']['raw']),
                 len(neuf), (v.get('template') or '(défaut)'),
                 sorted(manquants) or 'aucun'))
        for marque, n in (('<main', 1), ('<header class="entete"', 1),
                          ('<footer class="pied"', 1), ('<h1', 1)):
            vu = neuf.count(marque)
            if vu != n:
                raise SystemExit('%s : %d × %s, attendu %d'
                                 % (c['url'], vu, marque, n))

    if a.essai:
        return

    jour = datetime.date.today().isoformat()
    d = os.path.join(SAUVE, jour)
    os.makedirs(d, exist_ok=True)
    for x in prepare:
        f = os.path.join(d, '%s-%d.json' % (x['c']['type'], x['c']['cible']))
        json.dump(x['avant'], open(f, 'w'), ensure_ascii=False, indent=1)
        print('sauvegardé : %s' % os.path.relpath(f, RACINE))

    for x in prepare:
        c = x['c']
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']),
                       json={'content': '<!-- wp:html -->\n' + x['neuf']
                             + '\n<!-- /wp:html -->', 'template': CANVAS},
                       timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        # Elementor doit se taire, sinon il rend ses propres données
        S.post(B + '%s/%d' % (c['type'], c['cible']),
               json={'meta': {CLE: ''}}, timeout=180)
        d2 = lire('%s/%d' % (c['type'], c['cible']), context='edit')
        mt = (d2.get('meta') or {})
        print('%-26s écrite · gabarit %s · %s=%r · _elementor_data %s'
              % (c['url'].replace(SITE, ''), d2.get('template'), CLE,
                 mt.get(CLE), 'intactes' if mt.get('_elementor_data') else
                 '(non visibles par l API)'))

    time.sleep(3)
    for x in prepare:
        r = S.get(x['c']['url'], timeout=180)
        h = r.text
        print('%-26s %d · %d en-tête · %d pied · %d h1 · %d main'
              % (x['c']['url'].replace(SITE, ''), r.status_code,
                 h.count('<header class="entete"'), h.count('<footer class="pied"'),
                 len(re.findall(r'<h1[\s>]', h)), h.count('<main class="pg"')))


if __name__ == '__main__':
    main()
