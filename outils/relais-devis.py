#!/usr/bin/env python3
"""Faire que le relais vers /sur-mesure/ transmette ce que le visiteur a saisi.

    python3 outils/relais-devis.py --essai
    WP_AUTH='compte:mdp' python3 outils/relais-devis.py --appliquer

Les 14 pages de séjour portent un petit formulaire « Recevoir mon devis »
qui part en GET vers /sur-mesure/. Ses trois contrôles — période, nombre de
voyageurs, envies — n'ont pas d'attribut `name`, et aucun script ne lit ses
`data-sejour` / `data-prix` : la requête part donc vide. Le visiteur
choisit son mois, dit combien ils sont, écrit deux lignes, clique, et
retrouve un formulaire vierge. Tout est perdu.

On répare des deux côtés :

  — sur les 14 pages, les trois contrôles reçoivent un `name`, et le nom du
    séjour et son prix, déjà présents en attributs de données, partent en
    champs cachés ;
  — sur /sur-mesure/, un script lit la requête et pose ce qui vient d'être
    saisi dans le formulaire WPForms : le séjour dans le champ 3, le reste
    dans le champ 15 « Décrivez votre séjour ».

Le script ne touche jamais un champ déjà rempli, et ne pose que des mots
venant du visiteur ou du catalogue — rien n'est écrit à sa place.
"""

import argparse
import base64
import html
import json
import os
import re
import sys
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
SUR_MESURE = 786
FORM = 7445
MARQUE = 'relais-devis'

SCRIPT = ('<script id="' + MARQUE + '">/* Reprend ce que le visiteur a saisi sur la '
          'page du séjour. Ne remplit que les champs vides. */\n'
          '(function(){var p=new URLSearchParams(location.search);'
          'if(!p.get("sejour")&&!p.get("periode")&&!p.get("voyageurs")&&!p.get("envies"))return;'
          'function c(i){return document.getElementById("wpforms-%d-field_"+i)}'
          'function pose(){var s=c(3);'
          'if(s&&!s.value&&p.get("sejour"))s.value=p.get("sejour");'
          'var t=c(15);if(t&&!t.value){var l=[];'
          'if(p.get("sejour"))l.push("Séjour repéré sur le site : "+p.get("sejour")'
          '+(p.get("prix")?" ("+p.get("prix")+")":""));'
          'if(p.get("periode"))l.push("Période souhaitée : "+p.get("periode"));'
          'if(p.get("voyageurs"))l.push("Voyageurs : "+p.get("voyageurs"));'
          'if(p.get("envies"))l.push(p.get("envies"));'
          't.value=l.join("\\n");}}'
          'if(document.readyState!=="loading")pose();'
          'else document.addEventListener("DOMContentLoaded",pose);})();</script>' % FORM)


def nommer(s):
    """Donne un nom aux trois contrôles du relais et ajoute les champs cachés."""
    n = {'periode': 0, 'voyageurs': 0, 'envies': 0, 'caches': 0}
    i = 0
    while True:
        i = s.find('<form class="pan__form"', i)
        if i < 0:
            break
        j = s.find('</form>', i)
        f = s[i:j]
        if 'name="sejour"' in f:          # déjà fait
            i = j
            continue
        sejour = (re.search(r'data-sejour="([^"]*)"', f) or [None, ''])[1]
        prix = (re.search(r'data-prix="([^"]*)"', f) or [None, ''])[1]
        g = f
        g, k = re.subn(r'<select aria-label="Période souhaitée">',
                       '<select name="periode" aria-label="Période souhaitée">', g)
        n['periode'] += k
        g, k = re.subn(r'(<input type="number"[^>]*placeholder="Voyageurs")',
                       r'\1 name="voyageurs"', g)
        n['voyageurs'] += k
        g, k = re.subn(r'(<input class="pan__l2" type="text")',
                       r'\1 name="envies"', g)
        n['envies'] += k
        caches = ''
        if sejour:
            caches += '<input type="hidden" name="sejour" value="%s">' % sejour
        if prix:
            caches += '<input type="hidden" name="prix" value="%s">' % prix
        if caches:
            g = g.replace('>', '>' + caches, 1)   # juste après <form ...>
            n['caches'] += 1
        s = s[:i] + g + s[j:]
        i = j
    return s, n


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

    jours = sorted(j for j in os.listdir(SAUVE) if len(j) == 10 and j[4] == '-')
    man = json.load(open(os.path.join(SAUVE, jours[-1], 'MANIFESTE.json')))
    D = os.path.join(SAUVE, jours[-1], 'brouillons')

    # les pages qui portent un relais, brouillon et cible appariés
    couples = []
    for c in man['couples']:
        b = json.load(open(os.path.join(D, '%d.json' % c['brouillon'])))
        if '<form class="pan__form"' in b['contenu']:
            couples.append((c, b))
    print('%d page(s) portent le relais' % len(couples))

    total = {'periode': 0, 'voyageurs': 0, 'envies': 0, 'caches': 0}
    for c, b in couples:
        _, n = nommer(b['contenu'])
        for k in total:
            total[k] += n[k]
    print('   à nommer : %s' % total)

    if a.essai:
        # un exemple, pour voir ce que ça donne
        _, _ = nommer(couples[0][1]['contenu'])
        s, _ = nommer(couples[0][1]['contenu'])
        i = s.find('<form class="pan__form"')
        print('\nexemple :\n   %s' % re.sub(r'\s+', ' ', s[i:i + 420]))
        print('\nscript posé sur /sur-mesure/ : %d octets' % len(SCRIPT))
        return

    fait = 0
    for c, b in couples:
        for base, pid, source in (('pages', c['brouillon'], b['contenu']),
                                  (c['type'], c['cible'], None)):
            if source is None:
                r = S.get(B + '%s/%d' % (base, pid), params={'context': 'edit'}, timeout=120)
                source = (r.json().get('content') or {}).get('raw', '')
            neuf, n = nommer(source)
            if neuf == source:
                print('   %-9s #%-6d déjà fait' % (base, pid))
                continue
            charge = {'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'}
            for essai in range(4):
                r = S.post(B + '%s/%d' % (base, pid), json=charge, timeout=300)
                if r.status_code < 300:
                    break
                time.sleep(2 ** essai)
            else:
                sys.exit('écriture refusée sur %s #%d' % (base, pid))
            fait += 1
            print('   %-9s #%-6d %s' % (base, pid, n))
    print('%d contenu(s) écrits.' % fait)

    # et la page d'arrivée
    for pid in (SUR_MESURE,):
        r = S.get(B + 'pages/%d' % pid, params={'context': 'edit'}, timeout=120)
        s = (r.json().get('content') or {}).get('raw', '')
        if 'id="%s"' % MARQUE in s:
            print('   /sur-mesure/ : script déjà posé')
            continue
        charge = {'content': '<!-- wp:html -->\n' + s + SCRIPT + '\n<!-- /wp:html -->'}
        S.post(B + 'pages/%d' % pid, json=charge, timeout=300).raise_for_status()
        print('   /sur-mesure/ : script posé')


if __name__ == '__main__':
    main()
