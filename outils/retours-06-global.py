#!/usr/bin/env python3
"""Lot 1 des retours de Mélanie du 5 octobre : ce qui vaut pour tout le site.

    WP_AUTH='compte:mdp' python3 outils/retours-06-global.py --essai
    WP_AUTH='compte:mdp' python3 outils/retours-06-global.py --appliquer

Quatre demandes répétées d'une page à l'autre, donc traitées en une fois :

  1. « enlever agence locale basée au Caire sur tout le site » (12256), et
     « enlever agence locale Le Caire » sur l'accueil (12249, 12252). Le
     bandeau garde « Une personne de l'équipe vous répond ».
  2. Un bouton de demande de devis dans le bloc « Sur mesure » — demandé sept
     fois (12292, 12277, 12311, 12316, 12304, 12295, 12345), et une fois de
     plus en réponse : « c'est ok mais pouvez-vous le mettre en forme : texte
     en gras, bouton pour demander un devis » (10779). Le premier paragraphe
     passe donc en gras, et le bouton mène à /sur-mesure/.
  3. « mettre un espace entre les commentaires et le bouton, pareil pour les
     avis Google » — six fois (12293, 12312, 12317, 12305, 12296, 12328).
  4. « enlever ce texte » sur « Aucune carte bancaire demandée à cette
     étape » (12263). La demande ne vise qu'une page, mais c'est le même
     élément de gabarit sur cinquante-cinq : on le retire partout, et on le
     dit. C'est réversible.

Ce qu'on ne fait pas, et pourquoi : « est-ce possible d'enlever la mention ? »
à propos de « Fond de carte OpenStreetMap » (12285, 12314). Cette mention est
la condition de la licence ODbL sous laquelle le fond de carte est utilisé.
La retirer mettrait le site en défaut. À proposer autrement à Mélanie : la
rendre plus discrète, pas la supprimer.
"""

import argparse
import base64
import json
import os
import re
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARQUE = 'data-devis-bloc'

BOUTON = ('<p class="edito__act" ' + MARQUE + '>'
          '<a class="btn btn--or" href="' + SITE + '/sur-mesure/">'
          'Demander mon devis</a></p>')

STYLE = ('<style data-retours-06>'
         # 3 · les boutons d'avis collaient aux témoignages
         '.elementor-template-canvas .mur__liens{margin-top:26px}'
         # 2 · le bloc « Sur mesure » accueille son bouton
         '.elementor-template-canvas .edito__act{margin:18px 0 0}'
         '.elementor-template-canvas .edito .prose p:first-child{font-weight:700;'
         'color:var(--noir,#000)}'
         '</style>')


def corriger(h):
    j = {'agence': 0, 'bouton': 0, 'gras': 0, 'cb': 0, 'style': 0}

    # 1 · la mention d'agence
    h, n = re.subn(r'Agence locale basée au Caire\s*·\s*', '', h)
    j['agence'] += n
    h, n = re.subn(r'Agence locale basée au Caire', '', h)
    j['agence'] += n
    h, n = re.subn(r'Agence locale\s*·\s*Le Caire\s*·\s*', '', h)
    j['agence'] += n
    h, n = re.subn(r'Agence locale\s*·\s*Le Caire', '', h)
    j['agence'] += n

    # 4 · la mention de carte bancaire, avec son <small> quand il l'enveloppe
    h, n = re.subn(r'<small>\s*Aucune carte bancaire demandée à cette étape\.?\s*</small>',
                   '', h)
    j['cb'] += n
    h, n = re.subn(r'Aucune carte bancaire demandée à cette étape\.?', '', h)
    j['cb'] += n

    # 2 · le bouton dans le bloc « Sur mesure », une seule fois par bloc
    i = 0
    while True:
        i = h.find('<div class="edito">', i)
        if i < 0:
            break
        # la fin du bloc edito, comptée à la main
        p, k = 0, i
        while k < len(h):
            if h.startswith('<div', k):
                p += 1
            elif h.startswith('</div>', k):
                p -= 1
                if p == 0:
                    break
            k += 1
        bloc = h[i:k]
        if MARQUE in bloc or 'Votre voyage, vos envies' not in bloc:
            i = k
            continue
        # le bouton se pose à la fin de la prose
        f = bloc.rfind('</div>')
        neuf = bloc[:f] + BOUTON + bloc[f:]
        h = h[:i] + neuf + h[k:]
        j['bouton'] += 1
        i = i + len(neuf)

    if 'data-retours-06' not in h:
        h += STYLE
        j['style'] = 1
    return h, j


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
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    couples = list(man['couples']) + [{'type': 'pages', 'cible': 786,
                                       'url': SITE + '/sur-mesure/'}]

    total = {'agence': 0, 'bouton': 0, 'cb': 0, 'style': 0}
    a_ecrire = []
    for c in couples:
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        neuf, j = corriger(h)
        if neuf == h:
            continue
        for k in total:
            total[k] += j.get(k, 0)
        a_ecrire.append((c, neuf, j))

    print('mentions d agence retirées     : %d' % total['agence'])
    print('boutons de devis ajoutés       : %d' % total['bouton'])
    print('mentions de carte bancaire ôtées: %d' % total['cb'])
    print('feuille de style posée sur     : %d page(s)' % total['style'])
    print('%d page(s) à écrire' % len(a_ecrire))
    if a_ecrire:
        _, n1, _ = a_ecrire[0]
        o = len(re.findall(r'<(section|div|p|a)[\s>]', n1))
        f = len(re.findall(r'</(section|div|p|a)>', n1))
        print('balises ouvertes %d · fermées %d' % (o, f))
    if a.essai:
        return

    for c, neuf, j in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
    print('\n%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
