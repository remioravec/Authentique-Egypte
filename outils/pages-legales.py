#!/usr/bin/env python3
"""Les mentions légales et la newsletter passent au gabarit du site.

    WP_AUTH='compte:mdp' python3 outils/pages-legales.py --essai
    WP_AUTH='compte:mdp' python3 outils/pages-legales.py --appliquer

Quatre pages servaient encore l'ancien menu — celui qui propose « Oasis de
Dakhla » et « Sinai – Moise et Saint Catherine », que le reste du site ne
connaît plus. Deux d'entre elles sont à un clic de n'importe quelle page :
« L'agence », dans le méga-menu, et les mentions légales, dans le pied.

Celles-ci sont les plus simples : du texte. On les repose sur le gabarit des
guides — même en-tête, même pied, même typographie — sans toucher à un mot du
texte juridique, qui est recopié tel quel. Seuls partent les attributs
`data-start` et `data-end` laissés par l'éditeur, et le `<h1>` du corps, que
le gabarit porte déjà en chapeau.

La newsletter, elle, ne contient qu'un code court. Elle garde son formulaire,
dans une page qui ressemble enfin au site.
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
GABARIT = ('posts', 5746)             # /vaccins-egypte/
CANVAS = 'elementor_canvas'

CIBLES = {
    3785: {
        'url': SITE + '/mentions-legales-agence-voyage-egypte/',
        'fil': 'Mentions légales',
        'h1': 'Mentions légales et protection des données',
        'sous': ('Qui édite ce site, ce que nous collectons, ce que nous en '
                 'faisons, et comment nous demander de le corriger ou de '
                 'l’effacer.'),
        'corps': None,                # repris de la page
    },
    3784: {
        'url': SITE + '/newsletter/',
        'fil': 'Newsletter',
        'h1': 'Notre lettre d’information',
        'sous': ('Quelques fois par an, ce que nous apprenons sur le terrain : '
                 'les périodes à viser, les sites qui rouvrent, les itinéraires '
                 'qui marchent.'),
        'corps': ('<p>Laissez votre adresse, et rien d’autre. Vous pouvez vous '
                  'désinscrire en un clic, depuis n’importe lequel de nos '
                  'envois.</p>[newsletter]'),
    },
}


def nettoyer(h):
    """Le texte tel quel, sans les traces de l'éditeur."""
    h = re.sub(r'<!-- /?wp:html -->\n?', '', h)
    h = re.sub(r'\s*data-(?:start|end)="\d+"', '', h)
    h = re.sub(r'<h1[^>]*>.*?</h1>\s*', '', h, count=1, flags=re.S)
    # une liste dont chaque élément enveloppe un <p> : on aplatit
    h = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', h, flags=re.S)
    h = re.sub(r'<hr\s*/?>', '', h)
    return re.sub(r'\n{2,}', '\n', h).strip()


def page(gabarit, c):
    """Le gabarit des guides, avec le fil, le titre et le corps demandés."""
    a = gabarit.find('<main')
    b = gabarit.find('</main>', a) + len('</main>')
    tete, pied = gabarit[:a], gabarit[b:]
    corps = (
        '<main class="pg"><section class="chapeau"><div class="wrap">'
        '<nav class="ariane" aria-label="Fil d\'Ariane"><ol>'
        '<li><a href="%s/">Accueil</a></li>'
        '<li><span aria-current="page">%s</span></li></ol></nav>'
        '<h1>%s</h1><p class="sous">%s</p></div></section>'
        '<div class="wrap"><article class="corps mef">%s</article></div>'
        '</main>' % (SITE, c['fil'], c['h1'], c['sous'], c['corps']))
    return tete + corps + pied


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

    def lire(t, i):
        for essai in range(5):
            r = S.get(B + '%s/%d' % (t, i), params={'context': 'edit'},
                      timeout=300)
            if r.status_code < 300:
                return r.json()
            time.sleep(2 ** essai)
        raise SystemExit('lecture refusée sur %s/%d' % (t, i))

    gab = (lire(*GABARIT).get('content') or {}).get('raw', '')
    print('gabarit : %d caractères' % len(gab))

    prepare = []
    for i, c in CIBLES.items():
        d = lire('pages', i)
        vieux = (d.get('content') or {}).get('raw', '')
        c = dict(c)
        if c['corps'] is None:
            c['corps'] = nettoyer(vieux)
        neuf = page(gab, c)
        for marque, n in (('<main', 1), ('<h1', 1),
                          ('<header class="entete"', 1),
                          ('<footer class="pied"', 1)):
            if neuf.count(marque) != n:
                raise SystemExit('%s : %d × %s, attendu %d'
                                 % (c['url'], neuf.count(marque), marque, n))
        manque = [t for t in re.findall(r'<h2[^>]*>(.*?)</h2>', vieux, re.S)
                  if t not in neuf]
        if manque:
            raise SystemExit('titres perdus sur %s : %s' % (c['url'], manque))
        prepare.append((i, c, vieux, d, neuf))
        print('%-44s %6d → %6d caractères · %d h2 conservés'
              % (c['url'].replace(SITE, ''), len(vieux), len(neuf),
                 len(re.findall(r'<h2', neuf))))

    if a.essai:
        open('/tmp/claude-0/legales-essai.html', 'w').write(prepare[0][4])
        return

    jour = datetime.date.today().isoformat()
    dd = os.path.join(SAUVE, jour)
    os.makedirs(dd, exist_ok=True)
    for i, c, vieux, d, neuf in prepare:
        f = os.path.join(dd, 'pages-%d.json' % i)
        json.dump({'contenu': vieux, 'modele': d.get('template') or '',
                   'titre': d['title']['raw'], 'slug': d['slug']},
                  open(f, 'w'), ensure_ascii=False, indent=1)
        print('sauvegardé : %s' % os.path.relpath(f, RACINE))

    for i, c, vieux, d, neuf in prepare:
        for essai in range(4):
            r = S.post(B + 'pages/%d' % i, json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->',
                'template': CANVAS}, timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        S.post(B + 'pages/%d' % i, json={'meta': {'_elementor_edit_mode': ''}},
               timeout=180)
        time.sleep(2)
        r = S.get(c['url'], timeout=180)
        t = r.text
        print('%-44s %d · %d en-tête · %d pied · %d h1 · ancien menu %d'
              % (c['url'].replace(SITE, ''), r.status_code,
                 t.count('<header class="entete"'), t.count('<footer class="pied"'),
                 len(re.findall(r'<h1[\s>]', t)), t.count('Oasis de Dakhla')))


if __name__ == '__main__':
    main()
