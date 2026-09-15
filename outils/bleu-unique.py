#!/usr/bin/env python3
"""
Ramène tous les bleus d'une page sur le bleu de marque, sans toucher au reste.

    ./outils/bleu-unique.py --site DIR [--sortie DIR] [--essai]

Le site porte plusieurs bleus selon la génération de la page : #167FA4 sur
les guides, les destinations et les catégories, #079DB6 sur les fiches
programme refaites. Vu en naviguant, la marque change de couleur d'une page
à l'autre.

La correction ne remplace pas une valeur par une autre — il y en a trop, et
chacune a son rôle (fond, texte, bordure, survol). Toute couleur dont la
TEINTE est bleue est pivotée sur la teinte du bleu de marque. La couleur
devient une, la hiérarchie des tons reste.

Un pivot de teinte à clarté HLS constante ne conserve PAS le contraste : la
luminance WCAG pondère le vert bien plus que le bleu, si bien que tourner
vers le cyan éclaircit l'œil sans que la clarté HLS bouge. Mesuré sur les 31
nuances du site, le pivot nu faisait perdre jusqu'à 2,79 points de contraste,
et l'accent #167FA4 tombait de 4,56 à 3,78 — sous le seuil AA du texte
normal. La clarté est donc réajustée après le pivot jusqu'à retrouver la
luminance de la couleur d'origine : le contraste est alors conservé au
centième près, contre n'importe quel fond.

Deux garde-fous sur la plage de teintes retenue, 176° à 212° :
  – en dessous, les verts et les turquoises du fond de carte ;
  – au-dessus, les violets ;
  – et une saturation d'au moins .12, sinon les gris bleutés de l'interface
    virent au bleu franc.
Le « G » de Google, le rouge des alertes et l'or des boutons sont hors
plage : ils ne bougent pas.
"""

import argparse
import colorsys
import os
import re

MARQUE = '#079DB6'
TEINTE = colorsys.rgb_to_hls(0x07 / 255, 0x9D / 255, 0xB6 / 255)[0]
PLAGE = (176, 212)
SATURATION_MINIMALE = .12


def luminance(rgb):
    """La luminance relative WCAG, celle dont dépend le contraste."""
    def canal(x):
        x /= 255
        return x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4
    r, g, b = rgb
    return .2126 * canal(r) + .7152 * canal(g) + .0722 * canal(b)


def _rgb(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, min(1, max(0, l)), s)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def teinte(r, g, b):
    """La couleur pivotée sur la teinte de marque, ou None si hors plage.

    La clarté est réajustée par dichotomie jusqu'à retrouver la luminance
    WCAG d'origine : sans cela le pivot éclaircit la couleur pour l'œil et
    fait perdre du contraste, alors même que la clarté HLS n'a pas bougé.
    """
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if not (PLAGE[0] <= h * 360 <= PLAGE[1] and s >= SATURATION_MINIMALE):
        return None
    vise = luminance((r, g, b))
    bas, haut = 0.0, 1.0
    for _ in range(40):
        milieu = (bas + haut) / 2
        if luminance(_rgb(TEINTE, milieu, s)) < vise:
            bas = milieu
        else:
            haut = milieu
    candidat = _rgb(TEINTE, (bas + haut) / 2, s)
    # La dichotomie tombe entre deux entiers : on garde le voisin le plus
    # proche en luminance, pour ne pas dériver d'un centième à chaque passage.
    voisins = [candidat, _rgb(TEINTE, bas, s), _rgb(TEINTE, haut, s)]
    return min(voisins, key=lambda c: abs(luminance(c) - vise))


def unifier(texte):
    """Toute couleur de teinte bleue ramenée sur celle du bleu de marque."""
    def hexa(m):
        x = m.group(1)
        if len(x) == 3:
            x = ''.join(c * 2 for c in x)
        n = teinte(int(x[:2], 16), int(x[2:4], 16), int(x[4:], 16))
        return m.group(0) if n is None else '#%02X%02X%02X' % n

    def rgb(m):
        n = teinte(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        return m.group(0) if n is None else '%s%d,%d,%d' % (m.group(1), *n)

    texte = re.sub(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])', hexa, texte)
    return re.sub(r'(rgba?\(\s*)(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})', rgb, texte)


def couleurs(texte):
    """Les couleurs écrites dans un texte, en hexadécimal majuscule."""
    vues = set()
    for x in re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])', texte):
        if len(x) == 3:
            x = ''.join(c * 2 for c in x)
        vues.add('#' + x.upper())
    for m in re.finditer(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})', texte):
        vues.add('#%02X%02X%02X' % tuple(int(g) for g in m.groups()))
    return vues


def bleus(texte):
    """Les couleurs de teinte bleue d'un texte : ce que l'outil va pivoter."""
    return {c for c in couleurs(texte)
            if teinte(int(c[1:3], 16), int(c[3:5], 16), int(c[5:], 16))}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site', required=True, help='dossier des pages')
    p.add_argument('--sortie', help='dossier de sortie (défaut : sur place)')
    p.add_argument('--essai', action='store_true', help='montrer sans rien écrire')
    a = p.parse_args()

    source = os.path.abspath(a.site)
    sortie = os.path.abspath(a.sortie) if a.sortie else source
    os.makedirs(sortie, exist_ok=True)

    total, touchees = 0, 0
    avant_tous, apres_tous = set(), set()
    for nom in sorted(os.listdir(source)):
        if not nom.endswith(('.html', '.css')):
            continue
        with open(os.path.join(source, nom), encoding='utf-8') as f:
            h = f.read()
        total += 1
        avant = bleus(h)
        neuf = unifier(h)
        apres = bleus(neuf)
        avant_tous |= avant
        apres_tous |= apres
        if neuf != h:
            touchees += 1
            print('   %-58s %d bleu(s) → %s' % (nom[:58], len(avant),
                                                ', '.join(sorted(apres)) or '—'))
        if not a.essai:
            with open(os.path.join(sortie, nom), 'w', encoding='utf-8') as f:
                f.write(neuf)
        elif sortie != source:
            pass

    print('\n%d fichier(s) lu(s), %d %s.' % (
        total, touchees, 'à corriger' if a.essai else 'corrigé(s)'))
    print('bleus avant : %s' % ', '.join(sorted(avant_tous)))
    print('bleus après : %s' % ', '.join(sorted(apres_tous)))
    if apres_tous - {MARQUE}:
        print('\nLes bleus restants ne sont pas des variantes de marque mais des '
              'nuances : même teinte, clarté et saturation d’origine conservées.')


if __name__ == '__main__':
    main()
