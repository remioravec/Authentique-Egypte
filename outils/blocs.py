#!/usr/bin/env python3
"""
Synchronise l'entête et le pied de page des maquettes.

Le méga-menu et le pied sont des blocs communs : sur le site ils seront
posés une seule fois, dans le thème. Dans les maquettes, ils sont
recopiés dans chaque fichier — et c'est ainsi qu'ils divergent. Au
relevé du 26/08/2026 il y avait huit entêtes différentes et quatre pieds
différents : trois valeurs contradictoires pour le nombre de séjours,
des liens qui renvoyaient tantôt vers la maquette tantôt vers l'ancien
site, et des listes de destinations qui ne se ressemblaient pas.

Ce script fait autorité : les blocs vivent dans
`maquettes/assets/blocs/`, et sont réinjectés dans chaque page.

    ./outils/blocs.py              synchronise
    ./outils/blocs.py --verifier   ne modifie rien, sort en 1 si ça a divergé

Seul l'état « page courante » reste propre à chaque page : il est
réappliqué après l'injection, d'après la table PAGE_COURANTE.
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAQUETTES = os.path.join(RACINE, 'maquettes')
BLOCS = os.path.join(MAQUETTES, 'assets', 'blocs')

# Ce que chaque page doit marquer comme « vous êtes ici ».
#
# On vise l'ancre EXACTE, pas seulement le href : `index.html` apparaît
# deux fois dans l'entête — le logo d'abord, le lien « Accueil » ensuite
# — et c'est le lien qu'il faut marquer, pas le logo.
#
# `dans_menu` dit si l'ancre vit dans un panneau de méga-menu : dans ce
# cas seulement, le bouton qui ouvre le panneau s'allume aussi.
PAGE_COURANTE = {
    'index.html':                ('<a href="index.html">Accueil</a>', False),
    'categorie-desert.html':     ('<a href="categorie-desert.html"><span>', True),
    'produit-siwa.html':         ('<a href="categorie-desert.html"><span>', True),
    'article-quand-partir.html': ('<a href="blog.html">Guides</a>', False),
    'blog.html':                 ('<a href="blog.html">Guides</a>', False),
    'destination.html':          ('<a href="destination.html"><span>', True),
    'qui-sommes-nous.html':      ("<a href=\"qui-sommes-nous.html\">L'agence</a>", False),
    'devis.html':                ('<a href="devis.html" class="btn btn--or btn--sm"', False),
}


def bloc(nom):
    with open(os.path.join(BLOCS, nom), encoding='utf-8') as f:
        return f.read().rstrip('\n')


def remplacer(source, ouvre, ferme, neuf):
    """Remplace la première balise <ouvre …> … </ferme> par `neuf`."""
    i = source.find(ouvre)
    if i < 0:
        return source, False
    j = source.find(ferme, i)
    if j < 0:
        return source, False
    j += len(ferme)
    if source[i:j] == neuf:
        return source, False
    return source[:i] + neuf + source[j:], True


def marquer_courante(entete, fichier):
    """Repose l'état « page courante », que l'injection vient d'effacer."""
    ancre, dans_menu = PAGE_COURANTE.get(fichier, (None, False))
    if not ancre:
        return entete

    i = entete.find(ancre)
    if i < 0:
        raise SystemExit('Ancre de page courante introuvable dans %s : %s' % (fichier, ancre))

    # L'attribut se pose juste après le href, avant la fin de la balise.
    fin_href = entete.index('"', entete.index('href="', i) + 6) + 1
    entete = entete[:fin_href] + ' aria-current="page"' + entete[fin_href:]

    if dans_menu:
        pan = entete.rfind('<div class="menu">', 0, i)
        bouton = entete.find('<button aria-expanded="false"', pan)
        fin = bouton + len('<button aria-expanded="false"')
        entete = entete[:fin] + ' aria-current="true"' + entete[fin:]

    return entete


def main():
    verifier = '--verifier' in sys.argv
    entete_type, pied_type = bloc('entete.html'), bloc('pied.html')

    divergences = []
    for fichier in sorted(PAGE_COURANTE):
        chemin = os.path.join(MAQUETTES, fichier)
        if not os.path.exists(chemin):
            continue
        with open(chemin, encoding='utf-8') as f:
            source = f.read()

        source, a, b = source, False, False
        source, a = remplacer(source, '<header class="entete">', '</header>',
                              marquer_courante(entete_type, fichier))
        source, b = remplacer(source, '<footer class="pied">', '</footer>', pied_type)

        if a or b:
            divergences.append((fichier, 'entête' if a and not b else 'pied' if b and not a else 'entête + pied'))
            if not verifier:
                with open(chemin, 'w', encoding='utf-8') as f:
                    f.write(source)

    if not divergences:
        print('Les huit pages portent le même entête et le même pied.')
        return 0

    for fichier, quoi in divergences:
        print('  %-26s %s %s' % (fichier, quoi, 'a divergé' if verifier else 'resynchronisé'))
    if verifier:
        print('\n%d page(s) ont divergé des blocs communs. Lancez ./outils/blocs.py' % len(divergences))
        return 1
    print('\n%d page(s) resynchronisées sur maquettes/assets/blocs/.' % len(divergences))
    return 0


if __name__ == '__main__':
    sys.exit(main())
