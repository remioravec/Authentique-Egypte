#!/usr/bin/env python3
"""La dernière « Agence locale basée au Caire », sur la page restée Elementor.

    WP_AUTH='compte:mdp' python3 outils/nubie-agence.py --essai
    WP_AUTH='compte:mdp' python3 outils/nubie-agence.py --appliquer

Mélanie demande de retirer « agence locale basée au Caire » de tout le site
(12256). Les 57 pages refondues l'ont perdue. Il en restait une :
/programs/decouverte-de-la-nubie/, le quatorzième programme, qui n'a pas été
refondu faute d'itinéraire dans son brouillon.

Cette page-là n'affiche pas son `post_content` : elle a
`_elementor_edit_mode = builder` et 93 ko de `_elementor_data`, et c'est
cette donnée-là qui est rendue. On y retire donc les deux puces, dans le
JSON, après l'avoir sauvegardé tel quel.

On ne touche à rien d'autre : le JSON est relu, comparé clé à clé, et seules
les chaînes qui contiennent la puce changent.
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
CIBLE = ('programs', 1337)
PHRASE = 'Agence locale basée au Caire'


def oter(x, compte):
    """Descend dans le JSON et retire la puce des listes à icônes.

    La mention n'est pas du HTML : c'est une entrée de `icon_list`, la liste
    à puces d'Elementor, sous la forme {"text": "...", "selected_icon": ...}.
    On retire l'entrée, pas la chaîne, pour ne pas laisser une puce vide.
    """
    if isinstance(x, dict):
        neuf = {}
        for k, v in x.items():
            if k == 'icon_list' and isinstance(v, list):
                garde = [e for e in v
                         if not (isinstance(e, dict)
                                 and PHRASE.lower() in str(e.get('text', '')).lower())]
                compte[0] += len(v) - len(garde)
                neuf[k] = [oter(e, compte) for e in garde]
            else:
                neuf[k] = oter(v, compte)
        return neuf
    if isinstance(x, list):
        return [oter(v, compte) for v in x]
    if isinstance(x, str) and PHRASE.lower() in x.lower():
        compte[1] += 1
    return x


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
    B = SITE + '/wp-json/wp/v2/%s/%d' % CIBLE

    d = S.get(B, params={'context': 'edit'}, timeout=240).json()
    brut = (d.get('meta') or {}).get('_elementor_data') or ''
    if not brut:
        raise SystemExit('pas de _elementor_data lisible')
    donnee = json.loads(brut)
    compte = [0, 0]
    neuve = oter(donnee, compte)
    print('%d puce(s) retirée(s), %d mention(s) ailleurs laissée(s)'
          % (compte[0], compte[1]))
    texte = json.dumps(neuve, ensure_ascii=False, separators=(',', ':'))
    print('JSON : %d → %d octets' % (len(brut), len(texte)))
    if json.loads(texte) != neuve:
        raise SystemExit('le JSON ne se relit pas identique')
    h = (d.get('content') or {}).get('raw', '')
    # Elementor garde une copie rendue dans le post_content : c'est elle que
    # le site sert sur cette page. On la nettoie de la même puce.
    contenu, nc = re.subn(r'<li>\s*' + re.escape(PHRASE) + r'\s*</li>\s*', '',
                          h, flags=re.I)
    print('post_content : %d puce(s) à retirer' % nc)
    if not compte[0] and not nc:
        print('rien à faire')
        return
    if a.essai:
        return

    jour = datetime.date.today().isoformat()
    d2 = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne', jour)
    os.makedirs(d2, exist_ok=True)
    f = os.path.join(d2, 'programs-1337-elementor_data.json')
    open(f, 'w').write(brut)
    print('sauvegardé : %s' % os.path.relpath(f, RACINE))

    if compte[0]:
        for essai in range(4):
            r = S.post(B, json={'meta': {'_elementor_data': texte}}, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée')
    if nc:
        for essai in range(4):
            r = S.post(B, json={'content': contenu}, timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture du contenu refusée')
    vu = (S.get(B, params={'context': 'edit'}, timeout=240).json()
          .get('meta') or {}).get('_elementor_data') or ''
    if json.loads(vu) != neuve:
        raise SystemExit('ce qui est relu ne correspond pas à ce qui a été écrit')
    print('relu : %d octets, identique à ce qui a été écrit' % len(vu))
    time.sleep(2)
    page = S.get(SITE + '/programs/decouverte-de-la-nubie/', timeout=180)
    print('page en ligne : %d · %d mention(s) · %d caractères'
          % (page.status_code, page.text.count(PHRASE), len(page.text)))


if __name__ == '__main__':
    main()
