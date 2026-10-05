#!/usr/bin/env python3
"""Réécrire les && des scripts : WordPress les encode et casse le code.

    WP_AUTH='compte:mdp' python3 outils/sans-esperluette.py --essai
    WP_AUTH='compte:mdp' python3 outils/sans-esperluette.py --appliquer

Le contrôle qualité a trouvé neuf pages dont un script lève « Invalid or
unexpected token ». La cause : dans le HTML servi, les `&&` du JavaScript
sortent en `&#038;&#038;`. Le contenu stocké est propre — c'est au rendu
que l'esperluette est encodée. Conséquence réelle : sur les pages de
destination, le filtre à facettes ne filtre rien, et sur /sur-mesure/ le
préremplissage du formulaire ne s'exécute pas.

On ne peut pas empêcher l'encodage depuis le contenu. On écrit donc le
même code sans esperluette, en `if` imbriqués ou en ternaires. Dix motifs,
traités un par un : une substitution automatique de `A && B` demanderait
de connaître les bornes des opérandes, et se tromperait.

Un cas mérite attention : `if(A && B) X; else Y;` ne peut pas devenir
`if(A) if(B) X; else Y;` — le `else` se rattacherait au second `if`, et
Y ne s'exécuterait plus quand A est faux. Celui-là passe en ternaire.

Chaque script modifié est revalidé par Node avant écriture.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

E = r'\s*'          # espaces tolérés

REGLES = [
    # 1 · les polices chargées
    (r'if\(document\.fonts&&document\.fonts\.ready\)',
     'if(document.fonts)if(document.fonts.ready)'),
    # 2 · la mesure du relais de devis
    (r"if\(f&&f\.classList&&f\.classList\.contains\('pan__form'\)\)",
     "if(f)if(f.classList)if(f.classList.contains('pan__form'))"),
    # 3 · le lien cliqué
    (r"var a=e\.target&&e\.target\.closest\?e\.target\.closest\('a'\):null;",
     "var a=e.target?(e.target.closest?e.target.closest('a'):null):null;"),
    # 4 · l'observateur de confirmation
    (r'if\(!guetter\(\)&&window\.MutationObserver\)',
     'if(!guetter())if(window.MutationObserver)'),
    # 5 · la touche Échap ferme le menu
    (r'if\(e\.key==="Escape"&&n\.classList\.contains\("nav--ouverte"\)\)',
     'if(e.key==="Escape")if(n.classList.contains("nav--ouverte"))'),
    # 6 · le compteur de la valise
    (r'if\(valise&&etat\)', 'if(valise)if(etat)'),
    # 7 · la carte et ses étapes
    (r"if\(pts\.length&&etapes\.length&&'IntersectionObserver' in window\)",
     "if(pts.length)if(etapes.length)if('IntersectionObserver' in window)"),
    # 8 · la visionneuse
    (r"img=lb&&lb\.querySelector\('img'\);",
     "img=lb?lb.querySelector('img'):null;"),
    # 9 · le sommaire qui suit la lecture
    (r"if\('IntersectionObserver' in window&&liens\.length\)",
     "if('IntersectionObserver' in window)if(liens.length)"),
    # 10 · la première étape qui correspond au lieu
    (r"if\(!cible&&a\.getAttribute\('data-lieu'\)",
     "if(!cible)if(a.getAttribute('data-lieu')"),
    # 11 · le compte d'une facette — ternaire obligatoire, un else suit
    (r'if\(n' + E + r'===' + E + r'0' + E + r'&&' + E + r'!c\.checked\)',
     'if(n === 0 ? !c.checked : false)'),
    # 12 · facette, valeurs multiples
    (r"indexOf\(c\.value\)" + E + r">=" + E + r"0" + E + r"&&" + E
     + r"garde\(k," + E + r"g," + E + r"c\.dataset\.g\);",
     "indexOf(c.value) >= 0 ? garde(k, g, c.dataset.g) : false;"),
    # 13 · facette, valeur simple
    (r"===" + E + r"c\.value" + E + r"&&" + E + r"garde\(k," + E + r"g,"
     + E + r"c\.dataset\.g\);",
     "=== c.value ? garde(k, g, c.dataset.g) : false;"),
    # 14 · le préremplissage depuis une page de séjour
    (r'if\(!p\.get\("sejour"\)&&!p\.get\("periode"\)&&!p\.get\("voyageurs"\)'
     r'&&!p\.get\("envies"\)\)return;',
     'if(!p.get("sejour"))if(!p.get("periode"))if(!p.get("voyageurs"))'
     'if(!p.get("envies"))return;'),
    # 15 · le champ séjour, rempli seulement s'il est vide
    (r'if\(s&&!s\.value&&p\.get\("sejour"\)\)s\.value=p\.get\("sejour"\);',
     'if(s)if(!s.value)if(p.get("sejour"))s.value=p.get("sejour");'),
    # 16 · les trois facettes de l'accueil
    (r"correspond\(c,'qui'\)&&correspond\(c,'envie'\)&&correspond\(c,'duree'\)",
     "correspond(c,'qui')?(correspond(c,'envie')?correspond(c,'duree'):false):false"),
]


def corriger(h):
    n = 0
    for motif, neuf in REGLES:
        h, k = re.subn(motif, neuf.replace('\\', '\\\\'), h)
        n += k
    return h, n


def scripts(h):
    """Les scripts qui sont du JavaScript, et eux seuls.

    Un bloc `application/ld+json` est une donnée, pas du code : le passer
    à un parseur JavaScript le fait échouer sur le premier deux-points, et
    ferait croire à une page cassée.
    """
    out = []
    for m in re.finditer(r'<script([^>]*)>(.*?)</script>', h, re.S):
        attrs = m.group(1) or ''
        if re.search(r'\bsrc=', attrs):
            continue
        t = re.search(r'type=["\']([^"\']+)["\']', attrs)
        if t and not re.search(r'javascript|module', t.group(1)):
            continue
        out.append(m.group(2))
    return out


def valide(codes):
    """Node tranche : un script qui ne se parse pas ne part pas en ligne."""
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write('const c=%s;let k=0;for(const s of c){try{new Function(s)}'
                'catch(e){console.log("INVALIDE "+k+" "+e.message)};k++}'
                % json.dumps(codes))
        chemin = f.name
    env = dict(os.environ)
    r = subprocess.run(['node', chemin], capture_output=True, text=True, env=env)
    os.unlink(chemin)
    return r.stdout.strip()


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

    total, touchees, restants, mauvais = 0, [], 0, []
    for c in couples:
        d = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120).json()
        h = (d.get('content') or {}).get('raw', '')
        neuf, n = corriger(h)
        if not n:
            reste = sum(s.count('&&') for s in scripts(h))
            restants += reste
            continue
        total += n
        ko = valide(scripts(neuf))
        if ko:
            mauvais.append((c['url'], ko[:120]))
            continue
        restants += sum(s.count('&&') for s in scripts(neuf))
        touchees.append((c, neuf, n))

    print('%d remplacement(s) sur %d page(s)' % (total, len(touchees)))
    print('%d && restant(s) dans les scripts après correction' % restants)
    if mauvais:
        print('✗ %d page(s) écartées, script invalide après correction :' % len(mauvais))
        for u2, k in mauvais:
            print('   %s — %s' % (u2.replace(SITE, ''), k))
    if a.essai:
        return
    if mauvais:
        raise SystemExit('je n écris rien tant qu une page ne se valide pas')

    for c, neuf, n in touchees:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']),
                       json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                       timeout=300)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        print('   %-9s #%-6d %-46s %d' % (c['type'], c['cible'],
                                          c['url'].replace(SITE, '')[:46], n))
    print('\n%d page(s) écrites.' % len(touchees))


if __name__ == '__main__':
    main()
