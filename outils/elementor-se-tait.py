#!/usr/bin/env python3
"""Faire taire Elementor sur les cibles qu'il rend à la place du contenu.

    WP_AUTH='compte:mot de passe' python3 outils/elementor-se-tait.py --essai
    WP_AUTH='compte:mot de passe' python3 outils/elementor-se-tait.py --appliquer

Le problème, constaté en ligne le 2 octobre après la bascule des 55 : sur
39 cibles, la page publique affichait encore l'ANCIEN Elementor. La cause
est sans ambiguïté, la corrélation est parfaite sur les 55 :

  * 39 cibles ont `_elementor_edit_mode = builder` ET des `_elementor_data`
    non vides. Elementor rend alors SES données et ignore `post_content` :
    la refonte était bien écrite en base, et jamais affichée.
  * les 16 autres n'ont pas de données Elementor. Elles rendent
    `post_content`, et ce sont exactement les 16 qui marchaient.

Comme le gabarit était déjà passé en elementor_canvas, ces 39 pages étaient
en ligne avec l'ancien contenu ET sans menu ni pied : Canvas avait retiré
celui du thème, et l'ancien Elementor n'en portait pas.

Le remède : vider `_elementor_edit_mode`. WordPress rend alors
`post_content`, donc la refonte, qui embarque son en-tête et son pied.
Même mega menu et même pied partout, comme demandé.

On ne touche pas aux `_elementor_data` : elles restent en base, intactes.
C'est le filet — remettre `builder` suffit à retrouver l'ancienne page.

Une écriture qui rend 200 ne prouve rien sur ce site : les méta Yoast
rendent 200 et ne gardent rien. On relit donc chaque cible après coup, et
c'est la relecture qui compte.
"""

import argparse
import base64
import json
import os
import sys
import time

import requests

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
CLE = '_elementor_edit_mode'


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    g.add_argument('--revenir', action='store_true',
                   help='remet builder : Elementor reprend la main')
    a = p.parse_args()

    S = requests.Session()
    S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'

    jours = sorted(j for j in os.listdir(SAUVE)
                   if len(j) == 10 and j[4] == '-')
    man = json.load(open(os.path.join(SAUVE, jours[-1], 'MANIFESTE.json')))

    def lire(typ, pid):
        r = S.get(B + '%s/%d' % (typ, pid),
                  params={'context': 'edit'}, timeout=90)
        if r.status_code != 200:
            return {'erreur': r.status_code}
        d = r.json()
        mt = d.get('meta') or {}
        dat = mt.get(('_elementor_data'))
        return {'edit_mode': mt.get(CLE),
                'data': len(dat) if isinstance(dat, str) else 0,
                'contenu': len((d.get('content') or {}).get('raw', '')),
                'modele': d.get('template') or '(défaut)'}

    print("J'examine les %d cibles du manifeste du %s." % (len(man['couples']), jours[-1]))
    etat = {}
    for c in man['couples']:
        etat[(c['type'], c['cible'])] = (lire(c['type'], c['cible']), c)

    muettes = [(k, v) for k, v in etat.items()
               if not v[0].get('erreur') and v[0]['edit_mode'] == 'builder'
               and v[0]['data'] > 50]
    deja = [(k, v) for k, v in etat.items()
            if not v[0].get('erreur') and not (v[0]['edit_mode'] == 'builder'
                                               and v[0]['data'] > 50)]
    fautes = [(k, v) for k, v in etat.items() if v[0].get('erreur')]
    print('   %d cible(s) où Elementor rend ses données à la place du contenu'
          % len(muettes))
    print('   %d cible(s) qui rendent déjà post_content' % len(deja))
    if fautes:
        print('   %d cible(s) illisibles : %s' % (len(fautes), [k for k, _ in fautes]))

    if a.essai:
        for (typ, pid), (e, c) in sorted(muettes, key=lambda x: x[1][1]['url']):
            print('   %-9s #%-6d %-46s data %6d · contenu %6d'
                  % (typ, pid, (c['url'] or '').replace(SITE, '')[:46],
                     e['data'], e['contenu']))
        return

    cible_val = 'builder' if a.revenir else ''
    aretenir = deja if a.revenir else muettes
    if a.revenir:
        aretenir = [(k, v) for k, v in etat.items()
                    if not v[0].get('erreur') and v[0]['edit_mode'] != 'builder'
                    and v[0]['data'] > 50]
        print("   %d cible(s) à rendre à Elementor" % len(aretenir))

    n = 0
    for (typ, pid), (e, c) in aretenir:
        for essai in range(4):
            try:
                r = S.post(B + '%s/%d' % (typ, pid),
                           json={'meta': {CLE: cible_val}}, timeout=120)
                if r.status_code >= 300:
                    raise RuntimeError('HTTP %d' % r.status_code)
                # la relecture tranche, pas le code de retour
                ap = lire(typ, pid)
                if ap.get('edit_mode') != cible_val:
                    raise RuntimeError('non gardé : %r' % ap.get('edit_mode'))
                if ap.get('data', 0) < 50:
                    raise RuntimeError('les données Elementor ont disparu')
                n += 1
                print('   %-9s #%-6d %s' % (typ, pid,
                      (c['url'] or '').replace(SITE, '')))
                break
            except Exception as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif)[:70]))
                time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON %s #%d' % (typ, pid))

    print('\n%d / %d cible(s) passées à %s.'
          % (n, len(aretenir), repr(cible_val)))


if __name__ == '__main__':
    main()
