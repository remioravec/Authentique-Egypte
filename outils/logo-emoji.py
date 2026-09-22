#!/usr/bin/env python3
"""
Le nouveau logo partout, et plus un seul emoji hors des avis Google.

    WP_AUTH='compte:mot de passe' ./outils/logo-emoji.py [--essai]

LE LOGO. L'ancien fichier était déjà transparent : ce que Mélanie
appelait « le fond » venait de l'en-tête, blanc à 95 %, sur lequel le
doré est délavé. Rémi a fourni le nouveau, transparent lui aussi, aux
mêmes dimensions. Il remplace l'ancien aux 112 endroits où il figure —
56 en-têtes et 56 pieds de page.

LES EMOJI. « Aucun emoji dans le site ailleurs » : les avis Google sont
laissés tels quels, ce sont des témoignages publiés qu'on ne réécrit
pas. Partout ailleurs ils partent, y compris le ☰ du bouton de menu et
le ✉ du bandeau de contact : le mot « Menu » et l'adresse se suffisent.

Deux signes restent, parce que ce ne sont pas des emoji mais de la
typographie : l'étoile ★ des notes, et les flèches → des renvois. Les
retirer casserait l'affichage des notes.
"""

import argparse
import os
import re
import sys
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'

ANCIEN_LOGO = 'authentique-egypte-logo-transparent.webp'
NOUVEAU_LOGO = 'Logo_authentique_Egypte-removebg-preview.png'
BASE_2026_08 = 'https://authentiquegypte.com/wp-content/uploads/2026/08/'
BASE_2026_09 = 'https://authentiquegypte.com/wp-content/uploads/2026/09/'

# Les emoji. L'étoile ★☆ des notes et les flèches ne sont pas dedans :
# ce sont des signes typographiques, et l'étoile porte une information.
EMOJI = re.compile(
    '[\U0001F000-\U0001FAFF☀-☄☇-⛿✀-➿'
    '⬀-⯿️‍♀♂]')


def poser_logo(h):
    n = h.count(ANCIEN_LOGO)
    return h.replace(BASE_2026_08 + ANCIEN_LOGO, BASE_2026_09 + NOUVEAU_LOGO), n


def _nettoyer(t):
    """Retire les emoji et recolle proprement ce qui les entourait."""
    t = EMOJI.sub('\x00', t)
    # Un emoji seul entre deux espaces laisse un trou ; collé à un point,
    # il laisse deux phrases soudées. On recolle avec UN espace, sauf en
    # début ou en fin d'élément où il n'en faut aucun.
    t = re.sub(r'\s*\x00+\s*', lambda m: ' ', t)
    t = re.sub(r'(>)\s+', r'\1', t)
    t = re.sub(r'\s+(</)', r'\1', t)
    return t


def sans_emoji(h):
    """Tout le corps sauf le mur d'avis, les feuilles et les scripts."""
    gardes = []

    def mettre_de_cote(m):
        gardes.append(m.group(0))
        return '\x01%d\x01' % (len(gardes) - 1)

    # Les avis Google : verbatim, on n'y touche pas.
    h = re.sub(r'<article class="mur__a">.*?</article>', mettre_de_cote, h, flags=re.S)
    h = re.sub(r'<(script|style)\b.*?</\1>', mettre_de_cote, h, flags=re.S)

    avant = len(EMOJI.findall(h))
    h = _nettoyer(h)
    h = re.sub(r'\x01(\d+)\x01', lambda m: gardes[int(m.group(1))], h)
    return h, avant


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

    t_logo = t_emo = n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, nl = poser_logo(brut)
        neuf, ne = sans_emoji(neuf)
        if not nl and not ne:
            continue
        n += 1
        t_logo += nl
        t_emo += ne
        print('   #%-6d %-42s logo ×%d · emoji ×%d'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:42], nl, ne))
        if a.essai:
            continue
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if ANCIEN_LOGO not in relu['content']['raw']:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON, la page reste telle quelle')
    print('\n%d page(s) · %d logo(s) remplacé(s) · %d emoji retiré(s).' % (n, t_logo, t_emo))


if __name__ == '__main__':
    main()
