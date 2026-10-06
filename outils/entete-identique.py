#!/usr/bin/env python3
"""Un seul en-tête, un seul pied, un seul logo, sur toutes les pages.

    WP_AUTH='compte:mdp' python3 outils/entete-identique.py --essai
    WP_AUTH='compte:mdp' python3 outils/entete-identique.py --appliquer

Rémi&nbsp;: « le menu doit être exactement le même que toutes les autres
pages, qu'il n'y ait pas un changement de DA ». Mesure faite, il y avait
trois en-têtes sur le site :

  · 55 pages servent le même, au caractère près (4 139 octets) ;
  · l'accueil en sert un autre : logo en base64 au lieu d'une URL, et tous
    les sous-titres du méga-menu différents (« Dahabeya, felouque, bateau 5★ »
    contre « Dahabeya, felouque, Louxor et Assouan », « Voyage en solo » contre
    « Voyage solo »…) ;
  · le brouillon de « L'agence » en sert un troisième, avec un autre fichier
    de logo et un « ☰ » devant « Menu ».

On prend celui des 55 comme référence, et on l'écrit partout. Le script du
burger va chercher `.burger` et `.nav` et pose lui-même `type`,
`aria-expanded` et `aria-controls` : la place du bouton dans le balisage ne
change rien à son fonctionnement.

Et le logo. Mélanie a écrit deux fois « attention changer le logo pour un
fond transparent » (12347, 12348). Les quatre fichiers en service ont bien un
canal alpha — ce que j'avais répondu, et c'était passer à côté. En mesurant
la teinte des pixels opaques, on voit ce qu'elle voit :

  Logo_authentique_Egypte-removebg-preview.png   24,4 % de l'encre hors teinte
  cropped-Screenshot_…-removebg-preview-1.webp   23,5 %
  le logo en base64 de l'accueil                  3,8 %
  authentique-egypte-logo-transparent.webp        0,0 %

Un quart de l'encre du logo servi sur 55 pages est brune et non dorée : c'est
le liseré laissé par le détourage, très visible sur le bleu nuit du pied de
page. Le fichier d'août est propre. C'est lui qu'on sert, partout.
"""

import argparse
import base64
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cibles

SITE = 'https://authentiquegypte.com'
REFERENCE = 5229                      # /voyage-a-fayoum/
LOGO_SALE = re.compile(
    r'https://authentiquegypte\.com/wp-content/uploads/'
    r'(?:2026/09/Logo_authentique_Egypte-removebg-preview\.png'
    r'|2023/10/cropped-Screenshot_20231015_082741_Instagram-removebg-preview-1'
    r'\.webp)')
LOGO_PROPRE = (SITE + '/wp-content/uploads/2026/08/'
               'authentique-egypte-logo-transparent.webp')
BASE64 = re.compile(r'src="data:image/[a-z+]+;base64,[A-Za-z0-9+/=]+"')


def morceau(h, deb, fin):
    i = h.find(deb)
    if i < 0:
        return None
    j = h.find(fin, i)
    if j < 0:
        return None
    return i, j + len(fin)


def logo_propre(h):
    """Le logo détouré proprement, et plus de base64 dans l'en-tête."""
    h, n = LOGO_SALE.subn(LOGO_PROPRE, h)
    b = morceau(h, '<header class="entete"', '</header>')
    if b:
        tete = BASE64.sub('src="%s"' % LOGO_PROPRE, h[b[0]:b[1]])
        if tete != h[b[0]:b[1]]:
            h = h[:b[0]] + tete + h[b[1]:]
            n += 1
    return h, n


def poser(h, deb, fin, neuf, url):
    b = morceau(h, deb, fin)
    if not b:
        return h, 0
    if h[b[0]:b[1]] == neuf:
        return h, 0
    return h[:b[0]] + neuf + h[b[1]:], 1


def courante(h, url):
    """Remet aria-current sur le lien de la page qu'on regarde."""
    h = h.replace(' aria-current="page"', '')
    cible = '<a href="%s">' % url
    if h.count(cible) >= 1:
        h = h.replace(cible, '<a href="%s" aria-current="page">' % url, 1)
    return h


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

    ref = (lire('pages', REFERENCE).get('content') or {}).get('raw', '')
    ref, _ = logo_propre(ref)
    be = morceau(ref, '<header class="entete"', '</header>')
    bp = morceau(ref, '<footer class="pied"', '</footer>')
    if not be or not bp:
        raise SystemExit('en-tête ou pied introuvable sur la page de référence')
    ENTETE, PIED = ref[be[0]:be[1]], ref[bp[0]:bp[1]]
    print('référence : en-tête %d octets · pied %d octets · logo %s'
          % (len(ENTETE), len(PIED), 'propre' if LOGO_PROPRE in ENTETE else '?'))

    a_ecrire = []
    for c in cibles.toutes():
        d = lire(c['type'], c['cible'])
        h = (d.get('content') or {}).get('raw', '')
        if '<header class="entete"' not in h:
            print('%-46s pas de nouvel en-tête — laissée' % c['url'].replace(SITE, ''))
            continue
        neuf, nl = logo_propre(h)
        neuf, ne = poser(neuf, '<header class="entete"', '</header>', ENTETE,
                         c['url'])
        neuf, np = poser(neuf, '<footer class="pied"', '</footer>', PIED,
                         c['url'])
        if ne:
            b = morceau(neuf, '<header class="entete"', '</header>')
            neuf = (neuf[:b[0]] + courante(neuf[b[0]:b[1]], c['url'])
                    + neuf[b[1]:])
        if neuf == h:
            continue
        a_ecrire.append((c, neuf))
        print('%-46s logo ×%d · en-tête %s · pied %s · %+d octets'
              % (c['url'].replace(SITE, '')[:46], nl,
                 'remplacé' if ne else '=', 'remplacé' if np else '=',
                 len(neuf) - len(h)))

    print('\n%d page(s) à écrire' % len(a_ecrire))
    if a.essai:
        return
    for c, neuf in a_ecrire:
        for essai in range(4):
            r = S.post(B + '%s/%d' % (c['type'], c['cible']), json={
                'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                timeout=600)
            if r.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
    print('%d page(s) écrites.' % len(a_ecrire))


if __name__ == '__main__':
    main()
