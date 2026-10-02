#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le menu mobile, sur les pages où il ne s'ouvrait pas.

    WP_AUTH='compte:mot de passe' ./outils/menu-mobile.py [--essai]

Contrôle à 390 px, clic réel sur le bouton « Menu » des 57 pages : il
reste inerte sur 34 d'entre elles. La navigation garde `display:none`
après le clic, le bouton n'a pas d'`aria-expanded`, et rien ne se passe.
Les quatorze fiches programme, les six circuits, les neuf destinations,
les quatre profils et le blog : un visiteur sur téléphone ne peut pas
naviguer du tout. C'est la majorité du trafic d'une agence de voyage.

Deux pages sur trois marchent, et pour deux raisons différentes — ce qui
explique que personne ne l'ait vu. L'accueil porte la règle
`.nav--ouverte` et le gestionnaire qui la bascule. Les vingt-deux guides
passent par des styles en ligne. Les trente-quatre autres n'ont ni l'un
ni l'autre : elles ont hérité du bouton sans ce qui le fait fonctionner.

On reprend ce qui marche sur l'accueil et on le pose sur les autres : la
classe fait tout, le style en ligne ne survivait pas à un
redimensionnement. Le point de bascule est lu sur chaque page plutôt que
supposé — il vaut 910 px sur l'accueil et 860 px ailleurs, et une classe
d'ouverture qui traînerait au-delà laisserait une colonne blanche
flottante par-dessus la barre de navigation.
"""

import argparse
import os
import re
import time
from importlib.machinery import SourceFileLoader

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERE = 7642
Q = '/pages?parent=%d&per_page=100&status=any&context=edit&orderby=menu_order&order=asc'
E = '.elementor-template-canvas '
H = '.elementor-template-canvas' * 6 + ' '
MARQUE = 'data-menu1="1"'

REGLES = (
    H + '.nav.nav--ouverte{display:flex;position:absolute;top:74px;left:20px;right:20px;'
    'flex-direction:column;align-items:stretch;background:#fff;'
    'border:1px solid var(--ligne,#E4E4EA);border-radius:20px;padding:12px;'
    'box-shadow:var(--ombre-f,0 18px 40px rgba(9,77,96,.16));z-index:60;'
    'max-height:calc(100vh - 96px);overflow-y:auto}'
    + H + '.nav--ouverte .menu{position:static}'
    + H + '.nav--ouverte .menu__pan{position:static;transform:none;min-width:0;'
    'box-shadow:none;border:0;border-left:2px solid var(--or-fond,#FEF3DC);'
    'border-radius:0;margin:2px 0 6px 10px;padding:2px 0 2px 10px;display:none}'
    + H + '.nav--ouverte .menu:hover .menu__pan,'
    + H + '.nav--ouverte .menu:focus-within .menu__pan{transform:none}'
    + H + '.nav--ouverte .menu>button[aria-expanded="true"]+.menu__pan'
    '{transform:none;display:block;opacity:1;visibility:visible}')

# %d : la largeur à partir de laquelle la navigation redevient une barre.
SCRIPT = ('<script ' + MARQUE + '>(function(){'
          'var b=document.querySelector(".burger"),n=document.querySelector(".nav");'
          'if(!b||!n||b.dataset.pose)return;b.dataset.pose="1";'
          'if(!b.getAttribute("type"))b.setAttribute("type","button");'
          'b.setAttribute("aria-expanded","false");'
          'if(!n.id)n.id="nav-principale";'
          'b.setAttribute("aria-controls",n.id);'
          'function fermer(){n.classList.remove("nav--ouverte");'
          'b.setAttribute("aria-expanded","false");'
          'b.setAttribute("aria-label","Ouvrir le menu");'
          'Array.prototype.forEach.call('
          'n.querySelectorAll(\'.menu>button[aria-expanded="true"]\'),'
          'function(x){x.setAttribute("aria-expanded","false");});}'
          'b.addEventListener("click",function(){'
          'var o=n.classList.toggle("nav--ouverte");'
          'b.setAttribute("aria-expanded",String(o));'
          'b.setAttribute("aria-label",o?"Fermer le menu":"Ouvrir le menu");'
          'if(!o)fermer();});'
          'document.addEventListener("keydown",function(e){'
          'if(e.key==="Escape"&&n.classList.contains("nav--ouverte"))fermer();});'
          'var m=matchMedia("(min-width:%dpx)");'
          'var suivre=function(e){if(e.matches)fermer();};'
          'if(m.addEventListener)m.addEventListener("change",suivre);'
          'else m.addListener(suivre);'
          '})();</script>')


def _seuil(h):
    """La largeur à laquelle la page cache sa navigation. Lue, pas supposée."""
    for m in re.finditer(r'@media\s*\(max-width:\s*(\d+)px\)\s*\{', h):
        d = m.end()
        prof, k = 1, d
        while prof and k < len(h):
            prof += 1 if h[k] == '{' else -1 if h[k] == '}' else 0
            k += 1
        bloc = h[d:k]
        if re.search(r'\.nav\s*\{[^}]*display:\s*none', bloc):
            return int(m.group(1))
    return 910


# Le gestionnaire des vingt-deux guides écrit la mise en page dans
# l'attribut style de la navigation. Ouvert à 390 px puis élargi, le menu
# restait une colonne blanche posée par-dessus la barre : le style en
# ligne ne sait pas qu'on a changé de largeur. On le retire pour poser le
# même mécanisme que l'accueil, où c'est la classe qui décide.
ANCIEN = re.compile(r"<script[^>]*>(?:(?!</script>).)*?querySelector\('\.burger'\)"
                    r"(?:(?!</script>).)*?n\.style\.display(?:(?!</script>).)*?</script>",
                    re.S)


def corriger(h):
    if MARQUE in h:
        return h, None
    if 'class="burger"' not in h and "class='burger'" not in h:
        return h, None
    # L'accueil a déjà la bonne règle et le bon gestionnaire : on n'en
    # pose pas un second, deux gestionnaires sur un bouton se défont.
    if '.nav--ouverte' in h and re.search(r"querySelector\('\.burger'\)", h):
        return h, None
    h, vieux = ANCIEN.subn('', h)
    return (h + '<style ' + MARQUE + '>' + REGLES + '</style>'
            + SCRIPT % (_seuil(h) + 1)), (_seuil(h), vieux)


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

    n = 0
    for k in pages:
        p_ = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
        brut = re.sub(r'<!-- /?wp:html -->\n?', '', p_['content']['raw'])
        neuf, quoi = corriger(brut)
        if quoi is None:
            continue
        seuil, vieux = quoi
        print('   #%-6d %-34s bascule à %d px%s'
              % (k['id'], (p_.get('title') or {}).get('raw', '')[:34], seuil,
                 ' · ancien gestionnaire retiré' if vieux else ''))
        if a.essai:
            n += 1
            continue
        n += 1
        corps = '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'
        for essai in range(4):
            try:
                dep.appel('POST', '/pages/%d' % k['id'], {'content': corps})
                relu = dep.appel('GET', '/pages/%d?context=edit' % k['id'])
                if corriger(re.sub(r'<!-- /?wp:html -->\n?', '',
                                   relu['content']['raw']))[1] is None:
                    break
            except SystemExit as motif:
                print('      reprise %d/3 — %s' % (essai + 1, str(motif).splitlines()[0][:60]))
            time.sleep(2 ** essai)
        else:
            print('      ✗ ABANDON #%d' % k['id'])
    print('\n%d page(s) %s.' % (n, 'à corriger' if a.essai else 'corrigée(s)'))


if __name__ == '__main__':
    main()
